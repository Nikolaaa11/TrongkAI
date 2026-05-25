'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Recurso = {
  titulo: string;
  desc: string;
  url: string;
  tipo: 'PDF' | 'Excel' | 'HTML' | 'JSON' | 'Plataforma';
  tamano?: string;
  destacado?: boolean;
};

const RECURSOS: Recurso[] = [
  {
    titulo: '📄 Tearsheet Ejecutivo (PDF)',
    desc: 'PDF 4 páginas: KPIs, valoración, Monte Carlo, escenarios, readiness score 10 dim, data room, matriz canónica, carbono, compliance, macro Chile.',
    url: `${ENGINE_URL}/api/tearsheet.pdf`,
    tipo: 'PDF',
    tamano: '~100 KB',
    destacado: true,
  },
  {
    titulo: '🏠 Plataforma Web Completa',
    desc: 'Acceso navegable a las 22 secciones: directorio, sensitivity, financiamiento, carbono, compliance, etc.',
    url: 'https://trongkai-web.vercel.app/',
    tipo: 'Plataforma',
    destacado: true,
  },
  {
    titulo: '📊 Snapshot completo (JSON)',
    desc: 'Estado del modelo en formato máquina-legible: KPIs, plan, valuation, escenarios, MC, carbono, compliance, macro, readiness, data room, matriz.',
    url: `${ENGINE_URL}/api/snapshot`,
    tipo: 'JSON',
  },
  {
    titulo: '💯 Investment Readiness Score',
    desc: 'Score 0-100 con 10 dimensiones desglosadas. Refleja madurez para LP roadshow.',
    url: `${ENGINE_URL}/readiness/score?n_sims_mc=500`,
    tipo: 'JSON',
  },
  {
    titulo: '📋 Data Room Checklist DD',
    desc: '41 items DD agrupados en 6 categorías (corporativo, financiero, comercial, operacional, ESG, equipo).',
    url: `${ENGINE_URL}/data-room/checklist`,
    tipo: 'JSON',
  },
  {
    titulo: '📑 Matriz Variables (Excel original)',
    desc: '11 productos × 15 variables = 165 celdas con estado PD/OK_PROVISORIO/OK_VALIDADO.',
    url: `${ENGINE_URL}/variables/matrix`,
    tipo: 'JSON',
  },
  {
    titulo: '🌡️ Sensibilidad heatmap 2D',
    desc: '49 simulaciones cross-variable (precio × costo MMPP) con zonas seguras.',
    url: 'https://trongkai-web.vercel.app/sensitivity',
    tipo: 'Plataforma',
  },
  {
    titulo: '🌱 Carbon Footprint LCA',
    desc: 'Análisis ciclo de vida 3 escenarios (baseline / renewable / BECCS) con revenue créditos CO₂.',
    url: 'https://trongkai-web.vercel.app/carbono',
    tipo: 'Plataforma',
  },
  {
    titulo: '📚 API Documentation (Swagger)',
    desc: 'OpenAPI/Swagger UI con los 30+ endpoints documentados.',
    url: `${ENGINE_URL}/docs`,
    tipo: 'Plataforma',
  },
];

const RESOURCES_LOCAL = [
  {
    titulo: '📦 Excel Master (10 hojas)',
    desc: 'Dashboard, Plan 5 años, Sensibilidad, Escenarios, Carbono, Compliance, Macro, Supuestos.',
    path: 'entregables/02-excel-master/Trongkai-Master-*.xlsx',
    tipo: 'Excel',
  },
  {
    titulo: '📦 Excel con macros VBA',
    desc: 'Excel + módulo VBA TrongkaiAPI.bas con 6 macros para refrescar desde el motor live.',
    path: 'entregables/02-excel-master/Trongkai-Master-VBA-*.xlsm',
    tipo: 'Excel',
  },
  {
    titulo: '🌐 Presentación HTML Líderes',
    desc: 'One-pager Apple-style para directorio / LPs. Standalone, abre con doble-click.',
    path: 'entregables/01-presentaciones/Presentacion-Lideres.html',
    tipo: 'HTML',
  },
];

