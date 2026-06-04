"""Costeo por etapa y por SKU usando los parametros de planta.

Costo de cada etapa = MO + energia + calor + agua + materiales + arriendo prorrateado.

Costo total por SKU = suma de costos de etapas aplicables (Cuadro Etapas x Productos)
                    + flete MMPP entrada + flete despacho.

Resultado en CLP/kg producto y USD/kg producto.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field

from .etapas import EtapaPlanta, etapas_seed, productos_seed
from .parametros_planta import ParametrosPlanta, cargar_parametros


@dataclass
class CostoEtapa:
    etapa_id: str
    nombre: str
    orden: int
    # CLP por hora de operacion a throughput nominal
    costo_mo_clp_h: float = 0.0
    costo_energia_clp_h: float = 0.0
    costo_calor_clp_h: float = 0.0
    costo_agua_clp_h: float = 0.0
    costo_materiales_clp_h: float = 0.0
    costo_arriendo_clp_h: float = 0.0    # solo PEF en E3, etc
    # Totales
    costo_total_clp_h: float = 0.0
    costo_por_kg_input_clp: float = 0.0
    costo_por_kg_output_clp: float = 0.0
    masa_input_kg_h: float = 0.0
    masa_output_kg_h: float = 0.0

    def to_dict(self) -> dict:
        return {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in asdict(self).items()
        }


def _cargo_mo_clp_h(etapa: EtapaPlanta, params: ParametrosPlanta) -> float:
    """Costo MO/h: suma sueldos de los cargos MO directa + general.

    Heuristica: cada nombre listado en mo_directa/general aporta una fraccion
    de su tiempo segun hh_por_ton_input * masa_input/1000.
    """
    # tiempo total de personal en la etapa en h/h operacion
    hh_h = (etapa.masa_input_kg_h / 1000.0) * etapa.hh_por_ton_input
    if hh_h <= 0:
        return 0.0
    sueldos_by_cargo = {s.cargo: s.costo_hora_clp for s in params.sueldos}
    # Buscar match por palabra clave en los nombres del cargo
    def costo_para(nombre: str) -> float:
        nl = nombre.lower()
        if "laborator" in nl:
            return sueldos_by_cargo.get("Laboratorista (QC)", 5000)
        if "supervis" in nl:
            return sueldos_by_cargo.get("Supervisor Turno", 5000)
        if "gruero" in nl:
            return sueldos_by_cargo.get("Gruero Horquilla", 5000)
        if "limpieza" in nl:
            return sueldos_by_cargo.get("Operario Limpieza", 5000)
        if "recepcion" in nl or "recepción" in nl:
            return sueldos_by_cargo.get("Encargado Recepcion", 5000)
        if "secado" in nl:
            return sueldos_by_cargo.get("Encargado Secado", 5000)
        if "encargado" in nl:
            return sueldos_by_cargo.get("Encargado Proceso", 5000)
        return 4500.0  # default operario

    cargos = list(etapa.mo_directa) + list(etapa.mo_general)
    if not cargos:
        return 0.0
    costo_promedio_cargo = sum(costo_para(c) for c in cargos) / len(cargos)
    return costo_promedio_cargo * hh_h


def _costo_energia_etapa(etapa: EtapaPlanta, params: ParametrosPlanta) -> float:
    """CLP/h de energia electrica consumida en esta etapa."""
    return etapa.consumo_energia_kwh_h * params.energia.tarifa_promedio_clp_kwh


def _costo_calor_etapa(etapa: EtapaPlanta, params: ParametrosPlanta) -> float:
    """CLP/h calor residual. Solo aplica si la etapa usa calor (deshidratacion)."""
    if "DESHIDRATACION" not in etapa.id:
        return 0.0
    # Estimacion: 100% del consumo termico de la etapa se cubre con calor residual
    # (la deshidratacion E6a usa vapor + calor residual La Gloria)
    kwh_h_termico = etapa.consumo_energia_kwh_h * 4   # ~4x el electrico
    if params.calor_residual.disponible and not etapa.es_respaldo:
        return (kwh_h_termico * params.calor_residual.costo_kwh_termico_clp
                + params.calor_residual.costo_servicio_clp_mes / (16 * 30))
    # Si es respaldo (bomba calor): se cobra como electricidad
    return kwh_h_termico * params.energia.tarifa_promedio_clp_kwh * 0.30   # COP ~3


def _costo_agua_etapa(etapa: EtapaPlanta, params: ParametrosPlanta) -> float:
    """CLP/h de agua segun origen.

    Convencion: lavado y proceso usan agua industrial (pozo).
    CIP y vapor pueden usar llave en momentos puntuales (simplificacion: industrial).
    """
    if etapa.consumo_agua_l_h <= 0:
        return 0.0
    m3_h = etapa.consumo_agua_l_h / 1000.0
    # Default: agua industrial (pozo propio)
    return m3_h * params.agua.agua_industrial_clp_m3


def _costo_materiales_etapa(etapa: EtapaPlanta, params: ParametrosPlanta) -> float:
    """CLP/h de materiales consumibles + repuestos prorrateados.

    Heuristica simplificada por etapa.
    """
    costo = 0.0
    # Electrodos PEF: ~600k cada cambio cada 300h
    if "PEF" in etapa.id:
        costo += 600_000 / 300.0   # CLP/h
    # Filtros prensa/tricanter: 80k cada 200h
    if "PRENSADO" in etapa.id:
        costo += 80_000 / 200.0
    # Sacos/hilo/pallets ensacado: 80 CLP/kg producto
    if "ENSACADO" in etapa.id:
        costo += etapa.masa_output_kg_h * 80
    # Tinta etiquetado: 30k cada 500h
    if "ETIQUETADO" in etapa.id or "TOMA_MUESTRA" in etapa.id:
        costo += 30_000 / 500.0
    return costo


def _costo_arriendo_etapa(etapa: EtapaPlanta, params: ParametrosPlanta) -> float:
    """CLP/h de arriendo equipos.

    PEF -> arriendo_pef_clp_mes (prorrateado a 16h/dia * 30d = 480h/mes)
    Tricanter -> arriendo_tricanter_clp_mes
    """
    horas_operacion_mes = 16.0 * 30.0    # 480h/mes
    if "PEF" in etapa.id:
        return params.arriendos.arriendo_pef_clp_mes / horas_operacion_mes
    if "PRENSADO_CENTRIFUGO" in etapa.id or "TRICANTER" in etapa.id.upper():
        return params.arriendos.arriendo_tricanter_clp_mes / horas_operacion_mes
    return 0.0


def computar_costo_etapa(etapa: EtapaPlanta, params: ParametrosPlanta) -> CostoEtapa:
    costo_mo = _cargo_mo_clp_h(etapa, params)
    costo_energia = _costo_energia_etapa(etapa, params)
    costo_calor = _costo_calor_etapa(etapa, params)
    costo_agua = _costo_agua_etapa(etapa, params)
    costo_materiales = _costo_materiales_etapa(etapa, params)
    costo_arriendo = _costo_arriendo_etapa(etapa, params)
    total = costo_mo + costo_energia + costo_calor + costo_agua + costo_materiales + costo_arriendo

    return CostoEtapa(
        etapa_id=etapa.id,
        nombre=etapa.nombre,
        orden=etapa.orden,
        costo_mo_clp_h=costo_mo,
        costo_energia_clp_h=costo_energia,
        costo_calor_clp_h=costo_calor,
        costo_agua_clp_h=costo_agua,
        costo_materiales_clp_h=costo_materiales,
        costo_arriendo_clp_h=costo_arriendo,
        costo_total_clp_h=total,
        costo_por_kg_input_clp=total / max(etapa.masa_input_kg_h, 1),
        costo_por_kg_output_clp=total / max(etapa.masa_output_kg_h, 1),
        masa_input_kg_h=etapa.masa_input_kg_h,
        masa_output_kg_h=etapa.masa_output_kg_h,
    )


def computar_costeo_completo(
    throughput_kg_h: float = 2000.0,
    incluir_respaldo: bool = False,
    params: ParametrosPlanta | None = None,
) -> dict:
    """Costeo de las 11 etapas + por SKU."""
    if params is None:
        params = cargar_parametros()
    etapas = etapas_seed(throughput_kg_h, incluir_respaldo=incluir_respaldo)
    costos_etapas = [computar_costo_etapa(e, params) for e in etapas]

    masa_in = etapas[0].masa_input_kg_h
    masa_out = etapas[-1].masa_output_kg_h
    total_clp_h = sum(c.costo_total_clp_h for c in costos_etapas)

    # Costo por SKU (matriz productos x etapas)
    productos = productos_seed()
    costos_etapa_by_id = {c.etapa_id: c for c in costos_etapas}
    costos_por_sku = []
    for p in productos:
        costo_etapas_aplicables_clp_h = sum(
            costos_etapa_by_id[eid].costo_total_clp_h
            for eid in p.etapas_aplicables
            if eid in costos_etapa_by_id
        )
        # Producto generado por esta linea (kg/h) - aproximacion: usa la ultima etapa del proceso
        ultima_etapa_id = p.etapas_aplicables[-1] if p.etapas_aplicables else None
        masa_out_sku = (
            costos_etapa_by_id[ultima_etapa_id].masa_output_kg_h
            if ultima_etapa_id and ultima_etapa_id in costos_etapa_by_id
            else 0
        )
        costo_kg_producto = (
            costo_etapas_aplicables_clp_h / max(masa_out_sku, 1)
            if masa_out_sku > 0 else 0
        )
        # Agregar flete entrada (MMPP)
        costo_flete_mmpp_clp_kg = params.flete.costo_promedio_mmpp_clp_ton / 1000.0
        costo_flete_despacho_clp_kg = params.flete.costo_promedio_despacho_clp_ton / 1000.0
        costo_total_kg_clp = (
            costo_kg_producto
            + costo_flete_mmpp_clp_kg / max(p.rendimiento_msf_pct, 0.001)   # se divide por yield MSF
            + costo_flete_despacho_clp_kg
        )

        costos_por_sku.append({
            "codigo": p.codigo,
            "variante": p.variante,
            "rendimiento_msf_pct": p.rendimiento_msf_pct,
            "costo_proceso_clp_kg": round(costo_kg_producto, 2),
            "costo_flete_mmpp_clp_kg": round(
                costo_flete_mmpp_clp_kg / max(p.rendimiento_msf_pct, 0.001), 2),
            "costo_flete_despacho_clp_kg": round(costo_flete_despacho_clp_kg, 2),
            "costo_total_clp_kg": round(costo_total_kg_clp, 2),
            "costo_total_usd_kg": round(costo_total_kg_clp / params.usd_clp_referencia, 3),
            "etapas_aplicables": len(p.etapas_aplicables),
            "tiene_proceso_definido": len(p.etapas_aplicables) > 1,
        })

    return {
        "throughput_kg_h": throughput_kg_h,
        "masa_input_total_kg_h": masa_in,
        "masa_output_total_kg_h": masa_out,
        "costos_etapas": [c.to_dict() for c in costos_etapas],
        "costo_total_clp_h": round(total_clp_h, 2),
        "costo_total_clp_kg_input": round(total_clp_h / max(masa_in, 1), 2),
        "costo_total_clp_kg_output": round(total_clp_h / max(masa_out, 1), 2),
        "costo_total_usd_kg_output": round(
            total_clp_h / max(masa_out, 1) / params.usd_clp_referencia, 3),
        "costos_por_sku": costos_por_sku,
        "parametros_utilizados": {
            "usd_clp": params.usd_clp_referencia,
            "tarifa_energia_clp_kwh": round(params.energia.tarifa_promedio_clp_kwh, 2),
            "calor_residual_clp_kwh": params.calor_residual.costo_kwh_termico_clp,
            "agua_industrial_clp_m3": params.agua.agua_industrial_clp_m3,
            "arriendo_pef_clp_mes": params.arriendos.arriendo_pef_clp_mes,
            "flete_mmpp_clp_ton": round(params.flete.costo_promedio_mmpp_clp_ton, 0),
            "flete_despacho_clp_ton": round(params.flete.costo_promedio_despacho_clp_ton, 0),
        },
        "desglose_costos_clp_h": {
            "mo": round(sum(c.costo_mo_clp_h for c in costos_etapas), 2),
            "energia": round(sum(c.costo_energia_clp_h for c in costos_etapas), 2),
            "calor": round(sum(c.costo_calor_clp_h for c in costos_etapas), 2),
            "agua": round(sum(c.costo_agua_clp_h for c in costos_etapas), 2),
            "materiales": round(sum(c.costo_materiales_clp_h for c in costos_etapas), 2),
            "arriendos": round(sum(c.costo_arriendo_clp_h for c in costos_etapas), 2),
        },
    }
