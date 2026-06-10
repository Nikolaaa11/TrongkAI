'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ConectadoCon } from '@/components/ConectadoCon';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

// Board Pack imprimible. Fuente UNICA: /api/snapshot (1 GET cacheado 60s).
// Antes disparaba 6 POST pesados (incl. Monte Carlo 1.500 corridas) por visita.
type Snap = {
  generated_at: string;
  plan: { kpis: { tir: number | null; van: number; payback_meses: number | null; ebitda_margin_promedio?: number } };
  valuation: { ebitda_ano5_clp: number; ev_base_clp: number; ev_rango_clp: [number, number]; moic: number; multiplo_base: number };
  escenarios_estrategicos: { escenarios: { nombre: string; capex_total: number; tir: number | null; van: number; payback_meses: number | null }[]; recomendacion?: { elegido: string; razon: string } };
  monte_carlo_integrado: { n_runs: number; tir_p5: number; tir_p50: number; tir_p95: number; prob_tir_supera_wacc: number; prob_van_positivo: number };
  top_3_tornado: { variable: string; tir_baja: number; tir_alta: number; magnitud_tir: number }[];
  readiness_score: { score_total: number; interpretacion: string } | null;
  carbon_footprint: { baseline: { emisiones_netas_5y_ton: number; es_carbono_negativo: boolean } };
  compliance_rep: { vigentes: number; total_hitos: number; cercanas: number };
  macro_chile: { dolar_clp?: number; uf_clp?: number; tpm_pct?: number };
};

const pctFmt = (x: number | null | undefined) => (x == null ? '—' : `${(x * 100).toFixed(1)}%`);
const bFmt = (x: number) => `$${(x / 1e9).toFixed(1)}B`;

