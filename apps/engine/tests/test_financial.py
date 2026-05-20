"""Tests del módulo financiero — TIR, VAN, payback."""

from __future__ import annotations

import pytest

from trongkai_engine.financial import FlujoMes, KPIsFinancieros, calcular_kpis, tornado_chart


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


def test_tir_none_cuando_npv_no_cruza_cero_en_rango():
    """Si los flujos tienen signos mixtos pero NPV no cambia de signo en [-0.99, 10.0]
    (p.ej. ingreso enorme al inicio y costo chico después), _tir devuelve None.
    Cubre el branch n_low*n_high > 0 en financial._tir."""
    flujos = [
        FlujoMes(mes=1, ingresos_ventas=1000.0),
        FlujoMes(mes=2, costos_directos=1.0),
    ]
    kpis = calcular_kpis(flujos, wacc_anual=0.10)
    assert kpis.tir_proyecto_anual is None
    # VAN igualmente se computa y debe ser positivo
    assert kpis.van > 0


def test_ebitda_margin_se_promedia():
    flujos = make_flujos_baseline(capex_inicial=100_000_000, ebitda_mensual=10_000_000)
    kpis = calcular_kpis(flujos, wacc_anual=0.10)
    # Ingresos = 20M, costos = 10M → margin = 50%
    assert 0.45 < kpis.ebitda_margin_promedio < 0.55


def test_wacc_invalido_falla():
    with pytest.raises(ValueError):
        calcular_kpis([], wacc_anual=1.5)


def _kpis_stub(tir: float | None) -> KPIsFinancieros:
    return KPIsFinancieros(
        tir_proyecto_anual=tir,
        van=0.0,
        payback_meses=None,
        ebitda_margin_promedio=0.0,
        ratio_capex_ventas=0.0,
    )


def test_tornado_chart_ordena_por_magnitud_de_impacto():
    """Caso normal: base_tir + kpis_baja/alta con TIR válidas, ordena por magnitud absoluta del delta."""
    base = _kpis_stub(0.20)
    # variable A: impacto chico (0.18-0.20=-0.02 vs 0.22-0.20=+0.02) → magnitud 0.04
    # variable B: impacto grande (0.10-0.20=-0.10 vs 0.30-0.20=+0.10) → magnitud 0.20
    sens = [
        ("A", 0.10, _kpis_stub(0.18), _kpis_stub(0.22)),
        ("B", 0.20, _kpis_stub(0.10), _kpis_stub(0.30)),
    ]
    out = tornado_chart(base, sens)
    assert [e.variable for e in out] == ["B", "A"]
    assert out[0].impacto_tir_baja == pytest.approx(-0.10)
    assert out[0].impacto_tir_alta == pytest.approx(0.10)
    assert out[0].delta_baja_pct == -0.20
    assert out[0].delta_alta_pct == 0.20


def test_tornado_chart_base_tir_none_deja_impactos_none():
    """Branch: si base_tir es None, ambos impactos quedan en None aunque las TIRs de los kpis existan."""
    base = _kpis_stub(None)
    sens = [("X", 0.10, _kpis_stub(0.18), _kpis_stub(0.22))]
    out = tornado_chart(base, sens)
    assert len(out) == 1
    assert out[0].impacto_tir_baja is None
    assert out[0].impacto_tir_alta is None


def test_tornado_chart_tir_lado_none_deja_solo_ese_lado_en_none():
    """Branch: si kpis_baja.tir es None pero kpis_alta.tir existe, sólo impacto_tir_baja es None."""
    base = _kpis_stub(0.15)
    sens = [("Y", 0.05, _kpis_stub(None), _kpis_stub(0.20))]
    out = tornado_chart(base, sens)
    assert out[0].impacto_tir_baja is None
    assert out[0].impacto_tir_alta == pytest.approx(0.05)


def test_tornado_chart_lista_vacia():
    base = _kpis_stub(0.20)
    assert tornado_chart(base, []) == []
