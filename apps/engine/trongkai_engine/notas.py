"""Sistema de Notas - permite asociar comentarios markdown a cualquier entidad.

Entity types:
- celda:Variable|Producto  (ej: "celda:Precio de Venta|HARINA_ALPERUJO")
- decision:id              (ej: "decision:coh-1")
- lp:id                    (ej: "lp:lp-001")
- alerta:id
- hito_rep:nombre
- general:tag

Cada nota tiene:
- id único
- entidad_tipo + entidad_id
- texto (markdown)
- autor + timestamp creación + actualización

Storage: JSON local /tmp/trongkai-notas.json (prod usar Supabase).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

NOTAS_PATH = Path("/tmp/trongkai-notas.json")
MAX_NOTAS = 2000


@dataclass
class Nota:
    id: str
    entidad_tipo: str       # "celda" | "decision" | "lp" | "alerta" | "hito_rep" | "general"
    entidad_id: str         # ej "Precio de Venta|HARINA_ALPERUJO"
    texto: str
    autor: str
    timestamp_creacion: str
    timestamp_actualizacion: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entidad_tipo": self.entidad_tipo,
            "entidad_id": self.entidad_id,
            "texto": self.texto,
            "autor": self.autor,
            "timestamp_creacion": self.timestamp_creacion,
            "timestamp_actualizacion": self.timestamp_actualizacion or self.timestamp_creacion,
            "tags": self.tags,
        }


def _load() -> list[dict]:
    if not NOTAS_PATH.exists():
        return []
    try:
        with NOTAS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(notas: list[dict]) -> None:
    NOTAS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with NOTAS_PATH.open("w", encoding="utf-8") as f:
        json.dump(notas, f, ensure_ascii=False, indent=2, default=str)


def crear_nota(
    entidad_tipo: str,
    entidad_id: str,
    texto: str,
    autor: str = "Nicolás",
    tags: list[str] | None = None,
) -> dict:
    """Crea una nota nueva."""
    notas = _load()
    now = datetime.now(timezone.utc).isoformat()
    nota = Nota(
        id=f"nota-{str(uuid.uuid4())[:8]}",
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        texto=texto,
        autor=autor,
        timestamp_creacion=now,
        timestamp_actualizacion=now,
        tags=tags or [],
    )
    notas.append(nota.to_dict())
    if len(notas) > MAX_NOTAS:
        notas = notas[-MAX_NOTAS:]
    _save(notas)
    return nota.to_dict()


def actualizar_nota(nota_id: str, texto: str | None = None, tags: list[str] | None = None) -> dict | None:
    notas = _load()
    now = datetime.now(timezone.utc).isoformat()
    for n in notas:
        if n["id"] == nota_id:
            if texto is not None:
                n["texto"] = texto
            if tags is not None:
                n["tags"] = tags
            n["timestamp_actualizacion"] = now
            _save(notas)
            return n
    return None


def eliminar_nota(nota_id: str) -> bool:
    notas = _load()
    nuevas = [n for n in notas if n["id"] != nota_id]
    if len(nuevas) < len(notas):
        _save(nuevas)
        return True
    return False


def listar_notas_de(entidad_tipo: str | None = None, entidad_id: str | None = None) -> list[dict]:
    """Lista notas, opcionalmente filtradas por entidad."""
    notas = _load()
    if entidad_tipo:
        notas = [n for n in notas if n.get("entidad_tipo") == entidad_tipo]
    if entidad_id:
        notas = [n for n in notas if n.get("entidad_id") == entidad_id]
    # Más recientes primero
    notas.sort(key=lambda n: n.get("timestamp_actualizacion", ""), reverse=True)
    return notas


def stats_notas() -> dict:
    notas = _load()
    by_tipo: dict[str, int] = {}
    by_autor: dict[str, int] = {}
    for n in notas:
        by_tipo[n.get("entidad_tipo", "?")] = by_tipo.get(n.get("entidad_tipo", "?"), 0) + 1
        by_autor[n.get("autor", "?")] = by_autor.get(n.get("autor", "?"), 0) + 1
    return {
        "total": len(notas),
        "by_tipo": by_tipo,
        "by_autor": by_autor,
    }
