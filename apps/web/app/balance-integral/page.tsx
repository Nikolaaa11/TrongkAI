'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Integrado = {
  producto: any;
  energia: any;
  agua: any;
  rrhh: any;
  intensidades: Record<string, number>;
  costos_consolidados: Record<string, number>;
  alarmas_consolidadas: any[];
  score_eficiencia_global: number;
  coherencia_cross_balance: Record<string, any>;
};

export default function BalanceIntegralPage() {
  const [data, setData] = useState<Integrado | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/balance/integrado`)
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <p className="text-red-500">Error: {error}</p>;
  if (!data) return <p className="text-ink-400">Cargando los 4 balances…</p>;

  const criticas = data.alarmas_consolidadas.filter((a) => a.severidad === 'critica').length;
  const altas = data.alarmas_consolidadas.filter((a) => a.severidad === 'alta').length;

  const cards = [
    { title: '⚡ Energía', href: '/balance-energia', closure: data.energia.closure_pct, kpi: `${data.energia.consumo_total_anual_mwh.toFixed(1)} MWh/año`, alarmas: data.energia.alarmas.length },
    { title: '💧 Agua', href: '/balance-agua', closure: data.agua.closure_pct, kpi: `${data.agua.consumo_total_anual_m3.toFixed(0)} m³/año`, alarmas: data.agua.alarmas.length },
    { title: '👥 RRHH', href: '/balance-rrhh', closure: data.rrhh.closure_pct, kpi: `${(data.rrhh.utilizacion_pct * 100).toFixed(0)}% uso`, alarmas: data.rrhh.alarmas.length, isHR: true },
    { title: '📦 Producto', href: '/balance', closure: data.producto.closure_pct, kpi: `${(data.producto.produccion_anual_kg / 1000).toFixed(0)} t/año`, alarmas: 0 },
  ];

  return (
    <div className="space-y-12">
      <header className="text-center">
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Balances integrales</p>
        <h1 className="mt-2 text-5xl font-bold tracking-tight">Vista integral · los 4 balances</h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-ink-500">
          Producto, energía, agua y RRHH en un solo cockpit. Score de eficiencia global y cross-checks que validan coherencia entre los 4.
        </p>
      </header>

      {/* Score Global */}
      <section className="rounded-3xl border border-ink-100 bg-gradient-to-br from-ink-50/40 to-white p-10 text-center">
        <p className="text-[12px] font-semibold uppercase tracking-wider text-ink-400">Score eficiencia global</p>
        <div className="mt-3 text-7xl font-bold tracking-tight" style={{ background: 'linear-gradient(135deg, #1a8a1a 0%, #34a853 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          {data.score_eficiencia_global.toFixed(0)}
          <span className="text-3xl text-ink-400">/100</span>
        </div>
        <div className="mt-6 flex justify-center gap-4">
          <span className={`rounded-full px-4 py-2 text-sm font-semibold ${criticas > 0 ? 'bg-red-50 text-red-600' : 'bg-brand-50 text-brand'}`}>
            🚨 {criticas} críticas
          </span>
          <span className={`rounded-full px-4 py-2 text-sm font-semibold ${altas > 0 ? 'bg-orange-50 text-orange-600' : 'bg-ink-50 text-ink-600'}`}>
            ⚠️ {altas} altas
          </span>
        </div>
      </section>

      {/* 4 cards de balance */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {cards.map((c) => (
          <Link key={c.href} href={c.href} className="rounded-2xl border border-ink-100 bg-white p-6 transition-all hover:border-brand hover:shadow-lg">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-semibold">{c.title}</h3>
                <p className="mt-1 text-2xl font-bold text-ink-700">{c.kpi}</p>
                <p className="mt-1 text-xs text-ink-400">Closure {c.closure.toFixed(2)}%</p>
              </div>
              {c.alarmas > 0 && (
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${c.isHR ? 'bg-red-50 text-red-600' : 'bg-orange-50 text-orange-600'}`}>
                  {c.alarmas} alarmas
                </span>
              )}
            </div>
          </Link>
        ))}
      </section>

      {/* Intensidades */}
      <section>
        <h2 className="mb-6 text-2xl font-bold">Intensidades por kg producto</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Object.entries(data.intensidades).map(([k, v]) => (
            <div key={k} className="rounded-xl border border-ink-100 bg-white p-4">
              <p className="text-[11px] uppercase text-ink-400">{k.replace(/_/g, ' ')}</p>
              <p className="mt-2 text-2xl font-bold">{typeof v === 'number' ? v.toFixed(3) : v}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Costos consolidados */}
      <section>
        <h2 className="mb-6 text-2xl font-bold">Costos operacionales anuales</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {Object.entries(data.costos_consolidados).map(([k, v]) => (
            <div key={k} className={`rounded-xl border p-4 ${k.includes('total') ? 'border-brand bg-brand-50/50' : 'border-ink-100 bg-white'}`}>
              <p className="text-[11px] uppercase text-ink-400">{k.replace(/_/g, ' ').replace('anual usd', '')}</p>
              <p className="mt-2 text-xl font-bold">${(v / 1e3).toFixed(1)}k USD</p>
            </div>
          ))}
        </div>
      </section>

      {/* Cross-checks */}
      <section>
        <h2 className="mb-6 text-2xl font-bold">Coherencia cross-balance</h2>
        <div className="space-y-3">
          {Object.entries(data.coherencia_cross_balance).map(([k, v]: [string, any]) => (
            <div key={k} className="flex items-center justify-between rounded-xl border border-ink-100 bg-white p-4">
              <div>
                <p className="font-semibold">{k.replace(/_/g, ' ')}</p>
                <p className="text-sm text-ink-500">{JSON.stringify(v, null, 0).slice(0, 100)}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${v.ok ? 'bg-brand-50 text-brand' : 'bg-orange-50 text-orange-600'}`}>
                {v.ok ? 'OK' : 'ATENCIÓN'}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* Alarmas */}
      {data.alarmas_consolidadas.length > 0 && (
        <section>
          <h2 className="mb-6 text-2xl font-bold">Alarmas consolidadas ({data.alarmas_consolidadas.length})</h2>
          <div className="space-y-2">
            {data.alarmas_consolidadas.slice(0, 20).map((a, i) => (
              <div key={i} className={`rounded-xl border p-4 ${a.severidad === 'critica' ? 'border-red-200 bg-red-50' : a.severidad === 'alta' ? 'border-orange-200 bg-orange-50' : 'border-ink-100 bg-white'}`}>
                <div className="flex items-center justify-between">
                  <p className="font-semibold">[{a.balance}] {a.mensaje}</p>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${a.severidad === 'critica' ? 'bg-red-600 text-white' : a.severidad === 'alta' ? 'bg-orange-600 text-white' : 'bg-ink-600 text-white'}`}>
                    {a.severidad}
                  </span>
                </div>
                {a.accion && <p className="mt-1 text-sm text-ink-600">→ {a.accion}</p>}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
