"""Tests precision tracker."""
from __future__ import annotations

from trongkai_engine.balances.precision_tracker import (
    InputCritico,
    NIVEL_SCORE,
    computar_precision,
)


def test_precision_basica():
    r = computar_precision()
    assert 0 <= r.exactitud_global_pct <= 100
    assert r.total_inputs > 0


def test_niveles_score():
    assert NIVEL_SCORE["PD"] < NIVEL_SCORE["OK_PROVISORIO"] < NIVEL_SCORE["OK_VALIDADO"]
    assert NIVEL_SCORE["OK_VALIDADO"] == 1.0


def test_input_critico_prioridad():
    """Prioridad = impacto x gap."""
    i = InputCritico("x", "Test", "equipos", "PD", peso_impacto=0.8)
    # PD score 0.20, gap 0.80, prioridad = 0.8 * 0.80 = 0.64
    assert abs(i.prioridad - 0.64) < 0.01


def test_input_validado_sin_gap():
    i = InputCritico("x", "Test", "equipos", "OK_VALIDADO", peso_impacto=0.9)
    assert i.gap == 0.0
    assert i.prioridad == 0.0


def test_nivel_confianza_textual():
    r = computar_precision()
    assert r.nivel_confianza in ("estimado", "aproximado", "casi exacto", "exacto")


def test_top_para_validar_ordenado():
    r = computar_precision()
    prioridades = [t["prioridad"] for t in r.top_para_validar]
    assert prioridades == sorted(prioridades, reverse=True)


def test_top_para_validar_max_10():
    r = computar_precision()
    assert len(r.top_para_validar) <= 10


def test_por_categoria_completo():
    r = computar_precision()
    for cat in ["equipos", "parametros", "etapas", "mmpp", "comercial"]:
        assert cat in r.por_categoria
        assert "exactitud_pct" in r.por_categoria[cat]


def test_contadores_consistentes():
    r = computar_precision()
    assert r.validados + r.provisorios + r.sin_validar == r.total_inputs


def test_precio_venta_es_alto_impacto():
    """El precio venta debe ser input de impacto 1.0 (define revenue)."""
    r = computar_precision()
    precio = next((t for t in r.top_para_validar if "precio" in t["nombre"].lower()), None)
    # Si esta en top, su peso debe ser maximo
    if precio:
        assert precio["peso_impacto"] >= 0.9


def test_resumen_no_vacio():
    r = computar_precision()
    assert len(r.resumen) > 20


def test_to_dict_serializable():
    import json
    r = computar_precision()
    json.dumps(r.to_dict())


def test_quick_wins_son_provisorios():
    """Quick wins exactitud deben estar en PROVISORIO (faltan poco)."""
    r = computar_precision()
    for q in r.quick_wins_exactitud:
        assert q["nivel"] == "OK_PROVISORIO"
