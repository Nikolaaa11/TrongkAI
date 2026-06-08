"""Tests analisis PEF + fichas equipos."""
from __future__ import annotations

from trongkai_engine.balances.pef_analisis import (
    AnalisisPEF,
    analizar_pef_vs_sin_pef,
    computar_escenario,
    sensibilidad_pef,
)
from trongkai_engine.balances.fichas_equipos import (
    FichaEquipo,
    cargar_fichas,
    fichas_seed,
    resumen_completitud_fichas,
)
from trongkai_engine.balances.parametros_planta import parametros_seed


def test_analisis_basico():
    a = analizar_pef_vs_sin_pef()
    assert isinstance(a, AnalisisPEF)
    assert a.con_pef.usa_pef is True
    assert a.sin_pef.usa_pef is False


def test_con_pef_tiene_arriendo():
    a = analizar_pef_vs_sin_pef()
    assert a.con_pef.costo_arriendo_pef_clp_h > 0


def test_sin_pef_no_tiene_arriendo():
    a = analizar_pef_vs_sin_pef()
    assert a.sin_pef.costo_arriendo_pef_clp_h == 0


def test_default_1_pasada():
    """Por defecto 1 pasada segun respuesta usuario 4/06/26."""
    a = analizar_pef_vs_sin_pef()
    assert a.con_pef.pasadas_pef == 1


def test_breakeven_es_fraccion():
    a = analizar_pef_vs_sin_pef()
    assert 0 < a.breakeven_pct_reduccion_tiempo


def test_recomendacion_tiene_texto():
    a = analizar_pef_vs_sin_pef()
    assert len(a.recomendacion) > 10


def test_drivers_clave_minimo_5():
    a = analizar_pef_vs_sin_pef()
    assert len(a.drivers_clave) >= 5


def test_supuestos_incluyen_revenue():
    """Nuevo: supuestos incluyen revenue + margen."""
    a = analizar_pef_vs_sin_pef()
    for k in ["precio_venta_clp_kg", "margen_con_clp_h", "margen_sin_clp_h", "diff_margen_clp_h"]:
        assert k in a.supuestos


def test_supuestos_completos():
    a = analizar_pef_vs_sin_pef()
    for k in ["tiempo_secado_base_min", "yield_base_sin_pef",
              "vida_electrodos_h", "arriendo_pef_clp_mes"]:
        assert k in a.supuestos


def test_mayor_reduccion_secado_favorece_pef():
    """Mas % reduccion tiempo secado -> menor diferencia PEF (mas favorable)."""
    a1 = analizar_pef_vs_sin_pef(pct_reduccion_tiempo_secado=0.0)
    a2 = analizar_pef_vs_sin_pef(pct_reduccion_tiempo_secado=0.50)
    # Con 50% reduccion, PEF se ve mejor (menor diff_clp_h)
    assert a2.diferencia_clp_h <= a1.diferencia_clp_h


def test_uplift_yield_mejora_pef():
    a1 = analizar_pef_vs_sin_pef(pct_uplift_yield=0.0)
    a2 = analizar_pef_vs_sin_pef(pct_uplift_yield=0.10)
    # Mas yield = mejor costo unitario
    assert a2.con_pef.costo_unitario_clp_kg < a1.con_pef.costo_unitario_clp_kg


def test_sensibilidad_estructura():
    s = sensibilidad_pef()
    assert len(s) > 0
    for r in s:
        for k in ["pct_reduccion_secado", "diferencia_clp_h", "pef_es_mejor"]:
            assert k in r


def test_sensibilidad_monotonica():
    """A mayor reduccion secado, diferencia (con - sin) baja."""
    s = sensibilidad_pef()
    diffs = [r["diferencia_clp_h"] for r in s]
    assert diffs == sorted(diffs, reverse=True)


def test_to_dict_serializable():
    import json
    a = analizar_pef_vs_sin_pef()
    s = json.dumps(a.to_dict())
    assert "con_pef" in a.to_dict()


# =========================
# Fichas equipos
# =========================
def test_fichas_seed_no_vacio():
    fichas = fichas_seed()
    assert len(fichas) > 10


def test_pef_opticept_es_arriendo():
    fichas = fichas_seed()
    pef = next(f for f in fichas if "PEF" in f.id)
    assert pef.modalidad == "OPEX_arriendo"
    assert pef.arriendo_clp_mes > 0


def test_centrifuga_biobase_es_pruebas_lab():
    """Tras update Word: la centrifuga BioBase es escala laboratorio, no arriendo."""
    fichas = fichas_seed()
    cent = next(f for f in fichas if "CENTRIFUGA_BIOBASE" in f.id)
    assert "labor" in cent.notas.lower() or "prueba" in cent.notas.lower()


def test_romana_fuera_costos():
    """Romana es compartida con La Gloria - fuera del analisis."""
    fichas = fichas_seed()
    romana = next(f for f in fichas if "ROMANA" in f.id)
    assert romana.arriendo_clp_mes == 0
    assert "FUERA" in romana.notas.upper() or "compartida" in romana.notas.lower()


def test_resumen_completitud():
    r = resumen_completitud_fichas()
    assert r["total_fichas"] > 0
    for k in ["PD", "OK_PROVISORIO", "OK_VALIDADO"]:
        assert k in r["por_nivel"]
    assert 0 <= r["completitud_pct"] <= 100


def test_fichas_to_dict_serializable():
    import json
    fichas = fichas_seed()
    for f in fichas:
        s = json.dumps(f.to_dict())
        assert "id" in f.to_dict()
