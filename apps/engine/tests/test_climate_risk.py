"""Tests del modelo de riesgo climático."""

from __future__ import annotations

import random

from trongkai_engine.climate_risk import (
    EVENTOS_CHILE,
    aplicar_afectacion_a_volumen,
    simular_clima_n_corridas,
    simular_eventos_un_ano,
)


def test_eventos_chile_son_4():
    assert len(EVENTOS_CHILE) == 4
    nombres = {e.nombre for e in EVENTOS_CHILE}
    assert "Sequía severa" in nombres


def test_eventos_un_ano_devuelve_lista():
    rng = random.Random(42)
    eventos = simular_eventos_un_ano(rng)
    assert isinstance(eventos, list)
    # Con seed fijo, resultado determinístico
    eventos2 = simular_eventos_un_ano(random.Random(42))
    assert len(eventos) == len(eventos2)


def test_aplicar_afectacion_sin_eventos_no_perdida():
    vol_efect, perdida = aplicar_afectacion_a_volumen(10_000, [])
    assert vol_efect == 10_000
    assert perdida == 0.0


def test_simulacion_n_runs_estadisticos():
    vols = [15_000, 25_000, 40_000, 47_500, 50_000]
    r = simular_clima_n_corridas(vols, n_runs=200, seed=42)
    assert r.n_runs == 200
    assert len(r.volumen_p50_anual) == 5
    # P50 ≤ volumen base (siempre hay alguna pérdida media)
    for i, base in enumerate(vols):
        assert r.volumen_p50_anual[i] <= base
        assert r.volumen_p5_anual[i] <= r.volumen_p50_anual[i] <= r.volumen_p95_anual[i]


def test_seed_estable_clima():
    vols = [10_000] * 5
    r1 = simular_clima_n_corridas(vols, n_runs=100, seed=123)
    r2 = simular_clima_n_corridas(vols, n_runs=100, seed=123)
    assert r1.volumen_p50_anual == r2.volumen_p50_anual


def test_probabilidad_evento_critico_entre_0_y_1():
    vols = [10_000] * 5
    r = simular_clima_n_corridas(vols, n_runs=300, seed=7)
    assert 0 <= r.probabilidad_anyear_con_evento_critico <= 1


def test_perdida_acumulada_p95_mayor_p50():
    vols = [10_000] * 5
    r = simular_clima_n_corridas(vols, n_runs=500, seed=11)
    assert r.perdida_acumulada_p95_pct >= r.perdida_acumulada_p50_pct
