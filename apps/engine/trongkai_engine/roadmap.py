"""Roadmap Visual - timeline consolidado de próximos hitos.

Agrupa por mes en los próximos 12 meses:
- Hitos REP (compliance)
- LP pipeline next actions
- Decisiones top 5 (estimadas por quick_win + urgencia)
- Certificaciones esperadas

Cada item: fecha, tipo, titulo, owner, prioridad.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any


@dataclass
class HitoRoadmap:
    fecha: str  # YYYY-MM-DD
    tipo: str   # compliance | lp | decision | certificacion | financiero
    titulo: str
    descripcion: str
    owner: str
    prioridad: str  # alta | media | baja
    monto_estimado_usd: float | None = None
    link: str = ""

    def to_dict(self) -> dict:
        return {
            "fecha": self.fecha,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "owner": self.owner,
            "prioridad": self.prioridad,
            "monto_estimado_usd": self.monto_estimado_usd,
            "link": self.link,
        }


def construir_roadmap(meses_adelante: int = 12) -> dict[str, Any]:
    """Construye el roadmap consolidado para los próximos N meses."""
    hoy = date.today()
    limite = hoy + timedelta(days=meses_adelante * 30)
    hitos: list[HitoRoadmap] = []

    # 1. Hitos REP
    try:
        from .compliance_rep import HITOS_LEY_REP
        for h in HITOS_LEY_REP:
            if hoy <= h.fecha_vigor <= limite:
                hitos.append(HitoRoadmap(
                    fecha=h.fecha_vigor.isoformat(),
                    tipo="compliance",
                    titulo=h.nombre[:80],
                    descripcion=h.accion_requerida[:120],
                    owner="Compliance / Legal",
                    prioridad="alta" if h.severidad.value in ("CRITICA", "ALTA") else "media",
                    link="/compliance",
                ))
    except Exception:
        pass

    # 2. LP pipeline próximas acciones
    try:
        from .pipeline_lp import list_lps
        for lp in list_lps():
            fecha_str = lp.get("proxima_accion_fecha", "")
            if not fecha_str:
                continue
            try:
                f = date.fromisoformat(fecha_str)
                if hoy <= f <= limite:
                    hitos.append(HitoRoadmap(
                        fecha=fecha_str,
                        tipo="lp",
                        titulo=f"{lp['nombre']}: {lp.get('proxima_accion', '')[:60]}",
                        descripcion=f"Etapa {lp.get('etapa', '?')} · ticket ${lp.get('ticket_esperado_usd', 0)/1e6:.1f}M",
                        owner=lp.get("proxima_accion_owner", "?"),
                        prioridad="alta" if lp.get("prob_cierre", 0) >= 60 else "media",
                        monto_estimado_usd=lp.get("ticket_esperado_usd", 0) * lp.get("prob_cierre", 0) / 100,
                        link="/pipeline-lp",
                    ))
            except ValueError:
                pass
    except Exception:
        pass

    # 3. Decisiones top 5 estimadas por quick_win
    try:
        from .decision_engine import top_5_acciones
        for acc in top_5_acciones():
            # Estimar fecha: días = max(7, 90 - quick_win)
            dias_estimados = int(max(7, 90 - acc.quick_win))
            fecha_est = (hoy + timedelta(days=dias_estimados)).isoformat()
            prio = "alta" if acc.urgencia >= 70 else ("media" if acc.urgencia >= 40 else "baja")
            hitos.append(HitoRoadmap(
                fecha=fecha_est,
                tipo="decision",
                titulo=acc.titulo[:80],
                descripcion=acc.accion_concreta[:120],
                owner=acc.owner,
                prioridad=prio,
                link="/decisiones",
            ))
    except Exception:
        pass

    # 4. Certificaciones esperadas (placeholder hardcoded)
    certificaciones = [
        ("B-Corp certificación", "QA / Compliance", 180, "alta"),
        ("HACCP certificación planta", "QA", 120, "alta"),
        ("GMP+ feed certificación", "QA", 240, "media"),
    ]
    for nombre, owner, dias, prio in certificaciones:
        fecha_est = (hoy + timedelta(days=dias)).isoformat()
        if hoy <= date.fromisoformat(fecha_est) <= limite:
            hitos.append(HitoRoadmap(
                fecha=fecha_est,
                tipo="certificacion",
                titulo=nombre,
                descripcion=f"Auditoría + emisión certificación. Owner: {owner}",
                owner=owner,
                prioridad=prio,
                link="/data-room",
            ))

    # Ordenar cronológicamente
    hitos.sort(key=lambda h: h.fecha)

    # Agrupar por mes
    por_mes: dict[str, list[dict]] = {}
    for h in hitos:
        mes = h.fecha[:7]  # YYYY-MM
        por_mes.setdefault(mes, []).append(h.to_dict())

    # Stats
    total = len(hitos)
    por_tipo: dict[str, int] = {}
    monto_ponderado_total = 0.0
    for h in hitos:
        por_tipo[h.tipo] = por_tipo.get(h.tipo, 0) + 1
        if h.monto_estimado_usd:
            monto_ponderado_total += h.monto_estimado_usd

    return {
        "hoy": hoy.isoformat(),
        "horizonte_meses": meses_adelante,
        "total_hitos": total,
        "por_tipo": por_tipo,
        "por_mes": por_mes,
        "monto_lp_ponderado_total_usd": round(monto_ponderado_total, 0),
        "hitos": [h.to_dict() for h in hitos],
    }
