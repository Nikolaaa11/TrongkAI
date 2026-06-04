"""Fichas tecnicas detalladas por equipo de la planta.

El usuario alimentara info especifica de cada equipo (compatible con
los proveedores reales). Estructura abierta + persistente en /data.

Cada ficha tiene:
- Identificacion (nombre, proveedor, modelo)
- Especificaciones tecnicas (capacidad, consumo, dimensiones)
- Costos (CAPEX o arriendo OPEX)
- Mantencion (frecuencia, costo)
- Vincula con etapa(s) donde se usa
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Literal

from ..storage import data_path


TipoEquipo = Literal[
    "bomba", "tornillo_cinta", "homogenizador", "pef", "prensa",
    "tricanter", "secador", "intercambiador", "molino",
    "tamiz", "transportador", "ensacadora", "etiquetadora",
    "balanza", "grua", "estanque", "caldera"
]

ModalidadCompra = Literal["CAPEX_propio", "OPEX_arriendo", "leasing"]


@dataclass
class FichaEquipo:
    """Ficha tecnica de un equipo de planta."""
    id: str                                # "PEF_OPTICEPT_01"
    nombre: str                            # "PEF Opticept SP-100"
    tipo: TipoEquipo
    etapa_asociada: str                    # "E3_PEF"
    proveedor: str = ""
    modelo: str = ""
    # Especificaciones
    capacidad_kg_h: float = 0.0
    capacidad_unidad: str = "kg/h"
    potencia_kw: float = 0.0
    consumo_agua_l_h: float = 0.0
    dimensiones: str = ""                  # "2.5x1.2x1.8 m"
    peso_kg: float = 0.0
    # Costos
    modalidad: ModalidadCompra = "CAPEX_propio"
    capex_clp: float = 0.0
    arriendo_clp_mes: float = 0.0
    instalacion_clp: float = 0.0
    # Mantencion
    frecuencia_mantencion_h: float = 2000.0
    costo_mantencion_clp: float = 0.0
    vida_util_anos: float = 10.0
    # Notas y links
    notas: str = ""
    ficha_tecnica_url: str = ""
    contacto_proveedor: str = ""
    # Metadata
    fecha_creacion: str = "2026-06-04"
    nivel_dato: Literal["PD", "OK_PROVISORIO", "OK_VALIDADO"] = "PD"

    def to_dict(self) -> dict:
        return asdict(self)


def fichas_seed() -> list[FichaEquipo]:
    """Seed inicial con los equipos clave (a ser alimentados por usuario)."""
    return [
        FichaEquipo(
            id="ROMANA_LAGLORIA",
            nombre="Romana compartida La Gloria",
            tipo="balanza",
            etapa_asociada="PRE_E1",
            proveedor="La Gloria SA",
            modalidad="OPEX_arriendo",
            arriendo_clp_mes=0.0,
            notas="COMPARTIDA con La Gloria - FUERA del analisis de costos Trongkai.",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="TORNILLO_E1",
            nombre="Tornillo / Cinta / Bomba impulsion E1->E2",
            tipo="tornillo_cinta",
            etapa_asociada="E1_RECEPCION",
            notas="Define modalidad (tornillo, cinta, bomba) segun MMPP y reologia.",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="HOMOGENIZADOR_E2",
            nombre="Homogenizador paleta E2",
            tipo="homogenizador",
            etapa_asociada="E2_ESTANDARIZACION",
            notas="Mezclador para ajustar reologia previo PEF.",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="PEF_OPTICEPT_01",
            nombre="PEF Opticept (modelo a definir)",
            tipo="pef",
            etapa_asociada="E3_PEF",
            proveedor="Opticept Sweden",
            modalidad="OPEX_arriendo",
            arriendo_clp_mes=18_500_000,
            capacidad_kg_h=2000.0,
            potencia_kw=250.0,
            notas=(
                "1 pasada default segun usuario (4/06/26). "
                "Pendiente: kV optimo por MMPP, costo electrodos CIF Chile, "
                "% reduccion tiempo secado real."
            ),
            nivel_dato="OK_PROVISORIO",
        ),
        FichaEquipo(
            id="BOMBA_E3_SALIDA",
            nombre="Bomba salida PEF -> Prensado",
            tipo="bomba",
            etapa_asociada="E3_PEF",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="PRENSA_E4A",
            nombre="Prensa mecanica (horizontal/tornillo)",
            tipo="prensa",
            etapa_asociada="E4A_PRENSADO_MECANICO",
            notas="Reduce humedad a ~30% generando torta.",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="TRICANTER_E4B",
            nombre="Tricanter centrifugo (3 fases)",
            tipo="tricanter",
            etapa_asociada="E4B_PRENSADO_CENTRIFUGO",
            modalidad="OPEX_arriendo",
            arriendo_clp_mes=4_200_000,
            notas="Solo Tomasa Hot. Separa solido + liquido + aceite.",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="ESTANQUE_LIQUIDOS_E5",
            nombre="Estanque liquidos residuales + bombas",
            tipo="estanque",
            etapa_asociada="E5_LIQUIDOS_RESIDUALES",
            notas="Define materialidad + capacidad. Loop opcional a E2.",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="INTERCAMBIADOR_LAGLORIA",
            nombre="Intercambiador calor residual La Gloria",
            tipo="intercambiador",
            etapa_asociada="E6A_DESHIDRATACION_PRINCIPAL",
            proveedor="La Gloria SA (suministro calor)",
            notas="PRINCIPAL: calor residual termico desde La Gloria. Contrato pendiente.",
            nivel_dato="OK_PROVISORIO",
        ),
        FichaEquipo(
            id="BOMBA_CALOR_RESPALDO",
            nombre="Bomba de calor (respaldo deshidratacion)",
            tipo="caldera",
            etapa_asociada="E6B_DESHIDRATACION_RESPALDO",
            notas="SECUNDARIO: activo cuando La Gloria no entrega calor.",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="MOLINO_HOMOGENIZADOR_E8",
            nombre="Molino + Homogenizador harinas",
            tipo="molino",
            etapa_asociada="E8_HOMOGENEIZACION",
            notas="Solo SKU premium (post decision venta en E7).",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="ENSACADORA_E9",
            nombre="Ensacadora + selladora + palletizadora",
            tipo="ensacadora",
            etapa_asociada="E9_ENSACADO",
            notas="Sellado en 2 fases: plancha calor + cosido. Big bag y/o saco.",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="ETIQUETADORA_E10",
            nombre="Etiquetadora + codificadora",
            tipo="etiquetadora",
            etapa_asociada="E10_ETIQUETADO",
            nivel_dato="PD",
        ),
        FichaEquipo(
            id="GRUA_HORQUILLA",
            nombre="Grua de horquilla",
            tipo="grua",
            etapa_asociada="E10_ETIQUETADO",
            nivel_dato="PD",
        ),
    ]


# ===== Persistencia =====
_STORAGE = "fichas-equipos.json"


def cargar_fichas() -> list[FichaEquipo]:
    p = data_path(_STORAGE)
    if not p.exists():
        return fichas_seed()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return [FichaEquipo(**d) for d in data]
    except Exception:
        return fichas_seed()


def guardar_fichas(fichas: list[FichaEquipo]) -> None:
    p = data_path(_STORAGE)
    p.write_text(
        json.dumps([f.to_dict() for f in fichas], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def actualizar_ficha(equipo_id: str, updates: dict) -> FichaEquipo:
    """Actualiza una ficha existente o crea nueva."""
    fichas = cargar_fichas()
    for f in fichas:
        if f.id == equipo_id:
            for k, v in updates.items():
                if k in FichaEquipo.__dataclass_fields__:
                    setattr(f, k, v)
            guardar_fichas(fichas)
            return f
    # Crear nueva
    nueva = FichaEquipo(id=equipo_id, **{k: v for k, v in updates.items()
                                          if k in FichaEquipo.__dataclass_fields__})
    fichas.append(nueva)
    guardar_fichas(fichas)
    return nueva


def resumen_completitud_fichas() -> dict:
    """Cuantas fichas estan validadas vs pendientes."""
    fichas = cargar_fichas()
    by_nivel = {"PD": 0, "OK_PROVISORIO": 0, "OK_VALIDADO": 0}
    for f in fichas:
        by_nivel[f.nivel_dato] = by_nivel.get(f.nivel_dato, 0) + 1
    total = len(fichas)
    completitud = (by_nivel["OK_VALIDADO"] * 100 + by_nivel["OK_PROVISORIO"] * 60
                   + by_nivel["PD"] * 20) / max(total, 1)
    return {
        "total_fichas": total,
        "por_nivel": by_nivel,
        "completitud_pct": round(completitud, 1),
        "pendientes_PD": [
            {"id": f.id, "nombre": f.nombre, "etapa": f.etapa_asociada}
            for f in fichas if f.nivel_dato == "PD"
        ],
    }
