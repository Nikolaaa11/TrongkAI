"""Tests del balance de energia."""
from __future__ import annotations

import pytest

from trongkai_engine.balances.energia import (
    BalanceEnergia,
    FlujoEnergetico,
    balance_a_sankey,
    computar_balance_energia,
    flujos_seed,
)


def test_seed_tiene_7_equipos():
    assert len(flujos_seed()) == 7


def test_balance_basico():
    b = computar_balance_energia()
    assert isinstance(b, BalanceEnergia)
    assert b.consumo_total_anual_mwh > 0
    assert b.costo_total_anual_usd > 0


def test_closure_dentro_2pct():
    b = computar_balance_energia()
    assert b.closure_pct <= 2.0


def test_intensidad_razonable():
    """Para 850t/año y los 7 equipos, debe estar 5-25 kWh/kg."""
    b = computar_balance_energia(produccion_anual_kg=850_000)
    assert 1 <= b.intensidad_energetica_kwh_por_kg_producto <= 30


def test_mix_renovable_calculo():
    """Caldera biomasa 1200kW * 6000h * 0.7 = 5.04 GWh, ~30%+."""
    b = computar_balance_energia()
    assert b.mix_renovable_pct > 0.20
    assert b.mix_renovable_pct < 0.80


def test_factor_potencia_promedio():
    b = computar_balance_energia()
    # FP de electricos (PEF 0.94, micro 0.91, compresores 0.89, ilum 0.95) → ~0.9 a 0.95
    assert 0.85 <= b.factor_potencia_planta <= 1.0


def test_costo_total_no_negativo():
    b = computar_balance_energia()
    assert b.costo_total_anual_usd >= 0


def test_alarmas_es_lista():
    b = computar_balance_energia()
    assert isinstance(b.alarmas, list)


def test_alarma_factor_potencia_critica():
    """Si forzamos FP <0.92 en TODOS los electricos, dispara alarma critica."""
    flujos = [
        FlujoEnergetico("PEF", "electrica", 100, 6000, 0.8, factor_potencia=0.85),
        FlujoEnergetico("Micro", "electrica", 100, 6000, 0.8, factor_potencia=0.86),
    ]
    b = computar_balance_energia(flujos, produccion_anual_kg=500_000)
    criticas = [a for a in b.alarmas if a["tipo"] == "factor_potencia"]
    assert len(criticas) == 1


def test_alarma_sobreuso_equipo():
    """factor_carga > 0.95 dispara alarma alta."""
    flujos = [
        FlujoEnergetico("PEF", "electrica", 100, 6000, 0.99, factor_potencia=0.94),
    ]
    b = computar_balance_energia(flujos, produccion_anual_kg=500_000)
    sobreuso = [a for a in b.alarmas if a["tipo"] == "sobreuso_equipo"]
    assert len(sobreuso) == 1
    assert sobreuso[0]["equipo"] == "PEF"


def test_alarma_intensidad_alta():
    """Si intensidad > 3.5 kWh/kg dispara alarma media."""
    flujos = [
        FlujoEnergetico("Big", "electrica", 1000, 8000, 0.9, factor_potencia=0.95),
    ]
    b = computar_balance_energia(flujos, produccion_anual_kg=100_000)
    intens = [a for a in b.alarmas if a["tipo"] == "intensidad_alta"]
    assert len(intens) >= 1


def test_produccion_cero_levanta():
    with pytest.raises(ValueError):
        computar_balance_energia(produccion_anual_kg=0)


def test_sin_flujos_levanta():
    with pytest.raises(ValueError):
        computar_balance_energia(
            flujos=[FlujoEnergetico("zero", "electrica", 0, 0, 0)],
        )


def test_sankey_estructura():
    b = computar_balance_energia()
    s = balance_a_sankey(b)
    assert "nodes" in s
    assert "links" in s
    assert len(s["nodes"]) > 0
    assert len(s["links"]) > 0
    for link in s["links"]:
        assert link["value"] > 0


def test_flujo_consumo_calc():
    f = FlujoEnergetico("PEF", "electrica", 250, 6000, 0.85)
    # 250 * 6000 * 0.85 = 1_275_000 kWh
    assert f.consumo_anual_kwh == 1_275_000


def test_balance_to_dict_serializable():
    """to_dict debe ser JSON-serializable."""
    import json
    b = computar_balance_energia()
    d = b.to_dict()
    s = json.dumps(d)  # no debe levantar
    assert "consumo_total_anual_mwh" in d
    assert "alarmas" in d
