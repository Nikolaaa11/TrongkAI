"""FastAPI app — endpoints REST tipados del motor Trongkai."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .cache import cached_ttl  # noqa: E402 — early import for snapshot caching

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
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
from .depreciation import (
    MetodoDepreciacion,
    RegimenTributario,
    calcular_depreciacion,
    capex_a_activos_default,
    tax_shield,
)
from .escenarios import comparar_escenarios_estrategicos, recomendacion_estrategica
from .financing import (
    EstructuraFinanciamiento,
    TipoAmortizacion,
    calcular_tir_equity,
    coverage_ratios,
    estructurar_financiamiento,
)
from .carbon_footprint import comparar_escenarios_footprint
from .climate_risk import simular_clima_n_corridas
from .macro_chile import get_indicadores, snapshot_resumen
from .compliance_rep import (
    HITOS_LEY_REP,
    costo_compliance_total_clp,
    hitos_por_estado,
    proximos_hitos,
)
from .learning_curve import ahorro_por_aprendizaje_clp
from .slb import KPIS_DEFAULT, SlbBondSpec, simular_kpis_optimista_pesimista
from .monte_carlo import run_monte_carlo, run_monte_carlo_con_clima
from .valuation import valuar_proyecto_ev_ebitda
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
                "tam_clp_anual": r.tam_clp_anual,
                "penetracion_pct_ano5": r.penetracion_pct_ano5,
            }
            for marca, r in plan.por_marca.items()
        },
        "nwc_anuales": plan.nwc_anuales,
        "delta_nwc_anuales": plan.delta_nwc_anuales,
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


# ----- Escenarios estratégicos -----


@app.get(
    "/plan/escenarios-estrategicos",
    tags=["financiero"],
    summary="3 escenarios estratégicos de planta",
    description=(
        "Ejecuta los 3 escenarios canónicos (CONSERVADOR 25k ton, INDUSTRIAL 50k ton, "
        "EXPANSION 80k ton) y devuelve TIR/VAN/CapEx/Payback de cada uno + recomendación "
        "basada en heurística de risk-adjusted VAN. Pensado para decisión de directorio "
        "sobre estrategia de escalamiento."
    ),
    dependencies=[Depends(require_api_key)],
)
def escenarios_estrategicos_endpoint() -> dict:
    escs = comparar_escenarios_estrategicos()
    return {
        "escenarios": [
            {
                "nombre": e.nombre,
                "descripcion": e.descripcion,
                "volumen_objetivo_ton_ano": e.parametros.volumen_total_ton_ano,
                "kpis": {
                    "tir": e.resumen.kpis.tir_proyecto_anual,
                    "van": e.resumen.kpis.van,
                    "payback_meses": e.resumen.kpis.payback_meses,
                    "ebitda_margin": e.resumen.kpis.ebitda_margin_promedio,
                    "ratio_capex": e.resumen.kpis.ratio_capex_ventas,
                },
                "ingresos_anuales": e.resumen.ingresos_anuales,
                "ebitda_anuales": e.resumen.ebitda_anuales,
                "capex_anuales": e.resumen.capex_anuales,
                "capex_total": sum(e.resumen.capex_anuales),
                "por_marca": {
                    marca: {
                        "ingresos_anuales": r.ingresos_anuales,
                        "volumen_ton_anuales": r.volumen_ton_anuales,
                        "penetracion_pct_ano5": r.penetracion_pct_ano5,
                    }
                    for marca, r in e.resumen.por_marca.items()
                },
            }
            for e in escs
        ],
        "recomendacion": recomendacion_estrategica(escs),
    }


# ----- Valoración EV/EBITDA -----


@app.post(
    "/plan/valuation",
    tags=["financiero"],
    summary="Valoración EV/EBITDA año 5 (exit múltiple)",
    description=(
        "Aplica múltiplos EV/EBITDA verificados (food processing 9,63x global Damodaran, "
        "rango ingredientes funcionales 8-12x) al EBITDA año 5 para estimar el valor de "
        "salida del proyecto y MOIC (Multiple Of Invested Capital)."
    ),
    dependencies=[Depends(require_api_key)],
)
def plan_valuation_endpoint(req: PlanRequest) -> dict:
    params = ParametrosPlan(
        wacc_anual=req.wacc_anual,
        volumen_total_ton_ano=req.volumen_total_ton_ano,
        opex_mensual_clp=req.opex_mensual_clp,
        costo_mmpp_clp_kg=req.costo_mmpp_clp_kg,
    )
    plan = build_plan(params)
    v = valuar_proyecto_ev_ebitda(plan)
    return {
        "ebitda_ano5_clp": v.ebitda_ano5_clp,
        "multiple_base": v.multiple_base,
        "multiple_low": v.multiple_low,
        "multiple_high": v.multiple_high,
        "ev_clp_base": v.ev_clp_base,
        "ev_clp_low": v.ev_clp_low,
        "ev_clp_high": v.ev_clp_high,
        "moic_estimado": v.moic_estimado,
        "capex_total_5y_clp": v.capex_total_5y_clp,
        "nota": v.nota,
    }


# ----- Monte Carlo -----


class MonteCarloRequest(BaseModel):
    base: PlanRequest = Field(default_factory=PlanRequest)
    n_runs: int = Field(default=2_000, ge=100, le=20_000)
    seed: int = Field(default=42)


@app.post(
    "/plan/monte-carlo",
    tags=["financiero"],
    summary="Monte Carlo 10k corridas con bandas de confianza TIR",
    description=(
        "Sortea precios SKU (lognormal σ=0.20), WACC (normal σ=0.02), rendimientos por MMPP "
        "(normal σ=0.05), costo MMPP (normal σ=8) y OpEx (normal σ=15M). Devuelve P5/P50/P95 "
        "de TIR y VAN + probabilidad de que el proyecto supere la WACC + histograma TIR. "
        "Default 2.000 corridas (≈4s); para presentación 10.000 (≈20s)."
    ),
    dependencies=[Depends(require_api_key)],
)
def monte_carlo_endpoint(req: MonteCarloRequest) -> dict:
    base_params = ParametrosPlan(
        wacc_anual=req.base.wacc_anual,
        volumen_total_ton_ano=req.base.volumen_total_ton_ano,
        opex_mensual_clp=req.base.opex_mensual_clp,
        costo_mmpp_clp_kg=req.base.costo_mmpp_clp_kg,
    )
    r = run_monte_carlo(base_params=base_params, n_runs=req.n_runs, seed=req.seed)
    return {
        "n_runs": r.n_runs,
        "tir_p5": r.tir_p5,
        "tir_p50": r.tir_p50,
        "tir_p95": r.tir_p95,
        "van_p5": r.van_p5,
        "van_p50": r.van_p50,
        "van_p95": r.van_p95,
        "payback_p50": r.payback_p50,
        "prob_tir_supera_wacc": r.prob_tir_supera_wacc,
        "prob_van_positivo": r.prob_van_positivo,
        "histograma_tir": r.histograma_tir,
        "seed": r.seed,
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


# ----- Depreciación + Tax shield -----


class DepreciacionRequest(BaseModel):
    base: PlanRequest = Field(default_factory=PlanRequest)
    metodo: Literal["NORMAL", "ACELERADA", "INSTANTANEA"] = "NORMAL"
    regimen: Literal["GENERAL", "PROPYME"] = "GENERAL"


@app.post(
    "/plan/depreciation",
    tags=["financiero"],
    summary="Depreciación + tax shield + utilidad neta",
    description=(
        "Aplica depreciación lineal/acelerada/instantánea según DL 824 LIR + tabla SII "
        "Resolución 43/2002 al CapEx del plan. Devuelve cronograma de depreciación, "
        "EBT, impuesto, utilidad neta y tax shield por año. Toggle régimen General (27%) "
        "vs ProPyme 25%."
    ),
    dependencies=[Depends(require_api_key)],
)
def depreciation_endpoint(req: DepreciacionRequest) -> dict:
    params = ParametrosPlan(
        wacc_anual=req.base.wacc_anual,
        volumen_total_ton_ano=req.base.volumen_total_ton_ano,
        opex_mensual_clp=req.base.opex_mensual_clp,
        costo_mmpp_clp_kg=req.base.costo_mmpp_clp_kg,
    )
    plan = build_plan(params)
    metodo = MetodoDepreciacion(req.metodo)
    regimen = RegimenTributario(req.regimen)
    activos = capex_a_activos_default(params.capex_anual_clp, metodo=metodo)
    dep_anual = calcular_depreciacion(activos, horizonte_anos=5)
    shield = tax_shield(plan.ebitda_anuales, dep_anual, regimen=regimen)
    return {
        "metodo": req.metodo,
        "regimen": req.regimen,
        "depreciacion_anual": dep_anual,
        "total_depreciacion_5y": sum(dep_anual),
        **shield,
    }


# ----- Learning curve -----


class LearningCurveRequest(BaseModel):
    base: PlanRequest = Field(default_factory=PlanRequest)
    learning_rate: float = Field(default=0.90, ge=0.5, le=1.0)


@app.post(
    "/plan/learning-curve",
    tags=["financiero"],
    summary="Curva de aprendizaje (Wright's Law) sobre costos de proceso",
    description=(
        "Calcula el ahorro acumulado en costos de etapa aplicando Wright's Law con "
        "learning rate por defecto 0.90 (food processing típico). Cada doblamiento "
        "de volumen acumulado reduce costos unitarios -10%."
    ),
    dependencies=[Depends(require_api_key)],
)
def learning_curve_endpoint(req: LearningCurveRequest) -> dict:
    params = ParametrosPlan(
        wacc_anual=req.base.wacc_anual,
        volumen_total_ton_ano=req.base.volumen_total_ton_ano,
        opex_mensual_clp=req.base.opex_mensual_clp,
        costo_mmpp_clp_kg=req.base.costo_mmpp_clp_kg,
    )
    plan = build_plan(params)
    rendimiento_prom = sum(params.rendimiento_por_mmpp.values()) / len(params.rendimiento_por_mmpp)
    volumen_anual_producto = [
        params.volumen_total_ton_ano * params.volumen_pct_por_ano.get(ano, 1.0) * rendimiento_prom
        for ano in range(1, 6)
    ]
    out = ahorro_por_aprendizaje_clp(
        params.costo_etapa_clp_kg,
        volumen_anual_producto,
        learning_rate=req.learning_rate,
    )
    return out


# ----- Financiamiento -----


class FinanciamientoRequest(BaseModel):
    base: PlanRequest = Field(default_factory=PlanRequest)
    deuda_pct: float = Field(default=0.50, ge=0.0, le=0.85)
    tasa_deuda_anual: float = Field(default=0.095, ge=0.0, le=0.30)
    plazo_deuda_anos: int = Field(default=10, ge=1, le=20)
    grace_anos: int = Field(default=2, ge=0, le=5)
    tasa_equity_required: float = Field(default=0.20, ge=0.0, le=0.50)


@app.post(
    "/plan/financing",
    tags=["financiero"],
    summary="Mix deuda/equity con escudo fiscal + TIR equity + DSCR/LLCR",
    description=(
        "Estructura el financiamiento del proyecto (default 55% deuda CORFO + 45% equity), "
        "calcula servicio de la deuda (amortización francesa), tax shield de intereses, "
        "TIR equity (apalancado) y ratios de cobertura DSCR/LLCR para banca."
    ),
    dependencies=[Depends(require_api_key)],
)
def financing_endpoint(req: FinanciamientoRequest) -> dict:
    params = ParametrosPlan(
        wacc_anual=req.base.wacc_anual,
        volumen_total_ton_ano=req.base.volumen_total_ton_ano,
        opex_mensual_clp=req.base.opex_mensual_clp,
        costo_mmpp_clp_kg=req.base.costo_mmpp_clp_kg,
    )
    plan = build_plan(params)
    capex_anual = list(plan.capex_anuales)
    estructura = EstructuraFinanciamiento(
        deuda_pct=req.deuda_pct,
        tasa_deuda_anual=req.tasa_deuda_anual,
        plazo_deuda_anos=req.plazo_deuda_anos,
        grace_period_anos=req.grace_anos,
        tasa_equity_required=req.tasa_equity_required,
    )
    fin = estructurar_financiamiento(capex_anual, estructura, horizonte=5)

    # Tax shield con intereses
    activos = capex_a_activos_default(params.capex_anual_clp)
    dep_anual = calcular_depreciacion(activos, horizonte_anos=5)
    shield = tax_shield(plan.ebitda_anuales, dep_anual, fin["intereses_anual"], RegimenTributario.GENERAL)

    # Servicio total para coverage
    servicio_anual = [
        i + p for i, p in zip(fin["intereses_anual"], fin["principal_anual"])
    ]
    coverage = coverage_ratios(plan.ebitda_anuales, servicio_anual)

    tir_equity = calcular_tir_equity(
        equity_anual=fin["equity_anual"],
        utilidad_neta_anual=shield["utilidad_neta_anual"],
        principal_anual=fin["principal_anual"],
        valor_residual=plan.ebitda_anuales[4] * 5,  # proxy valor terminal
    )

    return {
        "estructura": fin["estructura"],
        "capex_total_clp": fin["capex_total_clp"],
        "monto_deuda_clp": fin["monto_deuda_clp"],
        "monto_equity_clp": fin["monto_equity_clp"],
        "intereses_anual": fin["intereses_anual"],
        "principal_anual": fin["principal_anual"],
        "saldo_deuda_anual": fin["saldo_deuda_anual"],
        "intereses_totales_clp": fin["intereses_totales_clp"],
        "tax_shield": {
            "anual": shield["tax_shield_anual"],
            "total_5y": shield["total_tax_shield_5y"],
            "utilidad_neta_anual": shield["utilidad_neta_anual"],
        },
        "coverage": coverage,
        "tir_equity_apalancado": tir_equity,
        "valor_residual_proxy_clp": plan.ebitda_anuales[4] * 5,
    }


# ----- Sustainability-Linked Bond -----


class SlbRequest(BaseModel):
    monto_clp: float = Field(default=5_000_000_000, gt=0)
    tasa_base_anual: float = Field(default=0.085, ge=0.05, le=0.20)
    plazo_anos: int = Field(default=7, ge=3, le=15)


@app.post(
    "/plan/slb-simulation",
    tags=["financiero"],
    summary="Sustainability-Linked Bond: caso optimista vs pesimista",
    description=(
        "Simula un Sustainability-Linked Bond con 3 KPIs ESG (toneladas CO2 evitadas, "
        "cuota mercado feed sostenible Chile, reducción uso harina pescado clientes). "
        "Cada KPI fallido suma 20-25 bps al spread (permanente). Devuelve costo extra "
        "entre caso pesimista (todos fallan) y optimista (todos cumplen) — el 'precio "
        "ESG' de la ejecución."
    ),
    dependencies=[Depends(require_api_key)],
)
def slb_endpoint(req: SlbRequest) -> dict:
    bond = SlbBondSpec(
        monto_clp=req.monto_clp,
        tasa_base_anual=req.tasa_base_anual,
        plazo_anos=req.plazo_anos,
        kpis=list(KPIS_DEFAULT),
    )
    return simular_kpis_optimista_pesimista(bond, horizonte=5)


# ----- Compliance Ley REP -----


@app.get(
    "/compliance/rep-calendar",
    tags=["compliance"],
    summary="Calendario de obligaciones Ley REP + Hoja Ruta Circular 2040",
    description=(
        "Hitos regulatorios chilenos relevantes para Trongkai con fecha de vigor, "
        "severidad, acción requerida y costo estimado. Categorizado en VIGENTE/CERCANA/"
        "FUTURA/LEJANA según ventana temporal."
    ),
    dependencies=[Depends(require_api_key)],
)
def rep_calendar_endpoint() -> dict:
    estado = hitos_por_estado()
    proximos = proximos_hitos(n=5)
    costo = costo_compliance_total_clp(ventana_anos=5)

    def hito_to_dict(h):
        return {
            "nombre": h.nombre,
            "fecha_vigor": h.fecha_vigor.isoformat(),
            "fuente": h.fuente,
            "severidad": h.severidad.value,
            "impacto_trongkai": h.impacto_trongkai,
            "accion_requerida": h.accion_requerida,
            "costo_estimado_clp": h.costo_estimado_clp,
        }

    return {
        "total_hitos": len(HITOS_LEY_REP),
        "por_estado": {k: [hito_to_dict(h) for h in v] for k, v in estado.items()},
        "proximos": [hito_to_dict(h) for h in proximos],
        "costo_compliance_5y_clp": costo,
    }


# ----- Riesgo climático -----


class ClimateRequest(BaseModel):
    base: PlanRequest = Field(default_factory=PlanRequest)
    n_runs: int = Field(default=1_000, ge=100, le=10_000)
    seed: int = Field(default=42)


@app.post(
    "/plan/climate-risk",
    tags=["financiero"],
    summary="Riesgo climático: simula impacto en volumen MMPP",
    description=(
        "Sortea ocurrencia anual de 4 eventos climáticos (sequía, helada, granizo, ola de calor) "
        "con probabilidades históricas Chile + afectación por MMPP. Devuelve volumen efectivo "
        "P5/P50/P95 anual + probabilidad de año con evento crítico (>15% pérdida)."
    ),
    dependencies=[Depends(require_api_key)],
)
def climate_risk_endpoint(req: ClimateRequest) -> dict:
    params = ParametrosPlan(
        volumen_total_ton_ano=req.base.volumen_total_ton_ano,
    )
    vols_anuales = [
        params.volumen_total_ton_ano * params.volumen_pct_por_ano.get(ano, 1.0)
        for ano in range(1, 6)
    ]
    r = simular_clima_n_corridas(vols_anuales, n_runs=req.n_runs, seed=req.seed)
    return {
        "n_runs": r.n_runs,
        "volumen_base_anual": vols_anuales,
        "volumen_p5_anual": r.volumen_p5_anual,
        "volumen_p50_anual": r.volumen_p50_anual,
        "volumen_p95_anual": r.volumen_p95_anual,
        "perdida_acumulada_p50_pct": r.perdida_acumulada_p50_pct,
        "perdida_acumulada_p95_pct": r.perdida_acumulada_p95_pct,
        "probabilidad_evento_critico": r.probabilidad_anyear_con_evento_critico,
        "eventos_ejemplo_corrida_1": [
            {
                "ano": e.ano,
                "evento": e.nombre_evento,
                "afectacion": e.afectacion_pct_por_mmpp,
            }
            for e in r.eventos_ejemplo_corrida_1
        ],
    }


# ----- Monte Carlo INTEGRADO precios + clima -----


class MonteCarloIntegradoRequest(BaseModel):
    base: PlanRequest = Field(default_factory=PlanRequest)
    n_runs: int = Field(default=2_000, ge=100, le=20_000)
    seed: int = Field(default=42)
    incluir_clima: bool = True


@app.post(
    "/plan/monte-carlo-integrado",
    tags=["financiero"],
    summary="Monte Carlo integrado: precios + WACC + rendimientos + clima",
    description=(
        "Sortea JUNTOS los riesgos financieros (precios lognormal σ=0.20, WACC normal "
        "σ=0.02, rendimientos σ=0.05, costos σ=8M, OpEx σ=15M) Y los riesgos climáticos "
        "(4 eventos chilenos con probabilidad histórica). Devuelve TIR P5/P50/P95 "
        "considerando ambos riesgos juntos. Esto es lo que un directorio serio quiere ver."
    ),
    dependencies=[Depends(require_api_key)],
)
def monte_carlo_integrado_endpoint(req: MonteCarloIntegradoRequest) -> dict:
    base_params = ParametrosPlan(
        wacc_anual=req.base.wacc_anual,
        volumen_total_ton_ano=req.base.volumen_total_ton_ano,
        opex_mensual_clp=req.base.opex_mensual_clp,
        costo_mmpp_clp_kg=req.base.costo_mmpp_clp_kg,
    )
    return run_monte_carlo_con_clima(
        base_params=base_params,
        n_runs=req.n_runs,
        seed=req.seed,
        incluir_clima=req.incluir_clima,
    )


# ----- Datos macroeconómicos Chile -----


@app.get(
    "/macro/chile",
    tags=["macro"],
    summary="Indicadores económicos Chile en vivo (Banco Central via mindicador.cl)",
    description=(
        "Devuelve los 6 indicadores clave: dólar observado CLP, UF, IPC mensual, "
        "TPM, UTM y tasa desempleo. Cache 24h. Fallback a snapshot si la API "
        "externa cae. Permite recalcular el plan en USD para inversionistas externos."
    ),
)
def macro_chile_endpoint() -> dict:
    return snapshot_resumen()


@app.get(
    "/macro/chile/full",
    tags=["macro"],
    summary="Todos los indicadores macro disponibles",
)
def macro_chile_full_endpoint() -> dict:
    inds = get_indicadores()
    return {
        codigo: {
            "valor": ind.valor,
            "fecha": ind.fecha,
            "unidad_medida": ind.unidad_medida,
            "fuente": ind.fuente,
        }
        for codigo, ind in inds.items()
    }


# ----- Footprint carbono + créditos CO2 -----


class CarbonRequest(BaseModel):
    base: PlanRequest = Field(default_factory=PlanRequest)


@app.post(
    "/plan/carbon-footprint",
    tags=["esg"],
    summary="LCA 3 escenarios (baseline/renovable/BECCS) + revenue créditos CO₂",
    description=(
        "Calcula footprint carbono según literatura (0.79 kg CO₂eq baseline → "
        "0.35 con renovables → -1.05 con BECCS). Suma emisiones EVITADAS por "
        "residuos no descompuestos en vertedero (0.5 ton CO₂eq/ton MMPP). "
        "Revenue potencial de créditos en mercado voluntario (USD 15-80/ton CO₂eq)."
    ),
    dependencies=[Depends(require_api_key)],
)
def carbon_footprint_endpoint(req: CarbonRequest) -> dict:
    params = ParametrosPlan(volumen_total_ton_ano=req.base.volumen_total_ton_ano)
    rendimiento_prom = sum(params.rendimiento_por_mmpp.values()) / len(params.rendimiento_por_mmpp)
    vols_anuales = [
        params.volumen_total_ton_ano * params.volumen_pct_por_ano.get(ano, 1.0)
        for ano in range(1, 6)
    ]
    return comparar_escenarios_footprint(vols_anuales, rendimiento_promedio=rendimiento_prom)


# ----- Snapshot único — agregador para tearsheet PDF / APIs externas -----


@app.get(
    "/api/snapshot",
    tags=["meta"],
    summary="Snapshot completo del plan en una sola llamada",
    description=(
        "Devuelve el estado consolidado: KPIs base + valuation + escenarios estratégicos + "
        "carbon footprint + REP calendar + macro Chile + monte carlo integrado + tornado. "
        "Cacheado 60s para reducir carga (forzar refresh con ?force=true)."
    ),
)
def snapshot_endpoint(force: bool = False) -> dict:
    if not force:
        return _snapshot_cached()
    # Bypass cache
    return _snapshot_build()


@cached_ttl(seconds=60)  # Cache snapshot 60s — alimenta cockpit, PDF, ZIP, digest
def _snapshot_cached() -> dict:
    return _snapshot_build()


def _snapshot_build() -> dict:
    base = ParametrosPlan()
    plan = build_plan(base)
    val = valuar_proyecto_ev_ebitda(plan)
    escs = comparar_escenarios_estrategicos()
    rec = recomendacion_estrategica(escs)

    rendimiento_prom = sum(base.rendimiento_por_mmpp.values()) / len(base.rendimiento_por_mmpp)
    vols_anuales = [
        base.volumen_total_ton_ano * base.volumen_pct_por_ano.get(ano, 1.0)
        for ano in range(1, 6)
    ]
    carbon = comparar_escenarios_footprint(vols_anuales, rendimiento_promedio=rendimiento_prom)

    # Compliance + macro
    rep_hitos = hitos_por_estado()
    proximos = proximos_hitos(n=3)
    costo_compliance = costo_compliance_total_clp(ventana_anos=5)
    macro = snapshot_resumen()

    # Monte Carlo light (300 corridas para no demorar el snapshot)
    mc = run_monte_carlo_con_clima(base, n_runs=300, seed=42, incluir_clima=True)
    tornado = tornado_sensibilidades(base, delta_pct=0.20)

    return {
        "version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plan": {
            "kpis": {
                "tir": plan.kpis.tir_proyecto_anual,
                "van": plan.kpis.van,
                "payback_meses": plan.kpis.payback_meses,
                "ebitda_margin_promedio": plan.kpis.ebitda_margin_promedio,
                "ratio_capex_ventas": plan.kpis.ratio_capex_ventas,
            },
            "ingresos_anuales": plan.ingresos_anuales,
            "ebitda_anuales": plan.ebitda_anuales,
            "capex_anuales": plan.capex_anuales,
            "nwc_anuales": plan.nwc_anuales,
        },
        "valuation": {
            "ebitda_ano5_clp": val.ebitda_ano5_clp,
            "ev_base_clp": val.ev_clp_base,
            "ev_rango_clp": [val.ev_clp_low, val.ev_clp_high],
            "moic": val.moic_estimado,
            "multiplo_base": val.multiple_base,
        },
        "escenarios_estrategicos": {
            "escenarios": [
                {
                    "nombre": e.nombre,
                    "capex_total": sum(e.resumen.capex_anuales),
                    "tir": e.resumen.kpis.tir_proyecto_anual,
                    "van": e.resumen.kpis.van,
                    "payback_meses": e.resumen.kpis.payback_meses,
                }
                for e in escs
            ],
            "recomendacion": rec,
        },
        "carbon_footprint": {
            "baseline": {
                "emisiones_netas_5y_ton": carbon["baseline"]["emisiones_netas_5y_ton"],
                "revenue_creditos_5y_clp": carbon["baseline"]["revenue_creditos_5y_clp"],
                "es_carbono_negativo": carbon["baseline"]["es_carbono_negativo"],
            },
            "beccs": {
                "emisiones_netas_5y_ton": carbon["beccs"]["emisiones_netas_5y_ton"],
                "revenue_creditos_5y_clp": carbon["beccs"]["revenue_creditos_5y_clp"],
            },
        },
        "compliance_rep": {
            "total_hitos": len(HITOS_LEY_REP),
            "vigentes": len(rep_hitos["VIGENTE"]),
            "cercanas": len(rep_hitos["CERCANA"]),
            "proximos_3": [
                {
                    "nombre": h.nombre,
                    "fecha_vigor": h.fecha_vigor.isoformat(),
                    "severidad": h.severidad.value,
                }
                for h in proximos
            ],
            "costo_compliance_5y_clp": costo_compliance["total_clp"],
        },
        "macro_chile": macro,
        "monte_carlo_integrado": {
            "n_runs": mc["n_runs"],
            "tir_p5": mc["tir_p5"],
            "tir_p50": mc["tir_p50"],
            "tir_p95": mc["tir_p95"],
            "prob_tir_supera_wacc": mc["prob_tir_supera_wacc"],
            "prob_van_positivo": mc["prob_van_positivo"],
            "promedio_anos_critico": mc["promedio_anos_critico_por_corrida"],
        },
        "top_3_tornado": [
            {
                "variable": s.variable,
                "tir_baja": s.tir_baja,
                "tir_alta": s.tir_alta,
                "magnitud_tir": s.magnitud_tir,
            }
            for s in tornado[:3]
        ],
        # NUEVO: meta-info para el tearsheet PDF
        "readiness_score": _safe_readiness(),
        "data_room": _safe_data_room(),
        "variables_matrix": _safe_variables_matrix(),
        # NUEVO v2: Decision Engine + Alertas
        "decisiones": _safe_decisiones(),
        "alertas": _safe_alertas(),
        "coherencia": _safe_coherencia(),
        # NUEVO v3: Balances integrales (4 balances + score)
        "balances": _safe_balances(),
        # NUEVO v4: Simulacion operacional + revenue
        "simulacion_planta": _safe_simulacion_planta(),
        # NUEVO v5: Sintesis inteligente cross-modular
        "inteligencia": _safe_sintesis(),
    }


@cached_ttl(seconds=300)
def _safe_decisiones() -> dict | None:
    try:
        from .decision_engine import resumen_decisiones
        r = resumen_decisiones().to_dict()
        # Reducir payload: solo top_5 y stats
        return {
            "top_5": r["top_5"],
            "total_acciones": r["total_acciones"],
            "uplift_potencial_readiness": r["uplift_potencial_readiness"],
            "quick_wins": r["quick_wins"],
        }
    except Exception:
        return None


@cached_ttl(seconds=180)  # Alertas más frecuentes
def _safe_alertas() -> dict | None:
    try:
        from .alertas import escanear_alertas
        return escanear_alertas().to_dict()
    except Exception:
        return None


@cached_ttl(seconds=600)
def _safe_coherencia() -> dict | None:
    try:
        from .matriz_coherence import resumen_coherencia
        return resumen_coherencia().to_dict()
    except Exception:
        return None


@cached_ttl(seconds=600)  # 10 min — Monte Carlo es caro
def _safe_readiness() -> dict | None:
    try:
        from .readiness_score import calcular_readiness_score
        return calcular_readiness_score(n_sims_mc=200).to_dict()
    except Exception:
        return None


@cached_ttl(seconds=600)
def _safe_data_room() -> dict | None:
    try:
        from .data_room import resumen_checklist
        return resumen_checklist().to_dict()
    except Exception:
        return None


@cached_ttl(seconds=600)
def _safe_variables_matrix() -> dict | None:
    try:
        from .variables_matrix import construir_matriz, stats_resumen
        return stats_resumen(construir_matriz())
    except Exception:
        return None


@cached_ttl(seconds=180)
def _safe_sintesis() -> dict | None:
    """Resumen inteligente ligero para el snapshot."""
    try:
        from .balances.sintesis_inteligente import computar_sintesis
        from .balances.precision_tracker import computar_precision
        s = computar_sintesis()
        prec = computar_precision()
        return {
            "score_global_inteligencia": s.score_global_inteligencia,
            "insights_criticos": s.insights_criticos,
            "insights_altos": s.insights_altos,
            "oportunidades": s.oportunidades,
            "amenazas": s.amenazas,
            "resumen_ejecutivo": s.resumen_ejecutivo,
            "exactitud_modelo_pct": round(prec.exactitud_global_pct, 1),
            "nivel_confianza": prec.nivel_confianza,
            "top_3_insights": [
                {"titulo": i.titulo, "severidad": i.severidad, "tipo": i.tipo,
                 "link": i.link_ui}
                for i in s.plan_accion_top_5[:3]
            ],
        }
    except Exception:
        return None


@cached_ttl(seconds=180)
def _safe_simulacion_planta() -> dict | None:
    """Resumen ligero simulacion piloto + escalado para snapshot."""
    try:
        from .balances.simulacion_revenue import simular_con_revenue, calcular_capex_piloto
        s = simular_con_revenue(periodo="ano")
        capex = calcular_capex_piloto()
        return {
            "piloto_t_ano": round(s.producto_total_kg / 1000, 1),
            "costo_anual_clp": round(s.costo_total_clp, 0),
            "revenue_anual_clp": round(s.revenue_total_clp, 0),
            "margen_anual_clp": round(s.margen_total_clp, 0),
            "margen_pct": round(s.margen_pct, 4),
            "costo_unitario_clp_kg": round(s.costo_unitario_clp_kg, 0),
            "precio_venta_clp_kg": s.precio_venta_clp_kg,
            "capex_total_clp": capex["total_clp"],
            "payback_anos": round(s.payback_simple_anos, 2)
                if s.payback_simple_anos != float("inf") else None,
            "es_rentable": s.margen_total_clp > 0,
        }
    except Exception:
        return None


@cached_ttl(seconds=180)
def _safe_balances() -> dict | None:
    """Resumen ligero de los 4 balances para el snapshot/PDF/cockpit."""
    try:
        from .balances.integrado import computar_balance_integrado
        b = computar_balance_integrado()
        return {
            "score_eficiencia_global": b.score_eficiencia_global,
            "alarmas_criticas": sum(
                1 for a in b.alarmas_consolidadas if a.get("severidad") == "critica"
            ),
            "alarmas_total": len(b.alarmas_consolidadas),
            "energia": {
                "consumo_mwh": b.energia["consumo_total_anual_mwh"],
                "mix_renovable_pct": b.energia["mix_renovable_pct"],
                "intensidad_kwh_kg": b.energia["intensidad_energetica_kwh_por_kg_producto"],
                "factor_potencia": b.energia["factor_potencia_planta"],
                "alarmas": len(b.energia["alarmas"]),
            },
            "agua": {
                "consumo_m3": b.agua["consumo_total_anual_m3"],
                "intensidad_l_kg": b.agua["intensidad_hidrica_l_por_kg_producto"],
                "recirculacion_pct": b.agua["agua_recirculada_pct"],
                "alarmas": len(b.agua["alarmas"]),
            },
            "rrhh": {
                "trabajadores": len(b.rrhh["trabajadores"]),
                "utilizacion_pct": b.rrhh["utilizacion_pct"],
                "productividad_kg_hh": b.rrhh["productividad_kg_por_hh"],
                "alarmas_criticas_horas": sum(
                    1 for a in b.rrhh["alarmas"] if a.get("severidad") == "critica"
                ),
                "alarmas_total": len(b.rrhh["alarmas"]),
            },
            "intensidades": b.intensidades,
            "costos_anuales_usd": b.costos_consolidados.get("total_operacional_anual_usd", 0),
        }
    except Exception:
        return None


# ----- Tearsheet PDF ejecutivo -----


@app.get(
    "/api/tearsheet.pdf",
    tags=["meta"],
    summary="Tearsheet PDF ejecutivo (descarga directa)",
    description=(
        "PDF profesional para LP roadshow / directorio. ~3 páginas con KPIs, valoración, "
        "escenarios estratégicos, Monte Carlo, carbono, compliance y macro Chile. "
        "Generado on-demand desde /api/snapshot con reportlab."
    ),
    response_class=FileResponse,
)
def tearsheet_pdf_endpoint() -> FileResponse:
    from datetime import datetime

    from .tearsheet_pdf import generar_tearsheet_pdf

    snap = snapshot_endpoint()
    pdf_bytes = generar_tearsheet_pdf(snap)

    exports_dir = Path("/tmp/trongkai-exports")
    exports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out = exports_dir / f"trongkai_tearsheet_{stamp}.pdf"
    out.write_bytes(pdf_bytes)

    return FileResponse(
        out,
        media_type="application/pdf",
        filename=f"trongkai_tearsheet_{stamp}.pdf",
    )


# ----- Sensitivity heatmap 2D -----


class SensitivityHeatmapRequest(BaseModel):
    """Request al endpoint /sensitivity/heatmap."""

    driver_x: str = "precio"
    driver_y: str = "costo_mmpp"
    n: int = 7
    hurdle_pct: float = 0.15


@app.post(
    "/sensitivity/heatmap",
    tags=["whatif"],
    summary="Heatmap 2D de TIR para combinaciones cross-variable",
    description=(
        "Genera un grid NxN de TIR para combinaciones de dos drivers simultáneos. "
        "Drivers soportados: precio, costo_mmpp, wacc, opex. "
        "Default 7x7=49 simulaciones. Útil para comité de inversión: muestra "
        "'zonas seguras' donde TIR > hurdle."
    ),
)
def sensitivity_heatmap_endpoint(req: SensitivityHeatmapRequest) -> dict:
    from .sensitivity import heatmap_2d

    try:
        res = heatmap_2d(
            driver_x=req.driver_x,  # type: ignore[arg-type]
            driver_y=req.driver_y,  # type: ignore[arg-type]
            n=req.n,
            hurdle_pct=req.hurdle_pct,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return res.to_dict()


# ----- LP Pack ZIP — UN solo archivo con todo -----


@app.get(
    "/api/lp-pack.zip",
    tags=["meta"],
    summary="LP Pack — ZIP con todos los entregables para LP roadshow",
    description=(
        "Descarga UN ZIP con: PDF tearsheet, snapshot JSON, readiness score, "
        "data room checklist, matriz canónica + README. Ideal para mandar a LP "
        "por mail o subir a data room virtual."
    ),
    response_class=FileResponse,
)
def lp_pack_zip_endpoint() -> FileResponse:
    from datetime import datetime
    from .data_room import checklist_completo
    from .lp_pack import generar_lp_pack
    from .sensitivity import heatmap_2d
    from .tearsheet_pdf import generar_tearsheet_pdf
    from .variables_matrix import construir_matriz

    snap = snapshot_endpoint()
    pdf_bytes = generar_tearsheet_pdf(snap)

    # Matriz completa (no solo stats)
    try:
        matriz_full = construir_matriz().to_dict()
    except Exception:
        matriz_full = None

    # Data room completo
    try:
        dr_full = checklist_completo()
    except Exception:
        dr_full = None

    try:
        sens = heatmap_2d(n=5).to_dict()
    except Exception:
        sens = None

    zip_bytes = generar_lp_pack(
        snap=snap,
        readiness=snap.get("readiness_score"),
        data_room=dr_full,
        matriz=matriz_full,
        sensitivity=sens,
        pdf_bytes=pdf_bytes,
    )

    exports_dir = Path("/tmp/trongkai-exports")
    exports_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out = exports_dir / f"Trongkai-LP-Pack-{stamp}.zip"
    out.write_bytes(zip_bytes)

    return FileResponse(
        out,
        media_type="application/zip",
        filename=f"Trongkai-LP-Pack-{stamp}.zip",
    )


# ----- Data Room — checklist Due Diligence para LP -----


@app.get(
    "/data-room/checklist",
    tags=["meta"],
    summary="Checklist Due Diligence completo (41 items)",
    description=(
        "Checklist DD típico para LP / banco / DFI. 6 categorías: corporativo, "
        "financiero, comercial, operacional, ESG, equipo. Cada item: estado "
        "(faltante/parcial/completo), responsable interno, formato esperado."
    ),
)
def data_room_endpoint() -> dict:
    from .data_room import checklist_completo

    return checklist_completo()


# ----- Nutrient Intelligence (perfil cientifico por SKU) -----


@cached_ttl(seconds=3600)
def _nutrient_resumen_cached() -> dict:
    from .nutrient_intelligence import resumen_completo
    return resumen_completo()


@app.get("/nutrientes", tags=["meta"], summary="Resumen del portfolio nutricional")
def nutrient_resumen_endpoint() -> dict:
    """Analisis ejecutivo: TAM total, top aplicaciones, mercados target."""
    return _nutrient_resumen_cached()


@app.get("/nutrientes/perfiles", tags=["meta"], summary="Perfiles cientificos de los 12 SKUs")
def nutrient_perfiles_endpoint() -> dict:
    from .nutrient_intelligence import listar_perfiles
    return {"perfiles": listar_perfiles()}


@app.get("/nutrientes/sku/{sku}", tags=["meta"], summary="Perfil cientifico de un SKU especifico")
def nutrient_sku_endpoint(sku: str) -> dict:
    from .nutrient_intelligence import perfil_por_sku
    p = perfil_por_sku(sku)
    if p is None:
        raise HTTPException(status_code=404, detail=f"SKU {sku} no encontrado")
    return p


# ----- Commercial Intelligence (pricing + concentration + tech ROI + pipeline) -----


@cached_ttl(seconds=600)
def _commercial_intelligence_cached() -> dict:
    from .commercial_intelligence import analisis_comercial_completo
    return analisis_comercial_completo()


@app.get("/commercial/intelligence", tags=["meta"], summary="Análisis comercial integral")
def commercial_intelligence_endpoint() -> dict:
    """Análisis comercial cruzando clientes reales, benchmarks, tech ROI y revenue pipeline."""
    return _commercial_intelligence_cached()


@app.get("/commercial/pricing", tags=["meta"], summary="Pricing power: precios SKU vs benchmarks")
def commercial_pricing_endpoint() -> dict:
    from .commercial_intelligence import analizar_pricing
    return {"pricing": [p.to_dict() for p in analizar_pricing()]}


@app.get("/commercial/concentration", tags=["meta"], summary="HHI concentración clientes")
def commercial_concentration_endpoint() -> dict:
    from .commercial_intelligence import analizar_concentracion
    return analizar_concentracion().to_dict()


@app.get("/commercial/tech-roi", tags=["meta"], summary="ROI por cada tecnología del stack")
def commercial_tech_roi_endpoint() -> dict:
    from .commercial_intelligence import analizar_tech_roi
    return {"tech_roi": [t.to_dict() for t in analizar_tech_roi()]}


# ----- Clientes Reales (catálogo P1) -----


@app.get("/clientes/reales", tags=["meta"], summary="Catálogo de clientes reales identificados en P1")
def clientes_reales_endpoint() -> dict:
    from .clientes_reales import listar_benchmarks, listar_clientes, resumen_clientes
    return {
        "clientes": listar_clientes(),
        "benchmarks_proteinas": listar_benchmarks(),
        "resumen": resumen_clientes(),
    }


# ----- Tecnologías (catálogo Opticept, Infrasonido, Micromolienda) -----


@app.get("/tecnologias", tags=["meta"], summary="Catálogo de tecnologías de la planta Trongkai")
def tecnologias_endpoint() -> dict:
    from .tecnologias_catalog import listar_tecnologias, resumen_tecnologias
    return {
        "tecnologias": listar_tecnologias(),
        "resumen": resumen_tecnologias(),
    }


# ----- Roadmap Timeline -----


@app.get(
    "/roadmap",
    tags=["meta"],
    summary="Roadmap consolidado de próximos hitos (12 meses)",
    description=(
        "Timeline cronológico con compliance REP, LP pipeline, decisiones top, "
        "certificaciones esperadas. Agrupado por mes."
    ),
)
def roadmap_endpoint(meses: int = 12) -> dict:
    from .roadmap import construir_roadmap
    return construir_roadmap(meses_adelante=meses)


# ----- Inbox Status -----


class InboxSyncRequest(BaseModel):
    archivos: dict = Field(default_factory=dict)
    version: int = 1


@app.post(
    "/inbox/sync",
    tags=["meta"],
    summary="Sincroniza inbox/_index.json local al engine (called from procesar_inbox.py)",
    description=(
        "Recibe el índice del inbox local y lo persiste en /tmp del engine. "
        "Permite que /inbox/status muestre estado actualizado desde la web pública."
    ),
)
def inbox_sync_endpoint(req: InboxSyncRequest) -> dict:
    import json
    from datetime import datetime, timezone
    from pathlib import Path
    from .storage import data_path
    out = data_path("inbox-index.json")
    payload = {
        "archivos": req.archivos,
        "version": req.version,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {"synced": True, "total_archivos": len(req.archivos), "path": str(out)}


@app.get(
    "/inbox/status",
    tags=["meta"],
    summary="Estado del inbox (archivos por categoría + sugerencias)",
    description=(
        "Devuelve stats del inbox. Primero busca /tmp/trongkai-inbox-index.json (sync), "
        "luego inbox/_index.json del repo."
    ),
)
def inbox_status_endpoint() -> dict:
    import json
    from pathlib import Path
    # Prioridad: 1) sync /tmp, 2) inbox local
    from .storage import data_path
    INDEX_PATHS = [
        data_path("inbox-index.json"),  # Volume persistente (/data o /tmp fallback)
        Path("/tmp/trongkai-inbox-index.json"),  # Legacy
        Path("/app/inbox/_index.json"),
        Path(__file__).parent.parent.parent.parent / "inbox" / "_index.json",
    ]
    for p in INDEX_PATHS:
        if p.exists():
            try:
                idx = json.loads(p.read_text(encoding="utf-8"))
                archivos = list(idx.get("archivos", {}).values())
                por_cat: dict[str, int] = {}
                por_subcat: dict[str, int] = {}
                sugerencias_total = 0
                ultimos: list[dict] = []
                for e in archivos:
                    cat = e.get("categoria", "?")
                    sub = f"{cat}/{e.get('subcategoria', '?')}"
                    por_cat[cat] = por_cat.get(cat, 0) + 1
                    por_subcat[sub] = por_subcat.get(sub, 0) + 1
                    sugerencias_total += len(e.get("sugerencias", []))
                # Más recientes primero
                archivos_sorted = sorted(
                    archivos,
                    key=lambda e: e.get("fecha_procesado", ""),
                    reverse=True,
                )
                ultimos = archivos_sorted[:10]
                return {
                    "total": len(archivos),
                    "por_categoria": por_cat,
                    "por_subcategoria": por_subcat,
                    "sugerencias_totales": sugerencias_total,
                    "ultimos_10": ultimos,
                }
            except Exception:
                pass
    return {
        "total": 0,
        "por_categoria": {},
        "por_subcategoria": {},
        "sugerencias_totales": 0,
        "ultimos_10": [],
        "nota": "No se encontró inbox/_index.json (procesar primero con scripts/procesar_inbox.py)",
    }


# ----- Sistema de Notas -----


class NotaCrearRequest(BaseModel):
    entidad_tipo: str
    entidad_id: str
    texto: str
    autor: str = "Nicolás"
    tags: list[str] = []


class NotaActualizarRequest(BaseModel):
    texto: str | None = None
    tags: list[str] | None = None


@app.get("/notas", tags=["meta"], summary="Lista notas, opcionalmente por entidad")
def notas_list_endpoint(entidad_tipo: str | None = None, entidad_id: str | None = None) -> dict:
    from .notas import listar_notas_de, stats_notas
    return {
        "notas": listar_notas_de(entidad_tipo, entidad_id),
        "stats": stats_notas(),
    }


@app.post("/notas", tags=["meta"], summary="Crea una nota nueva")
def notas_crear_endpoint(req: NotaCrearRequest) -> dict:
    from .notas import crear_nota
    return crear_nota(req.entidad_tipo, req.entidad_id, req.texto, req.autor, req.tags)


@app.patch("/notas/{nota_id}", tags=["meta"], summary="Actualiza una nota")
def notas_update_endpoint(nota_id: str, req: NotaActualizarRequest) -> dict:
    from .notas import actualizar_nota
    n = actualizar_nota(nota_id, req.texto, req.tags)
    if not n:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return n


@app.delete("/notas/{nota_id}", tags=["meta"], summary="Elimina una nota")
def notas_delete_endpoint(nota_id: str) -> dict:
    from .notas import eliminar_nota
    return {"deleted": eliminar_nota(nota_id)}


# ----- System Health -----


@app.get("/healthz", tags=["meta"], summary="Health check rápido (load balancer)", include_in_schema=False)
def healthz_endpoint() -> dict:
    """Ultra-rápido (<5ms): no toca módulos pesados. Para LB / monitoring."""
    return {"ok": True, "service": "trongkai-engine"}


@app.get("/health/full", tags=["meta"], summary="Reporte completo de salud del sistema")
def system_health_endpoint() -> dict:
    from .system_health import system_health_report
    return system_health_report()


# ----- Pipeline LP (CRM) -----


@app.get("/lp/pipeline", tags=["meta"], summary="Lista todos los LPs del pipeline")
def lp_list_endpoint() -> dict:
    from .pipeline_lp import list_lps, resumen_pipeline
    return {
        "lps": list_lps(),
        "resumen": resumen_pipeline().to_dict(),
    }


class LPUpsertRequest(BaseModel):
    id: str | None = None
    nombre: str
    tipo: str = "fondo"
    pais: str = "Chile"
    ticket_esperado_usd: float = 0
    etapa: str = "prospect"
    prob_cierre: float = 0
    proxima_accion: str = ""
    proxima_accion_owner: str = ""
    proxima_accion_fecha: str = ""
    notas: str = ""
    fecha_ultimo_contacto: str = ""


@app.post("/lp/upsert", tags=["meta"], summary="Crea o actualiza un LP en el pipeline")
def lp_upsert_endpoint(req: LPUpsertRequest) -> dict:
    from .pipeline_lp import upsert_lp
    data = req.model_dump(exclude_none=True)
    return upsert_lp(data)


@app.delete("/lp/{lp_id}", tags=["meta"], summary="Elimina un LP del pipeline")
def lp_delete_endpoint(lp_id: str) -> dict:
    from .pipeline_lp import delete_lp
    return {"deleted": delete_lp(lp_id)}


# ----- Snapshot Diff -----


@app.get("/snapshot/diff", tags=["meta"], summary="Compara snapshot actual con uno anterior")
def snapshot_diff_endpoint(dias_atras: int = 7) -> dict:
    """Compara snapshot live con uno hace N días (usando readiness_history como proxy)."""
    from datetime import datetime, timedelta, timezone
    from .readiness_history import get_history
    from .snapshot_diff import comparar_snapshots

    actual = snapshot_endpoint()
    hist = get_history(limit=200)
    if not hist:
        return {
            "error": "Sin historial — registra un snapshot antes con POST /readiness/snapshot",
            "diff_disponible": False,
        }
    # Buscar el entry más cercano a hace_N_dias
    cutoff = (datetime.now(timezone.utc) - timedelta(days=dias_atras)).isoformat()
    entry_anterior = None
    for h in reversed(hist):
        if h.get("timestamp", "") <= cutoff:
            entry_anterior = h
            break
    if not entry_anterior:
        entry_anterior = hist[0]  # El más viejo disponible

    # Construir snapshot-like del entry anterior (limitado)
    snap_anterior = {
        "generated_at": entry_anterior.get("timestamp", ""),
        "readiness_score": {"score_total": entry_anterior.get("score")},
        # Para los demás campos no tenemos histórico — usamos defaults
    }

    diff = comparar_snapshots(snap_anterior, actual)
    return diff.to_dict()


# ----- Audit Trail -----


@app.get("/audit/trail", tags=["meta"], summary="Historial de cambios al modelo")
def audit_trail_endpoint(limit: int = 50, tipo: str | None = None) -> dict:
    from .audit_trail import get_audit_trail, stats_audit_trail
    return {
        "entries": get_audit_trail(limit=limit, tipo=tipo),
        "stats": stats_audit_trail(),
    }


class LogEventoRequest(BaseModel):
    tipo: str
    descripcion: str
    actor: str = "system"
    valor_anterior: Any = None
    valor_nuevo: Any = None
    metadata: dict | None = None
    impacto_estimado: str | None = None


@app.post("/audit/log", tags=["meta"], summary="Registra un evento en el audit trail")
def audit_log_endpoint(req: LogEventoRequest) -> dict:
    from .audit_trail import log_evento
    entrada = log_evento(
        tipo=req.tipo,
        descripcion=req.descripcion,
        actor=req.actor,
        valor_anterior=req.valor_anterior,
        valor_nuevo=req.valor_nuevo,
        metadata=req.metadata,
        impacto_estimado=req.impacto_estimado,
    )
    return {"logged": True, "entry": entrada.to_dict()}


# ----- Weekly Digest HTML -----


@app.get(
    "/weekly-digest.html",
    tags=["meta"],
    summary="Genera el HTML del digest semanal (Apple style)",
    description=(
        "Resumen ejecutivo semanal listo para mandar por email. "
        "Incluye score con delta, top 3 acciones, alertas, progreso, audit trail."
    ),
    response_class=HTMLResponse,
)
def weekly_digest_endpoint() -> HTMLResponse:
    from .audit_trail import get_audit_trail
    from .readiness_history import get_history
    from .weekly_digest import generar_weekly_digest

    snap = snapshot_endpoint()
    # Score anterior: 7 días atrás
    hist = get_history(limit=20)
    from datetime import datetime, timedelta, timezone
    hace_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    score_anterior = None
    for h in reversed(hist):
        if h.get("timestamp", "") < hace_7d:
            score_anterior = h.get("score")
            break
    # Audit últimos 7 días
    audit_semana = [e for e in get_audit_trail(limit=200) if e.get("timestamp", "") >= hace_7d]

    html = generar_weekly_digest(snap, score_anterior=score_anterior, audit_entries_semana=audit_semana)
    return HTMLResponse(content=html)


# ----- Multi-Scenario Comparator -----


@app.get(
    "/scenarios/compare",
    tags=["whatif"],
    summary="Compara los 3 escenarios estratégicos lado a lado",
    description="CONSERVADOR vs INDUSTRIAL vs EXPANSION con ranking por métrica + recomendación.",
)
def scenarios_compare_endpoint() -> dict:
    from .scenario_comparator import comparar_estrategicos
    return comparar_estrategicos().to_dict()


# ----- Cache management -----


@app.get("/cache/stats", tags=["meta"], summary="Estado del cache in-memory")
def cache_stats_endpoint() -> dict:
    from .cache import cache_stats
    return cache_stats()


@app.post("/cache/clear", tags=["meta"], summary="Limpia todo el cache (forza recálculo)")
def cache_clear_endpoint() -> dict:
    from .cache import clear_all
    n = clear_all()
    return {"cleared": True, "entries_removed": n}


# ----- Sistema de Alertas Inteligentes -----


@app.get(
    "/alertas",
    tags=["meta"],
    summary="Alertas activas detectadas en todo el sistema",
    description=(
        "Escanea TODOS los módulos (plan, sensitivity, breakeven, compliance, "
        "carbon, modelo, progreso) y devuelve alertas ordenadas por severidad."
    ),
)
@cached_ttl(seconds=180)
def alertas_endpoint() -> dict:
    from .alertas import escanear_alertas

    return escanear_alertas().to_dict()


# ----- Decision Engine — cerebro central -----


@app.get(
    "/decisiones/top",
    tags=["meta"],
    summary="Top 5 acciones priorizadas por el motor de decisiones",
    description=(
        "Decision Engine que combina TODA la red (variables, data room, "
        "coherencia, breakeven, readiness, sensitivity) y produce 5 acciones "
        "priorizadas por: impacto TIR + sinergia + uplift readiness + quick-win + urgencia."
    ),
)
@cached_ttl(seconds=300)
def decisiones_top_endpoint() -> dict:
    from .decision_engine import resumen_decisiones

    return resumen_decisiones().to_dict()


# ----- Intelligence Graph — dependencias entre módulos -----


@app.get(
    "/graph/modulos",
    tags=["meta"],
    summary="Grafo de dependencias entre módulos del modelo",
    description=(
        "Mapa de cómo se conectan los módulos: inputs → matrices → cálculos → "
        "outputs. Útil para visualización tipo network graph."
    ),
)
def graph_modulos_endpoint() -> dict:
    from .intelligence_graph import grafo_completo

    return grafo_completo()


@app.get(
    "/graph/impacto/{modulo}",
    tags=["meta"],
    summary="Qué otros módulos se afectan si cambia uno (cascada)",
)
def graph_impacto_endpoint(modulo: str, profundidad: int = 3) -> dict:
    from .intelligence_graph import impacto_de_cambio

    impactados = impacto_de_cambio(modulo, profundidad=profundidad)
    return {"modulo_origen": modulo, "impactados": impactados, "profundidad": profundidad}


# ----- Coherencia Cross-Matriz -----


@app.get(
    "/matriz/coherencia",
    tags=["meta"],
    summary="Auditoría cruzada entre todas las matrices del modelo",
    description=(
        "Detecta gaps que aparecen simultáneamente en múltiples matrices "
        "(variables, data room, readiness, compliance). Prioriza por sinergia: "
        "los gaps que más se resuelven con una sola acción primero."
    ),
)
def matriz_coherencia_endpoint() -> dict:
    from .matriz_coherence import resumen_coherencia

    return resumen_coherencia().to_dict()


# ----- Sensitivity 3D -----


@app.get(
    "/sensitivity/heatmap-3d",
    tags=["whatif"],
    summary="Heatmap 3D para 3 drivers simultáneos",
    description=(
        "TIR para combinaciones cross-3-variables. Default 5x5x5 = 125 sims (~8s)."
    ),
)
def sensitivity_3d_endpoint(
    driver_x: str = "precio",
    driver_y: str = "costo_mmpp",
    driver_z: str = "wacc",
    n: int = 5,
    hurdle_pct: float = 0.15,
) -> dict:
    from .sensitivity import heatmap_3d

    try:
        res = heatmap_3d(
            driver_x=driver_x,  # type: ignore[arg-type]
            driver_y=driver_y,  # type: ignore[arg-type]
            driver_z=driver_z,  # type: ignore[arg-type]
            n=n,
            hurdle_pct=hurdle_pct,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return res.to_dict()


# ----- Variables Intelligence (auto-validación + sugerencias) -----


@app.get(
    "/variables/intelligence",
    tags=["meta"],
    summary="Análisis inteligente de la matriz: inconsistencias + sugerencias",
    description=(
        "Capa de inteligencia sobre la matriz canónica. Detecta inconsistencias "
        "matemáticas/lógicas, sugiere valores para celdas PD basado en celdas "
        "similares + benchmarks, y calcula confianza promedio por grupo de producto."
    ),
)
def variables_intelligence_endpoint() -> dict:
    from .variables_intelligence import analisis_inteligente

    return analisis_inteligente().to_dict()


class SimularCambioRequest(BaseModel):
    variable: str
    producto: str
    valor_nuevo: float


@app.post(
    "/variables/simular-cambio",
    tags=["meta"],
    summary="Simula cambio de una celda y mide impacto TIR/VAN",
    description=(
        "What-if a nivel celda: cambia (variable, producto) a valor_nuevo "
        "y devuelve el impacto en TIR (pp) y VAN (%)."
    ),
)
def simular_cambio_celda_endpoint(req: SimularCambioRequest) -> dict:
    from .variables_intelligence import simular_cambio_celda

    impacto = simular_cambio_celda(
        variable=req.variable,
        producto=req.producto,
        valor_nuevo=req.valor_nuevo,
    )
    return impacto.to_dict()


# ----- Matriz Variables (canónica del Excel original) -----


@app.get(
    "/variables/matrix",
    tags=["meta"],
    summary="Matriz canónica 11 productos x 15 variables del Excel original",
    description=(
        "Replica la matriz del Excel 'Variables Ingredientes Plan 5 Años'. "
        "Cada celda tiene estado PD (Por Definir) / OK_PROVISORIO / OK_VALIDADO. "
        "Útil para trazabilidad de supuestos ante directorio y due diligence."
    ),
)
def variables_matrix_endpoint() -> dict:
    from .variables_matrix import construir_matriz

    return construir_matriz().to_dict()


# ----- Investment Readiness Score -----


@cached_ttl(seconds=600)  # 10 min - Monte Carlo es caro
def _readiness_cached(n_sims_mc: int) -> dict:
    from .readiness_score import calcular_readiness_score
    return calcular_readiness_score(n_sims_mc=n_sims_mc).to_dict()


@app.get(
    "/readiness/score",
    tags=["meta"],
    summary="Investment Readiness Score (IRS) — score 0-100 de madurez del proyecto",
    description=(
        "Sintetiza 8 dimensiones (retorno, robustez MC, bancabilidad, diversificación, "
        "ESG, compliance, resiliencia, madurez operativa) en un score único 0-100. "
        "Útil para LP roadshow / comité de inversión. "
        "Score ≥ 80: bankable. 60-79: prometedor. 40-59: oportunidad. <40: re-think."
    ),
)
def readiness_score_endpoint(n_sims_mc: int = 500, save_history: bool = False) -> dict:
    from .readiness_history import add_snapshot

    if n_sims_mc < 100 or n_sims_mc > 5000:
        raise HTTPException(status_code=400, detail="n_sims_mc debe estar entre 100 y 5000")
    # Usar cache: misma n_sims_mc → mismo resultado por 10 min (TTL del _readiness_cached)
    result = _readiness_cached(n_sims_mc)
    if save_history:
        try:
            add_snapshot(result, evento="manual /readiness/score?save_history=true")
        except Exception:
            pass
    return result


@app.get(
    "/readiness/history",
    tags=["meta"],
    summary="Histórico del Investment Readiness Score",
    description="Devuelve los últimos N snapshots del score + stats de progreso.",
)
def readiness_history_endpoint(limit: int = 30) -> dict:
    from .readiness_history import get_evolucion_compacta, get_history, stats_progreso

    return {
        "evolucion_compacta": get_evolucion_compacta(limit=limit),
        "history": get_history(limit=limit),
        "stats": stats_progreso(),
    }


@app.post(
    "/readiness/snapshot",
    tags=["meta"],
    summary="Guarda un snapshot del readiness score en el histórico",
    description="Útil para marcar hitos del proyecto (LOI firmada, cotización recibida, etc).",
)
def readiness_snapshot_endpoint(evento: str = "") -> dict:
    from .readiness_history import add_snapshot
    from .readiness_score import calcular_readiness_score

    rs = calcular_readiness_score(n_sims_mc=200).to_dict()
    entry = add_snapshot(rs, evento=evento)
    return {"saved": True, "entry": entry}


# ----- Break-even analysis -----


@app.get(
    "/sensitivity/curves",
    tags=["whatif"],
    summary="Curvas 1D de TIR vs shock para los 4 drivers (small multiples)",
    description=(
        "Genera 4 curvas TIR vs shock (precio, costo_mmpp, wacc, opex). "
        "Útil para visualizar la elasticidad de cada driver individualmente. "
        "Complementa el heatmap 2D y el break-even analysis."
    ),
)
def sensitivity_curves_endpoint(n: int = 11) -> dict:
    from .sensitivity import curvas_todos_drivers

    if n < 3 or n > 25:
        raise HTTPException(status_code=400, detail="n debe estar entre 3 y 25")
    return curvas_todos_drivers(n=n)


@app.get(
    "/sensitivity/breakeven",
    tags=["whatif"],
    summary="Análisis break-even por driver (colchón frente a hurdle)",
    description=(
        "Para cada driver (precio, costo_mmpp, wacc, opex), encuentra por bisección "
        "el shock máximo soportable antes de que TIR caiga bajo el umbral indicado. "
        "Útil para identificar el driver más sensible y dimensionar el riesgo del proyecto."
    ),
)
def breakeven_endpoint(umbral_tir: float = 0.15) -> dict:
    from .breakeven import breakeven_summary

    if not 0 < umbral_tir < 1:
        raise HTTPException(status_code=400, detail="umbral_tir debe estar entre 0 y 1")
    return breakeven_summary(umbral_tir=umbral_tir).to_dict()


# =============================================================================
# BALANCES INTEGRALES (energia, agua, rrhh, integrado)
# =============================================================================
@app.get("/balance/energia", tags=["balances"], summary="Balance energetico anual (Sankey + alarmas)")
@cached_ttl(seconds=120)
def balance_energia_endpoint(produccion_anual_kg: float = 850_000.0) -> dict:
    from .balances.energia import balance_a_sankey, cargar_flujos, computar_balance_energia

    flujos = cargar_flujos()
    b = computar_balance_energia(flujos, produccion_anual_kg=produccion_anual_kg)
    out = b.to_dict()
    out["sankey"] = balance_a_sankey(b)
    return out


@app.get("/balance/energia/sankey", tags=["balances"], summary="Solo el Sankey energetico")
def balance_energia_sankey_endpoint(produccion_anual_kg: float = 850_000.0) -> dict:
    from .balances.energia import balance_a_sankey, cargar_flujos, computar_balance_energia

    b = computar_balance_energia(cargar_flujos(), produccion_anual_kg=produccion_anual_kg)
    return balance_a_sankey(b)


@app.get("/balance/agua", tags=["balances"], summary="Balance hidrico anual + cumplimiento DGA")
@cached_ttl(seconds=120)
def balance_agua_endpoint(produccion_anual_kg: float = 850_000.0) -> dict:
    from .balances.agua import balance_a_sankey, cargar_flujos_agua, computar_balance_agua

    flujos = cargar_flujos_agua()
    b = computar_balance_agua(flujos, produccion_anual_kg=produccion_anual_kg)
    out = b.to_dict()
    out["sankey"] = balance_a_sankey(b)
    return out


@app.get("/balance/agua/sankey", tags=["balances"], summary="Solo el Sankey hidrico")
def balance_agua_sankey_endpoint(produccion_anual_kg: float = 850_000.0) -> dict:
    from .balances.agua import balance_a_sankey, cargar_flujos_agua, computar_balance_agua

    b = computar_balance_agua(cargar_flujos_agua(), produccion_anual_kg=produccion_anual_kg)
    return balance_a_sankey(b)


@app.get("/balance/agua/cumplimiento-dga", tags=["balances"], summary="Estado derechos DGA")
def balance_agua_dga_endpoint() -> dict:
    from .balances.agua import cargar_flujos_agua, computar_balance_agua

    b = computar_balance_agua(cargar_flujos_agua())
    return b.cumplimiento_dga


@app.get(
    "/balance/rrhh",
    tags=["balances"],
    summary="Balance RRHH + alarmas horas extras (CT Chile)",
    description="Devuelve trabajadores, asignaciones de la semana, alarmas criticas si hay extras > 12h/sem o totales > 57h.",
)
@cached_ttl(seconds=60)
def balance_rrhh_endpoint(semana: str | None = None) -> dict:
    from .balances.rrhh import (
        cargar_asignaciones,
        cargar_trabajadores,
        computar_balance_rrhh,
    )

    sem = semana or "2026-W23"
    trabs = cargar_trabajadores()
    asigs = cargar_asignaciones(sem)
    b = computar_balance_rrhh(trabajadores=trabs, asignaciones=asigs, semana=sem)
    return b.to_dict()


@app.get(
    "/balance/rrhh/alarmas",
    tags=["balances"],
    summary="Solo alarmas criticas RRHH (para dashboard)",
)
def balance_rrhh_alarmas_endpoint(semana: str | None = None) -> dict:
    from .balances.rrhh import (
        cargar_asignaciones,
        cargar_trabajadores,
        detectar_alarmas,
    )

    sem = semana or "2026-W23"
    asigs = cargar_asignaciones(sem)
    al = detectar_alarmas(asigs, cargar_trabajadores())
    criticas = [a for a in al if a["severidad"] == "critica"]
    return {
        "semana": sem,
        "total_alarmas": len(al),
        "criticas": len(criticas),
        "altas": sum(1 for a in al if a["severidad"] == "alta"),
        "alarmas": al,
    }


class AsignacionRequest(BaseModel):
    trabajador_id: str
    semana_iso: str
    horas_regulares: float
    horas_extras: float = 0.0
    tareas: list[str] = Field(default_factory=list)
    equipo_asignado: str = ""


@app.post(
    "/balance/rrhh/asignar",
    tags=["balances"],
    summary="Asignar horas a un trabajador (siempre devuelve alarmas)",
)
def balance_rrhh_asignar_endpoint(req: AsignacionRequest) -> dict:
    from .balances.rrhh import (
        AsignacionHoras,
        cargar_asignaciones,
        cargar_trabajadores,
        detectar_alarmas,
        guardar_asignaciones,
    )
    from .cache import clear_all

    nueva = AsignacionHoras(
        trabajador_id=req.trabajador_id,
        semana_iso=req.semana_iso,
        horas_regulares=req.horas_regulares,
        horas_extras=req.horas_extras,
        tareas=req.tareas,
        equipo_asignado=req.equipo_asignado,
    )
    todas = cargar_asignaciones()
    # Reemplazar si existe para misma semana + trabajador
    todas = [
        a for a in todas
        if not (a.trabajador_id == nueva.trabajador_id and a.semana_iso == nueva.semana_iso)
    ]
    todas.append(nueva)
    guardar_asignaciones(todas)
    clear_all()  # invalida cache balances

    al = detectar_alarmas([nueva], cargar_trabajadores())
    return {
        "ok": True,
        "asignacion": nueva.to_dict(),
        "alarmas_disparadas": al,
        "tiene_alarma_critica": any(a["severidad"] == "critica" for a in al),
    }


@app.get(
    "/balance/integrado",
    tags=["balances"],
    summary="Los 4 balances integrados + cross-checks + score eficiencia global",
)
@cached_ttl(seconds=120)
def balance_integrado_endpoint(produccion_anual_kg: float = 850_000.0) -> dict:
    from .balances.integrado import computar_balance_integrado

    b = computar_balance_integrado(produccion_anual_kg=produccion_anual_kg)
    return b.to_dict()


@app.get(
    "/balance/etapas",
    tags=["balances"],
    summary="Balance por cada una de las etapas reales de la planta Agrosphere",
    description="Dinamico: cambiando throughput_kg_h recalcula los consumos por etapa, "
                "yield acumulado, bottlenecks, tiempos y completitud de datos. "
                "incluir_respaldo=true usa E6(b) Deshidratacion Respaldo (tiempo 150 min vs 120).",
)
@cached_ttl(seconds=60)
def balance_etapas_endpoint(
    throughput_kg_h: float = 2000.0,
    incluir_respaldo: bool = False,
) -> dict:
    from .balances.etapas import computar_balance_etapas

    if throughput_kg_h <= 0 or throughput_kg_h > 20_000:
        raise HTTPException(400, "throughput_kg_h debe estar entre 0 y 20000")
    return computar_balance_etapas(
        throughput_kg_h=throughput_kg_h,
        incluir_respaldo=incluir_respaldo,
    ).to_dict()


@app.get(
    "/balance/etapas/datos-faltantes",
    tags=["balances"],
    summary="Checklist de datos faltantes por etapa (para calibracion)",
)
def balance_etapas_datos_faltantes_endpoint() -> dict:
    from .balances.etapas import resumen_datos_faltantes
    return resumen_datos_faltantes()


@app.get(
    "/balance/etapas/productos",
    tags=["balances"],
    summary="Matriz productos x etapas (que MMPP pasa por que etapa + yield MSF)",
    description="Cuadro Etapas x Productos del Excel Agrosphere. "
                "Mapea cada MMPP/SKU a las etapas que aplica y calcula yield acumulado.",
)
def balance_productos_etapas_endpoint() -> dict:
    from .balances.etapas import matriz_productos_x_etapas
    return matriz_productos_x_etapas()


# =============================================================================
# PARAMETROS PLANTA + COSTEO
# =============================================================================
@app.get(
    "/parametros",
    tags=["parametros"],
    summary="Planilla variables (sueldos, energia, calor residual, agua, flete, arriendos)",
)
def parametros_get_endpoint() -> dict:
    from .balances.parametros_planta import cargar_parametros
    return cargar_parametros().to_dict()


class ParametrosUpdateRequest(BaseModel):
    """Update parcial. Solo los campos enviados se actualizan."""
    sueldos: list[dict] | None = None
    energia: dict | None = None
    calor_residual: dict | None = None
    agua: dict | None = None
    flete: dict | None = None
    arriendos: dict | None = None
    perdida_mmpp_global_pct: float | None = None
    usd_clp_referencia: float | None = None


@app.post(
    "/parametros/actualizar",
    tags=["parametros"],
    summary="Actualizar parametros variables planta (persistente en /data)",
)
def parametros_update_endpoint(req: ParametrosUpdateRequest) -> dict:
    from .balances.parametros_planta import actualizar_parametros
    from .cache import clear_all
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No se enviaron campos para actualizar")
    actualizados = actualizar_parametros(updates)
    clear_all()  # invalida cache de costeo
    return {"ok": True, "actualizado": actualizados.to_dict()}


@app.get(
    "/parametros/humedades-mmpp",
    tags=["parametros"],
    summary="Humedades de ingreso por MMPP (Tomasa, Orujo, Alperujo, Pomasa)",
)
def parametros_humedades_endpoint() -> dict:
    from .balances.humedades_mmpp import listar_humedades
    return {"humedades": listar_humedades(), "fuente": "Conversacion equipo 04/06/2026"}


@app.get(
    "/costeo/etapas",
    tags=["balances"],
    summary="Costeo completo por etapa y por SKU usando parametros actuales",
    description="MO + energia + calor residual + agua + materiales + arriendo PEF/Tricanter. "
                "Resultado en CLP/kg y USD/kg por SKU.",
)
@cached_ttl(seconds=120)
def costeo_etapas_endpoint(
    throughput_kg_h: float = 2000.0,
    incluir_respaldo: bool = False,
) -> dict:
    from .balances.costeo_etapas import computar_costeo_completo
    return computar_costeo_completo(
        throughput_kg_h=throughput_kg_h,
        incluir_respaldo=incluir_respaldo,
    )


# =============================================================================
# ANALISIS PEF (responde la pregunta 3 del usuario)
# =============================================================================
@app.get(
    "/pef/analisis",
    tags=["balances"],
    summary="Analisis economico PEF vs Prensado directo (A/B)",
    description="Responde: justifica economicamente usar PEF? "
                "Compara con/sin PEF + breakeven + sensibilidad % reduccion secado.",
)
@cached_ttl(seconds=120)
def pef_analisis_endpoint(
    throughput_kg_h: float = 2000.0,
    pct_reduccion_tiempo_secado: float = 0.30,
    pct_uplift_yield: float = 0.05,
    pasadas_pef: int = 1,
    precio_venta_clp_kg: float = 850.0,
    pct_premium_pef: float = 0.10,
) -> dict:
    from .balances.pef_analisis import analizar_pef_vs_sin_pef
    return analizar_pef_vs_sin_pef(
        throughput_kg_h=throughput_kg_h,
        pct_reduccion_tiempo_secado=pct_reduccion_tiempo_secado,
        pct_uplift_yield=pct_uplift_yield,
        pasadas_pef=pasadas_pef,
        precio_venta_clp_kg=precio_venta_clp_kg,
        pct_premium_pef=pct_premium_pef,
    ).to_dict()


@app.get(
    "/pef/sensibilidad",
    tags=["balances"],
    summary="Sensibilidad: PEF vs sin PEF para varios % reduccion secado",
)
def pef_sensibilidad_endpoint(throughput_kg_h: float = 2000.0) -> dict:
    from .balances.pef_analisis import sensibilidad_pef
    return {
        "throughput_kg_h": throughput_kg_h,
        "rangos": sensibilidad_pef(throughput_kg_h=throughput_kg_h),
    }


# =============================================================================
# FICHAS EQUIPOS (sistema captura info detallada)
# =============================================================================
@app.get(
    "/equipos/fichas",
    tags=["parametros"],
    summary="Listado de fichas tecnicas de equipos de planta",
)
def fichas_listar_endpoint() -> dict:
    from .balances.fichas_equipos import cargar_fichas, resumen_completitud_fichas
    return {
        "fichas": [f.to_dict() for f in cargar_fichas()],
        "resumen": resumen_completitud_fichas(),
    }


class FichaEquipoUpdate(BaseModel):
    equipo_id: str
    updates: dict


@app.post(
    "/equipos/fichas/actualizar",
    tags=["parametros"],
    summary="Actualizar ficha equipo (recibe info que el usuario alimenta)",
)
def fichas_actualizar_endpoint(req: FichaEquipoUpdate) -> dict:
    from .balances.fichas_equipos import actualizar_ficha
    from .cache import clear_all
    f = actualizar_ficha(req.equipo_id, req.updates)
    clear_all()
    return {"ok": True, "ficha": f.to_dict()}


# =============================================================================
# SIMULADOR TEMPORAL (por maquina + planta + timeline mensual)
# =============================================================================
@app.get(
    "/simulacion/planta",
    tags=["balances"],
    summary="Simulacion planta completa por periodo (hora/dia/mes/ano)",
    description=(
        "Simula la planta integrada con bottleneck detectado automaticamente. "
        "Devuelve producto + costos + utilizacion por maquina + timeline mensual estacional."
    ),
)
@cached_ttl(seconds=120)
def simulacion_planta_endpoint(
    periodo: str = "mes",
    horas_operacion_dia: float = 16.0,
    dias_operacion_mes: float = 25.0,
    meses_operacion_ano: float = 10.0,
    mmpp_principal: str = "TOMASA",
) -> dict:
    from .balances.simulador_temporal import simular_planta

    if periodo not in ("hora", "dia", "mes", "ano"):
        raise HTTPException(400, "periodo debe ser: hora, dia, mes o ano")
    if not (0 < horas_operacion_dia <= 24):
        raise HTTPException(400, "horas_operacion_dia debe estar entre 0 y 24")
    if not (0 < dias_operacion_mes <= 31):
        raise HTTPException(400, "dias_operacion_mes debe estar entre 0 y 31")
    if not (0 < meses_operacion_ano <= 12):
        raise HTTPException(400, "meses_operacion_ano debe estar entre 0 y 12")

    return simular_planta(
        periodo=periodo,                                       # type: ignore[arg-type]
        horas_operacion_dia=horas_operacion_dia,
        dias_operacion_mes=dias_operacion_mes,
        meses_operacion_ano=meses_operacion_ano,
        mmpp_principal=mmpp_principal,
    ).to_dict()


@app.get(
    "/simulacion/maquina/{equipo_id}",
    tags=["balances"],
    summary="Simulacion UNA maquina (aislada, capacidad nominal)",
)
def simulacion_maquina_endpoint(
    equipo_id: str,
    periodo: str = "mes",
    horas_operacion_dia: float = 16.0,
    dias_operacion_mes: float = 25.0,
    meses_operacion_ano: float = 10.0,
) -> dict:
    from .balances.simulador_temporal import simular_maquina_individual

    if periodo not in ("hora", "dia", "mes", "ano"):
        raise HTTPException(400, "periodo debe ser: hora, dia, mes o ano")
    try:
        return simular_maquina_individual(
            equipo_id=equipo_id,
            periodo=periodo,                                   # type: ignore[arg-type]
            horas_operacion_dia=horas_operacion_dia,
            dias_operacion_mes=dias_operacion_mes,
            meses_operacion_ano=meses_operacion_ano,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.get(
    "/simulacion/revenue",
    tags=["balances"],
    summary="Simulacion + revenue + margen + payback",
)
@cached_ttl(seconds=120)
def simulacion_revenue_endpoint(
    periodo: str = "ano",
    horas_dia: float = 16.0,
    dias_mes: float = 25.0,
    meses_ano: float = 10.0,
    mmpp_principal: str = "TOMASA",
    sku_principal: str = "harina_animal_premium",
    precio_venta_clp_kg: float | None = None,
) -> dict:
    from .balances.simulacion_revenue import simular_con_revenue
    return simular_con_revenue(
        periodo=periodo,
        horas_dia=horas_dia,
        dias_mes=dias_mes,
        meses_ano=meses_ano,
        mmpp_principal=mmpp_principal,
        sku_principal=sku_principal,
        precio_venta_clp_kg=precio_venta_clp_kg,
    ).to_dict()


@app.get(
    "/simulacion/escalas",
    tags=["balances"],
    summary="Comparador piloto vs industrial (x1, x10, x50, x100)",
    description="Economias de escala: curva 80% costo unit + Williams 0.7 CAPEX",
)
@cached_ttl(seconds=180)
def simulacion_escalas_endpoint(
    horas_dia: float = 16.0,
    dias_mes: float = 25.0,
    meses_ano: float = 10.0,
    mmpp_principal: str = "TOMASA",
    sku_principal: str = "harina_animal_premium",
) -> dict:
    from .balances.simulacion_revenue import comparar_escalas
    return comparar_escalas(
        horas_dia=horas_dia, dias_mes=dias_mes, meses_ano=meses_ano,
        mmpp_principal=mmpp_principal, sku_principal=sku_principal,
    )


@app.get(
    "/simulacion/precios-sku",
    tags=["balances"],
    summary="Catalogo precios estimados por SKU final",
)
def simulacion_precios_endpoint() -> dict:
    from .balances.simulacion_revenue import precios_venta_catalogo
    return precios_venta_catalogo()


@app.get(
    "/simulacion/capex-piloto",
    tags=["balances"],
    summary="CAPEX estimado total piloto (equipos + instalacion + ingenieria)",
)
def simulacion_capex_endpoint() -> dict:
    from .balances.simulacion_revenue import calcular_capex_piloto
    return calcular_capex_piloto()


@app.get(
    "/simulacion/margen-por-sku",
    tags=["balances"],
    summary="Margen del piloto y escala minima rentable POR CADA SKU",
    description=(
        "La verdad estrategica en una tabla: el costo de proceso es el mismo "
        "para todos los SKU; lo que cambia es el precio. Devuelve margen piloto, "
        "escala minima rentable y payback por SKU, ordenado por quien paga antes."
    ),
)
@cached_ttl(seconds=300)
def simulacion_margen_sku_endpoint() -> dict:
    from .balances.simulacion_revenue import margen_por_sku
    return margen_por_sku()


# =============================================================================
# SINTESIS INTELIGENTE (capa cross-modular)
# =============================================================================
@app.get(
    "/inteligencia/sintesis",
    tags=["inteligencia"],
    summary="Sintesis inteligente: insights cross-modulares + plan accion",
    description="Capa que consolida TODOS los modulos y genera insights accionables.",
)
@cached_ttl(seconds=120)
def inteligencia_sintesis_endpoint() -> dict:
    from .balances.sintesis_inteligente import computar_sintesis
    return computar_sintesis().to_dict()


@app.get(
    "/inteligencia/insights",
    tags=["inteligencia"],
    summary="Lista insights ordenados por prioridad",
)
def inteligencia_insights_endpoint(severidad: str | None = None, tipo: str | None = None) -> dict:
    from .balances.sintesis_inteligente import computar_sintesis
    s = computar_sintesis()
    insights = s.insights
    if severidad:
        insights = [i for i in insights if i.severidad == severidad]
    if tipo:
        insights = [i for i in insights if i.tipo == tipo]
    return {
        "total": len(insights),
        "insights": [i.to_dict() for i in insights],
    }


@app.get(
    "/inteligencia/precision",
    tags=["inteligencia"],
    summary="Exactitud del modelo (estimado -> exacto) + qué validar primero",
    description="Pondera cada input por impacto en el resultado final. "
                "Lista accionable de qué validar para subir la exactitud.",
)
@cached_ttl(seconds=120)
def inteligencia_precision_endpoint() -> dict:
    from .balances.precision_tracker import computar_precision
    return computar_precision().to_dict()


@app.get(
    "/inteligencia/prediccion",
    tags=["inteligencia"],
    summary="Predicción con bandas de confianza (p10/esperado/p90) + margen de error",
    description="Monte Carlo que propaga la incertidumbre de cada input (según su "
                "nivel de validación) a las predicciones clave. Reporta rango y margen "
                "de error, no un número falsamente preciso.",
)
@cached_ttl(seconds=120)
def inteligencia_prediccion_endpoint(
    sku_principal: str = "harina_animal_premium",
    n_sims: int = 3000,
) -> dict:
    from .balances.prediccion_intervalos import computar_prediccion
    if n_sims < 500 or n_sims > 10000:
        raise HTTPException(400, "n_sims debe estar entre 500 y 10000")
    return computar_prediccion(sku_principal=sku_principal, n_sims=n_sims).to_dict()
