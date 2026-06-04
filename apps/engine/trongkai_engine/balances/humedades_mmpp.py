"""Humedades de entrada por MMPP segun conversacion equipo planta.

Variabilidad por condiciones climaticas — ranges, no puntos.

Fuente: Conversacion 4/06/2026 con equipo Agrosphere/Trongkai.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class HumedadMMPP:
    codigo: str
    nombre_legible: str
    humedad_min_pct: float
    humedad_max_pct: float
    notas: str = ""

    @property
    def humedad_promedio_pct(self) -> float:
        return (self.humedad_min_pct + self.humedad_max_pct) / 2

    @property
    def variabilidad_pct(self) -> float:
        return self.humedad_max_pct - self.humedad_min_pct

    def to_dict(self) -> dict:
        d = asdict(self)
        d["humedad_promedio_pct"] = round(self.humedad_promedio_pct, 3)
        d["variabilidad_pct"] = round(self.variabilidad_pct, 3)
        return d


HUMEDADES_INGRESO = [
    HumedadMMPP("TOMASA_COLD", "Tomasa Cold (sin pasar por agua caliente)",
                0.75, 0.85,
                notas="Variabilidad por temporada (cosecha vs almacen)."),
    HumedadMMPP("TOMASA_HOT", "Tomasa Hot (pasada por agua caliente)",
                0.70, 0.80,
                notas="Levemente mas baja por evaporacion previa en proceso conservero."),
    HumedadMMPP("ORUJO", "Orujo (uva tinto/blanco)",
                0.60, 0.65,
                notas="Llega 3-7 dias post-cosecha. Variabilidad < 5pp."),
    HumedadMMPP("ALPERUJO", "Alperujo (oliva)",
                0.55, 0.60,
                notas="Co-producto extraccion EV/V. Estacional (abril-julio)."),
    HumedadMMPP("POMASA", "Pomasa (manzana)",
                0.78, 0.82,
                notas="Variabilidad por condicion fruta procesada."),
]


def humedad_por_mmpp(codigo: str) -> HumedadMMPP | None:
    for h in HUMEDADES_INGRESO:
        if h.codigo == codigo:
            return h
    return None


def listar_humedades() -> list[dict]:
    return [h.to_dict() for h in HUMEDADES_INGRESO]
