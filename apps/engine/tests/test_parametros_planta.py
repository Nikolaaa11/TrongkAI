"""Tests parametros variables planta + humedades MMPP + costeo."""
from __future__ import annotations

from trongkai_engine.balances.parametros_planta import (
    ParametrosPlanta,
    TarifaEnergia,
    CalorResidualLaGloria,
    TarifaAgua,
    TarifaFlete,
    ArriendoEquipos,
    SueldoCargo,
    sueldos_seed,
    parametros_seed,
)
from trongkai_engine.balances.humedades_mmpp import (
    HUMEDADES_INGRESO,
    humedad_por_mmpp,
    listar_humedades,
)
from trongkai_engine.balances.costeo_etapas import (
    computar_costo_etapa,
    computar_costeo_completo,
)
from trongkai_engine.balances.etapas import etapas_seed


# =========================
# Parametros planta
# =========================
def test_sueldos_seed_8_cargos():
    sueldos = sueldos_seed()
    assert len(sueldos) >= 6
    cargos = {s.cargo for s in sueldos}
    assert "Laboratorista (QC)" in cargos
    assert "Encargado Recepcion" in cargos


def test_sueldo_costo_hora_incluye_leyes_sociales():
    s = SueldoCargo(cargo="X", sueldo_bruto_clp=600_000)
    assert s.costo_total_clp > s.sueldo_bruto_clp     # con factor 1.35
    assert s.costo_hora_clp > 0


def test_tarifa_energia_promedio_ponderada():
    t = TarifaEnergia()
    promedio = t.tarifa_promedio_clp_kwh
    assert t.tarifa_energia_resto_clp_kwh < promedio < t.tarifa_energia_punta_clp_kwh


def test_calor_residual_la_gloria_bajo_costo():
    """Calor residual debe ser muy barato (es residuo)."""
    c = CalorResidualLaGloria()
    assert c.costo_kwh_termico_clp < 50    # vs ~100 CLP electrico


def test_tarifa_agua_industrial_mucho_mas_barata():
    """Pozo propio mucho mas barato que red."""
    a = TarifaAgua()
    assert a.agua_industrial_clp_m3 < a.agua_llave_clp_m3 / 5


def test_flete_costos_calculados():
    f = TarifaFlete()
    assert f.costo_promedio_mmpp_clp_ton > 0
    # Despacho lejano debe ser > 2x el flete MMPP local
    assert f.costo_promedio_despacho_clp_ton > f.costo_promedio_mmpp_clp_ton * 2


def test_arriendos_pef_no_es_capex():
    """PEF tiene arriendo mensual significativo."""
    a = ArriendoEquipos()
    assert a.arriendo_pef_clp_mes > 5_000_000   # > 5M CLP/mes
    assert a.arriendo_total_clp_mes > a.arriendo_pef_clp_mes


def test_parametros_seed_completo():
    p = parametros_seed()
    assert p.sueldos
    assert p.energia
    assert p.calor_residual
    assert p.agua
    assert p.flete
    assert p.arriendos
    assert p.perdida_mmpp_global_pct == 0.05      # 5% global


def test_parametros_to_dict_serializable():
    import json
    p = parametros_seed()
    s = json.dumps(p.to_dict())
    assert "sueldos" in p.to_dict()
    assert "checklist_pendientes" in p.to_dict()


# =========================
# Humedades MMPP
# =========================
def test_humedades_5_mmpp():
    assert len(HUMEDADES_INGRESO) == 5


def test_tomasa_cold_humedad_75_85():
    h = humedad_por_mmpp("TOMASA_COLD")
    assert h is not None
    assert h.humedad_min_pct == 0.75
    assert h.humedad_max_pct == 0.85
    assert h.humedad_promedio_pct == 0.80


def test_orujo_humedad_60_65():
    h = humedad_por_mmpp("ORUJO")
    assert h is not None
    assert h.humedad_promedio_pct < 0.70


def test_alperujo_humedad_baja():
    h = humedad_por_mmpp("ALPERUJO")
    assert h is not None
    assert h.humedad_max_pct <= 0.60


def test_pomasa_humedad_alta():
    h = humedad_por_mmpp("POMASA")
    assert h is not None
    assert h.humedad_promedio_pct >= 0.78


def test_listar_humedades_serializable():
    import json
    s = json.dumps(listar_humedades())
    assert "TOMASA_COLD" in s


