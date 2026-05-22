"""Tests del working capital cíclico — modelo NWC."""

from __future__ import annotations

import pytest

from trongkai_engine.plan_builder import ParametrosPlan, build_plan


def test_nwc_se_calcula_con_dso_inv_dpo():
    plan = build_plan()
    # NWC año 1 debe ser > 0 (hay ingresos, hay costos, hay inventario)
    assert plan.nwc_anuales[0] > 0
    # NWC crece con ramp-up (vol_pct 0.3 → 1.0)
    assert plan.nwc_anuales[4] > plan.nwc_anuales[0]


def test_delta_nwc_es_diferencia_vs_anio_anterior():
    plan = build_plan()
    # Año 1: delta = NWC_1 - 0
    assert plan.delta_nwc_anuales[0] == pytest.approx(plan.nwc_anuales[0])
    # Año 2..5: delta es diferencia
    for i in range(1, 5):
        expected = plan.nwc_anuales[i] - plan.nwc_anuales[i - 1]
        assert plan.delta_nwc_anuales[i] == pytest.approx(expected)


def test_dso_mayor_aumenta_nwc():
    """Si los clientes pagan más lento (DSO sube), NWC sube."""
    p_normal = ParametrosPlan(dso_dias=50)
    p_lento = ParametrosPlan(dso_dias=90)
    plan_n = build_plan(p_normal)
    plan_l = build_plan(p_lento)
    assert plan_l.nwc_anuales[4] > plan_n.nwc_anuales[4]


def test_dpo_mayor_reduce_nwc():
    """Si pagamos a proveedores más lento (DPO sube), NWC baja."""
    p_normal = ParametrosPlan(dpo_dias=35)
    p_lento = ParametrosPlan(dpo_dias=120)
    plan_n = build_plan(p_normal)
    plan_l = build_plan(p_lento)
    assert plan_l.nwc_anuales[4] < plan_n.nwc_anuales[4]


def test_inventario_mayor_aumenta_nwc():
    """Más días de inventario → más NWC inmovilizado."""
    p_normal = ParametrosPlan(inventario_dias=90)
    p_alto = ParametrosPlan(inventario_dias=180)
    plan_n = build_plan(p_normal)
    plan_a = build_plan(p_alto)
    assert plan_a.nwc_anuales[4] > plan_n.nwc_anuales[4]


def test_nwc_consume_cash_via_capex():
    """El delta NWC se acumula al CapEx en enero del año (cash leaves business)."""
    plan = build_plan()
    # Flujo de enero de cada año debe tener capex > 0
    eneros = [plan.flujos[mes_global - 1] for mes_global in [1, 13, 25, 37, 49]]
    for i, f in enumerate(eneros):
        # CapEx mes 1 = CapEx fijo del año + delta NWC del año
        expected_min = plan.capex_anuales[i]  # al menos el CapEx fijo
        # Si delta NWC > 0 (crece), enero tiene MÁS que solo capex fijo
        if plan.delta_nwc_anuales[i] > 0:
            assert f.capex_periodo > expected_min
