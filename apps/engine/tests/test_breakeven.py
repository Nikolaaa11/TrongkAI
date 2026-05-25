"""Tests del módulo break-even."""

from __future__ import annotations

import pytest

from trongkai_engine.breakeven import (
    BreakevenResultado,
    BreakevenSummary,
    breakeven_summary,
    breakeven_un_driver,
)
from trongkai_engine.plan_builder import ParametrosPlan


def test_breakeven_precio_bajada_encuentra_colchon():
    """El precio puede caer hasta cierto punto antes de no superar WACC."""
    res = breakeven_un_driver("precio", "bajada", umbral_tir=0.18)
    assert isinstance(res, BreakevenResultado)
    assert res.tir_base is not None and res.tir_base > 0.18
    # Debe haber un colchón razonable (precio puede bajar al menos algo)
    assert res.shock_breakeven is not None
    assert -0.5 < res.shock_breakeven < 0  # entre -50% y 0


def test_breakeven_costo_mmpp_subida():
    """El costo MMPP puede subir hasta cierto punto."""
    res = breakeven_un_driver("costo_mmpp", "subida", umbral_tir=0.18)
    assert res.tir_base is not None
    # Costo MMPP puede subir bastante porque su peso es bajo en el costeo total
    assert res.shock_breakeven is None or res.shock_breakeven > 0


def test_breakeven_wacc_bajada_no_aplica():
    """Bajar WACC siempre ayuda — no hay break-even por bajada."""
    res = breakeven_un_driver("wacc", "bajada", umbral_tir=0.18)
    assert res.shock_breakeven is None


def test_breakeven_wacc_subida_encuentra_techo():
    """Hay un WACC máximo soportable."""
    res = breakeven_un_driver("wacc", "subida", umbral_tir=0.18)
    # Con umbral = 0.18 (mismo que WACC base), basta un shock pequeño para perder
    assert res.shock_breakeven is not None
    assert res.shock_breakeven >= 0


def test_breakeven_summary_todos_drivers():
    """Summary corre los 4 drivers."""
    s = breakeven_summary(umbral_tir=0.15)
    assert isinstance(s, BreakevenSummary)
    assert len(s.resultados) == 4
    drivers = {r.driver for r in s.resultados}
    assert drivers == {"precio", "costo_mmpp", "wacc", "opex"}


def test_breakeven_to_dict_serializa():
    s = breakeven_summary(umbral_tir=0.15)
    d = s.to_dict()
    assert "resultados" in d
    assert "umbral_tir_aplicado" in d
    assert d["umbral_tir_aplicado"] == 0.15
    assert len(d["resultados"]) == 4
    for r in d["resultados"]:
        assert "driver" in r
        assert "shock_breakeven" in r
        assert "colchon_pct" in r
        assert "direccion" in r


def test_breakeven_driver_mas_sensible():
    """Identifica el driver con menor colchón."""
    s = breakeven_summary(umbral_tir=0.15)
    d = s.to_dict()
    # Si hay al menos un driver con colchón, debe identificarse el más sensible
    drivers_con_colchon = [r for r in s.resultados if r.colchon_pct is not None]
    if drivers_con_colchon:
        assert d["driver_mas_sensible"] is not None
        assert d["driver_mas_sensible"] in {"precio", "costo_mmpp", "wacc", "opex"}


def test_breakeven_direccion_invalida():
    with pytest.raises(ValueError):
        breakeven_un_driver("precio", "lateral", umbral_tir=0.18)  # type: ignore[arg-type]


def test_breakeven_si_base_ya_bajo_umbral():
    """Si la TIR base ya está bajo el umbral, devuelve shock=0."""
    # Forzar parámetros con TIR baja: subir mucho el WACC
    base = ParametrosPlan(wacc_anual=0.40)  # WACC altísimo
    res = breakeven_un_driver("precio", "bajada", umbral_tir=0.45, base_params=base)
    # tir_base con WACC alto probablemente < 0.45
    # En ese caso debe devolver shock=0
    if res.tir_base is not None and res.tir_base < 0.45:
        assert res.shock_breakeven == 0.0
