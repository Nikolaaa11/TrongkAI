'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';
import { NetworkGraph, type GraphData } from '@/components/NetworkGraph';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type GraphResp = GraphData & { stats: { total_nodos: number; total_edges: number; tipos_nodo: string[] } };

const TIPO_LABEL: Record<string, string> = {
  input: 'Inputs (datos del equipo)',
  matriz: 'Matrices base (165 + 41 + 8 items)',
  calculo: 'Cálculos derivados (plan, sensitivity, MC)',
  decision: 'Capa de decisión (cerebro)',
  output: 'Outputs (PDF, ZIP, Excel)',
};

const TIPO_COLOR: Record<string, string> = {
  input: '#86868B',
  matriz: '#1A8A1A',
  calculo: '#FF9500',
  decision: '#FF3B30',
  output: '#3FB23F',
};

export default function RedPage() {
  const [data, setData] = useState<GraphResp | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/graph/modulos`)
      .then((r) => (r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`)))
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Red Inteligente</h1>
          <p className="mt-2 text-sm text-ink-400">
            Mapa de cómo se conectan todos los módulos de la plataforma. Inputs del equipo
            alimentan matrices, las matrices alimentan cálculos, los cálculos alimentan el
            Decision Engine. Click en cualquier nodo para ir a su página.
          </p>
        </div>
      </header>

      {err && <div className="apple-card border border-red-200 bg-red-50/40 text-red-600">{err}</div>}

      {data && (
        <>
          {/* Stats */}
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Módulos" value={data.stats.total_nodos} />
            <StatCard label="Conexiones" value={data.stats.total_edges} />
            <StatCard label="Tipos de nodo" value={data.stats.tipos_nodo.length} />
            <StatCard label="Plataforma" value="100%" tone="ok" sub="Modelo conectado" />
          </section>

          {/* Leyenda */}
          <section className="apple-card">
            <h2 className="font-semibold text-ink">Leyenda</h2>
            <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-5">
              {Object.entries(TIPO_LABEL).map(([tipo, label]) => (
                <div key={tipo} className="flex items-center gap-2">
                  <span
                    className="h-3 w-3 shrink-0 rounded-full"
                    style={{ background: TIPO_COLOR[tipo] }}
                  />
                  <span className="text-xs text-ink-600">{label}</span>
                </div>
              ))}
            </div>
          </section>

          {/* Graph */}
          <section className="apple-card p-2">
            <NetworkGraph data={data} height={620} />
          </section>

          {/* Tips */}
          <section className="rounded-appleXl bg-ink-50 p-8">
            <h2 className="text-2xl font-semibold tracking-apple text-ink">Cómo interpretar la red</h2>
            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
              <FlujoCard
                num="1"
                titulo="Inputs alimentan matrices"
                desc="Datos del equipo (LOI, cotización, OpEx) → Matriz Variables y Data Room."
              />
              <FlujoCard
                num="2"
                titulo="Matrices alimentan cálculos"
                desc="Plan 5y, Sensitivity, Monte Carlo, Carbono — todos parten de la matriz canónica."
              />
              <FlujoCard
                num="3"
                titulo="Decision Engine sintetiza"
                desc="El cerebro toma todo y produce 5 acciones priorizadas. Cierra el ciclo."
              />
            </div>
            <div className="mt-6 rounded-lg bg-white p-4 text-sm text-ink-600">
              <strong className="text-ink">💡 Tip:</strong> Click en un nodo para ir a su página. Drag para reorganizar. Hover muestra descripción + URL.
            </div>
          </section>

          {/* Cascadas */}
          <section className="apple-card">
            <h2 className="text-xl font-semibold text-ink">Cascadas de impacto</h2>
            <p className="mt-1 text-sm text-ink-400">
              Si cambias un dato, qué se afecta. Útil para entender el blast-radius de cada decisión.
            </p>
            <div className="mt-4 space-y-2 text-sm">
              <CascadaRow modulo="Datos del equipo" desc="→ Matriz Variables → Plan 5y → Sensitivity → Readiness → PDF tearsheet" />
              <CascadaRow modulo="Cotización MMPP" desc="→ Costo MMPP → EERR → TIR → Readiness → Decisión" />
              <CascadaRow modulo="LOI cliente firmada" desc="→ Precio Venta → Margen → TIR + Bancabilidad → Score" />
              <CascadaRow modulo="Term sheet bancario" desc="→ Financiamiento → DSCR → Dimensión Bancabilidad → Readiness" />
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, tone, sub }: { label: string; value: string | number; tone?: 'ok'; sub?: string }) {
  const cls = tone === 'ok' ? 'text-brand' : 'text-ink';
  return (
    <div className="apple-card text-center">
      <div className="text-[10px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className={`tabular mt-1 text-3xl font-semibold ${cls}`}>{value}</div>
      {sub && <div className="text-[11px] text-ink-400">{sub}</div>}
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

function CascadaRow({ modulo, desc }: { modulo: string; desc: string }) {
  return (
    <div className="rounded-lg bg-ink-50 p-3">
      <div className="font-semibold text-ink">{modulo}</div>
      <div className="mt-0.5 text-xs text-ink-600">{desc}</div>
    </div>
  );
}