export default function DashboardDirectorioPage() {
  const [snap, setSnap] = useState<Snap | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/api/snapshot`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then(setSnap)
      .catch((e) => setErr(String(e)));
  }, []);

  if (err) return <div className="apple-card text-red-600">{err}</div>;
  if (!snap) return <p className="text-ink-400">Generando Board Pack…</p>;

  const k = snap.plan.kpis;
  const v = snap.valuation;
  const mc = snap.monte_carlo_integrado;
  const esc = snap.escenarios_estrategicos?.escenarios ?? [];
  const reco = snap.escenarios_estrategicos?.recomendacion;
  const maxMag = Math.max(...(snap.top_3_tornado ?? []).map((t) => t.magnitud_tir), 0.001);

  return (
    <div className="space-y-10">
      {/* Header + acciones (ocultas al imprimir) */}
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0 print:hidden" />
          <div>
            <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Board Pack</p>
            <h1 className="mt-1 font-serif text-3xl text-ink">Dashboard Directorio</h1>
            <p className="mt-1 text-sm text-ink-400">
              Plan industrial 5 años · generado {snap.generated_at?.slice(0, 16).replace('T', ' ')} UTC · fuente única: snapshot del motor
            </p>
          </div>
        </div>
        <div className="flex gap-2 print:hidden">
          <button onClick={() => window.print()} className="btn-apple btn-apple-ghost text-xs">🖨 Imprimir</button>
          <a href={`${ENGINE_URL}/api/tearsheet.pdf`} target="_blank" rel="noopener noreferrer" className="btn-apple text-xs">📄 Tearsheet PDF</a>
        </div>
      </header>

      {/* KPIs hero */}
      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KPI label="TIR Proyecto" value={pctFmt(k.tir)} sub="hurdle 15% · WACC 18%" />
        <KPI label="VAN @ 18%" value={bFmt(k.van)} sub="60 meses descontados" />
        <KPI label="Payback" value={k.payback_meses ? `${k.payback_meses} meses` : '—'} sub="simple, sin descontar" />
        <KPI label="Readiness" value={`${(snap.readiness_score?.score_total ?? 0).toFixed(0)}/100`} sub={snap.readiness_score?.interpretacion?.split('—')[0] ?? ''} />
      </section>

      {/* Escenarios estratégicos */}
      <section>
        <h2 className="mb-3 text-xl font-semibold tracking-apple text-ink">Escenarios estratégicos</h2>
        <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-ink-50/40 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-4 py-3 text-left">Escenario</th>
                <th className="px-4 py-3 text-right">CAPEX 5y</th>
                <th className="px-4 py-3 text-right">TIR</th>
                <th className="px-4 py-3 text-right">VAN</th>
                <th className="px-4 py-3 text-right">Payback</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-50">
              {esc.map((e) => (
                <tr key={e.nombre} className={reco?.elegido === e.nombre ? 'bg-brand-50/50' : ''}>
                  <td className="px-4 py-3 font-semibold">
                    {e.nombre}
                    {reco?.elegido === e.nombre && <span className="ml-2 rounded-full bg-brand px-2 py-0.5 text-[10px] font-bold text-white">RECOMENDADO</span>}
                  </td>
                  <td className="px-4 py-3 text-right tabular">{bFmt(e.capex_total)}</td>
                  <td className={`px-4 py-3 text-right tabular font-semibold ${(e.tir ?? 0) >= 0.18 ? 'text-brand' : 'text-orange-600'}`}>{pctFmt(e.tir)}</td>
                  <td className={`px-4 py-3 text-right tabular ${e.van > 0 ? '' : 'text-orange-600'}`}>{bFmt(e.van)}</td>
                  <td className="px-4 py-3 text-right tabular">{e.payback_meses ? `${e.payback_meses} m` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {reco && <p className="mt-2 text-sm text-ink-500">{reco.razon}</p>}
      </section>

      {/* Valuation + Monte Carlo lado a lado */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="apple-card">
          <h3 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-ink-400">Valuación exit año 5</h3>
          <div className="mt-2 flex items-baseline gap-3">
            <span className="tabular text-4xl font-semibold text-ink">{bFmt(v.ev_base_clp)}</span>
            <span className="text-sm text-ink-400">{v.multiplo_base.toFixed(1)}× EBITDA · MOIC {v.moic.toFixed(1)}×</span>
          </div>
          <div className="mt-3 text-sm text-ink-600 tabular">
            Rango: <span className="text-orange-600">{bFmt(v.ev_rango_clp[0])}</span>
            {' — '}<span className="font-semibold">{bFmt(v.ev_base_clp)}</span>
            {' — '}<span className="text-brand">{bFmt(v.ev_rango_clp[1])}</span>
          </div>
          <p className="mt-2 text-xs text-ink-400">EBITDA año 5: {bFmt(v.ebitda_ano5_clp)} · múltiplos comparables circular economy</p>
        </div>
        <div className="apple-card">
          <h3 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-ink-400">Monte Carlo · {mc.n_runs} corridas con clima</h3>
          <div className="mt-2 flex items-baseline gap-3">
            <span className="tabular text-4xl font-semibold text-ink">{Math.round(mc.prob_tir_supera_wacc * 100)}%</span>
            <span className="text-sm text-ink-400">prob. TIR &gt; WACC</span>
          </div>
          <div className="mt-3 flex gap-5 text-sm tabular">
            <span className="text-orange-600">P5 {pctFmt(mc.tir_p5)}</span>
            <span className="font-semibold text-ink">P50 {pctFmt(mc.tir_p50)}</span>
            <span className="text-brand">P95 {pctFmt(mc.tir_p95)}</span>
          </div>
          <p className="mt-2 text-xs text-ink-400">Histograma completo y stress tests en <Link href="/riesgo" className="text-brand underline">/riesgo</Link></p>
        </div>
      </section>

      {/* Tornado top 3 */}
      <section>
        <h2 className="mb-3 text-xl font-semibold tracking-apple text-ink">Qué mueve más la TIR (top 3)</h2>
        <div className="rounded-xl border border-ink-100 bg-white p-5 space-y-3">
          {(snap.top_3_tornado ?? []).map((t) => (
            <div key={t.variable} className="grid grid-cols-12 items-center gap-3 text-sm">
              <div className="col-span-3 font-medium capitalize">{t.variable.replace(/_/g, ' ')}</div>
              <div className="col-span-6">
                <div className="h-5 overflow-hidden rounded-full bg-ink-50">
                  <div className="h-full rounded-full bg-gradient-to-r from-orange-400 to-brand" style={{ width: `${(t.magnitud_tir / maxMag) * 100}%` }} />
                </div>
              </div>
              <div className="col-span-3 text-right tabular text-ink-600">
                {pctFmt(t.tir_baja)} → {pctFmt(t.tir_alta)}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Strip ESG / Compliance / Macro */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <KPI
          label="Carbono 5y"
          value={`${(snap.carbon_footprint.baseline.emisiones_netas_5y_ton / 1000).toFixed(0)}k ton`}
          sub={snap.carbon_footprint.baseline.es_carbono_negativo ? 'CO₂eq evitado — carbono negativo' : 'CO₂eq neto'}
        />
        <KPI
          label="Compliance REP"
          value={`${snap.compliance_rep.vigentes}/${snap.compliance_rep.total_hitos} hitos`}
          sub={`${snap.compliance_rep.cercanas} con vencimiento cercano`}
        />
        <KPI
          label="Macro Chile"
          value={snap.macro_chile?.dolar_clp ? `$${snap.macro_chile.dolar_clp.toFixed(0)} CLP/USD` : '—'}
          sub={`UF ${snap.macro_chile?.uf_clp?.toLocaleString('es-CL') ?? '—'} · TPM ${snap.macro_chile?.tpm_pct ?? '—'}%`}
        />
      </section>

      <div className="print:hidden">
        <ConectadoCon links={[
          { href: '/comando', label: 'Centro de Mando', razon: 'Cockpit operacional diario' },
          { href: '/plan', label: 'Plan 5 años', razon: 'EERR mensual + tornado completo' },
          { href: '/riesgo', label: 'Riesgo Integrado', razon: 'Monte Carlo + clima en detalle' },
          { href: '/readiness', label: 'Readiness', razon: 'Madurez para invertir' },
        ]} />
      </div>
    </div>
  );
}

function KPI({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="apple-card">
      <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">{label}</div>
      <div className="tabular mt-1 text-2xl font-semibold text-ink">{value}</div>
      {sub && <div className="mt-0.5 text-[12px] text-ink-400">{sub}</div>}
    </div>
  );
}
