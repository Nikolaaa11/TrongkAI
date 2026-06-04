"""Tests del balance por etapas de la planta - Modelo Agrosphere real."""
from __future__ import annotations

import pytest

from trongkai_engine.balances.etapas import (
    BalancePorEtapas,
    EtapaPlanta,
    NivelDato,
    ProductoEtapas,
    computar_balance_etapas,
    etapas_seed,
    matriz_productos_x_etapas,
    productos_seed,
    resumen_datos_faltantes,
)


def test_seed_11_etapas_principal():
    """11 etapas con E6(a) principal default."""
    assert len(etapas_seed()) == 12   # 11 + E11 toma muestra


def test_seed_con_respaldo_misma_cantidad():
    """Mismo numero de etapas pero E6 cambia a respaldo."""
    es = etapas_seed(incluir_respaldo=True)
    assert len(es) == 12
    assert any(e.id == "E6B_DESHIDRATACION_RESPALDO" for e in es)


def test_orden_etapas_correcto():
    es = etapas_seed()
    ordenes = [e.orden for e in es]
    assert ordenes == sorted(ordenes)


def test_recepcion_es_primera():
    assert etapas_seed()[0].id == "E1_RECEPCION"


def test_toma_muestra_es_ultima():
    assert etapas_seed()[-1].id == "E11_CONTROL_CALIDAD"


def test_balance_basico():
    b = computar_balance_etapas()
    assert isinstance(b, BalancePorEtapas)
    assert b.masa_entrada_total_kg_h > 0
    assert b.energia_total_kwh_h > 0


def test_yield_total_razonable():
    """Yield total considera secado y separaciones — esperado bajo (1-30%)."""
    b = computar_balance_etapas()
    assert 0.0001 < b.yield_total_proceso < 0.50


def test_tiempo_proceso_total_min():
    """Excel dice 120 min normal con E6(a)."""
    b = computar_balance_etapas()
    # Tiempos: 2+2+8+3+3+4+60+3+2+10+3+1 = 101 min (E4(a) + E4(b))
    assert 80 < b.tiempo_proceso_total_min < 130


def test_tiempo_con_respaldo_es_mayor():
    """Con E6(b) respaldo el tiempo aumenta a 150min."""
    b_normal = computar_balance_etapas()
    b_resp = computar_balance_etapas(incluir_respaldo=True)
    assert b_resp.tiempo_proceso_total_min > b_normal.tiempo_proceso_total_min


def test_humedad_post_pef_alta():
    es = etapas_seed()
    pef = next(e for e in es if e.id == "E3_PEF")
    # 75-80% segun Excel
    assert pef.humedad_post_etapa == (0.75, 0.80)


def test_humedad_post_deshidratacion_es_10_15():
    """Conversacion 4/06/26: deshidratacion baja 30% -> 10-15%, luego enfriado a 8-10%."""
    es = etapas_seed()
    deshid = next(e for e in es if "DESHIDRATACION" in e.id)
    assert deshid.humedad_post_etapa == (0.10, 0.15)


def test_humedad_post_enfriado_es_8_10():
    es = etapas_seed()
    enf = next(e for e in es if e.id == "E7_ENFRIADO")
    assert enf.humedad_post_etapa == (0.08, 0.10)


def test_etapa_pef_tiene_repuesto_electrodos():
    es = etapas_seed()
    pef = next(e for e in es if e.id == "E3_PEF")
    assert any("Electrodos" in r for r in pef.repuestos)


def test_etapa_ensacado_tiene_materiales():
    es = etapas_seed()
    ens = next(e for e in es if e.id == "E9_ENSACADO")
    assert "Sacos" in ens.materiales
    assert "Pallets" in ens.materiales


def test_etapa_pef_es_la_mas_intensiva_electrica_real():
    """Con calor residual La Gloria, E6a baja a 0.10 kWh/kg.
    PEF queda como mayor consumidor electrico (0.13 kWh/kg)."""
    es = etapas_seed()
    consumos = {e.id: e.energia_kwh_por_kg for e in es}
    max_id = max(consumos, key=consumos.get)
    assert max_id == "E3_PEF"


def test_alarmas_estructura():
    b = computar_balance_etapas()
    assert isinstance(b.alarmas, list)
    for a in b.alarmas:
        assert "tipo" in a
        assert "severidad" in a


def test_completitud_mejor_con_excel_real():
    """El Excel sube validez. E1 es VALIDADO, varias son PROVISORIO."""
    b = computar_balance_etapas()
    # Con datos del Excel real, completitud debe ser > 50%
    assert b.completitud_datos_pct > 50


def test_intensidades_acumuladas_incluyen_tiempo():
    b = computar_balance_etapas()
    i = b.intensidades_acumuladas
    assert "tiempo_min_por_ton" in i


def test_resumen_datos_faltantes():
    r = resumen_datos_faltantes()
    assert r["total_etapas"] == 12
    assert r["validadas"] + r["provisorias"] + r["sin_validar"] == 12


def test_throughput_alto_aumenta_consumos():
    b1 = computar_balance_etapas(throughput_kg_h=1000)
    b2 = computar_balance_etapas(throughput_kg_h=3000)
    assert b2.energia_total_kwh_h > b1.energia_total_kwh_h


def test_to_dict_serializable():
    import json
    b = computar_balance_etapas()
    d = b.to_dict()
    s = json.dumps(d)
    assert "etapas" in d
    assert "tiempo_proceso_total_min" in d


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


# =========================
# Matriz Productos x Etapas
# =========================
def test_productos_seed_8_items():
    """Excel: 2 Tomasa + 2 Orujo + 2 Alperujo + 2 Pomasa = 8 productos."""
    assert len(productos_seed()) == 8


def test_tomasa_cold_tiene_proceso_completo():
    ps = productos_seed()
    t1 = next(p for p in ps if p.codigo == "TOMASA_1")
    assert t1.variante == "Cold"
    assert t1.rendimiento_msf_pct == 0.30
    # Cold pasa por E4(a) Prensado Mecanico
    assert "E4A_PRENSADO_MECANICO" in t1.etapas_aplicables
    assert "E4B_PRENSADO_CENTRIFUGO" not in t1.etapas_aplicables


def test_tomasa_hot_pasa_por_tricanter():
    ps = productos_seed()
    t2 = next(p for p in ps if p.codigo == "TOMASA_2")
    assert t2.variante == "Hot"
    assert t2.rendimiento_msf_pct == 0.25
    assert "E4B_PRENSADO_CENTRIFUGO" in t2.etapas_aplicables


def test_orujo_y_alperujo_solo_recepcion():
    ps = productos_seed()
    for codigo in ["ORUJO_1", "ORUJO_2", "ALPERUJO_1", "ALPERUJO_2", "POMASA_1", "POMASA_2"]:
        p = next(x for x in ps if x.codigo == codigo)
        assert p.etapas_aplicables == ["E1_RECEPCION"]


def test_matriz_productos_x_etapas():
    m = matriz_productos_x_etapas()
    assert m["total_productos"] == 8
    assert m["productos_con_proceso_definido"] == 2     # solo Tomasa 1 y 2
    assert m["productos_solo_recepcion"] == 6


def test_matriz_yield_acumulado_tomasa():
    m = matriz_productos_x_etapas()
    t1 = next(p for p in m["productos"] if p["codigo"] == "TOMASA_1")
    # yield acumulado debe ser > 0 (productos de proceso completo)
    assert t1["yield_acumulado_teorico"] > 0
    assert t1["cantidad_etapas"] > 5
    assert t1["tiempo_proceso_min"] > 50
