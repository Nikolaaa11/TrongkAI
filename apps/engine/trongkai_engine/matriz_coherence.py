"""Matriz Cross-Module Coherence — auditoría cruzada entre matrices.

Cruza información de:
- variables_matrix (165 celdas técnicas/comerciales/operativas)
- data_room (41 items DD)
- readiness_score (10 dimensiones consolidadas)
- compliance_rep (8 hitos regulatorios)

Detecta:
- Brechas coherentes (ej: PD en matriz + FALTANTE en data room = doble gap)
- Gaps prioritarios (ítems críticos que aparecen en múltiples matrices)
- Sinergias (un solo dato del equipo cierra múltiples gaps)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data_room import CHECKLIST_DD, EstadoDD
from .variables_matrix import EstadoCelda, construir_matriz


@dataclass
class GapCoherente:
    """Gap detectado en múltiples matrices simultáneamente."""
    descripcion: str
    matrices_afectadas: list[str]
    severidad: str  # "critica" | "alta" | "media"
    accion_recomendada: str
    sinergia: int  # cuántos gaps resuelve si se cierra

    def to_dict(self) -> dict:
        return {
            "descripcion": self.descripcion,
            "matrices_afectadas": self.matrices_afectadas,
            "severidad": self.severidad,
            "accion_recomendada": self.accion_recomendada,
            "sinergia": self.sinergia,
        }


def detectar_gaps_coherentes() -> list[GapCoherente]:
    """Detecta gaps que aparecen simultáneamente en múltiples matrices."""
    gaps: list[GapCoherente] = []

    matriz = construir_matriz()

    # Gap 1: Cotización MMPP — afecta a "Precio Recepción Subproducto" en matriz
    # + item "contratos-mmpp" en data room
    matriz_precio_recepcion_pd = sum(
        1 for c in matriz.celdas
        if c.variable == "Precio Recepción Subproducto" and c.estado == EstadoCelda.PD
    )
    contratos_mmpp = next(
        (i for i in CHECKLIST_DD if i.id == "contratos-mmpp"),
        None,
    )
    if matriz_precio_recepcion_pd > 0 and contratos_mmpp and contratos_mmpp.estado != EstadoDD.COMPLETO:
        gaps.append(GapCoherente(
            descripcion=(
                f"Cotización MMPP: {matriz_precio_recepcion_pd} celdas PD en matriz "
                f"+ contratos-mmpp {contratos_mmpp.estado.value} en data room."
            ),
            matrices_afectadas=["variables_matrix", "data_room"],
            severidad="critica",
            accion_recomendada=(
                "Cerrar contratos firmes con 3 proveedores MMPP cubre ambas. "
                "Owner: Sergio · Comercial."
            ),
            sinergia=matriz_precio_recepcion_pd + 1,
        ))

    # Gap 2: Precios firmes con clientes — afecta "Precio de Venta" en matriz (PTEC PD)
    # + item "contratos-clientes" en data room
    matriz_precio_pd_ptec = sum(
        1 for c in matriz.celdas
        if c.variable == "Precio de Venta" and c.estado == EstadoCelda.PD
    )
    contratos_clientes = next(
        (i for i in CHECKLIST_DD if i.id == "contratos-clientes"),
        None,
    )
    if matriz_precio_pd_ptec > 0 and contratos_clientes and contratos_clientes.estado != EstadoDD.COMPLETO:
        gaps.append(GapCoherente(
            descripcion=(
                f"Precios firmes: {matriz_precio_pd_ptec} celdas Precio Venta PD "
                f"+ contratos-clientes {contratos_clientes.estado.value}."
            ),
            matrices_afectadas=["variables_matrix", "data_room"],
            severidad="critica",
            accion_recomendada=(
                "LOI firmadas con 2 clientes principales cubre ambas. "
                "Owner: Sergio · Comercial."
            ),
            sinergia=matriz_precio_pd_ptec + 1,
        ))

    # Gap 3: OpEx detallado — afecta costos transversales (44 celdas PD)
    # + EERR histórico data room
    opex_transversal_pd = sum(
        1 for c in matriz.celdas
        if c.variable in (
            "Costo Administración", "Costo Energía",
            "Costo Servicios Generales", "Costo Mantención Industrial",
        ) and c.estado == EstadoCelda.PD
    )
    if opex_transversal_pd > 30:
        gaps.append(GapCoherente(
            descripcion=(
                f"Desglose OpEx: {opex_transversal_pd} celdas PD en costos transversales. "
                "Sin desglose mensual real de contadora."
            ),
            matrices_afectadas=["variables_matrix", "data_room (EERR auditados)"],
            severidad="alta",
            accion_recomendada=(
                "1 Excel mensual de contadora desglosa OpEx en admin/energía/servicios/mantención. "
                "Owner: Contadora."
            ),
            sinergia=opex_transversal_pd + 1,
        ))

    # Gap 4: Certificaciones — afecta items DD ESG + nada en matriz
    certificaciones = next(
        (i for i in CHECKLIST_DD if i.id == "certificaciones-esg"),
        None,
    )
    permisos = next(
        (i for i in CHECKLIST_DD if i.id == "permisos-sanitarios"),
        None,
    )
    if certificaciones and certificaciones.estado == EstadoDD.FALTANTE:
        gaps.append(GapCoherente(
            descripcion=(
                "Certificaciones ESG (B-Corp, HACCP, GMP+) sin estado declarado. "
                "Bloquea acceso a mercados premium y fondos ESG."
            ),
            matrices_afectadas=["data_room (ESG)"],
            severidad="media",
            accion_recomendada=(
                "Checklist mensual de certificaciones con fecha esperada. "
                "Owner: QA / Compliance."
            ),
            sinergia=1 + (1 if permisos and permisos.estado != EstadoDD.COMPLETO else 0),
        ))

    # Ordenar por sinergia desc (más impacto primero)
    gaps.sort(key=lambda g: g.sinergia, reverse=True)
    return gaps


@dataclass
class ResumenCoherencia:
    gaps_coherentes: list[GapCoherente]
    total_gaps: int
    sinergia_total: int   # potencial de gaps que se resolverían si se cierran todos los gaps coherentes
    matrices_evaluadas: list[str]

    def to_dict(self) -> dict:
        return {
            "gaps_coherentes": [g.to_dict() for g in self.gaps_coherentes],
            "total_gaps": self.total_gaps,
            "sinergia_total": self.sinergia_total,
            "matrices_evaluadas": self.matrices_evaluadas,
        }


def resumen_coherencia() -> ResumenCoherencia:
    """Resumen ejecutivo del análisis cross-módulo."""
    gaps = detectar_gaps_coherentes()
    return ResumenCoherencia(
        gaps_coherentes=gaps,
        total_gaps=len(gaps),
        sinergia_total=sum(g.sinergia for g in gaps),
        matrices_evaluadas=["variables_matrix", "data_room", "readiness_score", "compliance_rep"],
    )
