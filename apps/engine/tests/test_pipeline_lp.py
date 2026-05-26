"""Tests del Pipeline LP."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from trongkai_engine import pipeline_lp as plp


@pytest.fixture
def temp_path(monkeypatch):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        p = Path(f.name)
    p.unlink(missing_ok=True)
    monkeypatch.setattr(plp, "PIPELINE_PATH", p)
    yield p
    p.unlink(missing_ok=True)


def test_seed_inicial(temp_path):
    """Sin archivo, devuelve seed inicial con 5 LPs."""
    lps = plp.list_lps()
    assert len(lps) == 5
    nombres = [lp["nombre"] for lp in lps]
    assert "BID Invest" in nombres


def test_upsert_nuevo_lp(temp_path):
    nuevo = plp.upsert_lp({
        "nombre": "Nuevo LP",
        "tipo": "fondo",
        "pais": "USA",
        "ticket_esperado_usd": 5_000_000,
        "etapa": "prospect",
        "prob_cierre": 30,
        "proxima_accion": "Mail intro",
        "proxima_accion_owner": "Nicolás",
        "proxima_accion_fecha": "2026-06-01",
    })
    assert nuevo["id"].startswith("lp-")
    assert nuevo["ticket_ponderado_usd"] == 1_500_000  # 5M × 30%

    lps = plp.list_lps()
    assert any(lp["nombre"] == "Nuevo LP" for lp in lps)


def test_upsert_actualiza_existente(temp_path):
    lps_inicial = plp.list_lps()
    lp_id = lps_inicial[0]["id"]
    actualizado = plp.upsert_lp({
        "id": lp_id,
        "prob_cierre": 80,
        "etapa": "comprometido",
        "nombre": lps_inicial[0]["nombre"],
        "tipo": lps_inicial[0]["tipo"],
        "pais": lps_inicial[0]["pais"],
        "ticket_esperado_usd": lps_inicial[0]["ticket_esperado_usd"],
        "proxima_accion": "Cerrar",
        "proxima_accion_owner": "Nicolás",
        "proxima_accion_fecha": "2026-07-01",
    })
    assert actualizado["prob_cierre"] == 80
    assert actualizado["etapa"] == "comprometido"


def test_delete(temp_path):
    lps_inicial = plp.list_lps()
    lp_id = lps_inicial[0]["id"]
    ok = plp.delete_lp(lp_id)
    assert ok
    assert not any(lp["id"] == lp_id for lp in plp.list_lps())


def test_resumen_pipeline(temp_path):
    r = plp.resumen_pipeline()
    assert r.total_lps == 5
    assert r.ticket_pipeline_usd > 0
    assert r.ticket_ponderado_usd < r.ticket_pipeline_usd
    assert r.objetivo_usd == 40_000_000
    assert "prospect" in r.por_etapa


def test_resumen_serializa(temp_path):
    r = plp.resumen_pipeline().to_dict()
    assert "ticket_pipeline_usd" in r
    assert "pct_objetivo_pipeline" in r
