"""Balance Integrado — combina los 4 balances + cross-checks.

Score de eficiencia global 0-100 ponderando:
- closure de cada balance      (40 pts)
- alarmas criticas activas     (30 pts)  - mas alarmas = menos score
- KPIs vs benchmarks           (30 pts)

Cross-checks que NINGUN balance individual valida:
- Producto vs HH disponibles    -> alarma si plan > capacidad HH
- Producto vs Energia            -> ratio fuera de banda
- Energia vs Agua (vapor)        -> caldera sin agua
- Turno noche con HH suficiente
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .agua import BalanceAgua, computar_balance_agua
from .energia import BalanceEnergia, computar_balance_energia
from .rrhh import BalanceRRHH, computar_balance_rrhh


@dataclass
class BalanceIntegrado:
    producto: dict
    energia: dict
    agua: dict
    rrhh: dict
    intensidades: dict           # kpis por kg producto
    costos_consolidados: dict
    alarmas_consolidadas: list[dict] = field(default_factory=list)
    score_eficiencia_global: float = 0.0
    coherencia_cross_balance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "producto": self.producto,
            "energia": self.energia,
            "agua": self.agua,
            "rrhh": self.rrhh,
            "intensidades": self.intensidades,
            "costos_consolidados": self.costos_consolidados,
            "alarmas_consolidadas": self.alarmas_consolidadas,
            "score_eficiencia_global": round(self.score_eficiencia_global, 2),
            "coherencia_cross_balance": self.coherencia_cross_balance,
        }


def _cross_checks(
    energia: BalanceEnergia,
    agua: BalanceAgua,
    rrhh: BalanceRRHH,
    produccion_anual_kg: float,
    hh_requeridas_por_kg: float = 0.06,
) -> tuple[list[dict], dict]:
    """Valida coherencia entre los 4 balances.

    Returns: (alarmas_cross, resumen_coherencia)
    """
    alarmas: list[dict] = []
    resumen = {}

    # 1. Producto vs HH disponibles (anual)
    hh_disponibles_anuales = rrhh.total_horas_disponibles_sem * 52
    hh_necesarias = produccion_anual_kg * hh_requeridas_por_kg
    ratio_hh = hh_necesarias / hh_disponibles_anuales if hh_disponibles_anuales > 0 else 0
    resumen["producto_vs_hh"] = {
        "hh_necesarias_anuales": round(hh_necesarias, 0),
        "hh_disponibles_anuales": round(hh_disponibles_anuales, 0),
        "ratio_necesarias_vs_disponibles": round(ratio_hh, 3),
        "ok": ratio_hh <= 1.0,
    }
    if ratio_hh > 1.0:
        alarmas.append({
            "tipo": "cross_producto_hh",
            "severidad": "alta",
            "mensaje": (
                f"Plan produccion necesita {hh_necesarias:,.0f} HH/año "
                f"pero solo hay {hh_disponibles_anuales:,.0f} HH disponibles "
                f"({ratio_hh:.1%}). Contratar o aumentar turnos."
            ),
        })

    # 2. Producto vs Energia
    intensidad_real = (energia.consumo_total_anual_mwh * 1000.0) / produccion_anual_kg
    benchmark_min, benchmark_max = 2.0, 5.0
    resumen["producto_vs_energia"] = {
        "intensidad_kwh_kg": round(intensidad_real, 3),
        "rango_esperado": [benchmark_min, benchmark_max],
        "ok": benchmark_min <= intensidad_real <= benchmark_max,
    }
    if intensidad_real > benchmark_max:
        alarmas.append({
            "tipo": "cross_producto_energia",
            "severidad": "media",
            "mensaje": (
                f"Intensidad energetica {intensidad_real:.2f} kWh/kg fuera del rango "
                f"[{benchmark_min}-{benchmark_max}]. Auditar equipos sobre-consumidores."
            ),
        })
    elif intensidad_real < benchmark_min:
        alarmas.append({
            "tipo": "cross_producto_energia",
            "severidad": "baja",
            "mensaje": (
                f"Intensidad energetica {intensidad_real:.2f} kWh/kg INFERIOR a rango. "
                "Verificar si la produccion reportada es real."
            ),
        })

    # 3. Energia vapor vs Agua para caldera
    energia_vapor_mwh = sum(
        f.consumo_anual_kwh / 1000.0 for f in energia.flujos if f.tipo == "vapor"
    )
    energia_biomasa_mwh = sum(
        f.consumo_anual_kwh / 1000.0 for f in energia.flujos if f.tipo == "biomasa"
    )
    agua_vapor_m3 = sum(
        f.volumen_anual_m3 for f in agua.flujos if f.uso == "vapor"
    )
    # Heuristic: 1 m3 agua ≈ 700 kWh vapor (calor latente aproximado)
    vapor_kwh_esperado = agua_vapor_m3 * 700.0
    vapor_kwh_real = (energia_vapor_mwh + energia_biomasa_mwh) * 1000.0
    ratio_vapor = vapor_kwh_real / max(vapor_kwh_esperado, 1e-6)
    resumen["energia_vs_agua_vapor"] = {
        "agua_vapor_m3": round(agua_vapor_m3, 1),
        "vapor_kwh_esperado": round(vapor_kwh_esperado, 0),
        "vapor_kwh_real": round(vapor_kwh_real, 0),
        "ratio": round(ratio_vapor, 3),
        "ok": 0.5 <= ratio_vapor <= 2.0,
    }
    if not (0.5 <= ratio_vapor <= 2.0):
        alarmas.append({
            "tipo": "cross_energia_agua",
            "severidad": "media",
            "mensaje": (
                f"Mismatch vapor/agua: vapor real {vapor_kwh_real:,.0f} kWh vs "
                f"esperado {vapor_kwh_esperado:,.0f} kWh (ratio {ratio_vapor:.2f}). "
                "Caldera puede tener fuga o medidor descalibrado."
            ),
        })

    # 4. Turno noche con HH minima
    operarios_noche = sum(
        1 for t in rrhh.trabajadores if t.activo and t.turno == "noche"
    )
    resumen["turno_noche"] = {
        "operarios": operarios_noche,
        "minimo_recomendado": 2,
        "ok": operarios_noche >= 2,
    }
    if operarios_noche < 2:
        alarmas.append({
            "tipo": "cross_turno_noche",
            "severidad": "alta",
            "mensaje": (
                f"Solo {operarios_noche} trabajadores en turno noche. "
                "Riesgo operacional + violacion proteccion laboral (operacion solo)."
            ),
        })

    return alarmas, resumen


def _score_global(
    energia: BalanceEnergia,
    agua: BalanceAgua,
    rrhh: BalanceRRHH,
    alarmas_cross: list[dict],
) -> float:
    """Score 0-100. Mayor es mejor."""
    score = 0.0

    # 40 pts: closure (10 pts c/u, max 40 si los 4 cierran)
    # mass balance se asume cerrado (validado por su propio modulo)
    score += 10.0  # producto
    score += 10.0 if energia.closure_pct <= 2.0 else max(0, 10 - energia.closure_pct)
    score += 10.0 if agua.closure_pct <= 1.0 else max(0, 10 - agua.closure_pct * 2)
    score += 10.0 if rrhh.closure_pct <= 1.0 else max(0, 10 - rrhh.closure_pct)

    # 30 pts: alarmas (deduce 5 por critica, 2 por alta, 1 por media)
    todas_alarmas = energia.alarmas + agua.alarmas + rrhh.alarmas + alarmas_cross
    deduccion = 0.0
    for a in todas_alarmas:
        sev = a.get("severidad", "media")
        if sev == "critica":
            deduccion += 5
        elif sev == "alta":
            deduccion += 2
        else:
            deduccion += 1
    score += max(0.0, 30.0 - deduccion)

    # 30 pts: KPIs vs benchmarks
    # mix renovable 30 → 5 pts
    if energia.mix_renovable_pct >= 0.30:
        score += 5
    elif energia.mix_renovable_pct >= 0.15:
        score += 3
    # FP > 0.92 → 5 pts
    if energia.factor_potencia_planta >= 0.95:
        score += 5
    elif energia.factor_potencia_planta >= 0.92:
        score += 3
    # recirculacion agua > 30 → 5 pts
    if agua.agua_recirculada_pct >= 0.30:
        score += 5
    elif agua.agua_recirculada_pct >= 0.15:
        score += 3
    # productividad > 25 → 5 pts
    if rrhh.productividad_kg_por_hh >= 25.0:
        score += 5
    elif rrhh.productividad_kg_por_hh >= 15.0:
        score += 3
    # utilizacion HH 70-95% → 5 pts
    if 0.70 <= rrhh.utilizacion_pct <= 0.95:
        score += 5
    elif 0.50 <= rrhh.utilizacion_pct <= 1.0:
        score += 3
    # rotacion < 20% → 5 pts
    if rrhh.rotacion_anual_pct <= 0.20:
        score += 5
    elif rrhh.rotacion_anual_pct <= 0.30:
        score += 3

    return min(100.0, max(0.0, score))


def computar_balance_integrado(
    produccion_anual_kg: float = 850_000.0,
) -> BalanceIntegrado:
    """Computa los 4 balances y los integra con cross-checks + score."""
    energia = computar_balance_energia(produccion_anual_kg=produccion_anual_kg)
    agua = computar_balance_agua(produccion_anual_kg=produccion_anual_kg)
    rrhh = computar_balance_rrhh(
        produccion_semanal_kg=produccion_anual_kg / 52.0,
    )

    alarmas_cross, coherencia = _cross_checks(energia, agua, rrhh, produccion_anual_kg)

    # Mass balance: usamos un resumen ligero
    producto_dict = {
        "produccion_anual_kg": produccion_anual_kg,
        "closure_pct": 0.3,  # promedio observado del mass_balance
        "fuente": "mass_balance.py (modulo separado)",
        "alarmas": [],
    }

    # Intensidades consolidadas (por kg producto)
    intensidades = {
        "energia_kwh_kg": round(
            (energia.consumo_total_anual_mwh * 1000.0) / produccion_anual_kg, 3
        ),
        "agua_l_kg": round(
            agua.consumo_total_anual_m3 * 1000.0 / produccion_anual_kg, 2
        ),
        "hh_kg": round(
            rrhh.total_horas_disponibles_sem * 52 / produccion_anual_kg, 4
        ),
        "costo_energia_usd_kg": round(
            energia.costo_total_anual_usd / produccion_anual_kg, 4
        ),
        "costo_agua_usd_kg": round(
            agua.costo_total_anual_usd / produccion_anual_kg, 4
        ),
        "costo_rrhh_usd_kg": round(
            rrhh.costo_total_mensual_clp * 12 / 900.0 / produccion_anual_kg, 4
        ),  # 900 CLP/USD aproximado
    }

    costos = {
        "energia_anual_usd": round(energia.costo_total_anual_usd, 2),
        "agua_anual_usd": round(agua.costo_total_anual_usd, 2),
        "rrhh_anual_usd": round(rrhh.costo_total_mensual_clp * 12 / 900.0, 2),
        "total_operacional_anual_usd": round(
            energia.costo_total_anual_usd
            + agua.costo_total_anual_usd
            + (rrhh.costo_total_mensual_clp * 12 / 900.0),
            2,
        ),
    }

    alarmas_todas = (
        [{"balance": "energia", **a} for a in energia.alarmas]
        + [{"balance": "agua", **a} for a in agua.alarmas]
        + [{"balance": "rrhh", **a} for a in rrhh.alarmas]
        + [{"balance": "integrado", **a} for a in alarmas_cross]
    )

    score = _score_global(energia, agua, rrhh, alarmas_cross)

    return BalanceIntegrado(
        producto=producto_dict,
        energia=energia.to_dict(),
        agua=agua.to_dict(),
        rrhh=rrhh.to_dict(),
        intensidades=intensidades,
        costos_consolidados=costos,
        alarmas_consolidadas=alarmas_todas,
        score_eficiencia_global=score,
        coherencia_cross_balance=coherencia,
    )
