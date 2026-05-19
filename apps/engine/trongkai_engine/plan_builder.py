"""Constructor del Plan 5 Años.

Espec del SUPER_PROMPT §4 M3:
- EERR mensual a 60 meses
- KPIs: TIR, VAN, payback, EBITDA margin, ratio CapEx/Ventas
- Reproduce ejemplo Olivero 1 del Excel original

Esta primera versión funciona con supuestos cargados manualmente
(no aún con OK_VALIDADO_*). Cuando entren precios reales y WACC, los flujos
se vuelven defendibles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .financial import FlujoMes, KPIsFinancieros, calcular_kpis


@dataclass
class ParametrosPlan:
    """Inputs del plan a 5 años. Todos los precios en CLP."""

    # Volúmenes — base de cálculo
    volumen_total_ton_ano: float = 50_000

    # Precios de venta por SKU (CLP/kg) — todos PD por default
    precios_clp_kg: dict[str, float] = field(default_factory=dict)

    # Rendimiento por MMPP (fracción de ton procesadas que termina en producto final)
    rendimiento_por_mmpp: dict[str, float] = field(
        default_factory=lambda: {
            "ALPERUJO": 0.39,
            "TOMASA": 0.20,
            "POMASA": 0.22,
            "ORUJO_UVA": 0.18,
            "LEVADURA": 0.30,
        }
    )

    # Costos por etapa CLP/kg producto final
    costo_etapa_clp_kg: dict[str, float] = field(
        default_factory=lambda: {
            "RECEPCION": 3, "ALIMENTACION": 3, "HOMOG_1": 2, "PEF": 6,
            "PRENSADO_MECANICO": 8, "TRICANTER": 10, "EXTRACCION": 12,
            "SECADO": 50, "HOMOG_2": 3, "ENSACADO": 5,
        }
    )

    # CapEx por año
    capex_anual_clp: dict[int, float] = field(
        default_factory=lambda: {1: 800_000_000, 2: 400_000_000, 3: 300_000_000, 4: 200_000_000, 5: 100_000_000}
    )

    # OpEx mensual base (incluye MO, mantención, energía, admin)
    opex_mensual_clp: float = 35_000_000

    # Ingreso accesorio mensual: maquilas
    maquilas_mensual_clp: float = 5_000_000
    transferencia_tec_anual_clp: float = 350_000_000  # patines CORFO

    # Logística MMPP — costo neto promedio CLP/kg input
    costo_mmpp_clp_kg: float = 50

    # Stagger de productos por año (fracción del volumen total)
    volumen_pct_por_ano: dict[int, float] = field(
        default_factory=lambda: {1: 0.3, 2: 0.55, 3: 0.8, 4: 0.95, 5: 1.0}
    )

    # WACC
    wacc_anual: float = 0.12  # 12% — supuesto provisional


PRECIOS_REFERENCIA = {
    "HARINA_ALPERUJO": 800,
    "ACEITE_ALPERUJO": 1_200,  # Jaime mencionó 1.200 $/kg
    "HARINA_ORUJO": 600,
    "HARINA_TOMASA": 700,
    "HARINA_POMASA": 700,
    "PECTINA": 8_000,
    "LICOPENO": 80_000,
    "PROTEINA_UNICEL": 3_500,
    "ANTIOXIDANTE": 5_000,
    "AGLOMERANTE": 2_000,
    "UMAMI": 4_500,
    "ACEITE_ORUJO_UVA": 1_500,
}


@dataclass
class ResumenPlan:
    flujos: list[FlujoMes]
    kpis: KPIsFinancieros
    parametros: ParametrosPlan
    ingresos_anuales: list[float]
    ebitda_anuales: list[float]
    capex_anuales: list[float]


def build_plan(parametros: ParametrosPlan | None = None) -> ResumenPlan:
    p = parametros or ParametrosPlan()
    if not p.precios_clp_kg:
        p.precios_clp_kg = dict(PRECIOS_REFERENCIA)

    # Precio promedio ponderado por SKU (asumimos mix uniforme dentro del año)
    precio_promedio_clp_kg = sum(p.precios_clp_kg.values()) / len(p.precios_clp_kg)
    rendimiento_promedio = sum(p.rendimiento_por_mmpp.values()) / len(p.rendimiento_por_mmpp)
    costo_etapa_total_clp_kg = sum(p.costo_etapa_clp_kg.values())

    flujos: list[FlujoMes] = []
    ingresos_anuales = [0.0] * 5
    ebitda_anuales = [0.0] * 5
    capex_anuales = [0.0] * 5

    for ano in range(1, 6):
        vol_pct = p.volumen_pct_por_ano.get(ano, 1.0)
        ton_anual = p.volumen_total_ton_ano * vol_pct
        ton_producto_final_anual = ton_anual * rendimiento_promedio
        # Precio promedio * ton convertido a kg
        ingreso_anual = ton_producto_final_anual * 1_000 * precio_promedio_clp_kg

        # Costos directos = MMPP + producción por etapa
        costo_mmpp_anual = ton_anual * 1_000 * p.costo_mmpp_clp_kg
        costo_produccion_anual = ton_producto_final_anual * 1_000 * costo_etapa_total_clp_kg
        directos_anual = costo_mmpp_anual + costo_produccion_anual

        # Gastos fijos
        fijos_anual = p.opex_mensual_clp * 12

        # Ingresos accesorios
        maquilas_anual = p.maquilas_mensual_clp * 12
        transferencia_anual = p.transferencia_tec_anual_clp if ano <= 2 else 0  # patines CORFO 2 primeros años

        capex_ano = p.capex_anual_clp.get(ano, 0)
        capex_anuales[ano - 1] = capex_ano
        ingresos_anuales[ano - 1] = ingreso_anual + maquilas_anual + transferencia_anual
        ebitda_anuales[ano - 1] = ingresos_anuales[ano - 1] - directos_anual - fijos_anual

        for mes in range(1, 13):
            mes_global = (ano - 1) * 12 + mes
            # Stagger lineal del ramp-up dentro del año (productos no llegan parejo)
            stagger = min(1.0, mes / 6.0) if ano == 1 else 1.0
            ingreso_mes = (ingreso_anual / 12) * stagger
            costo_mes = (directos_anual / 12) * stagger
            maquilas_mes = p.maquilas_mensual_clp
            transferencia_mes = transferencia_anual / 12 if transferencia_anual else 0
            capex_mes = capex_ano if mes == 1 else 0

            flujos.append(
                FlujoMes(
                    mes=mes_global,
                    ingresos_ventas=ingreso_mes,
                    ingresos_maquilas=maquilas_mes,
                    ingresos_transferencia_tec=transferencia_mes,
                    costos_directos=costo_mes,
                    gastos_fijos=p.opex_mensual_clp,
                    capex_periodo=capex_mes,
                )
            )

    kpis = calcular_kpis(flujos, wacc_anual=p.wacc_anual)
    return ResumenPlan(
        flujos=flujos,
        kpis=kpis,
        parametros=p,
        ingresos_anuales=ingresos_anuales,
        ebitda_anuales=ebitda_anuales,
        capex_anuales=capex_anuales,
    )


def caso_olivero_1_costo_unitario_kg(distancia_km: float = 82, tarifa_clp_km: float = 1800,
                                       capacidad_camion_ton: float = 25,
                                       pago_recepcion_clp_kg: float = -10) -> dict:
    """Reproduce el cálculo del 'Caso 1 — Olivero 1' del Excel original.

    Olivero 1: 82 km × $1.800/km = $147.600 por viaje.
    Camión 25 ton = 25.000 kg. Costo unitario = $147.600 / 25.000 = $5,904 CLP/kg.
    Pago recepción Caso 1 = nos paga el proveedor (-$10/kg). Costo neto = $5,904 + (-$10) = -$4,096/kg
    (negativo = ingreso neto en la práctica).

    Devuelve los componentes para validar contra el Excel original.
    """
    costo_viaje_clp = distancia_km * tarifa_clp_km
    kg_camion = capacidad_camion_ton * 1_000
    costo_unitario_flete = costo_viaje_clp / kg_camion
    return {
        "costo_viaje_clp": costo_viaje_clp,
        "costo_unitario_flete_clp_kg": round(costo_unitario_flete, 3),
        "pago_recepcion_clp_kg": pago_recepcion_clp_kg,
        "costo_neto_clp_kg": round(costo_unitario_flete + pago_recepcion_clp_kg, 3),
    }
