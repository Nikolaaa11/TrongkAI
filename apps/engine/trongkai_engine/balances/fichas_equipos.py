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
            notas="Impulsa residuo desde descarga hacia linea de pretratamiento PEF. Confirmado en doc tecnico planta piloto.",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 2. PRETRATAMIENTO PEF =====
        FichaEquipo(
            id="PEF_OPTICEPT_ODIN",
            nombre="PEF OptiCept ODIN",
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
                "Confirmado modelo: OptiCept ODIN. Capacidad 4 ton/h, consumo 10 kW/h. "
                "1 pasada default (segun respuesta usuario 4/06). "
                "Electroporacion: aumenta extraccion agua vegetal y compuestos de interes. "
                "Sin perdidas masa, sin cambio humedad."
            ),
            nivel_dato="OK_VALIDADO",
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
            notas=(
                "Prensa principal piloto. Capacidad 25 kg/h, consumo 1.5 kW/h. "
                "Genera torta solida + jugo. CUELLO DE BOTELLA aguas arriba "
                "(PEF puede 4000 kg/h pero prensa solo 25 kg/h en piloto)."
            ),
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
            notas=(
                "Segunda prensa especifica para alperujo - maximiza recuperacion "
                "aceite residual. Solo aplica linea oliva. Capacidad 15 kg/h."
            ),
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
            notas=(
                "ESCALA LABORATORIO (6×50 mL). Solo para PRUEBAS de separacion agua "
                "vegetal vs torta solida post-PEF. NO es operacion continua. "
                "Registrar humedad, pH, conductividad antes/despues."
            ),
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
            notas=(
                "Reduce humedad y estabiliza producto. Confirmado piloto. "
                "Compatible con uso de CALOR RESIDUAL La Gloria como input termico."
            ),
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 5. MOLIENDA =====
        FichaEquipo(
            id="MOLINO_MARTILLOS_HARINERO",
            nombre="Molino de martillos harinero generico",
            tipo="molino",
            etapa_asociada="E8_HOMOGENEIZACION",
            modelo="generico harinero",
            capacidad_kg_h=350.0,
            capacidad_unidad="kg/h (0.35 ton/h)",
            potencia_kw=2.2,
            notas=(
                "Reduccion granulometrica final HASTA 1mm (optimo alimentacion animal). "
                "Capacidad 350 kg/h, consumo 2.2 kW/h."
            ),
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 6. CAPTACION DE POLVO =====
        FichaEquipo(
            id="ASPIRADOR_POLVO",
            nombre="Aspirador Extractor Colector Polvo",
            tipo="tamiz",
            etapa_asociada="E8_HOMOGENEIZACION",
            potencia_kw=2.2,
            notas=(
                "Filtro de aire para controlar emisiones de harina suspendida. "
                "Mejora calidad ambiente + recupera material fino. 2.2 kW/h. "
                "Capacidad: control emisiones (no flow continuo de producto)."
            ),
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
            notas="Eleva harina desde molienda hacia tolva ensacadora automatica.",
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 8. ENSACADO =====
        FichaEquipo(
            id="ENSACADORA_AUTOMATICA",
            nombre="Ensacadora automatica (sacos 20 kg)",
            tipo="ensacadora",
            etapa_asociada="E9_ENSACADO",
            capacidad_kg_h=6000.0,
            capacidad_unidad="kg/h (6.0 ton/h)",
            potencia_kw=1.0,
            notas=(
                "Pesaje y llenado de sacos 20 kg (ACTUALIZADO: era 25 kg, ahora 20 kg "
                "confirmado en doc piloto). Capacidad 6 ton/h."
            ),
            nivel_dato="OK_VALIDADO",
        ),

        # ===== 9. TRANSPORTE 2 + COSEDORA =====
        FichaEquipo(
            id="CINTA_TRANSPORTADORA_SACOS",
            nombre="Cinta transportadora sacos llenos -> cosedora",
            tipo="transportador",
            etapa_asociada="E9_ENSACADO",
            notas="Transporta sacos 20 kg desde ensacadora hacia cosedora.",
            nivel_dato="OK_VALIDADO",
        ),
        FichaEquipo(
            id="COSEDORA_SACOS",
            nombre="Cosedora de sacos (sellado)",
            tipo="ensacadora",
            etapa_asociada="E9_ENSACADO",
            notas=(
                "Sella sacos 20 kg via costura. Producto final: harina ingrediente "
                "alimentacion animal listo para despacho."
            ),
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
