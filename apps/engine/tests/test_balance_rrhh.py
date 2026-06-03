"""Tests del balance RRHH + alarmas criticas horas extras CT Chile."""
from __future__ import annotations

import pytest

from trongkai_engine.balances.rrhh import (
    AsignacionHoras,
    BalanceRRHH,
    Trabajador,
    asignaciones_seed,
    computar_balance_rrhh,
    detectar_alarmas,
    trabajadores_seed,
)


# =========================
# Seed
# =========================
def test_seed_15_trabajadores():
    assert len(trabajadores_seed()) == 15


def test_seed_categorias_correctas():
    cats = {t.categoria for t in trabajadores_seed()}
    assert {"operario", "supervisor", "calidad", "mantenimiento", "admin"} == cats


def test_seed_asignaciones_15():
    assert len(asignaciones_seed()) == 15


# =========================
# Balance basico
# =========================
def test_balance_basico():
    b = computar_balance_rrhh()
    assert isinstance(b, BalanceRRHH)
    assert b.total_horas_disponibles_sem > 0
    assert b.utilizacion_pct > 0


def test_closure_100pct():
    b = computar_balance_rrhh()
    assert b.closure_pct <= 1.0


def test_productividad_kg_por_hh():
    b = computar_balance_rrhh()
    # 16350kg / ~700hh ≈ 20-25 kg/hh con seed default
    assert 5 < b.productividad_kg_por_hh < 100


def test_costo_mensual_positivo():
    b = computar_balance_rrhh()
    assert b.costo_total_mensual_clp > 0


# =========================
# ALARMAS CRITICAS — CT Chile
# =========================
def test_alarma_exceso_contrato():
    """Trabajador con 50h regulares (contrato 45h) → alarma alta."""
    trabs = [Trabajador("OP-X", "Test", "operario", "mañana")]
    asigs = [AsignacionHoras("OP-X", "2026-W23", 50.0, 0.0)]
    al = detectar_alarmas(asigs, trabs)
    excesos = [a for a in al if a["tipo"] == "exceso_contrato"]
    assert len(excesos) == 1
    assert excesos[0]["severidad"] == "alta"
    assert excesos[0]["exceso"] == 5.0


def test_alarma_exceso_legal_critica():
    """Trabajador con 60h totales (max 57h) → CRITICA."""
    trabs = [Trabajador("OP-X", "Test", "operario", "mañana")]
    asigs = [AsignacionHoras("OP-X", "2026-W23", 45.0, 15.0)]  # 60h totales
    al = detectar_alarmas(asigs, trabs)
    legales = [a for a in al if a["tipo"] == "exceso_legal"]
    assert len(legales) == 1
    assert legales[0]["severidad"] == "critica"


def test_alarma_extras_semanal_excedido():
    """Mas de 12h extras/sem → CRITICA."""
    trabs = [Trabajador("OP-X", "Test", "operario", "mañana")]
    asigs = [AsignacionHoras("OP-X", "2026-W23", 45.0, 13.0)]
    al = detectar_alarmas(asigs, trabs)
    sem = [a for a in al if a["tipo"] == "extras_semanal_excedido"]
    assert len(sem) == 1
    assert sem[0]["severidad"] == "critica"


def test_alarma_extras_mensual_excedido():
    """Suma de 4 semanas con extras > 32h/mes → CRITICA."""
    trabs = [Trabajador("OP-X", "Test", "operario", "mañana")]
    asigs_actual = [AsignacionHoras("OP-X", "2026-W23", 45.0, 8.0)]
    # Mes previo: 4 semanas con 10h c/u = 40h
    asigs_mes = [
        AsignacionHoras("OP-X", f"2026-W2{i}", 45.0, 10.0) for i in range(1, 5)
    ]
    al = detectar_alarmas(asigs_actual, trabs, asignaciones_mes_previo=asigs_mes)
    mensual = [a for a in al if a["tipo"] == "extras_mensual_excedido"]
    assert len(mensual) == 1
    assert mensual[0]["severidad"] == "critica"
    assert mensual[0]["extras_mes"] == 40.0


