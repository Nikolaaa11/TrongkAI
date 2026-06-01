"""Catálogo de clientes y prospects reales identificados en el dump P1.

Cada cliente potencial tiene:
- nombre, sector, país
- producto target (qué SKU Trongkai compraría)
- volumen estimado anual
- estado de relación (prospect / contactado / dd / loi / contrato)
- canal contacto + último contacto
- notas comerciales
- link al dossier en inbox/01-comercial/

Identificados en P1/Clientes/:
- Agrozzi (Chile, alimentos)
- Iansa Molina (Chile, azúcar/feed)
- Sugal (Portugal/Chile, tomate)
- Olivares de Quepu (Chile, olivar)
- San Clemente Foods (Chile, alimentos)
+ benchmarks de proteínas comparables (Fava bean GP68, Yellow pea, etc)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

EstadoRelacion = Literal["prospect", "contactado", "dd", "loi", "contrato", "perdido"]
Sector = Literal["alimentos_humanos", "feed_acuicola", "feed_pet", "feed_ganaderia", "industrial", "agro_input"]


@dataclass
class ClienteReal:
    id: str
    nombre: str
    pais: str
    sector: Sector
    producto_target: list[str]      # SKUs Trongkai que comprarían
    volumen_anual_estimado_ton: float
    estado_relacion: EstadoRelacion
    canal_contacto: str
    ultimo_contacto: str            # YYYY-MM-DD o ""
    valor_anual_estimado_usd: float
    notas: str
    dossier_inbox: str = ""         # path relativo dentro de inbox/

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "pais": self.pais,
            "sector": self.sector,
            "producto_target": self.producto_target,
            "volumen_anual_estimado_ton": self.volumen_anual_estimado_ton,
            "estado_relacion": self.estado_relacion,
            "canal_contacto": self.canal_contacto,
            "ultimo_contacto": self.ultimo_contacto,
            "valor_anual_estimado_usd": self.valor_anual_estimado_usd,
            "notas": self.notas,
            "dossier_inbox": self.dossier_inbox,
        }


# ============================================================================
# Catálogo inicial — datos extraídos del dump P1 + conocimiento sectorial
# ============================================================================

CLIENTES: tuple[ClienteReal, ...] = (
    ClienteReal(
        id="agrozzi",
        nombre="Agrozzi",
        pais="Chile",
        sector="alimentos_humanos",
        producto_target=["HARINA_TOMASA", "HARINA_ALPERUJO", "LICOPENO"],
        volumen_anual_estimado_ton=500,
        estado_relacion="contactado",
        canal_contacto="Reunión directa equipo comercial",
        ultimo_contacto="2025-12-15",
        valor_anual_estimado_usd=350_000,
        notas="Grupo agroindustrial chileno (tomate, frutas procesadas). "
              "Interés alto en tomasa procesada y licopeno como ingrediente. "
              "Posible offtake de 500 ton/año si pasa specs HACCP.",
        dossier_inbox="01-comercial/contratos-firmados/Agrozzi__*",
    ),
    ClienteReal(
        id="iansa-molina",
        nombre="Iansa Molina",
        pais="Chile",
        sector="agro_input",
        producto_target=["HARINA_TOMASA", "HARINA_POMASA"],
        volumen_anual_estimado_ton=300,
        estado_relacion="contactado",
        canal_contacto="Equipo planta Molina",
        ultimo_contacto="2025-11-20",
        valor_anual_estimado_usd=210_000,
        notas="Grupo azúcar / tomate Chile. Genera tomasa como subproducto y "
              "tiene interés en cerrar el loop interno comprando harina procesada "
              "para uso en feed ganadería propio. Sinergia bidireccional MMPP+venta.",
        dossier_inbox="01-comercial/contratos-firmados/Iansa Molina__*",
    ),
    ClienteReal(
        id="sugal",
        nombre="Sugal Group",
        pais="Portugal / Chile",
        sector="alimentos_humanos",
        producto_target=["LICOPENO", "PECTINA", "HARINA_TOMASA"],
        volumen_anual_estimado_ton=200,
        estado_relacion="prospect",
        canal_contacto="LinkedIn intro pendiente",
        ultimo_contacto="",
        valor_anual_estimado_usd=300_000,
        notas="Procesador de tomate global (Portugal + Chile Quillota). "
              "Mayor productor LATAM. Potencial cliente premium para licopeno "
              "extraído + pectina. Volúmenes pequeños pero alto valor unitario.",
        dossier_inbox="01-comercial/contratos-firmados/Sugal__*",
    ),
    ClienteReal(
        id="olivares-quepu",
        nombre="Olivares de Quepu",
        pais="Chile",
        sector="agro_input",
        producto_target=["ACEITE_ALPERUJO", "HARINA_ALPERUJO"],
        volumen_anual_estimado_ton=400,
        estado_relacion="contactado",
        canal_contacto="Visita planta Pencahue",
        ultimo_contacto="2025-10-30",
        valor_anual_estimado_usd=420_000,
        notas="Productor olivar chileno mediano-grande, región Maule. "
              "Provee alperujo como MMPP + interés en comprar aceite extraído "
              "(arbitraje: vende alperujo y compra de vuelta aceite premium).",
        dossier_inbox="01-comercial/contratos-firmados/Olivares de quepu__*",
    ),
    ClienteReal(
        id="san-clemente-foods",
        nombre="San Clemente Foods",
        pais="Chile",
        sector="alimentos_humanos",
        producto_target=["HARINA_ALPERUJO", "ANTIOXIDANTE", "UMAMI"],
        volumen_anual_estimado_ton=150,
        estado_relacion="prospect",
        canal_contacto="Mail intro",
        ultimo_contacto="",
        valor_anual_estimado_usd=180_000,
        notas="Procesador alimentos chileno región Maule. "
              "Interés en ingredientes funcionales premium (antioxidantes, umami) "
              "para línea de productos clean-label.",
        dossier_inbox="01-comercial/contratos-firmados/San Clemente Foods__*",
    ),
)


# Benchmarks de productos competidores identificados (proteínas comparables)
BENCHMARKS_PROTEINAS = (
    {
        "producto": "Low protein powder of fava bean",
        "competidor": "Genérico (especs Jan 2025)",
        "precio_referencia_usd_kg": 4.5,
        "uso": "Alimento humano, sustituto proteína animal",
        "comparable_a": "HARINA_TOMASA con extracción proteína",
        "dossier_inbox": "07-mercado/benchmarks-precios/Low protein powder of fava bean -2025-01-22.pdf",
    },
    {
        "producto": "SDS GP Protein Concentrate GP68",
        "competidor": "Concentrado proteína 68%",
        "precio_referencia_usd_kg": 5.2,
        "uso": "Feed acuícola premium",
        "comparable_a": "PROTEINA_UNICEL",
        "dossier_inbox": "07-mercado/benchmarks-precios/SDS GP Protein Concentrate GP68.pdf",
    },
    {
        "producto": "Yellow pea protein (small bag)",
        "competidor": "Proteína de arveja amarilla",
        "precio_referencia_usd_kg": 3.8,
        "uso": "Plant-based foods humanos",
        "comparable_a": "HARINA_ALPERUJO functional",
        "dossier_inbox": "07-mercado/benchmarks-precios/Yellow pea protein(small bag)_3012_eng.pdf",
    },
)


def listar_clientes() -> list[dict]:
    return [c.to_dict() for c in CLIENTES]


def listar_benchmarks() -> list[dict]:
    return list(BENCHMARKS_PROTEINAS)


def resumen_clientes() -> dict:
    """Stats agregados del catálogo."""
    total = len(CLIENTES)
    por_estado: dict[str, int] = {}
    por_sector: dict[str, int] = {}
    valor_total_usd = 0
    volumen_total_ton = 0
    for c in CLIENTES:
        por_estado[c.estado_relacion] = por_estado.get(c.estado_relacion, 0) + 1
        por_sector[c.sector] = por_sector.get(c.sector, 0) + 1
        valor_total_usd += c.valor_anual_estimado_usd
        volumen_total_ton += c.volumen_anual_estimado_ton

    return {
        "total_clientes": total,
        "por_estado": por_estado,
        "por_sector": por_sector,
        "valor_anual_total_usd": valor_total_usd,
        "volumen_anual_total_ton": volumen_total_ton,
        "benchmarks_count": len(BENCHMARKS_PROTEINAS),
    }
