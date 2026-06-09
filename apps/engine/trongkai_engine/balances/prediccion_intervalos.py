"""Prediccion con bandas de confianza (intervalos de incertidumbre).

Responde el pedido del usuario: "predicciones mas inteligentes sin margen
de error o el menos posible".

En vez de dar un numero unico falsamente preciso (ej: costo 6.736 CLP/kg),
propaga la incertidumbre de cada input a la salida y reporta un RANGO con
nivel de confianza (ej: 5.100 - 9.200, esperado 6.736).

La incertidumbre de cada input depende de su nivel de validacion:
- PD (sin validar):     ±35%  (placeholder, gran incertidumbre)
- OK_PROVISORIO:        ±15%  (validado con literatura/benchmark)
- OK_VALIDADO:          ±5%   (medido en planta real)

Mas la variabilidad intrinseca conocida:
- humedad MMPP varia por clima (rango real del doc tecnico)
- capacidades "nominales/referenciales" (doc Talca V2) tienen ±10% extra

Metodo: Monte Carlo (sampleo triangular por input) -> p10/p50/p90 del output.
A medida que se validan inputs (PD -> VALIDADO), las bandas se ESTRECHAN,
acercando el modelo a "sin margen de error".
"""
from __future__ import annotations

import random
from dataclasses import dataclass, asdict, field

# Incertidumbre relativa por nivel de validacion (fraccion del valor)
INCERTIDUMBRE_NIVEL = {
    "PD": 0.35,
    "OK_PROVISORIO": 0.15,
    "OK_VALIDADO": 0.05,
}

# Semilla fija para reproducibilidad (sin Date/random no-determinista)
_SEED = 42
N_SIMS_DEFAULT = 3000


@dataclass
class Banda:
    """Resultado de una variable con su intervalo de confianza."""
    nombre: str
    esperado: float
    p10: float
    p50: float
    p90: float
    unidad: str = ""
    margen_error_pct: float = 0.0   # (p90-p10)/2 / p50, ancho relativo de la banda

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "esperado": round(self.esperado, 2),
            "p10": round(self.p10, 2),
            "p50": round(self.p50, 2),
            "p90": round(self.p90, 2),
            "unidad": self.unidad,
            "margen_error_pct": round(self.margen_error_pct, 4),
        }


@dataclass
class PrediccionIntervalos:
    n_simulaciones: int
    bandas: dict           # nombre -> Banda.to_dict()
    margen_error_global_pct: float
    nivel_confianza_modelo_pct: float   # del precision tracker
    interpretacion: str
    drivers_incertidumbre: list[dict]   # qué inputs aportan mas incertidumbre

    def to_dict(self) -> dict:
        return {
            "n_simulaciones": self.n_simulaciones,
            "bandas": self.bandas,
            "margen_error_global_pct": round(self.margen_error_global_pct, 2),
            "nivel_confianza_modelo_pct": round(self.nivel_confianza_modelo_pct, 1),
            "interpretacion": self.interpretacion,
            "drivers_incertidumbre": self.drivers_incertidumbre,
        }


def _triangular(rng: random.Random, esperado: float, incert_rel: float) -> float:
    """Sampleo triangular alrededor del esperado con +-incert_rel."""
    if esperado == 0:
        return 0.0
    low = esperado * (1 - incert_rel)
    high = esperado * (1 + incert_rel)
    return rng.triangular(low, high, esperado)


def _banda_desde_muestras(nombre: str, muestras: list[float], esperado: float, unidad: str) -> Banda:
    s = sorted(muestras)
    n = len(s)
    p10 = s[int(n * 0.10)]
    p50 = s[int(n * 0.50)]
    p90 = s[min(int(n * 0.90), n - 1)]
    margen = ((p90 - p10) / 2) / p50 if p50 != 0 else 0.0
    return Banda(nombre=nombre, esperado=esperado, p10=p10, p50=p50, p90=p90,
                 unidad=unidad, margen_error_pct=margen)


