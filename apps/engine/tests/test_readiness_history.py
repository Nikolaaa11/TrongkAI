"""Tests del módulo readiness_history."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from trongkai_engine import readiness_history as rh


@pytest.fixture
def temp_history_path(monkeypatch):
    """Path temporal aislado por test."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = Path(f.name)
    # Asegurar que no existe al inicio
    path.unlink(missing_ok=True)
    monkeypatch.setattr(rh, "HISTORY_PATH", path)
    yield path
    path.unlink(missing_ok=True)


def test_history_vacio_si_no_existe(temp_history_path):
    history = rh.get_history()
    assert history == []


def test_add_snapshot_persiste(temp_history_path):
    readiness = {
        "score_total": 80.0,
        "interpretacion": "BANKABLE",
        "dimensiones": [
            {"nombre": "Retorno", "score_0_100": 75, "aporte_total": 15},
        ],
    }
    entry = rh.add_snapshot(readiness, evento="LOI firmada")
    assert entry["score"] == 80.0
    assert entry["evento"] == "LOI firmada"

    # Re-leer del disco
    history = rh.get_history()
    assert len(history) == 1
    assert history[0]["score"] == 80.0


def test_multiple_snapshots(temp_history_path):
    for score in [70, 75, 80, 85]:
        rh.add_snapshot({"score_total": score, "interpretacion": "x", "dimensiones": []})

    history = rh.get_history()
    assert len(history) == 4
    scores = [h["score"] for h in history]
    assert scores == [70, 75, 80, 85]


def test_get_history_con_limit(temp_history_path):
    for score in [70, 75, 80, 85]:
        rh.add_snapshot({"score_total": score, "interpretacion": "x", "dimensiones": []})

    last2 = rh.get_history(limit=2)
    assert len(last2) == 2
    assert [h["score"] for h in last2] == [80, 85]


def test_get_evolucion_compacta(temp_history_path):
    rh.add_snapshot({"score_total": 75.5, "interpretacion": "x", "dimensiones": []})
    rh.add_snapshot({"score_total": 78.2, "interpretacion": "x", "dimensiones": []})

    evol = rh.get_evolucion_compacta(limit=10)
    assert len(evol) == 2
    assert evol[0]["score"] == 75.5
    assert "timestamp" in evol[0]


def test_stats_progreso(temp_history_path):
    rh.add_snapshot({"score_total": 70.0, "interpretacion": "x", "dimensiones": []})
    rh.add_snapshot({"score_total": 85.5, "interpretacion": "x", "dimensiones": []})

    s = rh.stats_progreso()
    assert s["total_snapshots"] == 2
    assert s["score_actual"] == 85.5
    assert s["score_inicial"] == 70.0
    assert s["delta"] == 15.5


def test_stats_progreso_vacio(temp_history_path):
    s = rh.stats_progreso()
    assert s["total_snapshots"] == 0
    assert s["score_actual"] is None


def test_cap_max_entries(temp_history_path, monkeypatch):
    """Verifica que no crezca más allá de MAX_ENTRIES."""
    monkeypatch.setattr(rh, "MAX_ENTRIES", 5)
    for i in range(10):
        rh.add_snapshot({"score_total": float(i), "interpretacion": "x", "dimensiones": []})

    history = rh.get_history()
    assert len(history) == 5
    # Los más recientes (5-9) sobreviven
    assert [h["score"] for h in history] == [5.0, 6.0, 7.0, 8.0, 9.0]
