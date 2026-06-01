"""Catálogo de tecnologías clave de la planta Trongkai.

Identificadas en P1/Tecnologías + P1/Ingeniería:
- Opticept (PEF - Pulsed Electric Field) → permeabilización celular
- Infrasonido → asistencia secado low-temp
- Equipos micro-molienda → tamaño partícula
- Pulsator (cotización en P1/Cotizaciones) → proveedor PEF
- Alister, Cascada (cotizaciones equipos auxiliares)

Cada tech tiene:
- nombre, proveedor, función en proceso
- TRL (Technology Readiness Level 1-9)
- CapEx estimado
- Impacto en rendimientos (% gain vs convencional)
- Energy consumption
- Estado validación Trongkai (idea / piloto / industrial)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EstadoValidacion = Literal["idea", "lab", "piloto", "industrial", "produccion"]
EtapaProceso = Literal[
    "recepcion", "pretratamiento", "permeabilizacion",
    "secado", "molienda", "extraccion", "concentracion", "envasado",
]


@dataclass
class Tecnologia:
    id: str
    nombre: str
    proveedor: str
    funcion: str
    etapa_proceso: EtapaProceso
    trl: int   # 1-9 (TRL 9 = comercial)
    capex_usd: float
    opex_kwh_ton: float | None    # consumo energético
    impacto_rendimiento_pct: float | None  # +% vs convencional
    impacto_calidad_pct: float | None
    estado_validacion: EstadoValidacion
    descripcion: str
    referencias_dossier: list[str]   # paths en inbox/
    pros: list[str]
    contras: list[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "proveedor": self.proveedor,
            "funcion": self.funcion,
            "etapa_proceso": self.etapa_proceso,
            "trl": self.trl,
            "capex_usd": self.capex_usd,
            "opex_kwh_ton": self.opex_kwh_ton,
            "impacto_rendimiento_pct": self.impacto_rendimiento_pct,
            "impacto_calidad_pct": self.impacto_calidad_pct,
            "estado_validacion": self.estado_validacion,
            "descripcion": self.descripcion,
            "referencias_dossier": self.referencias_dossier,
            "pros": self.pros,
            "contras": self.contras,
        }


# ============================================================================
# Catálogo
# ============================================================================

TECNOLOGIAS: tuple[Tecnologia, ...] = (
    Tecnologia(
        id="opticept-pef",
        nombre="Opticept PEF (Pulsed Electric Field)",
        proveedor="OptiCept Technologies AB (Suecia)",
        funcion="Permeabilización celular pre-prensado/secado",
        etapa_proceso="permeabilizacion",
        trl=9,  # Comercial probado
        capex_usd=850_000,
        opex_kwh_ton=15,  # Muy bajo vs prensado en frío
        impacto_rendimiento_pct=18.0,  # +18% extracción aceite alperujo
        impacto_calidad_pct=12.0,  # +12% polifenoles preservados
        estado_validacion="piloto",
        descripcion=(
            "Tecnología sueca de Pulsed Electric Field validada en olivar mediterráneo. "
            "Aplicada PRE-prensado mecánico, aumenta extracción de aceite en alperujo +18% "
            "manteniendo polifenoles (antioxidantes) intactos. Sin solventes, sin calor."
        ),
        referencias_dossier=[
            "03-operacional/capacidad-equipos/Opticept__PEF Presentation Esp.pdf",
            "03-operacional/capacidad-equipos/Opticept__Copia de OliveCEPT - Results From Greece.mp4",
            "02-financiero/capex-cotizaciones/Pulsator__*",  # cotización proveedor
        ],
        pros=[
            "Validación industrial 9/9 TRL en olivar griego",
            "Sin químicos, sin solventes — compatible orgánico/B-Corp",
            "Bajo consumo energético (15 kWh/ton vs 250 secado térmico)",
            "Preserva polifenoles y compuestos termolábiles",
        ],
        contras=[
            "CapEx alto (USD 850k) — pero amortizable en 18 meses con uplift rendimiento",
            "Proveedor único — riesgo concentración tecnológica",
            "Maintenance specialized — capacitación requerida",
        ],
    ),
    Tecnologia(
        id="infrasonido",
        nombre="Secado asistido por infrasonido",
        proveedor="A definir (proveedor en exploración)",
        funcion="Secado de tomasa/pomasa a baja temperatura",
        etapa_proceso="secado",
        trl=6,  # Prototipo demostrado en ambiente relevante
        capex_usd=320_000,
        opex_kwh_ton=85,  # ~3× menos que secado tradicional 250 kWh/ton
        impacto_rendimiento_pct=8.0,
        impacto_calidad_pct=25.0,  # Mucho mejor preservación nutrientes
        estado_validacion="piloto",
        descripcion=(
            "Ondas de baja frecuencia (<20 Hz) que aceleran la evaporación de agua "
            "sin calentar el material. Crítico para mantener proteínas y compuestos "
            "bioactivos en tomasa, pomasa y harinas. En etapa piloto industrial."
        ),
        referencias_dossier=[
            "03-operacional/capacidad-equipos/Infrasonido__infrasound secador.ppt",
            "03-operacional/capacidad-equipos/Infrasonido__Video WhatsApp 2025-07-12 11.02.24.mp4",
        ],
        pros=[
            "Reduce consumo energético secado ~65% (vs 250 kWh/ton tradicional)",
            "Preserva proteínas, vitaminas y compuestos bioactivos",
            "Footprint menor que secador rotatorio convencional",
            "Sin riesgo de quemado o caramelización",
        ],
        contras=[
            "TRL 6 — requiere validación piloto en planta Trongkai",
            "Equipos custom — sin estandarización industrial",
            "Throughput máximo limitado por área de exposición acústica",
        ],
    ),
    Tecnologia(
        id="micro-molienda",
        nombre="Equipos de micro-molienda criogénica",
        proveedor="Múltiples (a cotizar)",
        funcion="Reducción a partícula <50 micrones para ingredientes premium",
        etapa_proceso="molienda",
        trl=9,
        capex_usd=180_000,
        opex_kwh_ton=45,
        impacto_rendimiento_pct=0,  # No afecta rendimiento, sí calidad
        impacto_calidad_pct=35.0,  # Aumenta biodisponibilidad y solubilidad
        estado_validacion="industrial",
        descripcion=(
            "Molienda con enfriamiento criogénico (N2 líquido) para llegar a partículas "
            "<50 micrones manteniendo termolábiles. Crítico para SKUs premium PTEC "
            "(PROTEINA_UNICEL, ANTIOXIDANTE) donde el tamaño define el precio."
        ),
        referencias_dossier=[
            "03-operacional/capacidad-equipos/Equipos de micro molienda__*",
        ],
        pros=[
            "Habilita SKUs premium con margen alto (+30-50% precio vs molienda gruesa)",
            "Tecnología madura y disponible LATAM",
            "Modular — se puede escalar agregando líneas",
        ],
        contras=[
            "Consumo N2 líquido aumenta OpEx",
            "Polvos finos requieren manejo neumático cerrado (HACCP)",
            "Inversión en sistema de extracción adicional",
        ],
    ),
)


def listar_tecnologias() -> list[dict]:
    return [t.to_dict() for t in TECNOLOGIAS]


def resumen_tecnologias() -> dict:
    """Stats consolidados del stack tecnológico."""
    total = len(TECNOLOGIAS)
    capex_total = sum(t.capex_usd for t in TECNOLOGIAS)
    por_estado: dict[str, int] = {}
    por_etapa: dict[str, int] = {}
    trl_promedio = sum(t.trl for t in TECNOLOGIAS) / total if total else 0
    for t in TECNOLOGIAS:
        por_estado[t.estado_validacion] = por_estado.get(t.estado_validacion, 0) + 1
        por_etapa[t.etapa_proceso] = por_etapa.get(t.etapa_proceso, 0) + 1

    return {
        "total_tecnologias": total,
        "capex_stack_usd": capex_total,
        "trl_promedio": round(trl_promedio, 1),
        "por_estado_validacion": por_estado,
        "por_etapa_proceso": por_etapa,
    }
