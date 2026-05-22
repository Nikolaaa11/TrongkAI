"""Modelo de riesgo climático para volumen MMPP disponible.

Chile Valle Central tiene riesgo creciente de eventos climáticos extremos:
- Sequía: reduce cosecha 15-40% en años secos. Probabilidad histórica ~25% por año (CR2).
- Heladas tardías: afectan floración olivos/uva. Probabilidad ~15%.
- Granizo: localizado, reduce 10-30% cosecha en zonas específicas. Prob ~10%.
- Ola de calor: estresa cultivos, reduce 5-15%. Prob ~30% (creciente con cambio climático).

Fuentes:
- Centro de Ciencia del Clima y Resiliencia (CR2): https://www.cr2.cl/
- INIA reportes climáticos anuales.
- Modelo seguro agrícola COMSA Chile.

Cada evento afecta diferente a cada MMPP. El modelo sortea combinaciones de eventos
year por year y proyecta el volumen efectivo disponible.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class EventoClimatico:
    nombre: str
    probabilidad_anual: float  # 0..1
    afectacion_por_mmpp: dict[str, tuple[float, float]]  # MMPP → (min_loss, max_loss) en fracción


EVENTOS_CHILE: list[EventoClimatico] = [
    EventoClimatico(
        nombre="Sequía severa",
        probabilidad_anual=0.25,
        afectacion_por_mmpp={
            "ALPERUJO": (0.20, 0.40),  # olivos sensibles a sequía multi-anual
            "TOMASA": (0.15, 0.35),    # tomate de riego
            "POMASA": (0.10, 0.30),    # manzana/pera
            "ORUJO_UVA": (0.10, 0.25),  # vid es resiliente
            "LEVADURA": (0.0, 0.0),    # no afectado
        },
    ),
    EventoClimatico(
        nombre="Helada tardía",
        probabilidad_anual=0.15,
        afectacion_por_mmpp={
            "ALPERUJO": (0.15, 0.30),  # olivos afectan floración
            "TOMASA": (0.05, 0.15),
            "POMASA": (0.20, 0.40),  # manzana/pera más sensible
            "ORUJO_UVA": (0.10, 0.25),
            "LEVADURA": (0.0, 0.0),
        },
    ),
    EventoClimatico(
        nombre="Granizo localizado",
        probabilidad_anual=0.10,
        afectacion_por_mmpp={
            "ALPERUJO": (0.05, 0.15),
            "TOMASA": (0.10, 0.30),
            "POMASA": (0.15, 0.35),
            "ORUJO_UVA": (0.10, 0.25),
            "LEVADURA": (0.0, 0.0),
        },
    ),
    EventoClimatico(
        nombre="Ola de calor extremo",
        probabilidad_anual=0.30,
        afectacion_por_mmpp={
            "ALPERUJO": (0.05, 0.15),
            "TOMASA": (0.10, 0.20),
            "POMASA": (0.05, 0.15),
            "ORUJO_UVA": (0.05, 0.15),
            "LEVADURA": (0.0, 0.0),
        },
    ),
]


@dataclass
class EventoOcurrido:
    ano: int
    nombre_evento: str
    afectacion_pct_por_mmpp: dict[str, float]


@dataclass
class SimulacionClimaResult:
    n_runs: int
    seed: int
    volumen_p5_anual: list[float]
    volumen_p50_anual: list[float]
    volumen_p95_anual: list[float]
    eventos_ejemplo_corrida_1: list[EventoOcurrido]
    perdida_acumulada_p50_pct: float
    perdida_acumulada_p95_pct: float
    probabilidad_anyear_con_evento_critico: float  # al menos 1 evento mayor en algun año


def simular_eventos_un_ano(
    rng: random.Random,
    eventos: list[EventoClimatico] = EVENTOS_CHILE,
) -> list[EventoOcurrido]:
    """Sortea qué eventos ocurren en un año y su intensidad."""
    ocurridos = []
    for ev in eventos:
        if rng.random() < ev.probabilidad_anual:
            afectacion = {
                mmpp: rng.uniform(low, high)
                for mmpp, (low, high) in ev.afectacion_por_mmpp.items()
                if high > 0
            }
            ocurridos.append(EventoOcurrido(
                ano=0,  # llenado luego
                nombre_evento=ev.nombre,
                afectacion_pct_por_mmpp=afectacion,
            ))
    return ocurridos


def aplicar_afectacion_a_volumen(
    volumen_base_anual_ton: float,
    eventos_ano: list[EventoOcurrido],
    pesos_mmpp: dict[str, float] | None = None,
) -> tuple[float, float]:
    """Aplica la peor afectación promedio ponderada al volumen total.

    pesos_mmpp = fracción del volumen que viene de cada MMPP. Si None, asume uniforme.
    Devuelve (volumen_efectivo, perdida_pct).
    """
    if not eventos_ano:
        return volumen_base_anual_ton, 0.0
    pesos = pesos_mmpp or {"ALPERUJO": 0.55, "TOMASA": 0.20, "POMASA": 0.10, "ORUJO_UVA": 0.10, "LEVADURA": 0.05}
    # Cada MMPP tiene perdida = max de las afectaciones de los eventos del año
    perdida_por_mmpp: dict[str, float] = {}
    for ev in eventos_ano:
        for mmpp, afect in ev.afectacion_pct_por_mmpp.items():
            perdida_por_mmpp[mmpp] = max(perdida_por_mmpp.get(mmpp, 0), afect)
    # Perdida ponderada
    perdida_total = sum(perdida_por_mmpp.get(mmpp, 0) * peso for mmpp, peso in pesos.items())
    return volumen_base_anual_ton * (1 - perdida_total), perdida_total


def simular_clima_n_corridas(
    volumen_base_anual_ton: list[float],  # vol anual del plan (5 años)
    n_runs: int = 2_000,
    seed: int = 42,
) -> SimulacionClimaResult:
    rng = random.Random(seed)
    n_anos = len(volumen_base_anual_ton)
    volumenes_por_ano: list[list[float]] = [[] for _ in range(n_anos)]
    perdidas_acumuladas: list[float] = []
    anos_con_evento_critico: int = 0
    eventos_corrida_1: list[EventoOcurrido] = []

    for run in range(n_runs):
        perdida_acum = 0.0
        tuvo_critico = False
        for ano_idx in range(n_anos):
            eventos = simular_eventos_un_ano(rng)
            for e in eventos:
                e_actualizado = EventoOcurrido(
                    ano=ano_idx + 1,
                    nombre_evento=e.nombre_evento,
                    afectacion_pct_por_mmpp=e.afectacion_pct_por_mmpp,
                )
                if run == 0:
                    eventos_corrida_1.append(e_actualizado)
            vol_efect, perdida = aplicar_afectacion_a_volumen(
                volumen_base_anual_ton[ano_idx], eventos
            )
            volumenes_por_ano[ano_idx].append(vol_efect)
            perdida_acum += perdida
            if perdida > 0.15:  # > 15% en un año = crítico
                tuvo_critico = True
        perdidas_acumuladas.append(perdida_acum / n_anos)
        if tuvo_critico:
            anos_con_evento_critico += 1

    def percentile(lst: list[float], p: float) -> float:
        s = sorted(lst)
        idx = int(round(len(s) * p / 100))
        idx = min(len(s) - 1, max(0, idx))
        return s[idx]

    return SimulacionClimaResult(
        n_runs=n_runs,
        seed=seed,
        volumen_p5_anual=[percentile(v, 5) for v in volumenes_por_ano],
        volumen_p50_anual=[percentile(v, 50) for v in volumenes_por_ano],
        volumen_p95_anual=[percentile(v, 95) for v in volumenes_por_ano],
        eventos_ejemplo_corrida_1=eventos_corrida_1,
        perdida_acumulada_p50_pct=percentile(perdidas_acumuladas, 50),
        perdida_acumulada_p95_pct=percentile(perdidas_acumuladas, 95),
        probabilidad_anyear_con_evento_critico=anos_con_evento_critico / n_runs,
    )
