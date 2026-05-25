"""Decision Engine — el cerebro central que une todas las matrices.

Toma TODO el contexto del modelo (variables matrix, data room, coherencia,
sensitivity, breakeven, readiness, compliance, climate, financing) y produce
recomendaciones priorizadas para tomar decisiones.

Output principal: top_5_acciones() — las 5 acciones que más mueven la aguja.

Scoring por acción:
  prioridad = impacto_tir × 0.30
            + sinergia × 0.25
            + uplift_readiness × 0.20
            + quick_win × 0.15
            + urgencia × 0.10

Cada componente normalizado a 0-100.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .breakeven import breakeven_summary
from .data_room import CHECKLIST_DD, EstadoDD, resumen_checklist
from .matriz_coherence import detectar_gaps_coherentes
from .variables_intelligence import simular_cambio_celda
from .variables_matrix import EstadoCelda, construir_matriz

Categoria = Literal["comercial", "financiero", "operacional", "compliance", "esg", "equipo"]


@dataclass
class AccionRecomendada:
    """Acción concreta priorizada por el motor de decisiones."""
    id: str
    titulo: str
    descripcion: str
    categoria: Categoria
    owner: str

    # Scoring (0-100 cada uno)
    impacto_tir: float       # Cuánto sube TIR si se cierra (estimado pp × 10)
    sinergia: float          # Cuántos gaps cross-matriz cierra
    uplift_readiness: float  # Cuántos puntos sube readiness (estimado)
    quick_win: float         # 100 = puede cerrarse en días; 0 = meses
    urgencia: float          # 100 = bloqueante; 0 = nice-to-have

    # Calculados
    prioridad: float = 0.0
    matrices_impactadas: list[str] = field(default_factory=list)
    accion_concreta: str = ""

    def calcular_prioridad(self) -> float:
        self.prioridad = (
            self.impacto_tir * 0.30
            + self.sinergia * 0.25
            + self.uplift_readiness * 0.20
            + self.quick_win * 0.15
            + self.urgencia * 0.10
        )
        return self.prioridad

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "categoria": self.categoria,
            "owner": self.owner,
            "impacto_tir": round(self.impacto_tir, 1),
            "sinergia": round(self.sinergia, 1),
            "uplift_readiness": round(self.uplift_readiness, 1),
            "quick_win": round(self.quick_win, 1),
            "urgencia": round(self.urgencia, 1),
            "prioridad": round(self.prioridad, 1),
            "matrices_impactadas": self.matrices_impactadas,
            "accion_concreta": self.accion_concreta,
        }


# ============================================================================
# Generación de acciones desde la red de matrices
# ============================================================================

def _impacto_tir_de_precio(producto: str, nuevo_precio: float, precio_actual: float) -> float:
    """Estima impacto TIR (0-100 scale) de cambiar precio de un SKU."""
    try:
        imp = simular_cambio_celda("Precio de Venta", producto, nuevo_precio)
        if imp.delta_tir_pp is None:
            return 0
        # Normalizar: 1pp = 50, 2pp = 100
        return min(100, abs(imp.delta_tir_pp) * 50)
    except Exception:
        return 0


def generar_acciones_desde_coherencia() -> list[AccionRecomendada]:
    """Cada gap cross-matriz genera 1 acción recomendada."""
    gaps = detectar_gaps_coherentes()
    acciones: list[AccionRecomendada] = []

    severidad_to_urgencia = {"critica": 100, "alta": 75, "media": 50, "baja": 25}

    for i, g in enumerate(gaps, 1):
        # Mapear acción
        if "MMPP" in g.descripcion or "cotización" in g.descripcion.lower():
            accion = AccionRecomendada(
                id=f"coh-{i}",
                titulo="Cotización firme MMPP de 3 proveedores",
                descripcion=g.descripcion,
                categoria="comercial",
                owner="Sergio · Comercial",
                impacto_tir=70,    # Costo MMPP es driver sensible
                sinergia=min(100, g.sinergia * 5),
                uplift_readiness=8,
                quick_win=60,      # 2-3 semanas
                urgencia=severidad_to_urgencia.get(g.severidad, 50),
                matrices_impactadas=g.matrices_afectadas,
                accion_concreta="Pedir cotización formal a 3 proveedores top (oliveros + tomatera + vinícolas) con condiciones 2026-2027",
            )
        elif "LOI" in g.descripcion or "clientes" in g.descripcion.lower() or "Precios firmes" in g.descripcion:
            accion = AccionRecomendada(
                id=f"coh-{i}",
                titulo="LOI firmadas con 2 clientes principales",
                descripcion=g.descripcion,
                categoria="comercial",
                owner="Sergio · Comercial",
                impacto_tir=85,
                sinergia=min(100, g.sinergia * 5),
                uplift_readiness=10,
                quick_win=40,      # 1-2 meses
                urgencia=severidad_to_urgencia.get(g.severidad, 50),
                matrices_impactadas=g.matrices_afectadas,
                accion_concreta="Cerrar reuniones con 2 clientes target (1 Feed + 1 Food) y obtener LOI firmadas con volumen y precio referencial",
            )
        elif "OpEx" in g.descripcion:
            accion = AccionRecomendada(
                id=f"coh-{i}",
                titulo="Desglose OpEx mensual real",
                descripcion=g.descripcion,
                categoria="financiero",
                owner="Contadora · Finanzas",
                impacto_tir=40,
                sinergia=min(100, g.sinergia * 2),  # 44 celdas → 88
                uplift_readiness=6,
                quick_win=90,      # 1-2 días pedirlo
                urgencia=severidad_to_urgencia.get(g.severidad, 50),
                matrices_impactadas=g.matrices_afectadas,
                accion_concreta="Pedir a contadora 1 Excel con OpEx mensual de los últimos 3 meses desglosado: MO + mantención + energía + admin + seguros",
            )
        elif "Certificaciones" in g.descripcion:
            accion = AccionRecomendada(
                id=f"coh-{i}",
                titulo="Roadmap de certificaciones ESG",
                descripcion=g.descripcion,
                categoria="esg",
                owner="QA / Compliance",
                impacto_tir=25,    # Indirecto, abre mercados premium
                sinergia=min(100, g.sinergia * 10),
                uplift_readiness=4,
                quick_win=70,
                urgencia=severidad_to_urgencia.get(g.severidad, 50),
                matrices_impactadas=g.matrices_afectadas,
                accion_concreta="Definir checklist con estado actual (no iniciado / en proceso / pendiente auditoría) de B-Corp, HACCP, GMP+ y fechas esperadas",
            )
        else:
            continue
        acciones.append(accion)

    return acciones


def generar_acciones_desde_breakeven() -> list[AccionRecomendada]:
    """Si algún driver tiene colchón muy bajo, recomendar cobertura."""
    acciones: list[AccionRecomendada] = []
    try:
        be = breakeven_summary(umbral_tir=0.15).to_dict()
    except Exception:
        return acciones

    for r in be.get("resultados", []):
        if r["colchon_pct"] is None or r["shock_breakeven"] is None:
            continue
        colchon = r["colchon_pct"]
        driver = r["driver"]

        # Si colchón < 20% para precio o costo, alertar
        if driver == "precio" and colchon < 0.20:
            acciones.append(AccionRecomendada(
                id="be-precio",
                titulo="Cobertura de precios SKU críticos",
                descripcion=f"El precio soporta solo -{colchon*100:.0f}% antes de bajar del hurdle 15%.",
                categoria="comercial",
                owner="Sergio · Comercial + asesor",
                impacto_tir=60,
                sinergia=30,
                uplift_readiness=5,
                quick_win=40,
                urgencia=80 if colchon < 0.15 else 60,
                matrices_impactadas=["breakeven", "sensitivity"],
                accion_concreta="Negociar contratos forward o take-or-pay con descuento por volumen para asegurar precio base 3-5 años",
            ))

    return acciones


def generar_acciones_desde_data_room() -> list[AccionRecomendada]:
    """Items DD must-have faltantes generan acciones."""
    acciones: list[AccionRecomendada] = []
    r = resumen_checklist()

    # Items FALTANTES must-have de alta visibilidad
    faltantes_mh = [
        i for i in CHECKLIST_DD
        if i.estado == EstadoDD.FALTANTE and i.must_have
    ]

    # Solo agrego una acción consolidada para no saturar
    if len(faltantes_mh) >= 3:
        items_top = sorted(faltantes_mh, key=lambda x: x.categoria.value)[:5]
        acciones.append(AccionRecomendada(
            id="dr-faltantes",
            titulo=f"Cerrar {len(faltantes_mh)} items DD must-have faltantes",
            descripcion=f"{len(faltantes_mh)} items must-have aún faltantes en data room. Bloqueante para LP serio.",
            categoria="comercial",
            owner="Nicolás · IR",
            impacto_tir=30,
            sinergia=min(100, len(faltantes_mh) * 8),
            uplift_readiness=7,
            quick_win=30,    # Toma tiempo recopilar todo
            urgencia=70,
            matrices_impactadas=["data_room", "readiness"],
            accion_concreta=(
                f"Top items pendientes: {', '.join(i.titulo for i in items_top[:3])}... "
                f"Asignar 1 owner por item y agenda semanal de follow-up."
            ),
        ))

    return acciones


def generar_acciones_desde_matriz() -> list[AccionRecomendada]:
    """Cobertura de matriz < 50% en algún grupo → acción de calibración."""
    matriz = construir_matriz()
    by_grupo: dict[str, list] = {}
    for c in matriz.celdas:
        from .variables_matrix import PRODUCTOS
        prod = next((p for p in PRODUCTOS if p.codigo == c.producto), None)
        if prod:
            by_grupo.setdefault(prod.grupo, []).append(c)

    acciones: list[AccionRecomendada] = []
    for grupo, celdas in by_grupo.items():
        pd = sum(1 for c in celdas if c.estado == EstadoCelda.PD)
        total = len(celdas)
        pct_pd = pd / total

        # Grupo PTEC suele tener muchas PD — acción específica
        if grupo == "Productos PTEC" and pct_pd > 0.5:
            acciones.append(AccionRecomendada(
                id="mat-ptec",
                titulo="Validación piloto Productos PTEC",
                descripcion=f"{pd}/{total} celdas PTEC en PD ({pct_pd*100:.0f}%). Productos nuevos sin datos reales.",
                categoria="operacional",
                owner="Jaime · CTO",
                impacto_tir=50,
                sinergia=min(100, pd * 3),
                uplift_readiness=8,
                quick_win=20,   # Requiere proceso piloto
                urgencia=60,
                matrices_impactadas=["variables_matrix"],
                accion_concreta="Lanzar piloto de 1 mes con 100 kg de cada PTEC (Proteína Unicel, Antioxidante, Aglomerante, Umami) para validar rendimiento y costo real",
            ))

    return acciones


# ============================================================================
# Orquestador principal
# ============================================================================

def top_5_acciones() -> list[AccionRecomendada]:
    """Compila TODAS las fuentes de acciones, calcula prioridad y devuelve top 5."""
    acciones = []
    acciones.extend(generar_acciones_desde_coherencia())
    acciones.extend(generar_acciones_desde_breakeven())
    acciones.extend(generar_acciones_desde_data_room())
    acciones.extend(generar_acciones_desde_matriz())

    # Calcular prioridad
    for a in acciones:
        a.calcular_prioridad()

    # Ordenar
    acciones.sort(key=lambda a: a.prioridad, reverse=True)
    return acciones[:5]


def todas_las_acciones() -> list[AccionRecomendada]:
    """Devuelve TODAS las acciones detectadas (sin limit)."""
    acciones = []
    acciones.extend(generar_acciones_desde_coherencia())
    acciones.extend(generar_acciones_desde_breakeven())
    acciones.extend(generar_acciones_desde_data_room())
    acciones.extend(generar_acciones_desde_matriz())

    for a in acciones:
        a.calcular_prioridad()
    acciones.sort(key=lambda a: a.prioridad, reverse=True)
    return acciones


@dataclass
class ResumenDecisiones:
    top_5: list[AccionRecomendada]
    todas: list[AccionRecomendada]
    impacto_potencial_tir_pp: float    # Suma de impactos si todo se hace
    uplift_potencial_readiness: float
    quick_wins: list[AccionRecomendada]   # quick_win > 70

    def to_dict(self) -> dict:
        return {
            "top_5": [a.to_dict() for a in self.top_5],
            "todas": [a.to_dict() for a in self.todas],
            "total_acciones": len(self.todas),
            "impacto_potencial_tir_pp": round(self.impacto_potencial_tir_pp, 1),
            "uplift_potencial_readiness": round(self.uplift_potencial_readiness, 1),
            "quick_wins": [a.to_dict() for a in self.quick_wins],
        }


def resumen_decisiones() -> ResumenDecisiones:
    """Resumen completo del motor de decisiones."""
    todas = todas_las_acciones()
    top = todas[:5]

    impacto_tir_total = sum(a.impacto_tir for a in todas) / 50  # Reescalar a pp aprox
    uplift_total = sum(a.uplift_readiness for a in todas)
    quick_wins = sorted([a for a in todas if a.quick_win > 70], key=lambda a: a.prioridad, reverse=True)

    return ResumenDecisiones(
        top_5=top,
        todas=todas,
        impacto_potencial_tir_pp=impacto_tir_total,
        uplift_potencial_readiness=uplift_total,
        quick_wins=quick_wins[:3],
    )
