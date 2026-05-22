"""Calendario de obligaciones Ley REP Chile + Hoja de Ruta Circular 2040.

Fuentes (WebSearch 2026-05):
- Ley 20.920 (Ley REP) - https://www.bcn.cl/leychile/navegar?idNorma=1090894
- País Circular https://www.paiscircular.cl/economia-circular/avanza-ley-de-residuos-organicos-...
- MMA Reglamento Sanitario - https://mma.gob.cl/gobierno-aprueba-nuevo-reglamento-sanitario-...
- Plan timeline 14 años para residuos orgánicos.
- Reglamento sanitario vigor julio 2026.

Categorías de obligaciones:
- INSTANTANEA: ya en vigor.
- CERCANA: dentro de 12 meses.
- FUTURA: 1-3 años.
- LEJANA: 3+ años.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Severidad(StrEnum):
    CRITICA = "CRITICA"  # multas o cierre operacional
    ALTA = "ALTA"        # impacto costo material
    MEDIA = "MEDIA"
    INFORMATIVA = "INFORMATIVA"


@dataclass
class HitoRegulatorio:
    nombre: str
    fecha_vigor: date
    fuente: str  # URL o referencia legal
    severidad: Severidad
    impacto_trongkai: str
    accion_requerida: str
    costo_estimado_clp: float | None = None  # costo incremental para Trongkai


# Calendario base (actualizar cuando salgan nuevos reglamentos)
HITOS_LEY_REP: list[HitoRegulatorio] = [
    HitoRegulatorio(
        nombre="Ley 20.920 REP vigente",
        fecha_vigor=date(2017, 6, 1),
        fuente="https://www.bcn.cl/leychile/navegar?idNorma=1090894",
        severidad=Severidad.INFORMATIVA,
        impacto_trongkai="Marco general — Trongkai es VALORIZADOR (productor de subproductos), no generador.",
        accion_requerida="Mantener inscripción como gestor autorizado en MMA cuando se formalice.",
    ),
    HitoRegulatorio(
        nombre="Reglamento sanitario para recepción y almacenamiento de residuos productos prioritarios",
        fecha_vigor=date(2026, 7, 14),
        fuente="https://mma.gob.cl/gobierno-aprueba-nuevo-reglamento-sanitario-para-la-gestion-de-residuos-bajo-la-ley-rep/",
        severidad=Severidad.ALTA,
        impacto_trongkai="Recepción de MMPP debe cumplir nuevo estándar sanitario: zonificación, ventilación, contención derrames.",
        accion_requerida="Diseño de planta industrial debe incluir specs reglamento. Auditoría Q3 2026.",
        costo_estimado_clp=80_000_000,  # adecuación de instalaciones
    ),
    HitoRegulatorio(
        nombre="Green Points existentes: 3 años transición sin autorización",
        fecha_vigor=date(2029, 7, 14),
        fuente="Reglamento sanitario MMA 2026-01-14",
        severidad=Severidad.MEDIA,
        impacto_trongkai="Acopios de MMPP de proveedores deben tener autorización formal.",
        accion_requerida="Apoyar a oliveros con trámite o usar Green Points formalizados.",
        costo_estimado_clp=15_000_000,
    ),
    HitoRegulatorio(
        nombre="Ley residuos orgánicos — fase 1 (poda + ferias)",
        fecha_vigor=date(2027, 1, 1),  # estimado, pendiente publicación
        fuente="https://www.paiscircular.cl/economia-circular/avanza-ley-de-residuos-organicos-...",
        severidad=Severidad.MEDIA,
        impacto_trongkai="Mercado de servicios valorización crece. Oportunidad de maquilas adicionales.",
        accion_requerida="Posicionarse como gestor en municipios productores (Valle Central oliva/uva).",
    ),
    HitoRegulatorio(
        nombre="Ley residuos orgánicos — fase 2 (centros comerciales + restaurantes)",
        fecha_vigor=date(2030, 1, 1),  # estimado
        fuente="Plan timeline 14 años MMA",
        severidad=Severidad.MEDIA,
        impacto_trongkai="Más volumen disponible para Trongkai si se posiciona en gestión residuos B2B.",
        accion_requerida="Evaluar pivotar/ampliar Servicios de Plataforma Tecnológica.",
    ),
    HitoRegulatorio(
        nombre="Hoja de Ruta Circular Chile 2040 — meta valorización 65%",
        fecha_vigor=date(2040, 1, 1),
        fuente="Política Nacional Economía Circular MMA",
        severidad=Severidad.INFORMATIVA,
        impacto_trongkai="TAM total Trongkai sigue creciendo con marco regulatorio.",
        accion_requerida="Posicionamiento estratégico — alineado con visión 2040.",
    ),
    HitoRegulatorio(
        nombre="Prohibición quemas agrícolas (PDA)",
        fecha_vigor=date(2026, 1, 1),
        fuente="Plan de Descontaminación Atmosférica Valle Central",
        severidad=Severidad.ALTA,
        impacto_trongkai="MMPP disponible AUMENTA (oliveros no pueden quemar, deben buscar valorización).",
        accion_requerida="Negociar contratos largos con proveedores que pierden la opción quema.",
    ),
    HitoRegulatorio(
        nombre="Norma BRC Global Standard for Food Safety (export)",
        fecha_vigor=date(2027, 6, 1),  # estimado certificación
        fuente="https://www.brcgs.com/",
        severidad=Severidad.ALTA,
        impacto_trongkai="Requisito mínimo para vender a EU + USA. Sin BRC, no hay export Food.",
        accion_requerida="Implementar HACCP + BRC en planta industrial año 2-3.",
        costo_estimado_clp=120_000_000,  # certificación + adecuación
    ),
]


def hitos_por_estado(hoy: date | None = None) -> dict:
    """Categoriza hitos en VIGENTE / CERCANA / FUTURA / LEJANA."""
    hoy = hoy or date.today()
    out: dict[str, list[HitoRegulatorio]] = {
        "VIGENTE": [],
        "CERCANA": [],  # < 12 meses
        "FUTURA": [],   # 1-3 años
        "LEJANA": [],   # >3 años
    }
    for h in HITOS_LEY_REP:
        delta_dias = (h.fecha_vigor - hoy).days
        if delta_dias <= 0:
            out["VIGENTE"].append(h)
        elif delta_dias <= 365:
            out["CERCANA"].append(h)
        elif delta_dias <= 365 * 3:
            out["FUTURA"].append(h)
        else:
            out["LEJANA"].append(h)
    return out


def costo_compliance_total_clp(hoy: date | None = None, ventana_anos: int = 5) -> dict:
    """Suma estimado de costos compliance dentro de la ventana."""
    hoy = hoy or date.today()
    limite = date(hoy.year + ventana_anos, hoy.month, hoy.day)
    detalle = []
    total = 0.0
    for h in HITOS_LEY_REP:
        if hoy <= h.fecha_vigor <= limite and h.costo_estimado_clp:
            total += h.costo_estimado_clp
            detalle.append({
                "nombre": h.nombre,
                "fecha_vigor": h.fecha_vigor.isoformat(),
                "costo_clp": h.costo_estimado_clp,
            })
    return {
        "ventana_anos": ventana_anos,
        "total_clp": total,
        "detalle": detalle,
    }


def proximos_hitos(n: int = 3, hoy: date | None = None) -> list[HitoRegulatorio]:
    """Los próximos N hitos en el calendario (orden cronológico)."""
    hoy = hoy or date.today()
    futuros = [h for h in HITOS_LEY_REP if h.fecha_vigor >= hoy]
    futuros.sort(key=lambda h: h.fecha_vigor)
    return futuros[:n]
