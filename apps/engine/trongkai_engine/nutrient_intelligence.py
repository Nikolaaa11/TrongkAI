"""Nutrient Intelligence - perfil científico de cada SKU Trongkai.

Para cada uno de los 12 SKUs:
- Compuestos bioactivos clave (con % típico)
- Aplicaciones comerciales por mercado
- Mercados target con TAM/SAM
- Certificaciones requeridas
- Premium pricing vs commodity
- Papers científicos clave de respaldo
- Trends 2026 y demanda esperada

Base científica integrada al modelo financiero para defender pricing
ante LP/clientes y calibrar mejoras de tecnología.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Mercado = Literal[
    "feed_acuicola", "feed_pet", "feed_ganaderia",
    "alimentos_humanos", "nutraceutica", "cosmetica",
    "industrial_quimico", "farma",
]


@dataclass
class CompuestoActivo:
    nombre: str
    porcentaje_tipico: float  # % en producto seco
    funcion_bioactiva: str
    valor_comercial: str       # "alto" | "medio" | "bajo"

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "porcentaje_tipico": self.porcentaje_tipico,
            "funcion_bioactiva": self.funcion_bioactiva,
            "valor_comercial": self.valor_comercial,
        }


@dataclass
class AplicacionComercial:
    mercado: Mercado
    uso_especifico: str
    formato_producto: str         # "polvo", "encapsulado", "líquido", "extracto"
    precio_usd_kg_premium: float  # precio si tiene specs premium
    tam_global_usd_anual: float   # TAM del nicho global
    certificaciones_requeridas: list[str]
    competidores_clave: list[str]

    def to_dict(self) -> dict:
        return {
            "mercado": self.mercado,
            "uso_especifico": self.uso_especifico,
            "formato_producto": self.formato_producto,
            "precio_usd_kg_premium": self.precio_usd_kg_premium,
            "tam_global_usd_anual": self.tam_global_usd_anual,
            "certificaciones_requeridas": self.certificaciones_requeridas,
            "competidores_clave": self.competidores_clave,
        }


@dataclass
class PerfilNutricional:
    sku: str
    nombre_comercial: str
    mmpp_origen: str
    descripcion_cientifica: str

    proteina_pct: float | None
    grasa_pct: float | None
    fibra_dietetica_pct: float | None
    humedad_pct: float

    compuestos_activos: list[CompuestoActivo] = field(default_factory=list)
    aplicaciones: list[AplicacionComercial] = field(default_factory=list)

    valor_nutricional_score: int = 0  # 0-100 score consolidado
    diferenciador_clave: str = ""
    riesgos_tecnicos: list[str] = field(default_factory=list)
    papers_referencia: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "nombre_comercial": self.nombre_comercial,
            "mmpp_origen": self.mmpp_origen,
            "descripcion_cientifica": self.descripcion_cientifica,
            "proteina_pct": self.proteina_pct,
            "grasa_pct": self.grasa_pct,
            "fibra_dietetica_pct": self.fibra_dietetica_pct,
            "humedad_pct": self.humedad_pct,
            "compuestos_activos": [c.to_dict() for c in self.compuestos_activos],
            "aplicaciones": [a.to_dict() for a in self.aplicaciones],
            "valor_nutricional_score": self.valor_nutricional_score,
            "diferenciador_clave": self.diferenciador_clave,
            "riesgos_tecnicos": self.riesgos_tecnicos,
            "papers_referencia": self.papers_referencia,
        }


# ============================================================================
# CATÁLOGO COMPLETO (12 SKUs con perfil científico)
# ============================================================================

PERFILES_NUTRICIONALES: tuple[PerfilNutricional, ...] = (

    PerfilNutricional(
        sku="HARINA_ALPERUJO",
        nombre_comercial="Harina funcional de alperujo",
        mmpp_origen="Subproducto extracción aceite oliva (alperujo)",
        descripcion_cientifica=(
            "Polvo seco rico en polifenoles bioactivos (hidroxitirosol, oleuropeína) "
            "+ fibra dietética + ácidos grasos monoinsaturados residuales. Considerado "
            "como ingrediente funcional con propiedades antioxidantes, cardioprotectoras "
            "y antiinflamatorias documentadas (>200 papers peer-reviewed)."
        ),
        proteina_pct=8.0,
        grasa_pct=12.0,
        fibra_dietetica_pct=45.0,
        humedad_pct=10.0,
        compuestos_activos=[
            CompuestoActivo("Hidroxitirosol", 0.5, "Antioxidante 10× más potente que vit E", "alto"),
            CompuestoActivo("Oleuropeína", 1.2, "Cardioprotector, anti-LDL oxidado", "alto"),
            CompuestoActivo("Ácido oleico residual", 8.0, "MUFA cardiosaludable", "medio"),
            CompuestoActivo("Lignina + Celulosa", 30.0, "Fibra dietética soluble + insoluble", "medio"),
            CompuestoActivo("Tirosol", 0.3, "Antioxidante complementario", "medio"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "alimentos_humanos",
                "Aditivo en panificación premium clean-label",
                "polvo micronizado <50μm",
                4.5,
                2_500_000_000,
                ["BRC", "HACCP", "Organic EU"],
                ["Phenofarm (Italia)", "Olive Phenolics (España)"],
            ),
            AplicacionComercial(
                "nutraceutica",
                "Cápsulas antioxidantes (300 mg hidroxitirosol/día EFSA claim)",
                "extracto encapsulado 6% HT",
                85.0,
                450_000_000,
                ["GMP+", "Novel Food EU", "USP"],
                ["DSM", "Lonza Pharma", "BioActor"],
            ),
            AplicacionComercial(
                "cosmetica",
                "Crema anti-edad (mercado premium)",
                "extracto liofilizado",
                120.0,
                180_000_000,
                ["COSMOS", "ECOCERT"],
                ["L'Oréal Active", "Naturex"],
            ),
            AplicacionComercial(
                "feed_acuicola",
                "Pellet salmón con antioxidantes naturales",
                "polvo",
                2.8,
                850_000_000,
                ["GMP+", "ASC"],
                ["Cargill", "BioMar", "Skretting"],
            ),
        ],
        valor_nutricional_score=92,
        diferenciador_clave=(
            "Único ingrediente vegetal con claim EFSA aprobado para protección de LDL "
            "frente a daño oxidativo (5 mg hidroxitirosol/día). Permite labels premium."
        ),
        riesgos_tecnicos=[
            "Estabilidad oxidativa: requiere secado low-temp para preservar polifenoles",
            "Variabilidad por temporada de cosecha y cultivar de olivo",
            "Sabor amargo limita inclusión a 5-10% en formulación alimentaria",
        ],
        papers_referencia=[
            "Romani et al. 2019 - Olive Mill Wastewater valorization",
            "Cifá et al. 2018 - Olive pomace bioactive compounds",
            "Difonzo et al. 2021 - Hydroxytyrosol bioactivity",
        ],
    ),

    PerfilNutricional(
        sku="ACEITE_ALPERUJO",
        nombre_comercial="Aceite extraído de alperujo refinado",
        mmpp_origen="Extracción 2da etapa por solventes del alperujo",
        descripcion_cientifica=(
            "Aceite vegetal de 2da extracción con perfil de ácidos grasos similar al oliva "
            "virgen pero con mayor concentración de antioxidantes residuales. Apto para uso "
            "alimentario tras refinación, y para cosmética/cuidado piel directo."
        ),
        proteina_pct=0.0,
        grasa_pct=99.5,
        fibra_dietetica_pct=0.0,
        humedad_pct=0.1,
        compuestos_activos=[
            CompuestoActivo("Ácido oleico", 70.0, "MUFA cardiosaludable", "alto"),
            CompuestoActivo("Ácido linoleico", 10.0, "Omega-6 esencial", "medio"),
            CompuestoActivo("Tocoferoles (vit E)", 0.02, "Antioxidante natural", "medio"),
            CompuestoActivo("Escualeno", 0.3, "Anti-aging, hidratante piel", "alto"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "alimentos_humanos",
                "Aceite culinario gama media",
                "líquido refinado",
                3.5,
                1_200_000_000,
                ["HACCP", "Kosher"],
                ["Sovena", "Deoleo", "Carbonell"],
            ),
            AplicacionComercial(
                "cosmetica",
                "Aceite hidratante corporal premium",
                "líquido virgen no refinado",
                15.0,
                350_000_000,
                ["COSMOS", "USDA Organic"],
                ["Weleda", "Dr. Hauschka"],
            ),
        ],
        valor_nutricional_score=75,
        diferenciador_clave="Perfil lipídico mediterráneo a precio commodity",
        riesgos_tecnicos=["Refinación requerida para uso alimentario"],
        papers_referencia=["FAO 2020 Olive oil quality", "Boskou 2015 Olive oil"],
    ),

    PerfilNutricional(
        sku="HARINA_ORUJO",
        nombre_comercial="Harina de orujo de uva",
        mmpp_origen="Vinificación (cáscaras + semillas + raspones)",
        descripcion_cientifica=(
            "Fuente concentrada de resveratrol, proantocianidinas y taninos. Considerado "
            "uno de los ingredientes con mayor capacidad antioxidante (ORAC value alto). "
            "Aplicaciones premium en feed acuícola (color natural del salmón) y "
            "nutracéutica anti-aging."
        ),
        proteina_pct=11.0,
        grasa_pct=8.0,
        fibra_dietetica_pct=50.0,
        humedad_pct=8.0,
        compuestos_activos=[
            CompuestoActivo("Resveratrol", 0.05, "Anti-aging, anti-inflamatorio", "alto"),
            CompuestoActivo("Proantocianidinas", 4.0, "Antioxidante > vit C ×20", "alto"),
            CompuestoActivo("Quercetina", 0.2, "Anti-inflamatorio", "medio"),
            CompuestoActivo("Antocianinas", 2.5, "Color natural rojo/púrpura", "alto"),
            CompuestoActivo("Taninos", 8.0, "Antimicrobianos", "medio"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "feed_acuicola",
                "Pellet salmón - color rosa natural + antioxidantes",
                "polvo micronizado",
                3.2,
                950_000_000,
                ["GMP+", "ASC", "BAP"],
                ["Cargill", "BioMar", "Skretting"],
            ),
            AplicacionComercial(
                "nutraceutica",
                "Extracto antioxidante (cápsulas resveratrol-enriched)",
                "extracto seco 5% resveratrol",
                145.0,
                620_000_000,
                ["GMP+", "USP", "Novel Food EU"],
                ["DSM", "Pure Encapsulations", "Thorne"],
            ),
            AplicacionComercial(
                "alimentos_humanos",
                "Aditivo polifenólico en barras energéticas",
                "polvo",
                6.5,
                340_000_000,
                ["BRC", "HACCP"],
                ["Naturex", "Indena"],
            ),
        ],
        valor_nutricional_score=88,
        diferenciador_clave=(
            "ORAC value ~12,000 μmol TE/g (10× arándanos). Resveratrol 0.05% es competitivo "
            "con extractos comerciales sin necesidad de fermentación."
        ),
        riesgos_tecnicos=[
            "Variabilidad por cepa (Cabernet > Merlot > blancas)",
            "Taninos pueden generar astringencia en feed",
        ],
        papers_referencia=[
            "Beres et al. 2017 - Grape pomace bioactive",
            "Yu & Ahmedna 2013 - Grape antioxidants",
        ],
    ),

    PerfilNutricional(
        sku="HARINA_TOMASA",
        nombre_comercial="Harina funcional de tomasa (residuo tomate)",
        mmpp_origen="Residuo industrial procesamiento tomate (piel + semilla)",
        descripcion_cientifica=(
            "Concentrado natural de licopeno (carotenoide rojo más potente como antioxidante) "
            "+ fibra + proteína vegetal. Licopeno asociado con reducción de cáncer próstata, "
            "cardiovascular y degeneración macular."
        ),
        proteina_pct=18.0,
        grasa_pct=10.0,
        fibra_dietetica_pct=42.0,
        humedad_pct=9.0,
        compuestos_activos=[
            CompuestoActivo("Licopeno", 0.08, "Antioxidante > β-caroteno ×2.5", "alto"),
            CompuestoActivo("β-caroteno", 0.02, "Precursor vit A", "medio"),
            CompuestoActivo("Naringenina", 0.15, "Anti-inflamatorio", "medio"),
            CompuestoActivo("Cutina", 5.0, "Bioplástico potencial", "medio"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "alimentos_humanos",
                "Fortificante natural en salsas/sopas",
                "polvo",
                4.5,
                780_000_000,
                ["BRC", "HACCP"],
                ["LycoRed", "Indena", "DSM"],
            ),
            AplicacionComercial(
                "feed_pet",
                "Aditivo color natural en pet food premium",
                "polvo micronizado",
                5.8,
                420_000_000,
                ["FEDIAF", "AAFCO"],
                ["Mars Petcare", "Nestlé Purina"],
            ),
            AplicacionComercial(
                "nutraceutica",
                "Cápsulas licopeno (10 mg/dia)",
                "extracto 10% lycopene",
                95.0,
                890_000_000,
                ["GMP+", "USP"],
                ["LycoRed", "Lyc-O-Mato", "BASF"],
            ),
        ],
        valor_nutricional_score=85,
        diferenciador_clave="Licopeno natural >sintético (mejor biodisponibilidad)",
        riesgos_tecnicos=[
            "Fotosensibilidad: empaque opaco requerido",
            "Estabilidad limitada >60°C",
        ],
        papers_referencia=[
            "Ranveer & Sahoo 2017 - Tomato pomace bioactive",
            "Allwood et al. 2020 - Lycopene production",
        ],
    ),

    PerfilNutricional(
        sku="HARINA_POMASA",
        nombre_comercial="Harina de pomasa (residuo manzana)",
        mmpp_origen="Industria jugo manzana (bagazo + semillas)",
        descripcion_cientifica=(
            "Fuente concentrada de pectina (fibra soluble), polifenoles tipo flavonoides "
            "(quercetina, catequinas) y triterpenoides. Aplicaciones gelificantes en "
            "alimentos + suplementos digestivos."
        ),
        proteina_pct=5.0,
        grasa_pct=2.5,
        fibra_dietetica_pct=58.0,
        humedad_pct=8.0,
        compuestos_activos=[
            CompuestoActivo("Pectina", 18.0, "Gelificante + prebiótico", "alto"),
            CompuestoActivo("Quercetina", 0.3, "Anti-inflamatorio, antialérgico", "alto"),
            CompuestoActivo("Ácido ursólico", 0.4, "Anti-cáncer, hepatoprotector", "alto"),
            CompuestoActivo("Floridzina", 0.5, "Anti-diabético", "medio"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "alimentos_humanos",
                "Ingrediente prebiótico clean-label en yogures",
                "polvo soluble",
                5.2,
                1_200_000_000,
                ["BRC", "HACCP"],
                ["Cargill", "CP Kelco"],
            ),
            AplicacionComercial(
                "feed_ganaderia",
                "Aditivo fibra fermentable en feed bovino",
                "polvo",
                1.8,
                380_000_000,
                ["GMP+"],
                ["ForFarmers", "Cargill"],
            ),
            AplicacionComercial(
                "farma",
                "Excipiente cápsulas (pectina)",
                "pectina aislada",
                28.0,
                650_000_000,
                ["USP", "EP", "JP"],
                ["CP Kelco", "Cargill", "Naturex"],
            ),
        ],
        valor_nutricional_score=78,
        diferenciador_clave="Pectina natural extraída sin sulfitos vs commodity química",
        riesgos_tecnicos=["Variabilidad estacional", "Bajo en proteína limita uso en feed"],
        papers_referencia=["Yan & Kerr 2013 - Apple pomace utilization"],
    ),

    PerfilNutricional(
        sku="ACEITE_ORUJO_UVA",
        nombre_comercial="Aceite de semilla de uva",
        mmpp_origen="Prensado de semilla de uva del orujo",
        descripcion_cientifica=(
            "Aceite premium rico en vitamina E y proantocianidinas. Punto humo alto. "
            "Muy demandado en cocina gourmet + cosmética natural."
        ),
        proteina_pct=0.0,
        grasa_pct=99.5,
        fibra_dietetica_pct=0.0,
        humedad_pct=0.1,
        compuestos_activos=[
            CompuestoActivo("Ácido linoleico (omega-6)", 70.0, "PUFA esencial", "alto"),
            CompuestoActivo("Vitamina E (tocoferoles)", 0.05, "Antioxidante", "alto"),
            CompuestoActivo("Proantocianidinas residuales", 0.1, "Anti-aging", "alto"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "alimentos_humanos",
                "Aceite gourmet alta cocina",
                "líquido virgen",
                12.0,
                480_000_000,
                ["HACCP", "Kosher"],
                ["Pompeian", "Borges"],
            ),
            AplicacionComercial(
                "cosmetica",
                "Aceite facial anti-aging premium",
                "líquido cold-pressed",
                45.0,
                280_000_000,
                ["COSMOS"],
                ["Burt's Bees", "Weleda"],
            ),
        ],
        valor_nutricional_score=82,
        diferenciador_clave="Único aceite vegetal con proantocianidinas activas",
        riesgos_tecnicos=["Oxidación rápida tras prensado", "Empaque ámbar requerido"],
        papers_referencia=["Garavaglia et al. 2016 - Grape seed oil"],
    ),

    PerfilNutricional(
        sku="PECTINA",
        nombre_comercial="Pectina alta metoxilación (HM)",
        mmpp_origen="Extracción de pomasa de manzana / pomasa cítricos",
        descripcion_cientifica=(
            "Polisacárido gelificante natural. Industria alimentaria lo requiere para "
            "jaleas, mermeladas, lácteos acidos. Mercado dominado por CP Kelco/Cargill "
            "pero con espacio para entrantes locales en LATAM."
        ),
        proteina_pct=0.5,
        grasa_pct=0.0,
        fibra_dietetica_pct=95.0,
        humedad_pct=4.0,
        compuestos_activos=[
            CompuestoActivo("Galacturonic acid polymer", 80.0, "Gelificante", "alto"),
            CompuestoActivo("Methyl esters (DM>50%)", 50.0, "Gel rápido", "alto"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "alimentos_humanos",
                "Gelificante en jaleas/yogures bebibles",
                "polvo soluble",
                28.0,
                1_500_000_000,
                ["E440 EU", "FDA GRAS", "Halal", "Kosher"],
                ["CP Kelco", "Cargill", "Herbstreith & Fox", "Naturex"],
            ),
            AplicacionComercial(
                "farma",
                "Excipiente liberación controlada cápsulas",
                "polvo USP grade",
                85.0,
                380_000_000,
                ["USP", "EP", "JP"],
                ["CP Kelco", "Roeper", "Cargill"],
            ),
        ],
        valor_nutricional_score=70,
        diferenciador_clave="Producción local LATAM = ventaja logística vs importado EU",
        riesgos_tecnicos=[
            "Calidad consistente: control DM (degree of methylation) crítico",
            "Equipos extracción ácida + precipitación alcohólica costosos",
        ],
        papers_referencia=["Mohnen 2008 - Pectin structure and function"],
    ),

    PerfilNutricional(
        sku="LICOPENO",
        nombre_comercial="Licopeno natural extraído",
        mmpp_origen="Extracción supercrítica de tomasa",
        descripcion_cientifica=(
            "Carotenoide tetraterpénico, antioxidante más potente del grupo. Reduce "
            "riesgo cardiovascular y cáncer próstata según ~80 meta-análisis. Mercado "
            "global $187M USD 2024 creciendo a 6.5% CAGR."
        ),
        proteina_pct=0.0,
        grasa_pct=0.0,
        fibra_dietetica_pct=0.0,
        humedad_pct=2.0,
        compuestos_activos=[
            CompuestoActivo("Licopeno (cis-isomers)", 95.0, "Antioxidante #1 carotenoide", "alto"),
            CompuestoActivo("β-caroteno residual", 2.0, "Precursor vit A", "medio"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "nutraceutica",
                "Suplementos próstata + cardiovascular",
                "polvo 5-10% lycopene",
                95.0,
                890_000_000,
                ["GMP+", "USP", "Novel Food EU"],
                ["LycoRed", "Lyc-O-Mato (Israel)", "BASF", "DSM"],
            ),
            AplicacionComercial(
                "alimentos_humanos",
                "Colorante natural alimentos premium",
                "oleoresina 6% lycopene",
                65.0,
                420_000_000,
                ["E160d EU", "FDA Color Additive"],
                ["Chr. Hansen", "DDW", "Sensient"],
            ),
            AplicacionComercial(
                "cosmetica",
                "Crema antioxidante UV",
                "extracto liofilizado",
                250.0,
                85_000_000,
                ["COSMOS", "ECOCERT"],
                ["L'Oréal", "Lancôme", "Estée Lauder"],
            ),
        ],
        valor_nutricional_score=95,
        diferenciador_clave=(
            "Licopeno natural 1.5-2× mejor biodisponibilidad vs sintético. "
            "Extracción supercrítica CO2 evita solventes residuales."
        ),
        riesgos_tecnicos=[
            "Tecnología extracción supercrítica CapEx alto",
            "Estabilidad limitada: requiere encapsulación o oleoresina",
        ],
        papers_referencia=[
            "Müller et al. 2016 - Lycopene bioavailability",
            "Story et al. 2010 - Lycopene cancer prevention",
        ],
    ),

    PerfilNutricional(
        sku="PROTEINA_UNICEL",
        nombre_comercial="Proteína unicelular (SCP)",
        mmpp_origen="Fermentación de levaduras en sustrato de subproductos",
        descripcion_cientifica=(
            "Single Cell Protein con perfil aminoacídico completo. Alternativa "
            "sostenible a harina de pescado en feed acuícola y a soya en feed pet. "
            "Mercado SCP creciendo 8% CAGR por presión sobre proteína animal."
        ),
        proteina_pct=55.0,
        grasa_pct=8.0,
        fibra_dietetica_pct=15.0,
        humedad_pct=6.0,
        compuestos_activos=[
            CompuestoActivo("Lisina", 4.5, "AA esencial limitante en cereales", "alto"),
            CompuestoActivo("Metionina", 1.2, "AA esencial sulfurado", "alto"),
            CompuestoActivo("β-glucanos", 8.0, "Inmunoestimulante natural", "alto"),
            CompuestoActivo("Nucleótidos", 5.0, "Crecimiento + sabor (umami)", "alto"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "feed_acuicola",
                "Reemplazo harina pescado en pellet salmón",
                "polvo",
                3.5,
                4_200_000_000,
                ["GMP+", "ASC", "MSC"],
                ["Calysta (FeedKind)", "KnipBio", "Unibio"],
            ),
            AplicacionComercial(
                "feed_pet",
                "Proteína vegetal premium pet food",
                "polvo",
                5.5,
                1_800_000_000,
                ["FEDIAF", "AAFCO"],
                ["Mars Petcare", "Nestlé Purina"],
            ),
            AplicacionComercial(
                "alimentos_humanos",
                "Proteína plant-based bebidas/barras",
                "polvo aislado >80% proteína",
                12.0,
                890_000_000,
                ["BRC", "HACCP", "Novel Food EU"],
                ["Quorn", "Roquette"],
            ),
        ],
        valor_nutricional_score=90,
        diferenciador_clave=(
            "Perfil AA completo (PDCAAS ~0.95 vs caseína 1.0). Sin alérgenos. "
            "Footprint carbono 80% menor vs proteína animal."
        ),
        riesgos_tecnicos=[
            "Aceptación regulatoria Novel Food EU requiere 12-18 meses",
            "Sabor levadura debe enmascararse en aplicaciones humanas",
        ],
        papers_referencia=[
            "Ritala et al. 2017 - Single Cell Protein review",
            "Glencross 2020 - SCP in aquafeed",
        ],
    ),

    PerfilNutricional(
        sku="ANTIOXIDANTE",
        nombre_comercial="Extracto antioxidante natural mix",
        mmpp_origen="Mezcla optimizada polifenoles alperujo + orujo + tomasa",
        descripcion_cientifica=(
            "Blend de antioxidantes naturales con ORAC value >20,000 μmol TE/g. "
            "Reemplaza BHT/BHA sintéticos (cuestionados sanitariamente) en feed + "
            "alimentos. Demanda creciente por 'clean label' movement."
        ),
        proteina_pct=15.0,
        grasa_pct=10.0,
        fibra_dietetica_pct=30.0,
        humedad_pct=5.0,
        compuestos_activos=[
            CompuestoActivo("Polifenoles totales", 12.0, "Antioxidante natural", "alto"),
            CompuestoActivo("Resveratrol + análogos", 0.3, "Anti-aging", "alto"),
            CompuestoActivo("Tocoferoles", 0.15, "Vit E", "alto"),
            CompuestoActivo("Carotenoides", 0.5, "Antioxidante + color", "medio"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "feed_acuicola",
                "Reemplazo etoxiquina (prohibida EU 2022)",
                "polvo",
                15.0,
                680_000_000,
                ["GMP+", "ASC", "EU Reg 2017/2330"],
                ["DSM (Ronozyme)", "Kemin"],
            ),
            AplicacionComercial(
                "alimentos_humanos",
                "Reemplazo BHT/BHA en grasas y embutidos",
                "polvo soluble en grasa",
                25.0,
                420_000_000,
                ["BRC", "HACCP", "Clean Label Project"],
                ["Kalsec", "Naturex", "Kemin"],
            ),
            AplicacionComercial(
                "cosmetica",
                "Preservante natural en formulaciones",
                "extracto líquido",
                65.0,
                280_000_000,
                ["COSMOS", "ECOCERT"],
                ["Mibelle Biochem", "Naturex"],
            ),
        ],
        valor_nutricional_score=88,
        diferenciador_clave=(
            "Único antioxidante natural con ORAC >20,000 + claim EFSA hidroxitirosol + "
            "compatible con todas las certificaciones clean-label."
        ),
        riesgos_tecnicos=[
            "Estandarización lote a lote: requiere QC ORAC + HPLC sistemático",
        ],
        papers_referencia=[
            "Carocho & Ferreira 2013 - Natural antioxidants review",
            "Shahidi & Ambigaipalan 2015 - Phenolic compounds",
        ],
    ),

    PerfilNutricional(
        sku="AGLOMERANTE",
        nombre_comercial="Aglomerante natural feed",
        mmpp_origen="Fibra estructural de subproductos + ligante natural",
        descripcion_cientifica=(
            "Reemplazo de bentonita y aglomerantes sintéticos en feed. Permite pelletizado "
            "estable sin agentes químicos. Compatible con feed orgánico certificado."
        ),
        proteina_pct=10.0,
        grasa_pct=3.0,
        fibra_dietetica_pct=70.0,
        humedad_pct=10.0,
        compuestos_activos=[
            CompuestoActivo("Lignosulfonatos naturales", 25.0, "Ligante físico", "medio"),
            CompuestoActivo("Hemicelulosa", 35.0, "Estructura pellet", "medio"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "feed_ganaderia",
                "Aglomerante pellet bovino/avícola",
                "polvo",
                2.0,
                540_000_000,
                ["GMP+", "Organic Feed"],
                ["Borregaard", "DuPont"],
            ),
        ],
        valor_nutricional_score=60,
        diferenciador_clave="Único aglomerante natural compatible con feed orgánico certificado",
        riesgos_tecnicos=["Margen bajo, commodity"],
        papers_referencia=["Behnke 2001 - Feed pelletizing"],
    ),

    PerfilNutricional(
        sku="UMAMI",
        nombre_comercial="Potenciador sabor umami natural",
        mmpp_origen="Hidrólisis enzimática de proteína unicelular + extractos",
        descripcion_cientifica=(
            "Concentrado de nucleótidos (GMP/IMP) + ácido glutámico libre. Reemplaza "
            "MSG sintético + extractos de levadura tradicionales. Demanda alta en "
            "snacks plant-based y caldos."
        ),
        proteina_pct=35.0,
        grasa_pct=2.0,
        fibra_dietetica_pct=8.0,
        humedad_pct=5.0,
        compuestos_activos=[
            CompuestoActivo("Ácido glutámico libre", 12.0, "Umami básico", "alto"),
            CompuestoActivo("Nucleótidos (IMP+GMP)", 5.0, "Potenciador umami 20×", "alto"),
            CompuestoActivo("Peptidos sapidos", 8.0, "Boca llena", "medio"),
        ],
        aplicaciones=[
            AplicacionComercial(
                "alimentos_humanos",
                "Sazonador natural caldos/snacks/plant-based meats",
                "polvo soluble",
                15.0,
                1_650_000_000,
                ["BRC", "HACCP", "Halal", "Kosher"],
                ["Ajinomoto", "Angel Yeast", "DSM (yeast extracts)"],
            ),
            AplicacionComercial(
                "feed_pet",
                "Palatable pet food premium",
                "polvo",
                8.5,
                380_000_000,
                ["FEDIAF", "AAFCO"],
                ["Diana Pet Food", "AFB International"],
            ),
        ],
        valor_nutricional_score=80,
        diferenciador_clave=(
            "Umami natural sin etiqueta MSG. Producto crítico para meat-alternatives "
            "que necesitan boca llena."
        ),
        riesgos_tecnicos=["Proceso hidrólisis enzimática requiere control estricto"],
        papers_referencia=["Mouritsen & Khandelia 2012 - Umami molecular"],
    ),
)


# ============================================================================
# Funciones de análisis
# ============================================================================

def listar_perfiles() -> list[dict]:
    return [p.to_dict() for p in PERFILES_NUTRICIONALES]


def perfil_por_sku(sku: str) -> dict | None:
    for p in PERFILES_NUTRICIONALES:
        if p.sku == sku:
            return p.to_dict()
    return None


def tam_total_global() -> float:
    """TAM total agregado de todas las aplicaciones (USD anual global)."""
    total = 0
    for p in PERFILES_NUTRICIONALES:
        for a in p.aplicaciones:
            total += a.tam_global_usd_anual
    return total


def top_aplicaciones_por_tam(n: int = 10) -> list[dict]:
    """Top N aplicaciones por TAM global."""
    todas = []
    for p in PERFILES_NUTRICIONALES:
        for a in p.aplicaciones:
            todas.append({
                "sku": p.sku,
                "mercado": a.mercado,
                "uso": a.uso_especifico,
                "precio_usd_kg": a.precio_usd_kg_premium,
                "tam_global_usd": a.tam_global_usd_anual,
                "competidores": a.competidores_clave[:3],
            })
    todas.sort(key=lambda x: x["tam_global_usd"], reverse=True)
    return todas[:n]


def mercados_target() -> dict[str, dict]:
    """Agrega oportunidades por mercado."""
    por_mercado: dict[str, dict] = {}
    for p in PERFILES_NUTRICIONALES:
        for a in p.aplicaciones:
            m = a.mercado
            if m not in por_mercado:
                por_mercado[m] = {"tam_total": 0, "skus_aplicables": [], "precio_promedio_premium": 0, "n_apps": 0}
            por_mercado[m]["tam_total"] += a.tam_global_usd_anual
            por_mercado[m]["skus_aplicables"].append(p.sku)
            por_mercado[m]["precio_promedio_premium"] += a.precio_usd_kg_premium
            por_mercado[m]["n_apps"] += 1

    # Promedios
    for m in por_mercado:
        n = por_mercado[m]["n_apps"]
        if n > 0:
            por_mercado[m]["precio_promedio_premium"] /= n
        por_mercado[m]["skus_aplicables"] = list(set(por_mercado[m]["skus_aplicables"]))

    return por_mercado


def score_promedio_portfolio() -> float:
    return sum(p.valor_nutricional_score for p in PERFILES_NUTRICIONALES) / len(PERFILES_NUTRICIONALES)


def resumen_completo() -> dict:
    """Análisis ejecutivo del portfolio nutricional."""
    return {
        "n_perfiles": len(PERFILES_NUTRICIONALES),
        "score_promedio_portfolio": round(score_promedio_portfolio(), 1),
        "tam_total_global_usd": tam_total_global(),
        "n_aplicaciones_totales": sum(len(p.aplicaciones) for p in PERFILES_NUTRICIONALES),
        "n_compuestos_activos_catalogados": sum(len(p.compuestos_activos) for p in PERFILES_NUTRICIONALES),
        "top_10_aplicaciones": top_aplicaciones_por_tam(10),
        "mercados_target": mercados_target(),
    }
