"""FastAPI app — endpoints REST tipados del motor Trongkai."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import __version__
from .agenda import (
    SupplierTarget,
    TemporadaMMPP,
    build_agenda,
)
from .bottleneck import (
    CapacidadEtapa,
    EtapaProceso,
    compute_bottleneck,
)
from .config import get_settings
from .excel_export import export_plan_to_excel
from .financial import FlujoMes, calcular_kpis
from .mass_balance import (
    BalanceMode,
    MassBalanceError,
    MateriaPrimaSpec,
    compute_mass_balance,
)
from .plan_builder import ParametrosPlan, build_plan, tornado_sensibilidades
from .whatif import Escenario, comparar_escenarios

log = structlog.get_logger()

app = FastAPI(
    title="Trongkai Engine",
    version=__version__,
    description="Motor de cálculo de la biorrefinería Trongkai",
)

# CORS: permite localhost dev + dominios oficiales del frontend (Vercel + custom).
# Para producción, restringir a dominios específicos seteando env CORS_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3010",
        "http://localhost:3011",
        "https://trongkai.vercel.app",
        "https://trongkai-nicolasrietta-1798s-projects.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)


DEFAULT_API_KEY = "changeme-internal-only"


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Valida header X-API-Key contra ENGINE_API_KEY env var.

    Modo "graceful auth":
    - Si `ENGINE_API_KEY` env var no está seteada o vale el default
      ("changeme-internal-only"), el endpoint queda abierto. Esto permite
      desarrollar localmente sin headers y deployar a Fly sin romper el
      frontend público hasta que se decida el modelo de auth definitivo.
    - Si está seteada a un valor distinto del default, el header X-API-Key
      es OBLIGATORIO y debe matchear.

    Para activar auth en prod: `fly secrets set ENGINE_API_KEY=<valor-fuerte>`.
    Aplica a todos los endpoints excepto /health (liveness probe de Fly).
    """
    expected = get_settings().engine_api_key
    if expected == DEFAULT_API_KEY or not expected:
        return  # modo abierto — auth desactivada
    if not x_api_key or x_api_key != expected:
        log.warning("auth_failed", has_header=bool(x_api_key))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
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
    dependencies=[Depends(require_api_key)],
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
    dependencies=[Depends(require_api_key)],
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


# ----- Agenda de camiones -----


class TemporadaInput(BaseModel):
    mmpp_codigo: str
    mes_inicio: int = Field(ge=1, le=12)
    mes_fin: int = Field(ge=1, le=12)
    tiempo_descomposicion_h: float = Field(gt=0)


class SupplierTargetInput(BaseModel):
    nombre: str
    mmpp_codigo: str
    volumen_anual_ton: float = Field(gt=0)
    capacidad_camion_ton: float = Field(default=22.5, gt=0)


class AgendaRequest(BaseModel):
    ano: int = Field(ge=2026, le=2035)
    capacidades: list[CapacidadInput]
    temporadas: list[TemporadaInput]
    suppliers: list[SupplierTargetInput]
    horas_operativas_dia: float = Field(default=24.0, gt=0, le=24)