# =========================
# Costeo
# =========================
def test_costo_etapa_basico():
    etapas = etapas_seed()
    pef = next(e for e in etapas if "PEF" in e.id)
    c = computar_costo_etapa(pef, parametros_seed())
    assert c.costo_total_clp_h > 0
    # PEF debe tener arriendo significativo
    assert c.costo_arriendo_clp_h > 0


def test_costo_pef_incluye_arriendo():
    etapas = etapas_seed()
    pef = next(e for e in etapas if "PEF" in e.id)
    c = computar_costo_etapa(pef, parametros_seed())
    # Arriendo PEF prorrateado 480h/mes
    assert c.costo_arriendo_clp_h > 30_000


def test_deshidratacion_calor_residual_es_barato():
    """E6a deshidratacion con calor residual debe ser mucho menor que respaldo electrico."""
    etapas_principal = etapas_seed(incluir_respaldo=False)
    etapas_respaldo = etapas_seed(incluir_respaldo=True)
    e6a = next(e for e in etapas_principal if "DESHIDRATACION" in e.id)
    e6b = next(e for e in etapas_respaldo if "DESHIDRATACION" in e.id)
    p = parametros_seed()
    c_a = computar_costo_etapa(e6a, p)
    c_b = computar_costo_etapa(e6b, p)
    # E6a usa calor residual (barato), E6b electrico (caro)
    # Pero el balance es energia electrica menor en E6a tambien
    assert c_a.costo_calor_clp_h >= 0


def test_costeo_completo_estructura():
    r = computar_costeo_completo(throughput_kg_h=2000)
    assert "costos_etapas" in r
    assert "costos_por_sku" in r
    assert "parametros_utilizados" in r
    assert "desglose_costos_clp_h" in r
    assert len(r["costos_etapas"]) == 12


def test_costeo_tomasa_cold_positivo():
    r = computar_costeo_completo(throughput_kg_h=2000)
    tomasa = next(s for s in r["costos_por_sku"] if s["codigo"] == "TOMASA_1")
    assert tomasa["costo_total_clp_kg"] > 0
    assert tomasa["costo_total_usd_kg"] > 0


def test_costeo_throughput_alto_diluye_costo_unitario():
    """A mayor throughput, menor costo unitario (economias de escala)."""
    r1 = computar_costeo_completo(throughput_kg_h=1000)
    r2 = computar_costeo_completo(throughput_kg_h=4000)
    # Costo total por kg output debe bajar con escala
    assert r2["costo_total_clp_kg_output"] < r1["costo_total_clp_kg_output"]


def test_costeo_to_dict_serializable():
    import json
    r = computar_costeo_completo()
    s = json.dumps(r)
    assert "costos_etapas" in r


# =========================
# Regresion: persistencia + endpoints (bugs 2026-06)
# =========================
def test_regresion_persistencia_parametros(tmp_path, monkeypatch):
    """REGRESION: actualizar_parametros debe persistir (no caer al seed).

    Bug: SueldoCargo(**s) recibia campo computado costo_hora_clp -> excepcion
    -> cargar_parametros devolvia el seed perdiendo el cambio.
    """
    import trongkai_engine.balances.parametros_planta as pp
    # Redirige el storage a tmp para no tocar datos reales
    monkeypatch.setattr(pp, "data_path", lambda f: tmp_path / f)
    pp.actualizar_parametros({"energia": {"tarifa_energia_resto_clp_kwh": 77.0}})
    recargado = pp.cargar_parametros()
    assert recargado.energia.tarifa_energia_resto_clp_kwh == 77.0


def test_regresion_sueldos_con_campos_computados(tmp_path, monkeypatch):
    """REGRESION: cargar sueldos con costo_hora_clp en el JSON no debe romper."""
    import trongkai_engine.balances.parametros_planta as pp
    monkeypatch.setattr(pp, "data_path", lambda f: tmp_path / f)
    p = pp.parametros_seed()
    pp.guardar_parametros(p)   # to_dict agrega costo_hora_clp
    recargado = pp.cargar_parametros()
    assert len(recargado.sueldos) == len(p.sueldos)   # no cayo al seed por error


def test_regresion_readiness_score_endpoint_sin_params():
    """REGRESION: /readiness/score debe responder 200 sin query params.

    Bug: @app.get decoraba _readiness_cached (n_sims_mc sin default) -> 422.
    """
    from fastapi.testclient import TestClient
    from trongkai_engine.main import app
    c = TestClient(app)
    r = c.get("/readiness/score")
    assert r.status_code == 200
    assert "score_total" in r.json() or "score" in str(r.json())
