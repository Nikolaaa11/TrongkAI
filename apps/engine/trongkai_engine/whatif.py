"""Simulador what-if — Módulo 4.

Toma un set de overrides sobre `ParametrosPlan` y produce 1..N escenarios.
Output: comparación de KPIs y resúmenes anuales.

Casos típicos (SUPER_PROMPT §4 M4):
1. No procesar tomasa → reasignar capacidad a alperujo.
2. Precio licopeno -30%.
3. 2da línea PEF año 2 vs año 3.
4. Olivero 3 500 → 2.000 ton.
5. Certificaciones nuevas con premium precio.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC
from hashlib import sha256
from typing import Any

from .plan_builder import ParametrosPlan, ResumenPlan, build_plan


@dataclass
class Escenario:
    nombre: str
    overrides: dict[str, Any] = field(default_factory=dict)
    descripcion: str | None = None


@dataclass
class ComparacionWhatIf:
    base: ResumenPlan
    escenarios: list[tuple[Escenario, ResumenPlan]]

    def to_dict(self) -> dict:
        return {
            "base": _resumen_to_dict(self.base),
            "escenarios": [
                {
                    "nombre": esc.nombre,
                    "descripcion": esc.descripcion,
                    "overrides": esc.overrides,
                    "resumen": _resumen_to_dict(plan),
                    "deltas": _diff_kpis(self.base, plan),
                }
                for esc, plan in self.escenarios
            ],
        }


def _resumen_to_dict(r: ResumenPlan) -> dict:
    return {
        "kpis": {
            "tir": r.kpis.tir_proyecto_anual,
            "van": r.kpis.van,
            "payback_meses": r.kpis.payback_meses,
            "ebitda_margin": r.kpis.ebitda_margin_promedio,
            "capex_ratio": r.kpis.ratio_capex_ventas,
        },
        "ingresos_anuales": r.ingresos_anuales,
        "ebitda_anuales": r.ebitda_anuales,
        "capex_anuales": r.capex_anuales,
    }


def _diff_kpis(base: ResumenPlan, escenario: ResumenPlan) -> dict:
    return {
        "tir_pp": (
            (escenario.kpis.tir_proyecto_anual - base.kpis.tir_proyecto_anual) * 100
            if base.kpis.tir_proyecto_anual is not None and escenario.kpis.tir_proyecto_anual is not None
            else None
        ),
        "van_pct": (
            ((escenario.kpis.van - base.kpis.van) / base.kpis.van) * 100
            if base.kpis.van not in (0, None)
            else None
        ),
        "payback_meses_delta": (
            (escenario.kpis.payback_meses or 0) - (base.kpis.payback_meses or 0)
            if base.kpis.payback_meses and escenario.kpis.payback_meses
            else None
        ),
    }


def comparar_escenarios(escenarios: list[Escenario], base_params: ParametrosPlan | None = None) -> ComparacionWhatIf:
    base = build_plan(base_params or ParametrosPlan())
    runs = []
    for esc in escenarios:
        params = _apply_overrides(base_params or ParametrosPlan(), esc.overrides)
        runs.append((esc, build_plan(params)))
    return ComparacionWhatIf(base=base, escenarios=runs)


def _apply_overrides(base: ParametrosPlan, overrides: dict[str, Any]) -> ParametrosPlan:
    """Aplica overrides en una copia de ParametrosPlan. Acepta dot-paths simples.

    Cuando el sub-dict tiene keys numéricas (CapEx por año, por ejemplo), el caller
    puede pasar "capex_anual_clp.1" — el "1" se convierte automáticamente a int si
    el dict original tiene int keys.
    """
    data = asdict(base)
    for k, v in overrides.items():
        if "." in k:
            head, _, tail = k.partition(".")
            target = data.get(head)
            if not isinstance(target, dict):
                raise ValueError(f"override no aplicable: {k}")
            # Detectar si las keys del dict son int y castear si tail es número
            if target and all(isinstance(key, int) for key in target.keys()):
                try:
                    tail_key: Any = int(tail)
                except ValueError:
                    tail_key = tail
            else:
                tail_key = tail
            target[tail_key] = v
        else:
            data[k] = v
    return ParametrosPlan(**data)


# ============================================================================
# Snapshots no destructivos
# ============================================================================

@dataclass
class Snapshot:
    nombre: str
    timestamp_iso: str
    comparacion: ComparacionWhatIf

    @property
    def hash(self) -> str:
        payload = json.dumps(self.comparacion.to_dict(), sort_keys=True, default=str).encode("utf-8")
        return sha256(payload).hexdigest()[:12]


def create_snapshot(nombre: str, comparacion: ComparacionWhatIf) -> Snapshot:
    from datetime import datetime, timezone
    return Snapshot(nombre=nombre, timestamp_iso=datetime.now(UTC).isoformat(), comparacion=comparacion)
