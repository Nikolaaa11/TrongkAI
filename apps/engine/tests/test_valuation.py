"""Tests de la valoración EV/EBITDA."""

from __future__ import annotations

from trongkai_engine.plan_builder import build_plan
from trongkai_engine.valuation import (
    MULTIPLE_FOOD_PROCESSING_GLOBAL,
    MULTIPLE_INGREDIENTES_FUNCIONALES_HIGH,
    MULTIPLE_INGREDIENTES_FUNCIONALES_LOW,
    valuar_proyecto_ev_ebitda,
)


def test_valuation_devuelve_rango_ordenado():
    plan = build_plan()
    v = valuar_proyecto_ev_ebitda(plan)
    assert v.ev_clp_low <= v.ev_clp_base <= v.ev_clp_high
    assert v.multiple_low <= v.multiple_base <= v.multiple_high


def test_multiplos_son_los_benchmarks_documentados():
    """Sanity: que estamos usando los múltiplos verificados con WebSearch."""
    plan = build_plan()
    v = valuar_proyecto_ev_ebitda(plan)
    assert v.multiple_base == MULTIPLE_FOOD_PROCESSING_GLOBAL
    assert v.multiple_low == MULTIPLE_INGREDIENTES_FUNCIONALES_LOW
    assert v.multiple_high == MULTIPLE_INGREDIENTES_FUNCIONALES_HIGH


def test_ev_es_ebitda_ano5_por_multiple():
    plan = build_plan()
    v = valuar_proyecto_ev_ebitda(plan)
    assert abs(v.ev_clp_base - v.ebitda_ano5_clp * v.multiple_base) < 1


def test_moic_se_calcula_si_hay_capex():
    plan = build_plan()
    v = valuar_proyecto_ev_ebitda(plan)
    # Plan base tiene CapEx > 0
    assert v.moic_estimado is not None
    assert v.moic_estimado > 0


def test_nota_es_string_descriptivo():
    plan = build_plan()
    v = valuar_proyecto_ev_ebitda(plan)
    assert "EBITDA" in v.nota
    assert "EV" in v.nota
