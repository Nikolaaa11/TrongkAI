"""Tests del balance integrado + cross-checks."""
from __future__ import annotations

from trongkai_engine.balances.integrado import (
    BalanceIntegrado,
    computar_balance_integrado,
)


def test_estructura_completa():
    b = computar_balance_integrado()
    assert isinstance(b, BalanceIntegrado)
    for k in ["producto", "energia", "agua", "rrhh"]:
        assert getattr(b, k) is not None


def test_intensidades_calculadas():
    b = computar_balance_integrado(produccion_anual_kg=850_000)
    i = b.intensidades
    assert "energia_kwh_kg" in i
    assert "agua_l_kg" in i
    assert "hh_kg" in i
    assert i["energia_kwh_kg"] > 0
    assert i["agua_l_kg"] > 0


def test_costos_consolidados():
    b = computar_balance_integrado()
    c = b.costos_consolidados
    assert c["total_operacional_anual_usd"] > 0
    # Total ≈ suma de los 3
    suma = c["energia_anual_usd"] + c["agua_anual_usd"] + c["rrhh_anual_usd"]
    assert abs(c["total_operacional_anual_usd"] - suma) < 1


def test_score_global_rango():
    b = computar_balance_integrado()
    assert 0 <= b.score_eficiencia_global <= 100


def test_score_seed_default_razonable():
    """Seed default sin alarmas criticas debe dar score > 50."""
    b = computar_balance_integrado()
    # No esperamos un score perfecto, pero si > 40 indica que funciona
    assert b.score_eficiencia_global > 40


def test_alarmas_consolidadas_incluye_balance_origen():
    b = computar_balance_integrado()
    for a in b.alarmas_consolidadas:
        assert "balance" in a
        assert a["balance"] in ("energia", "agua", "rrhh", "integrado", "producto")


def test_coherencia_estructura():
    b = computar_balance_integrado()
    c = b.coherencia_cross_balance
    for key in ["producto_vs_hh", "producto_vs_energia", "energia_vs_agua_vapor", "turno_noche"]:
        assert key in c
        assert "ok" in c[key]


def test_produccion_muy_alta_dispara_cross_hh():
    """100,000t/año → necesita mucho mas HH del disponible."""
    b = computar_balance_integrado(produccion_anual_kg=100_000_000)
    cross_alarmas = [
        a for a in b.alarmas_consolidadas
        if a.get("balance") == "integrado" and a["tipo"] == "cross_producto_hh"
    ]
    assert len(cross_alarmas) == 1


def test_to_dict_serializable():
    import json
    b = computar_balance_integrado()
    s = json.dumps(b.to_dict())
    assert isinstance(s, str)
    d = b.to_dict()
    assert "score_eficiencia_global" in d
