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
    foto_url: str = ""               # path relativo a /equipos/*.jpeg en /public
    # Metadata
    fecha_creacion: str = "2026-06-04"
    nivel_dato: Literal["PD", "OK_PROVISORIO", "OK_VALIDADO"] = "PD"

    def to_dict(self) -> dict:
        return asdict(self)


def fichas_seed() -> list[FichaEquipo]:
    """Seed con equipos REALES del documento 'Descripcion Tecnica Planta Piloto'
    (04/06/2026 - usuario).

    PLANTA PILOTO: capacidades bajas (kg/h, no ton/h industrial). Producto final:
    harina <1mm para alimentacion animal. Saco 20 kg.
    """
    return [
        # ===== ETAPA PREVIA (compartida) =====
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

        # ===== 1. RECEPCION Y ALIMENTACION =====
        FichaEquipo(
            id="BOMBA_VALISI_VSHH4",
            nombre="Bomba Valisi VSHH 4 (impulsion)",
            tipo="bomba",
            etapa_asociada="E1_RECEPCION",
            proveedor="Valisi",
            modelo="VSHH 4",
            capacidad_kg_h=3500.0,
            capacidad_unidad="kg/h (3.5 ton/h)",
            potencia_kw=3.0,
            notas="Bomba de tornillo. Impulsa residuo desde descarga hacia linea PEF.",
            foto_url="/equipos/Bomba-de-tornillo.jpeg",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 2. PRETRATAMIENTO PEF =====
        FichaEquipo(
            id="PEF_OPTICEPT_ODIN",
            nombre="PEF OptiCept ODIN (solidos)",
            tipo="pef",
            etapa_asociada="E3_PEF",
            proveedor="OptiCept (Sweden)",
            modelo="ODIN",
            modalidad="OPEX_arriendo",
            arriendo_clp_mes=18_500_000,
            capacidad_kg_h=4000.0,
            capacidad_unidad="kg/h (4.0 ton/h)",
            potencia_kw=10.0,
            notas=(
                "OptiCept ODIN - PEF para solidos. Capacidad 4 ton/h, 10 kW. "
                "1 pasada default. Electroporacion sin cambio masa/humedad."
            ),
            foto_url="/equipos/PEF-solidos.jpeg",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="PEF_OPTICEPT_SUBPRODUCTOS",
            nombre="PEF OptiCept ODIN (subproductos)",
            tipo="pef",
            etapa_asociada="E3_PEF",
            proveedor="OptiCept (Sweden)",
            modelo="ODIN (configuracion subproductos)",
            modalidad="OPEX_arriendo",
            capacidad_kg_h=4000.0,
            potencia_kw=10.0,
            notas="Modulo PEF configurado para tratamiento de subproductos liquidos/pastosos. Mismo equipo ODIN.",
            foto_url="/equipos/PEF-subproductos.jpeg",
            nivel_dato="OK_PROVISORIO",
        ),

        # ===== 3. SEPARACION MECANICA =====
        FichaEquipo(
            id="PRENSA_OELWERK_510",
            nombre="Prensa de tornillo Oelwerk 510 s-inox",
            tipo="prensa",
            etapa_asociada="E4A_PRENSADO_MECANICO",
            proveedor="Oelwerk",
            modelo="510 s-inox",
            capacidad_kg_h=25.0,
            capacidad_unidad="kg/h (0.025 ton/h)",
            potencia_kw=1.5,
            notas="Prensa principal piloto. CUELLO DE BOTELLA aguas arriba del PEF.",
            foto_url="/equipos/Prensa-de-tornillo.jpeg",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="PRENSA_EXTRACTORA_ACEITE",
            nombre="Prensa extractora de aceite (alperujo)",
            tipo="prensa",
            etapa_asociada="E4A_PRENSADO_MECANICO",
            capacidad_kg_h=15.0,
            capacidad_unidad="kg/h (0.015 ton/h)",
            potencia_kw=0.82,
            notas="Especifica alperujo. Maximiza recuperacion aceite residual.",
            foto_url="/equipos/Prensa-extractora-aceite.jpeg",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="CENTRIFUGA_BIOBASE",
            nombre="Centrifuga BioBase BKC-TL5VII (pruebas laboratorio)",
            tipo="tricanter",
            etapa_asociada="E4B_PRENSADO_CENTRIFUGO",
            proveedor="BioBase",
            modelo="BKC-TL5VII",
            capacidad_kg_h=0.3,
            capacidad_unidad="6×50 mL (escala laboratorio)",
            potencia_kw=0.2,
            notas="ESCALA LAB. Solo pruebas A/B post-PEF (humedad, pH, conductividad).",
            foto_url="/equipos/Centrifuga-laboratorio.jpeg",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 4. SECADO =====
        FichaEquipo(
            id="SECADOR_IKE_WRH300",
            nombre="Secador deshidratador IKE WRH-300",
            tipo="secador",
            etapa_asociada="E6A_DESHIDRATACION_PRINCIPAL",
            proveedor="IKE",
            modelo="WRH-300",
            capacidad_kg_h=300.0,
            capacidad_unidad="kg/h (0.30 ton/h)",
            potencia_kw=7.5,
            notas="Deshidratador. Compatible con calor residual La Gloria.",
            foto_url="/equipos/Deshidratador.jpeg",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 5. MOLIENDA =====
        FichaEquipo(
            id="MOLINO_MARTILLOS_HARINERO",
            nombre="Molino de martillos harinero",
            tipo="molino",
            etapa_asociada="E8_HOMOGENEIZACION",
            modelo="generico harinero",
            capacidad_kg_h=350.0,
            capacidad_unidad="kg/h (0.35 ton/h)",
            potencia_kw=2.2,
            notas="Reduccion granulometrica HASTA 1mm (alimentacion animal).",
            foto_url="/equipos/Molino-de-martillos.jpeg",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 6. CAPTACION DE POLVO =====
        FichaEquipo(
            id="ASPIRADOR_POLVO",
            nombre="Aspirador Extractor Colector Polvo",
            tipo="tamiz",
            etapa_asociada="E8_HOMOGENEIZACION",
            potencia_kw=2.2,
            notas="Filtro aire controla emisiones harina + recupera material fino.",
            foto_url="/equipos/Extractor-de-polvo.jpeg",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 7. TRANSPORTE =====
        FichaEquipo(
            id="TORNILLO_ELEVADOR",
            nombre="Tornillo elevador hacia tolva ensacadora",
            tipo="tornillo_cinta",
            etapa_asociada="E9_ENSACADO",
            modelo="generico",
            capacidad_kg_h=6000.0,
            capacidad_unidad="kg/h (6.0 ton/h)",
            potencia_kw=2.2,
            notas="Eleva harina desde molienda hacia tolva ensacadora.",
            foto_url="/equipos/Tornillo-elevador.jpeg",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 8-9. ENSACADO + CINTA + COSEDORA (linea integrada) =====
        FichaEquipo(
            id="ENSACADORA_AUTOMATICA",
            nombre="Ensacadora + Cinta + Cosedora (linea integrada)",
            tipo="ensacadora",
            etapa_asociada="E9_ENSACADO",
            capacidad_kg_h=6000.0,
            capacidad_unidad="kg/h (6.0 ton/h)",
            potencia_kw=1.0,
            notas=(
                "Linea integrada: ensacadora automatica (sacos 20 kg) -> "
                "cinta transportadora -> cosedora de sellado por costura."
            ),
            foto_url="/equipos/Ensacadora-cinta-cosedora.jpeg",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="CINTA_TRANSPORTADORA_SACOS",
            nombre="Cinta transportadora sacos llenos",
            tipo="transportador",
            etapa_asociada="E9_ENSACADO",
            notas="Parte de linea ensacado integrada. Ver foto principal en ENSACADORA_AUTOMATICA.",
            foto_url="/equipos/Ensacadora-cinta-cosedora.jpeg",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="COSEDORA_SACOS",
            nombre="Cosedora de sacos (sellado)",
            tipo="ensacadora",
            etapa_asociada="E9_ENSACADO",
            notas="Sella sacos 20 kg por costura. Parte linea ensacado integrada.",
            foto_url="/equipos/Ensacadora-cinta-cosedora.jpeg",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== AUXILIARES (detectados en fotos) =====
        FichaEquipo(
            id="COMPRESOR_PISTON",
            nombre="Compresor de piston (aire comprimido)",
            tipo="bomba",
            etapa_asociada="AUXILIAR",
            notas="Suministro de aire comprimido para neumatica de planta (valvulas, actuadores).",
            foto_url="/equipos/Compresor-de-piston.jpeg",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="EQUIPOS_MEDICION",
            nombre="Equipos de medicion (instrumentacion lab)",
            tipo="balanza",
            etapa_asociada="E11_CONTROL_CALIDAD",
            notas=(
                "Instrumentos de medicion para QC: humedad, pH, conductividad, "
                "granulometria, balanza. Critical para alimentar el sistema de "
                "calibracion (PD -> OK_PROVISORIO -> OK_VALIDADO)."
            ),
            foto_url="/equipos/Equipos-de-medicion.jpeg",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="TABLERO_ELECTRICO_EXTERIOR",
            nombre="Tablero electrico (vista exterior)",
            tipo="estanque",     # placeholder de tipo
            etapa_asociada="AUXILIAR",
            potencia_kw=30.62,   # total instalado
            notas=(
                "Tablero principal: contiene proteccion + control de todos los equipos. "
                "Total instalado: 30.62 kW (suma de los 10 equipos del piloto)."
            ),
            foto_url="/equipos/Tablero-electrico-exterior.jpeg",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="TABLERO_ELECTRICO_INTERIOR",
            nombre="Tablero electrico (vista interior)",
            tipo="estanque",
            etapa_asociada="AUXILIAR",
            notas="Detalle interno tablero: contactores, breakers, variadores.",
            foto_url="/equipos/Tablero-electrico-interior.jpeg",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== CALOR RESIDUAL (input externo) =====
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
            notas="SECUNDARIO: activo cuando La Gloria no entrega calor residual.",
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
