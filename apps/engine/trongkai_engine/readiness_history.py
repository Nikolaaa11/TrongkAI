"""Histórico del Investment Readiness Score.

Persiste snapshots del score en un JSON local (path configurable). Para
trackear evolución del proyecto y mostrar al directorio cómo va mejorando.

Storage: /tmp/trongkai-readiness-history.json (en Fly.io persiste en tmpfs
del container — para producción real usar Supabase / DB).

Estructura del JSON:
    [
        {"timestamp": "2026-05-25T10:00:00Z", "score": 84.7, "dimensiones": [...]},
        {"timestamp": "2026-05-26T10:00:00Z", "score": 86.2, "dimensiones": [...]},
        ...
    ]
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HISTORY_PATH = Path("/tmp/trongkai-readiness-history.json")
MAX_ENTRIES = 1000  # Cap para evitar crecimiento ilimitado


def _load_history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    try:
        with HISTORY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_history(history: list[dict]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2, default=str)


def add_snapshot(readiness: dict[str, Any], evento: str = "") -> dict:
    """Agrega un snapshot del readiness al histórico.

    Args:
        readiness: dict del readiness score (de calcular_readiness_score().to_dict())
        evento: descripción opcional ("Llegó cotización MMPP", "LOI firmada", etc)

    Returns:
        el entry agregado
    """
    history = _load_history()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": readiness.get("score_total", 0),
        "interpretacion": readiness.get("interpretacion", ""),
        "evento": evento,
        "dimensiones": [
            {
                "nombre": d["nombre"],
                "score_0_100": d["score_0_100"],
                "aporte_total": d["aporte_total"],
            }
            for d in readiness.get("dimensiones", [])
        ],
    }
    history.append(entry)
    # Cap
    if len(history) > MAX_ENTRIES:
        history = history[-MAX_ENTRIES:]
    _save_history(history)
    return entry


def get_history(limit: int | None = None) -> list[dict]:
    """Devuelve el histórico completo o los últimos N entries."""
    history = _load_history()
    if limit is not None:
        return history[-limit:]
    return history


def get_evolucion_compacta(limit: int = 30) -> list[dict]:
    """Devuelve solo timestamp + score para graficar."""
    history = _load_history()
    return [
        {"timestamp": h["timestamp"][:10], "score": h["score"]}
        for h in history[-limit:]
    ]


def stats_progreso() -> dict[str, Any]:
    """Calcula estadísticas del progreso del score."""
    history = _load_history()
    if not history:
        return {
            "total_snapshots": 0,
            "score_actual": None,
            "score_inicial": None,
            "delta": None,
            "fecha_inicio": None,
        }
    return {
        "total_snapshots": len(history),
        "score_actual": history[-1]["score"],
        "score_inicial": history[0]["score"],
        "delta": round(history[-1]["score"] - history[0]["score"], 1),
        "fecha_inicio": history[0]["timestamp"][:10],
        "fecha_ultima": history[-1]["timestamp"][:10],
    }