@app.post(
    "/agenda",
    tags=["operacion"],
    summary="Planificar agenda de camiones de un año",
    description=(
        "Recibe capacidades por etapa, temporadas por MMPP y suppliers con su volumen "
        "comprometido. Devuelve la lista de slots (fecha, supplier, ton, camiones) "
        "respetando el bottleneck. Entregable del Módulo 1: 'cuántos camiones puedo recibir'."
    ),
    dependencies=[Depends(require_api_key)],
)
def agenda_endpoint(req: AgendaRequest) -> dict:
    capacidades = [
        CapacidadEtapa(
            etapa=EtapaProceso(c.etapa),
            ton_por_hora=c.ton_por_hora,
            tiempo_residencia_h=c.tiempo_residencia_h,
            aplica=c.aplica,
        )
        for c in req.capacidades
    ]
    temporadas = [
        TemporadaMMPP(
            mmpp_codigo=t.mmpp_codigo,
            mes_inicio=t.mes_inicio,
            mes_fin=t.mes_fin,
            tiempo_descomposicion_h=t.tiempo_descomposicion_h,
        )
        for t in req.temporadas
    ]
    suppliers_por_mmpp: dict[str, list[SupplierTarget]] = {}
    for s in req.suppliers:
        suppliers_por_mmpp.setdefault(s.mmpp_codigo, []).append(
            SupplierTarget(
                nombre=s.nombre,
                mmpp_codigo=s.mmpp_codigo,
                volumen_anual_ton=s.volumen_anual_ton,
                capacidad_camion_ton=s.capacidad_camion_ton,
            )
        )

    result = build_agenda(
        ano=req.ano,
        capacidades=capacidades,
        temporadas=temporadas,
        suppliers_por_mmpp=suppliers_por_mmpp,
        horas_operativas_dia=req.horas_operativas_dia,
    )

    return {
        "total_ton_planificadas": result.total_ton_planificadas,
        "total_camiones": result.total_camiones,
        "advertencias": result.advertencias,
        "bottleneck": (
            {
                "etapa": result.bottleneck.etapa_bottleneck.value,
                "flujo_max_ton_h": result.bottleneck.flujo_max_ton_h,
                "camiones_max_dia": result.bottleneck.camiones_max_dia,
                "alerta": result.bottleneck.alerta,
            }
            if result.bottleneck
            else None
        ),
        "slots": [
            {
                "fecha": s.fecha.isoformat(),
                "supplier": s.supplier_nombre,
                "mmpp": s.mmpp_codigo,
                "ton_dia": s.ton_dia,
                "camiones_dia": s.camiones_dia,
            }
            for s in result.slots
        ],
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
    dependencies=[Depends(require_api_key)],
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


# ----- Plan 5 Años -----


class PlanRequest(BaseModel):
    wacc_anual: float = Field(default=0.12, ge=0, lt=1)
    volumen_total_ton_ano: float = Field(default=50_000, gt=0)
    opex_mensual_clp: float = Field(default=35_000_000, ge=0)
    costo_mmpp_clp_kg: float = Field(default=50, ge=0)


@app.post(
    "/plan",
    tags=["financiero"],
    summary="Generar Plan 5 Años con KPIs",
    description=(
        "Construye el plan financiero de 60 meses con precios y rendimientos por defecto, "
        "y devuelve flujos mensuales + KPIs + resumen anual. Si querés un export Excel, "
        "usá POST /plan/export en su lugar."
    ),
    dependencies=[Depends(require_api_key)],
)
def plan_endpoint(req: PlanRequest) -> dict:
    params = ParametrosPlan(
        wacc_anual=req.wacc_anual,
        volumen_total_ton_ano=req.volumen_total_ton_ano,
        opex_mensual_clp=req.opex_mensual_clp,
        costo_mmpp_clp_kg=req.costo_mmpp_clp_kg,
    )
    plan = build_plan(params)
    return {
        "kpis": {
            "tir_proyecto_anual": plan.kpis.tir_proyecto_anual,
            "van": plan.kpis.van,
            "payback_meses": plan.kpis.payback_meses,
            "ebitda_margin_promedio": plan.kpis.ebitda_margin_promedio,
            "ratio_capex_ventas": plan.kpis.ratio_capex_ventas,
        },
        "resumen_anual": [
            {
                "ano": i + 1,
                "ingresos": plan.ingresos_anuales[i],
                "ebitda": plan.ebitda_anuales[i],
                "capex": plan.capex_anuales[i],
                "ebitda_margin": (plan.ebitda_anuales[i] / plan.ingresos_anuales[i]) if plan.ingresos_anuales[i] else 0,
            }
            for i in range(5)
        ],
        "por_marca": {
            marca: {
                "ingresos_anuales": r.ingresos_anuales,
                "volumen_ton_anuales": r.volumen_ton_anuales,
            }
            for marca, r in plan.por_marca.items()
        },
        "flujos_meses": [
            {
                "mes": f.mes,
                "ingresos_ventas": f.ingresos_ventas,
                "ingresos_maquilas": f.ingresos_maquilas,
                "ingresos_transferencia_tec": f.ingresos_transferencia_tec,
                "costos_directos": f.costos_directos,
                "gastos_fijos": f.gastos_fijos,
                "ebitda": f.ebitda,
                "capex_periodo": f.capex_periodo,
                "flujo_neto": f.flujo_neto,
            }
            for f in plan.flujos
        ],
    }


@app.post(
    "/plan/export",
    tags=["financiero"],
    summary="Exportar Plan 5 Años a Excel formato directorio",
    description=(
        "Genera el Excel con hojas Supuestos, EERR_Mensual (60 meses), KPIs y Resumen_Anual. "
        "Color coding industry-standard: azul inputs, verde links, negativos en paréntesis."
    ),
    response_class=FileResponse,
    dependencies=[Depends(require_api_key)],
)
def plan_export_endpoint(req: PlanRequest) -> FileResponse:
    params = ParametrosPlan(
        wacc_anual=req.wacc_anual,
        volumen_total_ton_ano=req.volumen_total_ton_ano,
        opex_mensual_clp=req.opex_mensual_clp,
        costo_mmpp_clp_kg=req.costo_mmpp_clp_kg,
    )
    plan = build_plan(params)
    exports_dir = Path("/tmp/trongkai-exports")
    exports_dir.mkdir(parents=True, exist_ok=True)
    out = exports_dir / "Plan_5_Anos_Trongkai.xlsx"
    export_plan_to_excel(plan, out)
    return FileResponse(
        out,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Plan_5_Anos_Trongkai.xlsx",
    )


@app.post(
    "/plan/tornado",
    tags=["financiero"],
    summary="Tornado de sensibilidades del Plan 5 Años",
    description=(
        "Shockea ±20% (default) cada una de las 5 variables clave (WACC, precio promedio, "
        "costo MMPP, OpEx, rendimiento) y devuelve TIR y VAN baja/alta por variable, "
        "ordenado por magnitud de swing TIR. Output listo para gráfico tornado en el dashboard."
    ),
    dependencies=[Depends(require_api_key)],
)
def plan_tornado_endpoint(req: PlanRequest) -> dict:
    params = ParametrosPlan(
        wacc_anual=req.wacc_anual,
        volumen_total_ton_ano=req.volumen_total_ton_ano,
        opex_mensual_clp=req.opex_mensual_clp,
        costo_mmpp_clp_kg=req.costo_mmpp_clp_kg,
    )
    resultados = tornado_sensibilidades(params)
    return {
        "tornado": [
            {
                "variable": r.variable,
                "delta_pct": r.delta_pct,
                "tir_baja": r.tir_baja,
                "tir_alta": r.tir_alta,
                "van_baja": r.van_baja,
                "van_alta": r.van_alta,
            }
            for r in resultados
        ]
    }


# ----- What-If -----


class EscenarioInput(BaseModel):
    nombre: str
    descripcion: str | None = None
    overrides: dict = Field(default_factory=dict)


class WhatIfRequest(BaseModel):
    base: PlanRequest = Field(default_factory=PlanRequest)
    escenarios: list[EscenarioInput]


@app.post(
    "/whatif",
    tags=["financiero"],
    summary="Comparar escenarios what-if",
    description=(
        "Recibe un set de escenarios con overrides sobre ParametrosPlan y devuelve "
        "los KPIs de cada uno + los deltas vs el plan base. Pensado para responder "
        "las 5 preguntas tipo del SUPER_PROMPT (no procesar tomasa, licopeno -30%, etc.)."
    ),
    dependencies=[Depends(require_api_key)],
)
def whatif_endpoint(req: WhatIfRequest) -> dict:
    base_params = ParametrosPlan(
        wacc_anual=req.base.wacc_anual,
        volumen_total_ton_ano=req.base.volumen_total_ton_ano,
        opex_mensual_clp=req.base.opex_mensual_clp,
        costo_mmpp_clp_kg=req.base.costo_mmpp_clp_kg,
    )
    escenarios = [
        Escenario(nombre=e.nombre, descripcion=e.descripcion, overrides=e.overrides)
        for e in req.escenarios
    ]
    cmp = comparar_escenarios(escenarios, base_params=base_params)
    return cmp.to_dict()
