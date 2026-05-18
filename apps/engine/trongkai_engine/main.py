"""FastAPI app — endpoints REST tipados del motor Trongkai."""

from __future__ import annotations

from typing import Literal

import structlog
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .bottleneck import (
    CapacidadEtapa,
    EtapaProceso,
    compute_bottleneck,
)
from .financial import FlujoMes, calcular_kpis
from .mass_balance import (
    BalanceMode,
    MassBalanceError,
    MateriaPrimaSpec,
    compute_mass_balance,
)

log = structlog.get_logger()

app = FastAPI(
    title="Trongkai Engine",
    version=__version__,
    description="Motor de cálculo de la biorrefinería Trongkai",
)


@app.get(
    "/health",
    tags=["meta"],
    summary="Health check",
    description="Liveness probe del motor. Devuelve estado y versión del paquete.",
)
def health() -> dict:
    return {"status": "ok", "version": __version__}


# ----- Balance de masa -----


class MassBalanceRequest(BaseModel):
    mmpp_codigo: str
    humedad_inicial_pct: float = Field(ge=0, lt=1)
    materia_solida_pct: float = Field(ge=0, le=1)
    aceite_extraible_pct: float = Field(default=0.0, ge=0, le=1)
    licopeno_pct: float = Field(default=0.0, ge=0, le=1)
    pectina_pct: float = Field(default=0.0, ge=0, le=1)
    input_ton: float = Field(gt=0)
    mode: Literal["A", "B"] = "A"
    humedad_final_pct: float = Field(default=0.10, ge=0, lt=1)
    perdidas_pct: float = Field(default=0.031, ge=0, lt=1)


class MassBalanceResponse(BaseModel):
    mmpp: str
    mode: str
    input_ton: float
    materia_seca_pura_ton: float
    aceite_extraido_ton: float
    licopeno_extraido_ton: float
    pectina_extraida_ton: float
    harina_final_ton: float
    agua_evaporada_ton: float
    perdidas_ton: float
    materia_seca_neta_pct: float
    delta_balance_pct: float
    sankey: dict


