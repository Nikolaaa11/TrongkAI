"""Tests del cálculo de footprint carbono."""

from __future__ import annotations

from trongkai_engine.carbon_footprint import (
    GWP_BASELINE_KG_CO2EQ_POR_KG_PRODUCTO,
    GWP_BECCS_KG_CO2EQ_POR_KG_PRODUCTO,
    calcular_footprint,
    comparar_escenarios_footprint,
)


def test_baseline_emite_pero_menos_que_lo_evitado():
    """Trongkai baseline ya es carbono-neutro porque las emisiones evitadas (residuos
    que no van a vertedero) superan las emisiones del proceso."""
    vols = [15_000, 25_000, 40_000, 47_500, 50_000]
    r = calcular_footprint(vols, escenario="baseline")
    # Avoided 500 kg/kg MMPP × 50.000 ton = 25.000 ton CO2eq
    # Emisiones brutas: 50k × 0.26 × 0.79 = 10.270 ton CO2eq
    # Neta = 10.270 - 25.000 = -14.730 ton (claramente negativo)
    assert r.es_carbono_neutro
    assert r.es_carbono_negativo


def test_beccs_es_mas_negativo_que_baseline():
    vols = [10_000] * 5
    r_baseline = calcular_footprint(vols, escenario="baseline")
    r_beccs = calcular_footprint(vols, escenario="beccs")
    assert sum(r_beccs.emisiones_netas_ton_co2eq_anual) < sum(r_baseline.emisiones_netas_ton_co2eq_anual)


def test_revenue_creditos_es_positivo_si_neta_negativa():
    """Si emisiones netas son negativas (somos sumidero), genera revenue."""
    vols = [50_000] * 5
    r = calcular_footprint(vols, escenario="baseline")
    assert sum(r.revenue_creditos_co2_clp_anual) > 0


def test_comparar_3_escenarios_devuelve_dict():
    vols = [20_000] * 5
    out = comparar_escenarios_footprint(vols)
    assert set(out.keys()) == {"baseline", "renovable", "beccs"}
    for esc in ("baseline", "renovable", "beccs"):
        assert "emisiones_netas_5y_ton" in out[esc]
        assert "revenue_creditos_5y_clp" in out[esc]


def test_beccs_genera_mas_revenue_que_baseline():
    vols = [50_000] * 5
    out = comparar_escenarios_footprint(vols)
    assert out["beccs"]["revenue_creditos_5y_clp"] >= out["baseline"]["revenue_creditos_5y_clp"]


def test_constantes_consistentes_con_literatura():
    # Baseline ≈ 0.79 (paper succinic acid)
    assert 0.5 < GWP_BASELINE_KG_CO2EQ_POR_KG_PRODUCTO < 1.5
    # BECCS = -1.05 (paper ACS)
    assert GWP_BECCS_KG_CO2EQ_POR_KG_PRODUCTO == -1.05
