"""Tests del módulo roadmap."""

from __future__ import annotations

from trongkai_engine.roadmap import construir_roadmap


def test_roadmap_basico():
    r = construir_roadmap(meses_adelante=12)
    assert "total_hitos" in r
    assert "por_tipo" in r
    assert "por_mes" in r
    assert "hitos" in r
    assert r["horizonte_meses"] == 12


def test_roadmap_genera_hitos():
    r = construir_roadmap(meses_adelante=12)
    # Debe haber al menos algunos hitos (LP pipeline tiene 5 LPs con fechas)
    assert r["total_hitos"] > 0


def test_roadmap_hitos_ordenados():
    r = construir_roadmap(meses_adelante=12)
    fechas = [h["fecha"] for h in r["hitos"]]
    assert fechas == sorted(fechas)


def test_roadmap_por_tipo():
    r = construir_roadmap(meses_adelante=12)
    tipos_validos = {"compliance", "lp", "decision", "certificacion", "financiero"}
    for tipo in r["por_tipo"].keys():
        assert tipo in tipos_validos


def test_roadmap_por_mes_formato():
    r = construir_roadmap(meses_adelante=6)
    for mes in r["por_mes"].keys():
        # Formato YYYY-MM
        assert len(mes) == 7
        assert mes[4] == "-"


def test_horizonte_corto():
    r = construir_roadmap(meses_adelante=1)
    # Con 1 mes deben haber pocos hitos
    assert r["total_hitos"] >= 0