@app.post(
    "/mass-balance",
    response_model=MassBalanceResponse,
    tags=["balance-de-masa"],
    summary="Calcular balance de masa de un lote",
    description=(
        "Calcula el balance de masa para un lote de MMPP en modo A (base inicial) o B "
        "(base deshidratada). Devuelve toneladas de cada fracción, % de materia seca "
        "neta entregada y el grafo Sankey listo para ECharts. Falla con 422 si el "
        "cierre supera ±0.5% o si las extracciones exceden la materia sólida disponible."
    ),
)
def mass_balance_endpoint(req: MassBalanceRequest) -> MassBalanceResponse:
    try:
        spec = MateriaPrimaSpec(
            codigo=req.mmpp_codigo,
            humedad_inicial_pct=req.humedad_inicial_pct,
            materia_solida_pct=req.materia_solida_pct,
            aceite_extraible_pct=req.aceite_extraible_pct,
            licopeno_pct=req.licopeno_pct,
            pectina_pct=req.pectina_pct,
        )
        result = compute_mass_balance(
            spec=spec,
            input_ton=req.input_ton,
            mode=BalanceMode(req.mode),
            humedad_final_pct=req.humedad_final_pct,
            perdidas_pct=req.perdidas_pct,
        )
    except MassBalanceError as exc:
        log.warning("mass_balance_error", error=str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return MassBalanceResponse(
        mmpp=result.mmpp,
        mode=result.mode.value,
        input_ton=result.input_ton,
        materia_seca_pura_ton=result.materia_seca_pura_ton,
        aceite_extraido_ton=result.aceite_extraido_ton,
        licopeno_extraido_ton=result.licopeno_extraido_ton,
        pectina_extraida_ton=result.pectina_extraida_ton,
        harina_final_ton=result.harina_final_ton,
        agua_evaporada_ton=result.agua_evaporada_ton,
        perdidas_ton=result.perdidas_ton,
        materia_seca_neta_pct=result.materia_seca_neta_pct,
        delta_balance_pct=result.delta_balance_pct,
        sankey=result.sankey,
    )


# ----- Bottleneck -----


class CapacidadInput(BaseModel):
    etapa: str
    ton_por_hora: float | None = None
    tiempo_residencia_h: float = 0.0
    aplica: bool = True


class BottleneckRequest(BaseModel):
    capacidades: list[CapacidadInput]
    tiempo_descomposicion_h: float = Field(gt=0)
    capacidad_camion_ton: float = Field(default=22.5, gt=0)
    horas_operativas_dia: float = Field(default=24.0, gt=0, le=24)


@app.post(
    "/bottleneck",
    tags=["operacion"],
    summary="Detectar cuello de botella del proceso",
    description=(
        "Dado un set de capacidades por etapa y el tiempo de descomposición de la MMPP, "
        "calcula el flujo máximo (ton/h), identifica la etapa cuello de botella, evalúa "
        "si la planta puede recibir un nuevo camión y devuelve un semáforo de alerta "
        "(verde / amarilla / roja)."
    ),
)
def bottleneck_endpoint(req: BottleneckRequest) -> dict:
    capacidades = [
        CapacidadEtapa(
            etapa=EtapaProceso(c.etapa),
            ton_por_hora=c.ton_por_hora,
            tiempo_residencia_h=c.tiempo_residencia_h,
            aplica=c.aplica,
        )
        for c in req.capacidades
    ]
    try:
        result = compute_bottleneck(
            capacidades,
            tiempo_descomposicion_h=req.tiempo_descomposicion_h,
            capacidad_camion_ton=req.capacidad_camion_ton,
            horas_operativas_dia=req.horas_operativas_dia,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "flujo_max_ton_h": result.flujo_max_ton_h,
        "etapa_bottleneck": result.etapa_bottleneck.value,
        "tiempo_proceso_total_h": result.tiempo_proceso_total_h,
        "tiempo_descomposicion_h": result.tiempo_descomposicion_h,
        "ventana_segura_h": result.ventana_segura_h,
        "puede_recibir": result.puede_recibir,
        "camiones_max_dia": result.camiones_max_dia,
        "horas_operativas_dia": result.horas_operativas_dia,
        "incertidumbres": result.incertidumbres,
        "alerta": result.alerta,
    }


# ----- Financiero -----


class FlujoMesInput(BaseModel):
    mes: int
    ingresos_ventas: float = 0.0
    ingresos_maquilas: float = 0.0
    ingresos_recepcion: float = 0.0
    ingresos_transferencia_tec: float = 0.0
    costos_directos: float = 0.0
    gastos_fijos: float = 0.0
    capex_periodo: float = 0.0


class FinancialRequest(BaseModel):
    flujos: list[FlujoMesInput]
    wacc_anual: float = Field(ge=0, lt=1)


@app.post(
    "/financial/kpis",
    tags=["financiero"],
    summary="KPIs financieros de un plan de flujos",
    description=(
        "Recibe el flujo de caja mensual proyectado y la WACC anual; devuelve TIR "
        "anualizada del proyecto, VAN, payback descontado en meses, margen EBITDA "
        "promedio y ratio CapEx/Ventas. Base para el dashboard de directorio (Módulo 3)."
    ),
)
def financial_kpis_endpoint(req: FinancialRequest) -> dict:
    flujos = [
        FlujoMes(
            mes=f.mes,
            ingresos_ventas=f.ingresos_ventas,
            ingresos_maquilas=f.ingresos_maquilas,
            ingresos_recepcion=f.ingresos_recepcion,
            ingresos_transferencia_tec=f.ingresos_transferencia_tec,
            costos_directos=f.costos_directos,
            gastos_fijos=f.gastos_fijos,
            capex_periodo=f.capex_periodo,
        )
        for f in req.flujos
    ]
    kpis = calcular_kpis(flujos, wacc_anual=req.wacc_anual)
    return {
        "tir_proyecto_anual": kpis.tir_proyecto_anual,
        "van": kpis.van,
        "payback_meses": kpis.payback_meses,
        "ebitda_margin_promedio": kpis.ebitda_margin_promedio,
        "ratio_capex_ventas": kpis.ratio_capex_ventas,
    }
