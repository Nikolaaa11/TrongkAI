"""Break-even analysis — encuentra el shock máximo soportable por cada driver.

Para cada driver (precio, costo_mmpp, wacc, opex), busca por bisección el
shock que hace TIR = WACC (umbral de rechazo del proyecto).

Ejemplo: si precio_breakeven = -0.18, significa que el proyecto soporta
hasta una caída de 18% en precios antes de no superar el costo de capital.
Cuanto más grande el "colchón", más robusto el proyecto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .plan_builder import ParametrosPlan, build_plan
from .sensitivity import _aplicar_shock

Driver = Literal["precio", "costo_mmpp", "wacc", "opex"]


@dataclass
class BreakevenResultado:
    """Resultado del análisis break-even para un driver."""
    driver: Driver
    shock_breakeven: float | None  # Shock que hace TIR = umbral. None si no se encuentra.
    colchon_pct: float | None       # Magnitud absoluta del colchón (sin signo)
    tir_base: float | None
    umbral_tir: float
    direccion: str                   # "bajada" (precio) o "subida" (costo)
    iteraciones: int

    def to_dict(self) -> dict:
        return {
            "driver": self.driver,
            "shock_breakeven": self.shock_breakeven,
            "colchon_pct": self.colchon_pct,
            "tir_base": self.tir_base,
            "umbral_tir": self.umbral_tir,
            "direccion": self.direccion,
            "iteraciones": self.iteraciones,
        }


@dataclass
class BreakevenSummary:
    """Resumen completo: break-even por driver + métricas globales."""
    resultados: list[BreakevenResultado] = field(default_factory=list)
    umbral_tir_aplicado: float = 0.18

    def to_dict(self) -> dict:
        return {
            "umbral_tir_aplicado": self.umbral_tir_aplicado,
            "resultados": [r.to_dict() for r in self.resultados],
            "driver_mas_sensible": (
                min(
                    [r for r in self.resultados if r.colchon_pct is not None],
                    key=lambda r: r.colchon_pct or float("inf"),
                ).driver
                if any(r.colchon_pct is not None for r in self.resultados)
                else None
            ),
        }


def _tir_con_shock(base: ParametrosPlan, driver: Driver, shock: float) -> float | None:
    """Calcula la TIR del plan con el shock aplicado."""
    params = _aplicar_shock(base, driver, shock)
    try:
        plan = build_plan(params)
        return plan.kpis.tir_proyecto_anual
    except Exception:
        return None


def breakeven_un_driver(
    driver: Driver,
    direccion: str,
    umbral_tir: float,
    base_params: ParametrosPlan | None = None,
    max_iter: int = 30,
    tolerancia: float = 0.001,
) -> BreakevenResultado:
    """Encuentra por bisección el shock que hace TIR = umbral_tir.

    Args:
        driver: variable a sensibilizar
        direccion: "bajada" (busca shock negativo, ej precio) o "subida" (positivo, ej costo)
        umbral_tir: TIR objetivo (default WACC 18%)
        max_iter: iteraciones máximas de bisección
        tolerancia: precisión TIR (1pp por default)
    """
    base = base_params or ParametrosPlan()
    tir_base = _tir_con_shock(base, driver, 0.0)

    if tir_base is None or tir_base < umbral_tir:
        # Ya estamos por debajo del umbral con shock 0
        return BreakevenResultado(
            driver=driver,
            shock_breakeven=0.0,
            colchon_pct=0.0,
            tir_base=tir_base,
            umbral_tir=umbral_tir,
            direccion=direccion,
            iteraciones=0,
        )

    # Caso especial WACC: TIR del proyecto es independiente del WACC (es intrínseca al flujo).
    # El "break-even WACC" es simplemente TIR_base - umbral, expresado como subida absoluta del WACC.
    # WACC máximo soportable = TIR_base (con cualquier umbral).
    if driver == "wacc":
        if direccion == "bajada":
            return BreakevenResultado(
                driver=driver, shock_breakeven=None, colchon_pct=None,
                tir_base=tir_base, umbral_tir=umbral_tir, direccion=direccion,
                iteraciones=0,
            )
        # subida: cuántos pp puede subir el WACC antes de que TIR <= WACC
        # WACC_max_soportable = TIR_base; shock_breakeven = TIR_base - WACC_actual
        base_wacc = (base_params or ParametrosPlan()).wacc_anual
        shock_be = tir_base - base_wacc
        return BreakevenResultado(
            driver=driver,
            shock_breakeven=round(shock_be, 4),
            colchon_pct=abs(shock_be),
            tir_base=tir_base,
            umbral_tir=umbral_tir,
            direccion=direccion,
            iteraciones=1,
        )

    # Rangos según dirección
    if direccion == "bajada":
        lo, hi = -0.99, 0.0  # bajada extrema vs base
    elif direccion == "subida":
        lo, hi = 0.0, 5.0  # hasta +500% subida (extremo)
    else:
        raise ValueError(f"direccion debe ser 'bajada' o 'subida', no {direccion}")

    # Verificar que en el extremo el TIR sí cae bajo el umbral
    tir_extremo = _tir_con_shock(base, driver, lo if direccion == "bajada" else hi)
    if tir_extremo is not None and tir_extremo >= umbral_tir:
        # El proyecto soporta el extremo. No hay break-even en este rango.
        return BreakevenResultado(
            driver=driver, shock_breakeven=None, colchon_pct=None,
            tir_base=tir_base, umbral_tir=umbral_tir, direccion=direccion,
            iteraciones=0,
        )

    # Bisección estándar
    iteraciones = 0
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        tir_mid = _tir_con_shock(base, driver, mid)
        iteraciones += 1
        if tir_mid is None:
            # No converge — abortar
            break
        if abs(tir_mid - umbral_tir) < tolerancia:
            break
        # Si TIR > umbral, el shock es muy suave: empujar hacia el extremo
        if tir_mid > umbral_tir:
            if direccion == "bajada":
                hi = mid
            else:
                lo = mid
        else:
            if direccion == "bajada":
                lo = mid
            else:
                hi = mid

    shock_be = (lo + hi) / 2
    return BreakevenResultado(
        driver=driver,
        shock_breakeven=round(shock_be, 4),
        colchon_pct=abs(shock_be),
        tir_base=tir_base,
        umbral_tir=umbral_tir,
        direccion=direccion,
        iteraciones=iteraciones,
    )


# Pares (driver, direccion) que tienen sentido económico:
DRIVERS_BREAKEVEN: list[tuple[Driver, str]] = [
    ("precio", "bajada"),       # ¿cuánto puede caer el precio?
    ("costo_mmpp", "subida"),   # ¿cuánto puede subir el costo MMPP?
    ("wacc", "subida"),         # ¿cuánto puede subir el WACC (banca dura)?
    ("opex", "subida"),         # ¿cuánto puede subir el OpEx?
]


def breakeven_summary(
    umbral_tir: float = 0.18,
    base_params: ParametrosPlan | None = None,
) -> BreakevenSummary:
    """Corre break-even para los 4 drivers principales y devuelve resumen."""
    resultados = [
        breakeven_un_driver(d, direccion, umbral_tir, base_params)
        for d, direccion in DRIVERS_BREAKEVEN
    ]
    return BreakevenSummary(
        resultados=resultados,
        umbral_tir_aplicado=umbral_tir,
    )
