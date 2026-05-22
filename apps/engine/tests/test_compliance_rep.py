"""Tests del calendario de compliance Ley REP."""

from __future__ import annotations

from datetime import date

from trongkai_engine.compliance_rep import (
    HITOS_LEY_REP,
    Severidad,
    costo_compliance_total_clp,
    hitos_por_estado,
    proximos_hitos,
)


def test_calendario_tiene_al_menos_5_hitos():
    assert len(HITOS_LEY_REP) >= 5


def test_hitos_categorizados_por_estado():
    out = hitos_por_estado(hoy=date(2026, 5, 22))
    assert set(out.keys()) == {"VIGENTE", "CERCANA", "FUTURA", "LEJANA"}
    # Suma de todos los buckets = total
    total = sum(len(v) for v in out.values())
    assert total == len(HITOS_LEY_REP)


def test_ley_rep_2017_es_vigente_en_2026():
    out = hitos_por_estado(hoy=date(2026, 5, 22))
    nombres_vigentes = {h.nombre for h in out["VIGENTE"]}
    assert "Ley 20.920 REP vigente" in nombres_vigentes


def test_reglamento_julio_2026_es_cercano_desde_mayo_2026():
    out = hitos_por_estado(hoy=date(2026, 5, 22))
    # Reglamento sanitario vigor 2026-07-14, está a ~50 días → CERCANA
    nombres_cercanas = {h.nombre for h in out["CERCANA"]}
    assert any("Reglamento sanitario" in n for n in nombres_cercanas)


def test_costo_compliance_ventana_5y_es_positivo():
    out = costo_compliance_total_clp(hoy=date(2026, 5, 22), ventana_anos=5)
    assert out["total_clp"] > 0
    assert out["ventana_anos"] == 5
    assert len(out["detalle"]) > 0


def test_proximos_hitos_orden_cronologico():
    out = proximos_hitos(n=3, hoy=date(2026, 5, 22))
    assert len(out) <= 3
    # Verificar orden
    for i in range(len(out) - 1):
        assert out[i].fecha_vigor <= out[i + 1].fecha_vigor


def test_severidades_son_validas():
    for h in HITOS_LEY_REP:
        assert h.severidad in {Severidad.CRITICA, Severidad.ALTA, Severidad.MEDIA, Severidad.INFORMATIVA}


def test_hito_critico_tiene_accion():
    """Todo hito ALTA o CRITICA debe tener acción requerida documentada."""
    for h in HITOS_LEY_REP:
        if h.severidad in {Severidad.CRITICA, Severidad.ALTA}:
            assert h.accion_requerida.strip(), f"Hito sin acción: {h.nombre}"
