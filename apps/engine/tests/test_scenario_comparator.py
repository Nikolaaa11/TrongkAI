"""Tests del comparador de escenarios."""

from __future__ import annotations

from trongkai_engine.scenario_comparator import comparar_estrategicos


def test_compara_3_escenarios():
    c = comparar_estrategicos()
    assert len(c.escenarios) == 3
    nombres = {e["nombre"] for e in c.escenarios}
    assert nombres == {"PILOTO", "INDUSTRIAL", "EXPANSION"}


def test_cada_escenario_tiene_metricas_clave():
    c = comparar_estrategicos()
    for e in c.escenarios:
        m = e["metricas"]
        for k in ["tir", "van", "moic", "capex_total", "dscr_promedio_3_5"]:
            assert k in m


def test_mejor_por_metrica_son_validos():
    c = comparar_estrategicos()
    nombres_validos = {"PILOTO", "INDUSTRIAL", "EXPANSION"}
    for metrica, ganador in c.mejor_por_metrica.items():
        assert ganador in nombres_validos


def test_recomendacion_existe():
    c = comparar_estrategicos()
    assert "elegido" in c.recomendacion
    assert "razon" in c.recomendacion
    assert c.recomendacion["elegido"] in {"PILOTO", "INDUSTRIAL", "EXPANSION"}


def test_serialize():
    d = comparar_estrategicos().to_dict()
    assert "escenarios" in d
    assert "mejor_por_metrica" in d
    assert "matriz_ranking" in d
    assert "recomendacion" in d


def test_matriz_ranking_completa():
    """Cada escenario debe tener ranking en todas las métricas."""
    c = comparar_estrategicos()
    for nombre, ranks in c.matriz_ranking.items():
        # Debe rankear en al menos 7 métricas
        assert len(ranks) >= 7
        # Rankings de 1 a 3
        for metrica, rank in ranks.items():
            assert 1 <= rank <= 3
