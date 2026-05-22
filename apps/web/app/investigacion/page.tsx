'use client';

import { useState } from 'react';

type Paper = {
  titulo: string;
  hallazgo: string;
  url: string;
  ano?: number;
};

type Categoria = {
  mmpp: string;
  titulo: string;
  descripcion: string;
  papers: Paper[];
  yieldModelo?: { variable: string; valor: string; nota: string };
};

const CATEGORIAS: Categoria[] = [
  {
    mmpp: 'ALPERUJO',
    titulo: 'Alperujo (subproducto olivar)',
    descripcion: 'PEF Opticept aumenta polifenoles +91,6% vs sin pretratamiento. Rico en oleocanthal, oleuropeína, hidroxitirosol.',
    yieldModelo: { variable: 'rendimiento', valor: '0,39 sólidos/input', nota: 'Consistente con literatura (humedad inicial 65%, MS 35%).' },
    papers: [
      {
        titulo: 'Polyphenol Extraction from Food (by) Products by PEF: A Review',
        hallazgo: 'PEF a 3 kV/cm aumenta concentración polifenoles +91,6% vs sin PEF.',
        url: 'https://www.mdpi.com/1422-0067/24/21/15914',
        ano: 2023,
      },
      {
        titulo: 'Effect of PEF and high pressure on recovery from olive pomace',
        hallazgo: 'PEF (1-6,5 kV/cm, 0,9-51 kJ/kg) + extracción solvente 50% etanol 25°C 1h.',
        url: 'https://pubmed.ncbi.nlm.nih.gov/32267966/',
        ano: 2020,
      },
      {
        titulo: 'PEF Continuous System in Industrial Olive Oil Plant',
        hallazgo: 'PEF pre-tratamiento sube recuperación fenoles 9,8 → 18,6 g GAE/kg.',
        url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC9497696/',
        ano: 2022,
      },
      {
        titulo: 'Impact of PEF on Olive Oil Yield and Quality',
        hallazgo: 'Yield aceite mejora con PEF en planta industrial continua.',
        url: 'https://www.intechopen.com/chapters/87948',
        ano: 2023,
      },
    ],
  },
  {
    mmpp: 'TOMASA',
    titulo: 'Tomasa (subproducto tomate)',
    descripcion: 'Pomace = 25% del tomate procesado (40% pulpa + 27% cáscara con licopeno + 33% semillas). Mercado licopeno USD 171M global 2026.',
    yieldModelo: { variable: 'licopeno_pct', valor: '0,1% del input', nota: 'Conservador vs 6,11 mg/g literatura.' },
    papers: [
      {
        titulo: 'Standardization of Solvent Extraction for Lycopene from Tomato Pomace',
        hallazgo: 'Yield 6,11 mg/g pomace con acetona-etil acetato 1:1 a 40°C, 5h.',
        url: 'https://medcraveonline.com/JABB/standardization-of-solvent-extraction-process-for-lycopene-extraction-from-tomato-pomace.html',
      },
      {
        titulo: 'Valorization of Tomato By-Products (MDPI 2025)',
        hallazgo: 'Ultrasonido 5,11 mg/g DW; DES 1.446 µg/g DW; SC-CO₂ 1.017 mg/100g extracto.',
        url: 'https://www.mdpi.com/2076-3417/15/7/3914',
        ano: 2025,
      },
      {
        titulo: 'Techno-Economic Analysis of Lycopene via Pervaporation',
        hallazgo: 'Pervaporación competitiva económicamente vs solvente convencional.',
        url: 'https://pubs.acs.org/doi/10.1021/acs.iecr.4c00125',
        ano: 2024,
      },
      {
        titulo: 'Sustainable LCA of Lycopene Extraction Methods',
        hallazgo: 'Análisis ciclo de vida comparando métodos de extracción.',
        url: 'https://pubs.rsc.org/en/content/articlehtml/2026/fb/d5fb00899a',
        ano: 2026,
      },
    ],
  },
  {
    mmpp: 'ORUJO_UVA',
    titulo: 'Orujo de uva (subproducto vinificación)',
    descripcion: 'Pomace = 20-25% del peso de uva. Fenoles 5-35 mg GAE/g DW (piel/semilla). Fermentación con levadura enriquece perfil polifenólico.',
    yieldModelo: { variable: 'rendimiento', valor: '0,18 sólidos/input', nota: 'Conservador, literatura sugiere 0,2-0,25.' },
    papers: [
      {
        titulo: 'Valorization of Grape Pomace via Microbial Fermentation',
        hallazgo: 'Hongos filamentosos, levaduras, LAB enriquecen perfil polifenólico.',
        url: 'https://www.sciencedirect.com/science/article/pii/S0889157525004715',
        ano: 2025,
      },
      {
        titulo: 'Fatty Acid and Antioxidant Profile of Grape Pomace',
        hallazgo: 'Fenoles 5-35 mg GAE/g DW según piel/semilla. Pérdida humedad 83% freeze-drying.',
        url: 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12348267/',
        ano: 2025,
      },
      {
        titulo: 'Transforming Winemaking Waste — IVES 2025',
        hallazgo: 'GP como fuente sostenible de bioactivos para nutracéutica.',
        url: 'https://ives-openscience.eu/53139/',
        ano: 2025,
      },
    ],
  },
  {
    mmpp: 'LEVADURA',
    titulo: 'Levadura → Proteína Unicelular (SCP)',
    descripcion: 'Mercado SCP global USD 13,12B en 2026 → USD 20,94B en 2031. Salmoneras chilenas pueden sustituir 10-20% del fishmeal sin perder performance.',
    yieldModelo: { variable: 'rendimiento', valor: '0,30 sólidos/input', nota: 'Aplicable en biorreactor con levadura cervecera reciclada.' },
    papers: [
      {
        titulo: 'Torula yeast in rainbow trout (Ekmay 2024)',
        hallazgo: '10-20% inclusión, digestibilidad proteína 93,8% (vs fishmeal). Plant-based + yeast > fishmeal.',
        url: 'https://onlinelibrary.wiley.com/doi/10.1111/jwas.13047',
        ano: 2024,
      },
      {
        titulo: 'Bridging Protein Gap with SCP (Frontiers 2024)',
        hallazgo: '20% inclusión 12 sem, growth + health OK. Perfil aminoácidos balanceado.',
        url: 'https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2024.1384083/full',
        ano: 2024,
      },
      {
        titulo: 'Atlantic salmon smolts fed torula yeast',
        hallazgo: 'Tres niveles SCP comparables a fishmeal en growth performance.',
        url: 'https://onlinelibrary.wiley.com/doi/full/10.1002/aff2.70088',
        ano: 2025,
      },
      {
        titulo: 'DSM-Firmenich on SCP feed protein gap',
        hallazgo: 'Strategic alternative al fishmeal con menor footprint ambiental.',
        url: 'https://www.dsm-firmenich.com/anh/news/feed-talks/articles/bridging-the-feed-protein-gap-in-aquaculture-with-single-cell-protein.html',
      },
    ],
  },
  {
    mmpp: 'POMASA',
    titulo: 'Pomasa (manzana/pera)',
    descripcion: 'Apple pomace = 2da fuente mundial de pectina comercial (después de cítricos). Yield enzimático 6,76% con Celluclast 1.5L.',
    yieldModelo: { variable: 'pectina_pct', valor: '0,3% del input (commercial)', nota: 'Conservador vs 6,76% literatura (yield laboratorio).' },
    papers: [
      {
        titulo: 'Optimization Enzymatic Pectin Extraction (PMC 6600438)',
        hallazgo: 'Yield 6,76% con 48,3°C, 18h, 42,5 µL/g pomace. Galacturónico 97,46%.',
        url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC6600438/',
      },
      {
        titulo: 'Ohmic Heating Extraction of Apple Pectin',
        hallazgo: 'OHE reduce energía + mejora yield vs convencional.',
        url: 'https://www.sciencedirect.com/science/article/abs/pii/S0960308525000550',
        ano: 2025,
      },
      {
        titulo: 'Radio Frequency Assisted Pectin Extraction',
        hallazgo: 'RF + microondas competitivos vs convencional para industrial.',
        url: 'https://www.sciencedirect.com/science/article/abs/pii/S0268005X21004471',
        ano: 2021,
      },
    ],
  },
];

