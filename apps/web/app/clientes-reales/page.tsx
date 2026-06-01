'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Cliente = {
  id: string;
  nombre: string;
  pais: string;
  sector: string;
  producto_target: string[];
  volumen_anual_estimado_ton: number;
  estado_relacion: string;
  canal_contacto: string;
  ultimo_contacto: string;
  valor_anual_estimado_usd: number;
  notas: string;
  dossier_inbox: string;
};

type Benchmark = {
  producto: string;
  competidor: string;
  precio_referencia_usd_kg: number;
  uso: string;
  comparable_a: string;
  dossier_inbox: string;
};

type Resp = {
  clientes: Cliente[];
  benchmarks_proteinas: Benchmark[];
  resumen: {
    total_clientes: number;
    por_estado: Record<string, number>;
    por_sector: Record<string, number>;
    valor_anual_total_usd: number;
    volumen_anual_total_ton: number;
    benchmarks_count: number;
  };
};

const ESTADO_COLOR: Record<string, string> = {
  prospect: 'bg-ink-50 text-ink-600 ring-ink-100',
  contactado: 'bg-yellow-50 text-yellow-700 ring-yellow-200',
  dd: 'bg-orange-50 text-orange-600 ring-orange-200',
  loi: 'bg-brand-50 text-brand ring-brand/30',
  contrato: 'bg-brand-100 text-brand-700 ring-brand/40',
  perdido: 'bg-red-50 text-red-600 ring-red-200',
};

const SECTOR_LABEL: Record<string, string> = {
  alimentos_humanos: '🍽 Alimentos humanos',
  feed_acuicola: '🐟 Feed acuícola',
  feed_pet: '🐾 Feed pet',
  feed_ganaderia: '🐄 Feed ganadería',
  industrial: '🏭 Industrial',
  agro_input: '🌾 Agro input',
};

export default function ClientesRealesPage() {
  const [data, setData] = useState<Resp | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/clientes/reales`).then(r => r.ok && r.json()).then(setData);
  }, []);

  if (!data) return <div className="apple-card text-ink-400">Cargando catálogo...</div>;

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">🍽 Clientes Reales</h1>
          <p className="mt-2 text-sm text-ink-400">
            Catálogo de clientes y prospects identificados en el dossier P1.
            Sectores: alimentos humanos, agro input, feed.
          </p>
        </div>
      </header>

      {/* Hero stats */}
      <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Total clientes</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">{data.resumen.total_clientes}</div>
            <div className="text-xs text-ink-600">identificados en P1</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Valor anual potencial</div>
            <div className="tabular mt-2 text-4xl font-semibold text-brand">
              ${(data.resumen.valor_anual_total_usd / 1e6).toFixed(2)}M
            </div>
            <div className="text-xs text-ink-600">USD si todos cierran</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Volumen total</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">
              {data.resumen.volumen_anual_total_ton.toLocaleString('es-CL')}
            </div>
            <div className="text-xs text-ink-600">ton/año proyectadas</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Benchmarks</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">{data.resumen.benchmarks_count}</div>
            <div className="text-xs text-ink-600">competidores con specs</div>
          </div>
        </div>
      </section>

      {/* Clientes cards */}
      <section>
        <h2 className="mb-4 text-2xl font-semibold tracking-apple text-ink">Catálogo de clientes</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {data.clientes.map((c) => (
            <ClienteCard key={c.id} c={c} />
          ))}
        </div>
      </section>

      {/* Benchmarks */}
      <section>
        <h2 className="mb-4 text-2xl font-semibold tracking-apple text-ink">Benchmarks de mercado</h2>
        <p className="mb-4 text-sm text-ink-400">
          Especs de productos competidores identificados. Sirven de referencia para calibrar precios SKUs Trongkai.
        </p>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {data.benchmarks_proteinas.map((b, i) => (
            <div key={i} className="apple-card">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">{b.competidor}</div>
              <h3 className="mt-1 font-semibold text-ink">{b.producto}</h3>
              <div className="tabular mt-2 text-2xl font-semibold text-brand">
                ${b.precio_referencia_usd_kg.toFixed(2)}/kg
              </div>
              <p className="mt-2 text-xs text-ink-600">{b.uso}</p>
              <div className="mt-3 rounded bg-brand-50 px-2 py-1 text-[11px] text-brand">
                Comparable a Trongkai: <strong>{b.comparable_a}</strong>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function ClienteCard({ c }: { c: Cliente }) {
  return (
    <div className="apple-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-ink">{c.nombre}</h3>
          <div className="mt-0.5 text-xs text-ink-400">
            {c.pais} · {SECTOR_LABEL[c.sector] ?? c.sector}
          </div>
        </div>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${ESTADO_COLOR[c.estado_relacion] ?? 'bg-ink-50 text-ink-600 ring-ink-100'}`}>
          {c.estado_relacion}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 border-y border-ink-100 py-3">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-ink-400">Volumen anual</div>
          <div className="tabular text-base font-semibold text-ink">{c.volumen_anual_estimado_ton.toLocaleString('es-CL')} ton</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-ink-400">Valor anual</div>
          <div className="tabular text-base font-semibold text-brand">${(c.valor_anual_estimado_usd / 1000).toLocaleString('es-CL')}k USD</div>
        </div>
      </div>

      <div className="mt-3">
        <div className="text-[10px] uppercase tracking-wider text-ink-400">SKUs target</div>
        <div className="mt-1 flex flex-wrap gap-1">
          {c.producto_target.map((sku) => (
            <span key={sku} className="rounded-full bg-ink-50 px-2 py-0.5 text-[10px] font-medium text-ink-600">{sku}</span>
          ))}
        </div>
      </div>

      <p className="mt-3 text-xs text-ink-600 leading-relaxed">{c.notas}</p>

      <div className="mt-3 flex items-center justify-between border-t border-ink-100 pt-2 text-[11px] text-ink-400">
        <span>📞 {c.canal_contacto}</span>
        {c.ultimo_contacto && <span>{c.ultimo_contacto}</span>}
      </div>
    </div>
  );
}
