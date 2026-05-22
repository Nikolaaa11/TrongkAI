"""Monte Carlo de 10k corridas para estimar bandas de confianza TIR.

Distribuciones (basadas en RIESGO-SUPUESTOS.md sensibilidades):
- WACC: normal(0.18, 0.02) — fluctuación de tasa de descuento.
- Precios SKU: lognormal con sigma 0.20 por sigma de mercado.
- Rendimiento MMPP: normal con sigma 0.05 (planta piloto puede variar).
- Costo MMPP: normal(30, 8) — flete + pago varía.
- OpEx mensual: normal(80M, 15M) — costo operativo industrial real.

Devuelve:
- P5/P50/P95 de TIR, VAN, payback.
- Histograma de TIR (50 bins).
- Probabilidad TIR > WACC.
- Probabilidad VAN > 0.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .plan_builder import ParametrosPlan, build_plan


@dataclass
class MonteCarloResult:
    n_runs: int
    tir_p5: float | None
    tir_p50: float | None
    tir_p95: float | None
    van_p5: float
    van_p50: float
    van_p95: float
    payback_p50: int | None
    prob_tir_supera_wacc: float
    prob_van_positivo: float
    histograma_tir: list[dict] = field(default_factory=list)
    seed: int = 42


def _sample_normal(mu: float, sigma: float, rng: random.Random) -> float:
    """Distribución normal truncada a no-negativos."""
    return max(0.0, rng.gauss(mu, sigma))


def _sample_lognormal_factor(sigma: float, rng: random.Random) -> float:
    """Devuelve un factor multiplicativo lognormal centrado en 1."""
    import math
    return math.exp(rng.gauss(0, sigma))


def _sample_params(base: ParametrosPlan, rng: random.Random) -> ParametrosPlan:
    """Sortea un set de ParametrosPlan a partir del base."""
    # WACC: normal(mu=base, sigma=0.02), truncado a [0.05, 0.40]
    wacc = min(0.40, max(0.05, _sample_normal(base.wacc_anual, 0.02, rng)))
    # Precios: cada SKU escalado por un factor lognormal independiente
    precios = {
        sku: max(0.1, precio * _sample_lognormal_factor(0.20, rng))
        for sku, precio in base.precios_clp_kg.items()
    }
    # Rendimientos: normal con sigma 0.05, truncado a [0.05, 0.60]
    rendimientos = {
        mmpp: min(0.60, max(0.05, _sample_normal(r, 0.05, rng)))
        for mmpp, r in base.rendimiento_por_mmpp.items()
    }
    # Costo MMPP: normal(30, 8), truncado a [0, 100]
    costo_mmpp = min(100.0, max(0.0, _sample_normal(base.costo_mmpp_clp_kg, 8, rng)))
    # OpEx mensual: normal(base, 15M), truncado a [10M, 300M]
    opex = min(300_000_000, max(10_000_000, _sample_normal(base.opex_mensual_clp, 15_000_000, rng)))

    return ParametrosPlan(
        volumen_total_ton_ano=base.volumen_total_ton_ano,
        precios_clp_kg=precios,
        peso_sku=base.peso_sku,
        rendimiento_por_mmpp=rendimientos,
        costo_etapa_clp_kg=base.costo_etapa_clp_kg,
        capex_anual_clp=base.capex_anual_clp,
        opex_mensual_clp=opex,
        maquilas_mensual_clp=base.maquilas_mensual_clp,
        transferencia_tec_anual_clp=base.transferencia_tec_anual_clp,
        costo_mmpp_clp_kg=costo_mmpp,
        costo_comercializacion_pct=base.costo_comercializacion_pct,
        impuesto_renta_pct=base.impuesto_renta_pct,
        volumen_pct_por_ano=base.volumen_pct_por_ano,
        wacc_anual=wacc,
    )


def _percentil(valores: list[float], p: float) -> float | None:
    """Percentil p (0..100) de una lista. Devuelve None si lista vacía."""
    if not valores:
        return None
    s = sorted(valores)
    idx = int(round(len(s) * (p / 100)))
    idx = min(len(s) - 1, max(0, idx))
    return s[idx]


def _histograma(valores: list[float], bins: int = 50) -> list[dict]:
    """Histograma compacto: lista de {bin_start, bin_end, count, fraction}."""
    if not valores:
        return []
    lo = min(valores)
    hi = max(valores)
    if hi <= lo:
        return [{"bin_start": lo, "bin_end": hi, "count": len(valores), "fraction": 1.0}]
    width = (hi - lo) / bins
    cuentas = [0] * bins
    for v in valores:
        i = min(bins - 1, int((v - lo) / width))
        cuentas[i] += 1
    n = len(valores)
    return [
        {
            "bin_start": lo + i * width,
            "bin_end": lo + (i + 1) * width,
            "count": c,
            "fraction": c / n,
        }
        for i, c in enumerate(cuentas)
    ]


def run_monte_carlo(
    base_params: ParametrosPlan | None = None,
    n_runs: int = 10_000,
    seed: int = 42,
) -> MonteCarloResult:
    base = base_params or ParametrosPlan()
    rng = random.Random(seed)

    tirs: list[float] = []
    vans: list[float] = []
    paybacks: list[int] = []
    waccs_sample: list[float] = []

    for _ in range(n_runs):
        params = _sample_params(base, rng)
        waccs_sample.append(params.wacc_anual)
        plan = build_plan(params)
        if plan.kpis.tir_proyecto_anual is not None:
            tirs.append(plan.kpis.tir_proyecto_anual)
        vans.append(plan.kpis.van)
        if plan.kpis.payback_meses is not None:
            paybacks.append(plan.kpis.payback_meses)

    tir_supera_wacc = (
        sum(1 for t, w in zip(tirs, waccs_sample[: len(tirs)]) if t > w) / len(tirs)
        if tirs
        else 0.0
    )
    van_positivo = sum(1 for v in vans if v > 0) / len(vans) if vans else 0.0

    return MonteCarloResult(
        n_runs=n_runs,
        tir_p5=_percentil(tirs, 5),
        tir_p50=_percentil(tirs, 50),
        tir_p95=_percentil(tirs, 95),
        van_p5=_percentil(vans, 5) or 0.0,
        van_p50=_percentil(vans, 50) or 0.0,
        van_p95=_percentil(vans, 95) or 0.0,
        payback_p50=int(_percentil(paybacks, 50)) if paybacks else None,
        prob_tir_supera_wacc=tir_supera_wacc,
        prob_van_positivo=van_positivo,
        histograma_tir=_histograma(tirs, bins=40),
        seed=seed,
    )
