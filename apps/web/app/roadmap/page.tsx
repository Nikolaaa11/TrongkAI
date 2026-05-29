'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Hito = {
  fecha: string;
  tipo: 'compliance' | 'lp' | 'decision' | 'certificacion' | 'financiero';
  titulo: string;
  descripcion: string;
  owner: string;
  prioridad: 'alta' | 'media' | 'baja';
  monto_estimado_usd: number | null;
  link: string;
};

type RoadmapResp = {
  hoy: string;
  horizonte_meses: number;
  total_hitos: number;
  por_tipo: Record<string, number>;
  por_mes: Record<string, Hito[]>;
  monto_lp_ponderado_total_usd: number;
  hitos: Hito[];
};

const TIPO_COLOR: Record<string, string> = {
  compliance: 'bg-red-50 text-red-600 border-red-200',
  lp: 'bg-brand-50 text-brand border-brand/30',
  decision: 'bg-orange-50 text-orange-600 border-orange-200',
  certificacion: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  financiero: 'bg-ink-50 text-ink-600 border-ink-100',
};

const TIPO_ICON: Record<string, string> = {
  compliance: '📜',
  lp: '💼',
  decision: '🎯',
  certificacion: '🏅',
  financiero: '💰',
};

const TIPO_LABEL: Record<string, string> = {
  compliance: 'Compliance REP',
  lp: 'LP Pipeline',
  decision: 'Decision Engine',
  certificacion: 'Certificación',
  financiero: 'Financiero',
};

const MES_LABELS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

function formatMes(yyyymm: string): string {
  const [y, m] = yyyymm.split('-').map(Number);
  return `${MES_LABELS[m - 1] ?? '?'} ${y}`;
}

export default function RoadmapPage() {
  const [data, setData] = useState<RoadmapResp | null>(null);
  const [filtroTipo, setFiltroTipo] = useState<string>('todos');
  const [meses, setMeses] = useState(12);

  useEffect(() => {
    fetch(`${ENGINE_URL}/roadmap?meses=${meses}`)
      .then((r) => r.ok && r.json())
      .then(setData);
  }, [meses]);

  if (!data) {
    return <div className="apple-card text-ink-400">Cargando roadmap...</div>;
  }

  const mesesOrdenados = Object.keys(data.por_mes).sort();
  const hitosVisibles = filtroTipo === 'todos'
    ? data.hitos
    : data.hitos.filter((h) => h.tipo === filtroTipo);

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
          <div>
            <h1 className="font-serif text-3xl text-ink">🗺 Roadmap Visual</h1>
            <p className="mt-2 text-sm text-ink-400">
              Timeline consolidado de próximos hitos. Compliance REP, LP pipeline, Decision Engine
              y certificaciones esperadas. Todo cronológico.
            </p>
          </div>
        </div>
        <select
          value={meses}
          onChange={(e) => setMeses(Number(e.target.value))}
          className="rounded-lg border border-ink-100 bg-white px-3 py-2 text-sm"
        >
          <option value={3}>3 meses</option>
          <option value={6}>6 meses</option>
          <option value={12}>12 meses</option>
          <option value={24}>24 meses</option>
        </select>
      </header>

      {/* Hero stats */}
      <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Total hitos</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">{data.total_hitos}</div>
            <div className="text-xs text-ink-600">próximos {data.horizonte_meses} meses</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">LP ponderado esperado</div>
            <div className="tabular mt-2 text-4xl font-semibold text-brand">
              ${(data.monto_lp_ponderado_total_usd / 1e6).toFixed(1)}M
            </div>
            <div className="text-xs text-ink-600">USD pipeline × prob</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Meses con hitos</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">{mesesOrdenados.length}</div>
            <div className="text-xs text-ink-600">de {data.horizonte_meses} posibles</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Próximo hito</div>
            <div className="tabular mt-2 text-2xl font-semibold text-ink">
              {data.hitos[0] ? new Date(data.hitos[0].fecha).toLocaleDateString('es-CL') : '—'}
            </div>
            <div className="text-xs text-ink-600">
              {data.hitos[0]?.tipo ?? '—'}
            </div>
          </div>
        </div>
      </section>

      {/* Filtros */}
      <section className="flex flex-wrap items-center gap-2">
        <FiltroBtn label="Todos" count={data.total_hitos} active={filtroTipo === 'todos'} onClick={() => setFiltroTipo('todos')} />
        {Object.entries(data.por_tipo).map(([tipo, n]) => (
          <FiltroBtn
            key={tipo}
            label={`${TIPO_ICON[tipo] ?? ''} ${TIPO_LABEL[tipo] ?? tipo}`}
            count={n}
            active={filtroTipo === tipo}
            onClick={() => setFiltroTipo(tipo)}
          />
        ))}
      </section>

      {/* Timeline por mes */}
      <section className="space-y-6">
        {mesesOrdenados.map((mes) => {
          const hitos = data.por_mes[mes].filter((h) => filtroTipo === 'todos' || h.tipo === filtroTipo);
          if (hitos.length === 0) return null;
          return (
            <div key={mes}>
              <div className="sticky top-16 z-10 mb-3 inline-block rounded-full bg-ink px-4 py-1.5 text-sm font-semibold text-white shadow-apple">
                {formatMes(mes)}
                <span className="ml-2 text-xs opacity-70">({hitos.length})</span>
              </div>
              <div className="space-y-2 border-l-2 border-ink-100 pl-6 ml-3">
                {hitos.map((h, idx) => (
                  <HitoCard key={`${mes}-${idx}`} hito={h} />
                ))}
              </div>
            </div>
          );
        })}
        {hitosVisibles.length === 0 && (
          <div className="apple-card text-center text-ink-400">
            No hay hitos para el filtro seleccionado.
          </div>
        )}
      </section>
    </div>
  );
}

