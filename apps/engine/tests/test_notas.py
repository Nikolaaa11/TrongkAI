"""Tests del sistema de notas."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from trongkai_engine import notas as nt


@pytest.fixture
def temp_path(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        p = Path(f.name)
    p.unlink(missing_ok=True)
    monkeypatch.setattr(nt, "NOTAS_PATH", p)
    yield p
    p.unlink(missing_ok=True)


def test_crear_y_listar(temp_path):
    n = nt.crear_nota("celda", "Precio de Venta|HARINA_ALPERUJO", "Validar con Sergio antes del board.")
    assert n["id"].startswith("nota-")
    assert n["entidad_tipo"] == "celda"

    notas = nt.listar_notas_de()
    assert len(notas) == 1


def test_filtro_por_entidad(temp_path):
    nt.crear_nota("celda", "X|A", "nota A")
    nt.crear_nota("celda", "X|B", "nota B")
    nt.crear_nota("lp", "lp-001", "interesado")

    celdas = nt.listar_notas_de(entidad_tipo="celda")
    assert len(celdas) == 2

    una = nt.listar_notas_de(entidad_tipo="celda", entidad_id="X|A")
    assert len(una) == 1
    assert una[0]["texto"] == "nota A"


def test_actualizar(temp_path):
    n = nt.crear_nota("decision", "coh-1", "v1")
    n2 = nt.actualizar_nota(n["id"], texto="v2", tags=["urgente"])
    assert n2 is not None
    assert n2["texto"] == "v2"
    assert n2["tags"] == ["urgente"]


def test_eliminar(temp_path):
    n = nt.crear_nota("lp", "lp-001", "x")
    ok = nt.eliminar_nota(n["id"])
    assert ok
    assert len(nt.listar_notas_de()) == 0


def test_stats(temp_path):
    nt.crear_nota("celda", "X|A", "a", autor="Nicolás")
    nt.crear_nota("celda", "X|B", "b", autor="Sergio")
    nt.crear_nota("lp", "lp-001", "c", autor="Nicolás")

    s = nt.stats_notas()
    assert s["total"] == 3
    assert s["by_tipo"]["celda"] == 2
    assert s["by_autor"]["Nicolás"] == 2


def test_orden_mas_reciente_primero(temp_path):
    import time
    nt.crear_nota("g", "1", "a")
    time.sleep(0.001)
    nt.crear_nota("g", "2", "b")

    notas = nt.listar_notas_de()
    assert notas[0]["texto"] == "b"
