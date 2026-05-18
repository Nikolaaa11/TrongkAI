"""Tests del módulo financiero — TIR, VAN, payback."""

from __future__ import annotations

import pytest

from trongkai_engine.financial import FlujoMes, calcular_kpis


def make_flujos_baseline(capex_inicial: float, ebitda_mensual: float, meses: int = 60) -> list[FlujoMes]:
    flujos = []
    for m in range(1, meses + 1):
        capex = capex_inicial if m == 1 else 0.0
        flujos.append(
            FlujoMes(
                mes=m,
                ingresos_ventas=ebitda_mensual + 10_000_000,
                costos_directos=10_000_000,
                capex_periodo=capex,
            )
        )
    return flujos


def test_tir_positiva_con_proyecto_rentable():
    flujos = make_flujos_baseline(capex_inicial=500_000_000, ebitda_mensual=20_000_000)
    kpis = calcular_kpis(flujos, wacc_anual=0.10)
    assert kpis.tir_proyecto_anual is not None
    assert kpis.tir_proyecto_anual > 0.10  # tiene que superar el WACC


def test_van_positivo_con_proyecto_rentable():
    flujos = make_flujos_baseline(capex_inicial=500_000_000, ebitda_mensual=20_000_000)
    kpis = calcular_kpis(flujos, wacc_anual=0.10)
    assert kpis.van > 0


def test_payback_se_calcula():
    flujos = make_flujos_baseline(capex_inicial=500_000_000, ebitda_mensual=30_000_000)
    kpis = calcular_kpis(flujos, wacc_anual=0.08)
    assert kpis.payback_meses is not None
    assert 1 <= kpis.payback_meses <= 60


def test_proyecto_invertido_no_tiene_tir():
    """Si todos los flujos son negativos, no hay TIR."""
    flujos = [FlujoMes(mes=i, costos_directos=10_000_000) for i in range(1, 13)]
    kpis = calcular_kpis(flujos, wacc_anual=0.10)
    assert kpis.tir_proyecto_anual is None


def test_ebitda_margin_se_promedia():
    flujos = make_flujos_baseline(capex_inicial=100_000_000, ebitda_mensual=10_000_000)
    kpis = calcular_kpis(flujos, wacc_anual=0.10)
    # Ingresos = 20M, costos = 10M → margin = 50%
    assert 0.45 < kpis.ebitda_margin_promedio < 0.55


def test_wacc_invalido_falla():
    with pytest.raises(ValueError):
        calcular_kpis([], wacc_anual=1.5)
