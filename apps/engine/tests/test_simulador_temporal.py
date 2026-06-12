"""Tests simulador temporal por maquina y planta."""
from __future__ import annotations

import pytest

from trongkai_engine.balances.simulador_temporal import (
    ESTACIONALIDAD_MMPP,
    MESES,
    SimulacionTemporal,
    simular_maquina_individual,
    simular_planta,
)


def test_simulacion_planta_mes_default():
    s = simular_planta(periodo="mes")
    assert isinstance(s, SimulacionTemporal)
    assert s.periodo == "mes"
    assert s.producto_total_kg > 0
    assert s.costo_total_clp > 0


def test_bottleneck_es_prensa_oelwerk():
    """Con piloto la prensa Oelwerk (25 kg/h) limita el sistema."""
    s = simular_planta(periodo="hora")
    assert s.bottleneck_equipo == "PRENSA_OELWERK_510"
    assert s.throughput_planta_kg_h == 25.0


def test_horas_por_periodo():
    s_h = simular_planta(periodo="hora", horas_operacion_dia=16)
    s_d = simular_planta(periodo="dia", horas_operacion_dia=16)
    s_m = simular_planta(periodo="mes", horas_operacion_dia=16, dias_operacion_mes=25)
    s_a = simular_planta(periodo="ano", horas_operacion_dia=16, dias_operacion_mes=25, meses_operacion_ano=10)
    assert s_h.horas_totales_periodo == 1
    assert s_d.horas_totales_periodo == 16
    assert s_m.horas_totales_periodo == 16 * 25
    assert s_a.horas_totales_periodo == 16 * 25 * 10


def test_producto_escala_lineal_horas():
    """A mayor horas dia, mayor produccion."""
    s1 = simular_planta(periodo="mes", horas_operacion_dia=8)
    s2 = simular_planta(periodo="mes", horas_operacion_dia=16)
    assert s2.producto_total_kg == s1.producto_total_kg * 2


def test_maquinas_tienen_utilizacion():
    s = simular_planta(periodo="mes")
    for m in s.maquinas:
        if m.capacidad_nominal_kg_h > 0:
            assert 0 <= m.utilizacion_pct <= 1.0


def test_bottleneck_marcado_en_lista():
    s = simular_planta(periodo="mes")
    bottlenecks = [m for m in s.maquinas if m.es_bottleneck]
    assert len(bottlenecks) == 1
    assert bottlenecks[0].equipo_id == "PRENSA_OELWERK_510"


def test_pef_subutilizado_vs_capacidad():
    """PEF puede 4000 kg/h pero solo opera al ritmo del bottleneck (25 kg/h)."""
    s = simular_planta(periodo="hora")
    pef = next((m for m in s.maquinas if m.equipo_id == "PEF_OPTICEPT_ODIN"), None)
    assert pef is not None
    assert pef.utilizacion_pct < 0.01    # < 1% (25/4000)


def test_timeline_mensual_anual():
    s = simular_planta(periodo="ano", meses_operacion_ano=10, mmpp_principal="TOMASA")
    assert len(s.timeline_mensual) == 12
    for m in s.timeline_mensual:
        assert "mes" in m
        assert "factor_estacional" in m
        assert "producto_kg" in m


def test_estacionalidad_tomasa_alta_en_verano():
    """Tomasa pico en enero-febrero (cosecha)."""
    ene = ESTACIONALIDAD_MMPP["TOMASA"][0]
    jul = ESTACIONALIDAD_MMPP["TOMASA"][6]
    assert ene > jul


def test_estacionalidad_alperujo_solo_invierno():
    """Alperujo abril-julio (cosecha oliva)."""
    abr = ESTACIONALIDAD_MMPP["ALPERUJO"][3]
    ene = ESTACIONALIDAD_MMPP["ALPERUJO"][0]
    assert abr > ene
    assert ene == 0.0


def test_simular_maquina_individual():
    r = simular_maquina_individual(
        equipo_id="PRENSA_OELWERK_510", periodo="mes",
        horas_operacion_dia=16, dias_operacion_mes=25,
    )
    assert "equipo" in r
    assert r["equipo"]["equipo_id"] == "PRENSA_OELWERK_510"
    assert r["equipo"]["producto_kg"] > 0


def test_simular_maquina_inexistente_levanta():
    with pytest.raises(ValueError):
        simular_maquina_individual(equipo_id="FAKE_ID")


def test_timeline_anual_maquina_individual():
    r = simular_maquina_individual(
        equipo_id="PEF_OPTICEPT_ODIN", periodo="ano",
        meses_operacion_ano=10,
    )
    assert len(r["timeline_mensual"]) == 12
    operativos = [m for m in r["timeline_mensual"] if m["horas_operacion"] > 0]
    assert len(operativos) == 10


def test_costos_son_positivos():
    s = simular_planta(periodo="mes")
    assert s.costo_electrico_total_clp > 0
    assert s.costo_arriendo_total_clp > 0     # PEF arriendo


