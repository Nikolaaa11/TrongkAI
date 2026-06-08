'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Escala = {
  escala: number;
  etiqueta: string;
  producto_kg_ano: number;
  producto_t_ano: number;
  costo_total_clp: number;
  costo_unitario_clp_kg: number;
  revenue_clp: number;
  margen_clp: number;
  margen_pct: number;
  capex_clp: number;
  capex_usd: number;
  payback_anos: number | null;
  factor_aprendizaje: number;
};

type Resp = {
  base_piloto: any;
  escalas: Escala[];
  supuestos: { curva_aprendizaje_exp: number; capex_williams_exp: number; nota: string };
};

const SKUS = [
  { id: 'harina_animal_basica', label: 'Harina animal básica', precio: 850 },
  { id: 'harina_animal_premium', label: 'Harina animal premium (PEF)', precio: 1400 },
  { id: 'ingrediente_humano', label: 'Ingrediente humano', precio: 4500 },
  { id: 'nutraceutico_premium', label: 'Nutracéutico premium', precio: 12000 },
];

export default function EscalasPage() {
  const [data, setData] = useState<Resp | null>(null);
  const [horas, setHoras] = useState(16);
  const [dias, setDias] = useState(25);
  const [meses, setMeses] = useState(10);
  const [mmpp, setMmpp] = useState('TOMASA');
  const [sku, setSku] = useState('harina_animal_premium');

  useEffect(() => {
    const url = `${ENGINE_URL}/simulacion/escalas?horas_dia=${horas}&dias_mes=${dias}&meses_ano=${meses}&mmpp_principal=${mmpp}&sku_principal=${sku}`;
    fetch(url).then((r) => r.json()).then(setData);
  }, [horas, dias, meses, mmpp, sku]);

  if (!data) return <p className="text-ink-400">Calculando escalas...</p>;

  const maxMargen = Math.max(...data.escalas.map((e) => Math.abs(e.margen_clp)));

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Economías de escala</p>
        <h1 className="mt-2 text-4xl font-bold">📈 Piloto vs Industrial</h1>
        <p className="mt-2 text-ink-500">
          ¿Qué pasa si la planta crece x10, x50, x100? Curva 80% costo + Williams 0.7 CAPEX.
        </p>
      </header>

      {/* Controles */}
      <section className="rounded-2xl border border-ink-100 bg-white p-6 space-y-5">
        <div className="grid gap-4 md:grid-cols-3">
          <Slider label="Horas/día" value={horas} min={1} max={24} onChange={setHoras} unit="h" />
          <Slider label="Días/mes" value={dias} min={1} max={31} onChange={setDias} unit="d" />
          <Slider label="Meses/año" value={meses} min={1} max={12} onChange={setMeses} unit="m" />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs text-ink-500">MMPP principal</label>
            <select value={mmpp} onChange={(e) => setMmpp(e.target.value)}
              className="w-full mt-1 rounded border border-ink-200 px-3 py-2 text-sm">
              {['TOMASA', 'ORUJO', 'ALPERUJO', 'POMASA'].map((m) => <option key={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-ink-500">SKU principal (precio venta)</label>
            <select value={sku} onChange={(e) => setSku(e.target.value)}
              className="w-full mt-1 rounded border border-ink-200 px-3 py-2 text-sm">
              {SKUS.map((s) => <option key={s.id} value={s.id}>{s.label} (${s.precio.toLocaleString()} CLP/kg)</option>)}
            </select>
          </div>
        </div>
      </section>

      {/* Tabla comparativa */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Comparativa de escalas</h2>
        <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-ink-50/40 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-3 py-3 text-left">Escala</th>
                <th className="px-3 py-3 text-right">Producto</th>
                <th className="px-3 py-3 text-right">Costo unit</th>
                <th className="px-3 py-3 text-right">Revenue</th>
                <th className="px-3 py-3 text-right">Margen</th>
                <th className="px-3 py-3 text-right">Margen %</th>
                <th className="px-3 py-3 text-right">CAPEX</th>
                <th className="px-3 py-3 text-right">Payback</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-50">
              {data.escalas.map((e) => (
                <tr key={e.escala} className={e.margen_clp > 0 ? '' : 'bg-orange-50/60'}>
                  <td className="px-3 py-3 font-bold text-lg">{e.etiqueta}</td>
                  <td className="px-3 py-3 text-right tabular">{e.producto_t_ano.toLocaleString()} t/año</td>
                  <td className="px-3 py-3 text-right tabular">${e.costo_unitario_clp_kg.toLocaleString()}/kg</td>
                  <td className="px-3 py-3 text-right tabular">${(e.revenue_clp / 1e6).toFixed(0)}M</td>
                  <td className={`px-3 py-3 text-right tabular font-bold ${e.margen_clp > 0 ? 'text-brand' : 'text-orange-600'}`}>
                    {e.margen_clp > 0 ? '+' : ''}${(e.margen_clp / 1e6).toFixed(0)}M
                  </td>
                  <td className={`px-3 py-3 text-right tabular font-semibold ${e.margen_pct > 0 ? 'text-brand' : 'text-orange-600'}`}>
                    {(e.margen_pct * 100).toFixed(1)}%
                  </td>
                  <td className="px-3 py-3 text-right tabular">${(e.capex_clp / 1e6).toFixed(0)}M CLP</td>
                  <td className="px-3 py-3 text-right tabular font-semibold">
                    {e.payback_anos !== null ? `${e.payback_anos.toFixed(1)} años` : '∞'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Gráfico de margen visual */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Margen operativo por escala</h2>
        <div className="rounded-xl border border-ink-100 bg-white p-5">
          <div className="space-y-3">
            {data.escalas.map((e) => {
              const pct = Math.abs(e.margen_clp) / maxMargen * 100;
              const negativo = e.margen_clp < 0;
              return (
                <div key={e.escala} className="grid grid-cols-12 items-center gap-3 text-sm">
                  <div className="col-span-1 font-bold">{e.etiqueta}</div>
                  <div className="col-span-9">
                    <div className="h-7 overflow-hidden rounded-full bg-ink-50 relative">
                      <div
                        className={`h-full rounded-full ${negativo ? 'bg-orange-500' : 'bg-gradient-to-r from-brand to-brand-light'}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                  <div className={`col-span-2 text-right tabular font-bold ${negativo ? 'text-orange-600' : 'text-brand'}`}>
                    {negativo ? '−' : '+'}${(Math.abs(e.margen_clp) / 1e6).toFixed(0)}M CLP
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Insights */}
      <section className="rounded-2xl bg-blue-50 border-l-4 border-blue-500 p-5">
        <h3 className="text-lg font-bold text-blue-900">💡 Insight estratégico</h3>
        <p className="mt-2 text-sm text-blue-900">
          El <strong>piloto solo</strong> no es rentable: arriendo PEF ($18.5M/mes) + bajo throughput (prensa 25 kg/h) + yield real ~27.5% generan costo unitario alto.
        </p>
        <p className="mt-2 text-sm text-blue-900">
          <strong>El SKU define la rentabilidad:</strong> la harina animal ($1.400/kg) es commodity de bajo margen incluso a escala. El negocio rentable está en <strong>SKU de alto valor</strong>: ingrediente humano ($4.500/kg, rentable desde x10) y nutracéutico premium ($12.000/kg, rentable ya en piloto). Cambiá el SKU arriba para verlo.
        </p>
        <p className="mt-2 text-sm text-blue-900">
          <strong>Camino sugerido:</strong> piloto valida calidad + foco comercial en SKU premium → ampliar prensa (cuello de botella) → ramping industrial.
        </p>
      </section>

      <section>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-ink-500">Supuestos del modelo</h3>
        <div className="rounded-xl bg-ink-50/40 p-4 text-sm text-ink-600 space-y-1">
          <p>• Curva 80% costo unit: cada duplicación de producción → 20% menos costo unitario.</p>
          <p>• Williams 0.7 CAPEX: equipos más grandes cuestan sub-linealmente (factor escala 10x → 5x CAPEX).</p>
          <p>• Precio venta constante: asume mismo segmento de mercado al escalar.</p>
          <p>• Operación intensiva: {horas}h/día × {dias}d/mes × {meses}meses/año = {(horas * dias * meses).toLocaleString()} h/año.</p>
        </div>
      </section>
    </div>
  );
}

function Slider({ label, value, min, max, onChange, unit }: { label: string; value: number; min: number; max: number; onChange: (x: number) => void; unit: string }) {
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <label className="text-xs text-ink-500">{label}</label>
        <span className="text-lg font-bold tabular">{value} {unit}</span>
      </div>
      <input type="range" min={min} max={max} value={value}
        onChange={(e) => onChange(+e.target.value)} className="w-full accent-brand mt-1" />
    </div>
  );
}
