"""Balance de RRHH con alarmas de horas extras CT Chile.

ALARMAS CRITICAS (no negociables, regulatorias):
- Sem regulares  > 45h        -> alarma alta  (excede contrato)
- Sem totales    > 57h        -> CRITICA      (45 + 12 extras max legal Chile)
- Mes extras     > 32h        -> CRITICA      (Art. 31 CT)

Referencias legales:
- Codigo del Trabajo Art. 22: 45h/sem (40h vigente progresivo desde 2028)
- Codigo del Trabajo Art. 31: maximo 12h extras/sem, ~32h/mes
- Multas DT 2024: 5-20 UTM por trabajador en exceso

Seed: 15 trabajadores piloto Parral (operarios + supervisores + QA + mant + admin).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Literal

from ..storage import data_path

Turno = Literal["mañana", "tarde", "noche", "rotativo"]
Categoria = Literal["operario", "supervisor", "calidad", "mantenimiento", "admin"]

# Limites legales Chile (CT 2024)
HORAS_CONTRATO_DEFAULT = 45.0
HORAS_EXTRAS_MAX_SEM = 12.0
HORAS_EXTRAS_MAX_MES = 32.0
HORAS_TOTAL_MAX_SEM = HORAS_CONTRATO_DEFAULT + HORAS_EXTRAS_MAX_SEM   # 57h

# Productividad benchmark agroindustria Chile (kg/hh)
PRODUCTIVIDAD_BENCHMARK_KG_HH = 25.0
# Rotacion benchmark sectorial
ROTACION_BENCHMARK = 0.20


@dataclass
class Trabajador:
    id: str
    nombre: str
    categoria: Categoria
    turno: Turno
    horas_contrato_semanal: float = HORAS_CONTRATO_DEFAULT
    horas_max_legales_sem: float = HORAS_TOTAL_MAX_SEM
    sueldo_base_clp: float = 600_000.0
    horas_extra_max_mensual: float = HORAS_EXTRAS_MAX_MES
    activo: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AsignacionHoras:
    trabajador_id: str
    semana_iso: str                  # "2026-W23"
    horas_regulares: float
    horas_extras: float = 0.0
    tareas: list[str] = field(default_factory=list)
    equipo_asignado: str = ""

    @property
    def horas_totales(self) -> float:
        return self.horas_regulares + self.horas_extras

    def to_dict(self) -> dict:
        d = asdict(self)
        d["horas_totales"] = self.horas_totales
        return d


@dataclass
class BalanceRRHH:
    trabajadores: list[Trabajador]
    asignaciones_semana_actual: list[AsignacionHoras]
    semana_referencia: str
    total_horas_disponibles_sem: float
    total_horas_asignadas_sem: float
    utilizacion_pct: float
    costo_total_mensual_clp: float
    costo_horas_extra_mensual_clp: float
    productividad_kg_por_hh: float
    closure_pct: float
    rotacion_anual_pct: float
    alarmas: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "trabajadores": [t.to_dict() for t in self.trabajadores],
            "asignaciones_semana_actual": [a.to_dict() for a in self.asignaciones_semana_actual],
            "semana_referencia": self.semana_referencia,
            "total_horas_disponibles_sem": round(self.total_horas_disponibles_sem, 2),
            "total_horas_asignadas_sem": round(self.total_horas_asignadas_sem, 2),
            "utilizacion_pct": round(self.utilizacion_pct, 4),
            "costo_total_mensual_clp": round(self.costo_total_mensual_clp, 0),
            "costo_horas_extra_mensual_clp": round(self.costo_horas_extra_mensual_clp, 0),
            "productividad_kg_por_hh": round(self.productividad_kg_por_hh, 2),
            "closure_pct": round(self.closure_pct, 4),
            "rotacion_anual_pct": round(self.rotacion_anual_pct, 4),
            "alarmas": self.alarmas,
        }


def trabajadores_seed() -> list[Trabajador]:
    """15 trabajadores piloto industrial Parral."""
    return [
        Trabajador("OP-001", "Juan Pérez", "operario", "mañana", sueldo_base_clp=580_000),
        Trabajador("OP-002", "María Soto", "operario", "tarde", sueldo_base_clp=580_000),
        Trabajador("OP-003", "Pedro González", "operario", "noche", sueldo_base_clp=620_000),
        Trabajador("OP-004", "Ana Rojas", "operario", "mañana", sueldo_base_clp=580_000),
        Trabajador("OP-005", "Luis Fernández", "operario", "rotativo", sueldo_base_clp=600_000),
        Trabajador("SUP-001", "Carlos Muñoz", "supervisor", "mañana", sueldo_base_clp=950_000),
        Trabajador("SUP-002", "Rosa Toledo", "supervisor", "tarde", sueldo_base_clp=950_000),
        Trabajador("QA-001", "José Lillo", "calidad", "mañana", sueldo_base_clp=780_000),
        Trabajador("QA-002", "Carmen Vidal", "calidad", "tarde", sueldo_base_clp=780_000),
        Trabajador("QA-003", "Felipe Cortés", "calidad", "noche", sueldo_base_clp=820_000),
        Trabajador("MNT-001", "Diego Soto", "mantenimiento", "mañana", sueldo_base_clp=720_000),
        Trabajador("MNT-002", "Patricio Reyes", "mantenimiento", "tarde", sueldo_base_clp=720_000),
        Trabajador("ADM-001", "Verónica Pino", "admin", "mañana", sueldo_base_clp=850_000),
        Trabajador("ADM-002", "Manuel Espinoza", "admin", "mañana", sueldo_base_clp=850_000),
        Trabajador("ADM-003", "Andrea Vega", "admin", "mañana", sueldo_base_clp=850_000),
    ]


def asignaciones_seed(semana: str = "2026-W23") -> list[AsignacionHoras]:
    """Asignaciones tipicas: la mayoria a 45h, algunos con extras menores."""
    return [
        AsignacionHoras("OP-001", semana, 45.0, 4.0, ["Operacion PEF"], "PEF Opticept"),
        AsignacionHoras("OP-002", semana, 45.0, 0.0, ["Operacion PEF"], "PEF Opticept"),
        AsignacionHoras("OP-003", semana, 45.0, 0.0, ["Operacion PEF"], "PEF Opticept"),
        AsignacionHoras("OP-004", semana, 45.0, 6.0, ["Micromolienda"], "Micromolienda"),
        AsignacionHoras("OP-005", semana, 40.0, 0.0, ["Apoyo rotativo"], "Variable"),
        AsignacionHoras("SUP-001", semana, 45.0, 2.0, ["Supervision turno"], "Planta"),
        AsignacionHoras("SUP-002", semana, 45.0, 0.0, ["Supervision turno"], "Planta"),
        AsignacionHoras("QA-001", semana, 45.0, 0.0, ["Muestreo + LIMS"], "Laboratorio"),
        AsignacionHoras("QA-002", semana, 45.0, 0.0, ["Muestreo + LIMS"], "Laboratorio"),
        AsignacionHoras("QA-003", semana, 45.0, 0.0, ["Muestreo turno noche"], "Laboratorio"),
        AsignacionHoras("MNT-001", semana, 45.0, 8.0, ["Mantenimiento PEF"], "PEF Opticept"),
        AsignacionHoras("MNT-002", semana, 45.0, 0.0, ["Mantenimiento general"], "Planta"),
        AsignacionHoras("ADM-001", semana, 45.0, 0.0, ["Finanzas + compras"], "Oficina"),
        AsignacionHoras("ADM-002", semana, 45.0, 0.0, ["RRHH"], "Oficina"),
        AsignacionHoras("ADM-003", semana, 40.0, 0.0, ["Comercial"], "Oficina"),
    ]


def detectar_alarmas(
    asignaciones: list[AsignacionHoras],
    trabajadores: list[Trabajador],
    asignaciones_mes_previo: list[AsignacionHoras] | None = None,
) -> list[dict]:
    """Detecta las 3 alarmas criticas + 1 acumulada mensual.

    Args:
        asignaciones: semana actual.
        trabajadores: catalogo activo.
        asignaciones_mes_previo: TODAS las asignaciones del mes (4 semanas)
            para validar Art. 31 CT. Si None, solo valida la semana actual.
    """
    alarmas: list[dict] = []
    by_id = {t.id: t for t in trabajadores}

    for a in asignaciones:
        t = by_id.get(a.trabajador_id)
        if t is None or not t.activo:
            continue
        total = a.horas_totales

        # ALARMA 1: regulares > contrato
        if a.horas_regulares > t.horas_contrato_semanal:
            alarmas.append({
                "tipo": "exceso_contrato",
                "severidad": "alta",
                "trabajador_id": t.id,
                "trabajador": t.nombre,
                "semana": a.semana_iso,
                "horas_asignadas": a.horas_regulares,
                "horas_contrato": t.horas_contrato_semanal,
                "exceso": a.horas_regulares - t.horas_contrato_semanal,
                "mensaje": (
                    f"⚠️ {t.nombre}: {a.horas_regulares}h regulares vs "
                    f"{t.horas_contrato_semanal}h contrato."
                ),
                "accion": "Reducir asignacion semanal o renegociar contrato.",
            })

        # ALARMA 2: totales > 57h legal Chile
        if total > t.horas_max_legales_sem:
            alarmas.append({
                "tipo": "exceso_legal",
                "severidad": "critica",
                "trabajador_id": t.id,
                "trabajador": t.nombre,
                "semana": a.semana_iso,
                "total_horas": total,
                "limite_legal": t.horas_max_legales_sem,
                "exceso": total - t.horas_max_legales_sem,
                "mensaje": (
                    f"🚨 {t.nombre}: {total}h totales esta semana > "
                    f"{t.horas_max_legales_sem}h limite CT Chile."
                ),
                "accion": "DETENER asignacion. Riesgo multa DT 5-20 UTM por trabajador.",
            })

        # ALARMA 3: extras semanales > 12h
        if a.horas_extras > HORAS_EXTRAS_MAX_SEM:
            alarmas.append({
                "tipo": "extras_semanal_excedido",
                "severidad": "critica",
                "trabajador_id": t.id,
                "trabajador": t.nombre,
                "semana": a.semana_iso,
                "extras_asignadas": a.horas_extras,
                "limite": HORAS_EXTRAS_MAX_SEM,
                "mensaje": (
                    f"🚨 {t.nombre}: {a.horas_extras}h extras semanal > "
                    f"{HORAS_EXTRAS_MAX_SEM}h limite Art. 31 CT."
                ),
            })

    # ALARMA 4: acumulada mensual > 32h extras
    if asignaciones_mes_previo:
        extras_por_trab: dict[str, float] = {}
        for a in asignaciones_mes_previo:
            extras_por_trab[a.trabajador_id] = (
                extras_por_trab.get(a.trabajador_id, 0.0) + a.horas_extras
            )
        for trab_id, total_extras in extras_por_trab.items():
            t = by_id.get(trab_id)
            if t is None:
                continue
            if total_extras > t.horas_extra_max_mensual:
                alarmas.append({
                    "tipo": "extras_mensual_excedido",
                    "severidad": "critica",
                    "trabajador_id": t.id,
                    "trabajador": t.nombre,
                    "extras_mes": total_extras,
                    "limite_mensual": t.horas_extra_max_mensual,
                    "mensaje": (
                        f"🚨 {t.nombre}: {total_extras}h extras acumuladas en el mes > "
                        f"{t.horas_extra_max_mensual}h limite Art. 31 CT."
                    ),
                    "accion": "Bloquear nuevas extras hasta proximo mes calendario.",
                })

    return alarmas


def _costo_mensual_clp(
    asignaciones: list[AsignacionHoras],
    trabajadores: list[Trabajador],
) -> tuple[float, float]:
    """(costo_total_mensual, costo_extras_mensual) en CLP.

    Asume:
    - 4 semanas/mes
    - Hora extra: 1.5x base
    """
    by_id = {t.id: t for t in trabajadores}
    total = 0.0
    extras_total = 0.0
    SEMANAS_MES = 4.345  # 52/12

    # Sueldo base mensual de TODOS los trabajadores activos
    for t in trabajadores:
        if t.activo:
            total += t.sueldo_base_clp

    # Extras: se calculan sobre asignaciones semanales del catalogo
    for a in asignaciones:
        t = by_id.get(a.trabajador_id)
        if t is None or not t.activo:
            continue
        # tarifa hora base = sueldo / (45 * 4.345)
        tarifa_hora = t.sueldo_base_clp / (t.horas_contrato_semanal * SEMANAS_MES)
        # Extras de la semana * 1.5 * 4.345 sem/mes (asumimos patron semanal estable)
        costo_extra = a.horas_extras * tarifa_hora * 1.5 * SEMANAS_MES
        extras_total += costo_extra

    total += extras_total
    return total, extras_total


def computar_balance_rrhh(
    trabajadores: list[Trabajador] | None = None,
    asignaciones: list[AsignacionHoras] | None = None,
    semana: str = "2026-W23",
    produccion_semanal_kg: float = 16_350.0,  # ~850t/año / 52
    asignaciones_mes_previo: list[AsignacionHoras] | None = None,
    rotacion_anual: float = 0.18,
) -> BalanceRRHH:
    """Compone el balance + dispara alarmas."""
    if trabajadores is None:
        trabajadores = trabajadores_seed()
    if asignaciones is None:
        asignaciones = asignaciones_seed(semana)

    activos = [t for t in trabajadores if t.activo]
    total_disponibles = sum(t.horas_contrato_semanal for t in activos)
    total_asignadas = sum(a.horas_totales for a in asignaciones)
    utilizacion = total_asignadas / total_disponibles if total_disponibles > 0 else 0.0

    total_hh_semana = sum(a.horas_totales for a in asignaciones)
    productividad = (
        produccion_semanal_kg / total_hh_semana
        if total_hh_semana > 0 else 0.0
    )

    costo_total, costo_extras = _costo_mensual_clp(asignaciones, trabajadores)

    # Closure: suma asignaciones por trabajador ≈ total reportado (sanity)
    suma = sum(a.horas_totales for a in asignaciones)
    closure_pct = abs(suma - total_asignadas) / max(total_asignadas, 1e-6) * 100.0

    alarmas = detectar_alarmas(asignaciones, trabajadores, asignaciones_mes_previo)

    return BalanceRRHH(
        trabajadores=trabajadores,
        asignaciones_semana_actual=asignaciones,
        semana_referencia=semana,
        total_horas_disponibles_sem=total_disponibles,
        total_horas_asignadas_sem=total_asignadas,
        utilizacion_pct=utilizacion,
        costo_total_mensual_clp=costo_total,
        costo_horas_extra_mensual_clp=costo_extras,
        productividad_kg_por_hh=productividad,
        closure_pct=closure_pct,
        rotacion_anual_pct=rotacion_anual,
        alarmas=alarmas,
    )


# ===== Persistencia =====
_STORAGE_TRAB = "balance-rrhh-trabajadores.json"
_STORAGE_ASIG = "balance-rrhh-asignaciones.json"


def guardar_trabajadores(trabajadores: list[Trabajador]) -> None:
    data_path(_STORAGE_TRAB).write_text(
        json.dumps([t.to_dict() for t in trabajadores], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def cargar_trabajadores() -> list[Trabajador]:
    p = data_path(_STORAGE_TRAB)
    if not p.exists():
        return trabajadores_seed()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return [Trabajador(**d) for d in data]
    except Exception:
        return trabajadores_seed()


def guardar_asignaciones(asignaciones: list[AsignacionHoras]) -> None:
    data_path(_STORAGE_ASIG).write_text(
        json.dumps([a.to_dict() for a in asignaciones], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def cargar_asignaciones(semana: str | None = None) -> list[AsignacionHoras]:
    p = data_path(_STORAGE_ASIG)
    if not p.exists():
        return asignaciones_seed(semana or "2026-W23")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        all_asigs = [
            AsignacionHoras(
                trabajador_id=d["trabajador_id"],
                semana_iso=d["semana_iso"],
                horas_regulares=d["horas_regulares"],
                horas_extras=d.get("horas_extras", 0.0),
                tareas=d.get("tareas", []),
                equipo_asignado=d.get("equipo_asignado", ""),
            )
            for d in data
        ]
        if semana:
            return [a for a in all_asigs if a.semana_iso == semana]
        return all_asigs
    except Exception:
        return asignaciones_seed(semana or "2026-W23")
