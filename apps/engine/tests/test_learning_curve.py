"""Tests Wright's Law sobre costos de proceso."""

from __future__ import annotations

import pytest

from trongkai_engine.learning_curve import (
    ahorro_por_aprendizaje_clp,
    aplicar_curva_aprendizaje_a_costos,
    factor_descuento_aprendizaje,
)


def test_factor_es_1_si_volumen_no_supera_base():
    assert factor_descuento_aprendizaje(50, 100, 0.85) == 1.0


def test_factor_85pct_al_doblar():
    """Wright's Law 85%: al doblar el volumen, factor = 0.85."""
    f = factor_descuento_aprendizaje(200, 100, 0.85)
    assert abs(f - 0.85) < 0.001


def test_factor_90pct_al_doblar_food_processing():
    """Food processing typical: 90% learning rate → -10% al doblar."""
    f = factor_descuento_aprendizaje(200, 100, 0.90)
    assert abs(f - 0.90) < 0.001


def test_factor_invalido_lanza_error():
    with pytest.raises(ValueError):
        factor_descuento_aprendizaje(200, 100, learning_rate=1.5)


def test_aplicar_a_costos_produce_5_anos():
    costos = {"SECADO": 180, "ENSACADO": 8}
    vols = [15_000, 25_000, 40_000, 47_500, 50_000]
    out = aplicar_curva_aprendizaje_a_costos(costos, vols, 0.90)
    assert len(out) == 5
    # Año 1: vol_acum = vol_base → factor = 1
    assert abs(out[0]["SECADO"] - 180) < 0.5
    # Año 5: vol_acum mucho mayor → factor < 1 → costo < 180
    assert out[4]["SECADO"] < 180


def test_aplicar_costos_no_aumentan_solo_bajan():
    """Sanity: la curva sólo reduce, nunca aumenta."""
    costos = {"X": 100}
    vols = [1000, 1000, 1000, 1000, 1000]  # plano
    out = aplicar_curva_aprendizaje_a_costos(costos, vols, 0.85)
    for ano in out:
        assert ano["X"] <= 100 + 0.001


def test_ahorro_total_positivo_con_learning():
    costos = {"SECADO": 180, "ENSACADO": 8}
    vols = [15_000, 25_000, 40_000, 47_500, 50_000]
    out = ahorro_por_aprendizaje_clp(costos, vols, 0.90)
    assert out["ahorro_total_clp"] > 0
    assert 0 < out["ahorro_pct"] < 0.5  # ahorro razonable, no astronómico


def test_lr_1_no_genera_ahorro():
    """Learning rate 1.0 = sin aprendizaje, ahorro 0."""
    costos = {"X": 100}
    vols = [1000, 2000, 4000, 8000, 16_000]
    out = ahorro_por_aprendizaje_clp(costos, vols, 1.0)
    assert abs(out["ahorro_total_clp"]) < 1
