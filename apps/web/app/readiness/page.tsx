'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';
import { ReadinessHistoryChart, type HistoryPoint } from '@/components/ReadinessHistoryChart';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Dim = {
  nombre: string;
  peso: number;
  valor_metrico: number;
  score_0_100: number;
  aporte_total: number;
  detalle: string;
};

type ReadinessResp = {
  score_total: number;
  dimensiones: Dim[];
  interpretacion: string;
};

type HistoryResp = {
  evolucion_compacta: HistoryPoint[];
  stats: {
    total_snapshots: number;
    score_actual: number | null;
    score_inicial: number | null;
    delta: number | null;
    fecha_inicio: string | null;
  };
};

export default function ReadinessPage() {
  const [data, setData] = useState<ReadinessResp | null>(null);
  const [history, setHistory] = useState<HistoryResp | null>(null);
  const [loading, setLoading] = useState(false);
  const [marcandoHito, setMarcandoHito] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void cargar();
    void cargarHistory();
  }, []);

  async function cargarHistory() {
    try {
      const r = await fetch(`${ENGINE_URL}/readiness/history?limit=30`);
      if (r.ok) setHistory(await r.json());
    } catch (e) {
      console.error('history', e);
    }
  }

  async function marcarHito() {
    const evento = prompt('Descripción del hito (ej: LOI firmada con cliente XX):');
    if (!evento) return;
    setMarcandoHito(true);
    try {
      const r = await fetch(`${ENGINE_URL}/readiness/snapshot?evento=${encodeURIComponent(evento)}`, {
        method: 'POST',
      });
      if (r.ok) await cargarHistory();
    } catch (e) {
      setErr(String(e));
    } finally {
      setMarcandoHito(false);
    }
  }

  async function cargar() {
    setLoading(true);
    setErr(null);
    try {
      const r = await fetch(`${ENGINE_URL}/readiness/score?n_sims_mc=500`);
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
      setData(await r.json());
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  const tone = data
    ? data.score_total >= 80
      ? 'ok'
      : data.score_total >= 60
      ? 'warn'
      : data.score_total >= 40
      ? 'mid'
      : 'bad'
    : 'neutral';

  const toneCls = {
    ok: 'border-oliva-700/40 bg-oliva-50/40 text-oliva-900',
    warn: 'border-trigo/50 bg-trigo/10 text-tierra',
    mid: 'border-tierra/40 bg-tierra/5 text-tierra',
    bad: 'border-borgoña/40 bg-borgoña/10 text-borgoña',
    neutral: 'border-oliva/10 bg-white text-oliva-900',
  }[tone];

  return (
    <div className="space-y-6">
      <header className="flex items-start gap-4">
        <Image
          src="/icon-trongkai.png"
          alt="Trongkai"
          width={56}
          height={56}
          priority
          className="shrink-0"
        />
        <div>
          <h1 className="font-serif text-3xl text-oliva-900">Investment Readiness Score</h1>
          <p className="mt-2 text-sm text-oliva-600">
            Score 0-100 sintetizado de 8 dimensiones del proyecto. Útil para LP roadshow,
            comité de inversión y due diligence. Recalcula en vivo desde el motor.
          </p>
        </div>
      </header>

      {err && (
        <div className="rounded border border-borgoña/30 bg-borgoña/5 p-3 text-sm text-borgoña">
          {err}
        </div>
      )}

      {loading && (
        <div className="rounded border border-oliva/10 bg-papel p-3 text-sm text-oliva-700">
          Calculando 8 dimensiones del modelo (incluye 500 sims Monte Carlo)...
        </div>
      )}

      {data && (
        <>
          {/* Big score */}
          <section className={`rounded-lg border-2 p-6 ${toneCls}`}>
            <div className="flex flex-col items-center gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-[0.08em]">Score consolidado</div>
                <div className="mt-1 flex items-baseline gap-2">
                  <div className="tabular text-7xl font-bold">
                    {data.score_total.toFixed(1)}
                  </div>
                  <div className="text-2xl">/100</div>
                </div>
                <div className="mt-2 text-sm font-medium">{data.interpretacion}</div>
              </div>
              <button
                onClick={cargar}
                disabled={loading}
                className="rounded bg-borgoña px-3 py-1.5 text-xs text-crema hover:bg-tierra disabled:opacity-50"
              >
                {loading ? 'Recalculando...' : 'Recalcular ahora'}
              </button>
            </div>

            {/* Bar gauge */}
            <div className="mt-4">
              <div className="relative h-3 w-full overflow-hidden rounded-full bg-papel">
                <div
                  className="h-full bg-gradient-to-r from-borgoña via-trigo to-oliva-700 transition-all"
                  style={{ width: `${data.score_total}%` }}
                />
              </div>
              <div className="mt-1 flex justify-between text-[10px] text-oliva-600">
                <span>0 RE-THINK</span>
                <span>40 OPORT.</span>
                <span>60 PROM.</span>
                <span>80 BANKABLE</span>
                <span>100</span>
              </div>
            </div>
          </section>

          {/* Histórico timeline */}
          <section className="apple-card">
            <div className="mb-3 flex items-baseline justify-between">
              <div>
                <h2 className="text-xl font-semibold tracking-apple text-ink">Evolución histórica</h2>
                <p className="mt-1 text-xs text-ink-400">
                  Snapshots guardados del score. Marca un hito cuando llegue una LOI / cotización / term sheet.
                </p>
              </div>
              <button
                onClick={marcarHito}
                disabled={marcandoHito}
                className="btn-apple text-xs disabled:opacity-50"
              >
                {marcandoHito ? 'Guardando...' : '+ Marcar hito'}
              </button>
            </div>
            <ReadinessHistoryChart data={history?.evolucion_compacta ?? []} height={280} />
            {history && history.stats.total_snapshots > 0 && (
              <div className="mt-3 grid grid-cols-3 gap-3 border-t border-ink-100 pt-3 text-xs">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-ink-400">Snapshots</div>
                  <div className="tabular text-base font-semibold text-ink">{history.stats.total_snapshots}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-ink-400">Score inicial</div>
                  <div className="tabular text-base font-semibold text-ink">{history.stats.score_inicial?.toFixed(1)}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-ink-400">Delta</div>
                  <div className={`tabular text-base font-semibold ${(history.stats.delta ?? 0) >= 0 ? 'text-brand' : 'text-red-600'}`}>
                    {(history.stats.delta ?? 0) >= 0 ? '+' : ''}{history.stats.delta?.toFixed(1)} pts
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* LP Pack ZIP download */}
          <section className="apple-card bg-brand-50 ring-1 ring-brand/20">
            <div className="flex flex-col items-start gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="font-semibold text-ink">¿Listo para mandarlo a un LP?</h3>
                <p className="mt-1 text-sm text-ink-600">
                  Descarga el LP Pack: un ZIP con PDF tearsheet + snapshot JSON + readiness + data room + matriz + sensitivity + README. UN solo archivo, ~90KB.
                </p>
              </div>
              <a
                href={`${ENGINE_URL}/api/lp-pack.zip`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-apple shrink-0"
              >
                📦 Descargar LP Pack ZIP
              </a>
            </div>
          </section>

          {/* Dimensiones */}
          <section className="space-y-2">
            <h2 className="font-medium text-oliva-900">Desglose por dimensión</h2>
            {data.dimensiones.map((d) => (
              <DimRow key={d.nombre} d={d} />
            ))}
          </section>

          {/* Leyenda */}
          <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
            <strong>Cómo se calcula el score:</strong>
            <ul className="mt-2 list-disc space-y-0.5 pl-5">
              <li>
                <strong>Retorno financiero (20%)</strong>: TIR vs hurdle 15%. Lineal hasta 35% = 100.
              </li>
              <li>
                <strong>Robustez Monte Carlo (15%)</strong>: probabilidad de superar WACC en 500+ sims.
              </li>
              <li>
                <strong>Bancabilidad DSCR (15%)</strong>: DSCR ≥ 1.6 = 100; ≤ 1.0 = 0.
              </li>
              <li>
                <strong>Diversificación (10%)</strong>: balance entre marcas Feed/Food/Servicios.
              </li>
              <li>
                <strong>ESG carbono (10%)</strong>: carbono negativo = 100. Neutral = 80.
              </li>
              <li>
                <strong>Compliance (10%)</strong>: % de hitos REP vigentes vs total.
              </li>
              <li>
                <strong>Resiliencia (10%)</strong>: colchón promedio break-even por driver.
              </li>
              <li>
                <strong>Madurez operativa (10%)</strong>: año en que EBITDA cruza a positivo.
              </li>
            </ul>
          </section>
        </>
      )}
    </div>
  );
}

function DimRow({ d }: { d: Dim }) {
  const tone =
    d.score_0_100 >= 80
      ? 'ok'
      : d.score_0_100 >= 60
      ? 'warn'
      : d.score_0_100 >= 40
      ? 'mid'
      : 'bad';
  const barColor = {
    ok: 'bg-oliva-700',
    warn: 'bg-trigo',
    mid: 'bg-tierra',
    bad: 'bg-borgoña',
  }[tone];

  return (
    <div className="rounded border border-oliva/10 bg-white p-3 shadow-sm">
      <div className="flex items-baseline justify-between">
        <div>
          <span className="text-sm font-medium text-oliva-900">{d.nombre}</span>
          <span className="ml-2 text-[10px] uppercase tracking-[0.05em] text-oliva-600">
            peso {(d.peso * 100).toFixed(0)}%
          </span>
        </div>
        <div className="tabular text-sm font-medium text-oliva-900">
          {d.score_0_100.toFixed(0)}/100
          <span className="ml-2 text-xs text-oliva-600">(+{d.aporte_total.toFixed(1)} aporte)</span>
        </div>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-papel">
        <div
          className={`h-full ${barColor} transition-all`}
          style={{ width: `${d.score_0_100}%` }}
        />
      </div>
      <div className="mt-1 text-xs text-oliva-700">{d.detalle}</div>
    </div>
  );
}
