"""Tests de los catálogos clientes_reales y tecnologias_catalog."""

from __future__ import annotations

from trongkai_engine.clientes_reales import (
    CLIENTES, BENCHMARKS_PROTEINAS,
    listar_clientes, listar_benchmarks, resumen_clientes,
)
from trongkai_engine.tecnologias_catalog import (
    TECNOLOGIAS, listar_tecnologias, resumen_tecnologias,
)


# ===== Clientes =====

def test_clientes_no_vacios():
    assert len(CLIENTES) >= 5
    nombres = [c.nombre for c in CLIENTES]
    assert "Agrozzi" in nombres
    assert "Sugal Group" in nombres


def test_cliente_to_dict():
    c = listar_clientes()[0]
    for k in ["id", "nombre", "pais", "sector", "producto_target",
              "volumen_anual_estimado_ton", "estado_relacion",
              "valor_anual_estimado_usd"]:
        assert k in c


def test_resumen_clientes_consistente():
    r = resumen_clientes()
    assert r["total_clientes"] == len(CLIENTES)
    assert r["valor_anual_total_usd"] > 0
    assert r["volumen_anual_total_ton"] > 0
    assert r["benchmarks_count"] == len(BENCHMARKS_PROTEINAS)


def test_benchmarks_tienen_precio():
    for b in listar_benchmarks():
        assert b.get("precio_referencia_usd_kg", 0) > 0


def test_estados_relacion_validos():
    estados_validos = {"prospect", "contactado", "dd", "loi", "contrato", "perdido"}
    for c in CLIENTES:
        assert c.estado_relacion in estados_validos


# ===== Tecnologías =====

def test_tecnologias_no_vacias():
    assert len(TECNOLOGIAS) >= 3
    nombres = [t.nombre for t in TECNOLOGIAS]
    assert any("PEF" in n or "Opticept" in n for n in nombres)
    assert any("nfrasonido" in n for n in nombres)


def test_tecnologia_to_dict():
    t = listar_tecnologias()[0]
    for k in ["id", "nombre", "proveedor", "trl", "capex_usd", "estado_validacion"]:
        assert k in t


def test_trl_en_rango():
    for t in TECNOLOGIAS:
        assert 1 <= t.trl <= 9


def test_resumen_tecnologias():
    r = resumen_tecnologias()
    assert r["total_tecnologias"] == len(TECNOLOGIAS)
    assert r["capex_stack_usd"] > 0
    assert 1 <= r["trl_promedio"] <= 9


def test_capex_stack_razonable():
    """CapEx stack ~USD 1-2M razonable para planta piloto."""
    r = resumen_tecnologias()
    # Stack tecnológico debería estar entre USD 500k y USD 5M
    assert 500_000 <= r["capex_stack_usd"] <= 5_000_000