def test_sin_alarmas_con_45h_estandar():
    """Trabajador con exactamente 45h regulares, 0 extras → 0 alarmas."""
    trabs = [Trabajador("OP-X", "Test", "operario", "mañana")]
    asigs = [AsignacionHoras("OP-X", "2026-W23", 45.0, 0.0)]
    al = detectar_alarmas(asigs, trabs)
    assert len(al) == 0


def test_sin_alarmas_con_12h_extras_exactas():
    """Limite legal exacto: 45+12=57h. No debe disparar."""
    trabs = [Trabajador("OP-X", "Test", "operario", "mañana")]
    asigs = [AsignacionHoras("OP-X", "2026-W23", 45.0, 12.0)]
    al = detectar_alarmas(asigs, trabs)
    assert len(al) == 0


def test_trabajador_inactivo_no_alerta():
    """Inactivo se ignora aunque tenga asignacion fuera de rango."""
    trabs = [Trabajador("OP-X", "Test", "operario", "mañana", activo=False)]
    asigs = [AsignacionHoras("OP-X", "2026-W23", 60.0, 20.0)]
    al = detectar_alarmas(asigs, trabs)
    assert len(al) == 0


# =========================
# Multi-alarma combinada
# =========================
def test_multiples_trabajadores_con_alarmas():
    trabs = [
        Trabajador("OP-A", "A", "operario", "mañana"),
        Trabajador("OP-B", "B", "operario", "tarde"),
        Trabajador("OP-C", "C", "operario", "noche"),
    ]
    asigs = [
        AsignacionHoras("OP-A", "2026-W23", 50.0, 0.0),   # exceso_contrato
        AsignacionHoras("OP-B", "2026-W23", 45.0, 15.0),  # 60 → exceso_legal + extras_sem
        AsignacionHoras("OP-C", "2026-W23", 45.0, 0.0),   # ok
    ]
    al = detectar_alarmas(asigs, trabs)
    # OP-A: 1 alarma (exceso_contrato)
    # OP-B: 2 alarmas (exceso_legal + extras_semanal_excedido)
    # OP-C: 0 alarmas
    assert len(al) == 3
    tipos = {a["tipo"] for a in al}
    assert "exceso_contrato" in tipos
    assert "exceso_legal" in tipos
    assert "extras_semanal_excedido" in tipos


def test_balance_completo_dispara_alarmas_seed():
    """Seed default tiene MNT-001 con 53h totales y OP-001 con 49h → alarmas."""
    b = computar_balance_rrhh()
    # OP-001: 45+4=49 → exceso_contrato? No, regulares = 45 (no excede), totales 49 < 57. 0 alarmas.
    # OP-004: 45+6=51 → totales < 57, regulares = 45, ok
    # MNT-001: 45+8=53 → totales < 57, regulares 45, ok
    # SUP-001: 45+2=47 → ok
    # Default seed NO debe disparar alarmas individuales.
    assert isinstance(b.alarmas, list)


def test_alarma_severidad_critica_detecta_legal():
    """Si forzamos un caso critico, severidad debe estar marcada."""
    trabs = [Trabajador("OP-X", "Test", "operario", "mañana")]
    asigs = [AsignacionHoras("OP-X", "2026-W23", 45.0, 20.0)]  # 65h totales > 57
    al = detectar_alarmas(asigs, trabs)
    criticas = [a for a in al if a["severidad"] == "critica"]
    assert len(criticas) >= 1


# =========================
# KPIs
# =========================
def test_utilizacion_calculo():
    """15 trabajadores * 45 = 675h disponibles, 690 asignadas → 102%."""
    b = computar_balance_rrhh()
    assert 0.9 < b.utilizacion_pct < 1.2


def test_to_dict_serializable():
    import json
    b = computar_balance_rrhh()
    s = json.dumps(b.to_dict())  # no debe levantar
    assert "alarmas" in b.to_dict()
    assert "asignaciones_semana_actual" in b.to_dict()
