"""Datos macroeconómicos Chile via mindicador.cl (mirror del Banco Central).

API gratuita pública: https://mindicador.cl/api
Indicadores disponibles: uf, ivp, dolar, dolar_intercambio, euro, ipc, utm, imacec, tpm, libra_cobre, tasa_desempleo, bitcoin.

Cacheo en memoria 24h para reducir llamadas externas y resilencia ante caídas
de mindicador.cl. Si la API falla, devolvemos snapshot conocido como fallback.

Fuente: mindicador.cl mapea diariamente https://si3.bcentral.cl/Bdemovil/BDE/IndicadoresDiarios
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None
    from urllib.request import urlopen


# Snapshot fallback (actualizar trimestralmente con el data-hunter)
SNAPSHOT_FALLBACK: dict[str, dict[str, Any]] = {
    "dolar": {"valor": 920.0, "fecha": "2026-05-19", "unidad_medida": "Pesos"},
    "uf": {"valor": 39_500.0, "fecha": "2026-05-19", "unidad_medida": "Pesos"},
    "ipc": {"valor": 0.4, "fecha": "2026-04-01", "unidad_medida": "Porcentaje"},
    "tpm": {"valor": 5.0, "fecha": "2026-05-19", "unidad_medida": "Porcentaje"},
    "utm": {"valor": 67_580.0, "fecha": "2026-05-01", "unidad_medida": "Pesos"},
    "libra_cobre": {"valor": 4.65, "fecha": "2026-05-19", "unidad_medida": "USD"},
    "tasa_desempleo": {"valor": 8.4, "fecha": "2026-04-01", "unidad_medida": "Porcentaje"},
}

_CACHE: dict[str, Any] = {"timestamp": None, "data": None}
_CACHE_TTL = timedelta(hours=24)


@dataclass
class IndicadorMacro:
    codigo: str
    valor: float
    fecha: str
    unidad_medida: str
    fuente: str = "mindicador.cl (Banco Central Chile)"


def _fetch_remote(timeout: float = 5.0) -> dict | None:
    """Intenta traer la última foto de indicadores de mindicador.cl. None si falla."""
    try:
        if httpx:
            r = httpx.get("https://mindicador.cl/api", timeout=timeout)
            if r.status_code == 200:
                return r.json()
        else:
            with urlopen("https://mindicador.cl/api", timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None


def get_indicadores(force_refresh: bool = False) -> dict[str, IndicadorMacro]:
    """Devuelve dict de indicadores. Usa cache 24h. Fallback al snapshot si falla."""
    now = datetime.now(timezone.utc)
    if (
        not force_refresh
        and _CACHE["timestamp"] is not None
        and now - _CACHE["timestamp"] < _CACHE_TTL
        and _CACHE["data"]
    ):
        return _CACHE["data"]

    remote = _fetch_remote()
    indicadores: dict[str, IndicadorMacro] = {}

    if remote:
        # Estructura de mindicador.cl: { "version": "...", "autor": "...", "fecha": "...",
        #   "uf": { "codigo": "uf", "valor": 39500, "fecha": "..." }, ... }
        for codigo, data in remote.items():
            if isinstance(data, dict) and "valor" in data:
                indicadores[codigo] = IndicadorMacro(
                    codigo=codigo,
                    valor=float(data["valor"]),
                    fecha=str(data.get("fecha", "")),
                    unidad_medida=str(data.get("unidad_medida", "")),
                )
    else:
        # Fallback snapshot
        for codigo, data in SNAPSHOT_FALLBACK.items():
            indicadores[codigo] = IndicadorMacro(
                codigo=codigo,
                valor=float(data["valor"]),
                fecha=str(data.get("fecha", "")),
                unidad_medida=str(data.get("unidad_medida", "")),
                fuente="snapshot interno (mindicador.cl no disponible)",
            )

    _CACHE["timestamp"] = now
    _CACHE["data"] = indicadores
    return indicadores


def get_tc_usd_clp() -> float:
    """Tipo de cambio USD/CLP actual con fallback."""
    inds = get_indicadores()
    return inds.get("dolar", IndicadorMacro("dolar", 920.0, "snapshot", "Pesos")).valor


def convertir_clp_a_usd(monto_clp: float) -> float:
    return monto_clp / get_tc_usd_clp()


def convertir_usd_a_clp(monto_usd: float) -> float:
    return monto_usd * get_tc_usd_clp()


def snapshot_resumen() -> dict:
    """Devuelve los 6 indicadores principales con valor + fecha."""
    inds = get_indicadores()
    return {
        "dolar_clp": inds.get("dolar").valor if "dolar" in inds else None,
        "uf_clp": inds.get("uf").valor if "uf" in inds else None,
        "ipc_pct_mensual": inds.get("ipc").valor if "ipc" in inds else None,
        "tpm_pct": inds.get("tpm").valor if "tpm" in inds else None,
        "utm_clp": inds.get("utm").valor if "utm" in inds else None,
        "tasa_desempleo_pct": inds.get("tasa_desempleo").valor if "tasa_desempleo" in inds else None,
        "fecha_ultima_actualizacion": inds.get("dolar").fecha if "dolar" in inds else None,
        "fuente": inds.get("dolar").fuente if "dolar" in inds else "snapshot",
    }
