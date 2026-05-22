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
from .climate_risk import simular_clima_n_corridas
from .compliance_rep import (
    HITOS_LEY_REP,
    costo_compliance_total_clp,
    hitos_por_estado,
    proximos_hitos,
)
from .learning_curve import ahorro_por_aprendizaje_clp
from .slb import KPIS_DEFAULT, SlbBondSpec, simular_kpis_optimista_pesimista
from .monte_carlo import run_monte_carlo
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
        "Ejecuta los 3 escenarios canónicos (PILOTO 25k ton, INDUSTRIAL 50k ton, "
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
