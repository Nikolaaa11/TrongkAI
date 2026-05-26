'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Snap = {
  plan: { kpis: { tir: number | null; van: number; payback_meses: number | null; ebitda_margin_promedio: number } };
  valuation: { ev_base_clp: number; moic: number };
  readiness_score: { score_total: number; interpretacion: string } | null;
  data_room: { pct_avance: number; completos: number; total: number } | null;
  variables_matrix: { pct_cubierto: number; total: number; PD: number; OK_PROVISORIO: number; OK_VALIDADO: number } | null;
  decisiones: {
    top_5: any[];
    total_acciones: number;
    uplift_potencial_readiness: number;
    quick_wins: any[];
  } | null;
  alertas: {
    total: number;
    criticas: number;
    altas: number;
    medias: number;
    alertas: { titulo: string; nivel: string; tipo: string; accion_sugerida: string; link: string }[];
  } | null;
  coherencia: { total_gaps: number; sinergia_total: number; gaps_coherentes: any[] } | null;
  carbon_footprint: { baseline: { emisiones_netas_5y_ton: number; es_carbono_negativo: boolean } };
  compliance_rep: { vigentes: number; total_hitos: number; cercanas: number };
  macro_chile: { dolar_clp?: number; uf_clp?: number; tpm_pct?: number };
  monte_carlo_integrado: { prob_tir_supera_wacc: number };
};

const NIVEL_COLOR: Record<string, string> = {
  critica: 'bg-red-50 text-red-600 ring-red-200',
  alta: 'bg-orange-50 text-orange-600 ring-orange-200',
  media: 'bg-yellow-50 text-yellow-700 ring-yellow-200',
  baja: 'bg-brand-50 text-brand ring-brand/20',
  info: 'bg-ink-50 text-ink-600 ring-ink-100',
};

