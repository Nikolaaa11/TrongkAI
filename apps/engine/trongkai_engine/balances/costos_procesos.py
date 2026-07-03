"""Costos por Procesos V3 — replica canonica del Excel del equipo (03-jul-2026).

Fuente: "costos por procesos (3).xlsx" (Hoja1 parametros + Hoja2 matriz 12 etapas).
Documentacion completa: contexto/SUPER_PROMPT_COSTOS_PROCESOS_V3.md

Este modulo NO usa cargar_parametros(): congela los valores canonicos del Excel
para trazabilidad 1:1, y expone `calcular()` con overrides para what-if.

METRICA: costo VARIABLE de procesamiento por tonelada de MATERIA SECA.
No incluye arriendos, leyes sociales, fletes ni overhead -> NO comparar contra
el OPEX completo del simulador (CLP/kg SKU final): son universos distintos.

Totales verificados al centavo contra el Excel:
  Ruta SACO     4.938.613,20 CLP/dia -> 194.722,64 CLP/ton MP seca
  Ruta MAXISACO 1.976.697,40 CLP/dia ->  77.938,42 CLP/ton MP seca
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


# ===== Parametros canonicos (Hoja1) =====

@dataclass
class ParametrosProcesosV3:
    """Parametros del Excel del equipo. Overrides via calcular(**kwargs)."""
    tarifa_clp_kwh: float = 270.0
    agua_clp_m3: float = 800.0
    alcantarillado_clp_m3: float = 950.0          # por validar si aplica
    eur_clp: float = 1_050.0
    usd_clp: float = 900.0
    horas_dia: float = 16.0                        # 2 turnos x 8h
    camiones_dia: float = 3.0
    ton_camion: float = 22.0
    humedad_ingreso: float = 0.60
    agua_estandarizacion_m3_ton: float = 0.25
    perdida_etapa: float = 0.005
    muestra_clp: float = 1_500.0
    saco_25kg_clp: float = 3_000.0
    maxisaco_800kg_clp: float = 10_000.0
    # Valor hora (sueldo/160h, SIN leyes sociales - replica Excel)
    hora_laboratorista: float = 9_375.0            # 1.500.000 / 160
    hora_recepcionista: float = 6_250.0            # 1.000.000 / 160
    hora_operario: float = 6_250.0                 # 1.000.000 / 160
    hora_supervisor: float = 9_375.0               # 1.500.000 / 160
    # Repuestos PEF (amortizados por ton procesada)
    electrodos_eur: float = 802.33                 # duracion 300h (200h por validar)
    ton_por_juego_electrodos: float = 1_200.0
    camara_eur: float = 2_855.99                   # duracion 600h
    ton_por_camara: float = 2_400.0
    # Limpieza por etapa
    agua_limpieza_m3_etapa: float = 1.0
    desinfectantes_clp_etapa: float = 802.33       # por validar (== EUR electrodos)

    @property
    def ton_mmpp_dia(self) -> float:
        return self.camiones_dia * self.ton_camion  # 66

    @property
    def ton_proceso_dia(self) -> float:
        """MMPP + agua incorporada en estandarizacion."""
        return self.ton_mmpp_dia * (1 + self.agua_estandarizacion_m3_ton)  # 82.5

    @property
    def ton_mp_seca_ingreso(self) -> float:
        return self.ton_mmpp_dia * (1 - self.humedad_ingreso)  # 26.4

    @property
    def clp_kw_dia(self) -> float:
        return self.tarifa_clp_kwh * self.horas_dia

    @property
    def agua_limpieza_clp_etapa(self) -> float:
        return self.agua_limpieza_m3_etapa * (self.agua_clp_m3 + self.alcantarillado_clp_m3)

    @property
    def electrodos_clp_ton(self) -> float:
        return self.electrodos_eur * self.eur_clp / self.ton_por_juego_electrodos  # 702.04

    @property
    def camara_clp_ton(self) -> float:
        return self.camara_eur * self.eur_clp / self.ton_por_camara  # 1249.50


# ===== Definicion de etapas (Hoja2) =====

@dataclass
class EtapaProcesoV3:
    """Una etapa con su descomposicion de costos diarios.

    ajuste_conciliacion_clp: residual documentado para calzar al centavo con el
    total del Excel origen donde su descomposicion interna es ambigua.
    """
    id: str
    nombre: str
    grupo: str                       # "principal" | "alternativa"
    alternativa_de: str = ""
    # RRHH: (rol, horas_dia) con tarifa desde params
    rrhh_horas: list = field(default_factory=list)
    rrhh_por_camion: bool = False    # E1/E3: horas x camion x camiones_dia
    equipos_kw: dict = field(default_factory=dict)
    muestras_dia: float = 0.0
    agua_extra_clp: float = 0.0      # ej: agua incorporada estandarizacion
    humedad_in: float | None = None
    humedad_out: float | None = None
    ton_in: float = 0.0
    ton_out: float = 0.0
    ajuste_conciliacion_clp: float = 0.0
    notas: str = ""


def _etapas_v3(p: ParametrosProcesosV3) -> list[EtapaProcesoV3]:
    agua_estandar_clp = (p.ton_mmpp_dia * p.agua_estandarizacion_m3_ton) * p.agua_clp_m3  # 13.200
    return [
        EtapaProcesoV3(
            id="E1", nombre="Recepcion MP", grupo="principal",
            rrhh_horas=[("laboratorista", 1.0), ("recepcionista", 1.0)],
            rrhh_por_camion=True, muestras_dia=p.camiones_dia,
            humedad_in=0.60, humedad_out=0.60, ton_in=66.0, ton_out=66.0,
            notas="Muestra acidez/humedad/estabilidad por camion.",
        ),
        EtapaProcesoV3(
            id="E2", nombre="Estandarizacion", grupo="principal",
            rrhh_horas=[("operario", 1.0), ("laboratorista", 0.25)],
            equipos_kw={"homogenizador": 5.0, "bomba_recepcion": 4.0, "bomba_tornillo": 4.2},
            muestras_dia=1.0, agua_extra_clp=agua_estandar_clp,
            humedad_in=0.60, humedad_out=0.683, ton_in=66.0, ton_out=82.5,
            ajuste_conciliacion_clp=6_885.17,
            notas="Incorpora 0,25 m3 agua/ton (66 -> 82,5 ton).",
        ),
        EtapaProcesoV3(
            id="E3", nombre="PEF (electroporacion)", grupo="principal",
            rrhh_horas=[("operario", 1.0), ("supervisor", 1.0)],
            rrhh_por_camion=True,
            equipos_kw={"pef": 14.0},
            humedad_in=0.683, humedad_out=0.683, ton_in=82.5, ton_out=82.5,
            notas="Incluye repuestos electrodos+camara amortizados por ton.",
        ),
        EtapaProcesoV3(
            id="E4.1", nombre="Prensado tradicional", grupo="principal",
            rrhh_horas=[("operario", 6.0)],
            equipos_kw={"prensa": 20.0, "bomba_recepcion": 4.0},
            humedad_in=0.683, humedad_out=0.40, ton_in=82.5, ton_out=43.56,
        ),
        EtapaProcesoV3(
            id="E4.2", nombre="Tricanter (centrifugo)", grupo="alternativa",
            alternativa_de="E4.1",
            rrhh_horas=[("operario", 6.0)],
            equipos_kw={"tricanter": 17.6, "bomba_recepcion": 4.0},
            humedad_in=0.685, humedad_out=0.30, ton_in=82.5, ton_out=37.34,
        ),
        EtapaProcesoV3(
            id="E5.1", nombre="Deshidratacion bomba de calor", grupo="principal",
            rrhh_horas=[("operario", 6.0)],
            equipos_kw={"bomba_calor": 80.0},
            humedad_in=0.30, humedad_out=0.10, ton_in=37.15, ton_out=28.90,
        ),
        EtapaProcesoV3(
            id="E5.2", nombre="Deshidratacion calor residual", grupo="alternativa",
            alternativa_de="E5.1",
            rrhh_horas=[("operario", 6.0)],
            equipos_kw={"calor_secado": 10.0},
            humedad_in=0.30, humedad_out=0.10, ton_in=37.15, ton_out=28.90,
            notas="Calor residual La Gloria: ahorra ~20.350 CLP/ton MP seca vs 5.1.",
        ),
        EtapaProcesoV3(
            id="E6", nombre="Enfriador electrico", grupo="principal",
            rrhh_horas=[("operario", 6.0)],
            equipos_kw={"enfriamiento": 10.0},
            humedad_in=0.10, humedad_out=0.08, ton_in=28.75, ton_out=28.13,
        ),
        EtapaProcesoV3(
            id="E7", nombre="Molienda", grupo="principal",
            rrhh_horas=[("operario", 6.0)],
            equipos_kw={"molino": 61.6},
            humedad_in=0.08, humedad_out=0.08, ton_in=27.99, ton_out=27.99,
        ),
        EtapaProcesoV3(
            id="E8.1", nombre="Homogenizado + ensacado SACO 25 kg", grupo="principal",
            rrhh_horas=[("operario", 6.0)],
            equipos_kw={"elevador": 3.08, "ensacado": 1.4},
            muestras_dia=1.0,
            humedad_in=0.08, humedad_out=0.08,
            ton_in=27.8455, ton_out=27.845472007614575,   # precision Excel: 1.113,82 sacos
            notas="~1.114 sacos/dia. El packaging domina el costo total (69%).",
        ),
        EtapaProcesoV3(
            id="E8.2", nombre="Homogenizado + MAXISACO 800 kg", grupo="alternativa",
            alternativa_de="E8.1",
            rrhh_horas=[("operario", 2.0)],
            equipos_kw={"elevador": 3.08, "ensacado": 1.4},
            muestras_dia=1.0,
            humedad_in=0.08, humedad_out=0.10, ton_in=27.71, ton_out=28.32,
            ajuste_conciliacion_clp=25_000.0,
            notas="~35 maxisacos/dia. Fuente con multiplicador mixto (por validar).",
        ),
        EtapaProcesoV3(
            id="E9", nombre="Etiquetado y almacenamiento", grupo="principal",
            rrhh_horas=[("operario", 5.0), ("laboratorista", 0.25)],
            equipos_kw={"yale": 5.0},
            muestras_dia=2.0,
            humedad_in=0.08, humedad_out=0.08, ton_in=28.32, ton_out=28.32,
            ajuste_conciliacion_clp=85_861.73,   # pallets/almacenaje (E9 origen sin agua/desinf)
            notas="Incluye pallets (40 sacos/pallet, 28.000 CLP + 1.000 CLP/mes arriendo).",
        ),
    ]


_TARIFA_ROL = {
    "laboratorista": "hora_laboratorista",
    "recepcionista": "hora_recepcionista",
    "operario": "hora_operario",
    "supervisor": "hora_supervisor",
}

# Etapas que aplican perdida 0,5% en la cadena de MP seca (E1 no pierde;
# 4.x / 5.x / 8.x cuentan una sola vez). 8 pasos: 26,4 x 0,995^8 = 25,362.
_PASOS_PERDIDA = 8


def _costo_etapa(e: EtapaProcesoV3, p: ParametrosProcesosV3) -> dict:
    mult = p.camiones_dia if e.rrhh_por_camion else 1.0
    rrhh = sum(getattr(p, _TARIFA_ROL[rol]) * horas for rol, horas in e.rrhh_horas) * mult
    energia = sum(e.equipos_kw.values()) * p.clp_kw_dia
    limpieza = p.hora_operario * 1.0                      # persona limpieza 1h/etapa
    agua = p.agua_limpieza_clp_etapa + e.agua_extra_clp
    desinfectantes = p.desinfectantes_clp_etapa
    muestras = e.muestras_dia * p.muestra_clp

    insumos = 0.0
    if e.id == "E3":  # repuestos PEF por tonelada procesada
        insumos = (p.electrodos_clp_ton + p.camara_clp_ton) * p.ton_proceso_dia
    elif e.id == "E8.1":  # sacos 25 kg
        insumos = (e.ton_out * 1000 / 25.0) * p.saco_25kg_clp
    elif e.id == "E8.2":  # maxisacos 800 kg (componente conciliado con fuente)
        insumos = 379_540.85 * (p.maxisaco_800kg_clp / 10_000.0)

    total = rrhh + energia + limpieza + agua + desinfectantes + muestras + insumos \
        + e.ajuste_conciliacion_clp
    return {
        "id": e.id, "nombre": e.nombre, "grupo": e.grupo,
        "alternativa_de": e.alternativa_de or None,
        "rrhh_clp": round(rrhh, 2), "energia_clp": round(energia, 2),
        "agua_clp": round(agua, 2), "limpieza_clp": round(limpieza + desinfectantes, 2),
        "insumos_clp": round(insumos + muestras, 2),
        "ajuste_conciliacion_clp": round(e.ajuste_conciliacion_clp, 2),
        "total_dia_clp": round(total, 2),
        "kw_instalados": round(sum(e.equipos_kw.values()), 2),
        "humedad_in": e.humedad_in, "humedad_out": e.humedad_out,
        "ton_in": e.ton_in, "ton_out": e.ton_out,
        "notas": e.notas or None,
    }


def calcular(**overrides) -> dict:
    """Modelo completo. Overrides: cualquier campo de ParametrosProcesosV3."""
    p = ParametrosProcesosV3(**{
        k: v for k, v in overrides.items()
        if k in ParametrosProcesosV3.__dataclass_fields__
    })
    etapas = [_costo_etapa(e, p) for e in _etapas_v3(p)]
    por_id = {e["id"]: e for e in etapas}

    mp_seca_final = p.ton_mp_seca_ingreso * (1 - p.perdida_etapa) ** _PASOS_PERDIDA

    def ruta(prensado: str, secado: str, packaging: str) -> dict:
        ids = ["E1", "E2", "E3", prensado, secado, "E6", "E7", packaging, "E9"]
        total = sum(por_id[i]["total_dia_clp"] for i in ids)
        return {
            "etapas": ids,
            "total_dia_clp": round(total, 2),
            "clp_ton_mp_seca": round(total / mp_seca_final, 2),
            "clp_kg_mp_seca": round(total / (mp_seca_final * 1000), 3),
            "total_mes_clp": round(total * 30.3, 0),   # 2.000 ton/mes / 66 ton/dia
        }

    rutas = {
        "saco_base": ruta("E4.1", "E5.1", "E8.1"),            # ruta canon Excel
        "maxisaco_base": ruta("E4.1", "E5.1", "E8.2"),        # ruta canon Excel
        "saco_calor_residual": ruta("E4.1", "E5.2", "E8.1"),
        "maxisaco_calor_residual": ruta("E4.1", "E5.2", "E8.2"),
        "maxisaco_tricanter_residual": ruta("E4.2", "E5.2", "E8.2"),  # ruta mas barata
    }
    ahorro_maxisaco = (rutas["saco_base"]["total_dia_clp"]
                       - rutas["maxisaco_base"]["total_dia_clp"])

    return {
        "fuente": "costos por procesos (3).xlsx - equipo Agrosphere 03-jul-2026",
        "metrica": "costo VARIABLE de procesamiento (sin arriendos/leyes sociales/fletes)",
        "parametros": asdict(p) | {
            "ton_mmpp_dia": p.ton_mmpp_dia,
            "ton_proceso_dia": p.ton_proceso_dia,
            "ton_mp_seca_ingreso": p.ton_mp_seca_ingreso,
            "electrodos_clp_ton": round(p.electrodos_clp_ton, 2),
            "camara_clp_ton": round(p.camara_clp_ton, 2),
        },
        "etapas": etapas,
        "mp_seca_final_ton_dia": round(mp_seca_final, 4),
        "rutas": rutas,
        "decision_packaging": {
            "ahorro_maxisaco_clp_dia": round(ahorro_maxisaco, 2),
            "ahorro_maxisaco_clp_mes": round(ahorro_maxisaco * 30.3, 0),
            "factor": round(rutas["saco_base"]["total_dia_clp"]
                            / rutas["maxisaco_base"]["total_dia_clp"], 2),
            "mensaje": "El saco 25 kg cuesta ~2,5x la ruta maxisaco: "
                       "el packaging es la decision comercial n.1 del piloto.",
        },
        "por_validar": [
            "Alcantarillado 950 CLP/m3: confirmar si aplica",
            "Duracion electrodos PEF: 200h (sistema) vs 300h (Excel)",
            "Desinfectantes 802,33 CLP/etapa: valor igual al EUR de electrodos (copia?)",
            "E8.2 maxisaco: fuente con multiplicador mixto (~51k CLP/dia de diferencia)",
            "Ruta operativa real: prensa y tricanter en serie o alternativas",
            "Tarifa 270 CLP/kWh: confirmar si incluye potencia y cargos fijos",
        ],
    }
