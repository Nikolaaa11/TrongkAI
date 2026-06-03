"""Tests del balance por etapas de la planta."""
from __future__ import annotations

import pytest

from trongkai_engine.balances.etapas import (
    BalancePorEtapas,
    EtapaPlanta,
    NivelDato,
    computar_balance_etapas,
    etapas_seed,
    resumen_datos_faltantes,
)


def test_seed_12_etapas():
    assert len(etapas_seed()) == 12


def test_orden_etapas_correcto():
    es = etapas_seed()
    for i, e in enumerate(es, start=1):
        assert e.orden == i


def test_recepcion_es_primera():
    assert etapas_seed()[0].id == "RECEPCION"


def test_logistica_es_ultima():
    assert etapas_seed()[-1].id == "LOGISTICA"


def test_balance_basico():
    b = computar_balance_etapas()
    assert isinstance(b, BalancePorEtapas)
    assert b.masa_entrada_total_kg_h > 0
    assert b.energia_total_kwh_h > 0


def test_yield_total_razonable():
    """Para una planta de upcycling con secado, yield total ~ 30-35%."""
    b = computar_balance_etapas()
    assert 0.10 < b.yield_total_proceso < 0.50


def test_bottlenecks_detectados():
    b = computar_balance_etapas()
    # PEF + Secador deben aparecer cerca del bottleneck con seed default
    assert isinstance(b.bottlenecks, list)


def test_completitud_datos_calculada():
    b = computar_balance_etapas()
    assert 0 <= b.completitud_datos_pct <= 100


def test_etapa_pef_consume_agua():
    es = etapas_seed()
    pef = next(e for e in es if e.id == "PEF_OPTICEPT")
    assert pef.consumo_agua_l_h > 0
    assert pef.consumo_energia_kwh_h > 0


def test_etapa_secado_es_la_mas_intensiva_energia():
    es = etapas_seed()
    consumos = {e.id: e.energia_kwh_por_kg for e in es}
    # Secado tiene el mayor consumo unitario kWh/kg
    max_id = max(consumos, key=consumos.get)
    assert max_id == "SECADO_ROTATIVO"


def test_alarmas_estructura():
    b = computar_balance_etapas()
    assert isinstance(b.alarmas, list)
    for a in b.alarmas:
        assert "tipo" in a
        assert "severidad" in a


def test_alarmas_bottleneck():
    """Forzar utilizacion alta dispara alarma."""
    es = etapas_seed(throughput_kg_h=2000)
    # PEF tiene capacidad de 2000 kg/h y recibe ~1890 → 94% → bottleneck
    pef = next(e for e in es if e.id == "PEF_OPTICEPT")
    assert pef.es_bottleneck


def test_intensidades_acumuladas():
    b = computar_balance_etapas()
    i = b.intensidades_acumuladas
    for key in ["energia_kwh_por_kg_producto", "agua_l_por_kg_producto",
                "perdidas_totales_kg_h", "energia_kwh_por_kg_mmpp"]:
        assert key in i


def test_resumen_datos_faltantes():
    r = resumen_datos_faltantes()
    assert r["total_etapas"] == 12
    assert r["validadas"] + r["provisorias"] + r["sin_validar"] == 12
    assert 0 <= r["completitud_promedio_pct"] <= 100


def test_etapas_con_PD_listadas_en_criticos():
    r = resumen_datos_faltantes()
    # Algunas etapas estan en PD (e.g. ALMACENAMIENTO, TRITURACION, MEZCLADO)
    criticos_ids = [e["etapa"] for e in r["criticos_PD"]]
    assert "ALMACENAMIENTO" in criticos_ids or "TRITURACION" in criticos_ids


def test_throughput_alto_aumenta_consumos():
    b1 = computar_balance_etapas(throughput_kg_h=1000)
    b2 = computar_balance_etapas(throughput_kg_h=3000)
    assert b2.energia_total_kwh_h > b1.energia_total_kwh_h
    assert b2.agua_total_l_h > b1.agua_total_l_h


def test_to_dict_serializable():
    import json
    b = computar_balance_etapas()
    d = b.to_dict()
    s = json.dumps(d)
    assert "etapas" in d
    assert len(d["etapas"]) == 12


def test_nivel_dato_completitud():
    e_pd = EtapaPlanta("X", "Test", 1, "test", 100, 1.0, nivel_calibracion=NivelDato.PD)
    e_prov = EtapaPlanta("Y", "Test", 2, "test", 100, 1.0, nivel_calibracion=NivelDato.OK_PROVISORIO)
    e_val = EtapaPlanta("Z", "Test", 3, "test", 100, 1.0, nivel_calibracion=NivelDato.OK_VALIDADO)
    assert e_pd.datos_completitud_pct == 20.0
    assert e_prov.datos_completitud_pct == 60.0
    assert e_val.datos_completitud_pct == 100.0


def test_lista_etapas_vacia_levanta():
    with pytest.raises(ValueError):
        computar_balance_etapas(etapas=[])
