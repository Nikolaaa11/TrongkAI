'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Estado = 'faltante' | 'parcial' | 'completo';

type Item = {
  id: string;
  titulo: string;
  descripcion: string;
  categoria: string;
  estado: Estado;
  responsable: string;
  formato: string;
  must_have: boolean;
  plataforma_link: string;
};

type Resp = {
  items: Item[];
  resumen: {
    total: number;
    completos: number;
    parciales: number;
    faltantes: number;
    pct_completo: number;
    pct_avance: number;
    by_categoria: Record<string, { total: number; completos: number; parciales: number; faltantes: number }>;
  };
};

const ESTADO_LABEL: Record<Estado, string> = {
  faltante: 'Faltante',
  parcial: 'Parcial',
  completo: 'Completo',
};

const ESTADO_COLOR: Record<Estado, string> = {
  faltante: 'bg-red-50 text-red-600 ring-red-200',
  parcial: 'bg-yellow-50 text-yellow-700 ring-yellow-200',
  completo: 'bg-brand-50 text-brand ring-brand/20',
};

const CATEGORIA_ICON: Record<string, string> = {
  'Corporativo y Legal': '⚖️',
  'Financiero y Auditoría': '📊',
  'Comercial y Mercado': '💼',
  'Operacional y Técnico': '⚙️',
  'ESG y Sustentabilidad': '🌱',
  'Equipo y Gobierno': '👥',
};

