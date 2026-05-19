"""Tests de autenticación X-API-Key.

Verifica que:
- /health es público (liveness probe para Fly).
- Endpoints protegidos rechazan 401 sin header o con key inválida.
- Endpoints protegidos aceptan con el key correcto desde Settings.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from trongkai_engine.config import get_settings
from trongkai_engine.main import app


client = TestClient(app)


def test_health_no_requiere_api_key():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_endpoint_protegido_sin_header_devuelve_401():
    r = client.post("/financial/kpis", json={"flujos": [], "wacc_anual": 0.10})
    assert r.status_code == 401
    assert "X-API-Key" in r.json()["detail"]


def test_endpoint_protegido_con_key_invalida_devuelve_401():
    r = client.post(
        "/financial/kpis",
        json={"flujos": [], "wacc_anual": 0.10},
        headers={"X-API-Key": "wrong-key"},
    )
    assert r.status_code == 401


def test_endpoint_protegido_con_key_valida_pasa_auth():
    api_key = get_settings().engine_api_key
    r = client.post(
        "/financial/kpis",
        json={
            "flujos": [
                {"mes": 1, "ingresos_ventas": 1000, "costos_directos": 500},
            ],
            "wacc_anual": 0.10,
        },
        headers={"X-API-Key": api_key},
    )
    # Pasa la auth (no es 401). Cualquier otro status implica que llegó al handler.
    assert r.status_code != 401


def test_plan_endpoint_protegido():
    r = client.post("/plan", json={})
    assert r.status_code == 401


def test_mass_balance_endpoint_protegido():
    r = client.post("/mass-balance", json={})
    assert r.status_code == 401


def test_bottleneck_endpoint_protegido():
    r = client.post("/bottleneck", json={})
    assert r.status_code == 401


def test_agenda_endpoint_protegido():
    r = client.post("/agenda", json={})
    assert r.status_code == 401


def test_whatif_endpoint_protegido():
    r = client.post("/whatif", json={})
    assert r.status_code == 401


def test_plan_export_endpoint_protegido():
    r = client.post("/plan/export", json={})
    assert r.status_code == 401


def test_plan_tornado_endpoint_protegido():
    r = client.post("/plan/tornado", json={})
    assert r.status_code == 401