def computar_prediccion(
    throughput_kg_h: float = 25.0,   # bottleneck real (prensa)
    sku_principal: str = "harina_animal_premium",
    n_sims: int = N_SIMS_DEFAULT,
) -> PrediccionIntervalos:
    """Monte Carlo de las predicciones clave con bandas de confianza."""
    from .simulacion_revenue import PRECIOS_VENTA_DEFAULT
    from .simulacion_revenue import simular_con_revenue

    rng = random.Random(_SEED)

    # ANCLA: usar el simulador real como valor esperado (coherencia total).
    # La incertidumbre se aplica como factores relativos alrededor del ancla,
    # no recalculando el costo con una formula propia.
    base = simular_con_revenue(periodo="ano", sku_principal=sku_principal)
    producto_base_kg = base.producto_total_kg
    costo_base_total = base.costo_total_clp
    precio_base = base.precio_venta_clp_kg

    # Drivers e incertidumbre (factor relativo sobre el ancla):
    # - yield: PROVISORIO + clima -> afecta producto
    # - capacidad bottleneck: nominal/referencial -> afecta producto
    # - precio venta: PD -> afecta revenue
    # - costo operativo (arriendo PEF PD + energia PROVISORIO): -> afecta costo
    incert_yield = INCERTIDUMBRE_NIVEL["OK_PROVISORIO"] + 0.10
    incert_cap = INCERTIDUMBRE_NIVEL["OK_VALIDADO"] + 0.10
    incert_precio = INCERTIDUMBRE_NIVEL["PD"]
    # Costo: combina arriendo PEF (PD, ~55% del costo) + energia (PROV) + resto (PROV)
    incert_costo = INCERTIDUMBRE_NIVEL["PD"] * 0.55 + INCERTIDUMBRE_NIVEL["OK_PROVISORIO"] * 0.45

    out_producto, out_costo_unit, out_revenue, out_margen = [], [], [], []
    for _ in range(n_sims):
        f_yield = _triangular(rng, 1.0, incert_yield)
        f_cap = _triangular(rng, 1.0, incert_cap)
        f_precio = _triangular(rng, 1.0, incert_precio)
        f_costo = _triangular(rng, 1.0, incert_costo)

        producto_kg = producto_base_kg * f_yield * f_cap
        costo_total = costo_base_total * f_costo
        precio = precio_base * f_precio
        costo_unit = costo_total / max(producto_kg, 1)
        revenue = producto_kg * precio
        margen = revenue - costo_total

        out_producto.append(producto_kg / 1000)   # t/año
        out_costo_unit.append(costo_unit)
        out_revenue.append(revenue / 1e6)          # M CLP
        out_margen.append(margen / 1e6)            # M CLP

    # Valores esperados ANCLADOS al simulador (no la media del sampleo)
    esperado_producto = producto_base_kg / 1000
    esperado_costo_unit = costo_base_total / max(producto_base_kg, 1)
    esperado_revenue = (producto_base_kg * precio_base) / 1e6
    esperado_margen = (producto_base_kg * precio_base - costo_base_total) / 1e6

    bandas = {
        "produccion_t_ano": _banda_desde_muestras(
            "Producción anual", out_producto, esperado_producto, "t/año").to_dict(),
        "costo_unitario_clp_kg": _banda_desde_muestras(
            "Costo unitario", out_costo_unit, esperado_costo_unit, "CLP/kg").to_dict(),
        "revenue_anual_mclp": _banda_desde_muestras(
            "Revenue anual", out_revenue, esperado_revenue, "M CLP").to_dict(),
        "margen_anual_mclp": _banda_desde_muestras(
            "Margen anual", out_margen, esperado_margen, "M CLP").to_dict(),
    }

    # Margen de error global = promedio de los margenes de error de las bandas clave
    margen_global = (
        bandas["costo_unitario_clp_kg"]["margen_error_pct"]
        + bandas["produccion_t_ano"]["margen_error_pct"]
    ) / 2 * 100

    # Nivel de confianza del modelo (del precision tracker)
    try:
        from .precision_tracker import computar_precision
        confianza = computar_precision().exactitud_global_pct
    except Exception:
        confianza = 64.0

    # Drivers de incertidumbre: ranking por incertidumbre relativa
    drivers_rank = [
        {"input": "Precio venta", "incertidumbre_pct": round(incert_precio * 100),
         "razon": "Sin cotizaciones firmes (PD). Driver #1 del revenue."},
        {"input": "Costo operativo (arriendo PEF + energía)", "incertidumbre_pct": round(incert_costo * 100),
         "razon": "Arriendo PEF sin cotización final (PD) + tarifa energía estimada."},
        {"input": "Yield proceso", "incertidumbre_pct": round(incert_yield * 100),
         "razon": "MSF de literatura + variabilidad por humedad/clima."},
        {"input": "Capacidad bottleneck", "incertidumbre_pct": round(incert_cap * 100),
         "razon": "Capacidad nominal/referencial (doc Talca V2)."},
    ]
    drivers_rank.sort(key=lambda d: -d["incertidumbre_pct"])

    interp = (
        f"Con confianza del modelo {confianza:.0f}%, el margen de error de las "
        f"predicciones clave es ±{margen_global:.0f}%. Para reducirlo, validar primero: "
        f"{drivers_rank[0]['input']} y {drivers_rank[1]['input']}. "
        f"Cada input que pasa de PD a VALIDADO estrecha la banda significativamente."
    )

    return PrediccionIntervalos(
        n_simulaciones=n_sims,
        bandas=bandas,
        margen_error_global_pct=margen_global,
        nivel_confianza_modelo_pct=confianza,
        interpretacion=interp,
        drivers_incertidumbre=drivers_rank,
    )
