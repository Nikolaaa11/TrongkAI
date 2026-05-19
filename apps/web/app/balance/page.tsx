'use client';

import { useEffect, useState } from 'react';
import { SankeyChart, type SankeyData } from '@/components/SankeyChart';

interface MassBalanceResponse {
  mmpp: string;
  mode: string;
  input_ton: number;
  materia_seca_pura_ton: number;
  aceite_extraido_ton: number;
  licopeno_extraido_ton: number;
  pectina_extraida_ton: number;
  harina_final_ton: number;
  agua_evaporada_ton: number;
  perdidas_ton: number;
  materia_seca_neta_pct: number;
  delta_balance_pct: number;
  sankey: SankeyData;
}

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

const PRESETS: Record<string, { humedad: number; ms: number; aceite: number; licopeno: number; pectina: number }> = {
  ALPERUJO: { humedad: 0.65, ms: 0.35, aceite: 0.02, licopeno: 0, pectina: 0 },
  TOMASA: { humedad: 0.82, ms: 0.18, aceite: 0, licopeno: 0.001, pectina: 0.002 },
  POMASA: { humedad: 0.8, ms: 0.2, aceite: 0, licopeno: 0, pectina: 0.003 },
  ORUJO_UVA: { humedad: 0.6, ms: 0.4, aceite: 0.005, licopeno: 0, pectina: 0 },
  LEVADURA: { humedad: 0.75, ms: 0.25, aceite: 0, licopeno: 0, pectina: 0 },
};

