"""Balances por etapa de la planta Trongkai.

12 etapas del proceso completo upcycling agroindustrial:
RECEPCION -> ALMACENAMIENTO -> LAVADO -> TRITURACION -> PEF_OPTICEPT ->
EXTRACCION_LIQUIDA -> CENTRIFUGACION -> SECADO_ROTATIVO -> MICROMOLIENDA ->
MEZCLADO -> ENVASADO -> LOGISTICA

Cada etapa consume:
- masa de entrada (kg/h)
- energia (kWh)
- agua (L/h)
- horas-hombre (HH)
- aporta perdidas (% del input)
- tiene yield (% que pasa a la siguiente etapa)
- tiene capacidad maxima (kg/h) -> usado para bottleneck

Datos faltantes: nivel de completitud de calibracion (PD vs validado).
Esto permite a la UI decir "no puedo predecir bien hasta que tengamos X".
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Literal


class NivelDato(StrEnum):
    """Calidad de calibracion del parametro de la etapa."""
    PD = "PD"                          # placeholder - dato hardcoded sin validar
    OK_PROVISORIO = "OK_PROVISORIO"    # validado por benchmark literatura
    OK_VALIDADO = "OK_VALIDADO"         # validado en planta real


@dataclass
class CapacidadEtapa:
    """Capacidad maxima de la etapa (kg/h o L/h o numero)."""
    valor_maximo: float
    unidad: str = "kg/h"
    nivel_dato: NivelDato = NivelDato.PD


@dataclass
class EtapaPlanta:
    """Una etapa del proceso productivo."""
    id: str                            # "PEF_OPTICEPT"
    nombre: str                        # "PEF Opticept"
    orden: int                          # 1..12
    descripcion: str
    # Inputs/Outputs
    masa_input_kg_h: float
    yield_pct: float                    # 0..1 (% que pasa a siguiente)
    perdidas_pct: float = 0.02         # 0..1
    # Consumos por kg de input
    energia_kwh_por_kg: float = 0.0
    agua_l_por_kg: float = 0.0
    hh_por_ton_input: float = 0.0      # horas hombre por TONELADA input
    # Capacidad y operacion
    capacidad: CapacidadEtapa = field(default_factory=lambda: CapacidadEtapa(1000.0))
    horas_operacion_dia: float = 16.0
    dias_operacion_anual: float = 300.0
    # Calidad de datos
    datos_faltantes: list[str] = field(default_factory=list)
    nivel_calibracion: NivelDato = NivelDato.PD
    # Para integracion con otros balances
    equipo_energetico_principal: str = ""    # match con energia.py
    equipo_hidrico_principal: str = ""        # match con agua.py
    categoria_rrhh_principal: str = ""        # match con rrhh.py

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
        """% completitud: VALIDADO=100, PROVISORIO=60, PD=20."""
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
        return d


@dataclass
class BalancePorEtapas:
    etapas: list[EtapaPlanta]
    masa_entrada_total_kg_h: float
    masa_salida_final_kg_h: float
    yield_total_proceso: float            # producto_final / mmpp_entrada
    energia_total_kwh_h: float
    agua_total_l_h: float
    hh_totales_turno: float
    bottlenecks: list[str]
    completitud_datos_pct: float          # promedio de completitud
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
            "bottlenecks": self.bottlenecks,
            "completitud_datos_pct": round(self.completitud_datos_pct, 1),
            "intensidades_acumuladas": self.intensidades_acumuladas,
            "alarmas": self.alarmas,
        }


def etapas_seed(throughput_kg_h: float = 2000.0) -> list[EtapaPlanta]:
    """Seed de 12 etapas calibradas a un throughput nominal en kg/h.

    Throughput default = 2 t/h (-> 24 t/dia -> ~5800 t/ano operando 8h/dia 300 dias)
    """
    e1 = EtapaPlanta(
        id="RECEPCION",
        nombre="1. Recepcion de MMPP",
        orden=1,
        descripcion="Llegada camiones, pesaje en bascula, muestreo calidad y registro.",
        masa_input_kg_h=throughput_kg_h,
        yield_pct=1.00,
        perdidas_pct=0.005,
        energia_kwh_por_kg=0.0008,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.10,
        capacidad=CapacidadEtapa(throughput_kg_h * 2.0, "kg/h", NivelDato.OK_PROVISORIO),
        datos_faltantes=["Frecuencia llegada camiones real", "Tiempo promedio descarga"],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="operario",
    )
    e2 = EtapaPlanta(
        id="ALMACENAMIENTO",
        nombre="2. Almacenamiento humedo",
        orden=2,
        descripcion="Silos refrigerados o piscinas con control de pH para evitar fermentacion.",
        masa_input_kg_h=throughput_kg_h * 0.995,
        yield_pct=0.99,
        perdidas_pct=0.01,
        energia_kwh_por_kg=0.015,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.02,
        capacidad=CapacidadEtapa(throughput_kg_h * 3.0, "kg/h"),
        datos_faltantes=["Capacidad silos real (m3)", "Tiempo max almacenamiento sin degradar"],
        nivel_calibracion=NivelDato.PD,
    )
    e3 = EtapaPlanta(
        id="LAVADO",
        nombre="3. Lavado y limpieza",
        orden=3,
        descripcion="Remocion de tierra, piedras, hojas. Sistema de tambor rotativo + tamices.",
        masa_input_kg_h=throughput_kg_h * 0.985,
        yield_pct=0.97,
        perdidas_pct=0.03,
        energia_kwh_por_kg=0.025,
        agua_l_por_kg=2.5,
        hh_por_ton_input=0.15,
        capacidad=CapacidadEtapa(throughput_kg_h * 1.5, "kg/h"),
        datos_faltantes=["Volumen agua efectivo segun MMPP", "Tasa recirculacion lavado"],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        equipo_hidrico_principal="Lavadora MMPP",
        categoria_rrhh_principal="operario",
    )
    e4 = EtapaPlanta(
        id="TRITURACION",
        nombre="4. Trituracion primaria",
        orden=4,
        descripcion="Molino de martillos para reduccion a 5-10mm.",
        masa_input_kg_h=throughput_kg_h * 0.955,
        yield_pct=0.99,
        perdidas_pct=0.005,
        energia_kwh_por_kg=0.045,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.05,
        capacidad=CapacidadEtapa(throughput_kg_h * 1.4, "kg/h"),
        datos_faltantes=["Granulometria target por SKU", "Tasa desgaste martillos"],
        nivel_calibracion=NivelDato.PD,
        equipo_energetico_principal="Micromolienda",
    )
    e5 = EtapaPlanta(
        id="PEF_OPTICEPT",
        nombre="5. PEF Opticept (Electroporacion)",
        orden=5,
        descripcion="Pulsos electricos de alta tension para ruptura celular sin calor.",
        masa_input_kg_h=throughput_kg_h * 0.945,
        yield_pct=0.99,
        perdidas_pct=0.005,
        energia_kwh_por_kg=0.13,
        agua_l_por_kg=1.5,
        hh_por_ton_input=0.06,
        capacidad=CapacidadEtapa(throughput_kg_h * 1.0, "kg/h", NivelDato.OK_PROVISORIO),
        datos_faltantes=[
            "kV optimo por MMPP (orujo vs alperujo vs tomasa)",
            "Numero de pulsos optimo (campo electrico)",
            "Yield real vs benchmark Pulsemaster"
        ],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        equipo_energetico_principal="PEF Opticept",
        equipo_hidrico_principal="PEF Opticept",
    )
    e6 = EtapaPlanta(
        id="EXTRACCION_LIQUIDA",
        nombre="6. Extraccion liquida",
        orden=6,
        descripcion="Prensa horizontal o decanter para separar fase liquida (jugo/aceite) de solida.",
        masa_input_kg_h=throughput_kg_h * 0.935,
        yield_pct=0.95,
        perdidas_pct=0.005,
        energia_kwh_por_kg=0.04,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.08,
        capacidad=CapacidadEtapa(throughput_kg_h * 1.2, "kg/h"),
        datos_faltantes=["Yield aceite/jugo por MMPP", "Configuracion optima prensa"],
        nivel_calibracion=NivelDato.PD,
    )
    e7 = EtapaPlanta(
        id="CENTRIFUGACION",
        nombre="7. Centrifugacion (separacion fases)",
        orden=7,
        descripcion="Separacion 3 fases: aceite, agua de vegetacion y solidos finos.",
        masa_input_kg_h=throughput_kg_h * 0.30,    # solo la fase liquida pasa
        yield_pct=0.98,
        perdidas_pct=0.01,
        energia_kwh_por_kg=0.025,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.04,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.5, "kg/h"),
        datos_faltantes=["G-force optimo por MMPP", "Tiempo residencia"],
        nivel_calibracion=NivelDato.PD,
    )
    e8 = EtapaPlanta(
        id="SECADO_ROTATIVO",
        nombre="8. Secado rotativo",
        orden=8,
        descripcion="Reduccion humedad 60% -> 10% en tambor rotativo a 80-110C.",
        masa_input_kg_h=throughput_kg_h * 0.65,    # solo fase solida + reentrada
        yield_pct=0.50,                              # 50% del agua se evapora
        perdidas_pct=0.005,
        energia_kwh_por_kg=0.45,                    # alto consumo
        agua_l_por_kg=0.5,                           # algo para vapor
        hh_por_ton_input=0.10,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.8, "kg/h", NivelDato.OK_PROVISORIO),
        datos_faltantes=[
            "Temperatura optima sin degradar compuestos activos",
            "Tiempo residencia por MMPP",
            "Calor especifico de la pasta"
        ],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        equipo_energetico_principal="Secador rotativo",
        equipo_hidrico_principal="Caldera biomasa",
    )
    e9 = EtapaPlanta(
        id="MICROMOLIENDA",
        nombre="9. Micromolienda fina",
        orden=9,
        descripcion="Molino de impacto + clasificador para reducir a 100-200 micras (harina premium).",
        masa_input_kg_h=throughput_kg_h * 0.325,
        yield_pct=0.97,
        perdidas_pct=0.02,
        energia_kwh_por_kg=0.20,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.06,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.5, "kg/h"),
        datos_faltantes=["Granulometria por SKU final", "Tasa desgaste rotor"],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        equipo_energetico_principal="Micromolienda",
        categoria_rrhh_principal="operario",
    )
    e10 = EtapaPlanta(
        id="MEZCLADO",
        nombre="10. Mezclado y formulacion",
        orden=10,
        descripcion="Mezclador de cintas. Combinacion de fracciones para formular cada SKU final.",
        masa_input_kg_h=throughput_kg_h * 0.315,
        yield_pct=0.995,
        perdidas_pct=0.003,
        energia_kwh_por_kg=0.012,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.10,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.6, "kg/h"),
        datos_faltantes=["Recetas formales por SKU", "Tiempo mezcla homogenea"],
        nivel_calibracion=NivelDato.PD,
        categoria_rrhh_principal="calidad",
    )
    e11 = EtapaPlanta(
        id="ENVASADO",
        nombre="11. Envasado (big bags/sacos)",
        orden=11,
        descripcion="Llenadora gravimetrica + costura/sellado. Big bags 1000kg o sacos 25kg.",
        masa_input_kg_h=throughput_kg_h * 0.313,
        yield_pct=0.998,
        perdidas_pct=0.002,
        energia_kwh_por_kg=0.008,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.20,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.5, "kg/h"),
        datos_faltantes=["Mix big bag vs saco por mercado", "Tiempo cambio formato"],
        nivel_calibracion=NivelDato.OK_PROVISORIO,
        categoria_rrhh_principal="operario",
    )
    e12 = EtapaPlanta(
        id="LOGISTICA",
        nombre="12. Despacho y logistica",
        orden=12,
        descripcion="Carga camiones (FCL 24t o LCL pallet). Documentacion exportacion.",
        masa_input_kg_h=throughput_kg_h * 0.312,
        yield_pct=1.0,
        perdidas_pct=0.0,
        energia_kwh_por_kg=0.002,
        agua_l_por_kg=0.0,
        hh_por_ton_input=0.05,
        capacidad=CapacidadEtapa(throughput_kg_h * 0.5, "kg/h"),
        datos_faltantes=["Tiempo medio carga camion", "Acuerdos exportacion firmes"],
        nivel_calibracion=NivelDato.PD,
        categoria_rrhh_principal="admin",
    )
    return [e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11, e12]


def _detectar_alarmas_etapas(etapas: list[EtapaPlanta]) -> list[dict]:
    alarmas = []
    # Bottlenecks
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
    # Datos PD criticos
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
    # Yield muy bajo
    for e in etapas:
        if e.yield_pct < 0.50:
            alarmas.append({
                "tipo": "yield_bajo",
                "severidad": "baja",
                "etapa": e.id,
                "yield_pct": round(e.yield_pct, 3),
                "mensaje": f"📉 {e.nombre} con yield {e.yield_pct:.0%} (normal solo si es secado/evaporacion).",
            })
    return alarmas


def computar_balance_etapas(
    etapas: list[EtapaPlanta] | None = None,
    throughput_kg_h: float = 2000.0,
) -> BalancePorEtapas:
    """Calcula balance integral por etapa de la planta."""
    if etapas is None:
        etapas = etapas_seed(throughput_kg_h)

    if not etapas:
        raise ValueError("Lista de etapas vacia.")

    masa_in_total = etapas[0].masa_input_kg_h
    masa_out_final = etapas[-1].masa_output_kg_h
    yield_total = masa_out_final / masa_in_total if masa_in_total > 0 else 0.0

    energia_total = sum(e.consumo_energia_kwh_h for e in etapas)
    agua_total = sum(e.consumo_agua_l_h for e in etapas)
    # HH por turno (8h) = sum (input_ton_h * hh_per_ton_input * 8h)
    hh_turno = sum(
        (e.masa_input_kg_h / 1000.0) * e.hh_por_ton_input * 8.0 for e in etapas
    )

    bottlenecks = [e.id for e in etapas if e.es_bottleneck]
    completitud = sum(e.datos_completitud_pct for e in etapas) / len(etapas)

    intensidades = {
        "energia_kwh_por_kg_producto": round(energia_total / max(masa_out_final, 1), 3),
        "agua_l_por_kg_producto": round(agua_total / max(masa_out_final, 1), 3),
        "hh_por_t_producto": round(hh_turno / max(masa_out_final / 1000 * 8, 1), 3),
        "perdidas_totales_kg_h": round(sum(e.perdidas_kg_h for e in etapas), 2),
        "energia_kwh_por_kg_mmpp": round(energia_total / max(masa_in_total, 1), 3),
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
        bottlenecks=bottlenecks,
        completitud_datos_pct=completitud,
        intensidades_acumuladas=intensidades,
        alarmas=alarmas,
    )


def resumen_datos_faltantes(etapas: list[EtapaPlanta] | None = None) -> dict:
    """Para la guia: lista de TODO lo que falta calibrar por etapa.

    Genera un checklist priorizado por impacto y completitud actual.
    """
    if etapas is None:
        etapas = etapas_seed()

    pendientes_criticos = []   # PD con datos faltantes
    pendientes_medios = []      # OK_PROVISORIO con datos faltantes
    completos = []              # OK_VALIDADO

    for e in etapas:
        item = {
            "etapa": e.id,
            "nombre": e.nombre,
            "orden": e.orden,
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
