"""Calculadora footprint carbono Trongkai + revenue por créditos CO₂.

Modelo LCA cradle-to-gate basado en literatura peer-reviewed:
- ACS Sustainable Chem Eng 2025: olive pomace biorefinery con BECCS = -1.05 kg CO₂eq/UF
- ResearchGate: succinic acid biorefinery GWP 0.79 kg CO₂eq / kg dry pomace
- ScienceDirect 2024: olive pruning BECCS = -84.37 kg CO₂eq/kg etanol

Precio CO₂ Chile (Ley 21.210 Reforma Tributaria):
- Impuesto verde 5 USD/ton CO₂ para emisores grandes (>25 MW térmicos).
- Trongkai NO es emisor neto si está bien diseñado → potencial revenue por
  certificados de captura (Voluntary Carbon Market).

Mercado voluntario CO₂ 2026:
- Removal (BECCS, biochar): USD 30-150/ton (premium)
- Avoidance (reducción vertedero, etc): USD 5-30/ton
- Trongkai puede emitir créditos por residuos NO descompuestos en vertedero.
"""

from __future__ import annotations

from dataclasses import dataclass


# Factores de emisión por etapa (kg CO2eq / kg producto)
# Baseline literatura olive pomace biorefinería
GWP_BASELINE_KG_CO2EQ_POR_KG_PRODUCTO = 0.79

# Reducción potencial con energías renovables (sin BECCS)
GWP_RENOVABLE_KG_CO2EQ_POR_KG_PRODUCTO = 0.35

# Con BECCS (futuro, hipotético)
GWP_BECCS_KG_CO2EQ_POR_KG_PRODUCTO = -1.05

# Avoided emission: residuos que NO se descomponen en vertedero
# Factor IPCC: 1 ton residuos orgánicos → ~0.5 ton CH4 (× GWP 28) = 14 ton CO2eq
# Trongkai recibe MMPP que de otra forma iría a vertedero/quema
AVOIDED_EMISSION_KG_CO2EQ_POR_KG_MMPP = 0.5

# Precio CO₂ Chile y mercados voluntarios (USD/ton CO2eq) — actualizar trimestral
PRECIO_CO2_CHILE_IMPUESTO_VERDE_USD = 5.0
PRECIO_CO2_VCM_AVOIDANCE_USD = 15.0   # promedio mercado voluntario
PRECIO_CO2_VCM_REMOVAL_USD = 80.0     # premium captura efectiva (BECCS)

TC_USD_CLP_REFERENCIA = 920.0


@dataclass
class FootprintResult:
    scenario: str  # "baseline" | "renovable" | "beccs"
    emisiones_brutas_ton_co2eq_anual: list[float]
    emisiones_evitadas_ton_co2eq_anual: list[float]
    emisiones_netas_ton_co2eq_anual: list[float]
    revenue_creditos_co2_clp_anual: list[float]
    es_carbono_neutro: bool
    es_carbono_negativo: bool


def calcular_footprint(
    volumen_mmpp_anual_ton: list[float],
    rendimiento_promedio: float = 0.26,
    escenario: str = "baseline",  # "baseline" | "renovable" | "beccs"
    precio_credito_usd_ton: float = PRECIO_CO2_VCM_AVOIDANCE_USD,
    tc_usd_clp: float = TC_USD_CLP_REFERENCIA,
) -> FootprintResult:
    """Calcula footprint año por año.

    emisiones_brutas = ton producto × factor GWP del escenario.
    emisiones_evitadas = ton MMPP × factor avoided (residuos no van vertedero).
    emisiones_netas = brutas - evitadas.
    revenue = -emisiones_netas × precio (si negativo: ganancia).
    """
    factor_gwp = {
        "baseline": GWP_BASELINE_KG_CO2EQ_POR_KG_PRODUCTO,
        "renovable": GWP_RENOVABLE_KG_CO2EQ_POR_KG_PRODUCTO,
        "beccs": GWP_BECCS_KG_CO2EQ_POR_KG_PRODUCTO,
    }.get(escenario, GWP_BASELINE_KG_CO2EQ_POR_KG_PRODUCTO)

    emisiones_brutas: list[float] = []
    emisiones_evitadas: list[float] = []
    emisiones_netas: list[float] = []
    revenue_anual: list[float] = []

    for vol_mmpp_ton in volumen_mmpp_anual_ton:
        vol_producto_kg = vol_mmpp_ton * rendimiento_promedio * 1_000
        bruta_kg = vol_producto_kg * factor_gwp
        evitada_kg = vol_mmpp_ton * 1_000 * AVOIDED_EMISSION_KG_CO2EQ_POR_KG_MMPP
        neta_kg = bruta_kg - evitada_kg

        # Si neta < 0 (más evitadas que emitidas), genera créditos
        # Precio USD/ton × ton evitadas × TC = revenue CLP
        ton_creditos = max(0.0, -neta_kg / 1_000)
        rev_clp = ton_creditos * precio_credito_usd_ton * tc_usd_clp

        emisiones_brutas.append(bruta_kg / 1_000)  # convertir a ton
        emisiones_evitadas.append(evitada_kg / 1_000)
        emisiones_netas.append(neta_kg / 1_000)
        revenue_anual.append(rev_clp)

    neta_total = sum(emisiones_netas)
    return FootprintResult(
        scenario=escenario,
        emisiones_brutas_ton_co2eq_anual=emisiones_brutas,
        emisiones_evitadas_ton_co2eq_anual=emisiones_evitadas,
        emisiones_netas_ton_co2eq_anual=emisiones_netas,
        revenue_creditos_co2_clp_anual=revenue_anual,
        es_carbono_neutro=neta_total <= 0,
        es_carbono_negativo=neta_total < -1.0,  # claramente negativo
    )


def comparar_escenarios_footprint(
    volumen_mmpp_anual_ton: list[float],
    rendimiento_promedio: float = 0.26,
) -> dict:
    """Compara los 3 escenarios LCA + revenue potencial créditos CO₂."""
    out = {}
    for esc in ("baseline", "renovable", "beccs"):
        r = calcular_footprint(volumen_mmpp_anual_ton, rendimiento_promedio, esc)
        out[esc] = {
            "emisiones_netas_5y_ton": sum(r.emisiones_netas_ton_co2eq_anual),
            "emisiones_evitadas_5y_ton": sum(r.emisiones_evitadas_ton_co2eq_anual),
            "revenue_creditos_5y_clp": sum(r.revenue_creditos_co2_clp_anual),
            "es_carbono_neutro": r.es_carbono_neutro,
            "es_carbono_negativo": r.es_carbono_negativo,
            "detalle_anual": {
                "brutas_ton": r.emisiones_brutas_ton_co2eq_anual,
                "evitadas_ton": r.emisiones_evitadas_ton_co2eq_anual,
                "netas_ton": r.emisiones_netas_ton_co2eq_anual,
                "revenue_clp": r.revenue_creditos_co2_clp_anual,
            },
        }
    return out
