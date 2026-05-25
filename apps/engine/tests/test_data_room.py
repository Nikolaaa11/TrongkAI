"""Tests del módulo data_room."""

from __future__ import annotations

from trongkai_engine.data_room import (
    CHECKLIST_DD,
    Categoria,
    EstadoDD,
    checklist_completo,
    resumen_checklist,
)


def test_checklist_no_vacio():
    assert len(CHECKLIST_DD) >= 30


def test_todos_items_tienen_estado_valido():
    for i in CHECKLIST_DD:
        assert i.estado in {EstadoDD.FALTANTE, EstadoDD.PARCIAL, EstadoDD.COMPLETO}


def test_todas_categorias_cubiertas():
    cats = {i.categoria for i in CHECKLIST_DD}
    assert cats == {
        Categoria.CORPORATIVO,
        Categoria.FINANCIERO,
        Categoria.COMERCIAL,
        Categoria.OPERACIONAL,
        Categoria.ESG,
        Categoria.EQUIPO,
    }


def test_items_completos_tienen_plataforma_link():
    """Los items marcados COMPLETO deben tener link a una página de la plataforma."""
    completos = [i for i in CHECKLIST_DD if i.estado == EstadoDD.COMPLETO]
    for i in completos:
        # Todos los completos vienen de la plataforma → deben tener link
        assert i.plataforma_link != "", f"Item completo sin link: {i.titulo}"


def test_resumen_stats_correctos():
    r = resumen_checklist()
    assert r.total == len(CHECKLIST_DD)
    assert r.completos + r.parciales + r.faltantes == r.total
    assert 0 <= r.pct_completo <= 100
    assert 0 <= r.pct_avance <= 100
    # pct_avance debe ser >= pct_completo (incluye parciales)
    assert r.pct_avance >= r.pct_completo


def test_checklist_completo_serializa():
    d = checklist_completo()
    assert "items" in d
    assert "resumen" in d
    assert len(d["items"]) == len(CHECKLIST_DD)
    for item in d["items"]:
        assert "id" in item
        assert "categoria" in item
        assert "estado" in item


def test_ids_unicos():
    ids = [i.id for i in CHECKLIST_DD]
    assert len(ids) == len(set(ids)), "IDs duplicados"


def test_by_categoria_suma_total():
    r = resumen_checklist()
    suma = sum(c["total"] for c in r.by_categoria.values())
    assert suma == r.total
