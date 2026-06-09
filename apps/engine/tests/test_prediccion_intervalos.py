"""Tests prediccion con bandas de confianza."""
from __future__ import annotations

from trongkai_engine.balances.prediccion_intervalos import (
    INCERTIDUMBRE_NIVEL,
    computar_prediccion,
)


def test_prediccion_basica():
    p = computar_prediccion(n_sims=500)
    assert p.n_simulaciones == 500
    assert len(p.bandas) == 4


def test_incertidumbre_decrece_con_validacion():
    """PD debe tener mas incertidumbre que VALIDADO."""
    assert INCERTIDUMBRE_NIVEL["PD"] > INCERTIDUMBRE_NIVEL["OK_PROVISORIO"] > INCERTIDUMBRE_NIVEL["OK_VALIDADO"]


def test_bandas_ordenadas_p10_p50_p90():
    p = computar_prediccion(n_sims=2000)
    for b in p.bandas.values():
        assert b["p10"] <= b["p50"] <= b["p90"]


def test_margen_error_positivo():
    p = computar_prediccion(n_sims=1000)
    assert p.margen_error_global_pct > 0


def test_esperado_dentro_de_banda():
    p = computar_prediccion(n_sims=2000)
    for b in p.bandas.values():
        # El esperado (media) cae dentro de p10-p90 con tolerancia de medio
        # ancho de banda (robusto ante valores negativos como el margen).
        ancho = b["p90"] - b["p10"]
        assert (b["p10"] - 0.5 * ancho) <= b["esperado"] <= (b["p90"] + 0.5 * ancho)


def test_drivers_incertidumbre_ordenados():
    p = computar_prediccion(n_sims=500)
    incs = [d["incertidumbre_pct"] for d in p.drivers_incertidumbre]
    assert incs == sorted(incs, reverse=True)


def test_precio_es_top_driver_incertidumbre():
    """Precio venta (PD) debe ser de los mayores drivers de incertidumbre."""
    p = computar_prediccion(n_sims=500)
    top = p.drivers_incertidumbre[0]
    assert "Precio" in top["input"] or "Arriendo" in top["input"]


def test_sku_premium_mayor_revenue():
    p_basica = computar_prediccion(sku_principal="harina_animal_basica", n_sims=1000)
    p_premium = computar_prediccion(sku_principal="nutraceutico_premium", n_sims=1000)
    assert p_premium.bandas["revenue_anual_mclp"]["esperado"] > p_basica.bandas["revenue_anual_mclp"]["esperado"]


def test_reproducible_misma_semilla():
    """Misma semilla -> mismo resultado (determinista)."""
    p1 = computar_prediccion(n_sims=1000)
    p2 = computar_prediccion(n_sims=1000)
    assert p1.bandas["costo_unitario_clp_kg"]["p50"] == p2.bandas["costo_unitario_clp_kg"]["p50"]


def test_interpretacion_no_vacia():
    p = computar_prediccion(n_sims=500)
    assert len(p.interpretacion) > 30


def test_to_dict_serializable():
    import json
    p = computar_prediccion(n_sims=500)
    json.dumps(p.to_dict())
