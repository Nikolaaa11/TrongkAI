"""Tests del simulador what-if."""

from __future__ import annotations

import pytest

from trongkai_engine.plan_builder import ParametrosPlan
from trongkai_engine.whatif import Escenario, comparar_escenarios, create_snapshot


def test_comparar_dos_escenarios():
    escenarios = [
        Escenario(nombre="WACC 15%", overrides={"wacc_anual": 0.15}),
        Escenario(nombre="WACC 8%", overrides={"wacc_anual": 0.08}),
    ]
    cmp = comparar_escenarios(escenarios)
    d = cmp.to_dict()
    assert len(d["escenarios"]) == 2
    # Con WACC menor, VAN debe ser mayor (descuento menor)
    van_15 = d["escenarios"][0]["resumen"]["kpis"]["van"]
    van_8 = d["escenarios"][1]["resumen"]["kpis"]["van"]
    assert van_8 > van_15


def test_override_dict_path():
    """Probar override con path.dot sobre dict (CapEx por año)."""
    escenarios = [
        Escenario(
            nombre="CapEx año 1 al doble",
            overrides={"capex_anual_clp.1": 1_600_000_000},
        ),
    ]
    cmp = comparar_escenarios(escenarios)
    # El plan del escenario debe tener un capex distinto en el primer año
    base_capex = cmp.base.capex_anuales[0]
    esc_capex = cmp.escenarios[0][1].capex_anuales[0]
    assert esc_capex != base_capex
    assert esc_capex == 1_600_000_000


def test_snapshot_genera_hash_estable():
    cmp = comparar_escenarios([Escenario(nombre="X", overrides={"wacc_anual": 0.1})])
    s1 = create_snapshot("escenario X", cmp)
    s2 = create_snapshot("escenario X", cmp)
    assert s1.hash == s2.hash  # mismo contenido → mismo hash
    assert len(s1.hash) == 12


def test_deltas_se_calculan():
    cmp = comparar_escenarios([Escenario(nombre="opex doble", overrides={"opex_mensual_clp": 70_000_000})])
    deltas = cmp.to_dict()["escenarios"][0]["deltas"]
    # OpEx doble → TIR debería caer (delta_tir_pp < 0)
    assert deltas["tir_pp"] is not None
    assert deltas["tir_pp"] < 0


def test_escenario_sin_overrides_replica_base():
    cmp = comparar_escenarios([Escenario(nombre="igual", overrides={})])
    base_van = cmp.to_dict()["base"]["kpis"]["van"]
    esc_van = cmp.to_dict()["escenarios"][0]["resumen"]["kpis"]["van"]
    assert base_van == esc_van


def test_override_path_invalido_lanza_value_error():
    """Cobertura: dot-path sobre campo no-dict debe levantar ValueError (línea 109)."""
    # wacc_anual es float, no dict → no se puede aplicar override anidado
    escenarios = [Escenario(nombre="bad", overrides={"wacc_anual.foo": 0.1})]
    with pytest.raises(ValueError, match="override no aplicable"):
        comparar_escenarios(escenarios)


def test_override_dict_path_no_numerico_se_mantiene_como_string():
    """Cobertura: tail no-numérico en dict de int-keys cae al except y se usa
    tal cual (líneas 114-117). El override NO matchea ningún año pero igual
    debe completar sin error."""
    escenarios = [
        Escenario(
            nombre="key string",
            overrides={"capex_anual_clp.no_es_int": 12345},
        ),
    ]
    # No debe lanzar excepción
    cmp = comparar_escenarios(escenarios)
    assert len(cmp.escenarios) == 1
    # Como la key 'no_es_int' no matchea con ningún año entero (1..5),
    # capex anual base se mantiene
    base_capex = cmp.base.capex_anuales
    esc_capex = cmp.escenarios[0][1].capex_anuales
    assert esc_capex == base_capex


def test_override_dict_path_string_keys_no_castea():
    """Cobertura línea 117: dict de str-keys → tail_key se mantiene como string."""
    # precios_clp_kg arranca vacío pero acepta keys string
    base = ParametrosPlan(precios_clp_kg={"LICOPENO": 12000.0})
    escenarios = [
        Escenario(
            nombre="precio nuevo SKU",
            overrides={"precios_clp_kg.LICOPENO": 9000.0},
        ),
    ]
    from trongkai_engine.whatif import comparar_escenarios as cmp_fn
    cmp = cmp_fn(escenarios, base_params=base)
    # No debe explotar; el escenario corre
    assert len(cmp.escenarios) == 1


def test_snapshot_hash_es_comparable_entre_runs():
    """Snapshot reproducible: corre 2 veces y verifica hashes idénticos."""
    esc = [Escenario(nombre="repetible", overrides={"wacc_anual": 0.12})]
    cmp1 = comparar_escenarios(esc)
    cmp2 = comparar_escenarios(esc)
    s1 = create_snapshot("snap", cmp1)
    s2 = create_snapshot("snap", cmp2)
    assert s1.hash == s2.hash
