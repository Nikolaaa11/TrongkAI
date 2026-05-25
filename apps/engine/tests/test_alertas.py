"""Tests del sistema de alertas."""

from __future__ import annotations

from trongkai_engine.alertas import Alerta, ResumenAlertas, escanear_alertas


def test_escanear_alertas_no_falla():
    r = escanear_alertas()
    assert isinstance(r, ResumenAlertas)


def test_alertas_tienen_campos_validos():
    r = escanear_alertas()
    for a in r.alertas:
        assert a.id
        assert a.titulo
        assert a.tipo in {"financiera", "bancabilidad", "riesgo", "compliance", "macro", "modelo", "esg", "progreso"}
        assert a.nivel in {"critica", "alta", "media", "baja", "info"}
        assert a.accion_sugerida


def test_alertas_ordenadas_por_nivel():
    """Críticas primero, luego altas, etc."""
    r = escanear_alertas()
    NIVEL_ORDER = {"critica": 0, "alta": 1, "media": 2, "baja": 3, "info": 4}
    niveles = [NIVEL_ORDER[a.nivel] for a in r.alertas]
    assert niveles == sorted(niveles)


def test_resumen_serializa():
    r = escanear_alertas()
    d = r.to_dict()
    assert "total" in d
    assert "criticas" in d
    assert "altas" in d
    assert "by_tipo" in d
    assert "alertas" in d


def test_resumen_totales_consistentes():
    r = escanear_alertas()
    d = r.to_dict()
    assert d["total"] == len(d["alertas"])
    assert d["criticas"] + d["altas"] + d["medias"] + d["bajas"] <= d["total"]
