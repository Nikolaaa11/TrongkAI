'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type CasoBond = {
  monto_bond_clp: number;
  tasa_base_anual: number;
  tasas_anuales_efectivas: number[];
  intereses_anuales: number[];
  spread_acumulado_bps_final: number;
  incumplimientos: {
    ano_evaluado: number;
    kpi: string;
    target: number;
    valor_real: number;
    step_up_bps: number;
    spread_acumulado_bps: number;
  }[];
  intereses_totales_clp: number;
  intereses_sin_stepup_clp: number;
  costo_extra_por_incumplimientos_clp: number;
  pct_costo_extra_vs_baseline: number;
};

type SlbResponse = {
  caso_optimista: CasoBond;
  caso_pesimista: CasoBond;
  delta_costo_clp: number;
  incentivo_esg_clp: number;
};

const fmtB = (n: number) => `$${(n / 1e9).toFixed(2)}B CLP`;
const fmtPct = (n: number) => `${(n * 100).toFixed(2)}%`;
const fmtBps = (bps: number) => `+${bps} bps`;

export default function SlbPage() {
  const [montoB, setMontoB] = useState(5);  // en billones CLP
  const [tasaBase, setTasaBase] = useState(0.085);
  const [plazo, setPlazo] = useState(7);
  const [data, setData] = useState<SlbResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void simular();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function simular() {
    setLoading(true);
    setErr(null);
    try {
      const r = await fetch(`${ENGINE_URL}/plan/slb-simulation`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          monto_clp: montoB * 1e9,
          tasa_base_anual: tasaBase,
          plazo_anos: plazo,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Sustainability-Linked Bond Calculator</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Simulador de bono ESG con 3 KPIs (toneladas CO₂ evitadas, cuota feed sostenible Chile, harina pescado
          sustituida). Cada KPI fallido suma 20-25 bps al spread (permanente).
          {' '}Mercado global SLB 2026: <a href="https://press.spglobal.com/2026-03-12-S-P-Global-Ratings-Forecasts-Global-Sustainable-Bond-Market-Will-Consolidate-In-2026-with-Issuance-Levels-at-800-900-billion" target="_blank" rel="noopener noreferrer" className="text-trigo hover:underline">USD 25B</a>.
        </p>
      </header>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm card-hover">
        <h2 className="font-medium text-oliva-900">Parámetros del bono</h2>
        <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-3">
          <SliderInput label="Monto (B CLP)" value={montoB} setter={setMontoB} min={1} max={20} step={0.5} suffix="B" />
          <SliderInput label="Tasa base anual" value={tasaBase} setter={setTasaBase} min={0.05} max={0.15} step={0.005} pct />
          <SliderInput label="Plazo (años)" value={plazo} setter={setPlazo} min={3} max={15} step={1} />
        </div>
        <button
          onClick={simular}
          className="mt-4 rounded bg-oliva-900 px-4 py-2 text-sm text-crema hover:bg-oliva-600 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Simulando...' : 'Recalcular'}
        </button>
        {err && <p className="mt-2 text-sm text-borgoña">{err}</p>}
      </section>

      {data && (
        <>
          <section className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Card
              label="Incentivo ESG"
              value={fmtB(data.incentivo_esg_clp)}
              sub={`+${data.caso_pesimista.spread_acumulado_bps_final} bps acumulados si todos los KPIs fallan`}
              highlight
            />
            <Card
              label="Intereses caso optimista"
              value={fmtB(data.caso_optimista.intereses_totales_clp)}
              sub={`Tasa estable ${fmtPct(data.caso_optimista.tasa_base_anual)}`}
              tone="ok"
            />
            <Card
              label="Intereses caso pesimista"
              value={fmtB(data.caso_pesimista.intereses_totales_clp)}
              sub={`Tasa final: ${fmtPct(data.caso_pesimista.tasas_anuales_efectivas[data.caso_pesimista.tasas_anuales_efectivas.length - 1])}`}
              tone="warn"
            />
          </section>

          <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <BondTable titulo="Caso optimista (KPIs cumplidos)" caso={data.caso_optimista} tone="ok" />
            <BondTable titulo="Caso pesimista (KPIs fallan)" caso={data.caso_pesimista} tone="warn" />
          </section>

          {data.caso_pesimista.incumplimientos.length > 0 && (
            <section className="rounded-lg border border-borgoña/30 bg-borgoña/5 p-4">
              <h3 className="font-medium text-borgoña">
                Incumplimientos detectados (caso pesimista): {data.caso_pesimista.incumplimientos.length}
              </h3>
              <table className="mt-2 w-full text-sm">
                <thead className="text-xs uppercase tracking-wide text-oliva-600">
                  <tr>
                    <th className="text-left">Año</th>
                    <th className="text-left">KPI</th>
                    <th className="text-right">Target</th>
                    <th className="text-right">Real</th>
                    <th className="text-right">Step-up</th>
                    <th className="text-right">Spread acum.</th>
                  </tr>
                </thead>
                <tbody>
                  {data.caso_pesimista.incumplimientos.map((inc, i) => (
                    <tr key={i} className="border-t border-borgoña/10">
                      <td className="py-1 font-medium">A{inc.ano_evaluado}</td>
                      <td className="py-1 text-xs">{inc.kpi}</td>
                      <td className="py-1 text-right tabular">{inc.target.toLocaleString('es-CL')}</td>
                      <td className="py-1 text-right tabular text-borgoña">{inc.valor_real.toLocaleString('es-CL')}</td>
                      <td className="py-1 text-right text-xs">{fmtBps(inc.step_up_bps)}</td>
                      <td className="py-1 text-right font-medium tabular">{fmtBps(inc.spread_acumulado_bps)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
            <strong>Cómo leerlo:</strong> el bono SLB ofrece <em>incentivo financiero</em> al cumplimiento de KPIs
            ESG. Si Trongkai entrega la trayectoria comprometida (toneladas CO₂ evitadas + cuota feed sostenible
            + harina pescado sustituida), paga la tasa base. Si falla cualquier KPI año a año, suma step-up
            permanente. Diseño basado en{' '}
            <a href="https://www.icmagroup.org/sustainable-finance/sustainability-linked-bond-principles-slbp/" target="_blank" rel="noopener noreferrer" className="text-trigo hover:underline">
              ICMA SLB Principles
            </a>.
          </section>
        </>
      )}
    </div>
  );
}

function BondTable({ titulo, caso, tone }: { titulo: string; caso: CasoBond; tone: 'ok' | 'warn' }) {
  return (
    <div className={`rounded-lg border bg-white p-3 ${tone === 'ok' ? 'border-oliva/20' : 'border-borgoña/30'}`}>
      <h3 className="text-sm font-medium text-oliva-900">{titulo}</h3>
      <table className="mt-2 w-full text-xs">
        <thead className="text-[10px] uppercase tracking-wide text-oliva-600">
          <tr>
            <th className="text-left">Año</th>
            <th className="text-right">Tasa efectiva</th>
            <th className="text-right">Intereses</th>
          </tr>
        </thead>
        <tbody>
          {caso.tasas_anuales_efectivas.map((t, i) => (
            <tr key={i} className="border-t border-oliva/5">
              <td className="py-1">A{i + 1}</td>
              <td className={`py-1 text-right tabular ${tone === 'warn' && t > caso.tasa_base_anual ? 'text-borgoña font-medium' : ''}`}>
                {fmtPct(t)}
              </td>
              <td className="py-1 text-right tabular">${(caso.intereses_anuales[i] / 1e9).toFixed(2)}B</td>
            </tr>
          ))}
          <tr className="border-t-2 border-oliva/10 bg-oliva-50/30">
            <td className="py-1 font-semibold">Total</td>
            <td />
            <td className="py-1 text-right font-semibold tabular">${(caso.intereses_totales_clp / 1e9).toFixed(2)}B</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

function SliderInput({
  label, value, setter, min, max, step, pct, suffix,
}: { label: string; value: number; setter: (v: number) => void; min: number; max: number; step: number; pct?: boolean; suffix?: string }) {
  return (
    <label className="block">
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">{label}</div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => setter(parseFloat(e.target.value))}
        className="mt-1 w-full"
      />
      <div className="tabular text-sm font-medium text-oliva-900">
        {pct ? `${(value * 100).toFixed(1)}%` : value}{suffix ?? ''}
      </div>
    </label>
  );
}

function Card({ label, value, sub, tone, highlight }: { label: string; value: string; sub?: string; tone?: 'ok' | 'warn'; highlight?: boolean }) {
  const cls = highlight ? 'border-trigo/40 bg-trigo/5' :
              tone === 'ok' ? 'border-oliva/20 bg-oliva-50/30' :
              tone === 'warn' ? 'border-borgoña/30 bg-borgoña/5' :
              'border-oliva/10 bg-white';
  return (
    <div className={`card-hover rounded-lg border p-4 ${cls}`}>
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">{label}</div>
      <div className="tabular mt-1 text-2xl font-bold text-oliva-900">{value}</div>
      {sub && <div className="mt-1 text-xs text-oliva-600">{sub}</div>}
    </div>
  );
}
