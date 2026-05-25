"""Sensitivity heatmap 2D — análisis cross-variables.

Calcula una matriz NxN de TIR para combinaciones de dos drivers simultáneos.
Útil para comité de inversión: muestra "zonas seguras" donde TIR > hurdle.

Driver pairs soportados:
- precio × costo_mmpp   (clásico — más usado)
- precio × wacc
- precio × opex
- costo_mmpp × wacc

Para evitar tiempos de cálculo absurdos, el grid default es 7x7 = 49 simulaciones.
Cada celda corre `build_plan` completo (~150ms) → total ~7s aceptable como endpoint
cacheado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .plan_builder import ParametrosPlan, build_plan, precio_referencia_dict

Driver = Literal["precio", "costo_mmpp", "wacc", "opex"]


@dataclass
class HeatmapCelda:
    """Una celda del heatmap."""
    eje_x_pct: float          # shock en eje X (-0.25, ..., +0.25)
    eje_y_pct: float          # shock en eje Y
    tir: float | None         # TIR resultante
    van_clp: float            # VAN absoluto
    supera_hurdle: bool       # TIR > hurdle_pct


@dataclass
class HeatmapResultado:
    """Resultado completo del heatmap 2D."""
    driver_x: Driver
    driver_y: Driver
    rango_x: list[float] = field(default_factory=list)  # shocks evaluados eje X
    rango_y: list[float] = field(default_factory=list)
    celdas: list[HeatmapCelda] = field(default_factory=list)
    tir_base: float | None = None
    van_base: float = 0.0
    hurdle_pct: float = 0.15
    n_celdas_seguras: int = 0
    n_celdas_totales: int = 0

    @property
    def pct_zona_segura(self) -> float:
        if self.n_celdas_totales == 0:
            return 0.0
        return self.n_celdas_seguras / self.n_celdas_totales

    def to_dict(self) -> dict:
        return {
            "driver_x": self.driver_x,
            "driver_y": self.driver_y,
            "rango_x": self.rango_x,
            "rango_y": self.rango_y,
            "tir_base": self.tir_base,
            "van_base": self.van_base,
            "hurdle_pct": self.hurdle_pct,
            "n_celdas_seguras": self.n_celdas_seguras,
            "n_celdas_totales": self.n_celdas_totales,
            "pct_zona_segura": self.pct_zona_segura,
            "celdas": [
                {
                    "x_pct": c.eje_x_pct,
                    "y_pct": c.eje_y_pct,
                    "tir": c.tir,
                    "van_clp": c.van_clp,
                    "supera_hurdle": c.supera_hurdle,
                }
                for c in self.celdas
            ],
        }


def _aplicar_shock(
    base: ParametrosPlan, driver: Driver, shock: float
) -> ParametrosPlan:
    """Devuelve un ParametrosPlan con el shock aplicado al driver indicado."""
    if driver == "precio":
        precios_base = base.precios_clp_kg if base.precios_clp_kg else precio_referencia_dict()
        nuevos_precios = {k: v * (1 + shock) for k, v in precios_base.items()}
        # Reconstruir respetando todos los demás atributos del original.
        from dataclasses import replace
        return replace(base, precios_clp_kg=nuevos_precios)
    if driver == "costo_mmpp":
        from dataclasses import replace
        return replace(base, costo_mmpp_clp_kg=base.costo_mmpp_clp_kg * (1 + shock))
    if driver == "wacc":
        from dataclasses import replace
        # WACC: shock en pp absolutos (no relativo). +0.05 = +500 bps.
        return replace(base, wacc_anual=base.wacc_anual + shock)
    if driver == "opex":
        from dataclasses import replace
        return replace(base, opex_mensual_clp=base.opex_mensual_clp * (1 + shock))
    raise ValueError(f"driver desconocido: {driver}")


def _rango_default(driver: Driver, n: int) -> list[float]:
    """Rango de shocks default según driver."""
    if driver == "wacc":
        # WACC: -0.04 a +0.05 (en pp absolutos) — incluye escenario realista de subir tasa
        paso = 0.09 / (n - 1)
        return [round(-0.04 + i * paso, 4) for i in range(n)]
    # precio, costo_mmpp, opex: -25% a +25%
    paso = 0.50 / (n - 1)
    return [round(-0.25 + i * paso, 4) for i in range(n)]


@dataclass
class PuntoCurva:
    shock: float
    tir: float | None
    van_clp: float


@dataclass
class CurvaSensibilidad:
    driver: Driver
    puntos: list[PuntoCurva] = field(default_factory=list)
    tir_base: float | None = None

    def to_dict(self) -> dict:
        return {
            "driver": self.driver,
            "tir_base": self.tir_base,
            "puntos": [
                {"shock": p.shock, "tir": p.tir, "van_clp": p.van_clp}
                for p in self.puntos
            ],
        }


def curva_1d(
    driver: Driver,
    n: int = 11,
    base_params: ParametrosPlan | None = None,
) -> CurvaSensibilidad:
    """Genera una curva 1D TIR vs shock para un driver dado.

    Útil para small-multiples visual de los 4 drivers.
    """
    if n < 3 or n > 25:
        raise ValueError("n debe estar entre 3 y 25")

    base = base_params or ParametrosPlan()
    plan_base = build_plan(base)
    rango = _rango_default(driver, n)

    puntos: list[PuntoCurva] = []
    for shock in rango:
        params = _aplicar_shock(base, driver, shock)
        try:
            plan = build_plan(params)
            puntos.append(
                PuntoCurva(shock=shock, tir=plan.kpis.tir_proyecto_anual, van_clp=plan.kpis.van)
            )
        except Exception:
            puntos.append(PuntoCurva(shock=shock, tir=None, van_clp=0.0))

    return CurvaSensibilidad(
        driver=driver,
        puntos=puntos,
        tir_base=plan_base.kpis.tir_proyecto_anual,
    )


def curvas_todos_drivers(
    n: int = 11,
    base_params: ParametrosPlan | None = None,
) -> dict:
    """Devuelve las 4 curvas 1D en un solo dict para el endpoint /sensitivity/curves."""
    drivers: list[Driver] = ["precio", "costo_mmpp", "wacc", "opex"]
    return {
        "n": n,
        "curvas": [
            curva_1d(d, n=n, base_params=base_params).to_dict() for d in drivers
        ],
    }


@dataclass
class Sensitivity3DResult:
    driver_x: Driver
    driver_y: Driver
    driver_z: Driver
    rango_x: list[float]
    rango_y: list[float]
    rango_z: list[float]
    puntos: list[dict]  # [{x_pct, y_pct, z_pct, tir, supera_hurdle}]
    tir_base: float | None
    hurdle_pct: float
    pct_zona_segura: float

    def to_dict(self) -> dict:
        return {
            "driver_x": self.driver_x,
            "driver_y": self.driver_y,
            "driver_z": self.driver_z,
            "rango_x": self.rango_x,
            "rango_y": self.rango_y,
            "rango_z": self.rango_z,
            "puntos": self.puntos,
            "tir_base": self.tir_base,
            "hurdle_pct": self.hurdle_pct,
            "pct_zona_segura": self.pct_zona_segura,
            "n_puntos": len(self.puntos),
        }


def heatmap_3d(
    driver_x: Driver = "precio",
    driver_y: Driver = "costo_mmpp",
    driver_z: Driver = "wacc",
    n: int = 5,
    hurdle_pct: float = 0.15,
    base_params: ParametrosPlan | None = None,
) -> Sensitivity3DResult:
    """Heatmap 3D: TIR para todas las combinaciones de 3 drivers.

    Default 5x5x5 = 125 simulaciones (~8 segundos). Útil para identificar
    'regiones seguras' multidimensionales.
    """
    if len({driver_x, driver_y, driver_z}) != 3:
        raise ValueError("driver_x, driver_y, driver_z deben ser distintos")
    if n < 3 or n > 10:
        raise ValueError("n debe estar entre 3 y 10")

    base = base_params or ParametrosPlan()
    plan_base = build_plan(base)

    rango_x = _rango_default(driver_x, n)
    rango_y = _rango_default(driver_y, n)
    rango_z = _rango_default(driver_z, n)

    puntos = []
    n_seguros = 0

    for sx in rango_x:
        for sy in rango_y:
            for sz in rango_z:
                params = _aplicar_shock(base, driver_x, sx)
                params = _aplicar_shock(params, driver_y, sy)
                params = _aplicar_shock(params, driver_z, sz)
                try:
                    plan = build_plan(params)
                    tir = plan.kpis.tir_proyecto_anual
                except Exception:
                    tir = None
                supera = tir is not None and tir > hurdle_pct
                if supera:
                    n_seguros += 1
                puntos.append({
                    "x_pct": sx,
                    "y_pct": sy,
                    "z_pct": sz,
                    "tir": tir,
                    "supera_hurdle": supera,
                })

    return Sensitivity3DResult(
        driver_x=driver_x,
        driver_y=driver_y,
        driver_z=driver_z,
        rango_x=rango_x,
        rango_y=rango_y,
        rango_z=rango_z,
        puntos=puntos,
        tir_base=plan_base.kpis.tir_proyecto_anual,
        hurdle_pct=hurdle_pct,
        pct_zona_segura=n_seguros / len(puntos) if puntos else 0,
    )


def heatmap_2d(
    driver_x: Driver = "precio",
    driver_y: Driver = "costo_mmpp",
    n: int = 7,
    hurdle_pct: float = 0.15,
    base_params: ParametrosPlan | None = None,
) -> HeatmapResultado:
    """Genera un heatmap NxN de TIR para combinaciones de dos drivers.

    Args:
        driver_x: variable del eje X
        driver_y: variable del eje Y
        n: tamaño del grid (7 = 49 simulaciones, ~7s)
        hurdle_pct: umbral TIR para considerar "zona segura"
        base_params: parámetros base (default = ParametrosPlan())

    Returns:
        HeatmapResultado con celdas y metadatos
    """
    if driver_x == driver_y:
        raise ValueError("driver_x y driver_y deben ser distintos")
    if n < 3 or n > 15:
        raise ValueError("n debe estar entre 3 y 15")

    base = base_params or ParametrosPlan()
    plan_base = build_plan(base)

    rango_x = _rango_default(driver_x, n)
    rango_y = _rango_default(driver_y, n)

    celdas: list[HeatmapCelda] = []
    n_seguras = 0

    for sy in rango_y:
        for sx in rango_x:
            # Aplicar ambos shocks
            params = _aplicar_shock(base, driver_x, sx)
            params = _aplicar_shock(params, driver_y, sy)
            try:
                plan = build_plan(params)
                tir = plan.kpis.tir_proyecto_anual
                van = plan.kpis.van
            except Exception:
                tir, van = None, 0.0

            supera = tir is not None and tir > hurdle_pct
            if supera:
                n_seguras += 1
            celdas.append(
                HeatmapCelda(
                    eje_x_pct=sx,
                    eje_y_pct=sy,
                    tir=tir,
                    van_clp=van,
                    supera_hurdle=supera,
                )
            )

    return HeatmapResultado(
        driver_x=driver_x,
        driver_y=driver_y,
        rango_x=rango_x,
        rango_y=rango_y,
        celdas=celdas,
        tir_base=plan_base.kpis.tir_proyecto_anual,
        van_base=plan_base.kpis.van,
        hurdle_pct=hurdle_pct,
        n_celdas_seguras=n_seguras,
        n_celdas_totales=len(celdas),
    )
