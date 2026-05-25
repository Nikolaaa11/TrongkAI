"""Tests del Decision Engine."""

from __future__ import annotations

from trongkai_engine.decision_engine import (
    AccionRecomendada,
    generar_acciones_desde_coherencia,
    generar_acciones_desde_data_room,
    generar_acciones_desde_matriz,
    resumen_decisiones,
    todas_las_acciones,
    top_5_acciones,
)


def test_top_5_no_vacio():
    top = top_5_acciones()
    assert len(top) > 0
    assert len(top) <= 5


def test_acciones_tienen_prioridad_ordenada_desc():
    top = top_5_acciones()
    prioridades = [a.prioridad for a in top]
    assert prioridades == sorted(prioridades, reverse=True)


def test_accion_tiene_owner_y_concreta():
    top = top_5_acciones()
    for a in top:
        assert a.owner
        assert a.accion_concreta
        assert a.titulo
        assert a.categoria in {"comercial", "financiero", "operacional", "compliance", "esg", "equipo"}


def test_accion_scoring_normalizado():
    """Todos los componentes 0-100."""
    top = top_5_acciones()
    for a in top:
        for componente in [a.impacto_tir, a.sinergia, a.uplift_readiness, a.quick_win, a.urgencia, a.prioridad]:
            assert 0 <= componente <= 100, f"{componente} fuera de rango"


def test_acciones_coherencia_no_vacio():
    """Hay al menos 1 acción derivada de la coherencia (4 gaps base)."""
    acciones = generar_acciones_desde_coherencia()
    assert len(acciones) >= 2


def test_acciones_data_room():
    """Si hay items faltantes, hay acción consolidada."""
    acciones = generar_acciones_desde_data_room()
    # Hay 20 faltantes en data room, debe generar acción
    assert len(acciones) >= 1


def test_resumen_decisiones_completo():
    r = resumen_decisiones()
    d = r.to_dict()
    assert "top_5" in d
    assert "todas" in d
    assert "quick_wins" in d
    assert "impacto_potencial_tir_pp" in d
    assert "uplift_potencial_readiness" in d
    assert len(d["top_5"]) <= 5


def test_accion_serializa():
    top = top_5_acciones()
    if top:
        d = top[0].to_dict()
        assert all(k in d for k in [
            "id", "titulo", "descripcion", "categoria", "owner",
            "impacto_tir", "sinergia", "uplift_readiness", "quick_win",
            "urgencia", "prioridad", "matrices_impactadas", "accion_concreta",
        ])


def test_quick_wins_son_alto_quick_win():
    r = resumen_decisiones()
    for qw in r.quick_wins:
        assert qw.quick_win > 70
