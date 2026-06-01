'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type PricingSKU = {
  sku: string;
  precio_actual_clp_kg: number;
  precio_actual_usd_kg: number;
  benchmark_usd_kg: number | null;
  benchmark_descripcion: string;
  delta_pct_vs_benchmark: number | null;
  headroom_pct: number | null;
  recomendacion: string;
};

type Concentracion = {
  hhi: number;
  nivel_concentracion: string;
  top_1_pct: number;
  top_3_pct: number;
  n_clientes_efectivos: number;
  riesgo_perdida_top_1: string;
  recomendacion: string;
};

type TechROI = {
  tech_id: string;
  tech_nombre: string;
  capex_usd: number;
  incremento_revenue_anual_usd: number;
  ahorro_opex_anual_usd: number;
  payback_anos: number | null;
  npv_5y_usd: number;
  irr_aproximado_pct: number | null;
  recomendacion: string;
};

type RevenuePoint = {
  mes: number;
  revenue_base_usd: number;
  revenue_clientes_reales_usd: number;
  revenue_total_usd: number;
  clientes_activos: number;
};

type Resp = {
  pricing_skus: PricingSKU[];
  concentracion_clientes: Concentracion;
  tech_roi: TechROI[];
  revenue_pipeline_60m: RevenuePoint[];
  resumen_ejecutivo: {
    revenue_total_5y_usd: number;
    tech_npv_total_5y_usd: number;
    skus_sobreprecio: number;
    skus_con_headroom_alto: number;
    hhi_concentracion: number;
    concentracion_nivel: string;
    n_clientes_efectivos: number;
  };
};

const NIVEL_COLOR: Record<string, string> = {
  baja: 'text-brand',
  moderada: 'text-yellow-700',
  alta: 'text-orange-600',
  crítica: 'text-red-600',
};

