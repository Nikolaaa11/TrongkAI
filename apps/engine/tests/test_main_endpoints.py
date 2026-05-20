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


def test_plan_tornado_endpoint_devuelve_5_variables_con_shape_completo(monkeypatch):
    """POST /plan/tornado: contrato del wrapper sobre tornado_sensibilidades.

    Cubre lines 518-525 de main.py — el wrapper FastAPI no estaba ejercitado
    (los tests de financial atacan tornado_chart, no este endpoint que envuelve
    tornado_sensibilidades de plan_builder). Smoke + shape mínimo que consume
    el gráfico tornado del dashboard de directorio.
    """
    client = _open_client(monkeypatch)
    # Body vacío → defaults del PlanRequest (válidos por construcción).
    r = client.post("/plan/tornado", json={})
    assert r.status_code == 200, r.text

    body = r.json()
    assert "tornado" in body
    items = body["tornado"]

    # tornado_sensibilidades shockea 5 variables canónicas
    assert len(items) == 5
    variables = {it["variable"] for it in items}
    assert {"wacc_anual", "precio_promedio", "costo_mmpp", "opex_mensual"}.issubset(variables)

    # Shape por item — keys que consume el gráfico tornado del frontend
    expected_keys = {"variable", "delta_pct", "tir_baja", "tir_alta", "van_baja", "van_alta"}
    for it in items:
        assert expected_keys.issubset(it.keys())
        # delta_pct default es 0.20 (±20%)
        assert it["delta_pct"] == 0.20


def test_whatif_endpoint_devuelve_base_escenarios_y_deltas(monkeypatch):
    """POST /whatif: contrato del wrapper FastAPI sobre comparar_escenarios.

    Cubre lines 614-626 de main.py — el wrapper no estaba ejercitado (los tests
    de whatif atacan comparar_escenarios directo). Smoke + shape mínimo que
    consume el dashboard de simulación.
    """
    client = _open_client(monkeypatch)
    payload = {
        # base usa defaults (PlanRequest vacío válido por construcción)
        "base": {},
        "escenarios": [
            {
                "nombre": "WACC +200bps",
                "descripcion": "Subida de tasa",
                "overrides": {"wacc_anual": 0.14},
            },
            {
                "nombre": "Volumen -30%",
                "overrides": {"volumen_total_ton_ano": 700.0},
            },
        ],
    }
    r = client.post("/whatif", json=payload)
    assert r.status_code == 200, r.text

    body = r.json()
    # Contrato to_dict() de ComparacionWhatIf
    assert {"base", "escenarios"}.issubset(body.keys())
    assert {"kpis", "ingresos_anuales", "ebitda_anuales", "capex_anuales"}.issubset(
        body["base"].keys()
    )

    # 2 escenarios entran → 2 escenarios salen, con shape completo (resumen + deltas)
    assert len(body["escenarios"]) == 2
    for esc in body["escenarios"]:
        assert {"nombre", "descripcion", "overrides", "resumen", "deltas"}.issubset(
            esc.keys()
        )
        assert {"tir_pp", "van_pct", "payback_meses_delta"}.issubset(esc["deltas"].keys())

    # Los overrides se propagan tal cual al payload de respuesta
    nombres = {e["nombre"] for e in body["escenarios"]}
    assert nombres == {"WACC +200bps", "Volumen -30%"}
