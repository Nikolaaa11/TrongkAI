"""Tests del motor de cuello de botella — Módulo 1.

Entregable M1: contestar "¿cuántos camiones de tomasa puedo recibir si secador es bottleneck?"
"""

from __future__ import annotations

import pytest

from trongkai_engine.bottleneck import (
    CapacidadEtapa,
    EtapaProceso,
    compute_bottleneck,
)


@pytest.fixture
def caps_tomasa_baseline() -> list[CapacidadEtapa]:
    return [
        CapacidadEtapa(EtapaProceso.RECEPCION, ton_por_hora=10, tiempo_residencia_h=0.2),
        CapacidadEtapa(EtapaProceso.ALIMENTACION, ton_por_hora=8, tiempo_residencia_h=0.1),
        CapacidadEtapa(EtapaProceso.HOMOG_1, ton_por_hora=8, tiempo_residencia_h=0.1),
        CapacidadEtapa(EtapaProceso.PEF, ton_por_hora=6, tiempo_residencia_h=0.1),
        CapacidadEtapa(EtapaProceso.PRENSADO_MECANICO, ton_por_hora=5, tiempo_residencia_h=0.2),
        CapacidadEtapa(EtapaProceso.SECADO, ton_por_hora=2.5, tiempo_residencia_h=1.5),
        CapacidadEtapa(EtapaProceso.ENSACADO, ton_por_hora=5, tiempo_residencia_h=0.1),
    ]


def test_bottleneck_es_el_secador(caps_tomasa_baseline):
    r = compute_bottleneck(caps_tomasa_baseline, tiempo_descomposicion_h=3.0)
    assert r.etapa_bottleneck == EtapaProceso.SECADO
    assert r.flujo_max_ton_h == 2.5


def test_camiones_max_dia_calculo(caps_tomasa_baseline):
    r = compute_bottleneck(caps_tomasa_baseline, tiempo_descomposicion_h=3.0, capacidad_camion_ton=20.0)
    # 2.5 ton/h × 24 h = 60 ton/día → 60/20 = 3 camiones
    assert r.camiones_max_dia == 3
    assert r.puede_recibir is True


def test_alerta_roja_si_proceso_supera_descomposicion(caps_tomasa_baseline):
    """Tomasa que se fermenta en 1.5 h pero el proceso toma 2.3 h → ROJA."""
    r = compute_bottleneck(caps_tomasa_baseline, tiempo_descomposicion_h=1.5)
    assert r.puede_recibir is False
    assert r.camiones_max_dia == 0
    assert r.alerta == "ROJA"


def test_capacidad_pd_genera_incertidumbre(caps_tomasa_baseline):
    """Si el secador está PD, alerta amarilla pero sigue calculando con el resto."""
    caps = [c for c in caps_tomasa_baseline if c.etapa != EtapaProceso.SECADO]
    caps.append(CapacidadEtapa(EtapaProceso.SECADO, ton_por_hora=None, tiempo_residencia_h=1.5))
    r = compute_bottleneck(caps, tiempo_descomposicion_h=3.0)
    assert r.incertidumbres != []
    assert r.alerta == "AMARILLA"


def test_todas_pd_no_se_recibe():
    """Sin ninguna capacidad cargada, no se planifica."""
    caps = [CapacidadEtapa(EtapaProceso.SECADO, ton_por_hora=None, tiempo_residencia_h=1.5)]
    r = compute_bottleneck(caps, tiempo_descomposicion_h=3.0)
    assert r.puede_recibir is False
    assert r.alerta == "ROJA"


def test_tiempo_descomposicion_negativo_falla(caps_tomasa_baseline):
    with pytest.raises(ValueError):
        compute_bottleneck(caps_tomasa_baseline, tiempo_descomposicion_h=-1)


def test_capacidad_camion_negativa_falla(caps_tomasa_baseline):
    with pytest.raises(ValueError):
        compute_bottleneck(
            caps_tomasa_baseline,
            tiempo_descomposicion_h=3.0,
            capacidad_camion_ton=0,
        )


def test_sin_etapas_aplicables_falla():
    """Si todas las etapas tienen aplica=False, no se puede calcular bottleneck."""
    caps = [
        CapacidadEtapa(
            EtapaProceso.SECADO, ton_por_hora=2.5, tiempo_residencia_h=1.5, aplica=False
        ),
    ]
    with pytest.raises(ValueError):
        compute_bottleneck(caps, tiempo_descomposicion_h=3.0)


def test_alerta_amarilla_por_pd_aun_con_ventana_amplia(caps_tomasa_baseline):
    """Con ventana amplia pero alguna capacidad PD, sigue siendo AMARILLA."""
    caps = [c for c in caps_tomasa_baseline if c.etapa != EtapaProceso.ENSACADO]
    caps.append(CapacidadEtapa(EtapaProceso.ENSACADO, ton_por_hora=None, tiempo_residencia_h=0.1))
    r = compute_bottleneck(caps, tiempo_descomposicion_h=24.0)
    assert r.puede_recibir is True
    assert r.ventana_segura_h >= 1
    assert r.incertidumbres != []
    assert r.alerta == "AMARILLA"


def test_alerta_verde_cuando_ventana_amplia_y_sin_pd(caps_tomasa_baseline):
    """Con ventana >= 1h y sin capacidades PD, la alerta es VERDE."""
    # tiempo_total ≈ 2.3 h, descomposicion = 24 h → ventana ≈ 21.7 h
    r = compute_bottleneck(caps_tomasa_baseline, tiempo_descomposicion_h=24.0)
    assert r.puede_recibir is True
    assert r.incertidumbres == []
    assert r.ventana_segura_h >= 1
    assert r.alerta == "VERDE"
