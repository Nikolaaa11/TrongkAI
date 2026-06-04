'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Analisis = {
  con_pef: any;
  sin_pef: any;
  diferencia_clp_h: number;
  diferencia_clp_kg: number;
  diferencia_pct: number;
  breakeven_pct_reduccion_tiempo: number;
  recomendacion: string;
  drivers_clave: string[];
  supuestos: Record<string, any>;
};

type Sensibilidad = {
  rangos: { pct_reduccion_secado: number; diferencia_clp_h: number; diferencia_clp_kg: number; pef_es_mejor: boolean }[];
};

export default function PEFAnalisisPage() {
  const [data, setData] = useState<Analisis | null>(null);
  const [sens, setSens] = useState<Sensibilidad | null>(null);
  const [throughput, setThroughput] = useState(2000);
  const [reduccionSecado, setReduccionSecado] = useState(0.30);
  const [upliftYield, setUpliftYield] = useState(0.05);
  const [pasadas, setPasadas] = useState(1);
  const [premium, setPremium] = useState(0.10);
  const [precioVenta, setPrecioVenta] = useState(850);

  useEffect(() => {
    const url = `${ENGINE_URL}/pef/analisis?throughput_kg_h=${throughput}&pct_reduccion_tiempo_secado=${reduccionSecado}&pct_uplift_yield=${upliftYield}&pasadas_pef=${pasadas}&pct_premium_pef=${premium}&precio_venta_clp_kg=${precioVenta}`;
    fetch(url).then((r) => r.json()).then(setData);
    fetch(`${ENGINE_URL}/pef/sensibilidad?throughput_kg_h=${throughput}`).then((r) => r.json()).then(setSens);
  }, [throughput, reduccionSecado, upliftYield, pasadas, premium, precioVenta]);

  if (!data) return <p className="text-ink-400">Analizando PEF…</p>;

  const margenCon = data.supuestos.margen_con_clp_h || 0;
  const margenSin = data.supuestos.margen_sin_clp_h || 0;
  const diffMargen = data.supuestos.diff_margen_clp_h || 0;
  const isPefBetter = diffMargen > 0;

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Pregunta 3 del equipo</p>
        <h1 className="mt-2 text-4xl font-bold">⚡ Análisis económico PEF</h1>
        <p className="mt-2 text-ink-500">
          ¿Se justifica económicamente usar PEF? Comparativa A/B con tus respuestas:
          <strong> 1 pasada default</strong>, alimentación continua de info por equipo.
        </p>
      </header>

      {/* Recomendación destacada */}
      <section className={`rounded-2xl p-6 ${isPefBetter ? 'bg-brand-50 border border-brand' : 'bg-orange-50 border border-orange-400'}`}>
        <p className="text-xs font-semibold uppercase tracking-wider text-ink-500">Recomendación motor</p>
        <p className={`mt-2 text-xl font-semibold ${isPefBetter ? 'text-brand' : 'text-orange-700'}`}>
          {data.recomendacion}
        </p>
      </section>

      {/* Sliders */}
      <section className="rounded-2xl border border-ink-100 bg-white p-6 space-y-5">
        <h2 className="text-lg font-bold">🎚 Variables para evaluar</h2>
        <Slider label="Throughput" value={throughput} min={500} max={5000} step={100} onChange={setThroughput} unit="kg/h" />
        <Slider label="% reducción tiempo secado" value={reduccionSecado} min={0} max={0.8} step={0.05} onChange={setReduccionSecado} unit="" format={(v) => `${(v * 100).toFixed(0)}%`} />
        <Slider label="% uplift yield extracción (PEF habilita)" value={upliftYield} min={0} max={0.30} step={0.01} onChange={setUpliftYield} unit="" format={(v) => `${(v * 100).toFixed(0)}%`} />
        <Slider label="% premium price (calidad PEF)" value={premium} min={0} max={0.30} step={0.01} onChange={setPremium} unit="" format={(v) => `${(v * 100).toFixed(0)}%`} />
        <Slider label="Precio venta promedio" value={precioVenta} min={400} max={3000} step={50} onChange={setPrecioVenta} unit="CLP/kg" />
        <div className="flex items-center gap-3">
          <label className="text-sm text-ink-600 flex-1">Pasadas PEF (default 1 según tu respuesta)</label>
          <select value={pasadas} onChange={(e) => setPasadas(+e.target.value)} className="rounded border border-ink-200 px-3 py-1 text-sm">
            <option value={1}>1 pasada</option>
            <option value={2}>2 pasadas</option>
            <option value={3}>3 pasadas</option>
          </select>
        </div>
      </section>

      {/* A vs B */}
      <section className="grid gap-4 md:grid-cols-2">
        <Escenario titulo="🔴 CON PEF" data={data.con_pef} margen={margenCon} highlight={isPefBetter} />
        <Escenario titulo="🟢 SIN PEF (directo)" data={data.sin_pef} margen={margenSin} highlight={!isPefBetter} />
      </section>

      {/* Sensibilidad */}
      {sens && (
        <section>
          <h2 className="mb-4 text-xl font-bold">📊 Sensibilidad: ¿cuánto necesita reducir el secado para empatar?</h2>
          <div className="rounded-xl border border-ink-100 bg-white overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-ink-50/40 text-xs uppercase text-ink-500">
                <tr>
                  <th className="px-4 py-2 text-left">% reducción secado</th>
                  <th className="px-4 py-2 text-right">Diferencia CLP/h</th>
                  <th className="px-4 py-2 text-right">Diferencia CLP/kg</th>
                  <th className="px-4 py-2 text-center">PEF mejor?</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-50">
                {sens.rangos.map((r) => (
                  <tr key={r.pct_reduccion_secado} className={r.pef_es_mejor ? 'bg-brand-50/30' : ''}>
                    <td className="px-4 py-2 font-medium">{(r.pct_reduccion_secado * 100).toFixed(0)}%</td>
                    <td className="px-4 py-2 text-right tabular">${r.diferencia_clp_h.toLocaleString()}</td>
                    <td className="px-4 py-2 text-right tabular">${r.diferencia_clp_kg.toLocaleString()}</td>
                    <td className="px-4 py-2 text-center text-lg">{r.pef_es_mejor ? '✅' : '❌'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Drivers + Insight calor residual */}
      <section className="rounded-2xl bg-yellow-50 border-l-4 border-yellow-500 p-5">
        <h3 className="text-lg font-bold text-yellow-900">💡 Insight crítico (calor residual barato)</h3>
        <p className="mt-2 text-sm text-yellow-900">
          Como La Gloria entrega calor residual a precio simbólico ($5 CLP/kWh vs $110 eléctrico),
          el ahorro por reducir tiempo de secado es <strong>marginal</strong>.
          El PEF (arriendo ~$18.5M CLP/mes) solo se justifica si genera <strong>uplift de yield</strong> y/o
          <strong> premium price</strong> por calidad/bioactivos preservados.
        </p>
        <p className="mt-2 text-sm font-semibold text-yellow-900">
          → Necesitamos validar: % de yield extra real + precio premium efectivo (lo que vas a alimentar por equipo).
        </p>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-bold">🔑 Drivers clave (orden de impacto)</h2>
        <ol className="space-y-2">
          {data.drivers_clave.map((d, i) => (
            <li key={i} className="rounded-lg bg-white border border-ink-100 px-4 py-3 text-sm">
              <strong className="text-brand">{i + 1}.</strong> {d}
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-bold">📋 Supuestos del análisis</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          {Object.entries(data.supuestos).map(([k, v]) => (
            <div key={k} className="rounded-xl border border-ink-100 bg-white p-3">
              <p className="text-[10px] uppercase text-ink-400">{k.replace(/_/g, ' ')}</p>
              <p className="mt-1 text-base font-bold tabular">{typeof v === 'number' ? v.toLocaleString() : v}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Slider({ label, value, min, max, step, onChange, unit, format }: { label: string; value: number; min: number; max: number; step: number; onChange: (x: number) => void; unit: string; format?: (v: number) => string }) {
  const formatted = format ? format(value) : value.toLocaleString();
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <label className="text-sm text-ink-600">{label}</label>
        <span className="text-lg font-bold tabular">{formatted} {unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(+e.target.value)} className="w-full accent-brand mt-1" />
    </div>
  );
}

function Escenario({ titulo, data, margen, highlight }: { titulo: string; data: any; margen: number; highlight: boolean }) {
  return (
    <div className={`rounded-2xl border-2 p-6 ${highlight ? 'border-brand bg-brand-50/30' : 'border-ink-100 bg-white'}`}>
      <h3 className="text-lg font-bold">{titulo}</h3>
      <p className="mt-2 text-sm text-ink-500">{data.nombre}</p>
      <div className="mt-4 space-y-2">
        <Row label="Tiempo secado" valor={`${data.tiempo_secado_min.toFixed(0)} min`} />
        <Row label="Yield extracción" valor={`${(data.yield_extraccion_pct * 100).toFixed(1)}%`} />
        <Row label="Producto generado" valor={`${data.producto_kg_h.toFixed(0)} kg/h`} />
        <Row label="Arriendo PEF" valor={`$${data.costo_arriendo_pef_clp_h.toLocaleString()}`} />
        <Row label="Eléctrico PEF" valor={`$${data.costo_electrico_pef_clp_h.toLocaleString()}`} />
        <Row label="Electrodos" valor={`$${data.costo_electrodos_clp_h.toLocaleString()}`} />
        <Row label="Secado (calor residual)" valor={`$${data.costo_secado_clp_h.toLocaleString()}`} />
        <Row label="COSTO TOTAL/h" valor={`$${data.costo_total_clp_h.toLocaleString()}`} bold />
        <Row label="Costo unitario" valor={`$${data.costo_unitario_clp_kg.toLocaleString()} CLP/kg`} bold />
      </div>
      <div className={`mt-4 rounded-lg p-3 ${margen > 0 ? 'bg-brand-50' : 'bg-orange-50'}`}>
        <p className="text-xs uppercase text-ink-500">MARGEN OPERATIVO</p>
        <p className={`mt-1 text-2xl font-bold ${margen > 0 ? 'text-brand' : 'text-orange-600'}`}>
          ${margen.toLocaleString()} CLP/h
        </p>
      </div>
    </div>
  );
}

function Row({ label, valor, bold }: { label: string; valor: string; bold?: boolean }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-ink-500">{label}</span>
      <span className={`tabular ${bold ? 'font-bold' : ''}`}>{valor}</span>
    </div>
  );
}
