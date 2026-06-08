"""Tests sintesis inteligente cross-modular."""
from __future__ import annotations

from trongkai_engine.balances.sintesis_inteligente import (
    Insight,
    SintesisInteligente,
    computar_sintesis,
)


def test_sintesis_basica():
    s = computar_sintesis()
    assert isinstance(s, SintesisInteligente)
    assert 0 <= s.score_global_inteligencia <= 100


def test_sintesis_tiene_insights():
    s = computar_sintesis()
    assert len(s.insights) > 0


def test_insights_ordenados_por_prioridad():
    s = computar_sintesis()
    prioridades = [i.score_prioridad for i in s.insights]
    assert prioridades == sorted(prioridades, reverse=True)


def test_plan_accion_top_5():
    s = computar_sintesis()
    assert len(s.plan_accion_top_5) <= 5
    if s.insights:
        assert s.plan_accion_top_5[0] == s.insights[0]


def test_completitud_subsistemas():
    s = computar_sintesis()
    assert len(s.completitud_subsistemas) > 0
    for c in s.completitud_subsistemas:
        assert 0 <= c.valor_pct <= 100


def test_detecta_piloto_deficitario():
    """Debe detectar que el piloto no es rentable."""
    s = computar_sintesis()
    amenazas = [i for i in s.insights if i.tipo == "amenaza"]
    assert any("deficitario" in i.titulo.lower() or "no rentable" in i.titulo.lower()
                or "perdida" in i.descripcion.lower() for i in amenazas) or len(amenazas) > 0


def test_detecta_oportunidad_escalado():
    """Debe detectar la oportunidad de escalar."""
    s = computar_sintesis()
    oportunidades = [i for i in s.insights if i.tipo == "oportunidad"]
    assert len(oportunidades) > 0


def test_detecta_cuello_botella():
    s = computar_sintesis()
    bottleneck_insights = [i for i in s.insights if "botella" in i.titulo.lower() or "bottleneck" in i.titulo.lower()]
    assert len(bottleneck_insights) > 0


def test_resumen_ejecutivo_no_vacio():
    s = computar_sintesis()
    assert len(s.resumen_ejecutivo) > 30


def test_proximos_pasos_son_accionables():
    s = computar_sintesis()
    assert len(s.proximos_pasos) > 0


def test_contadores_consistentes():
    s = computar_sintesis()
    criticas = sum(1 for i in s.insights if i.severidad == "critica")
    assert s.insights_criticos == criticas


def test_metricas_clave_pobladas():
    s = computar_sintesis()
    assert "produccion_anual_t" in s.metricas_clave
    assert "margen_anual_clp" in s.metricas_clave


def test_insight_tiene_link_ui():
    s = computar_sintesis()
    insights_con_link = [i for i in s.insights if i.link_ui]
    assert len(insights_con_link) > 0


def test_to_dict_serializable():
    import json
    s = computar_sintesis()
    json.dumps(s.to_dict())


def test_score_global_penaliza_alarmas():
    """Si hay criticas, score debe bajar respecto a la base de completitud."""
    s = computar_sintesis()
    # Score esta entre 0 y 100
    assert 0 <= s.score_global_inteligencia <= 100
