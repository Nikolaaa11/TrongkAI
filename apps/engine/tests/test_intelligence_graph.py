"""Tests del Intelligence Graph."""

from __future__ import annotations

from trongkai_engine.intelligence_graph import (
    EDGES,
    NODOS,
    grafo_completo,
    impacto_de_cambio,
)


def test_grafo_no_vacio():
    g = grafo_completo()
    assert len(g["nodos"]) > 10
    assert len(g["edges"]) > 10
    assert g["stats"]["total_nodos"] == len(NODOS)
    assert g["stats"]["total_edges"] == len(EDGES)


def test_todos_edges_apuntan_a_nodos_validos():
    ids_nodos = {n.id for n in NODOS}
    for e in EDGES:
        assert e.desde in ids_nodos, f"Edge {e.desde} → {e.hacia}: origen no existe"
        assert e.hacia in ids_nodos, f"Edge {e.desde} → {e.hacia}: destino no existe"


def test_pesos_normalizados():
    for e in EDGES:
        assert 0 <= e.peso <= 1


def test_impacto_matriz_variables_es_grande():
    """matriz-variables impacta plan, sensitivity, readiness, etc."""
    impactados = impacto_de_cambio("matriz-variables", profundidad=3)
    # Al menos 5 módulos impactados
    assert len(impactados) >= 5
    labels = {i["label"] for i in impactados}
    # Plan 5 años debe estar impactado
    assert any("Plan" in l for l in labels)


def test_impacto_input_equipo_llega_a_pdf():
    """Cambio en datos del equipo debe propagarse hasta PDF tearsheet."""
    impactados = impacto_de_cambio("equipo-input", profundidad=5)
    labels = {i["label"] for i in impactados}
    assert any("PDF" in l for l in labels) or any("LP Pack" in l for l in labels)


def test_grafo_tiene_decision_node():
    g = grafo_completo()
    ids = {n["id"] for n in g["nodos"]}
    assert "decision" in ids


def test_grafo_serializa_completo():
    g = grafo_completo()
    for n in g["nodos"]:
        assert "id" in n
        assert "label" in n
        assert "tipo" in n
    for e in g["edges"]:
        assert "desde" in e
        assert "hacia" in e
        assert "tipo" in e
