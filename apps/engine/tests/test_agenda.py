"""Tests del planificador de agenda."""

from __future__ import annotations

import pytest

from trongkai_engine.agenda import (
    AgendaResult,
    SupplierTarget,
    TemporadaMMPP,
    build_agenda,
)
from trongkai_engine.bottleneck import CapacidadEtapa, EtapaProceso


@pytest.fixture
def caps_baseline():
    return [
        CapacidadEtapa(EtapaProceso.RECEPCION, ton_por_hora=10, tiempo_residencia_h=0.2),
        CapacidadEtapa(EtapaProceso.SECADO, ton_por_hora=2.5, tiempo_residencia_h=1.5),
        CapacidadEtapa(EtapaProceso.ENSACADO, ton_por_hora=5, tiempo_residencia_h=0.1),
    ]


def test_agenda_distribuye_olivero_3_en_temporada_alperujo(caps_baseline):
    """Olivero 3 con 2000 ton compromiso, temporada abril-junio (90 días)."""
    temp = TemporadaMMPP(mmpp_codigo="ALPERUJO", mes_inicio=4, mes_fin=6, tiempo_descomposicion_h=8.0)
    suppliers = {
        "ALPERUJO": [
            SupplierTarget(nombre="Olivero 3", mmpp_codigo="ALPERUJO",
                          volumen_anual_ton=2000, capacidad_camion_ton=20),
        ],
    }
    result = build_agenda(2027, caps_baseline, [temp], suppliers)
    assert isinstance(result, AgendaResult)
    assert result.total_ton_planificadas > 1000
    # No genera más slots que días en la temporada
    assert len(result.slots) <= 91
    # Bottleneck identificado
    assert result.bottleneck.etapa_bottleneck == EtapaProceso.SECADO


def test_agenda_sin_proveedores_genera_advertencia(caps_baseline):
    temp = TemporadaMMPP(mmpp_codigo="TOMASA", mes_inicio=1, mes_fin=3, tiempo_descomposicion_h=3.0)
    result = build_agenda(2027, caps_baseline, [temp], {})
    assert "No hay suppliers" in result.advertencias[0]
    assert result.total_camiones == 0


def test_agenda_alerta_roja_no_planifica(caps_baseline):
    """MMPP con tiempo de descomposición = 0.5h imposible con proceso de 1.8h"""
    temp = TemporadaMMPP(mmpp_codigo="TOMASA", mes_inicio=1, mes_fin=3, tiempo_descomposicion_h=0.5)
    suppliers = {
        "TOMASA": [SupplierTarget("Tomatera 1", "TOMASA", 500, 22)],
    }
    result = build_agenda(2027, caps_baseline, [temp], suppliers)
    assert any("ROJA" in w for w in result.advertencias)
    assert result.total_camiones == 0


def test_multiples_suppliers_se_planifican_paralelo(caps_baseline):
    temp = TemporadaMMPP(mmpp_codigo="ALPERUJO", mes_inicio=4, mes_fin=6, tiempo_descomposicion_h=8.0)
    suppliers = {
        "ALPERUJO": [
            SupplierTarget("Olivero 1", "ALPERUJO", 500, 20),
            SupplierTarget("Olivero 3", "ALPERUJO", 2000, 20),
        ],
    }
    result = build_agenda(2027, caps_baseline, [temp], suppliers)
    nombres = {s.supplier_nombre for s in result.slots}
    assert "Olivero 1" in nombres
    assert "Olivero 3" in nombres


def test_temporada_genera_fechas_correctas():
    temp = TemporadaMMPP(mmpp_codigo="ALPERUJO", mes_inicio=4, mes_fin=6, tiempo_descomposicion_h=8)
    fechas = list(temp.fechas(2027))
    assert fechas[0].month == 4 and fechas[0].day == 1
    assert fechas[-1].month == 6 and fechas[-1].day == 30
    assert len(fechas) == 91  # abr 30 + may 31 + jun 30 = 91


def test_temporada_diciembre_termina_31(caps_baseline):
    """Cobertura: rama mes_fin >= 12 en TemporadaMMPP.fechas (línea 56)."""
    temp = TemporadaMMPP(mmpp_codigo="ALPERUJO", mes_inicio=11, mes_fin=12, tiempo_descomposicion_h=8.0)
    fechas = list(temp.fechas(2027))
    # Nov 1 -> Dic 31 = 30 + 31 = 61 días
    assert fechas[0].month == 11 and fechas[0].day == 1
    assert fechas[-1].month == 12 and fechas[-1].day == 31
    assert len(fechas) == 61


def test_agenda_temporada_diciembre_se_ejecuta(caps_baseline):
    """Build agenda con temporada terminando en diciembre, ejerce línea 56."""
    temp = TemporadaMMPP(mmpp_codigo="ALPERUJO", mes_inicio=12, mes_fin=12, tiempo_descomposicion_h=8.0)
    suppliers = {
        "ALPERUJO": [SupplierTarget("Olivero X", "ALPERUJO", 600, 20)],
    }
    result = build_agenda(2027, caps_baseline, [temp], suppliers)
    # Diciembre tiene 31 días; debe planificar slots
    assert len(result.slots) > 0
    for s in result.slots:
        assert s.fecha.month == 12


def test_agenda_inverso_meses_no_genera_dias(caps_baseline):
    """Cobertura: si mes_inicio > mes_fin (config inválida) genera lista vacía y
    `build_agenda` toma la rama `if not dias: continue` (línea 119)."""
    # mes_inicio 8 > mes_fin 3 → fechas vacío
    temp = TemporadaMMPP(mmpp_codigo="ALPERUJO", mes_inicio=8, mes_fin=3, tiempo_descomposicion_h=8.0)
    fechas = list(temp.fechas(2027))
    assert fechas == []  # rama vacía garantizada

    suppliers = {
        "ALPERUJO": [SupplierTarget("Olivero Z", "ALPERUJO", 500, 20)],
    }
    result = build_agenda(2027, caps_baseline, [temp], suppliers)
    # No se generan slots porque dias está vacío
    assert result.slots == []
    assert result.total_camiones == 0
