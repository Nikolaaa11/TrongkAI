"""Tests del Plan 5 Años + entregable M3."""

from __future__ import annotations

import pytest

from trongkai_engine.plan_builder import (
    ParametrosPlan,
    TornadoSensibilidad,
    _precio_promedio_ponderado,
    build_plan,
    caso_olivero_1_costo_unitario_kg,
    tornado_sensibilidades,
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


def test_tornado_genera_cinco_variables_ordenadas_por_magnitud():
    """El tornado debe shockear las 5 variables clave y ordenarlas por impacto TIR."""
    resultados = tornado_sensibilidades()
    variables = {r.variable for r in resultados}
    assert variables == {"wacc_anual", "precio_promedio", "costo_mmpp", "opex_mensual", "rendimiento_promedio"}
    # Cada entry debe tener TIR baja/alta y VAN baja/alta numéricos
    for r in resultados:
        assert r.delta_pct == pytest.approx(0.20)
        assert r.van_baja != r.van_alta, f"{r.variable} sin swing VAN"
    # Orden descendente por magnitud absoluta del swing TIR
    magnitudes = [r.magnitud_tir for r in resultados]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_magnitud_tir_es_cero_cuando_alguna_tir_es_none():
    """Si una de las TIRs es None, magnitud_tir devuelve 0.0. Cubre línea 240."""
    s = TornadoSensibilidad(
        variable="x", delta_pct=0.2, tir_baja=None, tir_alta=0.15, van_baja=0.0, van_alta=0.0
    )
    assert s.magnitud_tir == 0.0
    s2 = TornadoSensibilidad(
        variable="x", delta_pct=0.2, tir_baja=0.10, tir_alta=None, van_baja=0.0, van_alta=0.0
    )
    assert s2.magnitud_tir == 0.0


def test_precio_promedio_ponderado_con_pesos_cero():
    """Si la suma de pesos es 0, el promedio es 0.0 (división protegida). Cubre línea 262."""
    assert _precio_promedio_ponderado({"A": 100.0, "B": 200.0}, {"A": 0.0, "B": 0.0}) == 0.0
    assert _precio_promedio_ponderado({}, {}) == 0.0


def test_tornado_precio_sube_tir_y_costo_baja_tir():
    """Sanity: subir precios mejora TIR; subir costo MMPP la empeora."""
    resultados = {r.variable: r for r in tornado_sensibilidades()}
    # Precio alto (+20%) => TIR alta > TIR baja
    precio = resultados["precio_promedio"]
    assert precio.tir_alta is not None and precio.tir_baja is not None
    assert precio.tir_alta > precio.tir_baja
    # Costo MMPP alto (+20%) => TIR alta < TIR baja (mayor costo => peor TIR)
    costo = resultados["costo_mmpp"]
    assert costo.tir_alta is not None and costo.tir_baja is not None
    assert costo.tir_alta < costo.tir_baja
