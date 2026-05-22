"""Tests del Sustainability-Linked Bond calculator."""

from __future__ import annotations

import pytest

from trongkai_engine.slb import (
    KPIS_DEFAULT,
    KpiSlb,
    SlbBondSpec,
    aplicar_step_up,
    evaluar_kpi,
    simular_kpis_optimista_pesimista,
)


def test_evaluar_kpi_subir_cumple():
    k = KpiSlb("test", "ton", 0, [10, 20, 30, 40, 50], direccion="subir")
    assert evaluar_kpi(k, 12, 1) is True  # 12 >= 10
    assert evaluar_kpi(k, 8, 1) is False  # 8 < 10


def test_evaluar_kpi_bajar_cumple():
    k = KpiSlb("emisiones", "ton", 100, [80, 60, 40, 30, 20], direccion="bajar")
    assert evaluar_kpi(k, 75, 1) is True  # 75 <= 80
    assert evaluar_kpi(k, 85, 1) is False


def test_caso_optimista_no_aplica_step_up():
    """Si todos los KPIs cumplen, no hay step-up y los intereses = baseline."""
    bond = SlbBondSpec(
        monto_clp=1_000_000_000, tasa_base_anual=0.085, plazo_anos=5,
        kpis=[KPIS_DEFAULT[0]],  # solo 1 KPI para simplificar
    )
    valores = {KPIS_DEFAULT[0].nombre: list(KPIS_DEFAULT[0].targets_anuales)}
    out = aplicar_step_up(bond, valores, horizonte=5)
    # Spread acumulado = 0 (sin penalización)
    assert out["spread_acumulado_bps_final"] == 0
    assert out["costo_extra_por_incumplimientos_clp"] == 0
    # Tasas todos los años = 8.5%
    for t in out["tasas_anuales_efectivas"]:
        assert abs(t - 0.085) < 1e-6


def test_caso_pesimista_acumula_step_up():
    """Si todos los KPIs fallan, spread acumulado = N años × 25 bps."""
    bond = SlbBondSpec(
        monto_clp=1_000_000_000, tasa_base_anual=0.085, plazo_anos=5,
        kpis=[KPIS_DEFAULT[0]],  # 25 bps per fallo
    )
    valores = {KPIS_DEFAULT[0].nombre: [0, 0, 0, 0, 0]}  # falla todo
    out = aplicar_step_up(bond, valores, horizonte=5)
    # 4 evaluaciones (años 1-4 se evalúan al inicio de años 2-5)
    # Cada una agrega 25 bps → 100 bps acumulado al final
    assert out["spread_acumulado_bps_final"] == 100
    assert out["costo_extra_por_incumplimientos_clp"] > 0


def test_simular_optimista_vs_pesimista():
    bond = SlbBondSpec(
        monto_clp=5_000_000_000, tasa_base_anual=0.085, plazo_anos=5,
        kpis=list(KPIS_DEFAULT),
    )
    out = simular_kpis_optimista_pesimista(bond, horizonte=5)
    assert "caso_optimista" in out
    assert "caso_pesimista" in out
    # Pesimista debe costar más
    assert out["caso_pesimista"]["intereses_totales_clp"] > out["caso_optimista"]["intereses_totales_clp"]
    assert out["incentivo_esg_clp"] > 0


def test_incumplimientos_se_registran_con_detalle():
    bond = SlbBondSpec(
        monto_clp=1_000_000_000, tasa_base_anual=0.085, plazo_anos=5,
        kpis=[KpiSlb("Test", "u", 0, [10, 20, 30, 40, 50])],
    )
    valores = {"Test": [5, 15, 30, 40, 50]}  # falla años 1 y 2, cumple 3-5
    out = aplicar_step_up(bond, valores, horizonte=5)
    # Los incumplimientos se evalúan AL INICIO de cada año siguiente
    # año 1 falla → step-up aplicado desde año 2
    # año 2 falla → step-up adicional desde año 3
    # años 3-5 cumplen, no más step-ups
    incumplimientos = out["incumplimientos"]
    assert len(incumplimientos) == 2
    assert incumplimientos[0]["kpi"] == "Test"
    assert incumplimientos[0]["ano_evaluado"] == 1


def test_default_kpis_son_3():
    assert len(KPIS_DEFAULT) == 3
    nombres = {k.nombre for k in KPIS_DEFAULT}
    assert "Toneladas CO2 evitadas" in nombres
    assert any("feed" in n.lower() for n in nombres)


@pytest.mark.parametrize("ano_invalido", [0, 6, -1, 100])
def test_evaluar_kpi_ano_invalido_devuelve_false(ano_invalido):
    k = KpiSlb("x", "u", 0, [1, 2, 3])
    assert evaluar_kpi(k, 5, ano_invalido) is False
