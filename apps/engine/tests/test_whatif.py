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
