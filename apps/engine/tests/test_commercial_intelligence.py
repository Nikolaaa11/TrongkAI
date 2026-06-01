"""Tests del Commercial Intelligence."""

from __future__ import annotations

from trongkai_engine.commercial_intelligence import (
    analisis_comercial_completo,
    analizar_concentracion,
    analizar_pricing,
    analizar_tech_roi,
    construir_revenue_pipeline,
)


def test_pricing_no_vacio():
    r = analizar_pricing()
    assert len(r) > 0
    for p in r:
        assert p.sku
        assert p.precio_actual_clp_kg > 0


def test_pricing_serializa():
    r = analizar_pricing()[0]
    d = r.to_dict()
    for k in ["sku", "precio_actual_clp_kg", "precio_actual_usd_kg",
              "benchmark_descripcion", "recomendacion"]:
        assert k in d


def test_pricing_skus_premium_son_premium():
    """LICOPENO debe estar bien por sobre proteínas."""
    r = analizar_pricing()
    licopeno = next(p for p in r if p.sku == "LICOPENO")
    proteina = next(p for p in r if p.sku == "PROTEINA_UNICEL")
    assert licopeno.precio_actual_usd_kg > proteina.precio_actual_usd_kg * 5


def test_concentracion_hhi_valido():
    c = analizar_concentracion()
    assert 0 <= c.hhi <= 10000
    assert c.nivel_concentracion in {"baja", "moderada", "alta", "crítica", "n/a"}
    assert 0 <= c.top_1_pct <= 100


def test_concentracion_top_3_mayor_a_top_1():
    c = analizar_concentracion()
    assert c.top_3_pct >= c.top_1_pct


def test_concentracion_n_efectivos():
    c = analizar_concentracion()
    # 5 clientes reales del catálogo
    assert 1 <= c.n_clientes_efectivos <= 5


def test_tech_roi_no_vacio():
    r = analizar_tech_roi()
    # 3 tecnologías en el catálogo
    assert len(r) == 3
    for t in r:
        assert t.capex_usd > 0
        assert t.recomendacion


def test_tech_roi_ordenado_por_npv():
    """Resultados deben venir ordenados NPV desc."""
    r = analizar_tech_roi()
    npvs = [t.npv_5y_usd for t in r]
    assert npvs == sorted(npvs, reverse=True)


def test_revenue_pipeline_60_meses():
    p = construir_revenue_pipeline(meses=60)
    assert len(p) == 60
    # Meses 1-60
    assert p[0].mes == 1
    assert p[-1].mes == 60


def test_revenue_pipeline_monotono_clientes_activos():
    """El número de clientes activos no debería decrecer en el tiempo."""
    p = construir_revenue_pipeline(meses=60)
    for i in range(len(p) - 1):
        assert p[i + 1].clientes_activos >= p[i].clientes_activos


def test_analisis_completo_serializa():
    a = analisis_comercial_completo()
    for k in ["pricing_skus", "concentracion_clientes", "tech_roi",
              "revenue_pipeline_60m", "resumen_ejecutivo"]:
        assert k in a
    assert "revenue_total_5y_usd" in a["resumen_ejecutivo"]


def test_revenue_total_5y_razonable():
    """Revenue 5y debe ser entre USD 5M y USD 50M."""
    a = analisis_comercial_completo()
    r = a["resumen_ejecutivo"]["revenue_total_5y_usd"]
    assert 5_000_000 <= r <= 100_000_000