export default function DataRoomPage() {
  const [data, setData] = useState<Resp | null>(null);
  const [filtro, setFiltro] = useState<'todos' | Estado>('todos');
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void cargar();
  }, []);

  async function cargar() {
    try {
      const r = await fetch(`${ENGINE_URL}/data-room/checklist`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      setErr(String(e));
    }
  }

  const itemsByCategoria = useMemo(() => {
    if (!data) return {};
    const filtered = filtro === 'todos' ? data.items : data.items.filter((i) => i.estado === filtro);
    return filtered.reduce<Record<string, Item[]>>((acc, item) => {
      if (!acc[item.categoria]) acc[item.categoria] = [];
      acc[item.categoria].push(item);
      return acc;
    }, {});
  }, [data, filtro]);

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Data Room — Due Diligence Checklist</h1>
          <p className="mt-2 text-sm text-ink-400">
            Estado consolidado del data room. 41 items DD organizados en 6 categorías para
            cumplir con expectativas de LPs, bancos (BICE, Santander) y DFIs (BID Invest, IFC).
          </p>
        </div>
      </header>

      {err && <div className="apple-card text-red-600">{err}</div>}

      {data && (
        <>
          {/* Score grande */}
          <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
            <div className="flex flex-col items-center gap-6 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
                  Avance Data Room
                </div>
                <div className="mt-2 flex items-baseline gap-3">
                  <div className="tabular text-6xl font-semibold text-ink">{data.resumen.pct_avance.toFixed(0)}</div>
                  <div className="text-2xl text-ink-400">/ 100</div>
                </div>
                <div className="mt-1 text-sm text-ink-600">
                  {data.resumen.completos} completos · {data.resumen.parciales} parciales · {data.resumen.faltantes} faltantes (de {data.resumen.total})
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 text-center">
                <MiniStat n={data.resumen.completos} label="Completos" tone="ok" />
                <MiniStat n={data.resumen.parciales} label="Parciales" tone="warn" />
                <MiniStat n={data.resumen.faltantes} label="Faltantes" tone="bad" />
              </div>
            </div>
            <div className="mt-6">
              <div className="relative h-3 w-full overflow-hidden rounded-full bg-white">
                <div className="absolute h-full bg-brand transition-all" style={{ width: `${data.resumen.pct_completo}%` }} />
                <div
                  className="absolute h-full bg-yellow-300 transition-all"
                  style={{
                    left: `${data.resumen.pct_completo}%`,
                    width: `${(data.resumen.parciales / data.resumen.total) * 100}%`,
                  }}
                />
              </div>
            </div>
          </section>

          {/* By categoria — small cards */}
          <section className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
            {Object.entries(data.resumen.by_categoria).map(([cat, s]) => (
              <div key={cat} className="apple-card">
                <div className="text-2xl">{CATEGORIA_ICON[cat] || '📁'}</div>
                <div className="mt-2 text-[11px] font-semibold uppercase tracking-wider text-ink-400">{cat}</div>
                <div className="tabular mt-1 text-xl font-semibold text-ink">{s.completos}<span className="text-sm text-ink-400">/{s.total}</span></div>
              </div>
            ))}
          </section>

          {/* Filtros */}
          <section className="flex flex-wrap items-center gap-2">
            <FiltroBtn label="Todos" count={data.resumen.total} active={filtro === 'todos'} onClick={() => setFiltro('todos')} />
            <FiltroBtn label="Faltantes" count={data.resumen.faltantes} active={filtro === 'faltante'} onClick={() => setFiltro('faltante')} tone="bad" />
            <FiltroBtn label="Parciales" count={data.resumen.parciales} active={filtro === 'parcial'} onClick={() => setFiltro('parcial')} tone="warn" />
            <FiltroBtn label="Completos" count={data.resumen.completos} active={filtro === 'completo'} onClick={() => setFiltro('completo')} tone="ok" />
          </section>

          {/* Items agrupados por categoría */}
          {Object.entries(itemsByCategoria).map(([cat, items]) => (
            <section key={cat}>
              <h2 className="mb-4 flex items-center gap-2 text-xl font-semibold tracking-apple text-ink">
                <span className="text-2xl">{CATEGORIA_ICON[cat] || '📁'}</span> {cat}
                <span className="text-sm font-normal text-ink-400">({items.length})</span>
              </h2>
              <div className="space-y-2">
                {items.map((item) => (
                  <ItemCard key={item.id} item={item} />
                ))}
              </div>
            </section>
          ))}

          {/* Cómo subir items */}
          <section className="rounded-appleXl bg-ink-50 p-8">
            <h2 className="text-2xl font-semibold tracking-apple text-ink">Cómo cerrar el data room al 100%</h2>
            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
              <FlujoCard num="1" titulo="Items COMPLETOS verdes" desc="Ya cubiertos por la plataforma (modelo, sensitivity, carbono, etc). Solo descarga el PDF correspondiente." />
              <FlujoCard num="2" titulo="Items PARCIALES" desc="Cubrimos parte (modelo) pero falta validación externa (auditor, asesor M&A, term sheets reales)." />
              <FlujoCard num="3" titulo="Items FALTANTES" desc="Documentos legales/operacionales que solo el equipo puede generar. Ver responsable de cada uno." />
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function ItemCard({ item }: { item: Item }) {
  return (
    <div className="apple-card">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-ink">{item.titulo}</h3>
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${ESTADO_COLOR[item.estado]}`}>
              {ESTADO_LABEL[item.estado]}
            </span>
            {item.must_have ? (
              <span className="text-[10px] font-medium uppercase tracking-wider text-ink-400">must-have</span>
            ) : (
              <span className="text-[10px] font-medium uppercase tracking-wider text-ink-400">nice-to-have</span>
            )}
          </div>
          <p className="mt-1 text-sm text-ink-600">{item.descripcion}</p>
          <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-ink-400">
            <span><strong className="text-ink-600">Responsable:</strong> {item.responsable}</span>
            <span><strong className="text-ink-600">Formato:</strong> {item.formato}</span>
          </div>
        </div>
        {item.plataforma_link && (
          <Link
            href={item.plataforma_link}
            className="shrink-0 rounded-full bg-brand px-3 py-1.5 text-xs font-medium text-white transition hover:bg-brand-700"
          >
            Ver en plataforma →
          </Link>
        )}
      </div>
    </div>
  );
}

function MiniStat({ n, label, tone }: { n: number; label: string; tone: 'ok' | 'warn' | 'bad' }) {
  const cls = tone === 'ok' ? 'text-brand' : tone === 'warn' ? 'text-yellow-700' : 'text-red-600';
  return (
    <div>
      <div className={`tabular text-3xl font-semibold ${cls}`}>{n}</div>
      <div className="text-[11px] uppercase tracking-wider text-ink-400">{label}</div>
    </div>
  );
}

function FiltroBtn({ label, count, active, onClick, tone }: { label: string; count: number; active: boolean; onClick: () => void; tone?: 'ok' | 'warn' | 'bad' }) {
  const activeColor = tone === 'ok' ? 'bg-brand-50 text-brand ring-brand/20' :
    tone === 'warn' ? 'bg-yellow-50 text-yellow-700 ring-yellow-200' :
    tone === 'bad' ? 'bg-red-50 text-red-600 ring-red-200' :
    'bg-ink text-white';
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
        active ? `ring-1 ${activeColor}` : 'text-ink-600 hover:bg-ink-50'
      }`}
    >
      {label} <span className="ml-1 text-xs opacity-70">({count})</span>
    </button>
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
