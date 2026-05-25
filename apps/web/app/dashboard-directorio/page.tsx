'use client';

import { useEffect, useState } from 'react';
import { HistogramaChart, type HistogramaBin } from '@/components/HistogramaChart';
import { SankeyChart, type SankeyData } from '@/components/SankeyChart';
import { TornadoChart, type TornadoEntry } from '@/components/TornadoChart';
import { seed, stats, suppliersActivos } from '@/lib/seed-data';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type PlanData = {
  kpis: {
    tir_proyecto_anual: number | null;
    van: number;
    payback_meses: number | null;
    ebitda_margin_promedio: number;
    ratio_capex_ventas: number;
  };
  por_marca: Record<string, { ingresos_anuales: number[]; tam_clp_anual?: number; penetracion_pct_ano5?: number }>;
  resumen_anual: { ano: number; ingresos: number; ebitda: number; ebitda_margin: number; capex: number }[];
  nwc_anuales?: number[];
  delta_nwc_anuales?: number[];
};

type Escenarios = {
  escenarios: { nombre: string; volumen_objetivo_ton_ano: number; capex_total: number; kpis: { tir: number; van: number; payback_meses: number | null } }[];
  recomendacion: { elegido: string; razon: string };
};

type Valuation = {
  ebitda_ano5_clp: number;
  multiple_base: number;
  multiple_low: number;
  multiple_high: number;
  ev_clp_base: number;
  ev_clp_low: number;
  ev_clp_high: number;
  moic_estimado: number | null;
  capex_total_5y_clp: number;
};

type MonteCarlo = {
  n_runs: number;
  tir_p5: number | null;
  tir_p50: number | null;
  tir_p95: number | null;
  van_p5: number;
  van_p50: number;
  van_p95: number;
  prob_tir_supera_wacc: number;
  prob_van_positivo: number;
  histograma_tir?: HistogramaBin[];
};

const fmtB = (n: number) => `$${(n / 1e9).toFixed(2)}B`;
const fmtPct = (n: number | null | undefined) =>
  n === null || n === undefined ? '—' : `${(n * 100).toFixed(2)}%`;

