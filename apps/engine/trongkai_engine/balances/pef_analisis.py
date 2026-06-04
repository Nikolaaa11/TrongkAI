"""Analisis economico PEF vs Prensado directo.

Responde la pregunta clave del equipo:
"3) Se justifica economicamente utilizar el PEF?"

Compara dos escenarios:
- ESCENARIO A: con PEF (1 pasada default, segun usuario 4/06/26)
  - Arriendo PEF mensual
  - Consumo electrico PEF
  - Electrodos cada 300hrs
  - BENEFICIO: reduccion % tiempo secado posterior + posible mayor yield
- ESCENARIO B: sin PEF (prensado directo)
  - Sin costo arriendo
  - Mayor tiempo deshidratacion (mas calor/energia)
  - Posible menor yield

Variables sensibles que afectan la decision:
- pct_reduccion_tiempo_secado (key driver - ahi el usuario alimentara)
- pct_aumento_yield (si PEF tambien aumenta rendimiento extraccion)
- pasadas_pef (default 1 segun usuario)
- precio_venta_producto
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict

from .parametros_planta import ParametrosPlanta, cargar_parametros


@dataclass
class EscenarioPEF:
    """Resultado economico de un escenario."""
    nombre: str
    usa_pef: bool
    pasadas_pef: int = 0
    tiempo_secado_min: float = 60.0
    # Costos por hora
    costo_arriendo_pef_clp_h: float = 0.0
    costo_electrico_pef_clp_h: float = 0.0
    costo_electrodos_clp_h: float = 0.0
    costo_secado_clp_h: float = 0.0
    costo_total_clp_h: float = 0.0
    # Yield y producto
    yield_extraccion_pct: float = 0.30
    producto_kg_h: float = 0.0
    costo_unitario_clp_kg: float = 0.0
    costo_unitario_usd_kg: float = 0.0

    def to_dict(self) -> dict:
        return {
            k: round(v, 3) if isinstance(v, float) else v
            for k, v in asdict(self).items()
        }


@dataclass
class AnalisisPEF:
    """Resultado completo A vs B."""
    con_pef: EscenarioPEF
    sin_pef: EscenarioPEF
    diferencia_clp_h: float
    diferencia_pct: float
    breakeven_pct_reduccion_tiempo: float   # minimo % reduccion tiempo para empatar
    recomendacion: str
    drivers_clave: list[str] = field(default_factory=list)
    supuestos: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "con_pef": self.con_pef.to_dict(),
            "sin_pef": self.sin_pef.to_dict(),
            "diferencia_clp_h": round(self.diferencia_clp_h, 0),
            "diferencia_clp_kg": round(
                self.diferencia_clp_h / max(self.con_pef.producto_kg_h, 1), 2),
            "diferencia_pct": round(self.diferencia_pct, 4),
            "breakeven_pct_reduccion_tiempo": round(self.breakeven_pct_reduccion_tiempo, 4),
            "recomendacion": self.recomendacion,
            "drivers_clave": self.drivers_clave,
            "supuestos": self.supuestos,
        }


def computar_escenario(
    usa_pef: bool,
    throughput_kg_h: float,
    pct_reduccion_tiempo_secado: float,
    pct_uplift_yield: float,
    pasadas_pef: int,
    params: ParametrosPlanta,
) -> EscenarioPEF:
    """Calcula costo total y producto generado por hora."""
    # Base: tiempo secado SIN PEF (referencia)
    tiempo_secado_base_min = 60.0
    yield_base = 0.30

    if usa_pef:
        # Costos PEF
        costo_arriendo_clp_h = params.arriendos.arriendo_pef_clp_mes / (16 * 30)
        # Energia: 0.13 kWh/kg input * pasadas
        kwh_h = throughput_kg_h * 0.13 * pasadas_pef
        costo_electrico = kwh_h * params.energia.tarifa_promedio_clp_kwh
        # Electrodos: ~600k cada 300h
        costo_electrodos = 600_000 / 300
        # Beneficio: reduccion tiempo secado
        tiempo_secado = tiempo_secado_base_min * (1 - pct_reduccion_tiempo_secado)
        # Yield mejorado
        yield_extraccion = yield_base * (1 + pct_uplift_yield)
    else:
        costo_arriendo_clp_h = 0.0
        costo_electrico = 0.0
        costo_electrodos = 0.0
        tiempo_secado = tiempo_secado_base_min
        yield_extraccion = yield_base

    # Costo secado: prorrateado por hora segun tiempo en deshidratacion
    # Con calor residual La Gloria: ~10 kWh termico/kg, costo $5 CLP/kWh
    kwh_termico_h = throughput_kg_h * 0.50 * 0.10    # 50% pasa a secado, 0.10 kWh/kg
    # Factor tiempo: si secado dura 60min y PEF reduce a 40 → factor 40/60 = 0.67
    factor_tiempo = tiempo_secado / tiempo_secado_base_min
    costo_secado = (kwh_termico_h * params.calor_residual.costo_kwh_termico_clp
                    * factor_tiempo)

    costo_total = costo_arriendo_clp_h + costo_electrico + costo_electrodos + costo_secado
    # Producto generado: throughput * yield
    producto_kg_h = throughput_kg_h * yield_extraccion
    costo_unitario_clp_kg = costo_total / max(producto_kg_h, 1)

    return EscenarioPEF(
        nombre="Con PEF" if usa_pef else "Sin PEF (prensado directo)",
        usa_pef=usa_pef,
        pasadas_pef=pasadas_pef if usa_pef else 0,
        tiempo_secado_min=tiempo_secado,
        costo_arriendo_pef_clp_h=costo_arriendo_clp_h,
        costo_electrico_pef_clp_h=costo_electrico,
        costo_electrodos_clp_h=costo_electrodos,
        costo_secado_clp_h=costo_secado,
        costo_total_clp_h=costo_total,
        yield_extraccion_pct=yield_extraccion,
        producto_kg_h=producto_kg_h,
        costo_unitario_clp_kg=costo_unitario_clp_kg,
        costo_unitario_usd_kg=costo_unitario_clp_kg / params.usd_clp_referencia,
    )


def analizar_pef_vs_sin_pef(
    throughput_kg_h: float = 2000.0,
    pct_reduccion_tiempo_secado: float = 0.30,
    pct_uplift_yield: float = 0.05,
    pasadas_pef: int = 1,
    precio_venta_clp_kg: float = 850.0,    # precio venta promedio harina premium CLP/kg
    pct_premium_pef: float = 0.10,           # PEF habilita 10% mas precio por calidad
    params: ParametrosPlanta | None = None,
) -> AnalisisPEF:
    """Compara los dos escenarios considerando costo + revenue uplift.

    KEY: con calor residual barato, el PEF solo se justifica si:
    - aumenta yield extraccion (mas kg producto por kg MMPP)
    - habilita precio premium por mejor calidad
    """
    if params is None:
        params = cargar_parametros()

    con = computar_escenario(True, throughput_kg_h, pct_reduccion_tiempo_secado,
                              pct_uplift_yield, pasadas_pef, params)
    sin = computar_escenario(False, throughput_kg_h, 0.0, 0.0, 0, params)

    diff_costo_clp_h = con.costo_total_clp_h - sin.costo_total_clp_h
    diff_pct = diff_costo_clp_h / max(sin.costo_total_clp_h, 1)

    # Revenue uplift: PEF habilita mas yield + premium price
    revenue_con_pef = con.producto_kg_h * precio_venta_clp_kg * (1 + pct_premium_pef)
    revenue_sin_pef = sin.producto_kg_h * precio_venta_clp_kg
    diff_revenue_clp_h = revenue_con_pef - revenue_sin_pef

    # MARGEN NETO: revenue - costo
    margen_con = revenue_con_pef - con.costo_total_clp_h
    margen_sin = revenue_sin_pef - sin.costo_total_clp_h
    diff_margen_clp_h = margen_con - margen_sin

    # Breakeven: cuanto necesita aumentar revenue (yield + premium) para empatar
    if revenue_sin_pef > 0:
        breakeven_uplift_revenue = (con.costo_total_clp_h - sin.costo_total_clp_h) / revenue_sin_pef
    else:
        breakeven_uplift_revenue = 1.0

    # Recomendacion considera margen
    if margen_con > margen_sin:
        ganancia_extra_anual = diff_margen_clp_h * 16 * 300    # 16h/dia 300 dias
        recomendacion = (
            f"✅ USAR PEF: margen +{diff_margen_clp_h:,.0f} CLP/h "
            f"(+${ganancia_extra_anual/1e6:.0f}M CLP/año vs sin PEF)"
        )
    elif breakeven_uplift_revenue < 0.20:
        recomendacion = (
            f"⚠️ MARGINAL: PEF empata si genera >={breakeven_uplift_revenue:.0%} mas revenue "
            f"(via yield o premium). Hoy asumimos {pct_uplift_yield + pct_premium_pef:.0%}. "
            f"Validar A/B real."
        )
    else:
        recomendacion = (
            f"❌ NO USAR PEF: con calor residual barato no compensa. "
            f"Necesita >{breakeven_uplift_revenue:.0%} uplift revenue (poco realista). "
            f"Margen diferencial: {diff_margen_clp_h:,.0f} CLP/h en contra."
        )

    drivers = [
        "% uplift yield extraccion (CRITICO - principal driver con calor residual barato)",
        "% premium price habilitado por PEF (calidad/bioactivos preservados)",
        "% reduccion tiempo secado (MENOR impacto si calor es residual barato)",
        "Numero de pasadas (1 default segun usuario)",
        "Costo arriendo PEF (cotizacion final proveedor)",
        "Precio venta producto (mayor precio = PEF mas rentable)",
        "Throughput nominal (a mayor escala, mas se diluye arriendo)",
    ]

    supuestos = {
        "tiempo_secado_base_min": 60.0,
        "yield_base_sin_pef": 0.30,
        "kwh_kg_pef_por_pasada": 0.13,
        "vida_electrodos_h": 300,
        "costo_electrodos_set_clp": 600_000,
        "kwh_termico_kg_secado": 0.10,
        "calor_residual_clp_kwh": params.calor_residual.costo_kwh_termico_clp,
        "arriendo_pef_clp_mes": params.arriendos.arriendo_pef_clp_mes,
        "horas_operacion_mes": 480.0,
        "precio_venta_clp_kg": precio_venta_clp_kg,
        "pct_premium_pef": pct_premium_pef,
        "revenue_con_pef_clp_h": round(revenue_con_pef, 0),
        "revenue_sin_pef_clp_h": round(revenue_sin_pef, 0),
        "diff_revenue_clp_h": round(diff_revenue_clp_h, 0),
        "margen_con_clp_h": round(margen_con, 0),
        "margen_sin_clp_h": round(margen_sin, 0),
        "diff_margen_clp_h": round(diff_margen_clp_h, 0),
    }

    return AnalisisPEF(
        con_pef=con,
        sin_pef=sin,
        diferencia_clp_h=diff_costo_clp_h,
        diferencia_pct=diff_pct,
        breakeven_pct_reduccion_tiempo=breakeven_uplift_revenue,
        recomendacion=recomendacion,
        drivers_clave=drivers,
        supuestos=supuestos,
    )


def sensibilidad_pef(
    throughput_kg_h: float = 2000.0,
    rangos_reduccion: list[float] | None = None,
    params: ParametrosPlanta | None = None,
) -> list[dict]:
    """Para varios % reduccion tiempo secado, computa diferencia PEF vs sin.

    Permite ver visualmente cuanto necesita reducirse el secado para que
    PEF sea rentable.
    """
    if rangos_reduccion is None:
        rangos_reduccion = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60]
    if params is None:
        params = cargar_parametros()

    resultados = []
    for r in rangos_reduccion:
        a = analizar_pef_vs_sin_pef(
            throughput_kg_h=throughput_kg_h,
            pct_reduccion_tiempo_secado=r,
            pct_uplift_yield=0.0,
            pasadas_pef=1,
            params=params,
        )
        resultados.append({
            "pct_reduccion_secado": r,
            "diferencia_clp_h": round(a.diferencia_clp_h, 0),
            "diferencia_clp_kg": round(
                a.diferencia_clp_h / max(a.con_pef.producto_kg_h, 1), 2),
            "pef_es_mejor": a.con_pef.costo_unitario_clp_kg < a.sin_pef.costo_unitario_clp_kg,
        })
    return resultados
