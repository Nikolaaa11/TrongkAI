"""Planificador de agenda de camiones — Módulo 1.

Dado:
- Un set de Suppliers con volumen comprometido por año y MMPP.
- Capacidades por etapa del proceso.
- Una ventana de fechas (rango de meses dentro de las temporadas de MMPP).

Distribuye camiones por día sin superar el bottleneck. La distribución es
determinística (no optimiza, sólo rellena) — el optimizador real (scipy) viene
en Fase 5 (What-if).

Output: lista de slots `(fecha, supplier, ton, camiones)`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Iterable

from .bottleneck import (
    BottleneckResult,
    CapacidadEtapa,
    compute_bottleneck,
)


@dataclass(frozen=True)
class SupplierSlot:
    fecha: date
    supplier_nombre: str
    mmpp_codigo: str
    ton_dia: float
    camiones_dia: int


@dataclass(frozen=True)
class SupplierTarget:
    """Volumen anual comprometido por un proveedor."""
    nombre: str
    mmpp_codigo: str
    volumen_anual_ton: float
    capacidad_camion_ton: float


@dataclass
class TemporadaMMPP:
    mmpp_codigo: str
    mes_inicio: int  # 1..12
    mes_fin: int  # 1..12 inclusive
    tiempo_descomposicion_h: float

    def fechas(self, ano: int) -> Iterable[date]:
        cur = date(ano, self.mes_inicio, 1)
        if self.mes_fin >= 12:
            fin = date(ano, 12, 31)
        else:
            fin = date(ano, self.mes_fin + 1, 1) - timedelta(days=1)
        while cur <= fin:
            yield cur
            cur += timedelta(days=1)


@dataclass
class AgendaResult:
    slots: list[SupplierSlot] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)
    bottleneck: BottleneckResult | None = None
    total_ton_planificadas: float = 0.0
    total_camiones: int = 0


def build_agenda(
    ano: int,
    capacidades: list[CapacidadEtapa],
    temporadas: list[TemporadaMMPP],
    suppliers_por_mmpp: dict[str, list[SupplierTarget]],
    horas_operativas_dia: float = 24.0,
) -> AgendaResult:
    """Reparte camiones por día respetando el bottleneck.

    Estrategia: por cada MMPP, durante su temporada, repartir el volumen comprometido
    de cada supplier en partes iguales por día, sin superar el camiones_max_dia del
    bottleneck.
    """
    result = AgendaResult()

    for temp in temporadas:
        suppliers = suppliers_por_mmpp.get(temp.mmpp_codigo, [])
        if not suppliers:
            result.advertencias.append(
                f"No hay suppliers ACTIVOS para {temp.mmpp_codigo} en temporada {temp.mes_inicio}-{temp.mes_fin}"
            )
            continue

        # Capacidad camión promedio del set de suppliers
        cap_camion_avg = sum(s.capacidad_camion_ton for s in suppliers) / len(suppliers)

        bottleneck = compute_bottleneck(
            capacidades,
            tiempo_descomposicion_h=temp.tiempo_descomposicion_h,
            capacidad_camion_ton=cap_camion_avg,
            horas_operativas_dia=horas_operativas_dia,
        )
        if result.bottleneck is None:
            result.bottleneck = bottleneck

        if not bottleneck.puede_recibir:
            result.advertencias.append(
                f"{temp.mmpp_codigo}: ALERTA ROJA — el proceso ({bottleneck.tiempo_proceso_total_h}h) "
                f"supera el tiempo de descomposición ({temp.tiempo_descomposicion_h}h). "
                f"No se planifican camiones."
            )
            continue

        # Días de la temporada
        dias = list(temp.fechas(ano))
        if not dias:
            continue
        max_camiones_dia = bottleneck.camiones_max_dia

        # Distribuir volumen de cada supplier uniformemente por la temporada
        for supplier in suppliers:
            ton_por_dia_ideal = supplier.volumen_anual_ton / len(dias)
            camiones_por_dia = max(1, round(ton_por_dia_ideal / supplier.capacidad_camion_ton))
            # No sobrepasar el cap del bottleneck para este supplier solo
            camiones_por_dia = min(camiones_por_dia, max_camiones_dia)
            ton_real_dia = camiones_por_dia * supplier.capacidad_camion_ton

            # Cantidad de días que necesitamos para completar volumen
            dias_necesarios = min(
                len(dias),
                max(1, int(supplier.volumen_anual_ton / ton_real_dia)),
            )
            # Repartir los días uniformemente en la temporada
            step = max(1, len(dias) // dias_necesarios)
            usados = 0
            for i, d in enumerate(dias):
                if i % step != 0:
                    continue
                if usados >= dias_necesarios:
                    break
                result.slots.append(
                    SupplierSlot(
                        fecha=d,
                        supplier_nombre=supplier.nombre,
                        mmpp_codigo=supplier.mmpp_codigo,
                        ton_dia=ton_real_dia,
                        camiones_dia=camiones_por_dia,
                    )
                )
                result.total_camiones += camiones_por_dia
                result.total_ton_planificadas += ton_real_dia
                usados += 1

    return result
