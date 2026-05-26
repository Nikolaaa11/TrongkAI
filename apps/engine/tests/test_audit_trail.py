"""Tests del audit trail."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from trongkai_engine import audit_trail as at


@pytest.fixture
def temp_path(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        p = Path(f.name)
    p.unlink(missing_ok=True)
    monkeypatch.setattr(at, "AUDIT_PATH", p)
    yield p
    p.unlink(missing_ok=True)


def test_log_y_get(temp_path):
    e = at.log_evento(
        tipo="matriz_celda_actualizada",
        descripcion="Precio HARINA_ALPERUJO: 800 → 850",
        actor="Nicolás",
        valor_anterior=800,
        valor_nuevo=850,
    )
    assert e.tipo == "matriz_celda_actualizada"
    assert e.valor_nuevo == 850

    entries = at.get_audit_trail()
    assert len(entries) == 1
    assert entries[0]["descripcion"].startswith("Precio")


def test_get_audit_trail_filtro_tipo(temp_path):
    at.log_evento("matriz_celda_actualizada", "X")
    at.log_evento("decision_marcada", "Y")
    at.log_evento("matriz_celda_actualizada", "Z")

    matriz_only = at.get_audit_trail(tipo="matriz_celda_actualizada")
    assert len(matriz_only) == 2


def test_orden_mas_reciente_primero(temp_path):
    at.log_evento("otro", "primero")
    at.log_evento("otro", "segundo")
    at.log_evento("otro", "tercero")

    entries = at.get_audit_trail()
    # Más reciente primero
    assert entries[0]["descripcion"] == "tercero"
    assert entries[-1]["descripcion"] == "primero"


def test_stats(temp_path):
    at.log_evento("matriz_celda_actualizada", "A", actor="Nicolás")
    at.log_evento("decision_marcada", "B", actor="Sergio")
    at.log_evento("matriz_celda_actualizada", "C", actor="Nicolás")

    s = at.stats_audit_trail()
    assert s["total_eventos"] == 3
    assert s["by_tipo"]["matriz_celda_actualizada"] == 2
    assert s["by_actor"]["Nicolás"] == 2


def test_cap_max_entries(temp_path, monkeypatch):
    monkeypatch.setattr(at, "MAX_ENTRIES", 5)
    for i in range(10):
        at.log_evento("otro", f"e{i}")

    entries = at.get_audit_trail(limit=100)
    assert len(entries) == 5


def test_clear(temp_path):
    at.log_evento("otro", "x")
    n = at.clear_audit_trail()
    assert n >= 1
    assert at.get_audit_trail() == []
