"""Sustainability-Linked Bond (SLB) calculator con step-up de tasa por KPIs ESG.

Estructura SLB típica (referencias ICMA Sustainability-Linked Bond Principles):
- Bond issued con tasa base (CORFO + spread).
- 1-3 KPIs sustainability con targets anuales.
- Si target NO se alcanza: tasa sube X bps por el resto de la vida del bond.
- Si se alcanza: tasa se mantiene o incluso baja en SLB premium.

KPIs relevantes para Trongkai (alineados con B-Corp + presentación):
1. ton CO2 eq evitados (vs descomposición vertedero).
2. % residuos agroindustriales valorizados / cuota contractual 50.000 ton.
3. % feed pescado sustituido (toneladas Trongkai Feed vendidas).
4. Reducción consumo agua proceso (m3/ton producto).
5. Empleo local generado (puestos directos en regiones agro).

Fuente: ICMA https://www.icmagroup.org/sustainable-finance/sustainability-linked-bond-principles-slbp/
Mercado Latam: S&P Global Ratings forecast USD 25B en SLBs globales 2026.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KpiSlb:
    """Un KPI sustainability con su trayectoria target."""
    nombre: str
    unidad: str
    baseline: float  # valor año 0 (situación actual o promedio industria)
    targets_anuales: list[float]  # 5 valores: target año 1..5
    pesos_pp_si_falla: float = 25  # basis points adicionales si NO se cumple
    direccion: str = "subir"  # "subir" (más es mejor) o "bajar" (menos es mejor)


@dataclass
class SlbBondSpec:
    """Especificación del bono SLB."""
    monto_clp: float
    tasa_base_anual: float  # ej 0.085 (8.5%)
    plazo_anos: int = 7
    kpis: list[KpiSlb] = field(default_factory=list)


# KPIs default Trongkai (calibrados con docs/INTELIGENCIA-COMPETITIVA.md)
KPIS_DEFAULT: list[KpiSlb] = [
    KpiSlb(
        nombre="Toneladas CO2 evitadas",
        unidad="ton CO2eq/año",
        baseline=0,
        # 50.000 ton MMPP × 0.5 ton CO2 evitada/ton (avg literatura) × ramp-up
        targets_anuales=[5_000, 10_000, 17_500, 23_500, 25_000],
        pesos_pp_si_falla=25,
        direccion="subir",
    ),
    KpiSlb(
        nombre="Cuota mercado feed sostenible Chile",
        unidad="% TAM Feed",
        baseline=0,
        # 9% año 5 según modelo penetracion_pct_ano5
        targets_anuales=[0.01, 0.025, 0.05, 0.075, 0.089],
        pesos_pp_si_falla=25,
        direccion="subir",
    ),
    KpiSlb(
        nombre="Reducción harina pescado uso clientes",
        unidad="ton sustituidas/año",
        baseline=0,
        # ~ 1.800 ton año 5 (1% del TAM 180k ton ingredientes marinos)
        targets_anuales=[100, 400, 900, 1_400, 1_800],
        pesos_pp_si_falla=20,
        direccion="subir",
    ),
]


def evaluar_kpi(kpi: KpiSlb, valor_real_ano: float, ano: int) -> bool:
    """¿Se cumplió el KPI en el año dado? (ano 1..5, índice 0..4)"""
    if ano < 1 or ano > len(kpi.targets_anuales):
        return False
    target = kpi.targets_anuales[ano - 1]
    if kpi.direccion == "subir":
        return valor_real_ano >= target
    return valor_real_ano <= target


def aplicar_step_up(
    bond: SlbBondSpec,
    valores_reales: dict[str, list[float]],
    horizonte: int = 5,
) -> dict:
    """Aplica step-up de tasa según incumplimiento de KPIs.

    Para cada año, evalúa los KPIs. Si UNO falla, agrega step-up al spread.
    El step-up es acumulativo y permanente en SLBs estándar (no decae).

    `valores_reales` = dict[nombre_kpi → list[valor año 1, año 2, ...]]
    """
    spread_acumulado_bps = 0
    tasas_anuales = []
    intereses_anuales = []
    incumplimientos: list[dict] = []

    saldo = bond.monto_clp

    for ano in range(1, horizonte + 1):
        # Antes de aplicar intereses del año, evaluar si hubo incumplimiento el año anterior
        # (los KPIs se observan a final del año X, el step-up aplica para año X+1+)
        if ano > 1:
            ano_evaluado = ano - 1
            for kpi in bond.kpis:
                valores = valores_reales.get(kpi.nombre, [])
                if len(valores) >= ano_evaluado:
                    cumple = evaluar_kpi(kpi, valores[ano_evaluado - 1], ano_evaluado)
                    if not cumple:
                        spread_acumulado_bps += kpi.pesos_pp_si_falla
                        incumplimientos.append({
                            "ano_evaluado": ano_evaluado,
                            "kpi": kpi.nombre,
                            "target": kpi.targets_anuales[ano_evaluado - 1],
                            "valor_real": valores[ano_evaluado - 1],
                            "step_up_bps": kpi.pesos_pp_si_falla,
                            "spread_acumulado_bps": spread_acumulado_bps,
                        })

        tasa_efectiva = bond.tasa_base_anual + spread_acumulado_bps / 10_000
        intereses = saldo * tasa_efectiva
        tasas_anuales.append(tasa_efectiva)
        intereses_anuales.append(intereses)

    interes_sin_stepup = bond.monto_clp * bond.tasa_base_anual * horizonte
    interes_con_stepup = sum(intereses_anuales)
    costo_extra_clp = interes_con_stepup - interes_sin_stepup

    return {
        "monto_bond_clp": bond.monto_clp,
        "tasa_base_anual": bond.tasa_base_anual,
        "tasas_anuales_efectivas": tasas_anuales,
        "intereses_anuales": intereses_anuales,
        "spread_acumulado_bps_final": spread_acumulado_bps,
        "incumplimientos": incumplimientos,
        "intereses_totales_clp": interes_con_stepup,
        "intereses_sin_stepup_clp": interes_sin_stepup,
        "costo_extra_por_incumplimientos_clp": costo_extra_clp,
        "pct_costo_extra_vs_baseline": costo_extra_clp / interes_sin_stepup if interes_sin_stepup else 0,
    }


def simular_kpis_optimista_pesimista(
    bond: SlbBondSpec,
    horizonte: int = 5,
) -> dict:
    """Simulación dual: caso (a) todos los KPIs cumplidos vs (b) todos fallan.

    Útil para mostrar al directorio el rango de costo financiero según ejecución ESG.
    """
    # Caso optimista: todos los reales = target
    optimista_valores = {
        kpi.nombre: list(kpi.targets_anuales) for kpi in bond.kpis
    }
    # Caso pesimista: todos los reales fallan (50% del target si dirección "subir")
    pesimista_valores = {
        kpi.nombre: [t * 0.5 for t in kpi.targets_anuales] for kpi in bond.kpis
    }

    optimista = aplicar_step_up(bond, optimista_valores, horizonte)
    pesimista = aplicar_step_up(bond, pesimista_valores, horizonte)

    return {
        "caso_optimista": optimista,
        "caso_pesimista": pesimista,
        "delta_costo_clp": pesimista["intereses_totales_clp"] - optimista["intereses_totales_clp"],
        "incentivo_esg_clp": pesimista["costo_extra_por_incumplimientos_clp"],
    }