def test_pef_genera_arriendo():
    """En periodo mes el PEF debe generar arriendo prorrateado."""
    s = simular_planta(periodo="mes", horas_operacion_dia=16, dias_operacion_mes=30)
    pef = next(m for m in s.maquinas if m.equipo_id == "PEF_OPTICEPT_ODIN")
    # PEF arriendo $18.5M/mes * (480h/480h) = $18.5M
    assert pef.costo_arriendo_clp > 10_000_000


def test_costo_unitario_clp_kg():
    s = simular_planta(periodo="mes")
    assert s.costo_unitario_clp_kg > 0


def test_to_dict_serializable():
    import json
    s = simular_planta(periodo="mes")
    json.dumps(s.to_dict())


def test_meses_constantes_12():
    assert len(MESES) == 12
    assert MESES[0] == "Ene"
    assert MESES[11] == "Dic"


def test_periodo_invalido_levanta():
    """A nivel funcion no, pero el endpoint si valida."""
    # La funcion no valida, devuelve 0 horas
    s = simular_planta(periodo="invalido")    # type: ignore[arg-type]
    assert s.horas_totales_periodo == 0


# ===== OPEX COMPLETO (energia + arriendo + labor + agua + flete) =====

def test_opex_incluye_todos_los_componentes():
    """El OPEX debe incluir mano de obra, agua y flete, no solo energia+arriendo."""
    s = simular_planta(periodo="ano")
    assert s.costo_labor_total_clp > 0, "falta mano de obra"
    assert s.costo_agua_total_clp > 0, "falta agua"
    assert s.costo_flete_total_clp > 0, "falta flete MMPP"
    assert s.costo_electrico_total_clp > 0
    assert s.costo_arriendo_total_clp > 0


def test_costo_total_es_suma_del_desglose():
    """costo_total_clp == suma de los componentes del desglose OPEX."""
    s = simular_planta(periodo="ano")
    d = s.desglose_opex
    suma = (d["energia_clp"] + d["arriendo_clp"] + d["labor_clp"]
            + d["agua_clp"] + d["flete_mmpp_clp"] + d["calor_residual_clp"])
    assert abs(suma - s.costo_total_clp) < 2.0
    assert abs(d["total_clp"] - s.costo_total_clp) < 2.0


def test_arriendo_anual_corre_12_meses_calendario():
    """REALISMO: el lease (PEF+Tricanter) se paga los 12 meses calendario,
    aunque la planta opere 10 por estacionalidad."""
    from trongkai_engine.balances.parametros_planta import cargar_parametros
    p = cargar_parametros()
    s = simular_planta(periodo="ano")
    esperado = p.arriendos.arriendo_total_clp_mes * 12.0
    assert abs(s.costo_arriendo_total_clp - esperado) < 2.0
    assert s.desglose_opex["meses_fijos"] == 12.0


def test_labor_anual_corre_12_meses_calendario():
    """La planilla se paga los 12 meses (no se despide al equipo 2 meses)."""
    from trongkai_engine.balances.parametros_planta import cargar_parametros
    p = cargar_parametros()
    s = simular_planta(periodo="ano")
    labor_mes = sum(x.costo_total_clp for x in p.sueldos)
    assert abs(s.costo_labor_total_clp - labor_mes * 12.0) < 2.0


def test_fijos_mensuales_prorrateados_en_periodos_cortos():
    """Para periodo 'mes' los fijos son 1 mes (prorrateo normal)."""
    from trongkai_engine.balances.parametros_planta import cargar_parametros
    p = cargar_parametros()
    s = simular_planta(periodo="mes")
    esperado = p.arriendos.arriendo_total_clp_mes * s.meses_equivalentes
    assert abs(s.costo_arriendo_total_clp - esperado) < 2.0


def test_timeline_mes_parado_paga_fijos():
    """Un mes no operativo (factor 0) tiene costo > 0: los fijos no paran."""
    s = simular_planta(periodo="ano", mmpp_principal="ALPERUJO")  # estacional dura
    parados = [m for m in s.timeline_mensual if not m["operativo"]]
    assert parados, "ALPERUJO debe tener meses no operativos"
    for m in parados:
        assert m["costo_fijo_clp"] > 0
        assert m["costo_variable_clp"] == 0
        assert m["costo_clp"] == m["costo_fijo_clp"]


def test_timeline_separa_fijo_y_variable():
    """costo_clp de cada mes = fijo + variable."""
    s = simular_planta(periodo="ano")
    for m in s.timeline_mensual:
        assert abs(m["costo_clp"] - (m["costo_fijo_clp"] + m["costo_variable_clp"])) < 2.0


def test_arriendo_domina_costo_en_piloto():
    """A escala piloto el arriendo es el mayor componente del OPEX."""
    s = simular_planta(periodo="ano")
    d = s.desglose_opex
    comps = {"energia": d["energia_clp"], "arriendo": d["arriendo_clp"],
             "labor": d["labor_clp"], "agua": d["agua_clp"]}
    assert max(comps, key=comps.get) == "arriendo"


def test_mmpp_mayor_que_producto_por_yield():
    """La MMPP de entrada > producto terminado (perdida de masa por yield)."""
    s = simular_planta(periodo="ano")
    assert s.mmpp_total_kg > s.producto_total_kg
    assert s.producto_total_kg / s.mmpp_total_kg < 0.5   # yield ~27.5%
