"""Constructor del Plan 5 Años.

Espec del SUPER_PROMPT §4 M3:
- EERR mensual a 60 meses
- KPIs: TIR, VAN, payback, EBITDA margin, ratio CapEx/Ventas
- Reproduce ejemplo Olivero 1 del Excel original

v2 (KI-001 fix): volumen ponderado por SKU + ramp-up por año de lanzamiento +
EERR separado por marca (Feed / Food / Servicios). Sin esto, la TIR salía
astronómica porque el promedio simple del precio incluía licopeno como si
todo el volumen fuera licopeno.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace
from typing import Literal

from .financial import FlujoMes, KPIsFinancieros, calcular_kpis


# ============================================================================
# Catálogo de SKUs — fuente única para precio, marca, año de lanzamiento y peso
# en el mix de productos finales.
# ============================================================================

@dataclass(frozen=True)
class SKUSpec:
    codigo: str
    precio_clp_kg: float
    marca: Literal["FEED", "FOOD", "SERVICIOS"]
    ano_lanzamiento: int
    # Peso en el mix de productos final (suma debe ≈ 1.0 cuando todos están maduros).
    # Heurística: harinas base son volumen, PTEC son nicho. Refinar con cuotas comerciales reales.
    peso_volumen_maduro: float


SKU_CATALOGO: tuple[SKUSpec, ...] = (
    # ----- Productos base (año 1) -----
    SKUSpec("HARINA_ALPERUJO",   800,    "FOOD", 1, 0.22),    # harina funcional premium
    SKUSpec("ACEITE_ALPERUJO",   1_300,  "FOOD", 1, 0.04),    # benchmark España refinado ajustado
    SKUSpec("HARINA_ORUJO",      600,    "FEED", 1, 0.16),    # 30% bajo harina pescado Chile
    SKUSpec("HARINA_TOMASA",     700,    "FOOD", 1, 0.15),
    SKUSpec("HARINA_POMASA",     700,    "FEED", 1, 0.12),
    SKUSpec("ACEITE_ORUJO_UVA",  1_500,  "FOOD", 2, 0.01),
    # ----- Valor agregado (año 2-3) — calibrado a mercado mundial con descuento nuevo entrante 50% -----
    SKUSpec("PECTINA",           25_000, "FOOD", 2, 0.02),    # USD 55/kg mundial × 0.5 nuevo entrante
    SKUSpec("LICOPENO",          80_000, "FOOD", 2, 0.0005),  # USD 108-253/kg × 0.5 — bulk + capacidad extracción limitada
    # ----- PTEC (año 3-5) — nuevos productos requieren tiempo de mercado -----
    SKUSpec("PROTEINA_UNICEL",   1_500,  "FEED", 3, 0.18),    # benchmark harina pescado Chile +30% premium
    SKUSpec("ANTIOXIDANTE",      15_000, "FEED", 3, 0.04),    # 30% del olive polyphenol premium (nuevo entrante)
    SKUSpec("AGLOMERANTE",       2_000,  "FEED", 4, 0.04),    # TODO: cotización firme
    SKUSpec("UMAMI",             4_500,  "FOOD", 5, 0.01),    # TODO: cotización firme
)


def precio_referencia_dict() -> dict[str, float]:
    """Retorna {sku: precio} para compat con código viejo."""
    return {s.codigo: s.precio_clp_kg for s in SKU_CATALOGO}


def peso_maduro_dict() -> dict[str, float]:
    return {s.codigo: s.peso_volumen_maduro for s in SKU_CATALOGO}


# Mantener nombre legacy para no romper imports externos.
PRECIOS_REFERENCIA = precio_referencia_dict()


# ============================================================================
# Parámetros del Plan
# ============================================================================

@dataclass
class ParametrosPlan:
    """Inputs del plan a 5 años. Todos los precios en CLP."""

    # Volúmenes — base de cálculo
    volumen_total_ton_ano: float = 50_000

    # Precios de venta por SKU (CLP/kg)
    precios_clp_kg: dict[str, float] = field(default_factory=precio_referencia_dict)

    # Peso de cada SKU en el mix de productos final a régimen pleno (suma ≈ 1.0)
    peso_sku: dict[str, float] = field(default_factory=peso_maduro_dict)

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

    # Costos por etapa CLP/kg producto final.
    # Calibrado a planta industrial real: secador es el caro (250 kWh/ton para humedad inicial 80%),
    # extracción licopeno/pectina necesita solventes y energía costosa.
    # Total ~ 330 CLP/kg → consistente con Jaime "ideal cercano a 100, máximo 250" + premium extracción.
    costo_etapa_clp_kg: dict[str, float] = field(
        default_factory=lambda: {
            "RECEPCION": 5, "ALIMENTACION": 5, "HOMOG_1": 4, "PEF": 12,
            "PRENSADO_MECANICO": 15, "TRICANTER": 20, "EXTRACCION": 80,  # extracción solventes
            "SECADO": 180,  # el "caro" (Jaime) — energía 80→10% humedad
            "HOMOG_2": 6, "ENSACADO": 8,
        }
    )

    # CapEx por año — calibrado para biorrefinería industrial:
    # A1 planta piloto + ingeniería conceptual, A2 escalado parcial, A3 línea PTEC + extracción,
    # A4-A5 mejoras + 2da línea. Total 5 años ~ USD 17M = CLP 15B.
    capex_anual_clp: dict[int, float] = field(
        default_factory=lambda: {
            1: 3_000_000_000,  # planta piloto + ingeniería
            2: 5_000_000_000,  # escalado parcial + 1er prensado
            3: 4_000_000_000,  # línea PTEC + Opticept + extracción
            4: 2_000_000_000,  # 2da línea
            5: 1_000_000_000,  # mejoras y debottlenecking
        }
    )

    # OpEx mensual base (incluye MO, mantención, energía, admin)
    # Calibrado a planta procesando 50k ton/año:
    # MO 25 personas × CLP 1.5M/mes = 37.5M; mantención + energía + admin = 42.5M → total 80M.
    opex_mensual_clp: float = 80_000_000

    # Ingreso accesorio mensual: maquilas
    maquilas_mensual_clp: float = 8_000_000   # procesamiento por terceros
    transferencia_tec_anual_clp: float = 350_000_000  # patines CORFO (Jaime "300-400M")

    # Logística MMPP — costo neto promedio CLP/kg input
    # Net Olivero 1-4: 5.9 - 10 + 10.08 + 5 + 0 + 0 + 18 + 0 = ~28/4 = 7 CLP/kg ingresos netos en oliveros activos.
    # Flete promedio 75 km × 2000 CLP / 22500 kg = 6.6 CLP/kg.
    # Conservador: 30 CLP/kg neto (flete - pagos parciales por residuo).
    costo_mmpp_clp_kg: float = 30

    # Costo de comercialización (% del revenue) — marketing, distribución, ventas, certificación,
    # I+D continuo. Plantas alimentarias industriales típicamente 15-25%; nuevo entrante 25-35%.
    # Default 22% mezcla razonable B2B comercializando 12 SKUs en 2 mercados (Feed + Food).
    costo_comercializacion_pct: float = 0.22

    # Impuesto a la renta corporativo Chile (27%). Aplica sobre EBITDA - depreciación.
    impuesto_renta_pct: float = 0.27

    # Fracción del volumen anual procesado (curva ramp-up de planta)
    volumen_pct_por_ano: dict[int, float] = field(
        default_factory=lambda: {1: 0.3, 2: 0.55, 3: 0.8, 4: 0.95, 5: 1.0}
    )

    # WACC: 19.6% nominal sector pesca-acuicultura Chile (Scielo) - 1.6pp premium ESG = 18%
    # docs/DATOS-MERCADO.md sección B
    wacc_anual: float = 0.18


# ============================================================================
# Resumen / Output
# ============================================================================

@dataclass
class ResumenMarca:
    """KPIs comerciales agregados por marca (Feed / Food / Servicios)."""
    marca: str
    ingresos_anuales: list[float] = field(default_factory=lambda: [0.0] * 5)
    volumen_ton_anuales: list[float] = field(default_factory=lambda: [0.0] * 5)


@dataclass
class ResumenPlan:
    flujos: list[FlujoMes]
    kpis: KPIsFinancieros
    parametros: ParametrosPlan
    ingresos_anuales: list[float]
    ebitda_anuales: list[float]
    capex_anuales: list[float]
    por_marca: dict[str, ResumenMarca] = field(default_factory=dict)


@dataclass
class TornadoSensibilidad:
    variable: str
    delta_pct: float  # ej. 0.20 para ±20%
    tir_baja: float | None
    tir_alta: float | None
    van_baja: float
    van_alta: float

    @property
    def magnitud_tir(self) -> float:
        if self.tir_alta is None or self.tir_baja is None:
            return 0.0
        return abs(self.tir_alta - self.tir_baja)


# ============================================================================
# Lógica de construcción
# ============================================================================

def _peso_sku_en_ano(spec: SKUSpec, ano: int, peso_maduro: dict[str, float]) -> float:
    """Peso efectivo del SKU en el ramp-up — 0 antes de su año de lanzamiento, 100% del peso maduro a partir de año+2."""
    if ano < spec.ano_lanzamiento:
        return 0.0
    # Ramp lineal: año de lanzamiento = 33%, +1 año = 66%, +2 años = 100%
    años_madurando = ano - spec.ano_lanzamiento
    ramp = min(1.0, (años_madurando + 1) / 3)
    return peso_maduro.get(spec.codigo, 0.0) * ramp


def _precio_promedio_ponderado(precios: dict[str, float], pesos_efectivos: dict[str, float]) -> float:
    """Promedio ponderado precio × peso (renormaliza pesos a suma 1)."""
    total_peso = sum(pesos_efectivos.values())
    if total_peso == 0:
        return 0.0
    return sum(precios.get(sku, 0) * peso for sku, peso in pesos_efectivos.items()) / total_peso


def build_plan(parametros: ParametrosPlan | None = None) -> ResumenPlan:
    p = parametros or ParametrosPlan()
    rendimiento_promedio = sum(p.rendimiento_por_mmpp.values()) / len(p.rendimiento_por_mmpp)
    costo_etapa_total_clp_kg = sum(p.costo_etapa_clp_kg.values())

    flujos: list[FlujoMes] = []
    ingresos_anuales = [0.0] * 5
    ebitda_anuales = [0.0] * 5
    capex_anuales = [0.0] * 5
    por_marca = {
        m: ResumenMarca(marca=m) for m in ("FEED", "FOOD", "SERVICIOS")
    }

    for ano in range(1, 6):
        vol_pct = p.volumen_pct_por_ano.get(ano, 1.0)
        ton_anual = p.volumen_total_ton_ano * vol_pct
        ton_producto_final_anual = ton_anual * rendimiento_promedio
        kg_producto_final_anual = ton_producto_final_anual * 1_000

        # Pesos efectivos de cada SKU este año (ramp-up por año de lanzamiento)
        pesos_efectivos: dict[str, float] = {}
        for spec in SKU_CATALOGO:
            peso = _peso_sku_en_ano(spec, ano, p.peso_sku)
            if peso > 0:
                pesos_efectivos[spec.codigo] = peso

        total_peso = sum(pesos_efectivos.values()) or 1.0
        pesos_normalizados = {sku: peso / total_peso for sku, peso in pesos_efectivos.items()}

        # Precio promedio ponderado
        precio_promedio = _precio_promedio_ponderado(p.precios_clp_kg, pesos_efectivos)
        ingreso_ventas_anual = kg_producto_final_anual * precio_promedio

        # Ingresos por marca (mismo precio promedio, repartido según pesos)
        for spec in SKU_CATALOGO:
            peso_norm = pesos_normalizados.get(spec.codigo, 0)
            if peso_norm == 0:
                continue
            kg_sku = kg_producto_final_anual * peso_norm
            ingreso_sku = kg_sku * p.precios_clp_kg.get(spec.codigo, 0)
            por_marca[spec.marca].ingresos_anuales[ano - 1] += ingreso_sku
            por_marca[spec.marca].volumen_ton_anuales[ano - 1] += kg_sku / 1_000

        # Costos directos = MMPP + producción por etapa (sobre ton producto final) + comercialización (% ingreso)
        costo_mmpp_anual = ton_anual * 1_000 * p.costo_mmpp_clp_kg
        costo_produccion_anual = kg_producto_final_anual * costo_etapa_total_clp_kg
        # Comercialización aplica sobre TODOS los ingresos (ventas + maquilas + transferencia tec)
        # — se cobra como % flat de revenue total. Refleja ventas, distribución, marketing, certificaciones.
        maquilas_anual = p.maquilas_mensual_clp * 12
        transferencia_anual = p.transferencia_tec_anual_clp if ano <= 2 else 0
        ingreso_total_anual = ingreso_ventas_anual + maquilas_anual + transferencia_anual
        costo_comercializacion_anual = ingreso_total_anual * p.costo_comercializacion_pct
        directos_anual = costo_mmpp_anual + costo_produccion_anual + costo_comercializacion_anual

        # Gastos fijos
        fijos_anual = p.opex_mensual_clp * 12

        # Maquilas + transferencia se asignan a marca SERVICIOS
        por_marca["SERVICIOS"].ingresos_anuales[ano - 1] += maquilas_anual + transferencia_anual

        capex_ano = p.capex_anual_clp.get(ano, 0)
        capex_anuales[ano - 1] = capex_ano
        ingresos_anuales[ano - 1] = ingreso_total_anual
        ebitda_anuales[ano - 1] = ingreso_total_anual - directos_anual - fijos_anual

        for mes in range(1, 13):
            mes_global = (ano - 1) * 12 + mes
            stagger = min(1.0, mes / 6.0) if ano == 1 else 1.0
            ingreso_mes = (ingreso_ventas_anual / 12) * stagger
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
        por_marca=por_marca,
    )


# ============================================================================
# Tornado de sensibilidades (preservado del Financial agent)
# ============================================================================

def tornado_sensibilidades(
    base_params: ParametrosPlan | None = None,
    delta_pct: float = 0.20,
) -> list[TornadoSensibilidad]:
    """Shockea ±delta_pct sobre 5 variables clave y mide impacto en TIR."""
    base = base_params or ParametrosPlan()
    base_plan = build_plan(base)
    out: list[TornadoSensibilidad] = []

    def shock_var(nombre: str, baja: ParametrosPlan, alta: ParametrosPlan) -> TornadoSensibilidad:
        pb = build_plan(baja)
        pa = build_plan(alta)
        return TornadoSensibilidad(
            variable=nombre,
            delta_pct=delta_pct,
            tir_baja=pb.kpis.tir_proyecto_anual,
            tir_alta=pa.kpis.tir_proyecto_anual,
            van_baja=pb.kpis.van,
            van_alta=pa.kpis.van,
        )

    # WACC
    out.append(shock_var(
        "wacc_anual",
        replace(base, wacc_anual=base.wacc_anual * (1 - delta_pct)),
        replace(base, wacc_anual=base.wacc_anual * (1 + delta_pct)),
    ))
    # Precio promedio: escalo TODOS los precios proporcionalmente
    precios_baja = {sku: precio * (1 - delta_pct) for sku, precio in base.precios_clp_kg.items()}
    precios_alta = {sku: precio * (1 + delta_pct) for sku, precio in base.precios_clp_kg.items()}
    out.append(shock_var(
        "precio_promedio",
        replace(base, precios_clp_kg=precios_baja),
        replace(base, precios_clp_kg=precios_alta),
    ))
    # Costo MMPP
    out.append(shock_var(
        "costo_mmpp",
        replace(base, costo_mmpp_clp_kg=base.costo_mmpp_clp_kg * (1 - delta_pct)),
        replace(base, costo_mmpp_clp_kg=base.costo_mmpp_clp_kg * (1 + delta_pct)),
    ))
    # OpEx mensual
    out.append(shock_var(
        "opex_mensual",
        replace(base, opex_mensual_clp=base.opex_mensual_clp * (1 - delta_pct)),
        replace(base, opex_mensual_clp=base.opex_mensual_clp * (1 + delta_pct)),
    ))
    # Rendimiento promedio: escalo todos los rendimientos
    rend_baja = {k: v * (1 - delta_pct) for k, v in base.rendimiento_por_mmpp.items()}
    rend_alta = {k: v * (1 + delta_pct) for k, v in base.rendimiento_por_mmpp.items()}
    out.append(shock_var(
        "rendimiento_promedio",
        replace(base, rendimiento_por_mmpp=rend_baja),
        replace(base, rendimiento_por_mmpp=rend_alta),
    ))

    out.sort(key=lambda s: s.magnitud_tir, reverse=True)
    return out


# ============================================================================
# Validación M3 — caso Olivero 1
# ============================================================================

def caso_olivero_1_costo_unitario_kg(distancia_km: float = 82, tarifa_clp_km: float = 1800,
                                       capacidad_camion_ton: float = 25,
                                       pago_recepcion_clp_kg: float = -10) -> dict:
    """Reproduce el cálculo del 'Caso 1 — Olivero 1' del Excel original."""
    costo_viaje_clp = distancia_km * tarifa_clp_km
    kg_camion = capacidad_camion_ton * 1_000
    costo_unitario_flete = costo_viaje_clp / kg_camion
    return {
        "costo_viaje_clp": costo_viaje_clp,
        "costo_unitario_flete_clp_kg": round(costo_unitario_flete, 3),
        "pago_recepcion_clp_kg": pago_recepcion_clp_kg,
        "costo_neto_clp_kg": round(costo_unitario_flete + pago_recepcion_clp_kg, 3),
    }
