'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

const fmtPct = (n: number | null | undefined) =>
  n === null || n === undefined ? '—' : `${(n * 100).toFixed(2)}%`;
const fmtB = (n: number) => `$${(n / 1e9).toFixed(2)}B CLP`;

type Plan = {
  kpis: {
    tir_proyecto_anual: number | null;
    van: number;
    payback_meses: number | null;
    ebitda_margin_promedio: number;
  };
};

type WhatIfResp = {
  base: { kpis: { tir: number | null; van: number; payback_meses: number | null; ebitda_margin: number } };
  escenarios: {
    nombre: string;
    resumen: { kpis: { tir: number | null; van: number; payback_meses: number | null; ebitda_margin: number } };
    deltas: { tir_pp: number | null; van_pct: number | null };
  }[];
};

export default function StressPage() {
  const [precioShock, setPrecioShock] = useState(-0.20);  // -20%
  const [costoMmppShock, setCostoMmppShock] = useState(0.20);  // +20%
  const [waccShock, setWaccShock] = useState(0.02);  // +200bps
  const [opexShock, setOpexShock] = useState(0.15);  // +15%
  const [base, setBase] = useState<Plan | null>(null);
  const [stress, setStress] = useState<WhatIfResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void cargarBase();
  }, []);

  async function cargarBase() {
    try {
      const r = await fetch(`${ENGINE_URL}/plan`, {
        method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({}),
      });
      if (r.ok) setBase(await r.json());
    } catch (e) {
      setErr(String(e));
    }
  }

  async function correrStress() {
    setLoading(true);
    setErr(null);
    try {
      // Construir overrides para whatif
      const planBase = base?.kpis ?? null;
      if (!planBase) {
        throw new Error('No hay plan base cargado');
      }
      // Stress: combinación de 4 shocks aplicados juntos
      const overrides: Record<string, number> = {
        wacc_anual: 0.18 + waccShock,
        costo_mmpp_clp_kg: 30 * (1 + costoMmppShock),
        opex_mensual_clp: 80_000_000 * (1 + opexShock),
      };
      // Precios: escalar TODOS los SKUs por (1 + precioShock)
      const precios = {
        HARINA_ALPERUJO: 800, ACEITE_ALPERUJO: 1300, HARINA_ORUJO: 600,
        HARINA_TOMASA: 700, HARINA_POMASA: 700, ACEITE_ORUJO_UVA: 1500,
        PECTINA: 25000, LICOPENO: 80000,
        PROTEINA_UNICEL: 1500, ANTIOXIDANTE: 15000, AGLOMERANTE: 2000, UMAMI: 4500,
      };
      const preciosShockados: Record<string, number> = {};
      for (const [k, v] of Object.entries(precios)) {
        preciosShockados[`precios_clp_kg.${k}`] = v * (1 + precioShock);
      }

      const r = await fetch(`${ENGINE_URL}/whatif`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          base: {},
          escenarios: [
            {
              nombre: `Stress: precio ${(precioShock * 100).toFixed(0)}% + costos +${(costoMmppShock * 100).toFixed(0)}% + WACC +${(waccShock * 10000).toFixed(0)}bps + OpEx +${(opexShock * 100).toFixed(0)}%`,
              overrides: { ...overrides, ...preciosShockados },
            },
          ],
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
      setStress(await r.json());
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  const esc = stress?.escenarios[0];
  const supera_hurdle_15 = esc?.resumen.kpis.tir ? esc.resumen.kpis.tir > 0.15 : false;
  const supera_wacc_18 = esc?.resumen.kpis.tir ? esc.resumen.kpis.tir > 0.18 : false;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Stress Test · Escenario Triple-Negativo</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Aplica shocks simultáneos al plan base. Útil para comité de inversión: muestra el peor caso
          razonable y si el proyecto resiste. Compara contra hurdle FIP CEHTA (18%).
        </p>
      </header>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm card-hover">
        <h2 className="font-medium text-oliva-900">Configuración del shock</h2>
        <div className="mt-3 grid grid-cols-2 gap-4 md:grid-cols-4">
          <Slider label="Shock precios SKU" value={precioShock} setter={setPrecioShock} min={-0.5} max={0} step={0.05} suffix="%" multiplier={100} />
          <Slider label="Shock costo MMPP" value={costoMmppShock} setter={setCostoMmppShock} min={0} max={0.5} step={0.05} suffix="%" multiplier={100} />
          <Slider label="Shock WACC (bps)" value={waccShock} setter={setWaccShock} min={0} max={0.05} step={0.005} suffix="bps" multiplier={10000} />
          <Slider label="Shock OpEx" value={opexShock} setter={setOpexShock} min={0} max={0.5} step={0.05} suffix="%" multiplier={100} />
        </div>
        <button
          onClick={correrStress}
          className="mt-4 rounded bg-borgoña px-4 py-2 text-sm text-crema hover:bg-tierra disabled:opacity-50"
          disabled={loading || !base}
        >
          {loading ? 'Calculando stress...' : 'Ejecutar stress test'}
        </button>
        {err && <p className="mt-2 text-sm text-borgoña">{err}</p>}
      </section>

      {base && esc && (
        <>
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <CasoCol
              titulo="Plan BASE (sin stress)"
              tir={base.kpis.tir_proyecto_anual}
              van={base.kpis.van}
              payback={base.kpis.payback_meses}
              ebitda={base.kpis.ebitda_margin_promedio}
              tone="ok"
            />
            <CasoCol
              titulo="STRESS triple-negativo"
              tir={esc.resumen.kpis.tir}
              van={esc.resumen.kpis.van}
              payback={esc.resumen.kpis.payback_meses}
              ebitda={esc.resumen.kpis.ebitda_margin}
              tone="warn"
              deltaTir={esc.deltas.tir_pp}
              deltaVan={esc.deltas.van_pct}
            />
          </section>

          <section
            className={`rounded-lg border-2 p-4 ${
              supera_wacc_18 ? 'border-oliva-700/40 bg-oliva-50/40' : 'border-borgoña/30 bg-borgoña/5'
            }`}
          >
            <h3 className="font-medium">
              {supera_wacc_18
                ? '✓ El proyecto resiste el stress test'
                : supera_hurdle_15
                ? '⚠ Por debajo del WACC pero por encima del hurdle mínimo'
                : '✗ El proyecto NO supera el stress test'}
            </h3>
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-oliva-700">
              <li>TIR stress: <strong className="tabular">{fmtPct(esc.resumen.kpis.tir)}</strong></li>
              <li>vs WACC 18%: {supera_wacc_18 ? 'supera' : 'no supera'} ({((esc.resumen.kpis.tir ?? 0) * 100 - 18).toFixed(2)} pp)</li>
              <li>vs hurdle CEHTA 15%: {supera_hurdle_15 ? 'supera' : 'no supera'}</li>
              <li>
                {supera_wacc_18
                  ? 'El plan es robusto frente a shock multi-variable. Defendible a comité.'
                  : 'Considerar: seguro de precios + contratos take-or-pay + cobertura cambiaria.'}
              </li>
            </ul>
          </section>

          <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
            <strong>Cómo se aplica el stress:</strong>
            <ul className="mt-2 list-disc space-y-0.5 pl-5">
              <li>Los 12 SKUs se escalan por (1 + precio_shock). Default −20%.</li>
              <li>Costo MMPP se escala por (1 + costo_mmpp_shock). Default +20%.</li>
              <li>WACC + delta. Default +200 bps.</li>
              <li>OpEx mensual × (1 + opex_shock). Default +15%.</li>
              <li>Working capital cíclico, depreciación y tax shield se recalculan.</li>
            </ul>
          </section>
        </>
      )}
    </div>
  );
}

function CasoCol({
  titulo, tir, van, payback, ebitda, tone, deltaTir, deltaVan,
}: {
  titulo: string; tir: number | null; van: number; payback: number | null; ebitda: number;
  tone: 'ok' | 'warn'; deltaTir?: number | null; deltaVan?: number | null;
}) {
  const cls = tone === 'ok' ? 'border-oliva/20 bg-oliva-50/30' : 'border-borgoña/30 bg-borgoña/5';
  return (
    <div className={`card-hover rounded-lg border-2 p-4 ${cls}`}>
      <h3 className="font-medium text-oliva-900">{titulo}</h3>
      <dl className="mt-3 space-y-2 text-sm">
        <Row dt="TIR proyecto" dd={fmtPct(tir)} delta={deltaTir ? `${deltaTir.toFixed(1)} pp` : undefined} highlight />
        <Row dt="VAN" dd={fmtB(van)} delta={deltaVan ? `${deltaVan.toFixed(1)}%` : undefined} />
        <Row dt="Payback" dd={`${payback ?? '—'} meses`} />
        <Row dt="EBITDA margin" dd={fmtPct(ebitda)} />
      </dl>
    </div>
  );
}

function Row({ dt, dd, delta, highlight }: { dt: string; dd: string; delta?: string; highlight?: boolean }) {
  return (
    <div className="flex items-baseline justify-between border-b border-oliva/5 py-1">
      <dt className="text-oliva-600">{dt}</dt>
      <dd className="flex items-baseline gap-2">
        <span className={`tabular ${highlight ? 'font-semibold text-oliva-900' : 'text-oliva-700'}`}>{dd}</span>
        {delta && <span className="text-xs text-borgoña">({delta})</span>}
      </dd>
    </div>
  );
}

function Slider({
  label, value, setter, min, max, step, suffix, multiplier = 1,
}: { label: string; value: number; setter: (v: number) => void; min: number; max: number; step: number; suffix: string; multiplier?: number }) {
  return (
    <label className="block">
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">{label}</div>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => setter(parseFloat(e.target.value))} className="mt-1 w-full" />
      <div className="tabular text-sm font-medium text-oliva-900">
        {(value * multiplier).toFixed(suffix === 'bps' ? 0 : 1)}{suffix}
      </div>
    </label>
  );
}