export default function DashboardDirectorioPage() {
  const [plan, setPlan] = useState<PlanData | null>(null);
  const [escenarios, setEscenarios] = useState<Escenarios | null>(null);
  const [valuation, setValuation] = useState<Valuation | null>(null);
  const [montecarlo, setMontecarlo] = useState<MonteCarlo | null>(null);
  const [tornado, setTornado] = useState<TornadoEntry[] | null>(null);
  const [sankey, setSankey] = useState<SankeyData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void cargarTodo();
  }, []);

  async function cargarTodo() {
    setLoading(true);
    setErr(null);
    try {
      const [planR, escR, valR, mcR, torR, sankeyR] = await Promise.all([
        fetch(`${ENGINE_URL}/plan`, {
          method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({}),
        }).then((r) => r.json()),
        fetch(`${ENGINE_URL}/plan/escenarios-estrategicos`).then((r) => r.json()),
        fetch(`${ENGINE_URL}/plan/valuation`, {
          method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({}),
        }).then((r) => r.json()),
        fetch(`${ENGINE_URL}/plan/monte-carlo`, {
          method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ n_runs: 1500 }),
        }).then((r) => r.json()),
        fetch(`${ENGINE_URL}/plan/tornado`, {
          method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({}),
        }).then((r) => r.json()),
        fetch(`${ENGINE_URL}/mass-balance`, {
          method: 'POST', headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            mmpp_codigo: 'ALPERUJO', humedad_inicial_pct: 0.65, materia_solida_pct: 0.35,
            aceite_extraible_pct: 0.02, input_ton: 1000, mode: 'A',
          }),
        }).then((r) => r.json()),
      ]);
      setPlan(planR);
      setEscenarios(escR);
      setValuation(valR);
      setMontecarlo(mcR);
      setTornado(torR.tornado ?? torR);
      setSankey(sankeyR.sankey);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div className="p-8 text-oliva-600">Cargando dashboard del directorio...</div>;
  if (err) return <div className="p-8 text-borgoña">Error: {err}</div>;

  return (
    <div className="space-y-6 print:bg-white">
      <header className="border-b border-oliva/20 pb-4 print:border-b-2">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="font-serif text-3xl text-oliva-900">Dashboard Directorio · Trongkai 2026</h1>
            <p className="mt-1 text-sm text-oliva-600">
              Resumen ejecutivo del plan financiero, escenarios estratégicos, valoración y análisis de riesgo. Imprimible para reunión.
            </p>
          </div>
          <a
            href={`${ENGINE_URL}/api/tearsheet.pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="no-print rounded-lg border border-oliva-900 bg-oliva-900 px-4 py-2 text-sm font-medium text-crema transition hover:bg-oliva-700"
            download
          >
            📄 Descargar PDF tearsheet
          </a>
        </div>
      </header>

      {/* ===== KPIs grandes ===== */}
      {plan && (
        <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
          <BigKpi label="TIR Proyecto" value={fmtPct(plan.kpis.tir_proyecto_anual)} highlight />
          <BigKpi label="VAN @ WACC 18%" value={fmtB(plan.kpis.van)} />
          <BigKpi label="Payback" value={`${plan.kpis.payback_meses ?? '—'} meses`} />
          <BigKpi label="EBITDA margin" value={fmtPct(plan.kpis.ebitda_margin_promedio)} />
          <BigKpi label="CapEx/Ventas" value={fmtPct(plan.kpis.ratio_capex_ventas)} />
        </section>
      )}

      {/* ===== Valoración exit ===== */}
      {valuation && (
        <section className="rounded-lg border border-trigo/40 bg-trigo/5 p-4">
          <h2 className="font-serif text-lg text-oliva-900">Valoración exit año 5 (EV/EBITDA múltiplo)</h2>
          <div className="mt-3 grid grid-cols-2 gap-4 md:grid-cols-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-oliva-600">EBITDA año 5</div>
              <div className="text-xl font-semibold text-oliva-900">{fmtB(valuation.ebitda_ano5_clp)}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-oliva-600">EV base (9,6x)</div>
              <div className="text-xl font-semibold text-oliva-900">{fmtB(valuation.ev_clp_base)}</div>
              <div className="text-xs text-oliva-600">
                Rango: {fmtB(valuation.ev_clp_low)} – {fmtB(valuation.ev_clp_high)}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-oliva-600">CapEx total 5y</div>
              <div className="text-xl font-semibold text-oliva-900">{fmtB(valuation.capex_total_5y_clp)}</div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-oliva-600">MOIC base</div>
              <div className="text-xl font-semibold text-oliva-900">
                {valuation.moic_estimado ? `${valuation.moic_estimado.toFixed(1)}x` : '—'}
              </div>
            </div>
          </div>
          <p className="mt-2 text-xs text-oliva-600">
            Múltiplos: food processing global 9,6x (Damodaran 2026) · ingredientes funcionales 8-12x.
          </p>
        </section>
      )}

      {/* ===== Monte Carlo bandas confianza ===== */}
      {montecarlo && (
        <section className="rounded-lg border border-oliva/20 bg-oliva-50/30 p-4">
          <h2 className="font-serif text-lg text-oliva-900">Bandas de confianza Monte Carlo ({montecarlo.n_runs} corridas)</h2>
          <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-oliva-600">TIR P5 / P50 / P95</div>
              <div className="text-sm font-semibold text-oliva-900">
                {fmtPct(montecarlo.tir_p5)} / <span className="text-trigo">{fmtPct(montecarlo.tir_p50)}</span> / {fmtPct(montecarlo.tir_p95)}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-oliva-600">VAN P5 / P50 / P95</div>
              <div className="text-sm font-semibold text-oliva-900">
                {fmtB(montecarlo.van_p5)} / <span className="text-trigo">{fmtB(montecarlo.van_p50)}</span> / {fmtB(montecarlo.van_p95)}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-oliva-600">Prob. TIR &gt; WACC</div>
              <div className={`text-2xl font-bold ${montecarlo.prob_tir_supera_wacc > 0.7 ? 'text-oliva-900' : 'text-borgoña'}`}>
                {(montecarlo.prob_tir_supera_wacc * 100).toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-wide text-oliva-600">Prob. VAN &gt; 0</div>
              <div className={`text-2xl font-bold ${montecarlo.prob_van_positivo > 0.7 ? 'text-oliva-900' : 'text-borgoña'}`}>
                {(montecarlo.prob_van_positivo * 100).toFixed(1)}%
              </div>
            </div>
          </div>
          {montecarlo.histograma_tir && montecarlo.histograma_tir.length > 0 && (
            <div className="mt-4 rounded border border-oliva/10 bg-white p-2">
              <HistogramaChart
                bins={montecarlo.histograma_tir}
                p5={montecarlo.tir_p5}
                p50={montecarlo.tir_p50}
                p95={montecarlo.tir_p95}
                baseValue={plan?.kpis.tir_proyecto_anual ?? undefined}
                title="Distribución de TIR (con P5/P50/P95 y base)"
                height={240}
              />
            </div>
          )}
        </section>
      )}

      {/* ===== Tornado ===== */}
      {tornado && plan?.kpis.tir_proyecto_anual && (
        <section className="rounded-lg border border-oliva/10 bg-white p-3 shadow-sm">
          <TornadoChart entries={tornado} baseTir={plan.kpis.tir_proyecto_anual} height={280} />
        </section>
      )}

      {/* ===== Escenarios + Sankey side-by-side ===== */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {escenarios && (
          <div className="rounded-lg border border-oliva/10 bg-white p-4">
            <h2 className="font-serif text-lg text-oliva-900">3 escenarios estratégicos</h2>
            <table className="mt-3 w-full text-sm">
              <thead className="text-xs uppercase tracking-wide text-oliva-600">
                <tr>
                  <th className="text-left">Escenario</th>
                  <th className="text-right">CapEx</th>
                  <th className="text-right">TIR</th>
                  <th className="text-right">VAN</th>
                </tr>
              </thead>
              <tbody>
                {escenarios.escenarios.map((e) => {
                  const isRec = e.nombre === escenarios.recomendacion.elegido;
                  return (
                    <tr key={e.nombre} className={`border-t border-oliva/5 ${isRec ? 'bg-trigo/10 font-medium' : ''}`}>
                      <td className="py-1">
                        {e.nombre} {isRec && '★'}
                      </td>
                      <td className="py-1 text-right">{fmtB(e.capex_total)}</td>
                      <td className="py-1 text-right">{fmtPct(e.kpis.tir)}</td>
                      <td className="py-1 text-right">{fmtB(e.kpis.van)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="mt-2 text-xs text-oliva-600">{escenarios.recomendacion.razon}</p>
          </div>
        )}

        {sankey && (
          <div className="rounded-lg border border-oliva/10 bg-white p-3">
            <h2 className="font-serif text-lg text-oliva-900">Balance de masa alperujo (1.000 ton input)</h2>
            <SankeyChart data={sankey} height={260} />
          </div>
        )}
      </section>

      {/* ===== Marca + proveedores ===== */}
      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {plan?.por_marca && (
          <div className="rounded-lg border border-oliva/10 bg-white p-4">
            <h2 className="font-serif text-lg text-oliva-900">Desglose por marca</h2>
            <table className="mt-3 w-full text-sm">
              <thead className="text-xs uppercase tracking-wide text-oliva-600">
                <tr>
                  <th className="text-left">Marca</th>
                  <th className="text-right">Ingresos A5</th>
                  <th className="text-right">TAM</th>
                  <th className="text-right">Penetración</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(plan.por_marca).map(([marca, r]) => (
                  <tr key={marca} className="border-t border-oliva/5">
                    <td className="py-1 font-medium">Trongkai {marca}</td>
                    <td className="py-1 text-right">{fmtB(r.ingresos_anuales[4])}</td>
                    <td className="py-1 text-right">{r.tam_clp_anual ? fmtB(r.tam_clp_anual) : '—'}</td>
                    <td className="py-1 text-right">{r.penetracion_pct_ano5 ? `${(r.penetracion_pct_ano5 * 100).toFixed(2)}%` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="rounded-lg border border-oliva/10 bg-white p-4">
          <h2 className="font-serif text-lg text-oliva-900">
            Proveedores activos ({stats.suppliersActivos}/{stats.suppliersTotal})
          </h2>
          <table className="mt-3 w-full text-sm">
            <thead className="text-xs uppercase tracking-wide text-oliva-600">
              <tr>
                <th className="text-left">Proveedor</th>
                <th className="text-right">Km</th>
                <th className="text-right">Volumen</th>
                <th className="text-left">Caso</th>
              </tr>
            </thead>
            <tbody>
              {suppliersActivos().map((s) => (
                <tr key={s.nombre} className="border-t border-oliva/5">
                  <td className="py-1 font-medium">{s.nombre}</td>
                  <td className="py-1 text-right">{s.distanciaKm}</td>
                  <td className="py-1 text-right">{s.volumenAnualComprometidoTon.toLocaleString('es-CL')}t</td>
                  <td className="py-1 text-xs text-oliva-600">{s.casoLogistico.replace('_', ' ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-xs text-oliva-600">
            Cuota contractual {stats.volumenContratoTon.toLocaleString('es-CL')} ton — comprometido{' '}
            {((stats.volumenComprometidoActual / stats.volumenContratoTon) * 100).toFixed(1)}%.
          </p>
        </div>
      </section>

      <footer className="border-t border-oliva/10 pt-3 text-xs text-oliva-500 print:text-black">
        Generado {new Date().toLocaleString('es-CL')} · Trongkai Platform · "En la naturaleza no existen los residuos, solo recursos."
      </footer>
    </div>
  );
}

function BigKpi({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div
      className={`card-hover rounded-lg border p-4 ${
        highlight ? 'border-trigo/40 bg-trigo/5' : 'border-oliva/10 bg-white'
      }`}
    >
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">{label}</div>
      <div className={`tabular mt-1.5 text-3xl font-bold leading-tight ${highlight ? 'text-trigo' : 'text-oliva-900'}`}>
        {value}
      </div>
    </div>
  );
}
