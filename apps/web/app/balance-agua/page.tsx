'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Balance = {
  flujos: any[];
  consumo_total_anual_m3: number;
  agua_fresca_m3: number;
  agua_recirculada_m3: number;
  agua_recirculada_pct: number;
  intensidad_hidrica_l_por_kg_producto: number;
  costo_total_anual_usd: number;
  rile_anual_m3: number;
  rile_pct: number;
  closure_pct: number;
  cumplimiento_dga: Record<string, any>;
  alarmas: any[];
  sankey: { nodes: any[]; links: any[]; unit?: string };
};

export default function BalanceAguaPage() {
  const [data, setData] = useState<Balance | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/balance/agua`).then((r) => r.json()).then(setData);
  }, []);

  if (!data) return <p className="text-ink-400">Cargando balance hídrico…</p>;

  const kpis = [
    { label: 'Consumo anual', valor: `${data.consumo_total_anual_m3.toFixed(0)} m³` },
    { label: 'Intensidad', valor: `${data.intensidad_hidrica_l_por_kg_producto.toFixed(1)} L/kg` },
    { label: 'Recirculación', valor: `${(data.agua_recirculada_pct * 100).toFixed(1)}%` },
    { label: 'RILE', valor: `${(data.rile_pct * 100).toFixed(0)}%` },
    { label: 'Costo anual', valor: `$${(data.costo_total_anual_usd / 1000).toFixed(1)}k USD` },
    { label: 'Closure', valor: `${data.closure_pct.toFixed(2)}%` },
  ];

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Balance de Agua</p>
        <h1 className="mt-2 text-4xl font-bold">💧 {data.consumo_total_anual_m3.toFixed(0)} m³/año</h1>
        <p className="mt-2 text-ink-500">5 flujos · closure ±1% · cumplimiento DGA</p>
      </header>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-xl border border-ink-100 bg-white p-4">
            <p className="text-[11px] uppercase text-ink-400">{k.label}</p>
            <p className="mt-1 text-xl font-bold">{k.valor}</p>
          </div>
        ))}
      </div>

      {/* DGA */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Cumplimiento DGA</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {Object.entries(data.cumplimiento_dga).map(([pozo, info]: [string, any]) => (
            <div key={pozo} className={`rounded-xl border p-5 ${info.ok ? 'border-brand bg-brand-50/40' : 'border-red-300 bg-red-50'}`}>
              <h3 className="text-lg font-semibold">{pozo}</h3>
              <p className="mt-2 text-sm text-ink-600">
                Derecho: <strong>{info.derecho_l_s} L/s</strong> · Uso: <strong>{info.uso_actual_l_s.toFixed(2)} L/s</strong>
              </p>
              <div className="mt-3 h-3 overflow-hidden rounded-full bg-ink-100">
                <div className={`h-full ${info.uso_pct_derecho > 0.8 ? 'bg-red-500' : 'bg-brand'}`} style={{ width: `${Math.min(100, info.uso_pct_derecho * 100)}%` }} />
              </div>
              <p className="mt-2 text-xs text-ink-500">{(info.uso_pct_derecho * 100).toFixed(1)}% del derecho · {info.ok ? '✅ OK' : '🚨 EXCEDIDO'}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Alarmas */}
      {data.alarmas.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold">Alarmas ({data.alarmas.length})</h2>
          <div className="space-y-2">
            {data.alarmas.map((a, i) => (
              <div key={i} className={`rounded-xl border p-4 ${a.severidad === 'critica' ? 'border-red-200 bg-red-50' : a.severidad === 'alta' ? 'border-orange-200 bg-orange-50' : 'border-ink-100 bg-white'}`}>
                <p className="font-semibold">{a.mensaje}</p>
                {a.accion && <p className="mt-1 text-sm text-ink-500">→ {a.accion}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Tabla flujos */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Flujos de agua</h2>
        <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
          <table className="min-w-full divide-y divide-ink-100 text-sm">
            <thead className="bg-ink-50/40 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3 text-left">Origen</th>
                <th className="px-4 py-3 text-left">Fuente</th>
                <th className="px-4 py-3 text-left">Destino</th>
                <th className="px-4 py-3 text-left">Uso</th>
                <th className="px-4 py-3 text-right">m³/h</th>
                <th className="px-4 py-3 text-right">L/s</th>
                <th className="px-4 py-3 text-right">m³/año</th>
                <th className="px-4 py-3 text-right">Recirc</th>
                <th className="px-4 py-3 text-right">Costo USD</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-50">
              {data.flujos.map((f, i) => (
                <tr key={i} className="hover:bg-ink-50/30">
                  <td className="px-4 py-3 font-medium">{f.origen}</td>
                  <td className="px-4 py-3 capitalize text-ink-500">{f.fuente.replace('_', ' ')}</td>
                  <td className="px-4 py-3">{f.destino}</td>
                  <td className="px-4 py-3 capitalize text-ink-500">{f.uso}</td>
                  <td className="px-4 py-3 text-right">{f.caudal_m3_h}</td>
                  <td className="px-4 py-3 text-right">{f.caudal_l_s.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-semibold">{f.volumen_anual_m3.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right">{(f.pct_recirculable * 100).toFixed(0)}%</td>
                  <td className="px-4 py-3 text-right">${f.costo_anual_usd.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
