'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Escenario = {
  nombre: string;
  descripcion: string;
  metricas: {
    tir: number;
    van: number;
    payback_meses: number | null;
    moic: number;
    capex_total: number;
    capex_peak: number;
    dscr_promedio_3_5: number;
    anio_ebitda_positivo: number | null;
    ebitda_ano5: number;
    ev_proxy_ano5: number;
  };
};

type CompResp = {
  escenarios: Escenario[];
  mejor_por_metrica: Record<string, string>;
  matriz_ranking: Record<string, Record<string, number>>;
  recomendacion: { elegido: string; razon: string };
};

const METRICA_LABEL: Record<string, { label: string; format: (v: number) => string; direccion: 'max' | 'min' }> = {
  tir: { label: 'TIR Proyecto', format: (v) => `${(v * 100).toFixed(2)}%`, direccion: 'max' },
  van: { label: 'VAN @ 18%', format: (v) => `$${(v / 1e9).toFixed(2)}B CLP`, direccion: 'max' },
  payback_meses: { label: 'Payback', format: (v) => `${v ?? '—'} meses`, direccion: 'min' },
  moic: { label: 'MOIC', format: (v) => `${v.toFixed(2)}×`, direccion: 'max' },
  capex_total: { label: 'CapEx Total', format: (v) => `$${(v / 1e9).toFixed(1)}B CLP`, direccion: 'min' },
  capex_peak: { label: 'CapEx Peak', format: (v) => `$${(v / 1e9).toFixed(1)}B CLP`, direccion: 'min' },
  dscr_promedio_3_5: { label: 'DSCR (años 3-5)', format: (v) => v.toFixed(2), direccion: 'max' },
  anio_ebitda_positivo: { label: 'EBITDA positivo', format: (v) => `año ${v ?? '—'}`, direccion: 'min' },
  ebitda_ano5: { label: 'EBITDA año 5', format: (v) => `$${(v / 1e9).toFixed(2)}B`, direccion: 'max' },
  ev_proxy_ano5: { label: 'EV exit (9.63×)', format: (v) => `$${(v / 1e9).toFixed(0)}B`, direccion: 'max' },
};

export default function ComparadorPage() {
  const [data, setData] = useState<CompResp | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/scenarios/compare`)
      .then((r) => (r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`)))
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Comparador de Escenarios</h1>
          <p className="mt-2 text-sm text-ink-400">
            PILOTO vs INDUSTRIAL vs EXPANSION lado a lado. 9 métricas, ranking por cada una,
            recomendación final del comparador.
          </p>
        </div>
      </header>

      {err && <div className="apple-card border border-red-200 bg-red-50/40 text-red-600">{err}</div>}

      {data && (
        <>
          {/* Recomendación */}
          <section className="rounded-appleXl bg-brand p-8 text-white">
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-white/80">
              Recomendación del comparador
            </div>
            <h2 className="mt-2 text-4xl font-semibold tracking-apple">{data.recomendacion.elegido}</h2>
            <p className="mt-3 text-white/85">{data.recomendacion.razon}</p>
          </section>

          {/* Cards lado a lado */}
          <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {data.escenarios.map((e) => {
              const esGanador = data.recomendacion.elegido === e.nombre;
              return (
                <div
                  key={e.nombre}
                  className={`apple-card ${esGanador ? 'bg-brand-50 ring-1 ring-brand/30' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-semibold tracking-apple text-ink">{e.nombre}</h3>
                    {esGanador && (
                      <span className="rounded-full bg-brand px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-white">
                        ★ Ganador
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-xs text-ink-600">{e.descripcion}</p>
                  <div className="mt-4 space-y-2 border-t border-ink-100 pt-3">
                    <KPIRow label="TIR" value={`${(e.metricas.tir * 100).toFixed(2)}%`} />
                    <KPIRow label="VAN" value={`$${(e.metricas.van / 1e9).toFixed(2)}B`} />
                    <KPIRow label="MOIC" value={`${e.metricas.moic.toFixed(2)}×`} highlight />
                    <KPIRow label="Payback" value={`${e.metricas.payback_meses ?? '—'} meses`} />
                    <KPIRow label="CapEx total" value={`$${(e.metricas.capex_total / 1e9).toFixed(1)}B`} />
                    <KPIRow label="EBITDA año 5" value={`$${(e.metricas.ebitda_ano5 / 1e9).toFixed(2)}B`} />
                  </div>
                </div>
              );
            })}
          </section>

          {/* Tabla ranking detallada */}
          <section className="apple-card overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-ink-100 bg-ink-50/50">
                  <th className="p-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">Métrica</th>
                  {data.escenarios.map((e) => (
                    <th key={e.nombre} className="p-3 text-center text-[11px] font-semibold uppercase tracking-wider text-ink-400">
                      {e.nombre}
                    </th>
                  ))}
                  <th className="p-3 text-center text-[11px] font-semibold uppercase tracking-wider text-ink-400">Mejor</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(METRICA_LABEL).map(([metrica, meta]) => (
                  <tr key={metrica} className="border-b border-ink-100 last:border-0">
                    <td className="p-3 font-medium text-ink">{meta.label}</td>
                    {data.escenarios.map((e) => {
                      const valor = (e.metricas as any)[metrica];
                      const rank = data.matriz_ranking[e.nombre]?.[metrica];
                      const esGanador = data.mejor_por_metrica[metrica] === e.nombre;
                      return (
                        <td key={e.nombre} className="p-3 text-center">
                          <div className={`tabular ${esGanador ? 'font-bold text-brand' : 'text-ink-600'}`}>
                            {meta.format(valor)}
                          </div>
                          <div className="text-[10px] uppercase tracking-wider text-ink-400">rank {rank}</div>
                        </td>
                      );
                    })}
                    <td className="p-3 text-center">
                      <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand">
                        {data.mejor_por_metrica[metrica]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {/* CTA */}
          <section className="rounded-appleXl bg-ink-50 p-8 text-center">
            <h2 className="text-2xl font-semibold tracking-apple text-ink">
              ¿Quieres simular un escenario personalizado?
            </h2>
            <p className="mt-2 text-sm text-ink-600">
              Usa el módulo What-if para combinar variables a tu gusto.
            </p>
            <a href="/whatif" className="btn-apple mt-4 inline-block">
              Ir a What-if →
            </a>
          </section>
        </>
      )}
    </div>
  );
}

function KPIRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-baseline justify-between text-sm">
      <span className="text-ink-400">{label}</span>
      <span className={`tabular ${highlight ? 'font-semibold text-brand' : 'text-ink'}`}>{value}</span>
    </div>
  );
}
