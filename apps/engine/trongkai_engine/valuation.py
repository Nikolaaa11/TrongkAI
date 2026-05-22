"""Valoración EV/EBITDA — sirve para estimar valor de salida (exit) año 5.

Benchmarks (docs/INTELIGENCIA-COMPETITIVA.md):
- Food processing global: **9,63x EV/EBITDA** (Damodaran 2026).
- Ingredientes especialidad/funcionales: 9-12x según calidad de earnings.
- Premium aplicable a Trongkai: certificaciones SQF/HACCP + ESG + sustentabilidad.

Devuelve un rango low/base/high para que el directorio vea bandas.
"""

from __future__ import annotations

from dataclasses import dataclass

from .plan_builder import ResumenPlan


@dataclass
class ValuationResult:
    ebitda_ano5_clp: float
    multiple_base: float
    multiple_low: float
    multiple_high: float
    ev_clp_base: float
    ev_clp_low: float
    ev_clp_high: float
    moic_estimado: float | None  # Multiple Of Invested Capital
    capex_total_5y_clp: float
    nota: str


# Benchmarks de mercado verificados con WebSearch (docs/INTELIGENCIA-COMPETITIVA.md)
MULTIPLE_FOOD_PROCESSING_GLOBAL = 9.63  # Damodaran
MULTIPLE_INGREDIENTES_FUNCIONALES_LOW = 8.0
MULTIPLE_INGREDIENTES_FUNCIONALES_HIGH = 12.0


def valuar_proyecto_ev_ebitda(plan: ResumenPlan) -> ValuationResult:
    """Calcula la valoración de salida en año 5 aplicando rango EV/EBITDA.

    EV = EBITDA_año5 × múltiple.
    MOIC = EV / CapEx total 5 años (proxy de retorno absoluto a CEHTA).
    """
    ebitda_5 = plan.ebitda_anuales[4] if len(plan.ebitda_anuales) >= 5 else 0
    capex_total = sum(plan.capex_anuales)

    ev_base = ebitda_5 * MULTIPLE_FOOD_PROCESSING_GLOBAL
    ev_low = ebitda_5 * MULTIPLE_INGREDIENTES_FUNCIONALES_LOW
    ev_high = ebitda_5 * MULTIPLE_INGREDIENTES_FUNCIONALES_HIGH

    moic = (ev_base / capex_total) if capex_total > 0 else None

    nota = (
        f"EBITDA año 5 = ${ebitda_5/1e9:.2f}B CLP. "
        f"Aplicando múltiplo food processing global ({MULTIPLE_FOOD_PROCESSING_GLOBAL:.2f}x), "
        f"EV base = ${ev_base/1e9:.2f}B CLP. "
        f"Rango ingredientes funcionales: {MULTIPLE_INGREDIENTES_FUNCIONALES_LOW:.0f}-{MULTIPLE_INGREDIENTES_FUNCIONALES_HIGH:.0f}x."
    )

    return ValuationResult(
        ebitda_ano5_clp=ebitda_5,
        multiple_base=MULTIPLE_FOOD_PROCESSING_GLOBAL,
        multiple_low=MULTIPLE_INGREDIENTES_FUNCIONALES_LOW,
        multiple_high=MULTIPLE_INGREDIENTES_FUNCIONALES_HIGH,
        ev_clp_base=ev_base,
        ev_clp_low=ev_low,
        ev_clp_high=ev_high,
        moic_estimado=moic,
        capex_total_5y_clp=capex_total,
        nota=nota,
    )
