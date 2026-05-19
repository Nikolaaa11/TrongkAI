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

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field, replace
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


# ============================================================================
# Tornado de sensibilidades — Módulo 4 (extensión)
# ============================================================================


@dataclass
class TornadoSensibilidad:
    """Resultado del tornado para una variable (corrida baja + alta)."""

    variable: str
    delta_pct: float
    tir_baja: float | None
    tir_alta: float | None
    van_baja: float
    van_alta: float

    @property
    def magnitud_tir(self) -> float:
        """Magnitud absoluta del swing TIR (alta - baja) para ordenamiento."""
        if self.tir_baja is None or self.tir_alta is None:
            return 0.0
        return abs(self.tir_alta - self.tir_baja)


# Mapeo declarativo de variable -> función que aplica el delta multiplicativo
# sobre una copia de ParametrosPlan. Cada variable se shockea ±delta_pct.
_VARIABLES_TORNADO: dict[str, Callable[[ParametrosPlan, float], ParametrosPlan]] = {
    "wacc_anual": lambda p, mult: _set_wacc(p, mult),
    "precio_promedio": lambda p, mult: _scale_precios(p, mult),
    "costo_mmpp": lambda p, mult: replace(p, costo_mmpp_clp_kg=p.costo_mmpp_clp_kg * mult),
    "opex_mensual": lambda p, mult: replace(p, opex_mensual_clp=p.opex_mensual_clp * mult),
    "rendimiento_promedio": lambda p, mult: _scale_rendimientos(p, mult),
}


def _set_wacc(p: ParametrosPlan, mult: float) -> ParametrosPlan:
    nuevo = p.wacc_anual * mult
    # Clamp al rango [0, 1) que requiere calcular_kpis
    nuevo = max(0.0, min(nuevo, 0.99))
    return replace(p, wacc_anual=nuevo)


def _scale_precios(p: ParametrosPlan, mult: float) -> ParametrosPlan:
    base = p.precios_clp_kg or dict(PRECIOS_REFERENCIA)
    return replace(p, precios_clp_kg={k: v * mult for k, v in base.items()})


def _scale_rendimientos(p: ParametrosPlan, mult: float) -> ParametrosPlan:
    nuevos = {k: min(1.0, max(0.0, v * mult)) for k, v in p.rendimiento_por_mmpp.items()}
    return replace(p, rendimiento_por_mmpp=nuevos)


def tornado_sensibilidades(
    base_params: ParametrosPlan | None = None,
    deltas_pct: dict[str, float] | None = None,
) -> list[TornadoSensibilidad]:
    """Genera el tornado de sensibilidades sobre las 5 variables clave.

    Para cada variable corre el plan con factor (1 - delta) y (1 + delta),
    captura TIR/VAN y devuelve la lista ordenada por magnitud de swing TIR
    (mayor impacto primero) — formato gráfico tornado estándar.

    `deltas_pct` permite override por variable (default 20% para todas).
    """
    base_params = base_params or ParametrosPlan()
    # Construye base fresh para que el plan use defaults sin contaminar params
    base_for_run = deepcopy(base_params)
    if not base_for_run.precios_clp_kg:
        base_for_run.precios_clp_kg = dict(PRECIOS_REFERENCIA)

    defaults = {var: 0.20 for var in _VARIABLES_TORNADO}
    if deltas_pct:
        defaults.update(deltas_pct)

    resultados: list[TornadoSensibilidad] = []
    for var, fn in _VARIABLES_TORNADO.items():
        delta = defaults[var]
        plan_baja = build_plan(fn(deepcopy(base_for_run), 1 - delta))
        plan_alta = build_plan(fn(deepcopy(base_for_run), 1 + delta))
        resultados.append(
            TornadoSensibilidad(
                variable=var,
                delta_pct=delta,
                tir_baja=plan_baja.kpis.tir_proyecto_anual,
                tir_alta=plan_alta.kpis.tir_proyecto_anual,
                van_baja=plan_baja.kpis.van,
                van_alta=plan_alta.kpis.van,
            )
        )

    resultados.sort(key=lambda r: r.magnitud_tir, reverse=True)
    return resultados
