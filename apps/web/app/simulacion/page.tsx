'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Maquina = {
  equipo_id: string; nombre: string; foto_url: string;
  capacidad_nominal_kg_h: number; throughput_efectivo_kg_h: number;
  utilizacion_pct: number; producto_kg: number;
  potencia_kw: number; kwh_consumidos: number;
  costo_electrico_clp: number; costo_arriendo_clp: number; costo_total_clp: number;
  es_bottleneck: boolean;
};

type Sim = {
  periodo: string;
  horas_operacion_dia: number;
  dias_operacion_mes: number;
  meses_operacion_ano: number;
  throughput_planta_kg_h: number;
  bottleneck_equipo: string;
  horas_totales_periodo: number;
  producto_total_kg: number;
  kwh_totales: number;
  costo_electrico_total_clp: number;
  costo_arriendo_total_clp: number;
  costo_total_clp: number;
  costo_unitario_clp_kg: number;
  maquinas: Maquina[];
  timeline_mensual: { mes: string; factor_estacional: number; producto_kg: number; costo_clp: number; operativo: boolean }[];
};

const MMPP_OPTIONS = ['TOMASA', 'ORUJO', 'ALPERUJO', 'POMASA'];

export default function SimulacionPage() {
  const [data, setData] = useState<Sim | null>(null);
  const [periodo, setPeriodo] = useState<'hora' | 'dia' | 'mes' | 'ano'>('mes');
  const [horas, setHoras] = useState(16);
  const [dias, setDias] = useState(25);
  const [meses, setMeses] = useState(10);
  const [mmpp, setMmpp] = useState('TOMASA');

  useEffect(() => {
    const url = `${ENGINE_URL}/simulacion/planta?periodo=${periodo}&horas_operacion_dia=${horas}&dias_operacion_mes=${dias}&meses_operacion_ano=${meses}&mmpp_principal=${mmpp}`;
    fetch(url).then((r) => r.json()).then(setData);
  }, [periodo, horas, dias, meses, mmpp]);

  if (!data) return <p className="text-ink-400">Simulando…</p>;

  const maxTimeline = Math.max(...data.timeline_mensual.map((m) => m.producto_kg), 1);

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Simulador temporal</p>
        <h1 className="mt-2 text-4xl font-bold">⏱ Producción y costos por periodo</h1>
        <p className="mt-2 text-ink-500">
          Cuánto produce la planta y cuánto cuesta — por hora, día, mes o año. Con bottleneck real y estacionalidad MMPP.
        </p>
      </header>

      {/* Tabs periodo */}
      <section className="rounded-2xl border border-ink-100 bg-white p-6 space-y-5">
        <div className="flex flex-wrap items-center gap-2">
          {(['hora', 'dia', 'mes', 'ano'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriodo(p)}
              className={`rounded-full px-5 py-2 text-sm font-semibold capitalize ${
                periodo === p ? 'bg-ink text-white' : 'bg-ink-50 text-ink-600'
              }`}
            >
              {p === 'ano' ? 'Año' : p}
            </button>
          ))}
          <span className="ml-auto text-xs text-ink-400">
            Total: <strong className="text-ink">{data.horas_totales_periodo.toLocaleString()} h</strong>
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Slider label="Horas/día" value={horas} min={1} max={24} step={1} onChange={setHoras} unit="h" />
          <Slider label="Días/mes" value={dias} min={1} max={31} step={1} onChange={setDias} unit="d" />
          <Slider label="Meses/año" value={meses} min={1} max={12} step={1} onChange={setMeses} unit="m" />
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-ink-600">MMPP principal (estacionalidad):</label>
          <select value={mmpp} onChange={(e) => setMmpp(e.target.value)}
            className="rounded border border-ink-200 px-3 py-1 text-sm">
            {MMPP_OPTIONS.map((m) => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>
      </section>

      {/* KPIs principales */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KPI label="Producto total" valor={`${(data.producto_total_kg / 1000).toFixed(2)} t`} sub={`${data.producto_total_kg.toLocaleString()} kg`} tono="ok" />
        <KPI label="Costo total" valor={`$${(data.costo_total_clp / 1e6).toFixed(1)}M CLP`} sub={`USD $${(data.costo_total_clp / 920 / 1e3).toFixed(0)}k`} />
        <KPI label="Costo unitario" valor={`$${data.costo_unitario_clp_kg.toLocaleString()} CLP/kg`} sub={`USD $${(data.costo_unitario_clp_kg / 920).toFixed(2)}/kg`} />
        <KPI label="kWh totales" valor={`${data.kwh_totales.toLocaleString()}`} sub={`${data.horas_totales_periodo.toLocaleString()} h operación`} />
      </div>

      {/* Bottleneck */}
      <section className="rounded-2xl bg-orange-50 border-l-4 border-orange-500 p-5">
        <p className="text-xs font-semibold uppercase tracking-wider text-orange-700">⚠️ Cuello de botella detectado</p>
        <p className="mt-1 text-lg font-bold text-orange-900">
          {data.bottleneck_equipo} → Throughput planta limitado a {data.throughput_planta_kg_h} kg/h
        </p>
        <p className="mt-1 text-sm text-orange-800">
          Todas las máquinas aguas arriba operan subutilizadas por este equipo. Ampliar capacidad acá libera el resto.
        </p>
      </section>

      {/* Timeline mensual */}
      {data.timeline_mensual.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold">📅 Producción mensual con estacionalidad ({mmpp})</h2>
          <div className="rounded-xl border border-ink-100 bg-white p-5">
            <div className="space-y-2">
              {data.timeline_mensual.map((m) => {
                const pct = (m.producto_kg / maxTimeline) * 100;
                return (
                  <div key={m.mes} className="grid grid-cols-12 items-center gap-3 text-sm">
                    <div className="col-span-1 font-semibold">{m.mes}</div>
                    <div className="col-span-7">
                      <div className="h-5 overflow-hidden rounded-full bg-ink-50">
                        <div
                          className={`h-full rounded-full ${m.operativo ? 'bg-gradient-to-r from-brand to-brand-light' : 'bg-ink-200'}`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                    <div className="col-span-2 text-right tabular">{(m.producto_kg / 1000).toFixed(2)} t</div>
                    <div className="col-span-2 text-right tabular text-ink-500">${(m.costo_clp / 1e6).toFixed(1)}M</div>
                  </div>
                );
              })}
            </div>
            <p className="mt-4 text-xs text-ink-400">
              Factor estacional según disponibilidad de {mmpp}. 0% = mes no operativo.
            </p>
          </div>
        </section>
      )}

      {/* Tabla por máquina */}
      <section>
        <h2 className="mb-4 text-xl font-bold">⚙️ Detalle por máquina ({data.maquinas.length})</h2>
        <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-ink-50/40 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-3 py-2 text-left">Equipo</th>
                <th className="px-3 py-2 text-right">Capacidad</th>
                <th className="px-3 py-2 text-right">Real</th>
                <th className="px-3 py-2 text-right">Uso</th>
                <th className="px-3 py-2 text-right">Producto</th>
                <th className="px-3 py-2 text-right">kW</th>
                <th className="px-3 py-2 text-right">kWh</th>
                <th className="px-3 py-2 text-right">Eléctrico</th>
                <th className="px-3 py-2 text-right">Arriendo</th>
                <th className="px-3 py-2 text-right">Total CLP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-50">
              {data.maquinas.sort((a, b) => b.costo_total_clp - a.costo_total_clp).map((m) => (
                <tr key={m.equipo_id} className={m.es_bottleneck ? 'bg-orange-50' : ''}>
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-2">
                      {m.foto_url && <img src={m.foto_url} alt="" className="w-8 h-8 object-cover rounded" />}
                      <div>
                        <p className="font-semibold text-xs">{m.nombre.slice(0, 38)}</p>
                        {m.es_bottleneck && <span className="text-[10px] font-bold text-orange-600">⚠ BOTTLENECK</span>}
                      </div>
                    </div>
                  </td>
                  <td className="px-3 py-2 text-right tabular">{m.capacidad_nominal_kg_h.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right tabular">{m.throughput_efectivo_kg_h.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right tabular">{(m.utilizacion_pct * 100).toFixed(1)}%</td>
                  <td className="px-3 py-2 text-right tabular">{m.producto_kg.toLocaleString()} kg</td>
                  <td className="px-3 py-2 text-right tabular">{m.potencia_kw}</td>
                  <td className="px-3 py-2 text-right tabular">{m.kwh_consumidos.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right tabular">${m.costo_electrico_clp.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right tabular">{m.costo_arriendo_clp > 0 ? `$${m.costo_arriendo_clp.toLocaleString()}` : '—'}</td>
                  <td className="px-3 py-2 text-right tabular font-bold text-brand">${m.costo_total_clp.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Slider({ label, value, min, max, step, onChange, unit }: { label: string; value: number; min: number; max: number; step: number; onChange: (x: number) => void; unit: string }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <label className="text-xs text-ink-500">{label}</label>
        <span className="text-lg font-bold tabular">{value} {unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(+e.target.value)} className="w-full accent-brand mt-1" />
    </div>
  );
}

function KPI({ label, valor, sub, tono }: { label: string; valor: string; sub?: string; tono?: 'ok' }) {
  const cls = tono === 'ok' ? 'text-brand' : 'text-ink';
  return (
    <div className="rounded-xl border border-ink-100 bg-white p-4">
      <p className="text-[11px] uppercase text-ink-400">{label}</p>
      <p className={`mt-1 text-xl font-bold tabular ${cls}`}>{valor}</p>
      {sub && <p className="text-xs text-ink-400">{sub}</p>}
    </div>
  );
}
