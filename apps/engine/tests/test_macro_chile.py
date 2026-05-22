"""Tests del módulo macro_chile (con fallback offline)."""

from __future__ import annotations

from unittest.mock import patch

from trongkai_engine.macro_chile import (
    SNAPSHOT_FALLBACK,
    convertir_clp_a_usd,
    convertir_usd_a_clp,
    get_indicadores,
    get_tc_usd_clp,
    snapshot_resumen,
)


def test_fallback_se_usa_si_api_falla():
    """Si la API remota devuelve None, usar SNAPSHOT_FALLBACK."""
    with patch("trongkai_engine.macro_chile._fetch_remote", return_value=None):
        # Force refresh para no usar cache de tests previos
        inds = get_indicadores(force_refresh=True)
        assert "dolar" in inds
        assert inds["dolar"].valor == SNAPSHOT_FALLBACK["dolar"]["valor"]
        assert "snapshot" in inds["dolar"].fuente.lower()


def test_get_tc_usd_clp_devuelve_float_positivo():
    with patch("trongkai_engine.macro_chile._fetch_remote", return_value=None):
        tc = get_tc_usd_clp()
        assert tc > 0
        # Range razonable para CLP: 700-1500
        assert 500 < tc < 2000


def test_conversion_clp_usd_idempotente():
    with patch("trongkai_engine.macro_chile._fetch_remote", return_value=None):
        original = 1_000_000_000
        usd = convertir_clp_a_usd(original)
        clp = convertir_usd_a_clp(usd)
        assert abs(clp - original) < 1


def test_snapshot_resumen_tiene_6_campos():
    with patch("trongkai_engine.macro_chile._fetch_remote", return_value=None):
        r = snapshot_resumen()
        assert "dolar_clp" in r
        assert "uf_clp" in r
        assert "ipc_pct_mensual" in r
        assert "tpm_pct" in r
        assert "fecha_ultima_actualizacion" in r


def test_api_real_devuelve_datos_si_disponible():
    """Si la API responde, los valores deben ser razonables."""
    mock_response = {
        "dolar": {"codigo": "dolar", "valor": 950.0, "fecha": "2026-05-22", "unidad_medida": "Pesos"},
        "uf": {"codigo": "uf", "valor": 39_700.0, "fecha": "2026-05-22", "unidad_medida": "Pesos"},
    }
    with patch("trongkai_engine.macro_chile._fetch_remote", return_value=mock_response):
        inds = get_indicadores(force_refresh=True)
        assert inds["dolar"].valor == 950.0
        assert inds["uf"].valor == 39_700.0
        assert "mindicador" in inds["dolar"].fuente
