'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Balance = {
  flujos: any[];
  consumo_total_anual_mwh: number;
  costo_total_anual_usd: number;
  intensidad_energetica_kwh_por_kg_producto: number;
  mix_renovable_pct: number;
  factor_potencia_planta: number;
  factor_carga_promedio: number;
  closure_pct: number;
  alarmas: any[];
  sankey: { nodes: any[]; links: any[]; unit?: string };
};

export default function BalanceEnergiaPage() {
  const [data, setData] = useState<Balance | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/balance/energia`).then((r) => r.json()).then(setData);
  }, []);

  if (!data) return <p className="text-ink-400">Cargando balance energético…</p>;

  const kpis = [
    { label: 'Consumo anual', valor: `${data.consumo_total_anual_mwh.toFixed(1)} MWh` },
    { label: 'Intensidad', valor: `${data.intensidad_energetica_kwh_por_kg_producto.toFixed(2)} kWh/kg` },
    { label: 'Mix renovable', valor: `${(data.mix_renovable_pct * 100).toFixed(1)}%` },
    { label: 'Factor potencia', valor: data.factor_potencia_planta.toFixed(3) },
    { label: 'Costo anual', valor: `$${(data.costo_total_anual_usd / 1000).toFixed(0)}k USD` },
    { label: 'Closure', valor: `${data.closure_pct.toFixed(2)}%` },
  ];

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Balance de Energía</p>
        <h1 className="mt-2 text-4xl font-bold">⚡ {data.consumo_total_anual_mwh.toFixed(0)} MWh/año</h1>
        <p className="mt-2 text-ink-500">7 equipos · closure ±2% · alarmas SEC + ESG</p>
      </header>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-xl border border-ink-100 bg-white p-4">
            <p className="text-[11px] uppercase text-ink-400">{k.label}</p>
            <p className="mt-1 text-xl font-bold">{k.valor}</p>
          </div>
        ))}
      </div>

      {/* Alarmas */}
      {data.alarmas.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold">Alarmas activas ({data.alarmas.length})</h2>
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
        <h2 className="mb-4 text-xl font-bold">Equipos energéticos</h2>
        <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
          <table className="min-w-full divide-y divide-ink-100 text-sm">
            <thead className="bg-ink-50/40 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3 text-left">Equipo</th>
                <th className="px-4 py-3 text-left">Tipo</th>
                <th className="px-4 py-3 text-right">kW</th>
                <th className="px-4 py-3 text-right">Horas/año</th>
                <th className="px-4 py-3 text-right">Carga</th>
                <th className="px-4 py-3 text-right">FP</th>
                <th className="px-4 py-3 text-right">MWh/año</th>
                <th className="px-4 py-3 text-right">Costo USD</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-50">
              {data.flujos.map((f, i) => (
                <tr key={i} className="hover:bg-ink-50/30">
                  <td className="px-4 py-3 font-medium">{f.equipo}</td>
                  <td className="px-4 py-3 capitalize text-ink-500">{f.tipo.replace('_', ' ')}</td>
                  <td className="px-4 py-3 text-right">{f.potencia_nominal_kw}</td>
                  <td className="px-4 py-3 text-right">{f.horas_operacion_anual}</td>
                  <td className="px-4 py-3 text-right">{(f.factor_carga * 100).toFixed(0)}%</td>
                  <td className="px-4 py-3 text-right">{f.factor_potencia.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right font-semibold">{(f.consumo_anual_kwh / 1000).toFixed(0)}</td>
                  <td className="px-4 py-3 text-right">${(f.costo_anual_usd / 1000).toFixed(1)}k</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Sankey simplificado */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Distribución por fuente → equipo</h2>
        <div className="rounded-2xl border border-ink-100 bg-white p-6">
          <div className="space-y-2">
            {data.sankey.links.map((l: any, i: number) => {
              const max = Math.max(...data.sankey.links.map((x: any) => x.value));
              const pct = (l.value / max) * 100;
              return (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-xs text-ink-600">
                    <span className="font-medium">{l.source} → {l.target}</span>
                    <span className="font-semibold">{l.value} {data.sankey.unit ?? ''}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-ink-50">
                    <div className="h-full bg-gradient-to-r from-brand to-brand-light" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
