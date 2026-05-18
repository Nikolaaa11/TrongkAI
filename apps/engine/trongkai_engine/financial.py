"""Módulo 3 — Flujo de caja a 5 años, TIR, VAN, payback.

Estructura del flujo mensual (60 meses):
- Ingresos: ventas SKUs + maquilas + transferencia tec + pago recepción residuos
- Costos directos: MMPP (flete + pago al proveedor) + producción por etapa + envase + transporte clientes
- Gastos fijos: MO + mantención + energía + admin + calidad + certificaciones
- EBITDA = Ingresos - Directos - Fijos
- Flujo Neto = EBITDA - CapEx
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


@dataclass
class FlujoMes:
    mes: int  # 1..60
    ingresos_ventas: float = 0.0
    ingresos_maquilas: float = 0.0
    ingresos_recepcion: float = 0.0
    ingresos_transferencia_tec: float = 0.0
    costos_directos: float = 0.0
    gastos_fijos: float = 0.0
    capex_periodo: float = 0.0

    @property
    def ingresos_totales(self) -> float:
        return (
            self.ingresos_ventas
            + self.ingresos_maquilas
            + self.ingresos_recepcion
            + self.ingresos_transferencia_tec
        )

    @property
    def ebitda(self) -> float:
        return self.ingresos_totales - self.costos_directos - self.gastos_fijos

    @property
    def flujo_neto(self) -> float:
        return self.ebitda - self.capex_periodo


@dataclass
class KPIsFinancieros:
    tir_proyecto_anual: float | None
    van: float
    payback_meses: int | None
    ebitda_margin_promedio: float
    ratio_capex_ventas: float


def calcular_kpis(flujos: list[FlujoMes], wacc_anual: float) -> KPIsFinancieros:
    if not 0 <= wacc_anual < 1:
        raise ValueError(f"wacc_anual ∈ [0,1), got {wacc_anual}")

    if not flujos:
        return KPIsFinancieros(None, 0.0, None, 0.0, 0.0)

    netos = np.array([f.flujo_neto for f in flujos])
    wacc_mensual = (1 + wacc_anual) ** (1 / 12) - 1
    discount = np.array([(1 + wacc_mensual) ** -i for i in range(1, len(netos) + 1)])
    van = float(np.sum(netos * discount))

    tir_mensual = _tir(netos)
    tir_anual = (1 + tir_mensual) ** 12 - 1 if tir_mensual is not None else None

    cumulative = np.cumsum(netos * discount)
    payback_idx = int(np.argmax(cumulative > 0)) + 1 if (cumulative > 0).any() else None

    ingresos_totales = sum(f.ingresos_totales for f in flujos)
    ebitda_totales = sum(f.ebitda for f in flujos)
    ebitda_margin = ebitda_totales / ingresos_totales if ingresos_totales > 0 else 0.0

    capex_total = sum(f.capex_periodo for f in flujos)
    ratio_capex = capex_total / ingresos_totales if ingresos_totales > 0 else 0.0

    return KPIsFinancieros(
        tir_proyecto_anual=tir_anual,
        van=van,
        payback_meses=payback_idx,
        ebitda_margin_promedio=ebitda_margin,
        ratio_capex_ventas=ratio_capex,
    )


def _tir(flujos: np.ndarray, tol: float = 1e-7, max_iter: int = 200) -> float | None:
    """TIR mensual por bisección estable. Devuelve None si no hay solución."""
    if len(flujos) < 2 or (flujos > 0).sum() == 0 or (flujos < 0).sum() == 0:
        return None

    def npv(rate: float) -> float:
        return float(np.sum(flujos / np.power(1 + rate, np.arange(1, len(flujos) + 1))))

    low, high = -0.99, 10.0
    n_low, n_high = npv(low), npv(high)
    if n_low * n_high > 0:
        return None
    for _ in range(max_iter):
        mid = (low + high) / 2
        v = npv(mid)
        if abs(v) < tol:
            return mid
        if v * n_low < 0:
            high = mid
        else:
            low = mid
            n_low = v
    return mid


@dataclass
class TornadoEntry:
    variable: str
    delta_baja_pct: float
    delta_alta_pct: float
    impacto_tir_baja: float | None
    impacto_tir_alta: float | None


def tornado_chart(
    base_kpis: KPIsFinancieros,
    sensibilidades: Iterable[tuple[str, float, KPIsFinancieros, KPIsFinancieros]],
) -> list[TornadoEntry]:
    """Toma una lista de (variable, delta_pct, kpis_baja, kpis_alta) y arma el chart."""
    out: list[TornadoEntry] = []
    base_tir = base_kpis.tir_proyecto_anual
    for var, delta, kpis_baja, kpis_alta in sensibilidades:
        out.append(
            TornadoEntry(
                variable=var,
                delta_baja_pct=-delta,
                delta_alta_pct=delta,
                impacto_tir_baja=(kpis_baja.tir_proyecto_anual - base_tir)
                if (kpis_baja.tir_proyecto_anual is not None and base_tir is not None)
                else None,
                impacto_tir_alta=(kpis_alta.tir_proyecto_anual - base_tir)
                if (kpis_alta.tir_proyecto_anual is not None and base_tir is not None)
                else None,
            )
        )
    # Ordenado por magnitud absoluta del impacto
    out.sort(
        key=lambda e: abs((e.impacto_tir_baja or 0.0) - (e.impacto_tir_alta or 0.0)),
        reverse=True,
    )
    return out
