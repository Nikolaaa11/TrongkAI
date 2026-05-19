"""Tests de los 3 escenarios estratégicos."""

from __future__ import annotations

from trongkai_engine.escenarios import (
    comparar_escenarios_estrategicos,
    recomendacion_estrategica,
)


def test_tres_escenarios_se_generan():
    out = comparar_escenarios_estrategicos()
    assert {e.nombre for e in out} == {"PILOTO", "INDUSTRIAL", "EXPANSION"}


def test_capex_total_creciente_con_escala():
    out = comparar_escenarios_estrategicos()
    by = {e.nombre: e for e in out}
    capex_p = sum(by["PILOTO"].resumen.capex_anuales)
    capex_i = sum(by["INDUSTRIAL"].resumen.capex_anuales)
    capex_e = sum(by["EXPANSION"].resumen.capex_anuales)
    assert capex_p < capex_i < capex_e


def test_ingresos_ano5_crecientes_con_escala():
    out = comparar_escenarios_estrategicos()
    by = {e.nombre: e for e in out}
    a5_p = by["PILOTO"].resumen.ingresos_anuales[4]
    a5_i = by["INDUSTRIAL"].resumen.ingresos_anuales[4]
    a5_e = by["EXPANSION"].resumen.ingresos_anuales[4]
    assert a5_p < a5_i < a5_e


def test_recomendacion_tiene_estructura_esperada():
    out = comparar_escenarios_estrategicos()
    rec = recomendacion_estrategica(out)
    assert rec["elegido"] in ("PILOTO", "INDUSTRIAL", "EXPANSION")
    assert "razon" in rec
    assert "vans_b_clp" in rec
    assert set(rec["vans_b_clp"].keys()) == {"PILOTO", "INDUSTRIAL", "EXPANSION"}


def test_recomendacion_explica_van_relativo():
    """Si el upside de EXPANSION supera 1.5× INDUSTRIAL, debería recomendarse."""
    out = comparar_escenarios_estrategicos()
    rec = recomendacion_estrategica(out)
    van_i = rec["vans_b_clp"]["INDUSTRIAL"]
    van_e = rec["vans_b_clp"]["EXPANSION"]
    if van_e > 1.5 * van_i > 0:
        assert rec["elegido"] == "EXPANSION"
    elif van_i > 0:
        assert rec["elegido"] == "INDUSTRIAL"
