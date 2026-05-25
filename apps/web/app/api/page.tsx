'use client';

import { useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type EndpointSpec = {
  id: string;
  method: 'GET' | 'POST';
  path: string;
  titulo: string;
  descripcion: string;
  body?: object;
  tag: 'Plan' | 'Risk' | 'Macro' | 'Sustainability' | 'Compliance' | 'Export';
};

const ENDPOINTS: EndpointSpec[] = [
  {
    id: 'snapshot',
    method: 'GET',
    path: '/api/snapshot',
    titulo: 'Snapshot completo',
    descripcion: 'Devuelve TODO el estado del modelo en una sola request: KPIs, valoración, Monte Carlo, carbono, compliance, macro.',
    tag: 'Plan',
  },
  {
    id: 'plan',
    method: 'POST',
    path: '/plan',
    titulo: 'Plan 5 años base',
    descripcion: 'EERR mensual a 60 meses + KPIs (TIR, VAN, payback, EBITDA margin) + ingresos por marca.',
    body: {},
    tag: 'Plan',
  },
  {
    id: 'monte-carlo',
    method: 'POST',
    path: '/montecarlo',
    titulo: 'Monte Carlo TIR',
    descripcion: '10k simulaciones con distribuciones realistas. Devuelve P5, P25, P50, P75, P95 + probabilidad de superar hurdle.',
    body: { n_sims: 1000, incluir_clima: true },
    tag: 'Risk',
  },
  {
    id: 'sensitivity-heatmap',
    method: 'POST',
    path: '/sensitivity/heatmap',
    titulo: 'Sensitivity heatmap 2D',
    descripcion: 'Mapa de calor TIR para combinaciones cross-variable. Default 7x7 = 49 simulaciones.',
    body: { driver_x: 'precio', driver_y: 'costo_mmpp', n: 5, hurdle_pct: 0.15 },
    tag: 'Risk',
  },
  {
    id: 'sensitivity-curves',
    method: 'GET',
    path: '/sensitivity/curves?n=11',
    titulo: 'Sensitivity curvas 1D',
    descripcion: 'TIR vs shock para los 4 drivers (precio, costo MMPP, WACC, OpEx). Small multiples.',
    tag: 'Risk',
  },
  {
    id: 'breakeven',
    method: 'GET',
    path: '/sensitivity/breakeven?umbral_tir=0.15',
    titulo: 'Break-even por driver',
    descripcion: 'Encuentra el shock máximo soportable por cada driver antes de bajar del hurdle.',
    tag: 'Risk',
  },
  {
    id: 'macro-chile',
    method: 'GET',
    path: '/macro/chile',
    titulo: 'Macro Chile en vivo',
    descripcion: 'USD/CLP, UF, IPC, TPM, desempleo desde Banco Central (mindicador.cl). Cache 24h.',
    tag: 'Macro',
  },
  {
    id: 'carbon-footprint',
    method: 'GET',
    path: '/carbon/footprint',
    titulo: 'Footprint carbono LCA',
    descripcion: 'Análisis ciclo de vida 3 escenarios: baseline / renewable / BECCS. Incluye revenue créditos CO2.',
    tag: 'Sustainability',
  },
  {
    id: 'compliance-rep',
    method: 'GET',
    path: '/compliance/rep',
    titulo: 'Ley REP timeline',
    descripcion: '8 hitos regulatorios Ley REP para agroindustria con alertas y costos.',
    tag: 'Compliance',
  },
  {
    id: 'tearsheet-pdf',
    method: 'GET',
    path: '/api/tearsheet.pdf',
    titulo: 'PDF tearsheet ejecutivo',
    descripcion: '3 páginas en PDF con todo el modelo. Listo para LP roadshow.',
    tag: 'Export',
  },
];

const TAG_COLOR: Record<EndpointSpec['tag'], string> = {
  Plan: 'bg-oliva-100 text-oliva-900 border-oliva-700/30',
  Risk: 'bg-borgoña/10 text-borgoña border-borgoña/30',
  Macro: 'bg-trigo/20 text-tierra border-trigo/40',
  Sustainability: 'bg-oliva-50 text-oliva-700 border-oliva-700/20',
  Compliance: 'bg-trigo/10 text-oliva-900 border-trigo/30',
  Export: 'bg-papel text-oliva-900 border-oliva/30',
};

export default function ApiExplorerPage() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">API Explorer</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Los {ENDPOINTS.length} endpoints públicos del motor TrongkAI. Pruebalos en vivo, copia el comando curl,
          o consúmelos desde el SDK Python / TypeScript. Engine base:{' '}
          <code className="rounded bg-papel px-1 text-xs text-oliva-900">{ENGINE_URL}</code>
        </p>
      </header>

      <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
        <strong>SDK disponibles:</strong>
        <ul className="mt-2 list-disc space-y-0.5 pl-5">
          <li>
            <strong>Python:</strong>{' '}
            <code className="rounded bg-papel px-1 text-xs">from trongkai_sdk import TrongkaiClient</code>
          </li>
          <li>
            <strong>TypeScript:</strong>{' '}
            <code className="rounded bg-papel px-1 text-xs">
              import {`{ TrongkaiClient }`} from &apos;@/lib/trongkai-client&apos;
            </code>
          </li>
          <li>OpenAPI/Swagger interactivo: <a className="text-borgoña underline" href={`${ENGINE_URL}/docs`} target="_blank" rel="noopener noreferrer">{ENGINE_URL}/docs</a></li>
        </ul>
      </section>

      <div className="grid grid-cols-1 gap-4">
        {ENDPOINTS.map((ep) => (
          <EndpointCard key={ep.id} ep={ep} />
        ))}
      </div>
    </div>
  );
}