export default function ComandoPage() {
  const [snap, setSnap] = useState<Snap | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    void cargar();
  }, []);

  async function cargar() {
    setLoading(true);
    setErr(null);
    try {
      const r = await fetch(`${ENGINE_URL}/api/snapshot`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setSnap(await r.json());
      setLastUpdate(new Date());
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  if (loading && !snap) {
    return (
      <div className="space-y-6">
        <div className="apple-card text-center text-ink-400">Cargando Centro de Mando...</div>
      </div>
    );
  }

  if (!snap) {
    return <div className="apple-card text-red-600">{err}</div>;
  }

  const topAccion = snap.decisiones?.top_5?.[0];
  const topAlerta = snap.alertas?.alertas?.[0];
  const topGap = snap.coherencia?.gaps_coherentes?.[0];

  const tir = (snap.plan.kpis.tir ?? 0) * 100;
  const van = snap.plan.kpis.van;
  const score = snap.readiness_score?.score_total ?? 0;
  const drAvance = snap.data_room?.pct_avance ?? 0;
  const matrizCob = snap.variables_matrix?.pct_cubierto ?? 0;
  const probWacc = (snap.monte_carlo_integrado?.prob_tir_supera_wacc ?? 0) * 100;

  return (
    <div className="space-y-6">
      {/* Header con timestamp */}
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
          <div>
            <h1 className="font-serif text-3xl text-ink">Centro de Mando</h1>
            <p className="mt-1 text-sm text-ink-400">
              Cockpit ejecutivo · todo el estado del proyecto en una página
              {lastUpdate && (
                <span className="ml-3 inline-flex items-center gap-1 text-xs">
                  <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-brand" />
                  Live · {lastUpdate.toLocaleTimeString('es-CL')}
                </span>
              )}
            </p>
          </div>
        </div>
        <button onClick={cargar} disabled={loading} className="btn-apple btn-apple-ghost text-xs">
          {loading ? 'Recargando...' : '↻ Refresh'}
        </button>
      </header>

      {/* HERO: Score + TIR + VAN + EV en grande */}
      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <BigKPI label="Investment Readiness" value={`${score.toFixed(0)}`} unit="/100" tone={score >= 80 ? 'ok' : score >= 60 ? 'warn' : 'bad'} sub={snap.readiness_score?.interpretacion?.slice(0, 30)} link="/readiness" />
        <BigKPI label="TIR Proyecto" value={`${tir.toFixed(1)}`} unit="%" tone={tir >= 25 ? 'ok' : tir >= 15 ? 'warn' : 'bad'} sub={`Hurdle 15%`} link="/plan" />
        <BigKPI label="VAN @ WACC 18%" value={`$${(van / 1e9).toFixed(1)}`} unit="B CLP" tone={van > 0 ? 'ok' : 'bad'} sub="60 meses descontados" link="/plan" />
        <BigKPI label="EV exit año 5" value={`$${(snap.valuation.ev_base_clp / 1e9).toFixed(0)}`} unit="B CLP" tone="ok" sub={`MOIC ${snap.valuation.moic.toFixed(1)}×`} link="/dashboard-directorio" />
      </section>

      {/* PRÓXIMA ACCIÓN — DECISIÓN del Engine */}
      {topAccion && (
        <section className="rounded-appleXl bg-brand p-8 text-white">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-white/80">
                🎯 Próxima acción recomendada (Decision Engine)
              </div>
              <h2 className="mt-2 text-2xl font-semibold tracking-apple md:text-3xl">{topAccion.titulo}</h2>
              <p className="mt-2 text-white/85">{topAccion.accion_concreta}</p>
              <div className="mt-4 flex flex-wrap gap-4 text-sm text-white/85">
                <span>👤 <strong className="text-white">{topAccion.owner}</strong></span>
                <span>📈 Uplift Readiness: <strong className="text-white">+{topAccion.uplift_readiness} pts</strong></span>
                <span>⚡ Quick-win: <strong className="text-white">{topAccion.quick_win}/100</strong></span>
              </div>
            </div>
            <Link href="/decisiones" className="shrink-0 rounded-full bg-white px-4 py-2 text-sm font-medium text-brand transition hover:scale-105">
              Ver todas →
            </Link>
          </div>
        </section>
      )}

      {/* ALERTAS ACTIVAS */}
      {snap.alertas && snap.alertas.total > 0 && (
        <section className="apple-card">
          <div className="flex items-baseline justify-between">
            <h2 className="text-xl font-semibold tracking-apple text-ink">
              🚨 Alertas activas ({snap.alertas.total})
            </h2>
            <div className="text-sm text-ink-400">
              {snap.alertas.criticas > 0 && <span className="text-red-600 font-semibold">{snap.alertas.criticas} críticas</span>}
              {snap.alertas.altas > 0 && <span className="ml-2 text-orange-600">· {snap.alertas.altas} altas</span>}
            </div>
          </div>
          <div className="mt-4 space-y-2">
            {snap.alertas.alertas.slice(0, 4).map((a, idx) => (
              <Link key={idx} href={a.link || '#'} className="block rounded-lg border border-ink-100 bg-white p-3 transition hover:bg-ink-50">
                <div className="flex items-start gap-3">
                  <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${NIVEL_COLOR[a.nivel]}`}>
                    {a.nivel}
                  </span>
                  <div className="flex-1">
                    <div className="font-medium text-ink">{a.titulo}</div>
                    <div className="mt-0.5 text-xs text-ink-600">{a.accion_sugerida}</div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* PROGRESO DEL MODELO — 3 barras */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <ProgresoCard
          label="Readiness Score"
          pct={score}
          detalle={snap.readiness_score?.interpretacion ?? '—'}
          link="/readiness"
        />
        <ProgresoCard
          label="Avance Data Room"
          pct={drAvance}
          detalle={`${snap.data_room?.completos ?? 0} de ${snap.data_room?.total ?? 0} items DD`}
          link="/data-room"
        />
        <ProgresoCard
          label="Matriz Variables cubierta"
          pct={matrizCob}
          detalle={`${snap.variables_matrix?.OK_PROVISORIO ?? 0} OK* + ${snap.variables_matrix?.OK_VALIDADO ?? 0} OK validados de ${snap.variables_matrix?.total ?? 0}`}
          link="/variables"
        />
      </section>

      {/* GRID inferior: Top Gap + Quick Wins + Macro + Compliance */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Top Gap coherencia */}
        {topGap && (
          <div className="apple-card">
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-orange-600">
              🔥 Gap coherente top (sinergia {topGap.sinergia})
            </div>
            <h3 className="mt-2 text-lg font-semibold text-ink">{topGap.descripcion.slice(0, 90)}</h3>
            <p className="mt-2 text-sm text-ink-600">{topGap.accion_recomendada}</p>
            <Link href="/coherencia" className="mt-3 inline-block text-xs font-medium text-brand">Ver coherencia →</Link>
          </div>
        )}

        {/* Quick wins */}
        {snap.decisiones?.quick_wins && snap.decisiones.quick_wins.length > 0 && (
          <div className="apple-card bg-brand-50 ring-1 ring-brand/20">
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
              ⚡ Quick wins disponibles ({snap.decisiones.quick_wins.length})
            </div>
            <h3 className="mt-2 text-lg font-semibold text-ink">{snap.decisiones.quick_wins[0].titulo}</h3>
            <p className="mt-2 text-sm text-ink-600">{snap.decisiones.quick_wins[0].owner}</p>
            <Link href="/decisiones" className="mt-3 inline-block text-xs font-medium text-brand">Ver todas →</Link>
          </div>
        )}

        {/* Macro Chile */}
        <div className="apple-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">
            🇨🇱 Macro Chile (live)
          </div>
          <div className="mt-2 grid grid-cols-3 gap-3">
            <div>
              <div className="text-[10px] uppercase tracking-wider text-ink-400">USD/CLP</div>
              <div className="tabular text-xl font-semibold text-ink">${snap.macro_chile?.dolar_clp?.toFixed(0) ?? '—'}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-ink-400">UF</div>
              <div className="tabular text-xl font-semibold text-ink">${(snap.macro_chile?.uf_clp ?? 0).toLocaleString('es-CL')}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-wider text-ink-400">TPM</div>
              <div className="tabular text-xl font-semibold text-ink">{snap.macro_chile?.tpm_pct?.toFixed(1) ?? '—'}%</div>
            </div>
          </div>
          <Link href="/macro" className="mt-3 inline-block text-xs font-medium text-brand">Ver macro completo →</Link>
        </div>

        {/* Compliance */}
        <div className="apple-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">
            📜 Compliance Ley REP
          </div>
          <div className="mt-2 flex items-baseline gap-4">
            <div>
              <div className="tabular text-2xl font-semibold text-brand">{snap.compliance_rep.vigentes}</div>
              <div className="text-[10px] uppercase tracking-wider text-ink-400">vigentes</div>
            </div>
            <div>
              <div className="tabular text-2xl font-semibold text-orange-600">{snap.compliance_rep.cercanas}</div>
              <div className="text-[10px] uppercase tracking-wider text-ink-400">cercanas</div>
            </div>
            <div>
              <div className="tabular text-2xl font-semibold text-ink-400">{snap.compliance_rep.total_hitos}</div>
              <div className="text-[10px] uppercase tracking-wider text-ink-400">total</div>
            </div>
          </div>
          <Link href="/compliance" className="mt-3 inline-block text-xs font-medium text-brand">Ver timeline REP →</Link>
        </div>
      </section>

      {/* Pipeline LP */}
      <PipelineLPCard />

      {/* ESG + Probabilidad MC */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className={`apple-card ${snap.carbon_footprint.baseline.es_carbono_negativo ? 'bg-brand-50 ring-1 ring-brand/20' : 'bg-orange-50 ring-1 ring-orange-200'}`}>
          <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
            🌱 ESG · Huella de carbono
          </div>
          <div className="mt-2 flex items-baseline gap-3">
            <div className={`tabular text-4xl font-semibold ${snap.carbon_footprint.baseline.es_carbono_negativo ? 'text-brand' : 'text-orange-600'}`}>
              {(snap.carbon_footprint.baseline.emisiones_netas_5y_ton / 1000).toFixed(1)}k
            </div>
            <div className="text-sm text-ink-400">ton CO₂eq · 5y</div>
          </div>
          <p className="mt-2 text-sm text-ink-600">
            {snap.carbon_footprint.baseline.es_carbono_negativo
              ? '✓ Proyecto carbono negativo. Apto para fondos ESG europeos.'
              : '⚠ Emisiones positivas. Implementar BECCS o renovables.'}
          </p>
          <Link href="/carbono" className="mt-3 inline-block text-xs font-medium text-brand">Ver LCA →</Link>
        </div>

        <div className="apple-card">
          <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">
            🎲 Monte Carlo · Robustez
          </div>
          <div className="mt-2 flex items-baseline gap-3">
            <div className="tabular text-4xl font-semibold text-ink">{probWacc.toFixed(0)}%</div>
            <div className="text-sm text-ink-400">prob. TIR &gt; WACC</div>
          </div>
          <p className="mt-2 text-sm text-ink-600">Basado en 300 simulaciones con riesgo climático.</p>
          <Link href="/plan" className="mt-3 inline-block text-xs font-medium text-brand">Ver Monte Carlo →</Link>
        </div>
      </section>

      {/* Footer con LP Pack ZIP */}
      <section className="rounded-appleXl bg-ink-50 p-6 text-center">
        <h3 className="text-lg font-semibold text-ink">¿Listo para mostrarlo a un LP?</h3>
        <p className="mt-1 text-sm text-ink-400">
          Descarga el LP Pack ZIP — 90KB con PDF + JSONs + README. Live data al momento.
        </p>
        <div className="mt-4 flex flex-wrap justify-center gap-3">
          <a
            href={`${ENGINE_URL}/api/lp-pack.zip`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-apple text-sm"
          >
            📦 LP Pack ZIP
          </a>
          <a
            href={`${ENGINE_URL}/api/tearsheet.pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-apple btn-apple-ghost text-sm"
          >
            📄 Solo PDF
          </a>
        </div>
      </section>
    </div>
  );
}

function BigKPI({ label, value, unit, tone, sub, link }: {
  label: string; value: string; unit: string; tone: 'ok' | 'warn' | 'bad'; sub?: string; link?: string;
}) {
  const cls = tone === 'ok' ? 'text-brand' : tone === 'warn' ? 'text-orange-600' : 'text-red-600';
  const ringCls = tone === 'ok' ? 'ring-brand/20' : tone === 'warn' ? 'ring-orange-200' : 'ring-red-200';
  const inner = (
    <>
      <div className="text-[10px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className="mt-1 flex items-baseline gap-1">
        <div className={`tabular text-3xl font-semibold ${cls}`}>{value}</div>
        <div className="text-sm text-ink-400">{unit}</div>
      </div>
      {sub && <div className="text-[11px] text-ink-400">{sub}</div>}
    </>
  );
  if (link) {
    return (
      <Link href={link} className={`apple-card ring-1 ${ringCls} transition hover:scale-[1.02]`}>
        {inner}
      </Link>
    );
  }
  return <div className={`apple-card ring-1 ${ringCls}`}>{inner}</div>;
}

function PipelineLPCard() {
  const [data, setData] = useState<{ resumen: { ticket_pipeline_usd: number; ticket_ponderado_usd: number; objetivo_usd: number; pct_objetivo_ponderado: number; total_lps: number; proximas_acciones_7d: number; por_etapa: Record<string, number> } } | null>(null);
  useEffect(() => {
    fetch(`${ENGINE_URL}/lp/pipeline`).then(r => r.ok && r.json()).then(setData).catch(() => {});
  }, []);
  if (!data) return null;
  const r = data.resumen;
  return (
    <section className="apple-card">
      <div className="flex items-baseline justify-between">
        <h2 className="text-xl font-semibold tracking-apple text-ink">💼 Pipeline LP (CRM)</h2>
        <Link href="/pipeline-lp" className="text-xs font-medium text-brand">Ver kanban →</Link>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-ink-400">Pipeline total</div>
          <div className="tabular mt-1 text-2xl font-semibold text-ink">${(r.ticket_pipeline_usd / 1e6).toFixed(1)}M</div>
          <div className="text-[11px] text-ink-400">{r.total_lps} LPs activos</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-ink-400">Ponderado por prob.</div>
          <div className="tabular mt-1 text-2xl font-semibold text-brand">${(r.ticket_ponderado_usd / 1e6).toFixed(1)}M</div>
          <div className="text-[11px] text-ink-400">{r.pct_objetivo_ponderado.toFixed(0)}% del target</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-ink-400">Objetivo round</div>
          <div className="tabular mt-1 text-2xl font-semibold text-ink">${(r.objetivo_usd / 1e6).toFixed(0)}M</div>
          <div className="text-[11px] text-ink-400">USD target</div>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-wider text-ink-400">Acciones próx 7d</div>
          <div className="tabular mt-1 text-2xl font-semibold text-orange-600">{r.proximas_acciones_7d}</div>
          <div className="text-[11px] text-ink-400">tareas vencen</div>
        </div>
      </div>
      <div className="mt-4 flex gap-1 text-[10px]">
        {(['prospect', 'contactado', 'reunion', 'dd', 'comprometido', 'ganado'] as const).map((e) => (
          <div key={e} className="flex-1 rounded bg-ink-50 px-2 py-1 text-center">
            <div className="text-ink-400">{e}</div>
            <div className="tabular font-semibold text-ink">{r.por_etapa[e] ?? 0}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function ProgresoCard({ label, pct, detalle, link }: { label: string; pct: number; detalle: string; link: string }) {
  const tone = pct >= 75 ? 'brand' : pct >= 50 ? 'orange' : 'red';
  const colorMap = { brand: 'bg-brand', orange: 'bg-orange-400', red: 'bg-red-400' };
  return (
    <Link href={link} className="apple-card block transition hover:scale-[1.02]">
      <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">{label}</div>
      <div className="mt-2 tabular text-3xl font-semibold text-ink">{pct.toFixed(0)}%</div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-ink-100">
        <div className={`h-full ${colorMap[tone as keyof typeof colorMap]} transition-all`} style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-2 text-xs text-ink-400">{detalle}</div>
    </Link>
  );
}
