"""Tests del módulo snapshot_diff."""

from __future__ import annotations

from trongkai_engine.snapshot_diff import comparar_snapshots


def _snap_minimo(tir=0.30, van=5e9, score=80):
    return {
        "generated_at": "2026-05-25T10:00:00Z",
        "plan": {"kpis": {"tir": tir, "van": van, "payback_meses": 52, "ebitda_margin_promedio": 0.45}},
        "valuation": {"ev_base_clp": 131e9, "moic": 9.0},
        "readiness_score": {"score_total": score},
        "data_room": {"pct_avance": 50},
        "variables_matrix": {"pct_cubierto": 42, "OK_VALIDADO": 0, "PD": 95},
        "alertas": {"criticas": 1},
    }


def test_diff_basico():
    ant = _snap_minimo(tir=0.25, score=70)
    act = _snap_minimo(tir=0.30, score=80)
    diff = comparar_snapshots(ant, act)
    assert diff.fecha_anterior == ant["generated_at"]
    assert len(diff.diffs_financieros) > 0


def test_diff_tir_sube():
    ant = _snap_minimo(tir=0.25)
    act = _snap_minimo(tir=0.30)
    diff = comparar_snapshots(ant, act)
    tir_diff = next(d for d in diff.diffs_financieros if d.nombre == "TIR proyecto")
    assert tir_diff.direccion == "subio"
    assert tir_diff.delta_absoluto is not None
    assert tir_diff.delta_absoluto > 0


def test_cambios_mayores_detectados():
    ant = _snap_minimo(tir=0.20, score=60)
    act = _snap_minimo(tir=0.35, score=85)
    diff = comparar_snapshots(ant, act)
    # Debe detectar cambio en TIR (15pp), score (+25 pts)
    assert any("TIR" in c for c in diff.cambios_mayores)
    assert any("Readiness Score" in c for c in diff.cambios_mayores)


def test_sin_cambios_significativos():
    snap = _snap_minimo()
    diff = comparar_snapshots(snap, snap)
    assert any("Sin cambios" in c or "sin cambios" in c for c in diff.cambios_mayores)


def test_serializa():
    ant = _snap_minimo()
    act = _snap_minimo(score=85)
    d = comparar_snapshots(ant, act).to_dict()
    assert "diffs_financieros" in d
    assert "diffs_score" in d
    assert "diffs_modelo" in d
    assert "cambios_mayores" in d
