"""Tests del catalogo nutricional."""
from __future__ import annotations

from trongkai_engine.nutrient_intelligence import (
    PERFILES_NUTRICIONALES, listar_perfiles, perfil_por_sku,
    resumen_completo, score_promedio_portfolio, tam_total_global,
    top_aplicaciones_por_tam, mercados_target,
)


def test_12_perfiles():
    assert len(PERFILES_NUTRICIONALES) == 12


def test_perfil_alperujo_tiene_hidroxitirosol():
    p = perfil_por_sku("HARINA_ALPERUJO")
    assert p is not None
    nombres_compuestos = [c["nombre"] for c in p["compuestos_activos"]]
    assert any("Hidroxitirosol" in n for n in nombres_compuestos)


def test_perfil_licopeno_aplicaciones():
    p = perfil_por_sku("LICOPENO")
    assert p is not None
    assert len(p["aplicaciones"]) >= 2
    mercados = [a["mercado"] for a in p["aplicaciones"]]
    assert "nutraceutica" in mercados


def test_sku_inexistente():
    assert perfil_por_sku("FOO_BAR") is None


def test_score_promedio_portfolio_razonable():
    s = score_promedio_portfolio()
    assert 60 <= s <= 100


def test_tam_total_global_es_substancial():
    """TAM agregado debe ser miles de millones USD."""
    t = tam_total_global()
    assert t >= 10_000_000_000  # > $10B USD


def test_top_aplicaciones():
    top = top_aplicaciones_por_tam(5)
    assert len(top) == 5
    # Ordenado desc por TAM
    tams = [a["tam_global_usd"] for a in top]
    assert tams == sorted(tams, reverse=True)


def test_mercados_target_completo():
    m = mercados_target()
    # Al menos los 4 mercados principales
    for mercado in ["feed_acuicola", "alimentos_humanos", "nutraceutica", "cosmetica"]:
        assert mercado in m
        assert m[mercado]["tam_total"] > 0


def test_resumen_completo_estructura():
    r = resumen_completo()
    for k in ["n_perfiles", "score_promedio_portfolio", "tam_total_global_usd",
              "n_aplicaciones_totales", "n_compuestos_activos_catalogados",
              "top_10_aplicaciones", "mercados_target"]:
        assert k in r


def test_todos_skus_tienen_compuestos():
    for p in PERFILES_NUTRICIONALES:
        # Aceites pueden tener pocos pero deben tener algo
        assert len(p.compuestos_activos) >= 1


def test_todos_skus_tienen_papers():
    """Cada perfil debe tener al menos 1 referencia cientifica."""
    for p in PERFILES_NUTRICIONALES:
        assert len(p.papers_referencia) >= 1, f"{p.sku} sin papers"


def test_listar_perfiles_serializa():
    perfiles = listar_perfiles()
    assert len(perfiles) == 12
    for p in perfiles:
        assert "sku" in p
        assert "compuestos_activos" in p
        assert "aplicaciones" in p
