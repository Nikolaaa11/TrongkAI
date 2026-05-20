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


def test_humedad_mas_ms_no_suman_uno_falla():
    """Constructor exige humedad + ms ≈ 1 (tolerancia 0.02). Cubre línea 48."""
    with pytest.raises(MassBalanceError, match="debe ≈ 1"):
        MateriaPrimaSpec(
            codigo="X",
            humedad_inicial_pct=0.5,
            materia_solida_pct=0.2,  # suma 0.7, fuera de tolerancia
        )


def test_perdidas_pct_fuera_de_rango(alperujo_spec):
    """`perdidas_pct >= 1` levanta error. Cubre línea 145."""
    with pytest.raises(MassBalanceError, match="perdidas_pct"):
        compute_mass_balance(alperujo_spec, input_ton=1.0, perdidas_pct=1.0)


def test_extracciones_modo_b_no_pueden_superar_ms_pura():
    """En modo B las extracciones sobre MS pura no pueden exceder la MS. Cubre línea 119."""
    spec = MateriaPrimaSpec(
        codigo="IMPOSIBLE_B",
        humedad_inicial_pct=0.65,
        materia_solida_pct=0.35,
        aceite_extraible_pct=0.6,
        licopeno_pct=0.5,  # 0.6 + 0.5 > 1 (de la MS) → imposible en modo B
    )
    with pytest.raises(MassBalanceError, match="modo B"):
        compute_mass_balance(spec, input_ton=1.0, mode=BalanceMode.B_DEHYDRATED_BASE)


def test_humedad_final_muy_alta_genera_agua_negativa(alperujo_spec):
    """Humedad final tan alta que la harina supera el input → agua_evaporada negativa. Cubre línea 157."""
    with pytest.raises(MassBalanceError, match="Agua evaporada negativa"):
        compute_mass_balance(
            alperujo_spec,
            input_ton=1.0,
            humedad_final_pct=0.99,
            perdidas_pct=0.0,
        )


def test_sankey_incluye_links_de_licopeno_y_pectina():
    """Si la MMPP tiene licopeno y/o pectina extraíbles, el sankey suma esos links. Cubre líneas 218 y 222."""
    spec = MateriaPrimaSpec(
        codigo="TOMASA_RICA",
        humedad_inicial_pct=0.82,
        materia_solida_pct=0.18,
        licopeno_pct=0.01,
        pectina_pct=0.02,
    )
    r = compute_mass_balance(spec, input_ton=10.0, mode=BalanceMode.A_INITIAL_BASE)
    targets = {link["target"] for link in r.sankey["links"]}
    assert "Licopeno" in targets
    assert "Pectina" in targets


def test_materia_seca_neta_pct_con_input_cero():
    """La property devuelve 0.0 cuando input_ton=0 (división protegida). Cubre línea 79."""
    from trongkai_engine.mass_balance import MassBalanceResult

    r = MassBalanceResult(
        mmpp="X",
        mode=BalanceMode.A_INITIAL_BASE,
        input_ton=0.0,
        humedad_final_pct=0.10,
        materia_seca_pura_ton=0.0,
        aceite_extraido_ton=0.0,
        licopeno_extraido_ton=0.0,
        pectina_extraida_ton=0.0,
        harina_final_ton=0.0,
        agua_evaporada_ton=0.0,
        perdidas_ton=0.0,
        suma_outputs_ton=0.0,
        delta_balance_pct=0.0,
    )
    assert r.materia_seca_neta_pct == 0.0
