"""Audit Trail — historial inmutable de cambios al modelo.

Cada cambio queda registrado con:
- timestamp UTC
- tipo (matriz_celda, supuesto, decision, hito, etc)
- actor (usuario o "system" si fue automático)
- payload (antes / después / metadata)
- descripcion humana

Storage: JSON local en /tmp/trongkai-audit-trail.json (en prod usar Supabase).

Useful for:
- Defenderse en due diligence ("¿quién cambió este número?")
- Detectar regresiones del modelo
- Onboarding de auditor externo
- Compliance/accountability
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

AUDIT_PATH = Path("/tmp/trongkai-audit-trail.json")
MAX_ENTRIES = 5000

TipoEvento = Literal[
    "matriz_celda_actualizada",
    "supuesto_cambiado",
    "decision_marcada",
    "hito_completado",
    "datos_equipo_recibidos",
    "snapshot_creado",
    "alerta_resuelta",
    "deploy",
    "modelo_recalibrado",
    "otro",
]


@dataclass
class EntradaAudit:
    timestamp: str
    tipo: str
    actor: str
    descripcion: str
    valor_anterior: Any = None
    valor_nuevo: Any = None
    metadata: dict = field(default_factory=dict)
    impacto_estimado: str | None = None  # texto opcional describing impact

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "tipo": self.tipo,
            "actor": self.actor,
            "descripcion": self.descripcion,
            "valor_anterior": self.valor_anterior,
            "valor_nuevo": self.valor_nuevo,
            "metadata": self.metadata,
            "impacto_estimado": self.impacto_estimado,
        }


def _load() -> list[dict]:
    if not AUDIT_PATH.exists():
        return []
    try:
        with AUDIT_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(entries: list[dict]) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2, default=str)


def log_evento(
    tipo: str,
    descripcion: str,
    actor: str = "system",
    valor_anterior: Any = None,
    valor_nuevo: Any = None,
    metadata: dict | None = None,
    impacto_estimado: str | None = None,
) -> EntradaAudit:
    """Registra un evento en el audit trail."""
    entries = _load()
    entrada = EntradaAudit(
        timestamp=datetime.now(timezone.utc).isoformat(),
        tipo=tipo,
        actor=actor,
        descripcion=descripcion,
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        metadata=metadata or {},
        impacto_estimado=impacto_estimado,
    )
    entries.append(entrada.to_dict())
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]
    _save(entries)
    return entrada


def get_audit_trail(
    limit: int = 50,
    tipo: str | None = None,
    desde: str | None = None,
) -> list[dict]:
    """Devuelve entradas del audit trail filtradas y ordenadas (más nuevo primero)."""
    entries = _load()
    if tipo:
        entries = [e for e in entries if e.get("tipo") == tipo]
    if desde:
        entries = [e for e in entries if e.get("timestamp", "") >= desde]
    # Más recientes primero
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def stats_audit_trail() -> dict:
    """Estadísticas del audit trail."""
    entries = _load()
    by_tipo: dict[str, int] = {}
    by_actor: dict[str, int] = {}
    for e in entries:
        by_tipo[e.get("tipo", "?")] = by_tipo.get(e.get("tipo", "?"), 0) + 1
        by_actor[e.get("actor", "?")] = by_actor.get(e.get("actor", "?"), 0) + 1
    return {
        "total_eventos": len(entries),
        "by_tipo": by_tipo,
        "by_actor": by_actor,
        "primer_evento": entries[0].get("timestamp") if entries else None,
        "ultimo_evento": entries[-1].get("timestamp") if entries else None,
    }


def clear_audit_trail() -> int:
    """⚠️ Borra todo el audit trail. SOLO para testing."""
    n = len(_load())
    if AUDIT_PATH.exists():
        AUDIT_PATH.unlink()
    return n
