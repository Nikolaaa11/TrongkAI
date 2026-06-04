"""Balances por etapa de la planta Trongkai - Modelo Agrosphere REAL.

Fuente: 'Etapas X Costeo Agrosphere 29052026.xlsx' - validado con equipo Agrosphere.

11 etapas reales del proceso completo de upcycling agroindustrial:
E1 Recepcion -> E2 Homogenizacion -> E3 PEF -> E4(a) Prensado Mecanico ->
E4(b) Prensado Centrifugo -> E5 Canalizacion -> E6(a) Deshidratacion Principal ->
[E6(b) Respaldo] -> E7 Enfriado/Molienda -> E8 Homogenizado/Calidad ->
E9 Ensacado -> E10 Etiquetado -> E11 Toma Muestra/Trazabilidad

Tiempos totales: 120 min normal, 150 min con equipo respaldo deshidratacion.

Datos por etapa: tiempo (min), humedad (% post-etapa), MO (Encargado +
auxiliares), equipos energeticos, repuestos, materiales, capacidad, yield.

Matriz Productos x Etapas (cuales MMPP/SKU pasan por cuales etapas):
- Tomasa 1 (Cold): E1-E4(a)        -> rendimiento MSF 30%
- Tomasa 2 (Hot):  E1-E3, E4(b)     -> rendimiento MSF 25%
- Orujo 1 (Tinto), Orujo 2 (Blanco): solo E1 (a definir)
- Alperujo 1 (EV), Alperujo 2 (V):  solo E1 (a definir)
- Pomasa 1 (Roja), Pomasa 2 (Verde): solo E1 (a definir)
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Literal


class NivelDato(StrEnum):
    PD = "PD"
    OK_PROVISORIO = "OK_PROVISORIO"
    OK_VALIDADO = "OK_VALIDADO"


@dataclass
class CapacidadEtapa:
    valor_maximo: float
    unidad: str = "kg/h"
    nivel_dato: NivelDato = NivelDato.PD


@dataclass
class EtapaPlanta:
    """Una etapa del proceso productivo Agrosphere."""
    id: str
    nombre: str
    orden: int
    descripcion: str
    # Inputs/Outputs
    masa_input_kg_h: float
    yield_pct: float
    perdidas_pct: float = 0.02
    humedad_post_etapa: tuple[float, float] = (0.0, 0.0)  # (min, max) fraccion
    # Consumos por kg de input
    energia_kwh_por_kg: float = 0.0
    agua_l_por_kg: float = 0.0
    hh_por_ton_input: float = 0.0
    # Tiempo de proceso
    tiempo_proceso_min: float = 0.0
    # Capacidad
    capacidad: CapacidadEtapa = field(default_factory=lambda: CapacidadEtapa(1000.0))
    horas_operacion_dia: float = 16.0
    dias_operacion_anual: float = 300.0
    # Personal y equipos (segun Excel Agrosphere)
    mo_directa: list[str] = field(default_factory=list)
    mo_general: list[str] = field(default_factory=list)
    equipos_energeticos: list[str] = field(default_factory=list)
    repuestos: list[str] = field(default_factory=list)
    materiales: list[str] = field(default_factory=list)
    notas_proceso: str = ""
    # Calidad de datos
    datos_faltantes: list[str] = field(default_factory=list)
    nivel_calibracion: NivelDato = NivelDato.PD
    # Es etapa de respaldo (opcional, no siempre activa)
    es_respaldo: bool = False
    # Integracion
    equipo_energetico_principal: str = ""
    equipo_hidrico_principal: str = ""
    categoria_rrhh_principal: str = ""

    @property
    def masa_output_kg_h(self) -> float:
        return self.masa_input_kg_h * self.yield_pct

    @property
    def perdidas_kg_h(self) -> float:
        return self.masa_input_kg_h * self.perdidas_pct

    @property
    def consumo_energia_kwh_h(self) -> float:
        return self.masa_input_kg_h * self.energia_kwh_por_kg

    @property
    def consumo_agua_l_h(self) -> float:
        return self.masa_input_kg_h * self.agua_l_por_kg

    @property
    def utilizacion_pct(self) -> float:
        if self.capacidad.valor_maximo <= 0:
            return 0.0
        return self.masa_input_kg_h / self.capacidad.valor_maximo

    @property
    def es_bottleneck(self) -> bool:
        return self.utilizacion_pct >= 0.85

    @property
    def datos_completitud_pct(self) -> float:
        score_map = {
            NivelDato.OK_VALIDADO: 100.0,
            NivelDato.OK_PROVISORIO: 60.0,
            NivelDato.PD: 20.0,
        }
        return score_map.get(self.nivel_calibracion, 0.0)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["masa_output_kg_h"] = round(self.masa_output_kg_h, 2)
        d["perdidas_kg_h"] = round(self.perdidas_kg_h, 2)
        d["consumo_energia_kwh_h"] = round(self.consumo_energia_kwh_h, 3)
        d["consumo_agua_l_h"] = round(self.consumo_agua_l_h, 2)
        d["utilizacion_pct"] = round(self.utilizacion_pct, 3)
        d["es_bottleneck"] = self.es_bottleneck
        d["datos_completitud_pct"] = round(self.datos_completitud_pct, 1)
        d["humedad_post_etapa"] = list(self.humedad_post_etapa)
        return d


@dataclass
class BalancePorEtapas:
    etapas: list[EtapaPlanta]
    masa_entrada_total_kg_h: float
    masa_salida_final_kg_h: float
    yield_total_proceso: float
    energia_total_kwh_h: float
    agua_total_l_h: float
    hh_totales_turno: float
    tiempo_proceso_total_min: float
    bottlenecks: list[str]
    completitud_datos_pct: float
    intensidades_acumuladas: dict
    alarmas: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "etapas": [e.to_dict() for e in self.etapas],
            "masa_entrada_total_kg_h": round(self.masa_entrada_total_kg_h, 2),
            "masa_salida_final_kg_h": round(self.masa_salida_final_kg_h, 2),
            "yield_total_proceso": round(self.yield_total_proceso, 4),
            "energia_total_kwh_h": round(self.energia_total_kwh_h, 3),
            "agua_total_l_h": round(self.agua_total_l_h, 2),
            "hh_totales_turno": round(self.hh_totales_turno, 2),
            "tiempo_proceso_total_min": round(self.tiempo_proceso_total_min, 1),
            "bottlenecks": self.bottlenecks,
            "completitud_datos_pct": round(self.completitud_datos_pct, 1),
            "intensidades_acumuladas": self.intensidades_acumuladas,
            "alarmas": self.alarmas,
        }


# =========================================================================
# 11 ETAPAS REALES AGROSPHERE (Excel 29052026)
# =========================================================================
def etapas_seed(throughput_kg_h: float = 2000.0, incluir_respaldo: bool = False) -> list[EtapaPlanta]:
    """Las 11 etapas reales del proceso Agrosphere.

    Si incluir_respaldo=True agrega E6(b) Deshidratacion Equipo Respaldo
    en lugar de E6(a) Principal (tiempo proceso pasa de 120 -> 150 min).
    """
    e1 = EtapaPlanta(
        id="E1_RECEPCION",
        nombre="E1. Recepcion (con muestreo previo Laboratorista)",
        orden=1,
        descripcion=(
            "Camion llega a estacionamiento - Laboratorista toma muestra ANTES de "
            "aceptar carga. Si aceptado: vertido en estanque (piscina/acero inox/aprobado). "
            "Encargado guia al camionero (20-30 min/camion). Tornillo/cinta/bomba "
            "impulsion lleva a etapa 2. ROMANA COMPARTIDA con La Gloria (fuera de costos)."
        ),
        masa_input_kg_h=throughput_kg_h,
        yield_pct=1.00,
        perdidas_pct=0.005,
        humedad_post_etapa=(0.55, 0.85),     # varia por MMPP - ver humedades_mmpp.py
        energia_kwh_por_kg=0.0008,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.40,                # alto por muestreo + recepcion
        tiempo_proceso_min=25.0,              # 20-30 min por camion segun conversacion
        capacidad=CapacidadEtapa(throughput_kg_h * 2.0, "kg/h", NivelDato.OK_PROVISORIO),
        mo_directa=["Laboratorista (muestreo previo)", "Encargado Recepcion"],
        mo_general=["Operario Limpieza"],
        equipos_energeticos=["Tornillo / Cinta / Bomba impulsion a E2"],
        notas_proceso=(
            "Romana COMPARTIDA con servicios La Gloria - FUERA de analisis costos. "
            "Solo se despachan documentos de recepcion DESPUES de aceptar la carga. "
            "Humedades ingreso varian por MMPP: Tomasa 75-85%, Orujo 65%, "
            "Alperujo 60%, Pomasa 80%. Variable por clima. "
            "Limpieza/desinfeccion estandarizada por cantidad material o dias productivos."
        ),
        datos_faltantes=[
            "Materialidad final estanque (piscina vs acero inox vs otra)",
            "Frecuencia llegada camiones por hora",
            "Tiempo muestreo Laboratorista (incluido en HH)",
            "Protocolo limpieza/desinfeccion (cantidad o dias)",
        ],
        nivel_calibracion=NivelDato.OK_VALIDADO,
        categoria_rrhh_principal="calidad",
    )
    e2 = EtapaPlanta(
        id="E2_ESTANDARIZACION",
        nombre="E2. Estandarizacion (analisis quimicos + ajuste)",
        orden=2,
        descripcion=(
            "Analisis parametros quimicos para configurar PEF. Evaluar incorporacion "
            "de agua y/o liquidos del prensado posterior (loop E5->E2). "
            "Homogenizador de paleta. Transporte por bomba tornillo a tolva PEF."
        ),
        masa_input_kg_h=throughput_kg_h * 0.995,
        yield_pct=0.995,
        perdidas_pct=0.005,
        humedad_post_etapa=(0.75, 0.80),
        energia_kwh_por_kg=0.015,
        agua_l_por_kg=1.0,
        hh_por_ton_input=0.03,
        tiempo_proceso_min=2.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 1.8, "kg/h"),
        mo_directa=["Encargado Proceso", "Laboratorista"],
        mo_general=["Limpieza"],
        equipos_energeticos=["Homogenizador de paleta", "Bomba tornillo alimentacion PEF"],
        notas_proceso=(
            "1) Analisis quimicos del lote para configurar PEF. "
            "2) Ajustar % agua/liquidos (puede usar agua llave + liquidos prensado E5). "
            "3) Limpieza/desinfeccion por batch/dia/MMPP."
        ),
        datos_faltantes=[
            "% agua optimo por MMPP para reologia PEF",
            "Densidad target post-homogenizacion",
            "Especificacion homogenizador (paleta vs cinta vs sinusoidal)",
        ],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        equipo_hidrico_principal="PEF Opticept",
        categoria_rrhh_principal="operario",
    )
    e3 = EtapaPlanta(
        id="E3_PEF",
        nombre="E3. PEF (Electroporacion - solo ruptura celular)",
        orden=3,
        descripcion=(
            "Pulsos electricos abren membranas celulares. SIN PERDIDAS DE MASA, "
            "SIN CAMBIO DE HUMEDAD. Bomba tornillo alimenta, bomba salida traslada "
            "a prensado. PEF es EQUIPO ARRENDADO (OPEX, no CAPEX propio)."
        ),
        masa_input_kg_h=throughput_kg_h * 0.990,
        yield_pct=1.00,                  # NO HAY PERDIDAS segun conversacion
        perdidas_pct=0.0,
        humedad_post_etapa=(0.75, 0.80),  # NO CAMBIA HUMEDAD
        energia_kwh_por_kg=0.13,
        agua_l_por_kg=0.5,
        hh_por_ton_input=0.04,
        tiempo_proceso_min=8.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 1.0, "kg/h", NivelDato.OK_PROVISORIO),
        mo_directa=["Encargado Proceso"],
        mo_general=["Operario Limpieza"],
        equipos_energeticos=["PEF Opticept ARRENDADO", "Bomba tornillo entrada", "Bomba salida"],
        repuestos=["Electrodos PEF (vida util 300hrs)"],
        notas_proceso=(
            "TRES EVALUACIONES PENDIENTES (criticas para tesis de inversion): "
            "1) PEF efectivamente disminuye tiempos secado posterior con impacto significativo? "
            "2) Pasada unica o multiple para apertura efectiva de membranas? "
            "3) Justifica economicamente el arriendo vs prensado directo? "
            "Test A/B: misma MMPP, fraccion con PEF + prensado vs prensado directo. "
            "Limpieza/desinfeccion por batch/dia/MMPP."
        ),
        datos_faltantes=[
            "kV optimo por MMPP (tomasa vs orujo vs alperujo)",
            "Numero pasadas optimas (1 o N)",
            "Validar disminucion real tiempos secado vs prensado directo (A/B test)",
            "Costo arriendo mensual PEF (cotizacion final)",
            "Costo electrodos CIF Chile",
        ],
        nivel_calibracion=NivelDato.PD,
        equipo_energetico_principal="PEF Opticept",
        equipo_hidrico_principal="PEF Opticept",
        categoria_rrhh_principal="operario",
    )
    e4a = EtapaPlanta(
        id="E4A_PRENSADO_MECANICO",
        nombre="E4(a). Prensado Mecanico",
        orden=4,
        descripcion="Prensa mecanica (tornillo/horizontal) para extraccion principal.",
        masa_input_kg_h=throughput_kg_h * 0.985,
        yield_pct=0.95,
        perdidas_pct=0.005,
        humedad_post_etapa=(0.40, 0.50),
        energia_kwh_por_kg=0.040,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.05,
        tiempo_proceso_min=3.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 1.2, "kg/h"),
        mo_directa=["Encargado"],
        mo_general=["Limpieza"],
        equipos_energeticos=["Prensa Mecanica"],
        repuestos=["Filtros prensa"],
        datos_faltantes=["Frecuencia cambio filtros", "Yield real por MMPP"],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="operario",
    )
    e4b = EtapaPlanta(
        id="E4B_PRENSADO_CENTRIFUGO",
        nombre="E4(b). Prensado Centrifugo (Tricanter)",
        orden=5,
        descripcion="Tricanter para Tomasa Hot. Separacion mas eficiente fase liquida.",
        masa_input_kg_h=throughput_kg_h * 0.985,
        yield_pct=0.93,
        perdidas_pct=0.005,
        humedad_post_etapa=(0.30, 0.35),
        energia_kwh_por_kg=0.055,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.05,
        tiempo_proceso_min=3.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 1.0, "kg/h"),
        mo_directa=["Encargado"],
        mo_general=["Limpieza"],
        equipos_energeticos=["Tricanter (centrifuga 3 fases)"],
        repuestos=["Filtros tricanter"],
        datos_faltantes=["G-force optimo", "Solo aplica a Tomasa Hot (validar)"],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="operario",
    )
    e5 = EtapaPlanta(
        id="E5_LIQUIDOS_RESIDUALES",
        nombre="E5. Liquidos residuales (loop opcional a E2)",
        orden=6,
        descripcion=(
            "Gestion fase liquida del prensado: almacenamiento + bombas traslado. "
            "Opciones: 1) tratar y descartar como RILE, 2) REINCORPORAR al proceso "
            "de Estandarizacion (E2) para ajustar reologia."
        ),
        masa_input_kg_h=throughput_kg_h * 0.50,   # fase liquida del prensado
        yield_pct=0.95,
        perdidas_pct=0.005,
        humedad_post_etapa=(0.0, 0.0),
        energia_kwh_por_kg=0.020,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.04,
        tiempo_proceso_min=4.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.8, "kg/h"),
        mo_directa=["Encargado Proceso"],
        mo_general=["Operario Limpieza"],
        equipos_energeticos=["Estanque almacenamiento", "Bombas traslado", "Planta tratamiento (opcional)"],
        notas_proceso=(
            "Decision clave: cuanto del liquido se reincorpora a E2 (reduce consumo "
            "agua llave) vs cuanto va a RILE (costo tratamiento). "
            "Loop E5 -> E2 puede reducir significativamente consumo de agua llave."
        ),
        datos_faltantes=[
            "Equipo concreto de canalizacion",
            "% optimo recirculacion E5->E2 por MMPP",
            "Costo planta tratamiento RILE (CAPEX + OPEX)",
            "Carga organica liquido (DBO/DQO) para dimensionar tratamiento",
        ],
        nivel_calibracion=NivelDato.PD,
    )
    if incluir_respaldo:
        e6 = EtapaPlanta(
            id="E6B_DESHIDRATACION_RESPALDO",
            nombre="E6(b). Deshidratacion - Bomba de Calor (respaldo)",
            orden=7,
            descripcion=(
                "Sistema secundario con bomba de calor. Activo cuando La Gloria no "
                "entrega calor residual o por mantencion. Mayor consumo electrico. "
                "Input: 30% humedad post-prensado -> Output: 10-15% humedad."
            ),
            masa_input_kg_h=throughput_kg_h * 0.50,
            yield_pct=0.50,
            perdidas_pct=0.005,
            humedad_post_etapa=(0.10, 0.15),     # ajustado segun conversacion
            energia_kwh_por_kg=0.55,
            agua_l_por_kg=0.5,
            hh_por_ton_input=0.08,
            tiempo_proceso_min=90.0,
            capacidad=CapacidadEtapa(throughput_kg_h * 0.6, "kg/h"),
            mo_directa=["Encargado Secado"],
            mo_general=["Operario Limpieza"],
            equipos_energeticos=["Bomba de calor (respaldo)", "Sistema Transportador hermetico"],
            notas_proceso=(
                "Desde sistema de secado en adelante NO PUEDE haber contacto con ambiente "
                "(humedad reabsorbida). Mas costoso que principal (4x electricidad)."
            ),
            datos_faltantes=[
                "COP (eficiencia) real bomba de calor",
                "Tiempo residencia por MMPP",
                "Costo CAPEX bomba calor + arriendo opcional",
            ],
            nivel_calibracion=NivelDato.PD,
            es_respaldo=True,
            equipo_energetico_principal="Bomba de calor",
        )
    else:
        e6 = EtapaPlanta(
            id="E6A_DESHIDRATACION_PRINCIPAL",
            nombre="E6(a). Deshidratacion - Calor Residual La Gloria",
            orden=7,
            descripcion=(
                "Sistema PRINCIPAL usa CALOR RESIDUAL desde planta La Gloria. "
                "Input: 30% humedad post-prensado -> Output: 10-15% humedad. "
                "Costo termico muy bajo (es residuo industrial)."
            ),
            masa_input_kg_h=throughput_kg_h * 0.50,
            yield_pct=0.50,
            perdidas_pct=0.005,
            humedad_post_etapa=(0.10, 0.15),     # 10-15% segun conversacion
            energia_kwh_por_kg=0.10,              # solo electrico para movimiento
            agua_l_por_kg=0.5,
            hh_por_ton_input=0.08,
            tiempo_proceso_min=60.0,
            capacidad=CapacidadEtapa(throughput_kg_h * 0.8, "kg/h", NivelDato.OK_PROVISORIO),
            mo_directa=["Encargado Secado"],
            mo_general=["Operario Limpieza"],
            equipos_energeticos=["Intercambiador calor residual La Gloria", "Sistema Transportador hermetico"],
            notas_proceso=(
                "CALOR RESIDUAL desde La Gloria (compartido). Costo muy bajo, validar contrato. "
                "Desde aqui NO puede haber contacto con ambiente (reabsorcion humedad)."
            ),
            datos_faltantes=[
                "Contrato formal con La Gloria por calor residual",
                "kWh termicos efectivos entregados/mes",
                "Temperatura optima sin degradar bioactivos por MMPP",
                "Tiempo residencia real por MMPP",
            ],
            nivel_calibracion=NivelDato.OK_PROVISORIO,
            equipo_energetico_principal="Calor residual La Gloria",
            equipo_hidrico_principal="Sistema vapor",
        )
    e7 = EtapaPlanta(
        id="E7_ENFRIADO",
        nombre="E7. Enfriado (humedad relativa final 8-10%)",
        orden=8,
        descripcion=(
            "Enfriado natural de la harina post-secado. Continua perdida de humedad "
            "por movimiento y perdida de calor. PUNTO DE DECISION DE VENTA: "
            "vender ya o pasar a E8 mejoramiento (molienda + mezcla)."
        ),
        masa_input_kg_h=throughput_kg_h * 0.25,
        yield_pct=0.99,
        perdidas_pct=0.010,
        humedad_post_etapa=(0.08, 0.10),     # 8-10% segun conversacion
        energia_kwh_por_kg=0.020,             # solo movimiento
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.04,
        tiempo_proceso_min=3.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.4, "kg/h"),
        mo_directa=["Encargado Proceso"],
        mo_general=["Operario Limpieza"],
        equipos_energeticos=["Sistema Transportador / enfriado natural"],
        notas_proceso=(
            "DECISION DE VENTA: Opcion A) Producto se ensaca directamente como harina basica "
            "(uso alimentacion animal) - va directo a E9. "
            "Opcion B) Pasa a E8 para mejoramiento (molienda + homogenizacion + mezcla SKU) "
            "para producto premium humanos/nutraceutica. "
            "Considerar valor distinto en ambas opciones."
        ),
        datos_faltantes=[
            "Demand split: % volumen que va a A (alimentacion) vs B (premium)",
            "Precio venta diferenciado por opcion",
            "Tiempo enfriado necesario hasta 8-10% humedad",
        ],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="operario",
    )
    e8 = EtapaPlanta(
        id="E8_HOMOGENEIZACION",
        nombre="E8. Homogeneizacion (molienda + mezcla SKU)",
        orden=9,
        descripcion=(
            "OPCIONAL - solo SKU premium. Molienda fina + homogenizacion del producto. "
            "Calidad evaluada y analizada. Mezcla con diferentes MMPP para alcanzar "
            "spec/demanda comercial. Equipo: homogenizador/mezclador de harinas."
        ),
        masa_input_kg_h=throughput_kg_h * 0.245,
        yield_pct=0.995,
        perdidas_pct=0.003,
        humedad_post_etapa=(0.08, 0.10),
        energia_kwh_por_kg=0.030,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.06,
        tiempo_proceso_min=2.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.6, "kg/h"),
        mo_directa=["Encargado Proceso", "Laboratorista"],
        mo_general=["Operario Limpieza"],
        equipos_energeticos=["Homogenizador/mezclador harinas", "Sistema Transportador"],
        notas_proceso=(
            "Solo aplica cuando E7 deriva a 'opcion B premium'. Permite mezclar MMPP "
            "para alcanzar especificaciones del cliente (proteina, fibra, ORAC, etc)."
        ),
        datos_faltantes=[
            "Recetas formales por SKU premium (% mezcla MMPP)",
            "Plan muestreo QC formal por lote",
            "Tiempo mezcla hasta homogeneidad",
            "Granulometria target por mercado (feed acuicola vs pet food vs humanos)",
        ],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="calidad",
    )
    e9 = EtapaPlanta(
        id="E9_ENSACADO",
        nombre="E9. Ensacado / Palletizado",
        orden=10,
        descripcion="Llenado de sacos/big bags + palletizado. Sellado en 2 fases.",
        masa_input_kg_h=throughput_kg_h * 0.243,
        yield_pct=0.998,
        perdidas_pct=0.002,
        humedad_post_etapa=(0.08, 0.10),
        energia_kwh_por_kg=0.012,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.18,
        tiempo_proceso_min=10.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.5, "kg/h"),
        mo_directa=["Encargado"],
        mo_general=["Limpieza"],
        equipos_energeticos=["Sistema de Llenado", "Sistema de Ensacado"],
        materiales=["Hilo de coser", "Sacos", "Pallets"],
        notas_proceso="Sellado en 2 fases: 1) plancha calor (sellado polvo) 2) cosido. Evaluar pelletizado.",
        datos_faltantes=["Mix big bag 1000kg vs saco 25kg por mercado", "Capacidad absorcion hidrica sacos"],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="operario",
    )
    e10 = EtapaPlanta(
        id="E10_ETIQUETADO",
        nombre="E10. Etiquetado / Codificacion / Almacenamiento",
        orden=11,
        descripcion="Etiqueta, codigo lote, traslado a bodega con grua horquilla.",
        masa_input_kg_h=throughput_kg_h * 0.242,
        yield_pct=0.999,
        perdidas_pct=0.001,
        humedad_post_etapa=(0.08, 0.10),
        energia_kwh_por_kg=0.005,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.05,
        tiempo_proceso_min=3.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.5, "kg/h"),
        mo_directa=["Encargado", "Laboratorista"],
        mo_general=["Gruero de Horquilla"],
        equipos_energeticos=[],
        repuestos=["Tinta impresora etiquetas"],
        datos_faltantes=["Sistema codificacion (QR/datamatrix)", "Capacidad bodega real"],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="operario",
    )
    e11 = EtapaPlanta(
        id="E11_CONTROL_CALIDAD",
        nombre="E11. Control de Calidad y Trazabilidad",
        orden=12,
        descripcion=(
            "Muestras para validar calidad de producto + trazabilidad por lote. "
            "Genera confianza con clientes y permite trazabilidad de los productos."
        ),
        masa_input_kg_h=throughput_kg_h * 0.001,   # solo muestras
        yield_pct=1.0,
        perdidas_pct=0.0,
        humedad_post_etapa=(0.08, 0.10),
        energia_kwh_por_kg=0.0,
        agua_l_por_kg=0.0,
        hh_por_ton_input=2.0,                       # alto en HH por muestra
        tiempo_proceso_min=1.0,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.01, "kg/h"),
        mo_directa=["Laboratorista"],
        notas_proceso=(
            "Zona almacenamiento separada para muestras retencion. Esencial para "
            "auditorias de clientes export (Asia/EU/USA) y certificacion ISO/HACCP."
        ),
        datos_faltantes=[
            "Tamano muestra retencion por SKU (kg)",
            "Tiempo retencion exigido (12 vs 24 meses por mercado)",
            "Parametros analiticos minimos por SKU",
        ],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="calidad",
    )

    etapas = [e1, e2, e3, e4a, e4b, e5, e6, e7, e8, e9, e10, e11]
    return etapas


# =========================================================================
# MATRIZ PRODUCTOS x ETAPAS (Excel Agrosphere)
# =========================================================================
@dataclass
class ProductoEtapas:
    """Producto/MMPP y por que etapas pasa + rendimiento MSF."""
    codigo: str
    variante: str
    etapas_aplicables: list[str]    # ids de etapas
    rendimiento_msf_pct: float = 0.0   # materia seca final (kg producto / kg MMPP)
    notas: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def productos_seed() -> list[ProductoEtapas]:
    """Matriz oficial Agrosphere (Cuadro Etapas x Productos del Excel)."""
    return [
        ProductoEtapas(
            codigo="TOMASA_1",
            variante="Cold",
            etapas_aplicables=["E1_RECEPCION", "E2_ESTANDARIZACION", "E3_PEF", "E4A_PRENSADO_MECANICO",
                                "E5_LIQUIDOS_RESIDUALES", "E6A_DESHIDRATACION_PRINCIPAL", "E7_ENFRIADO",
                                "E8_HOMOGENEIZACION", "E9_ENSACADO", "E10_ETIQUETADO", "E11_CONTROL_CALIDAD"],
            rendimiento_msf_pct=0.30,
            notas="Linea Cold: prensado mecanico. MSF 30%.",
        ),
        ProductoEtapas(
            codigo="TOMASA_2",
            variante="Hot",
            etapas_aplicables=["E1_RECEPCION", "E2_ESTANDARIZACION", "E3_PEF", "E4B_PRENSADO_CENTRIFUGO",
                                "E5_LIQUIDOS_RESIDUALES", "E6A_DESHIDRATACION_PRINCIPAL", "E7_ENFRIADO",
                                "E8_HOMOGENEIZACION", "E9_ENSACADO", "E10_ETIQUETADO", "E11_CONTROL_CALIDAD"],
            rendimiento_msf_pct=0.25,
            notas="Linea Hot: tricanter centrifugo. MSF 25%.",
        ),
        ProductoEtapas(
            codigo="ORUJO_1",
            variante="Tinto",
            etapas_aplicables=["E1_RECEPCION"],
            rendimiento_msf_pct=0.0,
            notas="Proceso a definir post Recepcion. Posiblemente Cold (E2-E11).",
        ),
        ProductoEtapas(
            codigo="ORUJO_2",
            variante="Blanco",
            etapas_aplicables=["E1_RECEPCION"],
            rendimiento_msf_pct=0.0,
            notas="Proceso a definir.",
        ),
        ProductoEtapas(
            codigo="ALPERUJO_1",
            variante="EV (Extra Virgen)",
            etapas_aplicables=["E1_RECEPCION"],
            rendimiento_msf_pct=0.0,
            notas="Proceso a definir.",
        ),
        ProductoEtapas(
            codigo="ALPERUJO_2",
            variante="V (Virgen)",
            etapas_aplicables=["E1_RECEPCION"],
            rendimiento_msf_pct=0.0,
            notas="Proceso a definir.",
        ),
        ProductoEtapas(
            codigo="POMASA_1",
            variante="Roja",
            etapas_aplicables=["E1_RECEPCION"],
            rendimiento_msf_pct=0.0,
            notas="Proceso a definir.",
        ),
        ProductoEtapas(
            codigo="POMASA_2",
            variante="Verde",
            etapas_aplicables=["E1_RECEPCION"],
            rendimiento_msf_pct=0.0,
            notas="Proceso a definir.",
        ),
    ]


def _detectar_alarmas_etapas(etapas: list[EtapaPlanta]) -> list[dict]:
    alarmas = []
    for e in etapas:
        if e.es_bottleneck:
            alarmas.append({
                "tipo": "bottleneck_etapa",
                "severidad": "alta",
                "etapa": e.id,
                "nombre": e.nombre,
                "utilizacion_pct": round(e.utilizacion_pct, 3),
                "mensaje": f"⚠️ {e.nombre} a {e.utilizacion_pct:.0%} capacidad: cuello de botella.",
                "accion": "Ampliar capacidad o reducir throughput aguas arriba.",
            })
    for e in etapas:
        if e.nivel_calibracion == NivelDato.PD and e.datos_faltantes:
            alarmas.append({
                "tipo": "datos_faltantes",
                "severidad": "media",
                "etapa": e.id,
                "nombre": e.nombre,
                "datos_pendientes": e.datos_faltantes,
                "mensaje": f"📋 {e.nombre}: faltan {len(e.datos_faltantes)} datos para calibrar.",
            })
    for e in etapas:
        if e.yield_pct < 0.50:
            alarmas.append({
                "tipo": "yield_bajo",
                "severidad": "baja",
                "etapa": e.id,
                "yield_pct": round(e.yield_pct, 3),
                "mensaje": f"📉 {e.nombre} con yield {e.yield_pct:.0%} (normal si es secado/separacion).",
            })
    return alarmas


def computar_balance_etapas(
    etapas: list[EtapaPlanta] | None = None,
    throughput_kg_h: float = 2000.0,
    incluir_respaldo: bool = False,
) -> BalancePorEtapas:
    if etapas is None:
        etapas = etapas_seed(throughput_kg_h, incluir_respaldo=incluir_respaldo)
    if not etapas:
        raise ValueError("Lista de etapas vacia.")

    masa_in_total = etapas[0].masa_input_kg_h
    masa_out_final = etapas[-1].masa_output_kg_h
    yield_total = masa_out_final / masa_in_total if masa_in_total > 0 else 0.0

    energia_total = sum(e.consumo_energia_kwh_h for e in etapas)
    agua_total = sum(e.consumo_agua_l_h for e in etapas)
    hh_turno = sum((e.masa_input_kg_h / 1000.0) * e.hh_por_ton_input * 8.0 for e in etapas)
    tiempo_total = sum(e.tiempo_proceso_min for e in etapas)

    bottlenecks = [e.id for e in etapas if e.es_bottleneck]
    completitud = sum(e.datos_completitud_pct for e in etapas) / len(etapas)

    intensidades = {
        "energia_kwh_por_kg_producto": round(energia_total / max(masa_out_final, 1), 3),
        "agua_l_por_kg_producto": round(agua_total / max(masa_out_final, 1), 3),
        "hh_por_t_producto": round(hh_turno / max(masa_out_final / 1000 * 8, 1), 3),
        "perdidas_totales_kg_h": round(sum(e.perdidas_kg_h for e in etapas), 2),
        "energia_kwh_por_kg_mmpp": round(energia_total / max(masa_in_total, 1), 3),
        "tiempo_min_por_ton": round(tiempo_total / max(masa_out_final / 1000.0, 0.001), 1),
    }
    alarmas = _detectar_alarmas_etapas(etapas)

    return BalancePorEtapas(
        etapas=etapas,
        masa_entrada_total_kg_h=masa_in_total,
        masa_salida_final_kg_h=masa_out_final,
        yield_total_proceso=yield_total,
        energia_total_kwh_h=energia_total,
        agua_total_l_h=agua_total,
        hh_totales_turno=hh_turno,
        tiempo_proceso_total_min=tiempo_total,
        bottlenecks=bottlenecks,
        completitud_datos_pct=completitud,
        intensidades_acumuladas=intensidades,
        alarmas=alarmas,
    )


def resumen_datos_faltantes(etapas: list[EtapaPlanta] | None = None) -> dict:
    if etapas is None:
        etapas = etapas_seed()
    pendientes_criticos, pendientes_medios, completos = [], [], []
    for e in etapas:
        item = {
            "etapa": e.id, "nombre": e.nombre, "orden": e.orden,
            "completitud_pct": e.datos_completitud_pct,
            "nivel": e.nivel_calibracion.value,
            "datos_faltantes": e.datos_faltantes,
        }
        if e.nivel_calibracion == NivelDato.OK_VALIDADO:
            completos.append(item)
        elif e.nivel_calibracion == NivelDato.OK_PROVISORIO:
            pendientes_medios.append(item)
        else:
            pendientes_criticos.append(item)
    return {
        "total_etapas": len(etapas),
        "validadas": len(completos),
        "provisorias": len(pendientes_medios),
        "sin_validar": len(pendientes_criticos),
        "completitud_promedio_pct": round(
            sum(e.datos_completitud_pct for e in etapas) / len(etapas), 1
        ),
        "criticos_PD": pendientes_criticos,
        "medios_PROVISORIO": pendientes_medios,
        "completos_VALIDADO": completos,
    }


def matriz_productos_x_etapas(
    productos: list[ProductoEtapas] | None = None,
    etapas: list[EtapaPlanta] | None = None,
) -> dict:
    """Matriz cruzada: para cada producto/MMPP, que etapas aplica.

    Calcula tambien el yield acumulado teorico siguiendo solo las etapas
    aplicables.
    """
    if productos is None:
        productos = productos_seed()
    if etapas is None:
        etapas = etapas_seed()

    etapas_by_id = {e.id: e for e in etapas}
    productos_data = []
    for p in productos:
        etapas_aplicables_completas = []
        yield_acumulado = 1.0
        tiempo_acumulado = 0.0
        for eid in p.etapas_aplicables:
            e = etapas_by_id.get(eid)
            if e:
                yield_acumulado *= e.yield_pct
                tiempo_acumulado += e.tiempo_proceso_min
                etapas_aplicables_completas.append({
                    "id": e.id,
                    "nombre": e.nombre,
                    "orden": e.orden,
                    "yield": e.yield_pct,
                    "tiempo_min": e.tiempo_proceso_min,
                })
        productos_data.append({
            **p.to_dict(),
            "yield_acumulado_teorico": round(yield_acumulado, 4),
            "tiempo_proceso_min": round(tiempo_acumulado, 1),
            "etapas_detalle": etapas_aplicables_completas,
            "cantidad_etapas": len(etapas_aplicables_completas),
            "tiene_proceso_definido": len(etapas_aplicables_completas) > 1,
        })

    return {
        "productos": productos_data,
        "total_productos": len(productos),
        "productos_con_proceso_definido": sum(
            1 for p in productos_data if p["tiene_proceso_definido"]
        ),
        "productos_solo_recepcion": sum(
            1 for p in productos_data if not p["tiene_proceso_definido"]
        ),
        "etapas_universo": [
            {"id": e.id, "nombre": e.nombre, "orden": e.orden} for e in etapas
        ],
    }