function EndpointCard({ ep }: { ep: EndpointSpec }) {
  const [loading, setLoading] = useState(false);
  const [output, setOutput] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);

  async function ejecutar() {
    setLoading(true);
    setErr(null);
    setOutput(null);
    const t0 = performance.now();
    try {
      const url = `${ENGINE_URL}${ep.path}`;
      // PDF descarga separada
      if (ep.path.endsWith('.pdf')) {
        window.open(url, '_blank');
        setOutput('(PDF abierto en nueva pestaña)');
        setElapsed(performance.now() - t0);
        return;
      }
      const opts: RequestInit = {
        method: ep.method,
        headers: ep.body ? { 'content-type': 'application/json' } : undefined,
        body: ep.body ? JSON.stringify(ep.body) : undefined,
      };
      const r = await fetch(url, opts);
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
      const data = await r.json();
      // Truncar para no romper la pantalla
      const formatted = JSON.stringify(data, null, 2);
      setOutput(formatted.length > 8000 ? formatted.slice(0, 8000) + '\n... (truncado, ' + formatted.length + ' chars total)' : formatted);
      setElapsed(performance.now() - t0);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  const curl = ep.body
    ? `curl -X POST '${ENGINE_URL}${ep.path}' -H 'content-type: application/json' -d '${JSON.stringify(ep.body)}'`
    : `curl '${ENGINE_URL}${ep.path}'`;

  return (
    <div className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm card-hover">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span
              className={`rounded border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-[0.05em] ${
                ep.method === 'GET'
                  ? 'border-oliva-700/30 bg-oliva-50 text-oliva-900'
                  : 'border-borgoña/30 bg-borgoña/10 text-borgoña'
              }`}
            >
              {ep.method}
            </span>
            <code className="text-sm text-oliva-900">{ep.path}</code>
            <span className={`rounded border px-1.5 py-0.5 text-[10px] uppercase tracking-[0.05em] ${TAG_COLOR[ep.tag]}`}>
              {ep.tag}
            </span>
          </div>
          <h3 className="mt-1 font-medium text-oliva-900">{ep.titulo}</h3>
          <p className="mt-0.5 text-xs text-oliva-700">{ep.descripcion}</p>
        </div>
        <button
          onClick={ejecutar}
          disabled={loading}
          className="shrink-0 rounded bg-borgoña px-3 py-1.5 text-xs text-crema hover:bg-tierra disabled:opacity-50"
        >
          {loading ? 'Ejecutando...' : 'Probar'}
        </button>
      </div>

      <details className="mt-3">
        <summary className="cursor-pointer text-xs text-oliva-600 hover:text-oliva-900">
          Ver comando curl
        </summary>
        <pre className="mt-2 overflow-x-auto rounded bg-papel p-2 text-[10px] text-oliva-900">{curl}</pre>
      </details>

      {(output || err) && (
        <div className="mt-3 border-t border-oliva/10 pt-3">
          {elapsed !== null && (
            <div className="mb-1 text-[10px] text-oliva-600">
              ⏱ {elapsed.toFixed(0)} ms
            </div>
          )}
          {err && <p className="text-sm text-borgoña">{err}</p>}
          {output && (
            <pre className="max-h-96 overflow-auto rounded bg-papel p-3 text-[10px] leading-snug text-oliva-900">
              {output}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
