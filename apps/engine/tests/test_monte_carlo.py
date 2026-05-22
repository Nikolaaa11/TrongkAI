"""Tests del simulador Monte Carlo."""

from __future__ import annotations

import pytest

from trongkai_engine.monte_carlo import run_monte_carlo


def test_monte_carlo_corre_y_devuelve_estadisticos():
    """Smoke + sanity: 200 corridas dan percentiles válidos y prob ∈ [0,1]."""
    r = run_monte_carlo(n_runs=200, seed=42)
    assert r.n_runs == 200
    # Algunos percentiles deben existir (rara vez 0 TIRs si hay 200 corridas)
    if r.tir_p50 is not None:
        assert -0.9 <= r.tir_p50 <= 10  # rango sano
    assert 0.0 <= r.prob_tir_supera_wacc <= 1.0
    assert 0.0 <= r.prob_van_positivo <= 1.0


def test_seed_estable():
    """Misma seed → mismos resultados (determinismo)."""
    r1 = run_monte_carlo(n_runs=100, seed=123)
    r2 = run_monte_carlo(n_runs=100, seed=123)
    assert r1.tir_p50 == r2.tir_p50
    assert r1.van_p50 == r2.van_p50


def test_seed_distinto_diferente_resultado():
    """Seeds distintos → resultados (probablemente) distintos."""
    r1 = run_monte_carlo(n_runs=100, seed=1)
    r2 = run_monte_carlo(n_runs=100, seed=999)
    # Con 100 corridas y sigma material, los p50 deberían diferir
    assert r1.tir_p50 != r2.tir_p50 or r1.van_p50 != r2.van_p50


def test_percentiles_ordenados():
    """P5 ≤ P50 ≤ P95 siempre."""
    r = run_monte_carlo(n_runs=500, seed=7)
    if r.tir_p5 is not None and r.tir_p95 is not None:
        assert r.tir_p5 <= r.tir_p50 <= r.tir_p95
    assert r.van_p5 <= r.van_p50 <= r.van_p95


def test_histograma_suma_a_uno():
    r = run_monte_carlo(n_runs=300, seed=11)
    if r.histograma_tir:
        total_fraction = sum(b["fraction"] for b in r.histograma_tir)
        assert abs(total_fraction - 1.0) < 0.01


def test_histograma_no_tiene_bins_vacios_overflow():
    """Cada bin debe ser dict con bin_start, bin_end, count, fraction."""
    r = run_monte_carlo(n_runs=200, seed=3)
    for b in r.histograma_tir:
        assert set(b.keys()) == {"bin_start", "bin_end", "count", "fraction"}
        assert b["bin_end"] >= b["bin_start"]
        assert b["count"] >= 0
