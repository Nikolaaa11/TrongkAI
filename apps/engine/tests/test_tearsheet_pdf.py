"""Tests del generador de tearsheet PDF."""

from __future__ import annotations

from datetime import datetime, timezone

from trongkai_engine.tearsheet_pdf import generar_tearsheet_pdf


def _snapshot_minimo() -> dict:
    """Snapshot mínimo válido para que el generador no falle."""
    return {
        "version": "0.0.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plan": {
            "kpis": {
                "tir": 0.30,
                "van": 5_000_000_000,
                "payback_meses": 52,
                "ebitda_margin_promedio": 0.45,
                "ratio_capex_ventas": 0.20,
            },
            "ingresos_anuales": [3e9, 8e9, 15e9, 23e9, 27e9],
            "ebitda_anuales": [-0.1e9, 2.4e9, 6.5e9, 11.7e9, 14e9],
            "capex_anuales": [3e9, 5e9, 4e9, 2e9, 1e9],
        },
        "valuation": {
            "ebitda_ano5_clp": 14e9,
            "ev_base_clp": 135e9,
            "ev_rango_clp": [112e9, 169e9],
            "moic": 9.0,
            "multiplo_base": 9.63,
        },
        "escenarios_estrategicos": {
            "escenarios": [
                {"nombre": "PILOTO", "capex_total": 9e9, "tir": 0.15, "van": -0.5e9, "payback_meses": None},
                {"nombre": "INDUSTRIAL", "capex_total": 15e9, "tir": 0.30, "van": 5e9, "payback_meses": 52},
                {"nombre": "EXPANSION", "capex_total": 28e9, "tir": 0.25, "van": 3e9, "payback_meses": 57},
            ],
            "recomendacion": {"elegido": "INDUSTRIAL", "razon": "VAN positivo y mejor risk-adjusted."},
        },
        "carbon_footprint": {
            "baseline": {"emisiones_netas_5y_ton": -53_312, "revenue_creditos_5y_clp": 736e6, "es_carbono_negativo": True},
            "beccs": {"emisiones_netas_5y_ton": -138_762, "revenue_creditos_5y_clp": 1.9e9},
        },
        "compliance_rep": {
            "total_hitos": 8,
            "vigentes": 2,
            "cercanas": 2,
            "proximos_3": [
                {"nombre": "Reglamento sanitario MMA", "fecha_vigor": "2026-07-14", "severidad": "ALTA"},
            ],
            "costo_compliance_5y_clp": 215e6,
        },
        "macro_chile": {
            "dolar_clp": 899.68,
            "uf_clp": 40_459,
            "ipc_pct_mensual": -0.2,
            "tpm_pct": 4.5,
            "tasa_desempleo_pct": 8.93,
            "fuente": "mindicador.cl",
        },
        "monte_carlo_integrado": {
            "n_runs": 300,
            "tir_p5": 0.08,
            "tir_p50": 0.27,
            "tir_p95": 0.44,
            "prob_tir_supera_wacc": 0.78,
            "prob_van_positivo": 0.78,
            "promedio_anos_critico": 1.87,
        },
        "top_3_tornado": [
            {"variable": "precio_promedio", "tir_baja": 0.08, "tir_alta": 0.51, "magnitud_tir": 0.43},
            {"variable": "rendimiento_promedio", "tir_baja": 0.15, "tir_alta": 0.44, "magnitud_tir": 0.29},
            {"variable": "costo_mmpp", "tir_baja": 0.33, "tir_alta": 0.28, "magnitud_tir": 0.05},
        ],
    }


def test_genera_pdf_y_es_no_vacio():
    snap = _snapshot_minimo()
    pdf = generar_tearsheet_pdf(snap)
    assert isinstance(pdf, bytes)
    assert len(pdf) > 1_000  # PDF razonable >1KB


def test_pdf_comienza_con_magic_bytes_pdf():
    """%PDF-1.x es el magic header de cualquier PDF."""
    snap = _snapshot_minimo()
    pdf = generar_tearsheet_pdf(snap)
    assert pdf.startswith(b"%PDF-")


def test_pdf_se_genera_aunque_faltan_campos_opcionales():
    snap = _snapshot_minimo()
    # Quitar el tornado (opcional)
    snap.pop("top_3_tornado", None)
    pdf = generar_tearsheet_pdf(snap)
    assert pdf.startswith(b"%PDF-")


def test_payback_meses_none_no_rompe():
    snap = _snapshot_minimo()
    snap["plan"]["kpis"]["payback_meses"] = None
    pdf = generar_tearsheet_pdf(snap)
    assert pdf.startswith(b"%PDF-")
