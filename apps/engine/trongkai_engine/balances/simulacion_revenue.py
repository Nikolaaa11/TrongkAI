"""Vincula simulacion temporal con precios SKU para calcular:
- Revenue por periodo (CLP y USD)
- Margen operativo (revenue - costo)
- Break-even por mes
- Payback simple del CAPEX inicial
- Comparador piloto vs industrial (escala x1, x10, x50, x100)
- NPV simplificado a N anos
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field

from .parametros_planta import ParametrosPlanta, cargar_parametros
from .simulador_temporal import (
    ESTACIONALIDAD_MMPP,
    MESES,
    SimulacionTemporal,
    simular_planta,
)


# Precios venta promedio por SKU final CLP/kg (estimacion mercado Chile 2026)
# Hay que validar con cotizaciones reales
PRECIOS_VENTA_DEFAULT = {
    "harina_animal_basica": 850.0,       # alimentacion animal generica
    "harina_animal_premium": 1_400.0,    # con uplift PEF + bioactivos
    "ingrediente_humano": 4_500.0,        # food grade, sin PEF marketing
    "nutraceutico_premium": 12_000.0,     # con compuestos bioactivos certificados
}


# CAPEX estimado del piloto (CLP) - estimaciones, validar con cotizaciones
CAPEX_PILOTO_DEFAULT_CLP = {
    "BOMBA_VALISI_VSHH4": 8_500_000,
    "PRENSA_OELWERK_510": 45_000_000,
    "PRENSA_EXTRACTORA_ACEITE": 12_000_000,
    "CENTRIFUGA_BIOBASE": 6_500_000,
    "SECADOR_IKE_WRH300": 38_000_000,
    "MOLINO_MARTILLOS_HARINERO": 14_000_000,
    "ASPIRADOR_POLVO": 8_000_000,
    "TORNILLO_ELEVADOR": 7_500_000,
    "ENSACADORA_AUTOMATICA": 25_000_000,
    "COMPRESOR_PISTON": 6_000_000,
    "TABLERO_ELECTRICO_EXTERIOR": 18_000_000,
}
INSTALACION_PCT = 0.25      # 25% adicional para instalacion + obra civil
INGENIERIA_CLP = 35_000_000  # ingenieria, permisos, montaje base


@dataclass
class RevenueMensual:
    mes: str
    factor_estacional: float
    producto_kg: float
    costo_clp: float
    revenue_clp: float
    margen_clp: float
    margen_pct: float
    operativo: bool


@dataclass
class SimulacionRevenue:
    """Simulacion temporal + revenue + margen + break-even + payback."""
    periodo: str
    horas_dia: float
    dias_mes: float
    meses_ano: float
    mmpp_principal: str
    sku_principal: str
    precio_venta_clp_kg: float
    # Outputs operativos
    producto_total_kg: float
    costo_total_clp: float
    revenue_total_clp: float
    margen_total_clp: float
    margen_pct: float
    costo_unitario_clp_kg: float
    # CAPEX y payback
    capex_total_clp: float
    payback_simple_anos: float
    # Timeline mensual
    revenue_mensual: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "horas_dia": self.horas_dia,
            "dias_mes": self.dias_mes,
            "meses_ano": self.meses_ano,
            "mmpp_principal": self.mmpp_principal,
            "sku_principal": self.sku_principal,
            "precio_venta_clp_kg": self.precio_venta_clp_kg,
            "producto_total_kg": round(self.producto_total_kg, 0),
            "costo_total_clp": round(self.costo_total_clp, 0),
            "revenue_total_clp": round(self.revenue_total_clp, 0),
            "margen_total_clp": round(self.margen_total_clp, 0),
            "margen_pct": round(self.margen_pct, 4),
            "costo_unitario_clp_kg": round(self.costo_unitario_clp_kg, 0),
            "capex_total_clp": round(self.capex_total_clp, 0),
            "payback_simple_anos": round(self.payback_simple_anos, 2)
                if self.payback_simple_anos != float("inf") else None,
            "revenue_mensual": self.revenue_mensual,
        }


def calcular_capex_piloto(
    capex_por_equipo: dict[str, float] | None = None,
    incluir_ingenieria: bool = True,
) -> dict:
    """CAPEX total del piloto = equipos + instalacion + ingenieria."""
    if capex_por_equipo is None:
        capex_por_equipo = CAPEX_PILOTO_DEFAULT_CLP
    equipos_total = sum(capex_por_equipo.values())
    instalacion = equipos_total * INSTALACION_PCT
    ingenieria = INGENIERIA_CLP if incluir_ingenieria else 0
    total = equipos_total + instalacion + ingenieria
    return {
        "equipos_clp": equipos_total,
        "instalacion_clp": instalacion,
        "ingenieria_clp": ingenieria,
        "total_clp": total,
        "total_usd": round(total / 920.0, 0),
        "desglose_equipos": capex_por_equipo,
    }


def simular_con_revenue(
    periodo: str = "ano",
    horas_dia: float = 16.0,
    dias_mes: float = 25.0,
    meses_ano: float = 10.0,
    mmpp_principal: str = "TOMASA",
    sku_principal: str = "harina_animal_premium",
    precio_venta_clp_kg: float | None = None,
    params: ParametrosPlanta | None = None,
) -> SimulacionRevenue:
    """Simula planta + calcula revenue/margen/payback."""
    if params is None:
        params = cargar_parametros()

    sim = simular_planta(
        periodo=periodo,                                   # type: ignore[arg-type]
        horas_operacion_dia=horas_dia,
        dias_operacion_mes=dias_mes,
        meses_operacion_ano=meses_ano,
        mmpp_principal=mmpp_principal,
        params=params,
    )

    precio = precio_venta_clp_kg or PRECIOS_VENTA_DEFAULT.get(sku_principal, 1000.0)
    revenue = sim.producto_total_kg * precio
    margen = revenue - sim.costo_total_clp
    margen_pct = margen / max(revenue, 1)

    # Timeline mensual con revenue
    revenue_mensual = []
    for m in sim.timeline_mensual:
        rev_m = m["producto_kg"] * precio
        mar_m = rev_m - m["costo_clp"]
        revenue_mensual.append({
            "mes": m["mes"],
            "factor_estacional": m["factor_estacional"],
            "producto_kg": m["producto_kg"],
            "costo_clp": m["costo_clp"],
            "revenue_clp": round(rev_m, 0),
            "margen_clp": round(mar_m, 0),
            "margen_pct": round(mar_m / max(rev_m, 1), 4),
            "operativo": m["operativo"],
        })

    # CAPEX y payback
    capex_info = calcular_capex_piloto()
    capex_total = capex_info["total_clp"]
    # Margen anualizado (si periodo no es ano, escalar)
    if periodo == "ano":
        margen_anual = margen
    elif periodo == "mes":
        margen_anual = margen * meses_ano
    elif periodo == "dia":
        margen_anual = margen * dias_mes * meses_ano
    else:
        margen_anual = margen * horas_dia * dias_mes * meses_ano
    payback = capex_total / margen_anual if margen_anual > 0 else float("inf")

    return SimulacionRevenue(
        periodo=periodo, horas_dia=horas_dia,
        dias_mes=dias_mes, meses_ano=meses_ano,
        mmpp_principal=mmpp_principal,
        sku_principal=sku_principal,
        precio_venta_clp_kg=precio,
        producto_total_kg=sim.producto_total_kg,
        costo_total_clp=sim.costo_total_clp,
        revenue_total_clp=revenue,
        margen_total_clp=margen,
        margen_pct=margen_pct,
        costo_unitario_clp_kg=sim.costo_unitario_clp_kg,
        capex_total_clp=capex_total,
        payback_simple_anos=payback,
        revenue_mensual=revenue_mensual,
    )


def comparar_escalas(
    escalas: list[int] | None = None,
    horas_dia: float = 16.0,
    dias_mes: float = 25.0,
    meses_ano: float = 10.0,
    mmpp_principal: str = "TOMASA",
    sku_principal: str = "harina_animal_premium",
) -> dict:
    """Compara piloto base (x1) vs escalas x10, x50, x100.

    Asume que al escalar:
    - Capacidades de cada equipo se multiplican (1 piloto -> N piloto en paralelo o equipo mayor)
    - Costo unitario baja por economias de escala (curva 80%: cada duplicacion ahorra 20%)
    - CAPEX crece sub-linealmente (exponente 0.7 - regla de Williams)
    - Arriendo PEF/Tricanter prorratea
    """
    if escalas is None:
        escalas = [1, 10, 50, 100]

    base = simular_con_revenue(
        periodo="ano", horas_dia=horas_dia, dias_mes=dias_mes,
        meses_ano=meses_ano, mmpp_principal=mmpp_principal,
        sku_principal=sku_principal,
    )

    resultados = []
    for x in escalas:
        # Producto escala lineal (con el factor escala)
        prod = base.producto_total_kg * x
        # Costo unitario baja con curva 80% (cada duplicacion -> 20% menos)
        import math
        factor_aprendizaje = 0.8 ** math.log2(max(x, 1))
        costo_unit = base.costo_unitario_clp_kg * factor_aprendizaje
        costo_total = costo_unit * prod
        # Revenue (precio constante - asume mismo segmento)
        revenue = prod * base.precio_venta_clp_kg
        margen = revenue - costo_total
        # CAPEX: exponente 0.7 (Williams)
        capex_total = base.capex_total_clp * (x ** 0.7)
        # Payback
        payback = capex_total / margen if margen > 0 else float("inf")

        resultados.append({
            "escala": x,
            "etiqueta": f"x{x}" if x > 1 else "Piloto",
            "producto_kg_ano": round(prod, 0),
            "producto_t_ano": round(prod / 1000, 1),
            "costo_total_clp": round(costo_total, 0),
            "costo_unitario_clp_kg": round(costo_unit, 0),
            "revenue_clp": round(revenue, 0),
            "margen_clp": round(margen, 0),
            "margen_pct": round(margen / max(revenue, 1), 4),
            "capex_clp": round(capex_total, 0),
            "capex_usd": round(capex_total / 920.0, 0),
            "payback_anos": round(payback, 2) if payback != float("inf") else None,
            "factor_aprendizaje": round(factor_aprendizaje, 3),
        })

    return {
        "base_piloto": base.to_dict(),
        "escalas": resultados,
        "supuestos": {
            "curva_aprendizaje_exp": 0.8,
            "capex_williams_exp": 0.7,
            "precio_venta_constante": True,
            "nota": "Curva 80%: cada duplicacion produccion -> 20% menos costo unit. "
                    "Williams 0.7: CAPEX crece sub-linealmente al escalar.",
        },
    }


def precios_venta_catalogo() -> dict:
    """Catalogo de precios estimados por SKU."""
    return {
        "skus": [
            {
                "id": k,
                "nombre": k.replace("_", " ").title(),
                "precio_clp_kg": v,
                "precio_usd_kg": round(v / 920.0, 2),
            }
            for k, v in PRECIOS_VENTA_DEFAULT.items()
        ],
        "fuente": "Estimacion mercado Chile 2026. Validar cotizaciones reales.",
    }


def margen_por_sku() -> dict:
    """La verdad estrategica en una tabla: para cada SKU, el margen del
    piloto y la escala minima a la que se vuelve rentable (si alguna).

    Responde 'el SKU define el negocio': harina animal no es rentable a
    ninguna escala; el nutraceutico paga desde x10.
    """
    filas = []
    for sku, precio in PRECIOS_VENTA_DEFAULT.items():
        piloto = simular_con_revenue(periodo="ano", sku_principal=sku)
        escalas = comparar_escalas(sku_principal=sku)["escalas"]
        rentable = next((e for e in escalas if e["margen_clp"] > 0), None)
        filas.append({
            "sku": sku,
            "nombre": sku.replace("_", " ").title(),
            "precio_clp_kg": precio,
            "margen_piloto_clp": round(piloto.margen_total_clp, 0),
            "margen_piloto_pct": round(piloto.margen_pct, 4),
            "escala_minima_rentable": rentable["escala"] if rentable else None,
            "margen_en_escala_clp": round(rentable["margen_clp"], 0) if rentable else None,
            "payback_en_escala_anos": rentable["payback_anos"] if rentable else None,
            "veredicto": (
                "Rentable ya en piloto" if piloto.margen_total_clp > 0
                else f"Rentable desde x{rentable['escala']}" if rentable
                else "No rentable a ninguna escala"
            ),
        })
    # Ordenar: primero los que pagan antes (escala minima asc, None al final)
    filas.sort(key=lambda f: (f["escala_minima_rentable"] is None,
                              f["escala_minima_rentable"] or 0))
    return {
        "skus": filas,
        "interpretacion": (
            "El SKU define el negocio: el costo de proceso es el mismo para todos, "
            "lo que cambia es el precio de venta. El piloto no es rentable con ningun "
            "SKU (prueba tecnologia); la rentabilidad emerge a escala SOLO con SKU de valor."
        ),
        "nota_precios": "Precios PD (sin cotizacion firme). Driver #1 de incertidumbre.",
    }
