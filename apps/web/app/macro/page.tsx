'use client';

import { useEffect, useState } from 'react';
import { trongkai } from '@/lib/trongkai-client';

type Snapshot = {
  dolar_clp: number | null;
  uf_clp: number | null;
  ipc_pct_mensual: number | null;
  tpm_pct: number | null;
  utm_clp: number | null;
  tasa_desempleo_pct: number | null;
  fecha_ultima_actualizacion: string | null;
  fuente: string;
};

const fmt = (n: number | null | undefined, suffix = '') =>
  n === null || n === undefined ? '—' : `${n.toLocaleString('es-CL', { maximumFractionDigits: 2 })}${suffix}`;

const fmtFecha = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString('es-CL', { dateStyle: 'medium', timeStyle: 'short' }) : '—';

export default function MacroPage() {
  const [data, setData] = useState<Snapshot | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [montoClp, setMontoClp] = useState(5_480_000_000);  // VAN base del plan
  const [vanResumen, setVanResumen] = useState<number | null>(null);

  useEffect(() => {
    void cargar();
  }, []);

  async function cargar() {
    try {
      const [s, plan] = await Promise.all([trongkai.macroChile(), trongkai.plan()]);
      setData(s);
      setVanResumen(plan.kpis.van);
    } catch (e) {
      setErr(String(e));
    }
  }

  if (err) return <div className="p-8 text-borgoña">Error: {err}</div>;
  if (!data) return <div className="p-8 text-oliva-600">Cargando indicadores macro Chile…</div>;

  const tc = data.dolar_clp ?? 920;
  const montoUsd = montoClp / tc;
  const vanUsd = vanResumen ? vanResumen / tc : null;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Macro Chile · en vivo</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Indicadores Banco Central Chile vía{' '}
          <a href="https://mindicador.cl" target="_blank" rel="noopener noreferrer" className="text-trigo hover:underline">
            mindicador.cl
          </a>
          . Cache 24h con fallback snapshot interno. Fuente:{' '}
          <em>{data.fuente}</em>. Última actualización: <strong>{fmtFecha(data.fecha_ultima_actualizacion)}</strong>.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <Tarjeta label="Dólar observado" value={`$${fmt(data.dolar_clp)}`} sub="CLP / USD" highlight />
        <Tarjeta label="UF" value={`$${fmt(data.uf_clp)}`} sub="CLP" />
        <Tarjeta label="IPC mensual" value={fmt(data.ipc_pct_mensual, '%')} sub="variación m/m" />
        <Tarjeta label="TPM" value={fmt(data.tpm_pct, '%')} sub="tasa política monetaria" />
        <Tarjeta label="UTM" value={`$${fmt(data.utm_clp)}`} sub="CLP" />
        <Tarjeta label="Desempleo" value={fmt(data.tasa_desempleo_pct, '%')} sub="último trimestre" />
      </section>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm card-hover">
        <h2 className="font-medium text-oliva-900">Conversor CLP ↔ USD</h2>
        <p className="mt-1 text-xs text-oliva-600">
          Usá el dólar observado para convertir el VAN o cualquier monto del plan a USD para inversionistas
          extranjeros (BID Invest, IFC, Triodos, etc).
        </p>
        <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
          <label className="block">
            <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">Monto CLP</div>
            <input
              type="number"
              value={montoClp}
              onChange={(e) => setMontoClp(parseFloat(e.target.value) || 0)}
              className="mt-1 w-full rounded border border-oliva/20 px-3 py-1.5 text-sm tabular"
            />
            <div className="text-xs text-oliva-500">${(montoClp / 1e9).toFixed(2)}B CLP</div>
          </label>
          <div>
            <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">TC aplicado</div>
            <div className="mt-1 text-2xl font-bold text-oliva-900 tabular">${fmt(tc)}</div>
            <div className="text-xs text-oliva-500">CLP / USD</div>
          </div>
          <div className="rounded bg-trigo/10 p-3">
            <div className="text-[10px] uppercase tracking-[0.08em] text-trigo">Equivalente USD</div>
            <div className="mt-1 text-2xl font-bold text-trigo tabular">
              USD {(montoUsd / 1e6).toFixed(2)}M
            </div>
            <div className="text-xs text-oliva-500">${montoUsd.toLocaleString('en-US', { maximumFractionDigits: 0 })}</div>
          </div>
        </div>
      </section>

      {vanResumen && vanUsd && (
        <section className="rounded-lg border-2 border-oliva-900/10 bg-oliva-50/30 p-4">
          <h2 className="font-serif text-lg text-oliva-900">VAN del Plan en USD</h2>
          <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-3">
            <div>
              <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">VAN CLP @ WACC 18%</div>
              <div className="tabular mt-1 text-xl font-bold text-oliva-900">
                ${(vanResumen / 1e9).toFixed(2)}B CLP
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.08em] text-trigo">VAN USD equivalente</div>
              <div className="tabular mt-1 text-xl font-bold text-trigo">
                USD {(vanUsd / 1e6).toFixed(2)}M
              </div>
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">TC sensibilidad</div>
              <div className="mt-1 text-sm text-oliva-700">
                Si TC sube 10% → VAN USD baja {((1 - 1 / 1.1) * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
        <strong>Para qué sirve:</strong> los LPs extranjeros piden cifras en USD. Banco Central Chile actualiza
        el dólar observado diariamente. Este endpoint cachea 24h y tiene fallback si la API externa cae.
        El plan completo (TIR/VAN/payback) se sirve en CLP pero se puede convertir on-the-fly.
      </section>
    </div>
  );
}

function Tarjeta({ label, value, sub, highlight }: { label: string; value: string; sub: string; highlight?: boolean }) {
  return (
    <div
      className={`card-hover rounded-lg border p-3 ${
        highlight ? 'border-trigo/40 bg-trigo/5' : 'border-oliva/10 bg-white'
      }`}
    >
      <div className="text-[9px] uppercase tracking-[0.08em] text-oliva-600">{label}</div>
      <div className={`tabular mt-1 text-xl font-bold ${highlight ? 'text-trigo' : 'text-oliva-900'}`}>{value}</div>
      <div className="mt-0.5 text-[10px] text-oliva-500">{sub}</div>
    </div>
  );
}
