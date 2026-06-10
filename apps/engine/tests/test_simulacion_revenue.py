"""Tests simulacion revenue + escalas."""
from __future__ import annotations

from trongkai_engine.balances.simulacion_revenue import (
    PRECIOS_VENTA_DEFAULT,
    calcular_capex_piloto,
    comparar_escalas,
    precios_venta_catalogo,
    simular_con_revenue,
)


def test_simular_con_revenue_basico():
    s = simular_con_revenue(periodo="ano")
    assert s.producto_total_kg > 0
    assert s.revenue_total_clp > 0
    assert s.costo_total_clp > 0
    assert s.precio_venta_clp_kg > 0


def test_revenue_es_producto_x_precio():
    s = simular_con_revenue(periodo="ano", precio_venta_clp_kg=1000.0)
    assert abs(s.revenue_total_clp - s.producto_total_kg * 1000) < 1


def test_margen_calculado():
    s = simular_con_revenue(periodo="ano")
    assert abs(s.margen_total_clp - (s.revenue_total_clp - s.costo_total_clp)) < 1


def test_precio_default_por_sku():
    s = simular_con_revenue(periodo="ano", sku_principal="harina_animal_premium")
    assert s.precio_venta_clp_kg == PRECIOS_VENTA_DEFAULT["harina_animal_premium"]


def test_sku_premium_genera_mas_revenue():
    s_basica = simular_con_revenue(periodo="ano", sku_principal="harina_animal_basica")
    s_premium = simular_con_revenue(periodo="ano", sku_principal="nutraceutico_premium")
    assert s_premium.revenue_total_clp > s_basica.revenue_total_clp


def test_capex_piloto_total():
    c = calcular_capex_piloto()
    assert c["total_clp"] > 0
    assert c["equipos_clp"] > 0
    assert c["instalacion_clp"] > 0
    assert c["total_usd"] > 0


def test_capex_incluye_componentes():
    c = calcular_capex_piloto()
    # instalacion = 25% equipos
    assert abs(c["instalacion_clp"] - c["equipos_clp"] * 0.25) < 100


def test_piloto_premium_no_rentable_con_opex_completo():
    """Con OPEX completo (arriendo+labor+agua+flete), el PILOTO no es rentable
    ni con el SKU premium: el piloto prueba tecnologia, la rentabilidad llega
    a escala. Esto es el comportamiento REALISTA esperado."""
    s = simular_con_revenue(periodo="ano", sku_principal="nutraceutico_premium")
    # costo unitario realista de un piloto de ~27 t/ano con lease 22.7M/mes
    assert s.costo_unitario_clp_kg > 10_000
    assert s.margen_total_clp < 0          # piloto no paga
    assert s.payback_simple_anos == float("inf")


def test_premium_rentable_a_escala_industrial():
    """El nutraceutico premium SI es rentable a escala industrial (x10+),
    donde los costos fijos se diluyen sobre mucho mas volumen."""
    r = comparar_escalas(sku_principal="nutraceutico_premium")
    por_escala = {e["escala"]: e for e in r["escalas"]}
    assert por_escala[1]["margen_clp"] < 0          # piloto no paga
    assert por_escala[10]["margen_clp"] > 0         # x10 ya es rentable
    assert por_escala[100]["margen_clp"] > por_escala[10]["margen_clp"]


def test_harina_animal_nunca_rentable():
    """La harina animal (commodity) no es rentable ni a escala: no es el negocio."""
    r = comparar_escalas(sku_principal="harina_animal_premium")
    for e in r["escalas"]:
        assert e["margen_clp"] < 0


def test_payback_infinito_si_margen_negativo():
    """Si precio muy bajo el margen es negativo -> payback = inf."""
    s = simular_con_revenue(periodo="ano", precio_venta_clp_kg=10.0)
    assert s.payback_simple_anos == float("inf")


def test_revenue_mensual_12_meses():
    s = simular_con_revenue(periodo="ano")
    assert len(s.revenue_mensual) == 12
    for m in s.revenue_mensual:
        assert "revenue_clp" in m
        assert "margen_clp" in m


def test_comparar_escalas_4_resultados():
    r = comparar_escalas()
    assert "escalas" in r
    assert len(r["escalas"]) == 4   # x1, x10, x50, x100


def test_escalas_producto_crece_lineal():
    r = comparar_escalas()
    base = r["escalas"][0]["producto_kg_ano"]
    for e in r["escalas"]:
        assert abs(e["producto_kg_ano"] - base * e["escala"]) < 1


def test_escalas_costo_unitario_baja():
    """Curva 80%: a mayor escala menor costo unitario."""
    r = comparar_escalas()
    costos = [e["costo_unitario_clp_kg"] for e in r["escalas"]]
    assert costos[0] > costos[1] > costos[2] > costos[3]


def test_escalas_capex_subliineal():
    """Williams 0.7: CAPEX crece menos que linealmente."""
    r = comparar_escalas()
    base_capex = r["escalas"][0]["capex_clp"]
    x10 = r["escalas"][1]["capex_clp"]
    # CAPEX x10 NO debe ser 10x el base, debe ser ~5x (10^0.7)
    assert x10 < base_capex * 10


def test_precios_catalogo_4_skus():
    c = precios_venta_catalogo()
    assert len(c["skus"]) >= 4


def test_to_dict_serializable():
    import json
    s = simular_con_revenue(periodo="ano")
    json.dumps(s.to_dict())


def test_periodo_mes_revenue():
    s = simular_con_revenue(periodo="mes")
    assert s.producto_total_kg > 0
    assert s.payback_simple_anos > 0


def test_factor_aprendizaje_decreciente():
    r = comparar_escalas()
    for e in r["escalas"]:
        assert 0 < e["factor_aprendizaje"] <= 1.0
    # x1 = factor 1.0, x100 = 0.8^log2(100) ~ 0.32
    assert r["escalas"][0]["factor_aprendizaje"] == 1.0
    assert r["escalas"][-1]["factor_aprendizaje"] < 0.5


def test_margen_por_sku_estructura():
    """La tabla margen-por-SKU cubre los 4 SKU con veredicto."""
    from trongkai_engine.balances.simulacion_revenue import margen_por_sku
    r = margen_por_sku()
    assert len(r["skus"]) == 4
    for f in r["skus"]:
        assert f["veredicto"]
        assert f["margen_piloto_clp"] < 0   # piloto deficitario con todos


def test_margen_por_sku_verdad_estrategica():
    """Nutraceutico rentable desde x10; harina animal nunca; orden por escala."""
    from trongkai_engine.balances.simulacion_revenue import margen_por_sku
    r = margen_por_sku()
    por_sku = {f["sku"]: f for f in r["skus"]}
    assert por_sku["nutraceutico_premium"]["escala_minima_rentable"] == 10
    assert por_sku["harina_animal_premium"]["escala_minima_rentable"] is None
    assert por_sku["harina_animal_basica"]["escala_minima_rentable"] is None
    # El primero de la lista es el que paga antes
    assert r["skus"][0]["sku"] == "nutraceutico_premium"