export default function CommercialPage() {
  const [data, setData] = useState<Resp | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/commercial/intelligence`).then(r => r.ok && r.json()).then(setData);
  }, []);

  if (!data) return <div className="apple-card text-ink-400">Cargando análisis comercial...</div>;

  const r = data.resumen_ejecutivo;

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">💼 Commercial Intelligence</h1>
          <p className="mt-2 text-sm text-ink-400">
            Cruce de datos reales: 5 clientes catalogados × 3 benchmarks proteínas × 3 tecnologías × plan financiero.
            Insights de pricing, concentración, ROI tecnológico y revenue pipeline.
          </p>
        </div>
      </header>

      {/* Hero stats */}
      <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Revenue total 5y</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">${(r.revenue_total_5y_usd / 1e6).toFixed(1)}M</div>
            <div className="text-xs text-ink-600">USD plan + clientes reales</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">NPV tech stack 5y</div>
            <div className={`tabular mt-2 text-4xl font-semibold ${r.tech_npv_total_5y_usd >= 0 ? 'text-brand' : 'text-red-600'}`}>
              ${(r.tech_npv_total_5y_usd / 1e6).toFixed(2)}M
            </div>
            <div className="text-xs text-ink-600">USD valor agregado tech</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Concentración HHI</div>
            <div className={`tabular mt-2 text-4xl font-semibold ${NIVEL_COLOR[r.concentracion_nivel] || 'text-ink'}`}>
              {r.hhi_concentracion.toFixed(0)}
            </div>
            <div className="text-xs text-ink-600">{r.concentracion_nivel} · {r.n_clientes_efectivos} clientes efectivos</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">SKUs con headroom</div>
            <div className="tabular mt-2 text-4xl font-semibold text-brand">{r.skus_con_headroom_alto}</div>
            <div className="text-xs text-ink-600">≥20% bajo benchmark (subir precio)</div>
          </div>
        </div>
      </section>

      {/* Pricing Analysis */}
      <section>
        <h2 className="mb-4 text-2xl font-semibold tracking-apple text-ink">📈 Pricing Power por SKU</h2>
        <p className="mb-4 text-sm text-ink-400">
          Precio actual vs benchmark de mercado (proteínas competidoras del dossier P1). Negativo = headroom para subir.
        </p>
        <div className="apple-card overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-100 bg-ink-50/50">
                <th className="p-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">SKU</th>
                <th className="p-3 text-right text-[11px] font-semibold uppercase tracking-wider text-ink-400">Precio USD/kg</th>
                <th className="p-3 text-right text-[11px] font-semibold uppercase tracking-wider text-ink-400">Benchmark</th>
                <th className="p-3 text-right text-[11px] font-semibold uppercase tracking-wider text-ink-400">Δ vs benchmark</th>
                <th className="p-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">Recomendación</th>
              </tr>
            </thead>
            <tbody>
              {data.pricing_skus.map((p) => {
                const tone = p.delta_pct_vs_benchmark === null
                  ? 'text-ink-400'
                  : p.delta_pct_vs_benchmark > 5
                  ? 'text-red-600 font-semibold'
                  : p.delta_pct_vs_benchmark < -20
                  ? 'text-brand font-semibold'
                  : 'text-ink-600';
                return (
                  <tr key={p.sku} className="border-b border-ink-100 last:border-0">
                    <td className="p-3 font-medium text-ink">{p.sku}</td>
                    <td className="p-3 tabular text-right text-ink">${p.precio_actual_usd_kg.toFixed(2)}</td>
                    <td className="p-3 tabular text-right text-ink-600">
                      {p.benchmark_usd_kg !== null ? `$${p.benchmark_usd_kg.toFixed(2)}` : '—'}
                    </td>
                    <td className={`p-3 tabular text-right ${tone}`}>
                      {p.delta_pct_vs_benchmark !== null ? `${p.delta_pct_vs_benchmark >= 0 ? '+' : ''}${p.delta_pct_vs_benchmark.toFixed(0)}%` : '—'}
                    </td>
                    <td className="p-3 text-xs text-ink-600">{p.recomendacion}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Concentración */}
      <section className="apple-card">
        <h2 className="text-xl font-semibold tracking-apple text-ink">🎯 Concentración de clientes (HHI)</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div>
            <div className="text-[10px] uppercase tracking-wider text-ink-400">Índice Herfindahl-Hirschman</div>
            <div className={`tabular mt-1 text-4xl font-semibold ${NIVEL_COLOR[data.concentracion_clientes.nivel_concentracion] || 'text-ink'}`}>
              {data.concentracion_clientes.hhi.toFixed(0)}
            </div>
            <div className="text-xs text-ink-600 mt-1">
              {data.concentracion_clientes.nivel_concentracion === 'baja' && '< 1,000 (diversificado)'}
              {data.concentracion_clientes.nivel_concentracion === 'moderada' && '1,000-1,800 (aceptable)'}
              {data.concentracion_clientes.nivel_concentracion === 'alta' && '1,800-2,500 (concentrado)'}
              {data.concentracion_clientes.nivel_concentracion === 'crítica' && '> 2,500 (crítico)'}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-ink-400">Top 1 cliente</div>
            <div className="tabular mt-1 text-4xl font-semibold text-ink">{data.concentracion_clientes.top_1_pct.toFixed(0)}%</div>
            <div className="text-xs text-ink-600 mt-1">del revenue total</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wider text-ink-400">Top 3 clientes</div>
            <div className="tabular mt-1 text-4xl font-semibold text-ink">{data.concentracion_clientes.top_3_pct.toFixed(0)}%</div>
            <div className="text-xs text-ink-600 mt-1">del revenue total</div>
          </div>
        </div>
        <div className="mt-4 rounded-lg bg-ink-50 p-3 text-sm">
          <strong className="text-ink">Riesgo</strong>: <span className="text-ink-600">{data.concentracion_clientes.riesgo_perdida_top_1}</span>
        </div>
        <div className="mt-2 rounded-lg bg-brand-50 p-3 text-sm">
          <strong className="text-brand">Recomendación</strong>: <span className="text-ink-600">{data.concentracion_clientes.recomendacion}</span>
        </div>
      </section>

      {/* Tech ROI */}
      <section>
        <h2 className="mb-4 text-2xl font-semibold tracking-apple text-ink">⚙️ ROI Stack Tecnológico</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {data.tech_roi.map((t) => (
            <div key={t.tech_id} className={`apple-card ${t.npv_5y_usd > 0 ? 'ring-1 ring-brand/20' : 'ring-1 ring-red-200'}`}>
              <h3 className="font-semibold text-ink">{t.tech_nombre.split('(')[0].trim()}</h3>
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-ink-400">CapEx</span><span className="tabular text-ink">${(t.capex_usd / 1000).toFixed(0)}k</span></div>
                <div className="flex justify-between"><span className="text-ink-400">Ahorro OpEx/año</span><span className="tabular text-ink">${(t.ahorro_opex_anual_usd / 1000).toFixed(0)}k</span></div>
                <div className="flex justify-between"><span className="text-ink-400">Payback</span><span className="tabular text-ink font-semibold">{t.payback_anos ? `${t.payback_anos.toFixed(1)} años` : '—'}</span></div>
                <div className="flex justify-between"><span className="text-ink-400">NPV 5y</span>
                  <span className={`tabular font-semibold ${t.npv_5y_usd >= 0 ? 'text-brand' : 'text-red-600'}`}>
                    ${(t.npv_5y_usd / 1000).toFixed(0)}k
                  </span>
                </div>
                {t.irr_aproximado_pct !== null && (
                  <div className="flex justify-between"><span className="text-ink-400">IRR aprox</span><span className="tabular text-ink">{t.irr_aproximado_pct.toFixed(0)}%</span></div>
                )}
              </div>
              <div className="mt-3 rounded bg-ink-50 p-2 text-xs text-ink-600">
                {t.recomendacion}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Revenue Pipeline visual */}
      <section className="apple-card">
        <h2 className="text-xl font-semibold tracking-apple text-ink">📊 Revenue Pipeline 60 meses</h2>
        <p className="mt-1 text-sm text-ink-400">
          Proyección mensual combinando plan financiero base + clientes reales catalogados con probabilidad ponderada.
        </p>
        <div className="mt-4 grid grid-cols-5 gap-2">
          {[0, 11, 23, 35, 59].map((idx) => {
            const p = data.revenue_pipeline_60m[idx];
            if (!p) return null;
            return (
              <div key={idx} className="rounded-lg bg-ink-50 p-3 text-center">
                <div className="text-[10px] uppercase tracking-wider text-ink-400">Mes {p.mes}</div>
                <div className="tabular mt-1 text-lg font-semibold text-ink">${(p.revenue_total_usd / 1e6).toFixed(2)}M</div>
                <div className="text-[10px] text-ink-400">{p.clientes_activos} clientes activos</div>
              </div>
            );
          })}
        </div>
        <div className="mt-4 text-xs text-ink-400">
          Revenue total 5y proyectado: <strong className="text-ink">${(r.revenue_total_5y_usd / 1e6).toFixed(1)}M USD</strong>
        </div>
      </section>
    </div>
  );
}
