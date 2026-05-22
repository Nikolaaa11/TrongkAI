'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type FinancingResp = {
  estructura: {
    deuda_pct: number;
    tasa_deuda_anual: number;
    plazo_deuda_anos: number;
    tipo_amortizacion: string;
    tasa_equity_required: number;
  };
  capex_total_clp: number;
  monto_deuda_clp: number;
  monto_equity_clp: number;
  intereses_anual: number[];
  principal_anual: number[];
  saldo_deuda_anual: number[];
  intereses_totales_clp: number;
  tax_shield: { anual: number[]; total_5y: number; utilidad_neta_anual: number[] };
  coverage: {
    dscr_anual: (number | null)[];
    dscr_minimo: number;
    dscr_minimo_post_rampup: number;
    llcr: number;
    saludable: boolean;
    excluir_ramp_up_anos: number;
    nota: string;
  };
  tir_equity_apalancado: number | null;
  valor_residual_proxy_clp: number;
};

const fmtB = (n: number) => `$${(n / 1e9).toFixed(2)}B`;
const fmtPct = (n: number | null | undefined) =>
  n === null || n === undefined ? '—' : `${(n * 100).toFixed(1)}%`;

export default function FinanciamientoPage() {
  const [deudaPct, setDeudaPct] = useState(0.50);
  const [tasa, setTasa] = useState(0.095);
  const [plazo, setPlazo] = useState(10);
  const [grace, setGrace] = useState(2);
  const [equityReq, setEquityReq] = useState(0.20);
  const [data, setData] = useState<FinancingResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void calcular();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function calcular() {
    setLoading(true);
    setErr(null);
    try {
      const r = await fetch(`${ENGINE_URL}/plan/financing`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          deuda_pct: deudaPct,
          tasa_deuda_anual: tasa,
          plazo_deuda_anos: plazo,
          grace_anos: grace,
          tasa_equity_required: equityReq,
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
        <h1 className="font-serif text-3xl text-oliva-900">Estructura de financiamiento</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Mix deuda/equity, escudo fiscal y ratios bancarios (DSCR/LLCR). Calibrado con tasas CORFO Chile
          + sustainability-linked bonds Latam. La heurística "saludable" excluye los años de ramp-up.
        </p>
      </header>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm card-hover">
        <h2 className="font-medium text-oliva-900">Parámetros de la deuda</h2>
        <div className="mt-3 grid grid-cols-2 gap-4 md:grid-cols-5">
          <SliderInput label="% Deuda" value={deudaPct} setter={setDeudaPct} min={0} max={0.85} step={0.05} pct />
          <SliderInput label="Tasa anual" value={tasa} setter={setTasa} min={0.05} max={0.20} step={0.005} pct />
          <SliderInput label="Plazo (años)" value={plazo} setter={setPlazo} min={3} max={20} step={1} />
          <SliderInput label="Gracia (años)" value={grace} setter={setGrace} min={0} max={5} step={1} />
          <SliderInput label="WACC equity" value={equityReq} setter={setEquityReq} min={0.10} max={0.40} step={0.01} pct />
        </div>
        <button
          onClick={calcular}
          className="mt-4 rounded bg-oliva-900 px-4 py-2 text-sm text-crema hover:bg-oliva-600 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Calculando...' : 'Recalcular'}
        </button>
        {err && <p className="mt-2 text-sm text-borgoña">{err}</p>}
      </section>

      {data && (
        <>
          <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <Card label="CapEx total" value={fmtB(data.capex_total_clp)} />
            <Card label="Deuda" value={fmtB(data.monto_deuda_clp)} sub={`${(data.estructura.deuda_pct * 100).toFixed(0)}%`} />
            <Card label="Equity" value={fmtB(data.monto_equity_clp)} sub={`${(100 - data.estructura.deuda_pct * 100).toFixed(0)}%`} />
            <Card
              label="TIR equity apalancado"
              value={fmtPct(data.tir_equity_apalancado)}
              highlight={(data.tir_equity_apalancado ?? 0) > 0.20}
            />
            <Card label="LLCR" value={data.coverage.llcr.toFixed(2)} highlight={data.coverage.llcr > 1.5} />
          </section>

          <section
            className={`rounded-lg border p-4 ${
              data.coverage.saludable ? 'border-trigo/40 bg-trigo/10' : 'border-borgoña/40 bg-borgoña/5'
            }`}
          >
            <h3 className="font-medium text-oliva-900">
              Cobertura {data.coverage.saludable ? '✓ saludable' : '⚠ revisar'}
            </h3>
            <p className="mt-1 text-sm text-oliva-700">{data.coverage.nota}</p>
            <div className="mt-3 grid grid-cols-2 gap-2 md:grid-cols-5">
              {data.coverage.dscr_anual.map((d, i) => (
                <div key={i} className="rounded bg-white p-2 text-center">
                  <div className="text-[10px] uppercase tracking-wide text-oliva-600">Año {i + 1}</div>
                  <div
                    className={`text-lg font-semibold ${
                      d === null ? 'text-oliva-400' : d >= 1.3 ? 'text-oliva-900' : 'text-borgoña'
                    }`}
                  >
                    {d === null ? '—' : d.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-oliva/10 bg-white p-4">
            <h2 className="font-medium text-oliva-900">Servicio de la deuda + Tax shield</h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-oliva-50 text-xs uppercase tracking-wide text-oliva-600">
                  <tr>
                    <th className="px-3 py-2 text-left">Año</th>
                    <th className="px-3 py-2 text-right">Intereses</th>
                    <th className="px-3 py-2 text-right">Principal</th>
                    <th className="px-3 py-2 text-right">Saldo deuda</th>
                    <th className="px-3 py-2 text-right">Tax shield</th>
                    <th className="px-3 py-2 text-right">Utilidad neta</th>
                  </tr>
                </thead>
                <tbody>
                  {data.intereses_anual.map((_, i) => (
                    <tr key={i} className="border-t border-oliva/5">
                      <td className="px-3 py-2 font-medium">A{i + 1}</td>
                      <td className="px-3 py-2 text-right tabular">{fmtB(data.intereses_anual[i])}</td>
                      <td className="px-3 py-2 text-right tabular">{fmtB(data.principal_anual[i])}</td>
                      <td className="px-3 py-2 text-right tabular text-oliva-600">{fmtB(data.saldo_deuda_anual[i])}</td>
                      <td className="px-3 py-2 text-right tabular text-trigo">{fmtB(data.tax_shield.anual[i])}</td>
                      <td
                        className={`px-3 py-2 text-right tabular ${
                          data.tax_shield.utilidad_neta_anual[i] < 0 ? 'text-borgoña' : 'text-oliva-900'
                        }`}
                      >
                        {fmtB(data.tax_shield.utilidad_neta_anual[i])}
                      </td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-oliva/20 bg-oliva-50/50">
                    <td className="px-3 py-2 font-semibold">Total 5y</td>
                    <td className="px-3 py-2 text-right font-semibold">{fmtB(data.intereses_totales_clp)}</td>
                    <td className="px-3 py-2 text-right font-semibold">
                      {fmtB(data.principal_anual.reduce((a, b) => a + b, 0))}
                    </td>
                    <td className="px-3 py-2 text-right text-xs text-oliva-500">final A5</td>
                    <td className="px-3 py-2 text-right font-semibold text-trigo">{fmtB(data.tax_shield.total_5y)}</td>
                    <td className="px-3 py-2 text-right font-semibold">
                      {fmtB(data.tax_shield.utilidad_neta_anual.reduce((a, b) => a + b, 0))}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
            <strong>Comparable de mercado (WebSearch 2026):</strong> tasa CORFO + spread sector circular Chile
            está en 9-11% nominal CLP. Sustainability-linked bonds Latam: USD 800-900B globally en 2026,
            con KPI ESG que ajusta tasa al alza si no se cumple. Banca chilena exige DSCR ≥ 1.3 fuera de años
            de ramp-up + LLCR &gt; 1.5.
          </section>
        </>
      )}
    </div>
  );
}

function SliderInput({
  label,
  value,
  setter,
  min,
  max,
  step,
  pct,
}: {
  label: string;
  value: number;
  setter: (v: number) => void;
  min: number;
  max: number;
  step: number;
  pct?: boolean;
}) {
  return (
    <label className="block">
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">{label}</div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => setter(parseFloat(e.target.value))}
        className="mt-1 w-full"
      />
      <div className="text-sm tabular font-medium text-oliva-900">
        {pct ? `${(value * 100).toFixed(1)}%` : value}
      </div>
    </label>
  );
}

function Card({ label, value, sub, highlight }: { label: string; value: string; sub?: string; highlight?: boolean }) {
  return (
    <div
      className={`card-hover rounded-lg border p-4 ${
        highlight ? 'border-trigo/40 bg-trigo/5' : 'border-oliva/10 bg-white'
      }`}
    >
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">{label}</div>
      <div className={`tabular mt-1 text-2xl font-bold ${highlight ? 'text-trigo' : 'text-oliva-900'}`}>{value}</div>
      {sub && <div className="text-xs text-oliva-500">{sub}</div>}
    </div>
  );
}
