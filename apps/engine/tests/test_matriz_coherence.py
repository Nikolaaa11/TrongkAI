"""Tests del módulo matriz_coherence."""

from __future__ import annotations

from trongkai_engine.matriz_coherence import (
    detectar_gaps_coherentes,
    resumen_coherencia,
)


def test_detecta_gaps():
    gaps = detectar_gaps_coherentes()
    # Debe haber al menos los 4 gaps principales (cotización MMPP, precios, opex, certif)
    assert len(gaps) >= 2
    for g in gaps:
        assert g.severidad in {"critica", "alta", "media"}
        assert g.sinergia > 0
        assert g.accion_recomendada
        assert len(g.matrices_afectadas) > 0


def test_gaps_ordenados_por_sinergia():
    """Los gaps deben venir ordenados por sinergia desc."""
    gaps = detectar_gaps_coherentes()
    sinergias = [g.sinergia for g in gaps]
    assert sinergias == sorted(sinergias, reverse=True)


def test_resumen_serializa():
    r = resumen_coherencia()
    d = r.to_dict()
    assert "gaps_coherentes" in d
    assert "total_gaps" in d
    assert "sinergia_total" in d
    assert "matrices_evaluadas" in d
    assert d["sinergia_total"] >= 0


def test_matrices_evaluadas():
    r = resumen_coherencia()
    assert "variables_matrix" in r.matrices_evaluadas
    assert "data_room" in r.matrices_evaluadas


def test_sinergia_total_es_suma_gaps():
    r = resumen_coherencia()
    assert r.sinergia_total == sum(g.sinergia for g in r.gaps_coherentes)
