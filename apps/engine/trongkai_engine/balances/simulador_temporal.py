"""Simulador temporal de la planta: por maquina, por hora/dia/mes/ano.

Calcula para cada equipo (y planta integrada):
- Throughput efectivo (limitado por bottleneck del sistema)
- Producto generado por periodo
- Consumo electrico (kWh) y costo CLP
- Costo arriendo prorrateado
- Utilizacion vs capacidad
- Identifica cuello de botella del sistema

Granularidad:
- HORA: consumo + produccion 1h
- DIA: x horas_operacion_dia
- MES: x dias_operacion_mes
- ANO: x meses_operacion_ano

Considera estacionalidad MMPP (Alperujo abril-julio, Tomasa enero-marzo, etc).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Literal

from .fichas_equipos import FichaEquipo, cargar_fichas
from .parametros_planta import ParametrosPlanta, cargar_parametros

Periodo = Literal["hora", "dia", "mes", "ano"]


# Estacionalidad por MMPP (% de capacidad mensual del piloto)
# 12 meses (enero=0). Valores 0..1
ESTACIONALIDAD_MMPP = {
    "TOMASA": [1.0, 1.0, 0.9, 0.5, 0.3, 0.2, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0],
    "ORUJO":  [0.0, 0.0, 0.5, 0.9, 0.7, 0.3, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0],
    "ALPERUJO":[0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.8, 0.3, 0.0, 0.0, 0.0, 0.0],
    "POMASA": [0.3, 0.3, 0.6, 0.5, 0.4, 0.3, 0.2, 0.2, 0.2, 0.6, 0.9, 0.7],
}

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


@dataclass
class ProduccionMaquina:
    """Produccion + costos de UNA maquina por UN periodo."""
    equipo_id: str
    nombre: str
    foto_url: str = ""
    periodo: Periodo = "mes"
    # Inputs
    horas_operacion: float = 0.0
    capacidad_nominal_kg_h: float = 0.0
    throughput_efectivo_kg_h: float = 0.0     # min(capacidad, throughput bottleneck)
    utilizacion_pct: float = 0.0
    # Output
    producto_kg: float = 0.0
    # Consumos + costos
    potencia_kw: float = 0.0
    kwh_consumidos: float = 0.0
    costo_electrico_clp: float = 0.0
    costo_arriendo_clp: float = 0.0
    costo_total_clp: float = 0.0
    es_bottleneck: bool = False

    def to_dict(self) -> dict:
        return {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in asdict(self).items()
        }


@dataclass
class SimulacionTemporal:
    periodo: Periodo
    horas_operacion_dia: float
    dias_operacion_mes: float
    meses_operacion_ano: float
    # Resultados globales
    throughput_planta_kg_h: float       # determinado por bottleneck
    bottleneck_equipo: str
    horas_totales_periodo: float
    producto_total_kg: float
    kwh_totales: float
    costo_electrico_total_clp: float
    costo_arriendo_total_clp: float
    costo_total_clp: float
    costo_unitario_clp_kg: float
    # Por maquina
    maquinas: list[ProduccionMaquina]
    # MMPP procesada (entrada) y OPEX completo
    mmpp_total_kg: float = 0.0
    costo_labor_total_clp: float = 0.0
    costo_agua_total_clp: float = 0.0
    costo_flete_total_clp: float = 0.0
    meses_equivalentes: float = 0.0
    desglose_opex: dict = field(default_factory=dict)
    # Para periodos largos: timeline mensual con estacionalidad
    timeline_mensual: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "horas_operacion_dia": self.horas_operacion_dia,
            "dias_operacion_mes": self.dias_operacion_mes,
            "meses_operacion_ano": self.meses_operacion_ano,
            "throughput_planta_kg_h": round(self.throughput_planta_kg_h, 2),
            "bottleneck_equipo": self.bottleneck_equipo,
            "horas_totales_periodo": round(self.horas_totales_periodo, 2),
            "producto_total_kg": round(self.producto_total_kg, 2),
            "mmpp_total_kg": round(self.mmpp_total_kg, 2),
            "kwh_totales": round(self.kwh_totales, 2),
            "costo_electrico_total_clp": round(self.costo_electrico_total_clp, 0),
            "costo_arriendo_total_clp": round(self.costo_arriendo_total_clp, 0),
            "costo_labor_total_clp": round(self.costo_labor_total_clp, 0),
            "costo_agua_total_clp": round(self.costo_agua_total_clp, 0),
            "costo_flete_total_clp": round(self.costo_flete_total_clp, 0),
            "costo_total_clp": round(self.costo_total_clp, 0),
            "costo_unitario_clp_kg": round(self.costo_unitario_clp_kg, 2),
            "meses_equivalentes": round(self.meses_equivalentes, 2),
            "desglose_opex": self.desglose_opex,
            "maquinas": [m.to_dict() for m in self.maquinas],
            "timeline_mensual": self.timeline_mensual,
        }


def _horas_en_periodo(periodo: Periodo, h_dia: float, d_mes: float, m_ano: float) -> float:
    if periodo == "hora": return 1.0
    if periodo == "dia": return h_dia
    if periodo == "mes": return h_dia * d_mes
    if periodo == "ano": return h_dia * d_mes * m_ano
    return 0.0


def _equipos_linea_productiva(fichas: list[FichaEquipo]) -> list[FichaEquipo]:
    """Filtra los equipos que estan en la linea productiva principal.

    Excluye: auxiliares, romana (compartida), bombas calor respaldo, PEF subproductos.
    Incluye solo los que limitan el throughput.
    """
    excluir_ids = {
        "ROMANA_LAGLORIA",
        "PEF_OPTICEPT_SUBPRODUCTOS",
        "BOMBA_CALOR_RESPALDO",
        "INTERCAMBIADOR_LAGLORIA",
        "CENTRIFUGA_BIOBASE",   # laboratorio
        "PRENSA_EXTRACTORA_ACEITE",   # solo alperujo, no siempre activa
        "COMPRESOR_PISTON",
        "EQUIPOS_MEDICION",
        "TABLERO_ELECTRICO_EXTERIOR",
        "TABLERO_ELECTRICO_INTERIOR",
        "CINTA_TRANSPORTADORA_SACOS",   # parte linea integrada
        "COSEDORA_SACOS",                # parte linea integrada
    }
    return [f for f in fichas if f.id not in excluir_ids and f.capacidad_kg_h > 0]


def _detectar_bottleneck(linea: list[FichaEquipo]) -> tuple[float, str]:
    """Retorna (throughput_efectivo_kg_h, equipo_bottleneck_id)."""
    min_cap = float("inf")
    bottleneck_id = ""
    for f in linea:
        if f.capacidad_kg_h > 0 and f.capacidad_kg_h < min_cap:
            min_cap = f.capacidad_kg_h
            bottleneck_id = f.id
    return min_cap, bottleneck_id


def _yield_proceso_completo() -> float:
    """Yield producto terminado / MMPP entrada (rendimiento MSF).

    Usa el rendimiento MSF promedio de los SKU con proceso definido
    (Tomasa Cold 30%, Hot 25%). Este es el yield REAL del producto
    vendible, no el de la etapa de toma de muestras.
    Default conservador 0.30 si falla.
    """
    try:
        from .etapas import productos_seed
        msf = [p.rendimiento_msf_pct for p in productos_seed()
               if p.rendimiento_msf_pct > 0]
        if msf:
            return sum(msf) / len(msf)
    except Exception:
        pass
    return 0.30


def simular_maquina(
    ficha: FichaEquipo,
    throughput_planta_kg_h: float,
    horas_operacion: float,
    es_bottleneck: bool,
    params: ParametrosPlanta,
    periodo: Periodo,
) -> ProduccionMaquina:
    """Simula UNA maquina dado el throughput limitado por planta."""
    # Throughput efectivo: si esta maquina ES el bottleneck, opera a 100% capacidad
    # Si no, opera al ritmo del bottleneck (subutilizada)
    if ficha.capacidad_kg_h > 0:
        throughput_efectivo = min(ficha.capacidad_kg_h, throughput_planta_kg_h)
        utilizacion = throughput_efectivo / ficha.capacidad_kg_h
    else:
        throughput_efectivo = throughput_planta_kg_h
        utilizacion = 0.0

    producto_kg = throughput_efectivo * horas_operacion
    kwh = ficha.potencia_kw * horas_operacion       # consumo a potencia nominal cuando opera
    costo_electrico = kwh * params.energia.tarifa_promedio_clp_kwh

    # Arriendo prorrateado al periodo
    arriendo = 0.0
    if ficha.modalidad == "OPEX_arriendo" and ficha.arriendo_clp_mes > 0:
        # 480 h/mes referencia (16h/dia x 30d)
        arriendo_por_h = ficha.arriendo_clp_mes / 480.0
        arriendo = arriendo_por_h * horas_operacion

    costo_total = costo_electrico + arriendo

    return ProduccionMaquina(
        equipo_id=ficha.id,
        nombre=ficha.nombre,
        foto_url=ficha.foto_url,
        periodo=periodo,
        horas_operacion=horas_operacion,
        capacidad_nominal_kg_h=ficha.capacidad_kg_h,
        throughput_efectivo_kg_h=throughput_efectivo,
        utilizacion_pct=utilizacion,
        producto_kg=producto_kg,
        potencia_kw=ficha.potencia_kw,
        kwh_consumidos=kwh,
        costo_electrico_clp=costo_electrico,
        costo_arriendo_clp=arriendo,
        costo_total_clp=costo_total,
        es_bottleneck=es_bottleneck,
    )


def _timeline_mensual_estacional(
    throughput_max_kg_h: float,
    horas_dia: float,
    dias_mes: float,
    costo_unitario_clp_kg: float,
    mmpp_principal: str = "TOMASA",
    yield_proceso: float = 1.0,
) -> list[dict]:
    """Genera 12 meses con factor estacional por MMPP."""
    factores = ESTACIONALIDAD_MMPP.get(mmpp_principal.upper(),
                                          [1.0] * 12)  # default sin estacionalidad
    out = []
    for i, mes in enumerate(MESES):
        factor = factores[i]
        horas_mes = horas_dia * dias_mes
        producto_kg = throughput_max_kg_h * horas_mes * factor * yield_proceso
        costo_clp = producto_kg * costo_unitario_clp_kg
        out.append({
            "mes": mes,
            "factor_estacional": round(factor, 3),
            "producto_kg": round(producto_kg, 0),
            "costo_clp": round(costo_clp, 0),
            "operativo": factor > 0.0,
        })
    return out


# Consumo de agua fresca de la planta (proceso 3 + lavado/CIP 2, ref. balance agua).
# Variable con las horas de operacion. m3/h promedio cuando la planta opera.
AGUA_FRESCA_M3_H = 5.0
# Fraccion del agua que se descarga como RILE (paga alcantarillado/tratamiento).
FRAC_DESCARGA_RILE = 0.70


def _opex_completo(
    params: ParametrosPlanta,
    producto_total_kg: float,
    mmpp_total_kg: float,
    costo_electrico: float,
    horas_periodo: float,
    meses_equivalentes: float,
) -> dict:
    """OPEX completo de la planta para el periodo.

    Suma los 6 componentes reales de costo (no solo energia + arriendo):
    - Energia electrica (variable, ya calculada por maquina)
    - Arriendo PEF + Tricanter + otros (FIJO mensual, fuente unica: params.arriendos)
    - Mano de obra: planilla completa x leyes sociales (FIJO mensual)
    - Agua: consumo fresco x tarifa pozo industrial + tratamiento RILE (variable)
    - Flete MMPP de entrada: ton procesadas x CLP/ton (variable)
    El calor residual de La Gloria entra solo si tiene fee de servicio (>0).

    Convencion: los costos FIJOS (arriendo, labor) se facturan por mes operativo
    -> se escalan por `meses_equivalentes` (= horas_periodo / horas_mes_referencia),
    que para el ano default (10 meses x 400 h) da 10 meses.
    """
    # --- FIJOS (por mes operativo) ---
    arriendo_mes = params.arriendos.arriendo_total_clp_mes      # PEF + Tricanter + otros
    labor_mes = sum(s.costo_total_clp for s in params.sueldos)  # bruto x factor leyes sociales
    calor_fee_mes = params.calor_residual.costo_servicio_clp_mes

    costo_arriendo = arriendo_mes * meses_equivalentes
    costo_labor = labor_mes * meses_equivalentes
    costo_calor = calor_fee_mes * meses_equivalentes

    # --- VARIABLES ---
    # Agua: m3 fresca x (tarifa pozo industrial + tratamiento de la fraccion descargada)
    m3_agua = AGUA_FRESCA_M3_H * horas_periodo
    costo_agua = (
        m3_agua * params.agua.agua_industrial_clp_m3
        + m3_agua * FRAC_DESCARGA_RILE * params.agua.alcantarillado_clp_m3
    )
    # Flete MMPP de entrada (campos proveedores -> planta)
    ton_mmpp = mmpp_total_kg / 1000.0
    costo_flete = ton_mmpp * params.flete.costo_promedio_mmpp_clp_ton

    total = (
        costo_electrico + costo_arriendo + costo_labor
        + costo_agua + costo_flete + costo_calor
    )

    return {
        "energia_clp": round(costo_electrico, 0),
        "arriendo_clp": round(costo_arriendo, 0),
        "labor_clp": round(costo_labor, 0),
        "agua_clp": round(costo_agua, 0),
        "flete_mmpp_clp": round(costo_flete, 0),
        "calor_residual_clp": round(costo_calor, 0),
        "total_clp": round(total, 0),
        "m3_agua": round(m3_agua, 1),
        "ton_mmpp": round(ton_mmpp, 2),
        "labor_headcount": len(params.sueldos),
        "arriendo_clp_mes": round(arriendo_mes, 0),
        "labor_clp_mes": round(labor_mes, 0),
    }


def simular_planta(
    periodo: Periodo = "mes",
    horas_operacion_dia: float = 16.0,
    dias_operacion_mes: float = 25.0,
    meses_operacion_ano: float = 10.0,
    mmpp_principal: str = "TOMASA",
    params: ParametrosPlanta | None = None,
    fichas: list[FichaEquipo] | None = None,
) -> SimulacionTemporal:
    """Simula la planta completa para un periodo dado."""
    if params is None:
        params = cargar_parametros()
    if fichas is None:
        fichas = cargar_fichas()

    linea = _equipos_linea_productiva(fichas)
    throughput_planta, bottleneck_id = _detectar_bottleneck(linea)

    horas_periodo = _horas_en_periodo(
        periodo, horas_operacion_dia, dias_operacion_mes, meses_operacion_ano
    )

    maquinas_sim = []
    for f in fichas:
        if f.id in {"ROMANA_LAGLORIA", "INTERCAMBIADOR_LAGLORIA"}:
            continue   # fuera de costos
        es_bottleneck = (f.id == bottleneck_id)
        sim = simular_maquina(f, throughput_planta, horas_periodo, es_bottleneck,
                                params, periodo)
        maquinas_sim.append(sim)

    # Output planta: throughput del bottleneck x yield del proceso completo.
    # El bottleneck define cuanta MMPP pasa por la linea, pero el producto
    # terminado es menor por la perdida de masa (secado, separaciones, etc).
    yield_proceso = _yield_proceso_completo()
    mmpp_total = throughput_planta * horas_periodo
    producto_total = mmpp_total * yield_proceso
    kwh_totales = sum(m.kwh_consumidos for m in maquinas_sim)
    costo_electrico = sum(m.costo_electrico_clp for m in maquinas_sim)

    # OPEX COMPLETO: energia + arriendo full + mano de obra + agua + flete MMPP.
    # Fuente unica de arriendo = params.arriendos (incluye PEF + Tricanter), por eso
    # NO se suma el arriendo prorrateado por maquina (evita doble conteo y subcuenta).
    horas_mes_ref = max(horas_operacion_dia * dias_operacion_mes, 1.0)
    meses_equivalentes = horas_periodo / horas_mes_ref
    desglose = _opex_completo(
        params, producto_total, mmpp_total, costo_electrico,
        horas_periodo, meses_equivalentes,
    )
    costo_arriendo = desglose["arriendo_clp"]
    costo_labor = desglose["labor_clp"]
    costo_agua = desglose["agua_clp"]
    costo_flete = desglose["flete_mmpp_clp"]
    costo_total = desglose["total_clp"]
    costo_unitario = costo_total / max(producto_total, 1)

    # Timeline mensual solo para periodo "ano" o "mes"
    timeline = []
    if periodo in ("ano", "mes"):
        timeline = _timeline_mensual_estacional(
            throughput_planta, horas_operacion_dia, dias_operacion_mes,
            costo_unitario, mmpp_principal, yield_proceso,
        )

    return SimulacionTemporal(
        periodo=periodo,
        horas_operacion_dia=horas_operacion_dia,
        dias_operacion_mes=dias_operacion_mes,
        meses_operacion_ano=meses_operacion_ano,
        throughput_planta_kg_h=throughput_planta,
        bottleneck_equipo=bottleneck_id,
        horas_totales_periodo=horas_periodo,
        producto_total_kg=producto_total,
        kwh_totales=kwh_totales,
        costo_electrico_total_clp=costo_electrico,
        costo_arriendo_total_clp=costo_arriendo,
        costo_total_clp=costo_total,
        costo_unitario_clp_kg=costo_unitario,
        maquinas=maquinas_sim,
        mmpp_total_kg=mmpp_total,
        costo_labor_total_clp=costo_labor,
        costo_agua_total_clp=costo_agua,
        costo_flete_total_clp=costo_flete,
        meses_equivalentes=meses_equivalentes,
        desglose_opex=desglose,
        timeline_mensual=timeline,
    )


def simular_maquina_individual(
    equipo_id: str,
    periodo: Periodo = "mes",
    horas_operacion_dia: float = 16.0,
    dias_operacion_mes: float = 25.0,
    meses_operacion_ano: float = 10.0,
    forzar_capacidad_nominal: bool = True,
    params: ParametrosPlanta | None = None,
) -> dict:
    """Simula UNA maquina aislada (no limitada por bottleneck).

    forzar_capacidad_nominal=True: la maquina opera a capacidad maxima.
    """
    if params is None:
        params = cargar_parametros()
    fichas = cargar_fichas()
    ficha = next((f for f in fichas if f.id == equipo_id), None)
    if ficha is None:
        raise ValueError(f"Equipo no encontrado: {equipo_id}")

    horas_periodo = _horas_en_periodo(
        periodo, horas_operacion_dia, dias_operacion_mes, meses_operacion_ano
    )
    throughput = ficha.capacidad_kg_h if forzar_capacidad_nominal else 0.0
    sim = simular_maquina(ficha, throughput, horas_periodo, True, params, periodo)

    # Para anos, generar tabla por mes
    timeline = []
    if periodo == "ano":
        for i, mes in enumerate(MESES):
            h_mes = horas_operacion_dia * dias_operacion_mes
            if i >= meses_operacion_ano:
                h_mes = 0   # meses no operativos
            prod = throughput * h_mes
            kwh = ficha.potencia_kw * h_mes
            costo = kwh * params.energia.tarifa_promedio_clp_kwh
            if ficha.modalidad == "OPEX_arriendo" and ficha.arriendo_clp_mes > 0:
                costo += ficha.arriendo_clp_mes if h_mes > 0 else 0
            timeline.append({
                "mes": mes,
                "horas_operacion": h_mes,
                "producto_kg": round(prod, 0),
                "kwh": round(kwh, 0),
                "costo_clp": round(costo, 0),
            })

    return {
        "equipo": sim.to_dict(),
        "timeline_mensual": timeline,
    }
