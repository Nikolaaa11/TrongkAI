"""Multi-Scenario Comparator — compara N escenarios lado a lado.

Para directorio: cuál de los 3 escenarios estratégicos elegir.
Comparación dimensional:
- Financiera: TIR, VAN, payback, MOIC
- CapEx: total, distribución, peak año
- Risk: prob TIR > WACC, colchón breakeven precio
- ESG: carbono baseline (todos los escenarios)
- Bancabilidad: DSCR proxy

Para cada métrica indica: cuál es el mejor + delta vs base.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .escenarios import comparar_escenarios_estrategicos
from .plan_builder import build_plan


@dataclass
class ComparacionEscenarios:
    escenarios: list[dict]   # uno por escenario con métricas
    mejor_por_metrica: dict[str, str]  # nombre del escenario ganador por métrica
    matriz_ranking: dict[str, dict[str, int]]  # {escenario: {metrica: ranking 1=mejor}}
    recomendacion: dict      # {elegido, razon}

    def to_dict(self) -> dict:
        return {
            "escenarios": self.escenarios,
            "mejor_por_metrica": self.mejor_por_metrica,
            "matriz_ranking": self.matriz_ranking,
            "recomendacion": self.recomendacion,
        }


def comparar_estrategicos() -> ComparacionEscenarios:
    """Compara PILOTO / INDUSTRIAL / EXPANSION en múltiples dimensiones."""
    estrategicos = comparar_escenarios_estrategicos()

    escenarios_data = []
    for e in estrategicos:
        plan = e.resumen
        tir = plan.kpis.tir_proyecto_anual or 0
        van = plan.kpis.van
        payback = plan.kpis.payback_meses
        capex_anuales = plan.capex_anuales
        capex_total = sum(capex_anuales)
        capex_peak = max(capex_anuales) if capex_anuales else 0
        ebitda_anuales = plan.ebitda_anuales

        # MOIC proxy
        ebitda_ano5 = ebitda_anuales[-1] if ebitda_anuales else 0
        ev_proxy = ebitda_ano5 * 9.63
        moic = ev_proxy / capex_total if capex_total > 0 else 0

        # DSCR proxy (años 3-5)
        ebitda_3_5 = ebitda_anuales[2:5] if len(ebitda_anuales) >= 5 else ebitda_anuales
        servicio_anual = (capex_total * 0.50) / 10
        dscr = (sum(ebitda_3_5) / len(ebitda_3_5)) / servicio_anual if ebitda_3_5 and servicio_anual else 0

        # Ramp-up: año en que EBITDA cruza positivo
        anio_ebitda_pos = None
        for i, eb in enumerate(ebitda_anuales, 1):
            if eb > 0:
                anio_ebitda_pos = i
                break

        escenarios_data.append({
            "nombre": e.nombre,
            "descripcion": e.descripcion,
            "metricas": {
                "tir": tir,
                "van": van,
                "payback_meses": payback,
                "moic": moic,
                "capex_total": capex_total,
                "capex_peak": capex_peak,
                "dscr_promedio_3_5": dscr,
                "anio_ebitda_positivo": anio_ebitda_pos,
                "ebitda_ano5": ebitda_ano5,
                "ev_proxy_ano5": ev_proxy,
            },
        })

    # Ranking por métrica (1 = mejor)
    metricas_para_ranking = {
        "tir": "max",            # TIR alta es mejor
        "van": "max",
        "moic": "max",
        "ebitda_ano5": "max",
        "dscr_promedio_3_5": "max",
        "payback_meses": "min",  # Payback bajo es mejor
        "capex_total": "min",
        "capex_peak": "min",
        "anio_ebitda_positivo": "min",
    }

    matriz_ranking: dict[str, dict[str, int]] = {e["nombre"]: {} for e in escenarios_data}
    mejor_por_metrica: dict[str, str] = {}

    for metrica, direccion in metricas_para_ranking.items():
        # Tomar valores
        valores = [
            (e["nombre"], e["metricas"].get(metrica) or 0)
            for e in escenarios_data
        ]
        # Sort según dirección
        reverse = direccion == "max"
        valores.sort(key=lambda x: x[1], reverse=reverse)
        # Asignar ranking
        for rank, (nombre, _) in enumerate(valores, 1):
            matriz_ranking[nombre][metrica] = rank
        # Ganador
        mejor_por_metrica[metrica] = valores[0][0]

    # Recomendación: el escenario con menor suma de rankings
    suma_ranks = {
        nombre: sum(matriz_ranking[nombre].values())
        for nombre in matriz_ranking
    }
    ganador = min(suma_ranks, key=suma_ranks.get)
    score_ganador = suma_ranks[ganador]
    score_max = max(suma_ranks.values())

    razon = (
        f"{ganador} obtiene el mejor balance: ranking promedio "
        f"{score_ganador / len(metricas_para_ranking):.1f} sobre {len(metricas_para_ranking)} métricas "
        f"(vs peor {score_max / len(metricas_para_ranking):.1f}). Wins en: "
        + ", ".join(m for m, w in mejor_por_metrica.items() if w == ganador)
    )

    return ComparacionEscenarios(
        escenarios=escenarios_data,
        mejor_por_metrica=mejor_por_metrica,
        matriz_ranking=matriz_ranking,
        recomendacion={"elegido": ganador, "razon": razon},
    )
