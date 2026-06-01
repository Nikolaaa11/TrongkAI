"""Storage paths centralizados con fallback persistente.

En Fly.io con volumen montado: TRONGKAI_DATA_DIR=/data (persistente entre deploys)
En local / sin volumen: /tmp (ephemeral) o cwd.

Todos los módulos que persistan estado JSON deben usar:
    from .storage import data_path
    PATH = data_path("readiness-history.json")
"""
from __future__ import annotations

import os
from pathlib import Path


def _resolve_base_dir() -> Path:
    """Resuelve el directorio base de datos persistentes.

    Prioridad:
    1. TRONGKAI_DATA_DIR env (set por fly.toml a /data)
    2. /data si existe y es escribible
    3. /tmp/trongkai (Linux/Mac)
    4. cwd/.trongkai (Windows local fallback)
    """
    env_dir = os.environ.get("TRONGKAI_DATA_DIR")
    if env_dir:
        p = Path(env_dir)
        try:
            p.mkdir(parents=True, exist_ok=True)
            test = p / ".write_test"
            test.touch()
            test.unlink()
            return p
        except Exception:
            pass

    # Fallback /data
    p = Path("/data")
    if p.exists() and p.is_dir():
        try:
            test = p / ".trongkai_write_test"
            test.touch()
            test.unlink()
            return p
        except Exception:
            pass

    # Fallback /tmp/trongkai (ephemeral)
    p = Path("/tmp/trongkai")
    try:
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        pass

    # Último fallback: cwd
    p = Path.cwd() / ".trongkai-data"
    p.mkdir(parents=True, exist_ok=True)
    return p


_BASE_DIR: Path | None = None


def data_dir() -> Path:
    global _BASE_DIR
    if _BASE_DIR is None:
        _BASE_DIR = _resolve_base_dir()
    return _BASE_DIR


def data_path(filename: str) -> Path:
    """Devuelve path absoluto a un archivo dentro del data dir."""
    return data_dir() / filename


def is_persistent() -> bool:
    """True si el data dir es persistente (volumen Fly.io o /data real)."""
    d = data_dir()
    return str(d).startswith("/data") or os.environ.get("TRONGKAI_DATA_DIR") is not None
