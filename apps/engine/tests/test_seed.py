"""Tests del seed Excel → payload.

No requiere DB — sólo valida integridad referencial del dict en memoria.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"


def _load_seed_module():
    """Carga scripts/seed-from-excel.py (hyphen impide import normal)."""
    spec = importlib.util.spec_from_file_location("seed_from_excel", SCRIPTS / "seed-from-excel.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["seed_from_excel"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def payload():
    seed = _load_seed_module()
    return seed.build_payload()


def test_mmpp_count(payload):
    assert len(payload.materias_primas) == 5
    codigos = {m["codigo"] for m in payload.materias_primas}
    assert codigos == {"ALPERUJO", "TOMASA", "POMASA", "ORUJO_UVA", "LEVADURA"}


def test_alperujo_humedad_correcta(payload):
    alperujo = next(m for m in payload.materias_primas if m["codigo"] == "ALPERUJO")
    assert alperujo["humedadInicialPct"] == pytest.approx(0.65)
    assert alperujo["materiaSolidaPct"] == pytest.approx(0.35)


def test_suppliers_4_oliveros_activos(payload):
    activos = [s for s in payload.suppliers if s["status"] == "ACTIVO"]
    assert len(activos) == 4
    nombres = {s["nombre"] for s in activos}
    assert {"Olivero 1", "Olivero 2", "Olivero 3", "Olivero 4"}.issubset(nombres)


def test_olivero_1_caso_1_pagamos_y_cobramos(payload):
    o1 = next(s for s in payload.suppliers if s["nombre"] == "Olivero 1")
    assert o1["casoLogistico"] == "CASO_1"
    assert o1["distanciaKm"] == 82
    assert o1["tarifaFleteClpKm"] == 1800
    # pago_recepcion -10 = al proveedor le cobramos $10/kg
    assert o1["pagoRecepcionClpKg"] == -10
    assert o1["volumenAnualComprometidoTon"] == 500


def test_olivero_3_caso_3_al_lado_sin_costos(payload):
    o3 = next(s for s in payload.suppliers if s["nombre"] == "Olivero 3")
    assert o3["casoLogistico"] == "CASO_3"
    assert o3["tarifaFleteClpKm"] == 0
    assert o3["pagoRecepcionClpKg"] == 0
    assert o3["volumenAnualComprometidoTon"] == 2000  # el más grande


def test_productos_son_12_y_marcas_validas(payload):
    assert len(payload.productos) == 12
    marcas = {p["marca"] for p in payload.productos}
    assert marcas.issubset({"FEED", "FOOD", "SERVICIOS"})
    feed = [p for p in payload.productos if p["marca"] == "FEED"]
    food = [p for p in payload.productos if p["marca"] == "FOOD"]
    assert len(feed) >= 4
    assert len(food) >= 4


def test_productos_referencian_mmpp_existentes(payload):
    """Integridad referencial: mmppOrigen debe existir o ser None."""
    mmpp_codigos = {m["codigo"] for m in payload.materias_primas}
    for p in payload.productos:
        if p["mmppOrigen"] is not None:
            assert p["mmppOrigen"] in mmpp_codigos, f"{p['codigo']} referencia MMPP inválida"


def test_supuestos_tienen_estado_valido(payload):
    estados_validos = {"PD", "OK_PROVISORIO", "OK_VALIDADO_JOSE", "OK_VALIDADO_CLAUDIO",
                       "OK_VALIDADO_JAIME", "OK_VALIDADO_DIRECTORIO", "NO_APLICA"}
    for s in payload.supuestos:
        assert s["estado"] in estados_validos


def test_capacidades_son_10_etapas(payload):
    assert len(payload.capacidades) == 10
    etapas = {c["etapa"] for c in payload.capacidades}
    assert "SECADO" in etapas
    assert "PEF" in etapas
    # PEF, TRICANTER y EXTRACCION son opcionales
    opcionales = {c["etapa"] for c in payload.capacidades if c["opcional"]}
    assert {"PEF", "TRICANTER", "EXTRACCION"}.issubset(opcionales)


def test_suppliers_referencian_mmpp_existentes(payload):
    mmpp_codigos = {m["codigo"] for m in payload.materias_primas}
    for s in payload.suppliers:
        assert s["mmppCodigo"] in mmpp_codigos


def test_no_supuesto_critico_en_estado_validado_sin_fuente(payload):
    """Un supuesto OK_VALIDADO_DIRECTORIO debería tener fuente clara."""
    for s in payload.supuestos:
        if s["estado"].startswith("OK_VALIDADO"):
            assert s["fuente"] != "", f"Supuesto {s['clave']} validado sin fuente"