export default function LPPackPage() {
  const [scoreLive, setScoreLive] = useState<number | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/readiness/score?n_sims_mc=200`)
      .then((r) => r.json())
      .then((d) => setScoreLive(d.score_total))
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-12">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">LP Pack — Centro de descargas</h1>
          <p className="mt-2 text-sm text-ink-400">
            Todos los recursos para LP roadshow / comité de inversión / due diligence en un solo lugar.
            Los enlaces son live: cada visita trae el dato actualizado del motor.
          </p>
        </div>
      </header>

      {/* Hero: Score live */}
      <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
        <div className="flex flex-col items-center gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
              Investment Readiness Score actual
            </div>
            <div className="mt-2 flex items-baseline gap-3">
              <div className="tabular text-6xl font-semibold text-ink">
                {scoreLive !== null ? scoreLive.toFixed(1) : '...'}
              </div>
              <div className="text-2xl text-ink-400">/ 100</div>
            </div>
            <div className="mt-1 text-sm text-ink-600">10 dimensiones evaluadas en vivo</div>
          </div>
          <a
            href={`${ENGINE_URL}/api/tearsheet.pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full bg-brand px-5 py-3 text-sm font-medium text-white transition hover:scale-105"
          >
            📄 Descargar PDF tearsheet
          </a>
        </div>
      </section>

      {/* Recursos online (live) */}
      <section>
        <h2 className="mb-2 text-2xl font-semibold tracking-apple text-ink">Recursos en vivo (motor)</h2>
        <p className="mb-6 text-sm text-ink-400">
          Datos recalculados al momento. Comparte el link y el LP siempre ve la versión más fresca.
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {RECURSOS.map((r) => (
            <RecursoCard key={r.url} r={r} />
          ))}
        </div>
      </section>

      {/* Archivos locales */}
      <section>
        <h2 className="mb-2 text-2xl font-semibold tracking-apple text-ink">Archivos en carpeta `entregables/`</h2>
        <p className="mb-6 text-sm text-ink-400">
          Generados localmente. Para mandar por mail, WhatsApp o subir a Drive.
        </p>
        <div className="space-y-3">
          {RESOURCES_LOCAL.map((r) => (
            <div key={r.path} className="apple-card">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-ink">{r.titulo}</h3>
                    <span className="rounded-full bg-ink-50 px-2 py-0.5 text-[10px] font-medium text-ink-600">{r.tipo}</span>
                  </div>
                  <p className="mt-1 text-sm text-ink-600">{r.desc}</p>
                </div>
              </div>
              <div className="mt-3 rounded-lg bg-ink-50 px-3 py-2">
                <code className="text-[11px] text-ink-600">{r.path}</code>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="rounded-appleXl bg-ink-50 p-8">
        <h2 className="text-2xl font-semibold tracking-apple text-ink">¿Cómo armar el pack para un LP específico?</h2>
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <FlujoCard
            num="1"
            titulo="Descarga PDF tearsheet"
            desc="Click en 'Descargar PDF tearsheet' arriba. Adjúntalo al mail."
          />
          <FlujoCard
            num="2"
            titulo="Manda link a plataforma"
            desc="https://trongkai-web.vercel.app/ — el LP puede explorar interactivamente."
          />
          <FlujoCard
            num="3"
            titulo="Si pide Excel: dale el Master"
            desc="entregables/02-excel-master/ — 10 hojas con datos vivos."
          />
        </div>
      </section>

      {/* Quick links */}
      <section className="apple-card">
        <h2 className="text-xl font-semibold text-ink">Enlaces rápidos para copiar</h2>
        <div className="mt-4 space-y-2 text-sm">
          <CopyLine label="Plataforma" url="https://trongkai-web.vercel.app/" />
          <CopyLine label="PDF tearsheet" url={`${ENGINE_URL}/api/tearsheet.pdf`} />
          <CopyLine label="Dashboard directorio" url="https://trongkai-web.vercel.app/dashboard-directorio" />
          <CopyLine label="Readiness Score" url="https://trongkai-web.vercel.app/readiness" />
          <CopyLine label="Data Room DD" url="https://trongkai-web.vercel.app/data-room" />
          <CopyLine label="API Docs (Swagger)" url={`${ENGINE_URL}/docs`} />
        </div>
      </section>
    </div>
  );
}

function RecursoCard({ r }: { r: Recurso }) {
  return (
    <a
      href={r.url}
      target="_blank"
      rel="noopener noreferrer"
      className={`apple-card block ${r.destacado ? 'bg-brand-50 ring-1 ring-brand/20' : ''}`}
    >
      <div className="flex items-center gap-2">
        <h3 className="font-semibold text-ink">{r.titulo}</h3>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
          r.tipo === 'PDF' ? 'bg-red-50 text-red-600' :
          r.tipo === 'Excel' ? 'bg-brand-50 text-brand' :
          r.tipo === 'HTML' ? 'bg-yellow-50 text-yellow-700' :
          r.tipo === 'Plataforma' ? 'bg-ink-50 text-ink-600' :
          'bg-ink-50 text-ink-600'
        }`}>{r.tipo}</span>
        {r.tamano && <span className="text-[11px] text-ink-400">{r.tamano}</span>}
      </div>
      <p className="mt-1 text-sm text-ink-600">{r.desc}</p>
      <div className="mt-2 text-[11px] text-brand">Abrir →</div>
    </a>
  );
}

function CopyLine({ label, url }: { label: string; url: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg bg-ink-50 px-3 py-2">
      <div className="flex flex-1 items-center gap-3 overflow-hidden">
        <span className="shrink-0 text-xs font-medium text-ink-400">{label}:</span>
        <code className="truncate text-[11px] text-ink-600">{url}</code>
      </div>
      <button
        onClick={() => navigator.clipboard.writeText(url)}
        className="shrink-0 rounded-full bg-white px-3 py-1 text-[11px] font-medium text-ink-600 ring-1 ring-ink-100 transition hover:bg-brand hover:text-white"
      >
        Copiar
      </button>
    </div>
  );
}

function FlujoCard({ num, titulo, desc }: { num: string; titulo: string; desc: string }) {
  return (
    <div className="apple-card">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">{num}</div>
      <h3 className="mt-3 font-semibold text-ink">{titulo}</h3>
      <p className="mt-1 text-xs text-ink-600">{desc}</p>
    </div>
  );
}
