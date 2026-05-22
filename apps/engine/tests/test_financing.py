"""Tests del modelo de financiamiento mix deuda/equity."""

from __future__ import annotations

import pytest

from trongkai_engine.financing import (
    EstructuraFinanciamiento,
    TipoAmortizacion,
    calcular_servicio_deuda,
    calcular_tir_equity,
    coverage_ratios,
    estructurar_financiamiento,
)


def test_servicio_deuda_francesa_cuota_constante():
    """Francesa: cuota constante = principal + intereses se reparte."""
    out = calcular_servicio_deuda(
        monto_deuda=1_000_000_000,
        tasa_anual=0.10,
        plazo_anos=5,
        horizonte=5,
        grace_anos=0,
        tipo=TipoAmortizacion.FRANCESA,
    )
    # Cuota anual = 1000M × 0.10 × 1.10^5 / (1.10^5 - 1) ≈ 263.8M
    assert abs(out["cuota_anual_clp"] - 263_797_481) < 1_000_000
    # Saldo final año 5 debería ser ~0
    assert out["saldo_fin"][4] < 1_000


def test_servicio_deuda_grace_anos_solo_intereses():
    out = calcular_servicio_deuda(
        monto_deuda=1_000_000_000,
        tasa_anual=0.10,
        plazo_anos=6,
        horizonte=5,
        grace_anos=2,
        tipo=TipoAmortizacion.FRANCESA,
    )
    # Año 1 y 2 sólo intereses
    assert out["principal_anual"][0] == 0
    assert out["principal_anual"][1] == 0
    assert out["interes_anual"][0] == pytest.approx(100_000_000, rel=0.001)


def test_estructurar_financiamiento_50_50_default():
    """Defaults bancable (DSCR ≥ 1.3): 50% deuda + 50% equity, plazo 10y, grace 2y."""
    capex_anual = [3_000_000_000, 5_000_000_000, 4_000_000_000, 2_000_000_000, 1_000_000_000]
    out = estructurar_financiamiento(capex_anual)
    assert out["capex_total_clp"] == 15_000_000_000
    assert abs(out["monto_deuda_clp"] - 7_500_000_000) < 1  # 50%
    assert abs(out["monto_equity_clp"] - 7_500_000_000) < 1  # 50%


def test_estructurar_solo_equity_sin_deuda():
    e = EstructuraFinanciamiento(deuda_pct=0.0)
    capex_anual = [1_000_000_000]
    out = estructurar_financiamiento(capex_anual, e, horizonte=5)
    assert out["monto_deuda_clp"] == 0
    assert out["intereses_totales_clp"] == 0
    assert out["monto_equity_clp"] == 1_000_000_000


def test_tir_equity_apalanca_returns():
    """TIR equity con deuda barata debe ser > TIR sin deuda (apalancamiento positivo).

    equity_anual = monto APORTADO (positivo) por año. La función lo convierte a salida de cash.
    """
    equity = [1_000_000_000, 0, 0, 0, 0]  # 1B aportado en año 1
    util_neta = [200_000_000, 400_000_000, 500_000_000, 500_000_000, 500_000_000]
    principal = [0, 200_000_000, 200_000_000, 200_000_000, 400_000_000]
    tir = calcular_tir_equity(equity, util_neta, principal, valor_residual=500_000_000)
    assert tir is not None
    # Debe ser > 0 (proyecto rentable) y razonable
    assert 0 < tir < 1.0


def test_tir_equity_none_si_todo_positivo():
    """Sin flujo negativo inicial, TIR no se puede calcular."""
    tir = calcular_tir_equity([0, 0, 0], [100, 100, 100], [0, 0, 0])
    assert tir is None


def test_dscr_saludable_si_ebitda_supera_servicio():
    ebitda = [1_000_000_000, 1_200_000_000, 1_500_000_000, 1_500_000_000, 1_500_000_000]
    servicio = [300_000_000, 300_000_000, 300_000_000, 300_000_000, 300_000_000]
    out = coverage_ratios(ebitda, servicio)
    # DSCR mínimo = 1000/300 ≈ 3.33 (>1.3 healthy)
    assert out["saludable"] is True
    assert out["dscr_minimo"] > 1.3
    assert out["llcr"] > 1.3


def test_dscr_no_saludable_si_servicio_supera_ebitda():
    ebitda = [200_000_000] * 5
    servicio = [300_000_000] * 5
    out = coverage_ratios(ebitda, servicio)
    assert out["saludable"] is False
    assert out["dscr_minimo"] < 1.3
