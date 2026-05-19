"""Tests de autenticación X-API-Key — modo graceful.

Comportamiento:
- Si ENGINE_API_KEY no está seteada o vale "changeme-internal-only" → endpoints abiertos.
- Si ENGINE_API_KEY tiene un valor real → header X-API-Key obligatorio.
- /health siempre público (Fly liveness probe).
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient


def _client_with_key(api_key: str | None) -> TestClient:
    """Recarga config + main con un ENGINE_API_KEY específico vía monkeypatching."""
    from trongkai_engine import config, main
    importlib.reload(config)
    importlib.reload(main)
    if api_key is None:
        main.get_settings().engine_api_key = "changeme-internal-only"
    else:
        main.get_settings().engine_api_key = api_key
    main.get_settings.cache_clear() if hasattr(main.get_settings, "cache_clear") else None
    # Forzar settings inline
    main.get_settings = lambda: type("S", (), {"engine_api_key": api_key or "changeme-internal-only"})()
    return TestClient(main.app)


# ----- /health siempre abierto -----


def test_health_no_requiere_api_key():
    from trongkai_engine.main import app
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ----- Modo default (API_KEY no seteada): endpoints abiertos -----


def test_modo_default_endpoints_abiertos(monkeypatch):
    """Sin ENGINE_API_KEY (o = default), los endpoints no requieren header."""
    from trongkai_engine import main
    monkeypatch.setattr(main, "get_settings", lambda: type("S", (), {"engine_api_key": "changeme-internal-only"})())
    client = TestClient(main.app)
    # Llamada sin header debería pasar la auth — el endpoint puede fallar por payload,
    # pero NO debe ser 401.
    r = client.post("/financial/kpis", json={"flujos": [], "wacc_anual": 0.10})
    assert r.status_code != 401


def test_modo_default_string_vacio_tambien_abierto(monkeypatch):
    from trongkai_engine import main
    monkeypatch.setattr(main, "get_settings", lambda: type("S", (), {"engine_api_key": ""})())
    client = TestClient(main.app)
    r = client.post("/financial/kpis", json={"flujos": [], "wacc_anual": 0.10})
    assert r.status_code != 401


# ----- Modo lock (API_KEY real): rechaza sin header -----


def test_modo_lock_sin_header_devuelve_401(monkeypatch):
    from trongkai_engine import main
    monkeypatch.setattr(main, "get_settings", lambda: type("S", (), {"engine_api_key": "secret-real-key-123"})())
    client = TestClient(main.app)
    r = client.post("/financial/kpis", json={"flujos": [], "wacc_anual": 0.10})
    assert r.status_code == 401
    assert "X-API-Key" in r.json()["detail"]


def test_modo_lock_con_key_invalida_devuelve_401(monkeypatch):
    from trongkai_engine import main
    monkeypatch.setattr(main, "get_settings", lambda: type("S", (), {"engine_api_key": "secret-real-key-123"})())
    client = TestClient(main.app)
    r = client.post(
        "/financial/kpis",
        json={"flujos": [], "wacc_anual": 0.10},
        headers={"X-API-Key": "wrong-key"},
    )
    assert r.status_code == 401


def test_modo_lock_con_key_valida_pasa(monkeypatch):
    from trongkai_engine import main
    monkeypatch.setattr(main, "get_settings", lambda: type("S", (), {"engine_api_key": "secret-real-key-123"})())
    client = TestClient(main.app)
    r = client.post(
        "/financial/kpis",
        json={
            "flujos": [
                {"mes": 1, "ingresos_ventas": 1000, "costos_directos": 500},
            ],
            "wacc_anual": 0.10,
        },
        headers={"X-API-Key": "secret-real-key-123"},
    )
    assert r.status_code != 401


# ----- Coverage por endpoint protegido (modo lock) -----


@pytest.mark.parametrize(
    "path",
    [
        "/plan",
        "/mass-balance",
        "/bottleneck",
        "/agenda",
        "/whatif",
        "/plan/export",
        "/plan/tornado",
    ],
)
def test_todos_los_endpoints_protegidos_rechazan_sin_header(monkeypatch, path):
    from trongkai_engine import main
    monkeypatch.setattr(main, "get_settings", lambda: type("S", (), {"engine_api_key": "secret-real-key-123"})())
    client = TestClient(main.app)
    r = client.post(path, json={})
    assert r.status_code == 401, f"{path} no rechazó sin X-API-Key (got {r.status_code})"
