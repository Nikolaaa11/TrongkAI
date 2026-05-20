"""Smoke tests de endpoints HTTP de main.py.

Cubre branches no testeados por test_auth.py (que sólo valida la auth, no el
contrato del endpoint). El primer caso cubre /plan/escenarios-estrategicos —
GET sin payload, ejercitable directo.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _open_client(monkeypatch) -> TestClient:
    """Devuelve TestClient con auth desactivada (modo default)."""
    from trongkai_engine import main
    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: type("S", (), {"engine_api_key": "changeme-internal-only"})(),
    )
    return TestClient(main.app)


def test_escenarios_estrategicos_devuelve_3_escenarios_y_recomendacion(monkeypatch):
    """GET /plan/escenarios-estrategicos: contrato básico del endpoint.

    Cubre lines 555-586 de main.py (en particular el body 556-557 que faltaba)
    y asegura el shape esperado por el frontend.
    """
    client = _open_client(monkeypatch)
    r = client.get("/plan/escenarios-estrategicos")
    assert r.status_code == 200, r.text

    body = r.json()
    assert "escenarios" in body
    assert "recomendacion" in body
    assert len(body["escenarios"]) == 3

    nombres = {e["nombre"] for e in body["escenarios"]}
    # Los 3 escenarios canónicos del SUPER_PROMPT
    assert nombres == {"PILOTO", "INDUSTRIAL", "EXPANSION"}

    # Shape mínimo por escenario — lo que consume el dashboard
    for e in body["escenarios"]:
        assert "kpis" in e
        assert {"tir", "van", "payback_meses"}.issubset(e["kpis"].keys())
        assert "capex_total" in e
        assert "por_marca" in e
        assert e["volumen_objetivo_ton_ano"] > 0
