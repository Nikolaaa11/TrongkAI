'use client';

import { useState } from 'react';

interface MassBalanceResponse {
  mmpp: string;
  mode: string;
  input_ton: number;
  materia_seca_pura_ton: number;
  aceite_extraido_ton: number;
  harina_final_ton: number;
  agua_evaporada_ton: number;
  perdidas_ton: number;
  materia_seca_neta_pct: number;
  delta_balance_pct: number;
  sankey: { nodes: { name: string }[]; links: { source: string; target: string; value: number }[] };
}

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

export default function BalancePage() {
  const [mmpp, setMmpp] = useState('ALPERUJO');
  const [humedad, setHumedad] = useState(0.65);
  const [ms, setMs] = useState(0.35);
  const [aceite, setAceite] = useState(0.02);
  const [inputTon, setInputTon] = useState(100);
  const [modoA, setModoA] = useState<MassBalanceResponse | null>(null);
  const [modoB, setModoB] = useState<MassBalanceResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function run() {
    setErr(null);
    try {
      const body = (mode: 'A' | 'B') => ({
        mmpp_codigo: mmpp,
        humedad_inicial_pct: humedad,
        materia_solida_pct: ms,
        aceite_extraible_pct: aceite,
        input_ton: inputTon,
        mode,
      });
      const [a, b] = await Promise.all([
        fetch(`${ENGINE_URL}/mass-balance`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body('A')),
        }).then((r) => (r.ok ? r.json() : Promise.reject(r.statusText))),
        fetch(`${ENGINE_URL}/mass-balance`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body('B')),
        }).then((r) => (r.ok ? r.json() : Promise.reject(r.statusText))),
      ]);
      setModoA(a);
      setModoB(b);
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-serif text-3xl text-oliva-900">Balance de masa — Módulo 2</h1>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
        <h2 className="font-medium text-oliva-900">Inputs</h2>
        <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-5">
          <label className="text-sm">
            MMPP
            <select
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1"
              value={mmpp}
              onChange={(e) => setMmpp(e.target.value)}
            >
              {['ALPERUJO', 'TOMASA', 'POMASA', 'ORUJO_UVA', 'LEVADURA'].map((m) => (
                <option key={m}>{m}</option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            Humedad inicial
            <input
              type="number"
              step="0.01"
              value={humedad}
              onChange={(e) => setHumedad(parseFloat(e.target.value))}
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1"
            />
          </label>
          <label className="text-sm">
            Materia sólida
            <input
              type="number"
              step="0.01"
              value={ms}
              onChange={(e) => setMs(parseFloat(e.target.value))}
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1"
            />
          </label>
          <label className="text-sm">
            Aceite extraíble
            <input
              type="number"
              step="0.001"
              value={aceite}
              onChange={(e) => setAceite(parseFloat(e.target.value))}
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1"
            />
          </label>
          <label className="text-sm">
            Input (ton)
            <input
              type="number"
              value={inputTon}
              onChange={(e) => setInputTon(parseFloat(e.target.value))}
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1"
            />
          </label>
        </div>
        <button
          onClick={run}
          className="mt-4 rounded bg-oliva-900 px-4 py-2 text-sm text-crema hover:bg-oliva-600"
        >
          Calcular ambos modos
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
              <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <dt>MS neta entregada</dt>
                <dd className="text-right">{(r.materia_seca_neta_pct * 100).toFixed(2)}%</dd>
                <dt>Harina final</dt>
                <dd className="text-right">{r.harina_final_ton.toFixed(3)} ton</dd>
                <dt>Aceite extraído</dt>
                <dd className="text-right">{r.aceite_extraido_ton.toFixed(3)} ton</dd>
                <dt>Agua evaporada</dt>
                <dd className="text-right">{r.agua_evaporada_ton.toFixed(3)} ton</dd>
                <dt>Pérdidas</dt>
                <dd className="text-right">{r.perdidas_ton.toFixed(3)} ton</dd>
                <dt>Δ balance</dt>
                <dd className="text-right text-oliva-400">
                  {(r.delta_balance_pct * 100).toFixed(3)}%
                </dd>
              </dl>
            )}
          </div>
        ))}
      </section>

      {modoA && modoB && (
        <section className="rounded-lg border border-trigo/40 bg-trigo/10 p-4 text-sm text-oliva-900">
          <p>
            <strong>Diferencia A vs B:</strong>{' '}
            {((modoB.materia_seca_neta_pct - modoA.materia_seca_neta_pct) * 100).toFixed(2)} pp de MS neta
            entregada. La decisión final requiere firma de José y Claudio (ADR-003).
          </p>
        </section>
      )}
    </div>
  );
}
