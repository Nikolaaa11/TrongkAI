'use client';

import { useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Kpis = { tir: number | null; van: number; payback_meses: number | null; ebitda_margin: number; capex_ratio: number };
type ResumenAno = { kpis: Kpis; ingresos_anuales: number[]; ebitda_anuales: number[]; capex_anuales: number[] };
type WhatIfResp = {
  base: ResumenAno;
  escenarios: {
    nombre: string;
    descripcion: string | null;
    overrides: Record<string, unknown>;
    resumen: ResumenAno;
    deltas: { tir_pp: number | null; van_pct: number | null; payback_meses_delta: number | null };
  }[];
};

const PREGUNTAS_TIPO: { nombre: string; descripcion: string; overrides: Record<string, unknown> }[] = [
  {
    nombre: 'Precio licopeno -30%',
    descripcion: 'Stress test sobre el SKU más caro del Módulo Food.',
    overrides: { 'precios_clp_kg.LICOPENO': 56_000 },
  },
  {
    nombre: 'Olivero 3 sube a 2.000 ton',
    descripcion: 'Más MMPP gratis cerca de planta → baja costo unitario.',
    overrides: { costo_mmpp_clp_kg: 35 },
  },
  {
    nombre: '2da línea PEF año 2',
    descripcion: 'Acelerar CapEx para capturar mayor rendimiento aceite.',
    overrides: { 'capex_anual_clp.2': 700_000_000 },
  },
  {
    nombre: 'WACC sube a 18% (riesgo país)',
    descripcion: 'Sensibilidad ante endurecimiento de tasa de descuento.',
    overrides: { wacc_anual: 0.18 },
  },
  {
    nombre: 'Sin transferencia tecnológica',
    descripcion: 'Si CORFO no aprueba los patines de 300-400 M.',
    overrides: { transferencia_tec_anual_clp: 0 },
  },
];

function fmt(n: number | null | undefined, suffix = ''): string {
  if (n === null || n === undefined) return '—';
  return n.toLocaleString('es-CL', { maximumFractionDigits: 0 }) + suffix;
}

function pct(n: number | null | undefined): string {
  if (n === null || n === undefined) return '—';
  return (n * 100).toFixed(2) + '%';
}

export default function WhatIfPage() {
  const [data, setData] = useState<WhatIfResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [selectedIdx, setSelectedIdx] = useState<[number, number]>([0, 1]);

  async function simular() {
    setLoading(true);
    setErr(null);
    try {
      const r = await fetch(`${ENGINE_URL}/whatif`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          base: {},
          escenarios: PREGUNTAS_TIPO,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
      const json = (await r.json()) as WhatIfResp;
      setData(json);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Simulador What-if — Módulo 4</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Comparación de escenarios contra el plan base. Las 5 preguntas tipo del SUPER_PROMPT precargadas. Cada
          simulación es un snapshot no destructivo (no muta el plan base).
        </p>
      </header>

      <div className="flex items-center gap-3">
        <button
          onClick={simular}
          className="rounded bg-oliva-900 px-4 py-2 text-sm text-crema hover:bg-oliva-600 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Simulando 5 escenarios...' : 'Ejecutar 5 escenarios'}
        </button>
        {err && <p className="text-sm text-borgoña">{err}</p>}
      </div>

      {data && (
        <>
          <section>
            <h2 className="font-serif text-xl text-oliva-900">3 paneles comparados</h2>
            <p className="mt-1 text-xs text-oliva-600">Elegí 2 escenarios para comparar contra el plan base.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {data.escenarios.map((e, i) => (
                <button
                  key={i}
                  onClick={() =>
                    setSelectedIdx(([a, b]) => (a === i ? [b, i] : b === i ? [i, a] : [a, i]))
                  }
                  className={`rounded border px-3 py-1 text-xs ${
                    selectedIdx.includes(i)
                      ? 'border-oliva-900 bg-oliva-900 text-crema'
                      : 'border-oliva/20 bg-white text-oliva-700'
                  }`}
                >
                  {e.nombre}
                </button>
              ))}
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
              <PanelEscenario titulo="Plan BASE" resumen={data.base} />
              {selectedIdx.map((idx, k) => {
                const e = data.escenarios[idx];
                return (
                  <PanelEscenario
                    key={k}
                    titulo={e.nombre}
                    descripcion={e.descripcion}
                    resumen={e.resumen}
                    deltaTir={e.deltas.tir_pp}
                    deltaVanPct={e.deltas.van_pct}
                    base={data.base}
                  />
                );
              })}
            </div>
          </section>

          <section>
            <h2 className="font-serif text-xl text-oliva-900">Tabla comparativa completa</h2>
            <div className="mt-3 overflow-x-auto rounded-lg border border-oliva/10 bg-white">
              <table className="w-full text-sm">
                <thead className="bg-oliva-50 text-xs uppercase tracking-wide text-oliva-600">
                  <tr>
                    <th className="px-3 py-2 text-left">Escenario</th>
                    <th className="px-3 py-2 text-right">TIR</th>
                    <th className="px-3 py-2 text-right">Δ TIR (pp)</th>
                    <th className="px-3 py-2 text-right">VAN</th>
                    <th className="px-3 py-2 text-right">Δ VAN (%)</th>
                    <th className="px-3 py-2 text-right">Payback</th>
                    <th className="px-3 py-2 text-right">EBITDA margin</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-oliva/10 bg-oliva-50/50">
                    <td className="px-3 py-2 font-medium">Plan BASE</td>
                    <td className="px-3 py-2 text-right">{pct(data.base.kpis.tir)}</td>
                    <td className="px-3 py-2 text-right">—</td>
                    <td className="px-3 py-2 text-right">${fmt(data.base.kpis.van)}</td>
                    <td className="px-3 py-2 text-right">—</td>
                    <td className="px-3 py-2 text-right">{data.base.kpis.payback_meses ?? '—'} mes</td>
                    <td className="px-3 py-2 text-right">{pct(data.base.kpis.ebitda_margin)}</td>
                  </tr>
                  {data.escenarios.map((e, i) => (
                    <tr key={i} className="border-t border-oliva/5">
                      <td className="px-3 py-2 font-medium">{e.nombre}</td>
                      <td className="px-3 py-2 text-right">{pct(e.resumen.kpis.tir)}</td>
                      <td
                        className={`px-3 py-2 text-right ${
                          (e.deltas.tir_pp ?? 0) < 0 ? 'text-borgoña' : 'text-oliva-700'
                        }`}
                      >
                        {e.deltas.tir_pp !== null ? e.deltas.tir_pp.toFixed(2) : '—'}
                      </td>
                      <td className="px-3 py-2 text-right">${fmt(e.resumen.kpis.van)}</td>
                      <td
                        className={`px-3 py-2 text-right ${
                          (e.deltas.van_pct ?? 0) < 0 ? 'text-borgoña' : 'text-oliva-700'
                        }`}
                      >
                        {e.deltas.van_pct !== null ? `${e.deltas.van_pct.toFixed(1)}%` : '—'}
                      </td>
                      <td className="px-3 py-2 text-right">{e.resumen.kpis.payback_meses ?? '—'} mes</td>
                      <td className="px-3 py-2 text-right">{pct(e.resumen.kpis.ebitda_margin)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function PanelEscenario({
  titulo,
  descripcion,
  resumen,
  deltaTir,
  deltaVanPct,
  base,
}: {
  titulo: string;
  descripcion?: string | null;
  resumen: ResumenAno;
  deltaTir?: number | null;
  deltaVanPct?: number | null;
  base?: ResumenAno;
}) {
  return (
    <div className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
      <h3 className="font-medium text-oliva-900">{titulo}</h3>
      {descripcion && <p className="mt-1 text-xs text-oliva-600">{descripcion}</p>}
      <dl className="mt-3 space-y-2 text-sm">
        <Row label="TIR proyecto" value={pct(resumen.kpis.tir)} delta={deltaTir ? `${deltaTir.toFixed(1)} pp` : undefined} negative={(deltaTir ?? 0) < 0} />
        <Row label="VAN" value={`$${fmt(resumen.kpis.van)}`} delta={deltaVanPct ? `${deltaVanPct.toFixed(1)}%` : undefined} negative={(deltaVanPct ?? 0) < 0} />
        <Row label="Payback" value={`${resumen.kpis.payback_meses ?? '—'} meses`} />
        <Row label="EBITDA margin" value={pct(resumen.kpis.ebitda_margin)} />
        <Row label="Ratio CapEx/Ventas" value={pct(resumen.kpis.capex_ratio)} />
      </dl>
      <div className="mt-3 border-t border-oliva/10 pt-3">
        <h4 className="text-xs uppercase tracking-wide text-oliva-600">Ingresos por año</h4>
        <div className="mt-1 flex justify-between text-xs">
          {resumen.ingresos_anuales.map((v, i) => (
            <span key={i} className="text-oliva-700">
              A{i + 1}: ${fmt(v / 1e6)}M
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, delta, negative }: { label: string; value: string; delta?: string; negative?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-oliva-600">{label}</dt>
      <dd className="flex items-baseline gap-2">
        <span className="font-medium text-oliva-900">{value}</span>
        {delta && (
          <span className={`text-xs ${negative ? 'text-borgoña' : 'text-oliva-400'}`}>({delta})</span>
        )}
      </dd>
    </div>
  );
}
