"""Snapshot Diff - compara dos puntos del tiempo del modelo.

Compara el snapshot actual con uno anterior (típicamente readiness_history)
y muestra qué cambió: KPIs financieros, score, matriz, alertas, etc.

Para directorio: "¿qué cambió esta semana vs anterior?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiffMetrica:
    nombre: str
    valor_anterior: float | None
    valor_actual: float | None
    delta_absoluto: float | None
    delta_pct: float | None
    direccion: str  # "subio" | "bajo" | "sin_cambio" | "n/a"

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "valor_anterior": self.valor_anterior,
            "valor_actual": self.valor_actual,
            "delta_absoluto": self.delta_absoluto,
            "delta_pct": self.delta_pct,
            "direccion": self.direccion,
        }


def _diff(nombre: str, anterior: float | None, actual: float | None) -> DiffMetrica:
    if anterior is None or actual is None:
        return DiffMetrica(nombre, anterior, actual, None, None, "n/a")
    delta_abs = actual - anterior
    delta_pct = (delta_abs / anterior * 100) if anterior else None
    direccion = "sin_cambio"
    if abs(delta_abs) > 1e-6:
        direccion = "subio" if delta_abs > 0 else "bajo"
    return DiffMetrica(nombre, anterior, actual, delta_abs, delta_pct, direccion)


@dataclass
class SnapshotDiff:
    fecha_anterior: str
    fecha_actual: str
    diffs_financieros: list[DiffMetrica] = field(default_factory=list)
    diffs_score: list[DiffMetrica] = field(default_factory=list)
    diffs_modelo: list[DiffMetrica] = field(default_factory=list)
    cambios_mayores: list[str] = field(default_factory=list)  # texto resumido

    def to_dict(self) -> dict:
        return {
            "fecha_anterior": self.fecha_anterior,
            "fecha_actual": self.fecha_actual,
            "diffs_financieros": [d.to_dict() for d in self.diffs_financieros],
            "diffs_score": [d.to_dict() for d in self.diffs_score],
            "diffs_modelo": [d.to_dict() for d in self.diffs_modelo],
            "cambios_mayores": self.cambios_mayores,
        }


def comparar_snapshots(anterior: dict, actual: dict) -> SnapshotDiff:
    """Compara dos snapshots completos."""
    fecha_ant = anterior.get("generated_at", "")
    fecha_act = actual.get("generated_at", "")

    diffs_fin = []
    diffs_score = []
    diffs_mod = []
    cambios = []

    # ===== Financieros =====
    plan_a = anterior.get("plan", {}).get("kpis", {})
    plan_b = actual.get("plan", {}).get("kpis", {})

    d = _diff("TIR proyecto", plan_a.get("tir"), plan_b.get("tir"))
    diffs_fin.append(d)
    if d.delta_absoluto is not None and abs(d.delta_absoluto) > 0.005:
        cambios.append(f"TIR {'subió' if d.direccion == 'subio' else 'bajó'} {abs(d.delta_absoluto)*100:.2f}pp")

    d = _diff("VAN", plan_a.get("van"), plan_b.get("van"))
    diffs_fin.append(d)
    if d.delta_pct is not None and abs(d.delta_pct) > 5:
        cambios.append(f"VAN {'creció' if d.direccion == 'subio' else 'cayó'} {abs(d.delta_pct):.1f}%")

    diffs_fin.append(_diff("Payback (meses)", plan_a.get("payback_meses"), plan_b.get("payback_meses")))
    diffs_fin.append(_diff("EBITDA margin", plan_a.get("ebitda_margin_promedio"), plan_b.get("ebitda_margin_promedio")))

    val_a = anterior.get("valuation", {})
    val_b = actual.get("valuation", {})
    diffs_fin.append(_diff("EV exit año 5", val_a.get("ev_base_clp"), val_b.get("ev_base_clp")))
    diffs_fin.append(_diff("MOIC", val_a.get("moic"), val_b.get("moic")))

    # ===== Score =====
    rs_a = anterior.get("readiness_score") or {}
    rs_b = actual.get("readiness_score") or {}
    d = _diff("Readiness Score", rs_a.get("score_total"), rs_b.get("score_total"))
    diffs_score.append(d)
    if d.delta_absoluto is not None and abs(d.delta_absoluto) > 1:
        cambios.append(f"Readiness Score {'+' if d.direccion == 'subio' else ''}{d.delta_absoluto:.1f} pts")

    # ===== Modelo =====
    dr_a = anterior.get("data_room") or {}
    dr_b = actual.get("data_room") or {}
    d = _diff("Data Room avance", dr_a.get("pct_avance"), dr_b.get("pct_avance"))
    diffs_mod.append(d)
    if d.delta_absoluto is not None and abs(d.delta_absoluto) > 2:
        cambios.append(f"Data Room {'+' if d.direccion == 'subio' else ''}{d.delta_absoluto:.1f}% avance")

    vm_a = anterior.get("variables_matrix") or {}
    vm_b = actual.get("variables_matrix") or {}
    diffs_mod.append(_diff("Matriz cubierta", vm_a.get("pct_cubierto"), vm_b.get("pct_cubierto")))
    diffs_mod.append(_diff("Celdas OK validadas", vm_a.get("OK_VALIDADO"), vm_b.get("OK_VALIDADO")))
    diffs_mod.append(_diff("Celdas PD", vm_a.get("PD"), vm_b.get("PD")))

    al_a = anterior.get("alertas") or {}
    al_b = actual.get("alertas") or {}
    d = _diff("Alertas críticas", al_a.get("criticas"), al_b.get("criticas"))
    diffs_mod.append(d)
    if d.delta_absoluto is not None and d.delta_absoluto > 0:
        cambios.append(f"⚠ Nuevas {d.delta_absoluto:.0f} alerta(s) crítica(s)")
    elif d.delta_absoluto is not None and d.delta_absoluto < 0:
        cambios.append(f"✓ Resolvió {abs(d.delta_absoluto):.0f} alerta(s) crítica(s)")

    if not cambios:
        cambios.append("Sin cambios significativos vs snapshot anterior.")

    return SnapshotDiff(
        fecha_anterior=fecha_ant,
        fecha_actual=fecha_act,
        diffs_financieros=diffs_fin,
        diffs_score=diffs_score,
        diffs_modelo=diffs_mod,
        cambios_mayores=cambios,
    )
