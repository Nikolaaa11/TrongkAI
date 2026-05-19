'use client';

import { useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Kpis = {
  tir_proyecto_anual: number | null;
  van: number;
  payback_meses: number | null;
  ebitda_margin_promedio: number;
  ratio_capex_ventas: number;
};

type ResumenAno = {
  ano: number;
  ingresos: number;
  ebitda: number;
  capex: number;
  ebitda_margin: number;
};

type PlanResponse = {
  kpis: Kpis;
  resumen_anual: ResumenAno[];
  flujos_meses: any[];
};

function fmt(n: number | null | undefined, suffix = ''): string {
  if (n === null || n === undefined) return '—';
  return n.toLocaleString('es-CL', { maximumFractionDigits: 0 }) + suffix;
}

function pct(n: number | null | undefined): string {
  if (n === null || n === undefined) return '—';
  return (n * 100).toFixed(2) + '%';
}

export default function PlanPage() {
  const [wacc, setWacc] = useState(0.12);
  const [volumen, setVolumen] = useState(50_000);
  const [opex, setOpex] = useState(35_000_000);
  const [costoMmpp, setCostoMmpp] = useState(50);
  const [data, setData] = useState<PlanResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function generar() {
    setLoading(true);
    setErr(null);
    try {
      const r = await fetch(`${ENGINE_URL}/plan`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          wacc_anual: wacc,
          volumen_total_ton_ano: volumen,
          opex_mensual_clp: opex,
          costo_mmpp_clp_kg: costoMmpp,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
      const json = (await r.json()) as PlanResponse;
      setData(json);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function descargar() {
    const r = await fetch(`${ENGINE_URL}/plan/export`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        wacc_anual: wacc,
        volumen_total_ton_ano: volumen,
        opex_mensual_clp: opex,
        costo_mmpp_clp_kg: costoMmpp,
      }),
    });
    if (!r.ok) {
      setErr('No se pudo descargar el Excel');
      return;
    }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Plan_5_Anos_Trongkai_${new Date().toISOString().slice(0, 10)}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Plan 5 Años — Módulo 3</h1>
        <p className="mt-2 text-sm text-oliva-600">
          EERR mensual a 60 meses, KPIs financieros y export a Excel formato directorio. Los inputs son
          parametrizables; los precios y rendimientos están en valores de referencia (PD).
        </p>
      </header>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
        <h2 className="font-medium text-oliva-900">Parámetros del plan</h2>
        <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
          <label className="text-xs uppercase tracking-wide text-oliva-600">
            WACC anual
            <input
              type="number"
              step="0.01"
              value={wacc}
              onChange={(e) => setWacc(parseFloat(e.target.value))}
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1 text-sm"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-oliva-600">
            Volumen anual (ton)
            <input
              type="number"
              value={volumen}
              onChange={(e) => setVolumen(parseFloat(e.target.value))}
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1 text-sm"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-oliva-600">
            OpEx mensual (CLP)
            <input
              type="number"
              value={opex}
              onChange={(e) => setOpex(parseFloat(e.target.value))}
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1 text-sm"
            />
          </label>
          <label className="text-xs uppercase tracking-wide text-oliva-600">
            Costo MMPP CLP/kg
            <input
              type="number"
              value={costoMmpp}
              onChange={(e) => setCostoMmpp(parseFloat(e.target.value))}
              className="mt-1 w-full rounded border border-oliva/20 px-2 py-1 text-sm"
            />
          </label>
        </div>
        <div className="mt-4 flex gap-3">
          <button
            onClick={generar}
            className="rounded bg-oliva-900 px-4 py-2 text-sm text-crema hover:bg-oliva-600 disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Generando...' : 'Generar plan'}
          </button>
          <button
            onClick={descargar}
            className="rounded border border-oliva-900 px-4 py-2 text-sm text-oliva-900 hover:bg-oliva-50"
          >
            Descargar Excel directorio
          </button>
        </div>
        {err && <p className="mt-2 text-sm text-borgoña">{err}</p>}
      </section>

      {data && (
        <>
          <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
            <KpiCard label="TIR proyecto anual" value={pct(data.kpis.tir_proyecto_anual)} />
            <KpiCard label="VAN" value={`$${fmt(data.kpis.van)}`} />
            <KpiCard
              label="Payback descontado"
              value={data.kpis.payback_meses ? `${data.kpis.payback_meses} meses` : '—'}
            />
            <KpiCard label="EBITDA margin" value={pct(data.kpis.ebitda_margin_promedio)} />
            <KpiCard label="CapEx / Ventas" value={pct(data.kpis.ratio_capex_ventas)} />
          </section>

          <section>
            <h2 className="font-serif text-xl text-oliva-900">Resumen anual</h2>
            <div className="mt-3 overflow-x-auto rounded-lg border border-oliva/10 bg-white">
              <table className="w-full text-sm">
                <thead className="bg-oliva-50 text-xs uppercase tracking-wide text-oliva-600">
                  <tr>
                    <th className="px-3 py-2 text-left">Año</th>
                    <th className="px-3 py-2 text-right">Ingresos</th>
                    <th className="px-3 py-2 text-right">EBITDA</th>
                    <th className="px-3 py-2 text-right">Margin</th>
                    <th className="px-3 py-2 text-right">CapEx</th>
                  </tr>
                </thead>
                <tbody>
                  {data.resumen_anual.map((a) => (
                    <tr key={a.ano} className="border-t border-oliva/5">
                      <td className="px-3 py-2 font-medium">Año {a.ano}</td>
                      <td className="px-3 py-2 text-right">${fmt(a.ingresos)}</td>
                      <td
                        className={`px-3 py-2 text-right ${a.ebitda < 0 ? 'text-borgoña' : 'text-oliva-900'}`}
                      >
                        ${fmt(a.ebitda)}
                      </td>
                      <td className="px-3 py-2 text-right">{pct(a.ebitda_margin)}</td>
                      <td className="px-3 py-2 text-right">${fmt(a.capex)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-lg border border-trigo/40 bg-trigo/10 p-4 text-sm text-oliva-900">
            <strong>Notas:</strong> precios por SKU y WACC actuales son <strong>PD provisorios</strong>.
            Para versión defendible a directorio (ADR-002), promover supuestos del top 10 a OK_VALIDADO_DIRECTORIO.
            Ver <code className="font-mono">/supuestos</code>.
          </section>
        </>
      )}
    </div>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
      <div className="text-xs uppercase tracking-wide text-oliva-600">{label}</div>
      <div className="mt-1 text-xl font-semibold text-oliva-900">{value}</div>
    </div>
  );
}
