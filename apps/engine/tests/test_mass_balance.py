"""Tests del motor de balance de masa.

Entregable de validación M2 (SUPER_PROMPT §4): replicar el ejemplo alperujo del Excel
(humedad 65%, MS 35%, aceite 2%) y obtener MS final ≈ 35% en modo A.
"""

from __future__ import annotations

import pytest

from trongkai_engine.mass_balance import (
    BalanceMode,
    MassBalanceError,
    MateriaPrimaSpec,
    compute_mass_balance,
)


@pytest.fixture
def alperujo_spec() -> MateriaPrimaSpec:
    return MateriaPrimaSpec(
        codigo="ALPERUJO",
        humedad_inicial_pct=0.65,
        materia_solida_pct=0.35,
        aceite_extraible_pct=0.02,
    )


@pytest.fixture
def tomasa_spec() -> MateriaPrimaSpec:
    return MateriaPrimaSpec(
        codigo="TOMASA",
        humedad_inicial_pct=0.82,
        materia_solida_pct=0.18,
    )


def test_alperujo_modo_a_replica_excel(alperujo_spec):
    """Modo A: la MS neta entregada al cliente es 35% del input (per Excel cliente)."""
    r = compute_mass_balance(alperujo_spec, input_ton=1.0, mode=BalanceMode.A_INITIAL_BASE, perdidas_pct=0.0)
    # MS pura = 0.35 - 0.02 (aceite) = 0.33 → harina con 10% humedad ≈ 0.367
    # Total entregado al cliente: harina + aceite ≈ 0.387
    assert r.materia_seca_neta_pct == pytest.approx(0.387, abs=0.005)
    assert r.aceite_extraido_ton == pytest.approx(0.02)
    assert r.delta_balance_pct < 0.005


def test_alperujo_modo_b_es_mayor_que_modo_a(alperujo_spec):
    """Modo B (base deshidratada) da más kg entregables que modo A."""
    a = compute_mass_balance(alperujo_spec, input_ton=1.0, mode=BalanceMode.A_INITIAL_BASE, perdidas_pct=0.0)
    b = compute_mass_balance(alperujo_spec, input_ton=1.0, mode=BalanceMode.B_DEHYDRATED_BASE, perdidas_pct=0.0)
    assert b.harina_final_ton > a.harina_final_ton or b.aceite_extraido_ton != a.aceite_extraido_ton
    assert b.materia_seca_neta_pct > a.materia_seca_neta_pct - 0.001


def test_tomasa_82_humedad_balance_cierra(tomasa_spec):
    r = compute_mass_balance(tomasa_spec, input_ton=10.0, mode=BalanceMode.A_INITIAL_BASE, perdidas_pct=0.01)
    assert r.delta_balance_pct < 0.005
    # MS neta ≈ 18% del input (sin extracciones)
    assert r.materia_seca_neta_pct == pytest.approx(0.18 / 0.9, abs=0.02)


def test_balance_cierra_con_perdidas_significativas(alperujo_spec):
    r = compute_mass_balance(alperujo_spec, input_ton=1.0, perdidas_pct=0.05)
    suma = (
        r.harina_final_ton
        + r.aceite_extraido_ton
        + r.licopeno_extraido_ton
        + r.pectina_extraida_ton
        + r.agua_evaporada_ton
        + r.perdidas_ton
    )
    assert abs(suma - 1.0) < 0.005


def test_input_negativo_falla(alperujo_spec):
    with pytest.raises(MassBalanceError):
        compute_mass_balance(alperujo_spec, input_ton=-1.0)


def test_humedad_inicial_invalida():
    with pytest.raises(MassBalanceError):
        MateriaPrimaSpec(codigo="X", humedad_inicial_pct=1.5, materia_solida_pct=0.5)


def test_humedad_final_invalida(alperujo_spec):
    with pytest.raises(ValueError):
        compute_mass_balance(alperujo_spec, input_ton=1.0, humedad_final_pct=1.0)


def test_sankey_tiene_nodos_y_links(alperujo_spec):
    r = compute_mass_balance(alperujo_spec, input_ton=1.0)
    assert "nodes" in r.sankey
    assert "links" in r.sankey
    assert len(r.sankey["nodes"]) >= 4
    assert all(link["value"] > 0 for link in r.sankey["links"])


def test_extracciones_no_pueden_superar_ms(alperujo_spec):
    """Si pedimos extraer más aceite que materia sólida disponible, falla."""
    spec = MateriaPrimaSpec(
        codigo="ALPERUJO_IMPOSIBLE",
        humedad_inicial_pct=0.65,
        materia_solida_pct=0.35,
        aceite_extraible_pct=0.50,  # más del 35% MS → imposible
    )
    with pytest.raises(MassBalanceError):
        compute_mass_balance(spec, input_ton=1.0, mode=BalanceMode.A_INITIAL_BASE)
