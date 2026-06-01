"""Commercial Intelligence - cálculos integrando datos reales del dump P1.

Cruza:
- Clientes reales (Agrozzi, Iansa, Sugal, Olivares, San Clemente) — USD 1.46M anual
- Benchmarks proteínas (Fava bean $4.5, GP68 $5.2, Yellow pea $3.8)
- Stack tecnológico (Opticept +18% rend, Infrasonido -65% energía, Micromolienda +35% calidad)
- Plan_builder con precios SKUs y rendimientos

Genera:
1. Pricing power: precio actual vs benchmark mercado por SKU
2. Customer concentration risk: HHI Herfindahl-Hirschman
3. Tech ROI: payback period y NPV por cada tecnología si se aplica
4. Revenue pipeline: proyección revenue mes a mes desde clientes reales
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .clientes_reales import CLIENTES, BENCHMARKS_PROTEINAS
from .plan_builder import PRECIOS_REFERENCIA, ParametrosPlan
from .tecnologias_catalog import TECNOLOGIAS


# ============================================================================
# 1. PRICING POWER - precios SKUs vs benchmarks
# ============================================================================

# Tipo de cambio USD/CLP (debería venir de macro_chile pero hardcoded fallback)
USD_CLP_FALLBACK = 900.0


@dataclass
class PricingAnalysis:
    sku: str
    precio_actual_clp_kg: float
    precio_actual_usd_kg: float
    benchmark_usd_kg: float | None
    benchmark_descripcion: str
    delta_pct_vs_benchmark: float | None  # % por sobre/debajo del benchmark
    headroom_pct: float | None             # cuánto se puede subir antes de llegar al benchmark
    recomendacion: str

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "precio_actual_clp_kg": self.precio_actual_clp_kg,
            "precio_actual_usd_kg": round(self.precio_actual_usd_kg, 2),
            "benchmark_usd_kg": self.benchmark_usd_kg,
            "benchmark_descripcion": self.benchmark_descripcion,
            "delta_pct_vs_benchmark": (
                round(self.delta_pct_vs_benchmark, 1)
                if self.delta_pct_vs_benchmark is not None else None
            ),
            "headroom_pct": (
                round(self.headroom_pct, 1)
                if self.headroom_pct is not None else None
            ),
            "recomendacion": self.recomendacion,
        }


# Mapeo SKU → benchmark más comparable
SKU_BENCHMARK_MAP = {
    "PROTEINA_UNICEL": ("SDS GP Protein Concentrate GP68", 5.2),
    "HARINA_ALPERUJO": ("Yellow pea protein", 3.8),
    "HARINA_TOMASA": ("Low protein powder of fava bean", 4.5),
    "ANTIOXIDANTE": ("Specialty antioxidant ingredient", 18.0),  # premium
    "LICOPENO": ("Licopeno extraído food grade", 95.0),  # ultra premium
    "PECTINA": ("Citrus pectin food grade", 28.0),
}


def analizar_pricing(usd_clp: float = USD_CLP_FALLBACK) -> list[PricingAnalysis]:
    """Compara precio actual de cada SKU con benchmark de mercado."""
    base = ParametrosPlan()
    resultados: list[PricingAnalysis] = []

    for sku, precio_clp in base.precios_clp_kg.items():
        precio_usd = precio_clp / usd_clp
        benchmark_info = SKU_BENCHMARK_MAP.get(sku)

        if benchmark_info:
            bench_desc, bench_usd = benchmark_info
            delta_pct = (precio_usd - bench_usd) / bench_usd * 100
            headroom = (bench_usd - precio_usd) / precio_usd * 100 if precio_usd > 0 else 0

            if delta_pct > 5:
                rec = f"⚠ Precio {delta_pct:.0f}% sobre benchmark — riesgo competitivo"
            elif delta_pct < -20:
                rec = f"💰 {abs(delta_pct):.0f}% bajo benchmark — headroom para subir {headroom:.0f}%"
            elif delta_pct < -10:
                rec = f"📈 Pricing aceptable con headroom moderado ({headroom:.0f}%)"
            else:
                rec = "✓ Pricing alineado con mercado"
        else:
            bench_desc = "Sin benchmark directo"
            bench_usd = None
            delta_pct = None
            headroom = None
            rec = "Validar precio con cliente target"

        resultados.append(PricingAnalysis(
            sku=sku,
            precio_actual_clp_kg=precio_clp,
            precio_actual_usd_kg=precio_usd,
            benchmark_usd_kg=bench_usd,
            benchmark_descripcion=bench_desc,
            delta_pct_vs_benchmark=delta_pct,
            headroom_pct=headroom,
            recomendacion=rec,
        ))

    return resultados


# ============================================================================
# 2. CUSTOMER CONCENTRATION - HHI
# ============================================================================

@dataclass
class ConcentrationAnalysis:
    hhi: float                       # Herfindahl-Hirschman Index 0-10000
    nivel_concentracion: str         # baja/moderada/alta/critica
    top_1_pct: float                  # % del cliente más grande
    top_3_pct: float                  # % de los top 3
    n_clientes_efectivos: float      # 1/sum(s²) — número equivalente clientes
    riesgo_perdida_top_1: str
    recomendacion: str

    def to_dict(self) -> dict:
        return {
            "hhi": round(self.hhi, 0),
            "nivel_concentracion": self.nivel_concentracion,
            "top_1_pct": round(self.top_1_pct, 1),
            "top_3_pct": round(self.top_3_pct, 1),
            "n_clientes_efectivos": round(self.n_clientes_efectivos, 1),
            "riesgo_perdida_top_1": self.riesgo_perdida_top_1,
            "recomendacion": self.recomendacion,
        }


def analizar_concentracion() -> ConcentrationAnalysis:
    """Calcula HHI de los clientes reales del catálogo P1."""
    revenue_por_cliente = [c.valor_anual_estimado_usd for c in CLIENTES]
    total = sum(revenue_por_cliente)
    if total == 0:
        return ConcentrationAnalysis(0, "n/a", 0, 0, 0, "n/a", "Sin clientes")

    # Cuotas (s_i)
    cuotas = sorted([(r / total) for r in revenue_por_cliente], reverse=True)
    # HHI = sum((cuota * 100)²) → escala 0-10,000 (estándar antitrust)
    hhi = sum((s * 100) ** 2 for s in cuotas)
    top_1 = cuotas[0] * 100
    top_3 = sum(cuotas[:3]) * 100
    n_efectivos = 1 / sum(s ** 2 for s in cuotas)

    if hhi > 2500:
        nivel = "crítica"
        riesgo = f"ALTO: top cliente concentra {top_1:.0f}% del revenue"
        rec = "Urgente diversificar pipeline LP. Sumar 3-5 clientes adicionales."
    elif hhi > 1800:
        nivel = "alta"
        riesgo = f"MEDIO-ALTO: top cliente concentra {top_1:.0f}%"
        rec = "Diversificar antes de roadshow LP. Buscar 2-3 clientes nuevos."
    elif hhi > 1000:
        nivel = "moderada"
        riesgo = "MEDIO: cartera con cierta dependencia"
        rec = "Monitorear, idealmente sumar 1-2 clientes ancla más."
    else:
        nivel = "baja"
        riesgo = "BAJO: cartera diversificada"
        rec = "✓ Concentración aceptable para LP serio."

    return ConcentrationAnalysis(
        hhi=hhi,
        nivel_concentracion=nivel,
        top_1_pct=top_1,
        top_3_pct=top_3,
        n_clientes_efectivos=n_efectivos,
        riesgo_perdida_top_1=riesgo,
        recomendacion=rec,
    )


# ============================================================================
# 3. TECH ROI - payback y NPV de aplicar cada tecnología
# ============================================================================

@dataclass
class TechROIAnalysis:
    tech_id: str
    tech_nombre: str
    capex_usd: float
    incremento_revenue_anual_usd: float  # estimado desde impacto rendimiento × revenue
    ahorro_opex_anual_usd: float          # estimado desde -kWh × precio energía
    payback_anos: float | None
    npv_5y_usd: float                     # NPV a 5 años descuento 10%
    irr_aproximado_pct: float | None
    recomendacion: str

    def to_dict(self) -> dict:
        return {
            "tech_id": self.tech_id,
            "tech_nombre": self.tech_nombre,
            "capex_usd": self.capex_usd,
            "incremento_revenue_anual_usd": round(self.incremento_revenue_anual_usd, 0),
            "ahorro_opex_anual_usd": round(self.ahorro_opex_anual_usd, 0),
            "payback_anos": round(self.payback_anos, 2) if self.payback_anos else None,
            "npv_5y_usd": round(self.npv_5y_usd, 0),
            "irr_aproximado_pct": (
                round(self.irr_aproximado_pct, 1)
                if self.irr_aproximado_pct is not None else None
            ),
            "recomendacion": self.recomendacion,
        }


# Costos referencia
ENERGIA_CLP_KWH = 130       # CLP industrial Chile 2026
DISCOUNT_RATE = 0.10        # 10% real para tech investments


def analizar_tech_roi(usd_clp: float = USD_CLP_FALLBACK) -> list[TechROIAnalysis]:
    """ROI por cada tecnología del stack."""
    # Revenue base estimado: USD 1.46M anual desde clientes reales
    revenue_base_anual = sum(c.valor_anual_estimado_usd for c in CLIENTES)
    # Volumen base ton
    volumen_base_ton = sum(c.volumen_anual_estimado_ton for c in CLIENTES)
    # Energía base secado (kWh/ton tradicional × volumen)
    energia_base_kwh_ano = 250 * volumen_base_ton

    resultados = []
    for t in TECNOLOGIAS:
        # 1. Incremento revenue: % rendimiento sobre revenue base
        incremento_revenue = (
            revenue_base_anual * (t.impacto_rendimiento_pct or 0) / 100
            if t.impacto_rendimiento_pct else 0
        )

        # 2. Ahorro OpEx por energía
        ahorro_opex = 0
        if t.opex_kwh_ton is not None:
            # Asumir que reemplaza secado tradicional 250 kWh/ton
            energia_nueva_kwh_ano = t.opex_kwh_ton * volumen_base_ton
            ahorro_kwh_ano = max(0, energia_base_kwh_ano - energia_nueva_kwh_ano)
            ahorro_clp_ano = ahorro_kwh_ano * ENERGIA_CLP_KWH
            ahorro_opex = ahorro_clp_ano / usd_clp

        # 3. Beneficio anual total
        beneficio_anual = incremento_revenue + ahorro_opex

        # 4. Payback
        payback = (
            t.capex_usd / beneficio_anual
            if beneficio_anual > 0 else None
        )

        # 5. NPV 5 años (cash flow constante, descuento 10%)
        npv = -t.capex_usd
        for year in range(1, 6):
            npv += beneficio_anual / ((1 + DISCOUNT_RATE) ** year)

        # 6. IRR aproximada (bisección simple)
        irr = None
        if beneficio_anual > 0 and t.capex_usd > 0:
            # IRR aproximada = beneficio_anual / capex (perpetuidad simple)
            # Más exacto con bisección
            lo, hi = 0.0, 5.0
            for _ in range(30):
                mid = (lo + hi) / 2
                npv_at = -t.capex_usd + sum(
                    beneficio_anual / ((1 + mid) ** y) for y in range(1, 6)
                )
                if abs(npv_at) < 100:
                    break
                if npv_at > 0:
                    lo = mid
                else:
                    hi = mid
            irr = mid * 100

        # Recomendación
        if payback is None or payback > 5:
            rec = "❌ Payback >5 años — postergar"
        elif payback < 1.5:
            rec = f"✅ Payback {payback:.1f} años — implementar YA"
        elif payback < 3:
            rec = f"📈 Payback {payback:.1f} años — buen ROI"
        else:
            rec = f"⏳ Payback {payback:.1f} años — evaluar contra alternativas"

        resultados.append(TechROIAnalysis(
            tech_id=t.id,
            tech_nombre=t.nombre,
            capex_usd=t.capex_usd,
            incremento_revenue_anual_usd=incremento_revenue,
            ahorro_opex_anual_usd=ahorro_opex,
            payback_anos=payback,
            npv_5y_usd=npv,
            irr_aproximado_pct=irr,
            recomendacion=rec,
        ))

    # Ordenar por NPV desc
    resultados.sort(key=lambda r: r.npv_5y_usd, reverse=True)
    return resultados


# ============================================================================
# 4. REVENUE PIPELINE - proyección mensual desde clientes reales
# ============================================================================

@dataclass
class RevenuePipelinePoint:
    mes: int                # 1-60 (5 años)
    revenue_base_usd: float       # baseline (sin clientes nuevos)
    revenue_clientes_reales_usd: float  # incremento por clientes del catálogo
    revenue_total_usd: float
    clientes_activos: int

    def to_dict(self) -> dict:
        return {
            "mes": self.mes,
            "revenue_base_usd": round(self.revenue_base_usd, 0),
            "revenue_clientes_reales_usd": round(self.revenue_clientes_reales_usd, 0),
            "revenue_total_usd": round(self.revenue_total_usd, 0),
            "clientes_activos": self.clientes_activos,
        }


# Mapeo estado → tiempo estimado hasta producción (meses)
TIEMPO_HASTA_PRODUCCION_MESES = {
    "prospect": 12,      # 6 meses contacto + 6 meses DD
    "contactado": 9,
    "dd": 6,
    "loi": 3,
    "contrato": 1,       # ya cerrado, ramp-up 1 mes
}


def construir_revenue_pipeline(meses: int = 60) -> list[RevenuePipelinePoint]:
    """Proyecta revenue mensual integrando clientes reales con su probabilidad de cierre."""
    # Revenue baseline desde el plan_builder REAL (ponderado por mix de SKUs)
    # Plan 5 años proyecta ~$27B CLP ingresos año 5 → ~$30M USD
    # Año 1 ramp-up 30%, año 5 100%
    from .plan_builder import build_plan
    base = ParametrosPlan()
    try:
        plan = build_plan(base)
        # ingresos_anuales viene en CLP
        ingresos_anuales_clp = plan.ingresos_anuales
        ingresos_anuales_usd = [i / USD_CLP_FALLBACK for i in ingresos_anuales_clp]
    except Exception:
        # Fallback razonable
        ingresos_anuales_usd = [5_000_000, 12_000_000, 18_000_000, 25_000_000, 30_000_000]

    # Clientes reales con su timing
    clientes_con_timing = []
    for c in CLIENTES:
        # Probabilidad implícita por estado
        prob = {
            "prospect": 0.20, "contactado": 0.40, "dd": 0.60,
            "loi": 0.80, "contrato": 0.95, "perdido": 0.0,
        }.get(c.estado_relacion, 0.20)
        mes_inicio = TIEMPO_HASTA_PRODUCCION_MESES.get(c.estado_relacion, 12)
        # Revenue mensual de este cliente (anualizado / 12 × prob)
        revenue_mensual_cliente = (
            c.valor_anual_estimado_usd * prob / 12
        )
        clientes_con_timing.append({
            "nombre": c.nombre,
            "mes_inicio": mes_inicio,
            "revenue_mensual": revenue_mensual_cliente,
        })

    pipeline = []
    for mes in range(1, meses + 1):
        # Baseline desde plan_builder real (interpolación lineal entre años)
        anio_idx = min(4, (mes - 1) // 12)
        revenue_anual_actual = ingresos_anuales_usd[anio_idx] if anio_idx < len(ingresos_anuales_usd) else ingresos_anuales_usd[-1]
        rev_base = revenue_anual_actual / 12

        # Clientes reales activos en este mes
        rev_clientes = 0
        n_activos = 0
        for cli in clientes_con_timing:
            if mes >= cli["mes_inicio"]:
                rev_clientes += cli["revenue_mensual"]
                n_activos += 1

        pipeline.append(RevenuePipelinePoint(
            mes=mes,
            revenue_base_usd=rev_base,
            revenue_clientes_reales_usd=rev_clientes,
            revenue_total_usd=rev_base + rev_clientes,
            clientes_activos=n_activos,
        ))

    return pipeline


# ============================================================================
# Orquestador
# ============================================================================

def analisis_comercial_completo() -> dict[str, Any]:
    """Análisis comercial integral. Salida única para endpoint."""
    pricing = analizar_pricing()
    concentracion = analizar_concentracion()
    tech_roi = analizar_tech_roi()
    pipeline = construir_revenue_pipeline(meses=60)

    # Resumen ejecutivo
    revenue_total_5y = sum(p.revenue_total_usd for p in pipeline)
    tech_npv_total = sum(t.npv_5y_usd for t in tech_roi)
    skus_sobreprecio = sum(
        1 for p in pricing
        if p.delta_pct_vs_benchmark is not None and p.delta_pct_vs_benchmark > 5
    )
    skus_con_headroom = sum(
        1 for p in pricing
        if p.headroom_pct is not None and p.headroom_pct > 20
    )

    return {
        "pricing_skus": [p.to_dict() for p in pricing],
        "concentracion_clientes": concentracion.to_dict(),
        "tech_roi": [t.to_dict() for t in tech_roi],
        "revenue_pipeline_60m": [p.to_dict() for p in pipeline],
        "resumen_ejecutivo": {
            "revenue_total_5y_usd": round(revenue_total_5y, 0),
            "tech_npv_total_5y_usd": round(tech_npv_total, 0),
            "skus_sobreprecio": skus_sobreprecio,
            "skus_con_headroom_alto": skus_con_headroom,
            "hhi_concentracion": round(concentracion.hhi, 0),
            "concentracion_nivel": concentracion.nivel_concentracion,
            "n_clientes_efectivos": round(concentracion.n_clientes_efectivos, 1),
        },
    }
