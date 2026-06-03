"""Tests del balance de agua."""
from __future__ import annotations

import pytest

from trongkai_engine.balances.agua import (
    BalanceAgua,
    FlujoAgua,
    balance_a_sankey,
    computar_balance_agua,
    flujos_agua_seed,
)


def test_seed_tiene_5_flujos():
    assert len(flujos_agua_seed()) == 5


def test_balance_basico():
    b = computar_balance_agua()
    assert isinstance(b, BalanceAgua)
    assert b.consumo_total_anual_m3 > 0


def test_closure_dentro_1pct():
    b = computar_balance_agua()
    assert b.closure_pct <= 1.0


def test_intensidad_razonable():
    """Para 850t/año debe estar 1-100 L/kg."""
    b = computar_balance_agua(produccion_anual_kg=850_000)
    assert 0.5 <= b.intensidad_hidrica_l_por_kg_producto <= 100


def test_agua_fresca_y_recirculada_suman():
    b = computar_balance_agua()
    total = b.agua_fresca_m3 + b.agua_recirculada_m3
    assert abs(total - b.consumo_total_anual_m3) < 1


def test_recirculacion_pct():
    """Con 1 flujo recirculado de 9000 m3 y 38500 m3 totales → ~23%."""
    b = computar_balance_agua()
    assert 0.10 < b.agua_recirculada_pct < 0.50


def test_cumplimiento_dga_estructura():
    b = computar_balance_agua()
    assert "Pozo 1 (Parral)" in b.cumplimiento_dga
    info = b.cumplimiento_dga["Pozo 1 (Parral)"]
    for key in ["derecho_l_s", "uso_actual_l_s", "uso_pct_derecho", "ok"]:
        assert key in info


def test_dga_dentro_limite_default():
    """Seed default debe estar dentro del derecho DGA."""
    b = computar_balance_agua()
    assert b.cumplimiento_dga["Pozo 1 (Parral)"]["ok"]


def test_alarma_dga_critica():
    """Forzando caudal alto en Pozo 1, dispara alarma critica."""
    flujos = [
        FlujoAgua("Pozo 1 (Parral)", "pozo_propio", "PEF", "proceso",
                  caudal_m3_h=18.0, horas_operacion_anual=6000, pct_recirculable=0.5),
    ]
    b = computar_balance_agua(flujos, produccion_anual_kg=850_000)
    criticas = [a for a in b.alarmas if a["tipo"] == "dga_excedido"]
    assert len(criticas) == 1


def test_alarma_recirculacion_baja():
    """Solo agua fresca dispara alarma media."""
    flujos = [
        FlujoAgua("Pozo 1 (Parral)", "pozo_propio", "PEF", "proceso",
                  caudal_m3_h=2.0, horas_operacion_anual=6000, pct_recirculable=0.0),
    ]
    b = computar_balance_agua(flujos, produccion_anual_kg=850_000)
    recirc_alarm = [a for a in b.alarmas if a["tipo"] == "recirculacion_baja"]
    assert len(recirc_alarm) == 1


def test_alarma_rile_excesivo():
    """100% no-recirculable y no-vapor dispara alarma alta."""
    flujos = [
        FlujoAgua("Red", "red_publica", "Lavadora", "lavado",
                  caudal_m3_h=5.0, horas_operacion_anual=6000, pct_recirculable=0.0),
    ]
    b = computar_balance_agua(flujos, produccion_anual_kg=850_000)
    rile_alarm = [a for a in b.alarmas if a["tipo"] == "rile_excesivo"]
    assert len(rile_alarm) == 1


def test_caudal_l_s_correcto():
    f = FlujoAgua("Pozo", "pozo_propio", "PEF", "proceso",
                  caudal_m3_h=3.6, horas_operacion_anual=6000, pct_recirculable=0.5)
    # 3.6 m3/h = 1 L/s
    assert abs(f.caudal_l_s - 1.0) < 0.01


def test_costo_total_consistente():
    b = computar_balance_agua()
    suma_individual = sum(f.costo_anual_usd for f in b.flujos)
    assert abs(b.costo_total_anual_usd - suma_individual) < 1


def test_sankey_estructura():
    b = computar_balance_agua()
    s = balance_a_sankey(b)
    assert "nodes" in s
    assert "links" in s
    assert len(s["nodes"]) > 0
    assert len(s["links"]) > 0


def test_produccion_cero_levanta():
    with pytest.raises(ValueError):
        computar_balance_agua(produccion_anual_kg=0)


def test_balance_to_dict_serializable():
    import json
    b = computar_balance_agua()
    s = json.dumps(b.to_dict())  # no debe levantar
    assert isinstance(s, str)
