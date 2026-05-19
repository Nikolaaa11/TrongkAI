"""Tests del Plan 5 Años + entregable M3."""

from __future__ import annotations

import pytest

from trongkai_engine.plan_builder import (
    ParametrosPlan,
    build_plan,
    caso_olivero_1_costo_unitario_kg,
)


def test_plan_genera_60_flujos():
    plan = build_plan()
    assert len(plan.flujos) == 60


def test_plan_tiene_kpis_calculados():
    plan = build_plan()
    assert plan.kpis.van is not None
    assert plan.kpis.ratio_capex_ventas >= 0


def test_plan_ano_5_tiene_mas_ingresos_que_ano_1():
    plan = build_plan()
    # Año 5 con 100% del volumen vs Año 1 con 30%
    assert plan.ingresos_anuales[4] > plan.ingresos_anuales[0]


def test_caso_olivero_1_excel_original():
    """Entregable M3: reproducir el cálculo 'Caso 1 — Olivero 1' del Excel.

    82 km × $1.800 = $147.600 flete.
    Camión 25 ton = 25.000 kg.
    Costo unitario = $147.600 / 25.000 = $5,904 CLP/kg flete.
    Pago recepción Caso 1 = al proveedor le cobramos $10/kg (negativo).
    """
    r = caso_olivero_1_costo_unitario_kg()
    assert r["costo_viaje_clp"] == 147_600
    assert r["costo_unitario_flete_clp_kg"] == pytest.approx(5.904)
    assert r["costo_neto_clp_kg"] == pytest.approx(5.904 + (-10))  # -4.096


def test_parametros_custom_se_usan():
    params = ParametrosPlan(volumen_total_ton_ano=10_000, wacc_anual=0.20)
    plan = build_plan(params)
    assert plan.parametros.volumen_total_ton_ano == 10_000
    assert plan.parametros.wacc_anual == 0.20


def test_capex_se_aplica_solo_en_enero_de_cada_ano():
    plan = build_plan()
    enero_meses = [1, 13, 25, 37, 49]
    for mes in enero_meses:
        f = plan.flujos[mes - 1]
        assert f.capex_periodo > 0, f"mes {mes} debe tener CapEx"
    for mes in range(2, 13):
        f = plan.flujos[mes - 1]
        assert f.capex_periodo == 0
