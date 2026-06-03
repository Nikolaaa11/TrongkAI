'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Etapa = {
  id: string;
  nombre: string;
  orden: number;
  descripcion: string;
  masa_input_kg_h: number;
  masa_output_kg_h: number;
  yield_pct: number;
  perdidas_kg_h: number;
  energia_kwh_por_kg: number;
  agua_l_por_kg: number;
  hh_por_ton_input: number;
  consumo_energia_kwh_h: number;
  consumo_agua_l_h: number;
  utilizacion_pct: number;
  es_bottleneck: boolean;
  datos_completitud_pct: number;
  nivel_calibracion: 'PD' | 'OK_PROVISORIO' | 'OK_VALIDADO';
  datos_faltantes: string[];
  capacidad: { valor_maximo: number; unidad: string };
};

type Balance = {
  etapas: Etapa[];
  masa_entrada_total_kg_h: number;
  masa_salida_final_kg_h: number;
  yield_total_proceso: number;
  energia_total_kwh_h: number;
  agua_total_l_h: number;
  hh_totales_turno: number;
  bottlenecks: string[];
  completitud_datos_pct: number;
  intensidades_acumuladas: Record<string, number>;
  alarmas: any[];
};

const NIVEL_COLOR: Record<string, string> = {
  PD: 'bg-red-50 text-red-700 ring-red-200',
  OK_PROVISORIO: 'bg-yellow-50 text-yellow-700 ring-yellow-200',
  OK_VALIDADO: 'bg-brand-50 text-brand ring-brand/30',
};

const NIVEL_DOT: Record<string, string> = {
  PD: 'bg-red-500',
  OK_PROVISORIO: 'bg-yellow-500',
  OK_VALIDADO: 'bg-brand',
};

