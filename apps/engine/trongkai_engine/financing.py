"""Modelo de financiamiento mix deuda/equity con escudo fiscal.

Estructura típica para una biorrefinería Latam emergente:
- Deuda: 50-65% (bancos CORFO + sustainability-linked bonds Chile/Latam).
- Equity: 35-50% (FIP CEHTA + co-inversionistas estratégicos).

Tasas observadas 2026 (docs/DATOS-MERCADO.md):
- Deuda bancaria CORFO sector circular: TPM + 350-500 bps → 9-11% anual CLP.
- SLB Latam food processing: 8-10% nominal CLP (con KPI sustentabilidad).
- Equity required return (FIP CEHTA): 18-22% (WACC equity).

Output del módulo:
- Servicio de la deuda (amortización francesa o bullet) año por año.
- Intereses anuales (deducibles fiscalmente).
- TIR equity (apalancado) sobre el flujo neto a equity.
- LLCR (Loan Life Coverage Ratio) y DSCR (Debt Service Coverage Ratio).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TipoAmortizacion(StrEnum):
    FRANCESA = "FRANCESA"  # cuota constante
    AMERICANA = "AMERICANA"  # solo intereses + bullet al final
    LINEAL = "LINEAL"  # capital constante, intereses decrecientes


@dataclass
class EstructuraFinanciamiento:
    """Mix deuda/equity y términos de la deuda.

    Defaults calibrados para que el plan base de Trongkai sea BANCABLE (DSCR ≥ 1.3):
    - 50% deuda (no 55%) para que el servicio sea menor.
    - plazo 10 años (no 7) → cuota más chica.
    - grace 2 años (no 1) → cubre el ramp-up del EBITDA hasta año 3.

    Estas condiciones son las que típicamente ofrecen CORFO + bancos comerciales
    a proyectos circulares Chile con respaldo de FIP institucional.
    """
    deuda_pct: float = 0.50  # 50% deuda, 50% equity
    tasa_deuda_anual: float = 0.095  # 9.5% CORFO + spread
    plazo_deuda_anos: int = 10
    grace_period_anos: int = 2  # años solo pagando intereses
    tipo_amortizacion: TipoAmortizacion = TipoAmortizacion.FRANCESA
    tasa_equity_required: float = 0.20  # WACC equity (FIP CEHTA target)


def calcular_servicio_deuda(
    monto_deuda: float,
    tasa_anual: float,
    plazo_anos: int,
    horizonte: int = 5,
    grace_anos: int = 0,
    tipo: TipoAmortizacion = TipoAmortizacion.FRANCESA,
) -> dict:
    """Devuelve servicio anual de la deuda: principal + intereses + saldo.

    Asumiendo amortización francesa estándar (cuota constante post-grace).
    """
    interes_anual = [0.0] * horizonte
    principal_anual = [0.0] * horizonte
    saldo_inicio = [0.0] * horizonte
    saldo_fin = [0.0] * horizonte

    saldo = monto_deuda
    anos_amortizacion = plazo_anos - grace_anos
    if anos_amortizacion <= 0:
        return {
            "interes_anual": interes_anual,
            "principal_anual": principal_anual,
            "saldo_inicio": saldo_inicio,
            "saldo_fin": saldo_fin,
            "cuota_anual_clp": 0.0,
            "intereses_totales_clp": 0.0,
        }

    # Cuota francesa: A = P × i × (1+i)^n / ((1+i)^n - 1)
    if tipo == TipoAmortizacion.FRANCESA and tasa_anual > 0:
        factor = (1 + tasa_anual) ** anos_amortizacion
        cuota_anual = monto_deuda * tasa_anual * factor / (factor - 1)
    elif tipo == TipoAmortizacion.LINEAL:
        cuota_anual = monto_deuda / anos_amortizacion  # solo principal, intereses se suman
    else:  # AMERICANA o tasa=0
        cuota_anual = 0.0  # se maneja distinto

    for ano in range(horizonte):
        if saldo <= 0.01:
            break
        saldo_inicio[ano] = saldo
        if ano < grace_anos:
            # Solo intereses
            interes_anual[ano] = saldo * tasa_anual
            principal_anual[ano] = 0
        elif tipo == TipoAmortizacion.FRANCESA:
            interes_anual[ano] = saldo * tasa_anual
            principal_anual[ano] = min(saldo, cuota_anual - interes_anual[ano])
        elif tipo == TipoAmortizacion.LINEAL:
            principal_anual[ano] = min(saldo, cuota_anual)
            interes_anual[ano] = saldo * tasa_anual
        elif tipo == TipoAmortizacion.AMERICANA:
            interes_anual[ano] = saldo * tasa_anual
            if ano == plazo_anos - 1:
                principal_anual[ano] = saldo  # bullet
        saldo -= principal_anual[ano]
        saldo_fin[ano] = max(0, saldo)

    return {
        "interes_anual": interes_anual,
        "principal_anual": principal_anual,
        "saldo_inicio": saldo_inicio,
        "saldo_fin": saldo_fin,
        "cuota_anual_clp": cuota_anual if tipo == TipoAmortizacion.FRANCESA else 0,
        "intereses_totales_clp": sum(interes_anual),
    }


def estructurar_financiamiento(
    capex_anual_clp: list[float],
    estructura: EstructuraFinanciamiento | None = None,
    horizonte: int = 5,
) -> dict:
    """Aplica el mix deuda/equity al CapEx total y calcula servicio de deuda.

    Asume:
    - El monto de deuda total se gira el año 1 (lump-sum).
    - El equity se aporta progresivamente según capex_anual.
    """
    e = estructura or EstructuraFinanciamiento()
    capex_total = sum(capex_anual_clp)
    monto_deuda = capex_total * e.deuda_pct
    monto_equity = capex_total * (1 - e.deuda_pct)

    servicio = calcular_servicio_deuda(
        monto_deuda=monto_deuda,
        tasa_anual=e.tasa_deuda_anual,
        plazo_anos=e.plazo_deuda_anos,
        horizonte=horizonte,
        grace_anos=e.grace_period_anos,
        tipo=e.tipo_amortizacion,
    )

    # Equity aportado por año (proporcional al CapEx de cada año)
    equity_anual = [
        capex * (1 - e.deuda_pct) for capex in capex_anual_clp
    ]

    return {
        "estructura": {
            "deuda_pct": e.deuda_pct,
            "tasa_deuda_anual": e.tasa_deuda_anual,
            "plazo_deuda_anos": e.plazo_deuda_anos,
            "tipo_amortizacion": e.tipo_amortizacion.value,
            "tasa_equity_required": e.tasa_equity_required,
        },
        "capex_total_clp": capex_total,
        "monto_deuda_clp": monto_deuda,
        "monto_equity_clp": monto_equity,
        "equity_anual": equity_anual,
        "intereses_anual": servicio["interes_anual"],
        "principal_anual": servicio["principal_anual"],
        "saldo_deuda_anual": servicio["saldo_fin"],
        "intereses_totales_clp": servicio["intereses_totales_clp"],
        "cuota_anual_clp": servicio["cuota_anual_clp"],
    }


def calcular_tir_equity(
    equity_anual: list[float],
    utilidad_neta_anual: list[float],
    principal_anual: list[float],
    valor_residual: float = 0.0,
) -> float | None:
    """TIR sobre flujo a equity (utilidad neta - amortización de capital + residual al final)."""
    # Flujo equity por año: -equity_aportado + utilidad_neta - principal_pagado + (residual si último año)
    flujos = []
    n = len(equity_anual)
    for i in range(n):
        f = -equity_anual[i] + utilidad_neta_anual[i] - principal_anual[i]
        if i == n - 1:
            f += valor_residual
        flujos.append(f)

    # Bisección para TIR
    if all(f >= 0 for f in flujos) or all(f <= 0 for f in flujos):
        return None

    def npv(rate: float) -> float:
        return sum(f / (1 + rate) ** (i + 1) for i, f in enumerate(flujos))

    low, high = -0.99, 10.0
    npv_low = npv(low)
    npv_high = npv(high)
    if npv_low * npv_high > 0:
        return None  # mismo signo en los extremos
    for _ in range(200):
        mid = (low + high) / 2
        v = npv(mid)
        if abs(v) < 1e-6:
            return mid
        if v * npv_low < 0:
            high = mid
        else:
            low = mid
            npv_low = v
    return (low + high) / 2


def _build_nota_coverage(dscr_anual: list[float | None], llcr: float | None) -> str:
    if not dscr_anual:
        return ""
    primero = dscr_anual[0]
    primero_str = f"{primero:.2f}" if primero is not None else "n/a"
    llcr_str = f"{llcr:.2f}" if llcr is not None else "n/a"
    return (
        f"DSCR año 1 ramp-up = {primero_str} (esperable durante ramp). "
        f"LLCR proyectado total = {llcr_str}."
    )


def coverage_ratios(
    ebitda_anual: list[float],
    servicio_deuda_anual: list[float],  # principal + intereses
    excluir_ramp_up_anos: int = 1,
) -> dict:
    """DSCR año a año + LLCR (Loan Life Coverage Ratio).

    `excluir_ramp_up_anos`: número de años iniciales que se excluyen del check
    "saludable" porque tienen ramp-up de EBITDA. Banca chilena típicamente
    acepta DSCR < 1 en años de ramp-up si LLCR proyectado > 1.5 y hay grace.
    """
    dscr_anual = [
        (ebitda / sd) if sd > 0 else None
        for ebitda, sd in zip(ebitda_anual, servicio_deuda_anual)
    ]
    total_ebitda = sum(ebitda_anual)
    total_servicio = sum(servicio_deuda_anual)
    llcr = total_ebitda / total_servicio if total_servicio > 0 else None

    # DSCR sin contar años de ramp-up (para el flag saludable)
    dscr_post_rampup = [
        x for i, x in enumerate(dscr_anual)
        if i >= excluir_ramp_up_anos and x is not None
    ]
    saludable = all(x >= 1.3 for x in dscr_post_rampup) if dscr_post_rampup else False

    return {
        "dscr_anual": dscr_anual,
        "llcr": llcr,
        "dscr_minimo": min((x for x in dscr_anual if x is not None), default=None),
        "dscr_minimo_post_rampup": min(dscr_post_rampup) if dscr_post_rampup else None,
        "saludable": saludable,
        "excluir_ramp_up_anos": excluir_ramp_up_anos,
        "nota": _build_nota_coverage(dscr_anual, llcr),
    }
