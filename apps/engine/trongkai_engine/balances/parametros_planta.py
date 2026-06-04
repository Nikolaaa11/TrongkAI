"""Planilla de parametros variables de la planta Trongkai.

Centraliza TODAS las variables economicas que alimentan el costeo:
- Sueldos profesionales planta (Encargado, Laboratorista, Limpieza, Gruero)
- Tarifa energia electrica por banda horaria
- Valor calor residual entregado por La Gloria (compartida)
- Agua llave (Essbio) y Agua industrial (pozo propio)
- Flete por traslado MMPP/producto
- Arriendo PEF (no es CAPEX propio - es OPEX mensual)

Persistencia en data/parametros-planta.json - sobreviven deploys.
Refresh con POST /parametros/actualizar.

Valores 2026 calibrados con benchmarks chilenos y conversaciones equipo.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Literal

from ..storage import data_path

USD_CLP_DEFAULT = 920.0   # tipo cambio referencia


@dataclass
class SueldoCargo:
    """Sueldo bruto mensual CLP de un cargo de planta."""
    cargo: str
    sueldo_bruto_clp: float
    costo_total_clp: float = 0.0   # bruto * factor (leyes sociales, seguros, etc)
    factor_leyes_sociales: float = 1.35   # multiplicador estandar Chile

    def __post_init__(self):
        if self.costo_total_clp == 0:
            self.costo_total_clp = self.sueldo_bruto_clp * self.factor_leyes_sociales

    @property
    def costo_hora_clp(self) -> float:
        """Costo total/hora considerando 180 h/mes (45h/sem * 4 sem)."""
        return self.costo_total_clp / 180.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["costo_hora_clp"] = round(self.costo_hora_clp, 2)
        return d


@dataclass
class TarifaEnergia:
    """Tarifa electrica industrial Chile (CGE/Enel/cooperativa rural)."""
    proveedor: str = "CGE Distribucion (BT4-3)"
    tarifa_energia_clp_kwh: float = 110.0    # punta alta (P) y baja (Resto)
    tarifa_energia_punta_clp_kwh: float = 165.0
    tarifa_energia_resto_clp_kwh: float = 95.0
    cargo_potencia_clp_kw_mes: float = 7500.0
    cargo_fijo_clp_mes: float = 12000.0
    pct_horas_punta: float = 0.20             # 18:00-23:00 invierno
    factor_potencia_objetivo: float = 0.94
    notas: str = "Tarifa BT-4-3 estimada Parral 2026. Validar con factura real."

    @property
    def tarifa_promedio_clp_kwh(self) -> float:
        return (
            self.tarifa_energia_punta_clp_kwh * self.pct_horas_punta
            + self.tarifa_energia_resto_clp_kwh * (1 - self.pct_horas_punta)
        )

    @property
    def tarifa_promedio_usd_kwh(self) -> float:
        return self.tarifa_promedio_clp_kwh / USD_CLP_DEFAULT

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tarifa_promedio_clp_kwh"] = round(self.tarifa_promedio_clp_kwh, 2)
        d["tarifa_promedio_usd_kwh"] = round(self.tarifa_promedio_usd_kwh, 4)
        return d


@dataclass
class CalorResidualLaGloria:
    """Calor residual desde planta La Gloria (compartida).

    Es residuo industrial -> costo puede ser muy bajo o cero.
    Si La Gloria cobra fee de servicio, va en costo_servicio_clp_mes.
    """
    disponible: bool = True
    capacidad_kwh_termico_mes: float = 350_000.0   # ~480 kW * 730h
    costo_kwh_termico_clp: float = 5.0              # tarifa "interna" ~0.5 USD/MWh
    costo_servicio_clp_mes: float = 0.0             # fee fijo si lo hay
    fuente: str = "Calor residual termico La Gloria SA"
    notas: str = "Pendiente: contrato formal de servicio + medicion entregada."
    nivel_dato: Literal["PD", "OK_PROVISORIO", "OK_VALIDADO"] = "PD"

    @property
    def costo_kwh_usd(self) -> float:
        return self.costo_kwh_termico_clp / USD_CLP_DEFAULT

    def to_dict(self) -> dict:
        d = asdict(self)
        d["costo_kwh_usd"] = round(self.costo_kwh_usd, 5)
        return d


@dataclass
class TarifaAgua:
    """Tarifas agua diferenciadas por origen."""
    # Agua de red (Essbio Parral)
    agua_llave_clp_m3: float = 1_450.0       # tarifa industrial 2026 estimada
    cargo_fijo_llave_clp_mes: float = 6_000.0
    alcantarillado_clp_m3: float = 1_200.0
    # Agua industrial (pozo propio - solo costo bombeo)
    agua_industrial_clp_m3: float = 180.0     # electricidad bombeo + mantencion
    derecho_dga_l_s: float = 5.0
    # Agua recirculada
    agua_recirculada_clp_m3: float = 45.0     # tratamiento basico
    nivel_dato: Literal["PD", "OK_PROVISORIO", "OK_VALIDADO"] = "PD"
    notas: str = "Validar tarifa Essbio + caudalimetro instalado en Pozo 1."

    @property
    def agua_llave_usd_m3(self) -> float:
        return (self.agua_llave_clp_m3 + self.alcantarillado_clp_m3) / USD_CLP_DEFAULT

    @property
    def agua_industrial_usd_m3(self) -> float:
        return self.agua_industrial_clp_m3 / USD_CLP_DEFAULT

    def to_dict(self) -> dict:
        d = asdict(self)
        d["agua_llave_usd_m3"] = round(self.agua_llave_usd_m3, 4)
        d["agua_industrial_usd_m3"] = round(self.agua_industrial_usd_m3, 4)
        return d


@dataclass
class TarifaFlete:
    """Costo de traslado MMPP/producto terminado."""
    flete_clp_km: float = 1_400.0             # camion 28 ton CLP/km
    flete_minimo_clp_viaje: float = 180_000.0  # base + carga + descarga
    distancia_promedio_mmpp_km: float = 65.0   # campos proveedores -> Parral
    distancia_promedio_despacho_km: float = 350.0   # Parral -> Valparaiso (export)
    capacidad_camion_ton: float = 28.0
    notas: str = "Tarifa benchmark camion FCL Chile centro-sur 2026."

    @property
    def costo_promedio_mmpp_clp_ton(self) -> float:
        viaje = max(
            self.flete_minimo_clp_viaje,
            self.flete_clp_km * self.distancia_promedio_mmpp_km,
        )
        return viaje / self.capacidad_camion_ton

    @property
    def costo_promedio_despacho_clp_ton(self) -> float:
        viaje = max(
            self.flete_minimo_clp_viaje,
            self.flete_clp_km * self.distancia_promedio_despacho_km,
        )
        return viaje / self.capacidad_camion_ton

    def to_dict(self) -> dict:
        d = asdict(self)
        d["costo_promedio_mmpp_clp_ton"] = round(self.costo_promedio_mmpp_clp_ton, 0)
        d["costo_promedio_despacho_clp_ton"] = round(self.costo_promedio_despacho_clp_ton, 0)
        return d


@dataclass
class ArriendoEquipos:
    """OPEX equipos arrendados (no CAPEX propio)."""
    arriendo_pef_clp_mes: float = 18_500_000.0    # PEF Opticept arriendo OPEX
    arriendo_tricanter_clp_mes: float = 4_200_000.0
    arriendo_otros_clp_mes: float = 0.0
    nivel_dato: Literal["PD", "OK_PROVISORIO", "OK_VALIDADO"] = "PD"
    notas: str = "PEF NO es CAPEX propio. Cotizacion final pendiente proveedor."

    @property
    def arriendo_total_clp_mes(self) -> float:
        return (self.arriendo_pef_clp_mes + self.arriendo_tricanter_clp_mes
                + self.arriendo_otros_clp_mes)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["arriendo_total_clp_mes"] = self.arriendo_total_clp_mes
        d["arriendo_total_usd_mes"] = round(self.arriendo_total_clp_mes / USD_CLP_DEFAULT, 2)
        return d


@dataclass
class ParametrosPlanta:
    """Bundle completo de parametros variables de planta."""
    sueldos: list[SueldoCargo] = field(default_factory=list)
    energia: TarifaEnergia = field(default_factory=TarifaEnergia)
    calor_residual: CalorResidualLaGloria = field(default_factory=CalorResidualLaGloria)
    agua: TarifaAgua = field(default_factory=TarifaAgua)
    flete: TarifaFlete = field(default_factory=TarifaFlete)
    arriendos: ArriendoEquipos = field(default_factory=ArriendoEquipos)
    perdida_mmpp_global_pct: float = 0.05      # 5% global segun conversacion
    usd_clp_referencia: float = USD_CLP_DEFAULT
    fecha_actualizacion: str = "2026-06-04"

    def to_dict(self) -> dict:
        return {
            "sueldos": [s.to_dict() for s in self.sueldos],
            "energia": self.energia.to_dict(),
            "calor_residual": self.calor_residual.to_dict(),
            "agua": self.agua.to_dict(),
            "flete": self.flete.to_dict(),
            "arriendos": self.arriendos.to_dict(),
            "perdida_mmpp_global_pct": self.perdida_mmpp_global_pct,
            "usd_clp_referencia": self.usd_clp_referencia,
            "fecha_actualizacion": self.fecha_actualizacion,
            "checklist_pendientes": [
                p for p in [
                    "Calor residual: contrato formal con La Gloria" if self.calor_residual.nivel_dato == "PD" else None,
                    "Agua: tarifa Essbio actualizada + caudalimetro instalado" if self.agua.nivel_dato == "PD" else None,
                    "Arriendos: cotizacion final PEF + Tricanter" if self.arriendos.nivel_dato == "PD" else None,
                    "Sueldos: validar con planilla remuneraciones real" if not self.sueldos else None,
                ] if p
            ],
        }


def sueldos_seed() -> list[SueldoCargo]:
    """Sueldos brutos referencia agroindustria centro-sur Chile 2026.

    Calibrados con benchmarks Indeed/Computrabajo + estimacion sector.
    """
    return [
        SueldoCargo(cargo="Laboratorista (QC)", sueldo_bruto_clp=780_000),
        SueldoCargo(cargo="Encargado Recepcion", sueldo_bruto_clp=620_000),
        SueldoCargo(cargo="Encargado Proceso", sueldo_bruto_clp=680_000),
        SueldoCargo(cargo="Encargado Secado", sueldo_bruto_clp=720_000),
        SueldoCargo(cargo="Operario Limpieza", sueldo_bruto_clp=540_000),
        SueldoCargo(cargo="Gruero Horquilla", sueldo_bruto_clp=650_000),
        SueldoCargo(cargo="Supervisor Turno", sueldo_bruto_clp=950_000),
        SueldoCargo(cargo="Jefe Planta", sueldo_bruto_clp=1_800_000),
    ]


def parametros_seed() -> ParametrosPlanta:
    return ParametrosPlanta(sueldos=sueldos_seed())


# ===== Persistencia =====
_STORAGE = "parametros-planta.json"


def cargar_parametros() -> ParametrosPlanta:
    p = data_path(_STORAGE)
    if not p.exists():
        return parametros_seed()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        # Reconstruir dataclasses anidados
        sueldos = [SueldoCargo(**s) for s in data.get("sueldos", [])]
        return ParametrosPlanta(
            sueldos=sueldos or sueldos_seed(),
            energia=TarifaEnergia(**{k: v for k, v in data.get("energia", {}).items()
                                      if k in TarifaEnergia.__dataclass_fields__}),
            calor_residual=CalorResidualLaGloria(**{k: v for k, v in data.get("calor_residual", {}).items()
                                                     if k in CalorResidualLaGloria.__dataclass_fields__}),
            agua=TarifaAgua(**{k: v for k, v in data.get("agua", {}).items()
                                if k in TarifaAgua.__dataclass_fields__}),
            flete=TarifaFlete(**{k: v for k, v in data.get("flete", {}).items()
                                  if k in TarifaFlete.__dataclass_fields__}),
            arriendos=ArriendoEquipos(**{k: v for k, v in data.get("arriendos", {}).items()
                                          if k in ArriendoEquipos.__dataclass_fields__}),
            perdida_mmpp_global_pct=data.get("perdida_mmpp_global_pct", 0.05),
            usd_clp_referencia=data.get("usd_clp_referencia", USD_CLP_DEFAULT),
            fecha_actualizacion=data.get("fecha_actualizacion", "2026-06-04"),
        )
    except Exception:
        return parametros_seed()


def guardar_parametros(params: ParametrosPlanta) -> None:
    p = data_path(_STORAGE)
    p.write_text(
        json.dumps(params.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def actualizar_parametros(updates: dict) -> ParametrosPlanta:
    """Aplica updates parciales (solo los campos provistos)."""
    actual = cargar_parametros()

    if "sueldos" in updates:
        actual.sueldos = [SueldoCargo(**s) for s in updates["sueldos"]]
    if "energia" in updates:
        for k, v in updates["energia"].items():
            if k in TarifaEnergia.__dataclass_fields__:
                setattr(actual.energia, k, v)
    if "calor_residual" in updates:
        for k, v in updates["calor_residual"].items():
            if k in CalorResidualLaGloria.__dataclass_fields__:
                setattr(actual.calor_residual, k, v)
    if "agua" in updates:
        for k, v in updates["agua"].items():
            if k in TarifaAgua.__dataclass_fields__:
                setattr(actual.agua, k, v)
    if "flete" in updates:
        for k, v in updates["flete"].items():
            if k in TarifaFlete.__dataclass_fields__:
                setattr(actual.flete, k, v)
    if "arriendos" in updates:
        for k, v in updates["arriendos"].items():
            if k in ArriendoEquipos.__dataclass_fields__:
                setattr(actual.arriendos, k, v)
    if "perdida_mmpp_global_pct" in updates:
        actual.perdida_mmpp_global_pct = updates["perdida_mmpp_global_pct"]
    if "usd_clp_referencia" in updates:
        actual.usd_clp_referencia = updates["usd_clp_referencia"]

    from datetime import datetime
    actual.fecha_actualizacion = datetime.now().strftime("%Y-%m-%d")
    guardar_parametros(actual)
    return actual