export default function BalanceEtapasPage() {
  const [data, setData] = useState<Balance | null>(null);
  const [throughput, setThroughput] = useState(2000);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/balance/etapas?throughput_kg_h=${throughput}`)
      .then((r) => r.json())
      .then(setData);
  }, [throughput]);

  if (!data) return <p className="text-ink-400">Cargando balance por etapas…</p>;

  const selected = selectedId ? data.etapas.find((e) => e.id === selectedId) : null;

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Balance por etapas · proceso completo</p>
        <h1 className="mt-2 text-4xl font-bold">🏭 12 etapas de la planta Trongkai</h1>
        <p className="mt-2 text-ink-500">
          De MMPP a producto final. Cambia el throughput y todo se recalcula dinámicamente.
        </p>
      </header>

      {/* Slider throughput */}
      <section className="rounded-2xl border border-ink-100 bg-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-ink-500">Throughput nominal</p>
            <p className="mt-1 text-3xl font-bold">{throughput.toLocaleString()} kg/h</p>
            <p className="text-xs text-ink-400">
              {(throughput * 16 / 1000).toFixed(1)} t/día · {((throughput * 16 * 300) / 1000).toFixed(0)} t/año
            </p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <p className="text-xs text-ink-400">Ajusta el caudal de entrada</p>
            <input
              type="range"
              min="500"
              max="5000"
              step="100"
              value={throughput}
              onChange={(e) => setThroughput(+e.target.value)}
              className="w-64 accent-brand"
            />
            <div className="flex w-64 justify-between text-[10px] text-ink-400">
              <span>500</span><span>2.5k</span><span>5k kg/h</span>
            </div>
          </div>
        </div>
      </section>

      {/* KPIs globales */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <KPI label="Entrada MMPP" valor={`${(data.masa_entrada_total_kg_h / 1000).toFixed(1)} t/h`} />
        <KPI label="Producto final" valor={`${(data.masa_salida_final_kg_h / 1000).toFixed(2)} t/h`} />
        <KPI label="Yield total" valor={`${(data.yield_total_proceso * 100).toFixed(1)}%`} />
        <KPI label="Energía" valor={`${data.energia_total_kwh_h.toFixed(0)} kWh/h`} />
        <KPI label="Agua" valor={`${data.agua_total_l_h.toFixed(0)} L/h`} />
        <KPI label="HH/turno" valor={`${data.hh_totales_turno.toFixed(1)} h`} />
      </div>

      {/* Completitud de datos */}
      <section className="rounded-2xl border border-ink-100 bg-white p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-ink-500">Calibración del modelo</p>
            <p className="mt-1 text-3xl font-bold">
              {data.completitud_datos_pct.toFixed(0)}<span className="text-lg text-ink-400">/100</span>
            </p>
            <p className="text-xs text-ink-400">Promedio de calidad de datos por etapa</p>
          </div>
          <div className="flex gap-3 text-xs">
            <Legend dot="bg-brand" label="Validado planta" />
            <Legend dot="bg-yellow-500" label="Provisorio (literatura)" />
            <Legend dot="bg-red-500" label="Sin validar (PD)" />
          </div>
        </div>
        <div className="mt-4 h-3 overflow-hidden rounded-full bg-ink-100">
          <div className="h-full bg-gradient-to-r from-red-400 via-yellow-400 to-brand transition-all"
            style={{ width: `${data.completitud_datos_pct}%` }} />
        </div>
      </section>

      {/* Alarmas */}
      {data.alarmas.length > 0 && (
        <section>
          <h2 className="mb-3 text-xl font-bold">Alarmas activas en el proceso ({data.alarmas.length})</h2>
          <div className="space-y-2">
            {data.alarmas.slice(0, 8).map((a, i) => (
              <div key={i} className={`rounded-xl border p-3 ${a.severidad === 'alta' ? 'border-orange-200 bg-orange-50' : 'border-ink-100 bg-white'}`}>
                <p className="text-sm font-semibold">{a.mensaje}</p>
                {a.accion && <p className="mt-0.5 text-xs text-ink-500">→ {a.accion}</p>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Flujo de etapas */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Flujo del proceso · click en cada etapa para detalle</h2>
        <div className="space-y-2">
          {data.etapas.map((e, i) => {
            const isLast = i === data.etapas.length - 1;
            const isSelected = selectedId === e.id;
            return (
              <div key={e.id}>
                <button
                  onClick={() => setSelectedId(isSelected ? null : e.id)}
                  className={`w-full rounded-2xl border p-4 text-left transition-all hover:shadow-md ${
                    isSelected ? 'border-brand bg-brand-50/30' : 'border-ink-100 bg-white'
                  } ${e.es_bottleneck ? 'ring-2 ring-orange-300' : ''}`}
                >
                  <div className="grid grid-cols-12 items-center gap-3">
                    {/* Numero */}
                    <div className="col-span-1 flex justify-center">
                      <div className={`flex h-10 w-10 items-center justify-center rounded-full font-bold ${
                        e.es_bottleneck ? 'bg-orange-500 text-white' : 'bg-ink text-white'
                      }`}>
                        {e.orden}
                      </div>
                    </div>
                    {/* Nombre + nivel */}
                    <div className="col-span-3">
                      <p className="text-sm font-semibold">{e.nombre.replace(/^\d+\.\s*/, '')}</p>
                      <div className="mt-1 flex items-center gap-2">
                        <span className={`inline-block h-2 w-2 rounded-full ${NIVEL_DOT[e.nivel_calibracion]}`} />
                        <span className="text-[10px] uppercase text-ink-400">{e.nivel_calibracion}</span>
                      </div>
                    </div>
                    {/* Masa flow */}
                    <div className="col-span-3 text-xs">
                      <span className="text-ink-500">In:</span> <strong>{e.masa_input_kg_h.toFixed(0)} kg/h</strong>
                      <span className="ml-2 text-ink-400">→</span>
                      <span className="ml-2 text-ink-500">Out:</span> <strong>{e.masa_output_kg_h.toFixed(0)} kg/h</strong>
                      <p className="mt-0.5 text-[10px] text-ink-400">Yield {(e.yield_pct * 100).toFixed(0)}% · perdidas {e.perdidas_kg_h.toFixed(1)} kg/h</p>
                    </div>
                    {/* Consumos */}
                    <div className="col-span-3 text-xs">
                      <div>⚡ <strong>{e.consumo_energia_kwh_h.toFixed(1)} kWh/h</strong></div>
                      <div>💧 <strong>{e.consumo_agua_l_h.toFixed(0)} L/h</strong></div>
                      <div>👤 <strong>{e.hh_por_ton_input.toFixed(2)} HH/t</strong></div>
                    </div>
                    {/* Utilización */}
                    <div className="col-span-2">
                      <div className="flex items-baseline justify-between text-xs">
                        <span className="text-ink-500">Capacidad</span>
                        <span className={`font-semibold ${e.es_bottleneck ? 'text-orange-600' : ''}`}>
                          {(e.utilizacion_pct * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-ink-100">
                        <div className={`h-full ${e.es_bottleneck ? 'bg-orange-500' : 'bg-brand'}`}
                          style={{ width: `${Math.min(100, e.utilizacion_pct * 100)}%` }} />
                      </div>
                      {e.es_bottleneck && <p className="mt-0.5 text-[10px] font-bold text-orange-600">⚠ BOTTLENECK</p>}
                    </div>
                  </div>
                </button>

                {/* Detalle expandido */}
                {isSelected && (
                  <div className="ml-12 mt-2 mb-3 rounded-xl bg-ink-50/40 p-5">
                    <p className="text-sm italic text-ink-600">{e.descripcion}</p>
                    <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
                      <div>
                        <p className="text-[10px] uppercase text-ink-400">Capacidad max</p>
                        <p className="font-semibold">{e.capacidad.valor_maximo.toFixed(0)} {e.capacidad.unidad}</p>
                      </div>
                      <div>
                        <p className="text-[10px] uppercase text-ink-400">Energía unitaria</p>
                        <p className="font-semibold">{e.energia_kwh_por_kg.toFixed(4)} kWh/kg</p>
                      </div>
                      <div>
                        <p className="text-[10px] uppercase text-ink-400">Agua unitaria</p>
                        <p className="font-semibold">{e.agua_l_por_kg.toFixed(2)} L/kg</p>
                      </div>
                      <div>
                        <p className="text-[10px] uppercase text-ink-400">Completitud datos</p>
                        <p className="font-semibold">{e.datos_completitud_pct.toFixed(0)}%</p>
                      </div>
                    </div>
                    {e.datos_faltantes.length > 0 && (
                      <div className="mt-4">
                        <p className="text-xs font-semibold uppercase tracking-wider text-ink-500">📋 Datos pendientes para calibrar</p>
                        <ul className="mt-2 space-y-1">
                          {e.datos_faltantes.map((d, j) => (
                            <li key={j} className={`text-sm ${e.nivel_calibracion === 'PD' ? 'text-red-600' : 'text-yellow-700'}`}>
                              • {d}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                {!isLast && (
                  <div className="ml-[1.7rem] my-1 h-3 w-0.5 bg-ink-200" />
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* Intensidades acumuladas */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Intensidades del proceso completo</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {Object.entries(data.intensidades_acumuladas).map(([k, v]) => (
            <div key={k} className="rounded-xl border border-ink-100 bg-white p-4">
              <p className="text-[10px] uppercase text-ink-400">{k.replace(/_/g, ' ')}</p>
              <p className="mt-1 text-lg font-bold tabular">{v.toFixed(2)}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function KPI({ label, valor }: { label: string; valor: string }) {
  return (
    <div className="rounded-xl border border-ink-100 bg-white p-4">
      <p className="text-[11px] uppercase text-ink-400">{label}</p>
      <p className="mt-1 text-xl font-bold tabular">{valor}</p>
    </div>
  );
}

function Legend({ dot, label }: { dot: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={`inline-block h-2 w-2 rounded-full ${dot}`} />
      <span className="text-ink-500">{label}</span>
    </div>
  );
}
