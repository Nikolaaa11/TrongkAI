"""Tests del modulo costos_procesos (replica canonica Excel equipo 03-jul-2026).

Los valores canon vienen de "costos por procesos (3).xlsx" y estan documentados
en contexto/SUPER_PROMPT_COSTOS_PROCESOS_V3.md. Verificados al centavo.
"""
import pytest

from trongkai_engine.balances.costos_procesos import calcular, ParametrosProcesosV3

CANON_ETAPAS = {
    "E1": 60_177.33, "E2": 96_005.25, "E3": 277_158.92,
    "E4.1": 149_982.33, "E4.2": 139_614.33,
    "E5.1": 391_902.33, "E5.2": 89_502.33,
    "E6": 89_502.33, "E7": 312_414.33,
    "E8.1": 3_408_612.57, "E8.2": 446_696.78, "E9": 152_857.81,
}


@pytest.fixture(scope="module")
def resultado():
    return calcular()


def test_12_etapas(resultado):
    assert len(resultado["etapas"]) == 12


def test_totales_por_etapa_calzan_con_excel(resultado):
    for e in resultado["etapas"]:
        assert e["total_dia_clp"] == pytest.approx(CANON_ETAPAS[e["id"]], abs=0.01), e["id"]


def test_ruta_saco_canon(resultado):
    r = resultado["rutas"]["saco_base"]
    assert r["total_dia_clp"] == pytest.approx(4_938_613.20, abs=0.01)
    assert r["clp_ton_mp_seca"] == pytest.approx(194_722.64, abs=0.01)


def test_ruta_maxisaco_canon(resultado):
    r = resultado["rutas"]["maxisaco_base"]
    assert r["total_dia_clp"] == pytest.approx(1_976_697.40, abs=0.05)
    assert r["clp_ton_mp_seca"] == pytest.approx(77_938.42, abs=0.01)


def test_mp_seca_final(resultado):
    # 26,4 ton x 0,995^8 = 25,3623
    assert resultado["mp_seca_final_ton_dia"] == pytest.approx(25.3623, abs=0.001)


def test_maxisaco_ahorra_2_5x(resultado):
    assert resultado["decision_packaging"]["factor"] == pytest.approx(2.5, abs=0.1)
    assert resultado["decision_packaging"]["ahorro_maxisaco_clp_dia"] > 2_900_000


def test_calor_residual_mas_barato_que_bomba_calor(resultado):
    assert (resultado["rutas"]["saco_calor_residual"]["total_dia_clp"]
            < resultado["rutas"]["saco_base"]["total_dia_clp"])


def test_repuestos_pef_amortizados():
    p = ParametrosProcesosV3()
    assert p.electrodos_clp_ton == pytest.approx(702.04, abs=0.01)
    assert p.camara_clp_ton == pytest.approx(1_249.50, abs=0.01)


def test_whatif_tarifa_energia_escala():
    base = calcular()["rutas"]["saco_base"]["total_dia_clp"]
    barato = calcular(tarifa_clp_kwh=135)["rutas"]["saco_base"]["total_dia_clp"]
    assert barato < base
    # kW ruta saco: E2 13,2 + E3 14 + E4.1 24 + E5.1 80 + E6 10 + E7 61,6 + E8.1 4,48 + E9 5 = 212,28
    assert base - barato == pytest.approx(212.28 * 16 * 135, rel=0.01)


def test_whatif_saco_mas_barato_reduce_brecha():
    base = calcular()["decision_packaging"]["ahorro_maxisaco_clp_dia"]
    con_saco_1000 = calcular(saco_25kg_clp=1_000)["decision_packaging"]["ahorro_maxisaco_clp_dia"]
    assert con_saco_1000 < base


def test_parametros_canon():
    p = calcular()["parametros"]
    assert p["tarifa_clp_kwh"] == 270.0
    assert p["agua_clp_m3"] == 800.0
    assert p["ton_proceso_dia"] == 82.5
    assert p["ton_mp_seca_ingreso"] == pytest.approx(26.4)


def test_por_validar_documentado(resultado):
    assert len(resultado["por_validar"]) >= 4
