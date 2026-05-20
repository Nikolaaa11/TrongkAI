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


def test_bottleneck_endpoint_devuelve_secador_y_contrato_completo(monkeypatch):
    """POST /bottleneck: contrato HTTP del endpoint que envuelve compute_bottleneck.

    Cubre lines 215-234 de main.py — el wrapper FastAPI no estaba ejercitado
    (los tests de bottleneck atacan compute_bottleneck directo). Smoke + shape
    del response que consume el frontend del Módulo 1.
    """
    client = _open_client(monkeypatch)
    # Baseline tomasa: secador es bottleneck a 2.5 ton/h (ver test_bottleneck.py).
    payload = {
        "capacidades": [
            {"etapa": "RECEPCION", "ton_por_hora": 10, "tiempo_residencia_h": 0.2},
            {"etapa": "ALIMENTACION", "ton_por_hora": 8, "tiempo_residencia_h": 0.1},
            {"etapa": "HOMOG_1", "ton_por_hora": 8, "tiempo_residencia_h": 0.1},
            {"etapa": "PEF", "ton_por_hora": 6, "tiempo_residencia_h": 0.1},
            {"etapa": "PRENSADO_MECANICO", "ton_por_hora": 5, "tiempo_residencia_h": 0.2},
            {"etapa": "SECADO", "ton_por_hora": 2.5, "tiempo_residencia_h": 1.5},
            {"etapa": "ENSACADO", "ton_por_hora": 5, "tiempo_residencia_h": 0.1},
        ],
        "tiempo_descomposicion_h": 3.0,
        "capacidad_camion_ton": 20.0,
    }
    r = client.post("/bottleneck", json=payload)
    assert r.status_code == 200, r.text

    body = r.json()
    # Contrato mínimo que el frontend consume
    expected_keys = {
        "flujo_max_ton_h",
        "etapa_bottleneck",
        "tiempo_proceso_total_h",
        "tiempo_descomposicion_h",
        "ventana_segura_h",
        "puede_recibir",
        "camiones_max_dia",
        "horas_operativas_dia",
        "incertidumbres",
        "alerta",
    }
    assert expected_keys.issubset(body.keys())

    # Valores load-bearing: secador es bottleneck, planta puede recibir.
    assert body["etapa_bottleneck"] == "SECADO"
    assert body["flujo_max_ton_h"] == 2.5
    assert body["puede_recibir"] is True
    assert body["camiones_max_dia"] == 3  # 2.5 × 24 / 20 = 3


def test_bottleneck_endpoint_devuelve_422_con_input_invalido(monkeypatch):
    """POST /bottleneck: la rama except ValueError → HTTPException 422 (line 231-232).

    Capacidades vacías hace que compute_bottleneck eleve ValueError, que el
    endpoint mapea a 422 para no exponer 500 al frontend.
    """
    client = _open_client(monkeypatch)
    payload = {
        "capacidades": [],  # ValueError: "Se requiere al menos una etapa..."
        "tiempo_descomposicion_h": 3.0,
    }
    r = client.post("/bottleneck", json=payload)
    assert r.status_code == 422, r.text
    assert "detail" in r.json()


def test_plan_endpoint_devuelve_kpis_resumen_y_flujos(monkeypatch):
    """POST /plan: contrato del wrapper FastAPI sobre build_plan.

    Cubre lines 425-473 de main.py — el wrapper no estaba ejercitado (los tests
    de plan_builder atacan build_plan directo). Smoke + shape mínimo que el
    dashboard de directorio (Módulo 3) consume.
    """
    client = _open_client(monkeypatch)
    # Body vacío usa defaults del PlanRequest — válido por construcción.
    r = client.post("/plan", json={})
    assert r.status_code == 200, r.text

    body = r.json()
    assert {"kpis", "resumen_anual", "por_marca", "flujos_meses"}.issubset(body.keys())

    # KPIs shape — keys que consume el tornado/dashboard
    assert {
        "tir_proyecto_anual",
        "van",
        "payback_meses",
        "ebitda_margin_promedio",
        "ratio_capex_ventas",
    }.issubset(body["kpis"].keys())

    # Plan 5 Años → 5 años resumidos, 60 flujos mensuales
    assert len(body["resumen_anual"]) == 5
    assert len(body["flujos_meses"]) == 60
    assert body["resumen_anual"][0]["ano"] == 1
    assert body["resumen_anual"][4]["ano"] == 5

    # Invariante Plan: año 5 (100% volumen) > año 1 (30% volumen)
    assert body["resumen_anual"][4]["ingresos"] > body["resumen_anual"][0]["ingresos"]
