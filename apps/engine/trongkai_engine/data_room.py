"""Data Room — checklist Due Diligence típico para LP / banco / DFI.

Basado en best-practices DD para fondos de inversión / DFIs (BID Invest, IFC,
Proparco, FinDev). 6 categorías × ~7 items = 42 items DD.

Cada item tiene:
- estado: faltante / parcial / completo
- responsable interno
- doc esperado
- relevancia (must-have / nice-to-have)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EstadoDD(StrEnum):
    FALTANTE = "faltante"     # No existe
    PARCIAL = "parcial"        # Existe pero incompleto
    COMPLETO = "completo"      # Listo para LP


class Categoria(StrEnum):
    CORPORATIVO = "Corporativo y Legal"
    FINANCIERO = "Financiero y Auditoría"
    COMERCIAL = "Comercial y Mercado"
    OPERACIONAL = "Operacional y Técnico"
    ESG = "ESG y Sustentabilidad"
    EQUIPO = "Equipo y Gobierno"


@dataclass
class ItemDD:
    id: str
    titulo: str
    descripcion: str
    categoria: Categoria
    estado: EstadoDD
    responsable: str
    formato: str
    must_have: bool = True
    plataforma_link: str = ""  # link a página de la plataforma que cubre esto

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "categoria": self.categoria.value,
            "estado": self.estado.value,
            "responsable": self.responsable,
            "formato": self.formato,
            "must_have": self.must_have,
            "plataforma_link": self.plataforma_link,
        }


# ============================================================================
# Checklist completo
# ============================================================================

CHECKLIST_DD: list[ItemDD] = [
    # ===== CORPORATIVO Y LEGAL =====
    ItemDD("escritura-constitucion", "Escritura de constitución",
           "Escritura pública vigente + modificaciones posteriores",
           Categoria.CORPORATIVO, EstadoDD.FALTANTE, "Legal", "PDF escritura"),
    ItemDD("estatutos-actualizados", "Estatutos actualizados",
           "Estatutos vigentes con todas las reformas",
           Categoria.CORPORATIVO, EstadoDD.FALTANTE, "Legal", "PDF"),
    ItemDD("certificado-vigencia", "Certificado de vigencia",
           "Vigente últimos 30 días",
           Categoria.CORPORATIVO, EstadoDD.FALTANTE, "Legal", "PDF Registro Comercio"),
    ItemDD("estructura-societaria", "Estructura societaria",
           "Org chart con % participación accionistas",
           Categoria.CORPORATIVO, EstadoDD.PARCIAL, "Legal", "PDF + Excel cap table"),
    ItemDD("patentes-marcas", "Patentes y marcas registradas",
           "Propiedad intelectual: Trongkai marca + procesos PTEC",
           Categoria.CORPORATIVO, EstadoDD.FALTANTE, "Legal / IP",
           "PDFs INAPI", must_have=False),
    ItemDD("contratos-clientes", "Contratos vigentes con clientes",
           "LOIs + contratos firmados con compradores Feed/Food",
           Categoria.CORPORATIVO, EstadoDD.FALTANTE, "Comercial", "PDFs"),
    ItemDD("contratos-mmpp", "Contratos con proveedores MMPP",
           "Acuerdos largo plazo con olivar / tomatera / vinícolas",
           Categoria.CORPORATIVO, EstadoDD.FALTANTE, "Comercial", "PDFs"),

    # ===== FINANCIERO =====
    ItemDD("eerr-historico", "EERR histórico 3 años",
           "Estados financieros auditados últimos 3 años (si aplica)",
           Categoria.FINANCIERO, EstadoDD.FALTANTE, "Contadora", "PDFs auditados"),
    ItemDD("modelo-proyecciones", "Modelo financiero proyecciones 5 años",
           "Plan 5 años con EERR mensual, KPIs, sensitivity",
           Categoria.FINANCIERO, EstadoDD.COMPLETO, "Plataforma", "Excel + PDF",
           plataforma_link="/plan"),
    ItemDD("analisis-sensibilidad", "Análisis de sensibilidad",
           "Heatmap 2D + break-even + tornado",
           Categoria.FINANCIERO, EstadoDD.COMPLETO, "Plataforma", "PDF",
           plataforma_link="/sensitivity"),
    ItemDD("monte-carlo", "Análisis Monte Carlo",
           "10k simulaciones con riesgo climático integrado",
           Categoria.FINANCIERO, EstadoDD.COMPLETO, "Plataforma", "Charts",
           plataforma_link="/plan"),
    ItemDD("valuation", "Valoración exit (DCF + comparables)",
           "EV/EBITDA 9.63× + DCF + comparables LATAM",
           Categoria.FINANCIERO, EstadoDD.PARCIAL, "Plataforma + asesor",
           "PDF tearsheet", plataforma_link="/dashboard-directorio"),
    ItemDD("estructura-deuda", "Estructura de deuda propuesta",
           "Term sheets bancarios + DSCR + LLCR",
           Categoria.FINANCIERO, EstadoDD.PARCIAL, "Finanzas / asesor",
           "Term sheets + plataforma", plataforma_link="/financiamiento"),
    ItemDD("auditor-externo", "Auditor externo designado",
           "Big-4 o local respetable",
           Categoria.FINANCIERO, EstadoDD.FALTANTE, "Finanzas", "Carta engagement"),

    # ===== COMERCIAL Y MERCADO =====
    ItemDD("pitch-deck", "Pitch deck ejecutivo",
           "Deck PPT/PDF para roadshow",
           Categoria.COMERCIAL, EstadoDD.PARCIAL, "Nicolás", "PDF + Keynote/PPT"),
    ItemDD("tearsheet", "Tearsheet ejecutivo PDF",
           "Resumen 3 páginas con KPIs, valoración, ESG",
           Categoria.COMERCIAL, EstadoDD.COMPLETO, "Plataforma", "PDF",
           plataforma_link="/dashboard-directorio"),
    ItemDD("market-study", "Estudio de mercado validado",
           "TAM/SAM/SOM + competencia + tendencias",
           Categoria.COMERCIAL, EstadoDD.PARCIAL, "Comercial / consultor",
           "PDF estudio mercado"),
    ItemDD("clientes-pipeline", "Pipeline comercial",
           "Lista clientes target con etapa + ticket",
           Categoria.COMERCIAL, EstadoDD.FALTANTE, "Sergio", "CRM o Excel"),
    ItemDD("benchmarking-precios", "Benchmarking de precios",
           "Comparación precios SKUs vs mercado",
           Categoria.COMERCIAL, EstadoDD.COMPLETO, "Plataforma",
           "Tabla precios", plataforma_link="/variables"),
    ItemDD("comparables-ma", "Comparables transacciones M&A",
           "Múltiplos pagados en operaciones similares LATAM",
           Categoria.COMERCIAL, EstadoDD.PARCIAL, "Banca inversión",
           "PDF benchmarking", must_have=False),
    ItemDD("estrategia-go-to-market", "Estrategia go-to-market",
           "Plan comercial por canal + ramp-up",
           Categoria.COMERCIAL, EstadoDD.FALTANTE, "Sergio", "PDF estrategia"),

    # ===== OPERACIONAL Y TÉCNICO =====
    ItemDD("layout-planta", "Layout de planta + ingeniería",
           "Planos arquitectura + ingeniería detalle",
           Categoria.OPERACIONAL, EstadoDD.FALTANTE, "Ingeniería", "AutoCAD + PDF"),
    ItemDD("balance-masa", "Balance de masa validado",
           "Cierre ±0.5% del flujo MMPP→producto",
           Categoria.OPERACIONAL, EstadoDD.COMPLETO, "Plataforma",
           "Sankey + tabla", plataforma_link="/balance"),
    ItemDD("capex-detallado", "CapEx detallado por equipo",
           "Cotizaciones firmas por línea de equipo",
           Categoria.OPERACIONAL, EstadoDD.PARCIAL, "Jaime + proveedores",
           "Excel + cotizaciones PDF"),
    ItemDD("agenda-mmpp", "Agenda de recepción MMPP",
           "Calendario estacional con buffer",
           Categoria.OPERACIONAL, EstadoDD.COMPLETO, "Plataforma",
           "Calendario", plataforma_link="/agenda"),
    ItemDD("permisos-sanitarios", "Permisos sanitarios SAG/Seremi",
           "Resoluciones vigentes + fecha vencimiento",
           Categoria.OPERACIONAL, EstadoDD.FALTANTE, "Compliance",
           "PDFs resoluciones"),
    ItemDD("rca", "Resolución Calificación Ambiental",
           "RCA del proyecto (si aplica)",
           Categoria.OPERACIONAL, EstadoDD.FALTANTE, "Compliance / legal",
           "PDF RCA"),
    ItemDD("seguros", "Pólizas de seguros activas",
           "Operacional + responsabilidad civil + lucro cesante",
           Categoria.OPERACIONAL, EstadoDD.FALTANTE, "Finanzas", "PDFs pólizas"),

    # ===== ESG Y SUSTENTABILIDAD =====
    ItemDD("huella-carbono", "Huella de carbono LCA",
           "LCA con 3 escenarios + revenue créditos CO2",
           Categoria.ESG, EstadoDD.COMPLETO, "Plataforma",
           "Reporte LCA", plataforma_link="/carbono"),
    ItemDD("compliance-rep", "Compliance Ley REP",
           "8 hitos regulatorios timeline",
           Categoria.ESG, EstadoDD.COMPLETO, "Plataforma",
           "Timeline", plataforma_link="/compliance"),
    ItemDD("riesgo-climatico", "Análisis de riesgo climático",
           "4 eventos climáticos chilenos (sequía, granizo, heladas)",
           Categoria.ESG, EstadoDD.COMPLETO, "Plataforma",
           "Matriz riesgo", plataforma_link="/riesgo"),
    ItemDD("certificaciones-esg", "Certificaciones ESG activas",
           "B-Corp, HACCP, GMP+ — estado + roadmap",
           Categoria.ESG, EstadoDD.FALTANTE, "QA / Compliance",
           "Checklist + evidencias"),
    ItemDD("politicas-internas", "Políticas internas (ética, género, etc)",
           "Code of conduct + políticas de diversidad",
           Categoria.ESG, EstadoDD.FALTANTE, "RR.HH.", "PDFs políticas",
           must_have=False),
    ItemDD("alineacion-sdg", "Alineación con SDGs",
           "Mapeo SDG 12, 13, 9, 8",
           Categoria.ESG, EstadoDD.PARCIAL, "ESG officer",
           "PDF mapeo SDG", must_have=False),
    ItemDD("sustainability-linked-bonds", "Simulador Sustainability Bonds",
           "SLB calculator con KPIs step-up",
           Categoria.ESG, EstadoDD.COMPLETO, "Plataforma",
           "Simulador", plataforma_link="/slb"),

    # ===== EQUIPO Y GOBIERNO =====
    ItemDD("cvs-fundadores", "CVs fundadores y directorio",
           "Nicolás, Jaime, Sergio + miembros directorio",
           Categoria.EQUIPO, EstadoDD.FALTANTE, "Cada uno",
           "PDFs + fotos profesionales"),
    ItemDD("organigrama", "Organigrama empresa",
           "Estructura organizacional + reporting lines",
           Categoria.EQUIPO, EstadoDD.FALTANTE, "RR.HH.", "PDF orgchart"),
    ItemDD("directorio-actas", "Actas de directorio últimas 6",
           "Decisiones materiales tomadas",
           Categoria.EQUIPO, EstadoDD.FALTANTE, "Secretaria directorio",
           "PDFs actas"),
    ItemDD("politica-compensacion", "Política de compensación ejecutivos",
           "Sueldo + bonos + opciones para C-level",
           Categoria.EQUIPO, EstadoDD.FALTANTE, "Directorio", "PDF política",
           must_have=False),
    ItemDD("advisors", "Lista de advisors / mentores",
           "Con expertise relevante",
           Categoria.EQUIPO, EstadoDD.PARCIAL, "Nicolás", "PDF + LinkedIn",
           must_have=False),
    ItemDD("alianzas-estrategicas", "Alianzas estratégicas",
           "MOUs con universidades, CORFO, partners técnicos",
           Categoria.EQUIPO, EstadoDD.PARCIAL, "Nicolás", "MOUs PDF"),
]


@dataclass
class ResumenDD:
    total: int
    completos: int
    parciales: int
    faltantes: int
    pct_completo: float
    pct_avance: float          # completo + parcial × 0.5
    by_categoria: dict[str, dict]

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "completos": self.completos,
            "parciales": self.parciales,
            "faltantes": self.faltantes,
            "pct_completo": self.pct_completo,
            "pct_avance": self.pct_avance,
            "by_categoria": self.by_categoria,
        }


def resumen_checklist() -> ResumenDD:
    """Calcula stats agregadas del checklist."""
    total = len(CHECKLIST_DD)
    completos = sum(1 for i in CHECKLIST_DD if i.estado == EstadoDD.COMPLETO)
    parciales = sum(1 for i in CHECKLIST_DD if i.estado == EstadoDD.PARCIAL)
    faltantes = sum(1 for i in CHECKLIST_DD if i.estado == EstadoDD.FALTANTE)
    pct_completo = round(completos / total * 100, 1) if total > 0 else 0
    pct_avance = round((completos + parciales * 0.5) / total * 100, 1) if total > 0 else 0

    by_cat: dict[str, dict] = {}
    for cat in Categoria:
        items_cat = [i for i in CHECKLIST_DD if i.categoria == cat]
        if not items_cat:
            continue
        by_cat[cat.value] = {
            "total": len(items_cat),
            "completos": sum(1 for i in items_cat if i.estado == EstadoDD.COMPLETO),
            "parciales": sum(1 for i in items_cat if i.estado == EstadoDD.PARCIAL),
            "faltantes": sum(1 for i in items_cat if i.estado == EstadoDD.FALTANTE),
        }

    return ResumenDD(
        total=total,
        completos=completos,
        parciales=parciales,
        faltantes=faltantes,
        pct_completo=pct_completo,
        pct_avance=pct_avance,
        by_categoria=by_cat,
    )


def checklist_completo() -> dict:
    """Devuelve el checklist completo + resumen."""
    return {
        "items": [i.to_dict() for i in CHECKLIST_DD],
        "resumen": resumen_checklist().to_dict(),
    }
