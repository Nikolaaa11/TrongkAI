"""Tests de los 3 escenarios estratégicos."""

from __future__ import annotations

from dataclasses import replace

from trongkai_engine.escenarios import (
    EscenarioEstrategico,
    comparar_escenarios_estrategicos,
    recomendacion_estrategica,
)
from trongkai_engine.financial import KPIsFinancieros
from trongkai_engine.plan_builder import ParametrosPlan, ResumenPlan


def _stub_escenario(nombre: str, van: float, wacc: float = 0.18) -> EscenarioEstrategico:
    """Construye un EscenarioEstrategico mínimo con VAN/WACC controlados.

    No corre build_plan: arma ResumenPlan/KPIsFinancieros vacíos para testear
    sólo la lógica de recomendacion_estrategica.
    """
    params = replace(ParametrosPlan(), wacc_anual=wacc)
    kpis = KPIsFinancieros(
        tir_proyecto_anual=0.25,
        van=van,
        payback_meses=36,
        ebitda_margin_promedio=0.20,
        ratio_capex_ventas=0.10,
    )
    resumen = ResumenPlan(
        flujos=[],
        kpis=kpis,
        parametros=params,
        ingresos_anuales=[],
        ebitda_anuales=[],
        capex_anuales=[],
    )
    return EscenarioEstrategico(
        nombre=nombre,
        descripcion=f"stub {nombre}",
        parametros=params,
        resumen=resumen,
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


def test_recomendacion_wacc_alto_fuerza_piloto():
    """Si WACC > 0.20, la heurística elige PILOTO sin importar los VAN."""
    stubs = [
        _stub_escenario("PILOTO", van=1e9, wacc=0.25),
        _stub_escenario("INDUSTRIAL", van=50e9, wacc=0.25),
        _stub_escenario("EXPANSION", van=200e9, wacc=0.25),
    ]
    rec = recomendacion_estrategica(stubs)
    assert rec["elegido"] == "PILOTO"
    assert "WACC" in rec["razon"]


def test_recomendacion_van_industrial_negativo_cae_a_piloto():
    """Si ningún escenario da VAN positivo (INDUSTRIAL ≤ 0), cae a PILOTO."""
    stubs = [
        _stub_escenario("PILOTO", van=-1e9),
        _stub_escenario("INDUSTRIAL", van=-5e9),
        _stub_escenario("EXPANSION", van=-3e9),
    ]
    rec = recomendacion_estrategica(stubs)
    assert rec["elegido"] == "PILOTO"
    assert "no positivo" in rec["razon"]


def test_recomendacion_incluye_tirs_pct_por_escenario():
    """El dict de salida debe exponer tirs_pct para los 3 escenarios."""
    out = comparar_escenarios_estrategicos()
    rec = recomendacion_estrategica(out)
    assert "tirs_pct" in rec
    assert set(rec["tirs_pct"].keys()) == {"PILOTO", "INDUSTRIAL", "EXPANSION"}