export default function BalancePage() {
  const [mmpp, setMmpp] = useState('ALPERUJO');
  const [params, setParams] = useState(PRESETS.ALPERUJO);
  const [inputTon, setInputTon] = useState(100);
  const [modoA, setModoA] = useState<MassBalanceResponse | null>(null);
  const [modoB, setModoB] = useState<MassBalanceResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setParams(PRESETS[mmpp] ?? PRESETS.ALPERUJO);
  }, [mmpp]);

  async function run() {
    setErr(null);
    setLoading(true);
    try {
      const body = (mode: 'A' | 'B') => ({
        mmpp_codigo: mmpp,
        humedad_inicial_pct: params.humedad,
        materia_solida_pct: params.ms,
        aceite_extraible_pct: params.aceite,
        licopeno_pct: params.licopeno,
        pectina_pct: params.pectina,
        input_ton: inputTon,
        mode,
      });
      const [a, b] = await Promise.all([
        fetch(`${ENGINE_URL}/mass-balance`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body('A')),
        }).then((r) => (r.ok ? r.json() : r.text().then((t) => Promise.reject(t)))),
        fetch(`${ENGINE_URL}/mass-balance`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body('B')),
        }).then((r) => (r.ok ? r.json() : r.text().then((t) => Promise.reject(t)))),
      ]);
      setModoA(a);
      setModoB(b);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  const deltaPp = modoA && modoB ? (modoB.materia_seca_neta_pct - modoA.materia_seca_neta_pct) * 100 : null;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Balance de masa — Módulo 2</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Replica el ejemplo del Excel cliente y visualiza el flujo completo con Sankey. Comparación inmediata
          entre <strong>modo A</strong> (base inicial) y <strong>modo B</strong> (base deshidratada).
        </p>
      </header>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
        <h2 className="font-medium text-oliva-900">Inputs</h2>
        <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-7">
          <label className="text-xs uppercase tracking-wide text-oliva-600">
            MMPP
            <select
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1 text-sm"
              value={mmpp}
              onChange={(e) => setMmpp(e.target.value)}
            >
              {Object.keys(PRESETS).map((m) => (
                <option key={m}>{m}</option>
              ))}
            </select>
          </label>
          <NumericInput label="Humedad inicial" value={params.humedad} onChange={(v) => setParams({ ...params, humedad: v })} step={0.01} />
          <NumericInput label="Materia sólida" value={params.ms} onChange={(v) => setParams({ ...params, ms: v })} step={0.01} />
          <NumericInput label="Aceite extr." value={params.aceite} onChange={(v) => setParams({ ...params, aceite: v })} step={0.001} />
          <NumericInput label="Licopeno" value={params.licopeno} onChange={(v) => setParams({ ...params, licopeno: v })} step={0.0005} />
          <NumericInput label="Pectina" value={params.pectina} onChange={(v) => setParams({ ...params, pectina: v })} step={0.0005} />
          <NumericInput label="Input (ton)" value={inputTon} onChange={setInputTon} step={1} />
        </div>
        <button
          onClick={run}
          className="mt-4 rounded bg-oliva-900 px-4 py-2 text-sm text-crema hover:bg-oliva-600 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Calculando...' : 'Calcular ambos modos'}
        </button>
        {err && <p className="mt-2 text-sm text-borgoña">{err}</p>}
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {[
          { titulo: 'Modo A — Base inicial', r: modoA },
          { titulo: 'Modo B — Base deshidratada', r: modoB },
        ].map(({ titulo, r }) => (
          <div key={titulo} className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
            <h3 className="font-medium text-oliva-900">{titulo}</h3>
            {!r && <p className="mt-2 text-sm text-oliva-400">Sin datos — ejecuta el cálculo.</p>}
            {r && (
              <>
                <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <Stat dt="MS neta entregada" dd={`${(r.materia_seca_neta_pct * 100).toFixed(2)}%`} highlight />
                  <Stat dt="Harina final (10% humedad)" dd={`${r.harina_final_ton.toFixed(3)} ton`} />
                  <Stat dt="Aceite extraído" dd={`${r.aceite_extraido_ton.toFixed(3)} ton`} />
                  {r.licopeno_extraido_ton > 0 && (
                    <Stat dt="Licopeno" dd={`${r.licopeno_extraido_ton.toFixed(4)} ton`} />
                  )}
                  {r.pectina_extraida_ton > 0 && (
                    <Stat dt="Pectina" dd={`${r.pectina_extraida_ton.toFixed(4)} ton`} />
                  )}
                  <Stat dt="Agua evaporada" dd={`${r.agua_evaporada_ton.toFixed(3)} ton`} />
                  <Stat dt="Pérdidas" dd={`${r.perdidas_ton.toFixed(3)} ton`} />
                  <Stat dt="Δ balance" dd={`${(r.delta_balance_pct * 100).toFixed(3)}%`} />
                </dl>
                <div className="mt-4 -mx-2">
                  <SankeyChart data={r.sankey} title="" height={320} />
                </div>
              </>
            )}
          </div>
        ))}
      </section>

      {modoA && modoB && deltaPp !== null && (
        <section
          className={`rounded-lg border p-4 text-sm ${
            Math.abs(deltaPp) > 5
              ? 'border-borgoña/40 bg-borgoña/5 text-oliva-900'
              : 'border-trigo/40 bg-trigo/10 text-oliva-900'
          }`}
        >
          <p>
            <strong>Diferencia A vs B:</strong> {deltaPp > 0 ? '+' : ''}{deltaPp.toFixed(2)} pp de MS neta entregada (
            {((deltaPp / (modoA.materia_seca_neta_pct * 100)) * 100).toFixed(1)}% relativo). {Math.abs(deltaPp) > 5 ? (
              <strong>Material — requiere firma de José y Claudio (ADR-003).</strong>
            ) : (
              <span>Diferencia no material; la elección de modo no es bloqueante a corto plazo.</span>
            )}
          </p>
        </section>
      )}
    </div>
  );
}

function NumericInput({
  label,
  value,
  onChange,
  step = 0.01,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
}) {
  return (
    <label className="text-xs uppercase tracking-wide text-oliva-600">
      {label}
      <input
        type="number"
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="mt-1 w-full rounded border border-oliva/20 px-2 py-1 text-sm"
      />
    </label>
  );
}

function Stat({ dt, dd, highlight }: { dt: string; dd: string; highlight?: boolean }) {
  return (
    <>
      <dt className="text-oliva-600">{dt}</dt>
      <dd className={`text-right ${highlight ? 'font-semibold text-oliva-900' : 'text-oliva-700'}`}>{dd}</dd>
    </>
  );
}
