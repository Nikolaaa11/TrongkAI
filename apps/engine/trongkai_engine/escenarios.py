"""Tres escenarios estratégicos de planta INDUSTRIAL — decisión de directorio.

Cada escenario es una estrategia de escala INDUSTRIAL (decenas de miles de t/año),
NO el piloto físico de 27,5 t/año (ese vive en balances/simulacion_revenue.py y no
es rentable a escala x1). Cada uno tiene perfil de CapEx + volumen + ramp distinto.

| Escenario   | Y1 vol | Y3 vol | Y5 vol | CapEx total 5y | Filosofía                            |
|-------------|--------|--------|--------|----------------|--------------------------------------|
| CONSERVADOR | 5k     | 15k    | 25k    | CLP 9B         | Escala reducida, menor riesgo        |
| INDUSTRIAL  | 15k    | 40k    | 50k    | CLP 15B (default plan_builder)        | Plan base actual                     |
| EXPANSION   | 20k    | 50k    | 80k    | CLP 28B        | Sobrescalar para capturar mercado    |

Output: comparación TIR/VAN/Payback de cada estrategia + recomendación.
"""

from __future__ import annotations

from dataclasses import dataclass

from .plan_builder import ParametrosPlan, ResumenPlan, build_plan


@dataclass
class EscenarioEstrategico:
    nombre: str
    descripcion: str
    parametros: ParametrosPlan
    resumen: ResumenPlan


def _params_conservador() -> ParametrosPlan:
    """Estrategia conservadora INDUSTRIAL: escala reducida, menor riesgo.

    NO confundir con el piloto físico (27,5 t/año). Es una planta industrial chica.
    - Volumen empieza en 5k año 1 y crece a 25k al año 5 (la mitad del cap contractual).
    - CapEx total 9B CLP (vs 15B del industrial) — menor riesgo.
    - Renunciamos a parte del upside pero el payback es más rápido.
    """
    return ParametrosPlan(
        volumen_total_ton_ano=25_000,  # cap menor
        volumen_pct_por_ano={1: 0.20, 2: 0.40, 3: 0.60, 4: 0.85, 5: 1.0},
        capex_anual_clp={
            1: 1_500_000_000,  # planta piloto chica
            2: 2_500_000_000,  # escalado parcial
            3: 2_500_000_000,  # 1ra línea PTEC
            4: 1_500_000_000,
            5: 1_000_000_000,
        },
        opex_mensual_clp=50_000_000,  # 15 personas + mantención básica
    )


def _params_industrial() -> ParametrosPlan:
    """Plan base actual del plan_builder.

    50k ton/año al año 5. CapEx 15B 5 años. OpEx 80M/mes.
    """
    return ParametrosPlan()  # defaults del módulo


def _params_expansion() -> ParametrosPlan:
    """Estrategia agresiva: sobrescalar para capturar todo el mercado oliva + tomate Chile.

    - Volumen target 80k ton año 5 (sobre-pasa cap contractual con compromiso nuevo).
    - CapEx 28B 5 años — 2 plantas o 1 con líneas duplicadas.
    - OpEx 120M (40+ personas).
    """
    return ParametrosPlan(
        volumen_total_ton_ano=80_000,
        capex_anual_clp={
            1: 5_000_000_000,
            2: 8_000_000_000,
            3: 7_000_000_000,
            4: 5_000_000_000,
            5: 3_000_000_000,
        },
        opex_mensual_clp=120_000_000,
    )


def comparar_escenarios_estrategicos() -> list[EscenarioEstrategico]:
    """Ejecuta los 3 escenarios y devuelve lista ordenada para tabla comparativa."""
    specs = [
        ("CONSERVADOR", "Escala industrial reducida 25k ton/año máx. Menor riesgo, payback temprano.", _params_conservador()),
        ("INDUSTRIAL", "Plan base contractual 50k ton/año. Industria estándar.", _params_industrial()),
        ("EXPANSION", "Sobrescalar a 80k ton/año. Maximiza VAN si financiamiento disponible.", _params_expansion()),
    ]
    return [
        EscenarioEstrategico(nombre=nombre, descripcion=desc, parametros=params, resumen=build_plan(params))
        for nombre, desc, params in specs
    ]


def recomendacion_estrategica(escenarios: list[EscenarioEstrategico]) -> dict:
    """Aplica una heurística simple para elegir escenario por perfil de riesgo:

    - Si WACC base > 0.20 → CONSERVADOR (riesgo alto en tasa)
    - Si VAN(EXPANSION) > 1.5× VAN(INDUSTRIAL) y VAN(EXPANSION) > 0 → EXPANSION
    - Si VAN(INDUSTRIAL) > 0 → INDUSTRIAL
    - Else → CONSERVADOR (bajar exposición cuando ningún escenario da VAN positivo)
    """
    by_name = {e.nombre: e for e in escenarios}
    van_ind = by_name["INDUSTRIAL"].resumen.kpis.van
    van_exp = by_name["EXPANSION"].resumen.kpis.van
    van_con = by_name["CONSERVADOR"].resumen.kpis.van
    wacc = by_name["INDUSTRIAL"].parametros.wacc_anual

    if wacc > 0.20:
        choice = "CONSERVADOR"
        reason = f"WACC {wacc:.1%} es muy alto — minimizar exposición."
    elif van_exp > 1.5 * van_ind and van_exp > 0:
        choice = "EXPANSION"
        reason = f"VAN(EXPANSION)={van_exp/1e9:.1f}B > 1.5× INDUSTRIAL={van_ind/1e9:.1f}B."
    elif van_ind > 0:
        choice = "INDUSTRIAL"
        reason = f"VAN(INDUSTRIAL)={van_ind/1e9:.1f}B positivo y mejor risk-adjusted."
    else:
        choice = "CONSERVADOR"
        reason = f"VAN(INDUSTRIAL)={van_ind/1e9:.1f}B no positivo — bajar exposición."

    return {
        "elegido": choice,
        "razon": reason,
        "vans_b_clp": {"CONSERVADOR": van_con/1e9, "INDUSTRIAL": van_ind/1e9, "EXPANSION": van_exp/1e9},
        "tirs_pct": {
            e.nombre: (e.resumen.kpis.tir_proyecto_anual * 100) if e.resumen.kpis.tir_proyecto_anual else None
            for e in escenarios
        },
    }
