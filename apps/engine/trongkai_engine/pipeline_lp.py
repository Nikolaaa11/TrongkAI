"""Pipeline LP - CRM ligero para tracking de Limited Partners en roadshow.

5 etapas del funnel:
- prospect: identificado, sin contacto aún
- contactado: primer mail/intro mandado
- reunion: agendada o realizada
- dd: en due diligence (recibieron Data Room)
- comprometido: LOI o commitment letter firmada
- ganado: cerrado (cash in)
- perdido: descartó

Cada LP tiene:
- nombre, tipo (fondo / FO / DFI / banco / particular), país
- ticket esperado (USD)
- etapa actual + fecha último contacto
- prob_cierre (0-100)
- próxima acción + owner + fecha
- notas

Storage: JSON local /tmp/trongkai-pipeline-lp.json (en prod usar Supabase).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

PIPELINE_PATH = Path("/tmp/trongkai-pipeline-lp.json")

Etapa = Literal["prospect", "contactado", "reunion", "dd", "comprometido", "ganado", "perdido"]
TipoLP = Literal["fondo", "family_office", "dfi", "banco", "particular", "corporativo"]


@dataclass
class LP:
    id: str
    nombre: str
    tipo: TipoLP
    pais: str
    ticket_esperado_usd: float
    etapa: Etapa
    prob_cierre: float  # 0-100
    proxima_accion: str
    proxima_accion_owner: str
    proxima_accion_fecha: str  # ISO date
    notas: str = ""
    fecha_ultimo_contacto: str = ""
    fecha_creacion: str = ""
    fecha_actualizacion: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "tipo": self.tipo,
            "pais": self.pais,
            "ticket_esperado_usd": self.ticket_esperado_usd,
            "etapa": self.etapa,
            "prob_cierre": self.prob_cierre,
            "ticket_ponderado_usd": round(self.ticket_esperado_usd * self.prob_cierre / 100, 0),
            "proxima_accion": self.proxima_accion,
            "proxima_accion_owner": self.proxima_accion_owner,
            "proxima_accion_fecha": self.proxima_accion_fecha,
            "notas": self.notas,
            "fecha_ultimo_contacto": self.fecha_ultimo_contacto,
            "fecha_creacion": self.fecha_creacion,
            "fecha_actualizacion": self.fecha_actualizacion,
        }


def _load() -> list[dict]:
    if not PIPELINE_PATH.exists():
        # Seed inicial con 5 LPs ejemplo
        return _seed_inicial()
    try:
        with PIPELINE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else _seed_inicial()
    except Exception:
        return _seed_inicial()


def _save(lps: list[dict]) -> None:
    PIPELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PIPELINE_PATH.open("w", encoding="utf-8") as f:
        json.dump(lps, f, ensure_ascii=False, indent=2, default=str)


def _seed_inicial() -> list[dict]:
    """Pipeline ejemplo realista para arrancar."""
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "id": "lp-001", "nombre": "BID Invest", "tipo": "dfi", "pais": "USA",
            "ticket_esperado_usd": 15_000_000, "etapa": "prospect", "prob_cierre": 25,
            "proxima_accion": "Mandar tearsheet inicial + intro call",
            "proxima_accion_owner": "Nicolás", "proxima_accion_fecha": "2026-06-15",
            "notas": "Apto por carbono negativo + DFI ESG. Conecta via Cehta Capital.",
            "fecha_ultimo_contacto": "", "fecha_creacion": now, "fecha_actualizacion": now,
        },
        {
            "id": "lp-002", "nombre": "Proparco", "tipo": "dfi", "pais": "Francia",
            "ticket_esperado_usd": 10_000_000, "etapa": "prospect", "prob_cierre": 20,
            "proxima_accion": "Email cold con LP Pack ZIP",
            "proxima_accion_owner": "Nicolás", "proxima_accion_fecha": "2026-06-20",
            "notas": "DFI francesa, foco SFDR Art 9. Requiere reporte LCA.",
            "fecha_ultimo_contacto": "", "fecha_creacion": now, "fecha_actualizacion": now,
        },
        {
            "id": "lp-003", "nombre": "Family Office X", "tipo": "family_office", "pais": "Chile",
            "ticket_esperado_usd": 3_000_000, "etapa": "contactado", "prob_cierre": 40,
            "proxima_accion": "Reunión presencial Santiago",
            "proxima_accion_owner": "Nicolás", "proxima_accion_fecha": "2026-06-10",
            "notas": "Interesado en agroindustria local. Tiene exposición agro previa.",
            "fecha_ultimo_contacto": "2026-05-28", "fecha_creacion": now, "fecha_actualizacion": now,
        },
        {
            "id": "lp-004", "nombre": "Fondo ESG LATAM", "tipo": "fondo", "pais": "Brasil",
            "ticket_esperado_usd": 8_000_000, "etapa": "reunion", "prob_cierre": 55,
            "proxima_accion": "Mandar Data Room + responder follow-ups DD",
            "proxima_accion_owner": "Nicolás", "proxima_accion_fecha": "2026-06-08",
            "notas": "Avanzado. Pidieron 12 items DD + CVs equipo. Comprometen $8M si pasa DD.",
            "fecha_ultimo_contacto": "2026-05-30", "fecha_creacion": now, "fecha_actualizacion": now,
        },
        {
            "id": "lp-005", "nombre": "Banco BICE", "tipo": "banco", "pais": "Chile",
            "ticket_esperado_usd": 5_000_000, "etapa": "dd", "prob_cierre": 70,
            "proxima_accion": "Sign-off comité de crédito",
            "proxima_accion_owner": "Sergio", "proxima_accion_fecha": "2026-06-05",
            "notas": "DSCR/LLCR aprobados por mesa. Falta comité crédito formal.",
            "fecha_ultimo_contacto": "2026-06-01", "fecha_creacion": now, "fecha_actualizacion": now,
        },
    ]


def list_lps() -> list[dict]:
    return _load()


def upsert_lp(lp_data: dict) -> dict:
    """Crea o actualiza un LP. Si tiene 'id' actualiza; si no, crea."""
    lps = _load()
    now = datetime.now(timezone.utc).isoformat()

    if lp_data.get("id"):
        # Update existente
        for i, lp in enumerate(lps):
            if lp.get("id") == lp_data["id"]:
                lps[i] = {**lp, **lp_data, "fecha_actualizacion": now}
                _save(lps)
                return lps[i]

    # Create nuevo
    new_lp = {
        "id": f"lp-{str(uuid.uuid4())[:8]}",
        "fecha_creacion": now,
        "fecha_actualizacion": now,
        **lp_data,
    }
    # Calcular ticket ponderado
    new_lp["ticket_ponderado_usd"] = round(
        new_lp.get("ticket_esperado_usd", 0) * new_lp.get("prob_cierre", 0) / 100, 0
    )
    lps.append(new_lp)
    _save(lps)
    return new_lp


def delete_lp(lp_id: str) -> bool:
    lps = _load()
    nueva = [lp for lp in lps if lp.get("id") != lp_id]
    if len(nueva) < len(lps):
        _save(nueva)
        return True
    return False


@dataclass
class ResumenPipeline:
    total_lps: int
    por_etapa: dict[str, int]
    ticket_pipeline_usd: float    # Suma ticket esperado
    ticket_ponderado_usd: float    # Suma ticket × prob cierre
    objetivo_usd: float            # Hardcoded $40M para round Trongkai
    pct_objetivo_pipeline: float
    pct_objetivo_ponderado: float
    proximas_acciones_7d: int

    def to_dict(self) -> dict:
        return {
            "total_lps": self.total_lps,
            "por_etapa": self.por_etapa,
            "ticket_pipeline_usd": self.ticket_pipeline_usd,
            "ticket_ponderado_usd": self.ticket_ponderado_usd,
            "objetivo_usd": self.objetivo_usd,
            "pct_objetivo_pipeline": self.pct_objetivo_pipeline,
            "pct_objetivo_ponderado": self.pct_objetivo_ponderado,
            "proximas_acciones_7d": self.proximas_acciones_7d,
        }


def resumen_pipeline() -> ResumenPipeline:
    """Stats agregadas del pipeline."""
    from datetime import date, timedelta
    lps = _load()
    activos = [lp for lp in lps if lp.get("etapa") not in ("perdido",)]

    por_etapa: dict[str, int] = {}
    for lp in activos:
        etapa = lp.get("etapa", "prospect")
        por_etapa[etapa] = por_etapa.get(etapa, 0) + 1

    ticket_total = sum(lp.get("ticket_esperado_usd", 0) for lp in activos)
    ticket_pond = sum(
        lp.get("ticket_esperado_usd", 0) * lp.get("prob_cierre", 0) / 100
        for lp in activos
    )

    OBJETIVO = 40_000_000  # $40M round target

    hoy = date.today()
    en_7d = (hoy + timedelta(days=7)).isoformat()
    proximas_7d = sum(
        1 for lp in activos
        if lp.get("proxima_accion_fecha", "9999") <= en_7d
    )

    return ResumenPipeline(
        total_lps=len(activos),
        por_etapa=por_etapa,
        ticket_pipeline_usd=ticket_total,
        ticket_ponderado_usd=ticket_pond,
        objetivo_usd=OBJETIVO,
        pct_objetivo_pipeline=round(ticket_total / OBJETIVO * 100, 1) if OBJETIVO else 0,
        pct_objetivo_ponderado=round(ticket_pond / OBJETIVO * 100, 1) if OBJETIVO else 0,
        proximas_acciones_7d=proximas_7d,
    )
