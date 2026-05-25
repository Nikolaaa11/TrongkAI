"""Tests del módulo sensitivity heatmap 2D."""

from __future__ import annotations

import pytest

from trongkai_engine.sensitivity import (
    HeatmapResultado,
    _aplicar_shock,
    _rango_default,
    heatmap_2d,
)
from trongkai_engine.plan_builder import ParametrosPlan


def test_rango_default_precio_simetrico():
    r = _rango_default("precio", 7)
    assert len(r) == 7
    assert r[0] == -0.25
    assert r[-1] == 0.25
    # Punto medio en 0
    assert abs(r[3]) < 1e-6


def test_rango_default_wacc_incluye_subida_tasa():
    r = _rango_default("wacc", 7)
    assert r[0] == -0.04
    assert r[-1] == 0.05
    assert len(r) == 7


def test_aplicar_shock_precio_escala_todos_skus():
    base = ParametrosPlan()
    precio_orig = base.precios_clp_kg["LICOPENO"]
    shocked = _aplicar_shock(base, "precio", -0.25)
    # Todos los precios deben bajar 25%
    assert shocked.precios_clp_kg["LICOPENO"] == pytest.approx(precio_orig * 0.75)
    assert shocked.precios_clp_kg["HARINA_ALPERUJO"] == pytest.approx(800 * 0.75)


def test_aplicar_shock_costo_mmpp():
    base = ParametrosPlan()
    shocked = _aplicar_shock(base, "costo_mmpp", 0.20)
    assert shocked.costo_mmpp_clp_kg == pytest.approx(30 * 1.20)


def test_aplicar_shock_wacc_es_aditivo():
    base = ParametrosPlan()
    shocked = _aplicar_shock(base, "wacc", 0.02)
    # WACC: +200 bps absolutos sobre 18% = 20%
    assert shocked.wacc_anual == pytest.approx(0.20)


def test_heatmap_2d_basico_no_falla():
    res = heatmap_2d(driver_x="precio", driver_y="costo_mmpp", n=5)
    assert isinstance(res, HeatmapResultado)
    assert res.n_celdas_totales == 25  # 5x5
    assert len(res.celdas) == 25
    assert res.driver_x == "precio"
    assert res.driver_y == "costo_mmpp"


def test_heatmap_celda_central_aproxima_base():
    """La celda central (shock=0,0) debe coincidir con plan base."""
    res = heatmap_2d(driver_x="precio", driver_y="costo_mmpp", n=5)
    # Buscar la celda central
    centrales = [c for c in res.celdas if abs(c.eje_x_pct) < 1e-6 and abs(c.eje_y_pct) < 1e-6]
    assert len(centrales) == 1
    central = centrales[0]
    assert central.tir is not None
    # TIR central debe estar cerca de la base (mismas params)
    assert abs(central.tir - (res.tir_base or 0)) < 0.01


def test_heatmap_zona_segura_existe():
    """Con hurdle bajo, debe haber al menos algunas zonas seguras."""
    res = heatmap_2d(driver_x="precio", driver_y="costo_mmpp", n=5, hurdle_pct=0.10)
    assert res.n_celdas_seguras > 0
    assert 0 <= res.pct_zona_segura <= 1


def test_heatmap_to_dict_serializa():
    res = heatmap_2d(driver_x="precio", driver_y="costo_mmpp", n=3)
    d = res.to_dict()
    assert "celdas" in d
    assert "rango_x" in d
    assert "rango_y" in d
    assert d["n_celdas_totales"] == 9
    # Cada celda serializada tiene campos clave
    for c in d["celdas"]:
        assert "x_pct" in c
        assert "y_pct" in c
        assert "tir" in c
        assert "supera_hurdle" in c


def test_heatmap_drivers_iguales_lanza_error():
    with pytest.raises(ValueError):
        heatmap_2d(driver_x="precio", driver_y="precio", n=3)


def test_heatmap_n_fuera_de_rango():
    with pytest.raises(ValueError):
        heatmap_2d(driver_x="precio", driver_y="costo_mmpp", n=2)
    with pytest.raises(ValueError):
        heatmap_2d(driver_x="precio", driver_y="costo_mmpp", n=20)


def test_heatmap_precio_vs_wacc():
    """Smoke test del pair precio × wacc."""
    res = heatmap_2d(driver_x="precio", driver_y="wacc", n=5)
    assert res.driver_y == "wacc"
    # WACC + alto debe bajar TIR (en celdas con shock positivo de WACC)
    celdas_wacc_alto = [c for c in res.celdas if c.eje_y_pct > 0.02 and c.tir is not None]
    assert len(celdas_wacc_alto) > 0


def test_curva_1d_basica():
    from trongkai_engine.sensitivity import curva_1d, CurvaSensibilidad
    c = curva_1d("precio", n=11)
    assert isinstance(c, CurvaSensibilidad)
    assert len(c.puntos) == 11
    assert c.driver == "precio"
    assert c.tir_base is not None


def test_curva_1d_monotona_precio():
    """TIR creciente con precio."""
    from trongkai_engine.sensitivity import curva_1d
    c = curva_1d("precio", n=7)
    tirs = [p.tir for p in c.puntos if p.tir is not None]
    for i in range(len(tirs) - 1):
        assert tirs[i] <= tirs[i + 1] + 1e-6


def test_curva_1d_monotona_costo_decreciente():
    """TIR decreciente con costo MMPP."""
    from trongkai_engine.sensitivity import curva_1d
    c = curva_1d("costo_mmpp", n=7)
    tirs = [p.tir for p in c.puntos if p.tir is not None]
    for i in range(len(tirs) - 1):
        assert tirs[i] >= tirs[i + 1] - 1e-6


def test_curvas_todos_drivers():
    from trongkai_engine.sensitivity import curvas_todos_drivers
    d = curvas_todos_drivers(n=5)
    assert d["n"] == 5
    assert len(d["curvas"]) == 4
    drivers = {c["driver"] for c in d["curvas"]}
    assert drivers == {"precio", "costo_mmpp", "wacc", "opex"}


def test_heatmap_monotonia_precio():
    """Al subir el precio, la TIR debe subir (a costo MMPP constante)."""
    res = heatmap_2d(driver_x="precio", driver_y="costo_mmpp", n=5)
    # Tomar todas las celdas con costo_mmpp shock=0
    celdas_costo_cero = [c for c in res.celdas if abs(c.eje_y_pct) < 1e-6 and c.tir is not None]
    celdas_costo_cero.sort(key=lambda c: c.eje_x_pct)
    tirs = [c.tir for c in celdas_costo_cero]
    # TIR debe ser monótona creciente en precio
    for i in range(len(tirs) - 1):
        assert tirs[i] <= tirs[i + 1] + 1e-6, f"No monótono: {tirs}"
