'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Producto = {
  codigo: string;
  variante: string;
  etapas_aplicables: string[];
  rendimiento_msf_pct: number;
  notas: string;
  yield_acumulado_teorico: number;
  tiempo_proceso_min: number;
  cantidad_etapas: number;
  tiene_proceso_definido: boolean;
  etapas_detalle: { id: string; nombre: string; orden: number; yield: number; tiempo_min: number }[];
};

type Matriz = {
  productos: Producto[];
  total_productos: number;
  productos_con_proceso_definido: number;
  productos_solo_recepcion: number;
  etapas_universo: { id: string; nombre: string; orden: number }[];
};

const ICON_MMPP: Record<string, string> = {
  TOMASA_1: '🍅', TOMASA_2: '🍅',
  ORUJO_1: '🍇', ORUJO_2: '🍇',
  ALPERUJO_1: '🫒', ALPERUJO_2: '🫒',
  POMASA_1: '🍎', POMASA_2: '🍏',
};

export default function ProductosEtapasPage() {
  const [data, setData] = useState<Matriz | null>(null);
  const [selectedProd, setSelectedProd] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/balance/etapas/productos`).then((r) => r.json()).then(setData);
  }, []);

  if (!data) return <p className="text-ink-400">Cargando matriz productos × etapas…</p>;

  const selected = selectedProd ? data.productos.find((p) => p.codigo === selectedProd) : null;

  // Para la matriz visual
  const etapaIds = data.etapas_universo.map((e) => e.id);

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Cuadro Etapas × Productos</p>
        <h1 className="mt-2 text-4xl font-bold">🧬 Matriz Productos × Etapas Agrosphere</h1>
        <p className="mt-2 text-ink-500">
          Qué MMPP/SKU pasa por qué etapas, rendimiento MSF y tiempo de proceso.
          Fuente: Excel "Etapas X Costeo Agrosphere 29052026".
        </p>
      </header>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KPI label="Productos catalogados" valor={`${data.total_productos}`} />
        <KPI label="Con proceso completo" valor={`${data.productos_con_proceso_definido}`} tono="ok" />
        <KPI label="Solo recepción definida" valor={`${data.productos_solo_recepcion}`} tono="warn" />
        <KPI label="Etapas del universo" valor={`${data.etapas_universo.length}`} />
      </div>

      {/* Matriz visual */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Matriz visual: producto × etapa</h2>
        <p className="mb-3 text-sm text-ink-500">🟢 etapa aplica · ⚪ no aplica</p>
        <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
          <table className="min-w-full text-xs">
            <thead className="bg-ink-50/40">
              <tr>
                <th className="sticky left-0 bg-ink-50/40 px-3 py-2 text-left font-semibold">Producto</th>
                <th className="px-3 py-2 text-right font-semibold">MSF</th>
                <th className="px-3 py-2 text-right font-semibold">Tiempo</th>
                {data.etapas_universo.map((e) => (
                  <th key={e.id} className="px-2 py-2 text-center font-medium" title={e.nombre}>
                    <div className="-rotate-45 origin-bottom-left text-[10px]" style={{ minWidth: '22px' }}>{e.id.split('_')[0]}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-50">
              {data.productos.map((p) => (
                <tr key={p.codigo} className="hover:bg-ink-50/30 cursor-pointer" onClick={() => setSelectedProd(p.codigo === selectedProd ? null : p.codigo)}>
                  <td className="sticky left-0 bg-white px-3 py-2 font-semibold">
                    {ICON_MMPP[p.codigo] ?? '🌿'} {p.codigo.replace('_', ' ')} <span className="text-ink-400">({p.variante})</span>
                  </td>
                  <td className="px-3 py-2 text-right tabular">{p.rendimiento_msf_pct > 0 ? `${(p.rendimiento_msf_pct * 100).toFixed(0)}%` : '—'}</td>
                  <td className="px-3 py-2 text-right tabular">{p.tiempo_proceso_min}m</td>
                  {etapaIds.map((eid) => {
                    const aplica = p.etapas_aplicables.includes(eid);
                    return (
                      <td key={eid} className="px-1 py-2 text-center">
                        {aplica ? (
                          <span className="inline-block h-3 w-3 rounded-full bg-brand" />
                        ) : (
                          <span className="inline-block h-3 w-3 rounded-full border border-ink-200" />
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Detalle producto */}
      {selected && (
        <section>
          <h2 className="mb-4 text-xl font-bold">
            {ICON_MMPP[selected.codigo] ?? '🌿'} {selected.codigo.replace('_', ' ')} · {selected.variante}
          </h2>
          <div className="rounded-2xl border border-ink-100 bg-white p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div>
                <p className="text-[10px] uppercase text-ink-400">Rendimiento MSF</p>
                <p className="text-2xl font-bold">
                  {selected.rendimiento_msf_pct > 0 ? `${(selected.rendimiento_msf_pct * 100).toFixed(0)}%` : 'PD'}
                </p>
              </div>
              <div>
                <p className="text-[10px] uppercase text-ink-400">Tiempo proceso</p>
                <p className="text-2xl font-bold">{selected.tiempo_proceso_min} min</p>
              </div>
              <div>
                <p className="text-[10px] uppercase text-ink-400">Etapas que aplica</p>
                <p className="text-2xl font-bold">{selected.cantidad_etapas} / {data.etapas_universo.length}</p>
              </div>
              <div>
                <p className="text-[10px] uppercase text-ink-400">Yield acumulado</p>
                <p className="text-2xl font-bold">{(selected.yield_acumulado_teorico * 100).toFixed(1)}%</p>
              </div>
            </div>

            {selected.notas && (
              <div className="rounded-lg bg-brand-50/40 border-l-3 border-brand p-3 text-sm">
                💡 {selected.notas}
              </div>
            )}

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-ink-500 mb-2">Etapas en orden</p>
              <div className="space-y-1">
                {selected.etapas_detalle.map((e) => (
                  <div key={e.id} className="flex items-center justify-between rounded-lg border border-ink-100 px-3 py-2 text-sm">
                    <span><strong>{e.orden}.</strong> {e.nombre}</span>
                    <span className="text-ink-500 tabular">
                      yield {(e.yield * 100).toFixed(0)}% · {e.tiempo_min} min
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Productos sin proceso */}
      <section>
        <h2 className="mb-4 text-xl font-bold">⚠️ Productos sin proceso definido</h2>
        <p className="mb-3 text-sm text-ink-500">
          Estos MMPP solo tienen Recepción registrada en el Excel. Falta definir si pasan por la línea Cold o Hot
          (o un proceso propio).
        </p>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {data.productos.filter((p) => !p.tiene_proceso_definido).map((p) => (
            <div key={p.codigo} className="rounded-xl border border-orange-200 bg-orange-50/40 p-4">
              <div className="flex items-center gap-2">
                <span className="text-xl">{ICON_MMPP[p.codigo] ?? '🌿'}</span>
                <p className="font-semibold">{p.codigo.replace('_', ' ')}</p>
                <span className="text-xs text-ink-500">({p.variante})</span>
              </div>
              <p className="mt-2 text-xs text-ink-600">{p.notas}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function KPI({ label, valor, tono }: { label: string; valor: string; tono?: 'ok' | 'warn' }) {
  const color = tono === 'ok' ? 'text-brand' : tono === 'warn' ? 'text-orange-600' : 'text-ink';
  return (
    <div className="rounded-xl border border-ink-100 bg-white p-4">
      <p className="text-[11px] uppercase text-ink-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold tabular ${color}`}>{valor}</p>
    </div>
  );
}