function HitoCard({ hito }: { hito: Hito }) {
  const cls = TIPO_COLOR[hito.tipo] ?? 'bg-ink-50 text-ink-600 border-ink-100';
  const icon = TIPO_ICON[hito.tipo] ?? '📌';
  return (
    <div className={`apple-card relative ${hito.prioridad === 'alta' ? 'ring-1 ring-orange-200' : ''}`}>
      {/* Dot en línea */}
      <div className={`absolute -left-[34px] top-5 h-3 w-3 rounded-full border-2 border-white ring-2 ${hito.prioridad === 'alta' ? 'bg-orange-500 ring-orange-200' : 'bg-brand ring-brand/30'}`} />
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-base">{icon}</span>
            <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${cls}`}>
              {TIPO_LABEL[hito.tipo] ?? hito.tipo}
            </span>
            <span className="tabular text-ink-400">{new Date(hito.fecha).toLocaleDateString('es-CL')}</span>
            {hito.prioridad === 'alta' && (
              <span className="rounded-full bg-orange-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-orange-600">
                ⚡ Alta
              </span>
            )}
          </div>
          <h3 className="mt-2 font-semibold text-ink">{hito.titulo}</h3>
          <p className="mt-1 text-xs text-ink-600">{hito.descripcion}</p>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-ink-400">
            <span>👤 {hito.owner}</span>
            {hito.monto_estimado_usd && hito.monto_estimado_usd > 0 && (
              <span className="text-brand">💰 ${(hito.monto_estimado_usd / 1e6).toFixed(1)}M USD (ponderado)</span>
            )}
          </div>
        </div>
        {hito.link && (
          <Link href={hito.link} className="shrink-0 rounded-full bg-ink-50 px-3 py-1 text-[11px] font-medium text-ink-600 transition hover:bg-brand hover:text-white">
            Ver →
          </Link>
        )}
      </div>
    </div>
  );
}

function FiltroBtn({ label, count, active, onClick }: { label: string; count: number; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
        active ? 'bg-ink text-white' : 'bg-ink-50 text-ink-600 hover:bg-ink-100'
      }`}
    >
      {label} <span className="opacity-70">({count})</span>
    </button>
  );
}
