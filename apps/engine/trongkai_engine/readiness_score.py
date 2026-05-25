"""Investment Readiness Score (IRS) — score 0-100 de madurez del proyecto.

Sintetiza 8 dimensiones en una nota única que puede comunicarse a LP / comité
de inversión / directorio:

| Dimensión                 | Peso | Métrica                                         |
|---------------------------|------|-------------------------------------------------|
| 1. Retorno financiero     | 20%  | TIR proyecto vs hurdle (15%)                    |
| 2. Robustez (Monte Carlo) | 15%  | Prob TIR > WACC (P5/P50)                        |
| 3. Bancabilidad           | 15%  | DSCR promedio años 3-5 (>1.3 = bancable)        |
| 4. Diversificación        | 10%  | Concentración del top SKU (HHI revenue)         |
| 5. ESG (carbono)          | 10%  | Carbono negativo en baseline = 10/10             |
| 6. Compliance regulatorio | 10%  | Hitos vigentes / total                          |
| 7. Resilencia (sensitivity)| 10% | Colchón promedio break-even                     |
| 8. Madurez operativa      | 10%  | Working capital saneado + ramp-up               |

Score >= 80: bankable / investable de inmediato.
Score 60-79: requiere optimización en 1-2 dimensiones.
Score 40-59: oportunidad de mejora estructural.
Score < 40: re-think estratégico.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .breakeven import breakeven_summary
from .carbon_footprint import calcular_footprint, comparar_escenarios_footprint
from .compliance_rep import hitos_por_estado
from .monte_carlo import run_monte_carlo_con_clima
from .plan_builder import ParametrosPlan, build_plan


@dataclass
class DimensionScore:
    nombre: str
    peso: float
    valor_metrico: float
    score_0_100: float
    detalle: str

    def aporte_total(self) -> float:
        return self.score_0_100 * self.peso


@dataclass
class ReadinessScore:
    score_total: float
    dimensiones: list[DimensionScore] = field(default_factory=list)
    interpretacion: str = ""

    def to_dict(self) -> dict:
        return {
            "score_total": round(self.score_total, 1),
            "dimensiones": [
                {
                    "nombre": d.nombre,
                    "peso": d.peso,
                    "valor_metrico": d.valor_metrico,
                    "score_0_100": round(d.score_0_100, 1),
                    "aporte_total": round(d.aporte_total(), 1),
                    "detalle": d.detalle,
                }
                for d in self.dimensiones
            ],
            "interpretacion": self.interpretacion,
        }


def _score_retorno(tir: float | None, hurdle: float = 0.15) -> tuple[float, str]:
    """Score 0-100 según TIR vs hurdle. Lineal entre hurdle y hurdle+20pp = 100."""
    if tir is None:
        return 0.0, "TIR no calculable"
    if tir <= hurdle:
        return 0.0, f"TIR {tir*100:.1f}% <= hurdle {hurdle*100:.0f}%"
    if tir >= hurdle + 0.20:
        return 100.0, f"TIR {tir*100:.1f}% >> hurdle"
    score = ((tir - hurdle) / 0.20) * 100
    return score, f"TIR {tir*100:.1f}% (+{(tir-hurdle)*100:.1f}pp sobre hurdle)"


def _score_robustez(prob_supera_wacc: float | None) -> tuple[float, str]:
    """Probabilidad de superar WACC. 100% = 100, 50% = 50, 0% = 0."""
    if prob_supera_wacc is None:
        return 0.0, "Monte Carlo no disponible"
    score = prob_supera_wacc * 100
    return score, f"Prob(TIR>WACC) = {prob_supera_wacc*100:.0f}% en 1000+ sims"


def _score_bancabilidad(dscr_promedio: float) -> tuple[float, str]:
    """DSCR >= 1.6 = 100, DSCR <= 1.0 = 0, lineal entremedio."""
    if dscr_promedio <= 1.0:
        return 0.0, f"DSCR {dscr_promedio:.2f} — no bancable"
    if dscr_promedio >= 1.6:
        return 100.0, f"DSCR {dscr_promedio:.2f} — bancable holgado"
    score = ((dscr_promedio - 1.0) / 0.6) * 100
    return score, f"DSCR {dscr_promedio:.2f}"


def _score_diversificacion(plan_summary) -> tuple[float, str]:
    """HHI invertido: concentración baja = score alto. Si top SKU > 40% → penalización."""
    ingresos_marca = getattr(plan_summary, "ingresos_por_marca", None)
    if not ingresos_marca:
        return 50.0, "Sin desglose por marca"
    # Calcular concentración: si Feed/Food/Servicios bien balanceados → 100
    totales = [
        sum(m.ingresos_anuales) if hasattr(m, "ingresos_anuales") else 0.0
        for m in ingresos_marca
    ]
    total = sum(totales)
    if total == 0:
        return 0.0, "Sin ingresos"
    pct_top = max(totales) / total
    # 33% perfectamente balanceado → 100; 100% concentrado → 0
    score = max(0.0, (1 - (pct_top - 0.33) / 0.67) * 100) if pct_top > 0.33 else 100.0
    return score, f"Top marca: {pct_top*100:.0f}% del revenue 5y"


def _score_esg(carbono) -> tuple[float, str]:
    """Carbono negativo = 100. Carbono neutral = 50. Positivo = 0."""
    if not carbono:
        return 50.0, "LCA no disponible"
    baseline = carbono.get("baseline", {})
    emisiones = baseline.get("emisiones_netas_5y_ton", 0)
    if emisiones < 0:
        # Carbono negativo
        return 100.0, f"Carbono negativo (-{abs(emisiones):,.0f} ton CO2eq 5y)"
    if emisiones == 0:
        return 80.0, "Carbono neutral"
    # Score decrece con emisiones positivas
    score = max(0.0, 80 - emisiones / 1000)
    return score, f"Emisiones +{emisiones:,.0f} ton CO2eq"


def _score_compliance(rep_summary) -> tuple[float, str]:
    """Hitos vigentes / total. Default 100% si no hay info."""
    if not rep_summary:
        return 50.0, "Sin info compliance"
    vigentes = rep_summary.get("vigentes", 0)
    total = rep_summary.get("total_hitos", 0)
    if total == 0:
        return 100.0, "Sin obligaciones pendientes"
    pct = vigentes / total
    return pct * 100, f"{vigentes}/{total} hitos REP vigentes"


def _score_resiliencia(breakeven_resumen) -> tuple[float, str]:
    """Promedio de colchones break-even. > 30% promedio = 100."""
    if not breakeven_resumen:
        return 50.0, "Break-even no disponible"
    res = breakeven_resumen.get("resultados", [])
    colchones = [r["colchon_pct"] for r in res if r["colchon_pct"] is not None]
    if not colchones:
        return 0.0, "Sin colchones calculables"
    promedio = sum(colchones) / len(colchones)
    # Cap a 100
    score = min(100.0, promedio / 0.50 * 100)  # 50% colchón promedio = 100
    return score, f"Colchón promedio {promedio*100:.0f}%"


def _score_madurez_operativa(plan) -> tuple[float, str]:
    """Working capital + ramp-up. Si EBITDA año 1 > 0 → 100. Si EBITDA año 2 > 0 → 80."""
    ebitda = plan.ebitda_anuales
    if not ebitda or len(ebitda) < 2:
        return 50.0, "Sin EERR anual"
    if ebitda[0] > 0:
        return 100.0, "EBITDA año 1 positivo"
    if ebitda[1] > 0:
        return 75.0, "EBITDA año 2 positivo (ramp-up año 1)"
    if ebitda[2] > 0:
        return 50.0, "EBITDA año 3 positivo (ramp-up 2 años)"
    return 25.0, "EBITDA negativo > 3 años"


def calcular_readiness_score(
    base_params: ParametrosPlan | None = None,
    n_sims_mc: int = 500,  # MC reducido para velocidad
) -> ReadinessScore:
    """Calcula el Investment Readiness Score completo."""
    base = base_params or ParametrosPlan()
    plan = build_plan(base)

    # Métricas auxiliares
    tir = plan.kpis.tir_proyecto_anual
    s1, d1 = _score_retorno(tir)

    # Monte Carlo
    try:
        mc = run_monte_carlo_con_clima(n_runs=n_sims_mc, seed=42)
        prob_wacc = (
            mc.get("prob_tir_supera_wacc")
            if isinstance(mc, dict)
            else getattr(mc, "prob_tir_supera_wacc", None)
        )
    except Exception:
        prob_wacc = None
    s2, d2 = _score_robustez(prob_wacc)

    # DSCR (sin financing call para evitar dependencia compleja)
    # Heurística: usar EBITDA / proxy de servicio deuda
    ebitda_3_5 = plan.ebitda_anuales[2:5] if len(plan.ebitda_anuales) >= 5 else plan.ebitda_anuales
    # Proxy servicio deuda: 50% del CapEx total / 10 años plazo
    capex_total = sum(plan.capex_anuales) if hasattr(plan, "capex_anuales") else 15_000_000_000
    servicio_anual_proxy = (capex_total * 0.50) / 10  # 50% deuda, 10y
    if servicio_anual_proxy > 0 and ebitda_3_5:
        dscr_promedio = sum(ebitda_3_5) / len(ebitda_3_5) / servicio_anual_proxy
    else:
        dscr_promedio = 1.0
    s3, d3 = _score_bancabilidad(dscr_promedio)

    # Diversificación
    s4, d4 = _score_diversificacion(plan)

    # ESG carbono — usar escenarios footprint baseline
    try:
        volumenes = [50_000 * (plan.kpis.ratio_capex_ventas or 0.3)] * 5  # proxy
        # mejor: usar volúmenes reales del plan si disponibles
        if hasattr(plan, "volumen_anual_ton") and plan.volumen_anual_ton:
            volumenes = list(plan.volumen_anual_ton)
        else:
            volumenes = [
                base.volumen_total_ton_ano * base.volumen_pct_por_ano.get(y, 1.0)
                for y in range(1, 6)
            ]
        escenarios_co2 = comparar_escenarios_footprint(volumen_mmpp_anual_ton=volumenes)
        baseline = escenarios_co2.get("baseline") if isinstance(escenarios_co2, dict) else None
        if baseline and isinstance(baseline, dict):
            carbon = {"baseline": baseline}
        elif baseline:
            carbon = {"baseline": {"emisiones_netas_5y_ton": getattr(baseline, "emisiones_netas_5y_ton", 0)}}
        else:
            carbon = None
    except Exception:
        carbon = None
    s5, d5 = _score_esg(carbon)

    # Compliance — usar hitos_por_estado
    try:
        rep_estado = hitos_por_estado()
        rep = {
            "vigentes": rep_estado.get("vigentes", 0),
            "total_hitos": sum(rep_estado.get(k, 0) for k in ("vigentes", "proximos", "cumplidos", "vencidos")),
        }
    except Exception:
        rep = None
    s6, d6 = _score_compliance(rep)

    # Resiliencia (breakeven)
    try:
        be = breakeven_summary(umbral_tir=0.15).to_dict()
    except Exception:
        be = None
    s7, d7 = _score_resiliencia(be)

    # Madurez operativa
    s8, d8 = _score_madurez_operativa(plan)

    dimensiones = [
        DimensionScore("Retorno financiero", 0.20, tir or 0, s1, d1),
        DimensionScore("Robustez Monte Carlo", 0.15, prob_wacc or 0, s2, d2),
        DimensionScore("Bancabilidad DSCR", 0.15, dscr_promedio, s3, d3),
        DimensionScore("Diversificación marca", 0.10, 0, s4, d4),
        DimensionScore("ESG carbono", 0.10, 0, s5, d5),
        DimensionScore("Compliance regulatorio", 0.10, 0, s6, d6),
        DimensionScore("Resiliencia (break-even)", 0.10, 0, s7, d7),
        DimensionScore("Madurez operativa", 0.10, 0, s8, d8),
    ]

    score_total = sum(d.aporte_total() for d in dimensiones)

    # Interpretación
    if score_total >= 80:
        interpretacion = "BANKABLE — proyecto listo para LP roadshow / cierre de financiamiento."
    elif score_total >= 60:
        interpretacion = "PROMETEDOR — requiere optimización en 1-2 dimensiones antes del cierre."
    elif score_total >= 40:
        interpretacion = "OPORTUNIDAD — mejora estructural necesaria en múltiples dimensiones."
    else:
        interpretacion = "RE-THINK — revisar tesis fundamental del proyecto."

    return ReadinessScore(
        score_total=score_total,
        dimensiones=dimensiones,
        interpretacion=interpretacion,
    )