export default function InvestigacionPage() {
  const [activeMmpp, setActiveMmpp] = useState(CATEGORIAS[0].mmpp);
  const active = CATEGORIAS.find((c) => c.mmpp === activeMmpp)!;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Literatura científica</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Papers peer-reviewed con DOI trazable que sustentan los rendimientos y procesos asumidos por el modelo
          financiero. Refresh trimestral via agente <code className="font-mono text-trigo">trongkai-data-hunter</code>.
        </p>
      </header>

      <nav className="flex flex-wrap gap-2">
        {CATEGORIAS.map((c) => (
          <button
            key={c.mmpp}
            onClick={() => setActiveMmpp(c.mmpp)}
            className={`rounded border px-3 py-1.5 text-sm transition ${
              activeMmpp === c.mmpp
                ? 'border-oliva-900 bg-oliva-900 text-crema'
                : 'border-oliva/20 bg-white text-oliva-700 hover:border-oliva-900'
            }`}
          >
            {c.mmpp}
          </button>
        ))}
      </nav>

      <section className="rounded-lg border border-oliva/10 bg-white p-5 shadow-sm">
        <h2 className="font-serif text-2xl text-oliva-900">{active.titulo}</h2>
        <p className="mt-2 text-sm text-oliva-700">{active.descripcion}</p>

        {active.yieldModelo && (
          <div className="mt-4 rounded border-l-4 border-trigo bg-trigo/5 p-3">
            <div className="text-[10px] uppercase tracking-[0.08em] text-trigo">Aplicación al modelo Trongkai</div>
            <div className="mt-1 text-sm">
              <strong>{active.yieldModelo.variable}</strong>: <span className="tabular">{active.yieldModelo.valor}</span>
            </div>
            <div className="text-xs text-oliva-600">{active.yieldModelo.nota}</div>
          </div>
        )}

        <div className="mt-5 space-y-3">
          <h3 className="text-xs uppercase tracking-[0.08em] text-oliva-600">
            Papers ({active.papers.length})
          </h3>
          {active.papers.map((p, i) => (
            <article key={i} className="card-hover rounded border border-oliva/10 bg-white p-3">
              <a
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block font-medium text-oliva-900 hover:text-trigo"
              >
                {p.titulo} {p.ano && <span className="text-xs text-oliva-500">({p.ano})</span>}
              </a>
              <p className="mt-1 text-sm text-oliva-700">{p.hallazgo}</p>
              <a
                href={p.url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-1 inline-block text-xs text-trigo hover:underline"
              >
                {p.url}
              </a>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
        <strong>Reglas de citación del modelo:</strong>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-oliva-700">
          <li>Todo precio o rendimiento en SKU_CATALOGO debe tener al menos una fuente trazable.</li>
          <li>Si una fila tiene fuente "estimación", no puede promoverse a OK_VALIDADO.</li>
          <li>El agente trongkai-data-hunter re-verifica papers cada 90 días via WebSearch.</li>
        </ol>
      </section>
    </div>
  );
}
