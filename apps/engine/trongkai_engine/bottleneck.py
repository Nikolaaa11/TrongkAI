"""Motor de cuello de botella — Módulo 1.

Spec: SUPER_PROMPT §4 M1.

Determina:
- flujo_max_ton_hora = min(capacidad por etapa aplicable)
- ventana_segura_horas = tiempo_descomposicion - tiempo_proceso_total
- camiones_max_dia = (flujo_max_ton_hora * horas_operativas) / capacidad_camion_ton
- alerta ROJA si tiempo_proceso > tiempo_descomposicion → NO recibir.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EtapaProceso(StrEnum):
    RECEPCION = "RECEPCION"
    ALIMENTACION = "ALIMENTACION"
    HOMOG_1 = "HOMOG_1"
    PEF = "PEF"
    PRENSADO_MECANICO = "PRENSADO_MECANICO"
    TRICANTER = "TRICANTER"
    EXTRACCION = "EXTRACCION"
    SECADO = "SECADO"
    HOMOG_2 = "HOMOG_2"
    ENSACADO = "ENSACADO"


@dataclass(frozen=True)
class CapacidadEtapa:
    etapa: EtapaProceso
    ton_por_hora: float | None  # None = aún no determinado (estado PD)
    tiempo_residencia_h: float = 0.0  # horas que la MMPP pasa en la etapa
    aplica: bool = True  # si la etapa aplica a la MMPP en cuestión


@dataclass
class BottleneckResult:
    flujo_max_ton_h: float
    etapa_bottleneck: EtapaProceso
    tiempo_proceso_total_h: float
    tiempo_descomposicion_h: float
    ventana_segura_h: float  # negativo = ALERTA ROJA
    puede_recibir: bool
    camiones_max_dia: int
    horas_operativas_dia: float
    incertidumbres: list[str]  # cuando hay etapas con capacidad PD

    @property
    def alerta(self) -> str:
        if not self.puede_recibir:
            return "ROJA"
        if self.ventana_segura_h < 1:
            return "AMARILLA"
        if self.incertidumbres:
            return "AMARILLA"
        return "VERDE"


def compute_bottleneck(
    capacidades: list[CapacidadEtapa],
    tiempo_descomposicion_h: float,
    capacidad_camion_ton: float = 22.5,  # midpoint 20-25 ton del SUPER_PROMPT
    horas_operativas_dia: float = 24.0,  # 24/7 en temporada según Jaime
) -> BottleneckResult:
    if tiempo_descomposicion_h <= 0:
        raise ValueError("tiempo_descomposicion_h debe ser > 0")
    if capacidad_camion_ton <= 0:
        raise ValueError("capacidad_camion_ton debe ser > 0")

    aplicables = [c for c in capacidades if c.aplica]
    if not aplicables:
        raise ValueError("No hay etapas aplicables a esta MMPP")

    # Bottleneck = etapa con menor ton/h (ignorando None = PD)
    con_capacidad = [c for c in aplicables if c.ton_por_hora is not None]
    incertidumbres = [
        f"Capacidad de {c.etapa.value} aún PD; excluida del cálculo de bottleneck"
        for c in aplicables
        if c.ton_por_hora is None
    ]

    if not con_capacidad:
        # Todo PD → no se puede recibir nada con seguridad.
        return BottleneckResult(
            flujo_max_ton_h=0.0,
            etapa_bottleneck=aplicables[0].etapa,
            tiempo_proceso_total_h=sum(c.tiempo_residencia_h for c in aplicables),
            tiempo_descomposicion_h=tiempo_descomposicion_h,
            ventana_segura_h=-1,
            puede_recibir=False,
            camiones_max_dia=0,
            horas_operativas_dia=horas_operativas_dia,
            incertidumbres=["Todas las capacidades están PD; no se puede planificar."],
        )

    bottleneck = min(con_capacidad, key=lambda c: c.ton_por_hora or float("inf"))
    flujo_max = bottleneck.ton_por_hora or 0.0
    tiempo_total = sum(c.tiempo_residencia_h for c in aplicables)
    ventana = tiempo_descomposicion_h - tiempo_total
    puede_recibir = ventana > 0

    camiones = int((flujo_max * horas_operativas_dia) // capacidad_camion_ton) if puede_recibir else 0

    return BottleneckResult(
        flujo_max_ton_h=flujo_max,
        etapa_bottleneck=bottleneck.etapa,
        tiempo_proceso_total_h=tiempo_total,
        tiempo_descomposicion_h=tiempo_descomposicion_h,
        ventana_segura_h=ventana,
        puede_recibir=puede_recibir,
        camiones_max_dia=camiones,
        horas_operativas_dia=horas_operativas_dia,
        incertidumbres=incertidumbres,
    )
