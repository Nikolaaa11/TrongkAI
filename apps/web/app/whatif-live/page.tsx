'use client';

import Image from 'next/image';
import { useEffect, useMemo, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type WhatIfResp = {
  base: { kpis: { tir: number | null; van: number; payback_meses: number | null; ebitda_margin: number } };
  escenarios: {
    nombre: string;
    resumen: { kpis: { tir: number | null; van: number; payback_meses: number | null; ebitda_margin: number } };
    deltas: { tir_pp: number | null; van_pct: number | null };
  }[];
};

const PRECIOS_BASE: Record<string, number> = {
  HARINA_ALPERUJO: 800,
  ACEITE_ALPERUJO: 1300,
  HARINA_ORUJO: 600,
  HARINA_TOMASA: 700,
  HARINA_POMASA: 700,
  ACEITE_ORUJO_UVA: 1500,
  PECTINA: 25000,
  LICOPENO: 80000,
  PROTEINA_UNICEL: 1500,
  ANTIOXIDANTE: 15000,
  AGLOMERANTE: 2000,
  UMAMI: 4500,
};

export default function WhatIfLivePage() {
  // 4 sliders
  const [precioShock, setPrecioShock] = useState(0);     // -0.30 a +0.30
  const [costoShock, setCostoShock] = useState(0);       // -0.30 a +0.30
  const [waccShock, setWaccShock] = useState(0);          // -0.04 a +0.04 (pp absolutos)
  const [opexShock, setOpexShock] = useState(0);          // -0.30 a +0.30
  const [data, setData] = useState<WhatIfResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Debounced auto-recalc
  useEffect(() => {
    const timer = setTimeout(() => {
      void recalcular();
    }, 400);
    return () => clearTimeout(timer);
  }, [precioShock, costoShock, waccShock, opexShock]);

  async function recalcular() {
    setLoading(true);
    setErr(null);
    try {
      const precios: Record<string, number> = {};
      for (const [k, v] of Object.entries(PRECIOS_BASE)) {
        precios[`precios_clp_kg.${k}`] = v * (1 + precioShock);
      }
      const overrides: Record<string, number> = {
        wacc_anual: 0.18 + waccShock,
        costo_mmpp_clp_kg: 30 * (1 + costoShock),
        opex_mensual_clp: 80_000_000 * (1 + opexShock),
        ...precios,
      };

      const r = await fetch(`${ENGINE_URL}/whatif`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          base: {},
          escenarios: [
            {
              nombre: 'Live what-if',
              overrides,
            },
          ],
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

  const esc = data?.escenarios[0];
  const tirBase = data?.base.kpis.tir ?? 0;
  const tirEsc = esc?.resumen.kpis.tir ?? 0;
  const vanBase = data?.base.kpis.van ?? 0;
  const vanEsc = esc?.resumen.kpis.van ?? 0;

  const deltaTirPP = esc?.deltas.tir_pp ?? 0;
  const deltaVanPct = esc?.deltas.van_pct ?? 0;

  const superaHurdle = tirEsc > 0.15;
  const superaWacc = tirEsc > 0.18;

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">What-if Live</h1>
          <p className="mt-2 text-sm text-ink-400">
            Mueve los sliders y observa el impacto en TIR/VAN en tiempo real (debounce 400ms).
            Útil para defender el plan ante directorio: "¿qué pasa si baja el precio 10%?"
          </p>
        </div>
      </header>

      {/* Sliders */}
      <section className="apple-card">
        <h2 className="text-lg font-semibold text-ink">4 drivers principales</h2>
        <p className="mt-1 text-sm text-ink-400">Cada slider mueve un % sobre el valor base. WACC en puntos absolutos.</p>
        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          <SliderRow label="Precio SKUs" value={precioShock} onChange={setPrecioShock} min={-0.30} max={0.30} step={0.01} display={`${(precioShock * 100).toFixed(0)}%`} hint="0 = sin cambio | +25% = subida fuerte" />
          <SliderRow label="Costo MMPP" value={costoShock} onChange={setCostoShock} min={-0.30} max={0.30} step={0.01} display={`${(costoShock * 100).toFixed(0)}%`} hint="0 = sin cambio | +25% = MMPP más caro" reverse />
          <SliderRow label="WACC" value={waccShock} onChange={setWaccShock} min={-0.04} max={0.04} step={0.005} display={`${waccShock >= 0 ? '+' : ''}${(waccShock * 10000).toFixed(0)} bps`} hint="0 = 18% base | +200bps = banca dura" reverse />
          <SliderRow label="OpEx mensual" value={opexShock} onChange={setOpexShock} min={-0.30} max={0.30} step={0.01} display={`${(opexShock * 100).toFixed(0)}%`} hint="0 = $80M/mes | +20% = más caro operar" reverse />
        </div>
        <div className="mt-4 flex justify-end">
          <button onClick={() => { setPrecioShock(0); setCostoShock(0); setWaccShock(0); setOpexShock(0); }} className="btn-apple btn-apple-ghost text-xs">
            ↺ Reset (base)
          </button>
        </div>
      </section>

      {err && <div className="apple-card border border-red-200 bg-red-50/40 text-red-600">{err}</div>}

      {/* Resultados grandes */}
      {data && esc && (
        <>
          <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {/* BASE */}
            <div className="apple-card bg-ink-50/40">
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-400">
                Plan BASE (sin shocks)
              </div>
              <div className="mt-3 space-y-3">
                <Row label="TIR proyecto" value={`${(tirBase * 100).toFixed(2)}%`} large />
                <Row label="VAN @ 18%" value={`$${(vanBase / 1e9).toFixed(2)}B CLP`} />
                <Row label="Payback" value={`${data.base.kpis.payback_meses ?? '—'} meses`} />
                <Row label="EBITDA margin" value={`${((data.base.kpis.ebitda_margin ?? 0) * 100).toFixed(1)}%`} />
              </div>
            </div>

            {/* ESCENARIO LIVE */}
            <div className={`apple-card ring-1 ${superaWacc ? 'bg-brand-50 ring-brand/30' : superaHurdle ? 'bg-orange-50 ring-orange-200' : 'bg-red-50 ring-red-200'}`}>
              <div className={`text-[11px] font-semibold uppercase tracking-[0.08em] ${superaWacc ? 'text-brand' : superaHurdle ? 'text-orange-600' : 'text-red-600'}`}>
                Escenario LIVE {loading && '(recalculando...)'}
              </div>
              <div className="mt-3 space-y-3">
                <Row
                  label="TIR proyecto"
                  value={`${(tirEsc * 100).toFixed(2)}%`}
                  delta={`${deltaTirPP >= 0 ? '+' : ''}${deltaTirPP.toFixed(2)}pp`}
                  large
                  tone={deltaTirPP >= 0 ? 'ok' : 'bad'}
                />
                <Row
                  label="VAN @ 18%"
                  value={`$${(vanEsc / 1e9).toFixed(2)}B CLP`}
                  delta={`${deltaVanPct >= 0 ? '+' : ''}${deltaVanPct.toFixed(1)}%`}
                  tone={deltaVanPct >= 0 ? 'ok' : 'bad'}
                />
                <Row label="Payback" value={`${esc.resumen.kpis.payback_meses ?? '—'} meses`} />
                <Row label="EBITDA margin" value={`${((esc.resumen.kpis.ebitda_margin ?? 0) * 100).toFixed(1)}%`} />
              </div>
            </div>
          </section>

          {/* Veredicto */}
          <section
            className={`rounded-appleXl p-6 ring-1 ${
              superaWacc
                ? 'bg-brand-50 ring-brand/30'
                : superaHurdle
                ? 'bg-orange-50 ring-orange-200'
                : 'bg-red-50 ring-red-200'
            }`}
          >
            <h3 className="text-xl font-semibold text-ink">
              {superaWacc
                ? '✓ Proyecto resiste el escenario (TIR > WACC 18%)'
                : superaHurdle
                ? '⚠ Bajo WACC pero sobre hurdle CEHTA 15% (defendible con holgura ESG)'
                : '✗ Escenario destruye valor (TIR < hurdle)'}
            </h3>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-ink-700">
              <li>TIR escenario: <strong className="tabular">{(tirEsc * 100).toFixed(2)}%</strong></li>
              <li>vs WACC 18%: {superaWacc ? 'supera' : 'no supera'} ({((tirEsc * 100 - 18)).toFixed(2)} pp)</li>
              <li>vs hurdle CEHTA 15%: {superaHurdle ? 'supera' : 'no supera'} ({((tirEsc * 100 - 15)).toFixed(2)} pp)</li>
              <li>VAN: {vanEsc >= 0 ? 'positivo' : 'NEGATIVO'} ({deltaVanPct >= 0 ? '+' : ''}{deltaVanPct.toFixed(1)}% vs base)</li>
            </ul>
          </section>

          {/* Quick scenarios */}
          <section className="apple-card">
            <h3 className="text-lg font-semibold text-ink">Escenarios pre-configurados</h3>
            <p className="mt-1 text-sm text-ink-400">Click para aplicar combinaciones típicas.</p>
            <div className="mt-4 grid grid-cols-2 gap-2 md:grid-cols-4">
              <QuickBtn label="Recesión leve" onClick={() => { setPrecioShock(-0.10); setCostoShock(0.05); setWaccShock(0.01); setOpexShock(0.05); }} />
              <QuickBtn label="Crisis fuerte" onClick={() => { setPrecioShock(-0.25); setCostoShock(0.20); setWaccShock(0.03); setOpexShock(0.15); }} />
              <QuickBtn label="Optimista" onClick={() => { setPrecioShock(0.15); setCostoShock(-0.10); setWaccShock(-0.01); setOpexShock(-0.05); }} />
              <QuickBtn label="Macro normal" onClick={() => { setPrecioShock(0); setCostoShock(0); setWaccShock(0); setOpexShock(0); }} />
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function SliderRow({
  label, value, onChange, min, max, step, display, hint, reverse,
}: {
  label: string; value: number; onChange: (v: number) => void;
  min: number; max: number; step: number; display: string; hint?: string; reverse?: boolean;
}) {
  const isPositive = reverse ? value <= 0 : value >= 0;
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-ink">{label}</span>
        <span className={`tabular text-lg font-semibold ${isPositive ? 'text-brand' : 'text-red-600'}`}>{display}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="mt-2 w-full accent-brand"
      />
      {hint && <div className="text-[10px] text-ink-400">{hint}</div>}
    </div>
  );
}

function Row({ label, value, delta, tone, large }: { label: string; value: string; delta?: string; tone?: 'ok' | 'bad'; large?: boolean }) {
  const deltaColor = tone === 'ok' ? 'text-brand' : tone === 'bad' ? 'text-red-600' : 'text-ink-400';
  return (
    <div className="flex items-baseline justify-between border-b border-ink-100 pb-2 last:border-0">
      <span className="text-sm text-ink-600">{label}</span>
      <div className="flex items-baseline gap-3">
        <span className={`tabular ${large ? 'text-2xl font-semibold' : 'text-base font-medium'} text-ink`}>{value}</span>
        {delta && <span className={`tabular text-xs ${deltaColor}`}>{delta}</span>}
      </div>
    </div>
  );
}

function QuickBtn({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="rounded-lg border border-ink-100 bg-white px-3 py-2 text-sm font-medium text-ink-600 transition hover:border-brand hover:text-brand">
      {label}
    </button>
  );
}
