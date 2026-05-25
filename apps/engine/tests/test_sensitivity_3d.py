"""Tests del módulo sensitivity 3D."""

from __future__ import annotations

import pytest

from trongkai_engine.sensitivity import Sensitivity3DResult, heatmap_3d


def test_heatmap_3d_3x3x3():
    res = heatmap_3d(driver_x="precio", driver_y="costo_mmpp", driver_z="wacc", n=3)
    assert isinstance(res, Sensitivity3DResult)
    # 3x3x3 = 27 puntos
    assert len(res.puntos) == 27
    for p in res.puntos:
        assert "x_pct" in p
        assert "y_pct" in p
        assert "z_pct" in p
        assert "supera_hurdle" in p


def test_heatmap_3d_drivers_distintos():
    with pytest.raises(ValueError):
        heatmap_3d(driver_x="precio", driver_y="precio", driver_z="wacc", n=3)


def test_heatmap_3d_n_invalido():
    with pytest.raises(ValueError):
        heatmap_3d(n=2)
    with pytest.raises(ValueError):
        heatmap_3d(n=15)


def test_heatmap_3d_zona_segura_no_negativa():
    res = heatmap_3d(n=3)
    assert 0 <= res.pct_zona_segura <= 1


def test_heatmap_3d_serializa():
    res = heatmap_3d(n=3)
    d = res.to_dict()
    assert "driver_x" in d
    assert "driver_y" in d
    assert "driver_z" in d
    assert "puntos" in d
    assert "pct_zona_segura" in d
    assert d["n_puntos"] == 27
