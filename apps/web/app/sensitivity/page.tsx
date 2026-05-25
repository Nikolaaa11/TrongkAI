'use client';

import { useEffect, useState } from 'react';
import { HeatmapChart, type HeatmapData } from '@/components/HeatmapChart';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Driver = 'precio' | 'costo_mmpp' | 'wacc' | 'opex';

const DRIVER_LABEL: Record<Driver, string> = {
  precio: 'Precio SKUs',
  costo_mmpp: 'Costo MMPP',
  wacc: 'WACC',
  opex: 'OpEx',
};

export default function SensitivityPage() {
  const [driverX, setDriverX] = useState<Driver>('precio');
  const [driverY, setDriverY] = useState<Driver>('costo_mmpp');
  const [n, setN] = useState(7);
  const [hurdle, setHurdle] = useState(0.15);
  const [data, setData] = useState<(HeatmapData & {
    tir_base: number | null;
    van_base: number;
    n_celdas_seguras: number;
    n_celdas_totales: number;
    pct_zona_segura: number;
  }) | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function cargar() {
    if (driverX === driverY) {
      setErr('Los dos drivers deben ser distintos');
      return;
    }
    setLoading(true);
    setErr(null);
    try {
      const r = await fetch(`${ENGINE_URL}/sensitivity/heatmap`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          driver_x: driverX,
          driver_y: driverY,
          n,
          hurdle_pct: hurdle,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
      setData(await r.json());
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">
          Sensitivity Analysis 2D
        </h1>
        <p className="mt-2 text-sm text-oliva-600">
          Mapa de calor de TIR para combinaciones simultáneas de dos drivers.
          Identifica visualmente las &quot;zonas seguras&quot; del proyecto
          (TIR &gt; hurdle CEHTA 15%).
        </p>
      </header>

      <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm card-hover">
        <h2 className="font-medium text-oliva-900">Configuración del análisis</h2>
        <div className="mt-3 grid grid-cols-2 gap-4 md:grid-cols-4">
          <Select
            label="Driver eje X"
            value={driverX}
            onChange={setDriverX}
            options={['precio', 'costo_mmpp', 'wacc', 'opex'] as Driver[]}
          />
          <Select
            label="Driver eje Y"
            value={driverY}
            onChange={setDriverY}
            options={['precio', 'costo_mmpp', 'wacc', 'opex'] as Driver[]}
          />
          <label className="block">
            <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">
              Grid (N x N)
            </div>
            <input
              type="range"
              min={5}
              max={11}
              step={2}
              value={n}
              onChange={(e) => setN(parseInt(e.target.value, 10))}
              className="mt-1 w-full"
            />
            <div className="tabular text-sm font-medium text-oliva-900">
              {n}×{n} = {n * n} sims
            </div>
          </label>
          <label className="block">
            <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">
              Hurdle TIR
            </div>
            <input
              type="range"
              min={0.1}
              max={0.25}
              step={0.01}
              value={hurdle}
              onChange={(e) => setHurdle(parseFloat(e.target.value))}
              className="mt-1 w-full"
            />
            <div className="tabular text-sm font-medium text-oliva-900">
              {(hurdle * 100).toFixed(0)}%
            </div>
          </label>
        </div>
        <button
          onClick={cargar}
          className="mt-4 rounded bg-borgoña px-4 py-2 text-sm text-crema hover:bg-tierra disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Calculando...' : 'Ejecutar análisis'}
        </button>
        {err && <p className="mt-2 text-sm text-borgoña">{err}</p>}
      </section>

      {data && (
        <>
          {/* KPIs superiores */}
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Card
              titulo="TIR base"
              valor={data.tir_base !== null ? `${(data.tir_base * 100).toFixed(2)}%` : '—'}
              detalle="Punto central del grid"
            />
            <Card
              titulo="Zona segura"
              valor={`${(data.pct_zona_segura * 100).toFixed(0)}%`}
              detalle={`${data.n_celdas_seguras} de ${data.n_celdas_totales} celdas > hurdle`}
              tone={
                data.pct_zona_segura > 0.7
                  ? 'ok'
                  : data.pct_zona_segura > 0.4
                  ? 'warn'
                  : 'bad'
              }
            />
            <Card
              titulo="Peor caso"
              valor={(() => {
                const tirs = data.celdas
                  .map((c) => c.tir)
                  .filter((t): t is number => t !== null);
                return `${(Math.min(...tirs) * 100).toFixed(2)}%`;
              })()}
              detalle="Celda con peor TIR"
              tone="bad"
            />
            <Card
              titulo="Mejor caso"
              valor={(() => {
                const tirs = data.celdas
                  .map((c) => c.tir)
                  .filter((t): t is number => t !== null);
                return `${(Math.max(...tirs) * 100).toFixed(2)}%`;
              })()}
              detalle="Celda con mejor TIR"
              tone="ok"
            />
          </section>

          {/* Heatmap */}
          <section className="rounded-lg border border-oliva/10 bg-white p-4 shadow-sm">
            <HeatmapChart
              data={data}
              height={520}
              title={`TIR según ${DRIVER_LABEL[data.driver_x as Driver]} × ${DRIVER_LABEL[data.driver_y as Driver]}`}
            />
          </section>

          {/* Interpretación */}
          <section className="rounded-lg border border-trigo/30 bg-trigo/5 p-4 text-sm text-oliva-900">
            <strong>Cómo leer el mapa:</strong>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>
                <span className="font-medium">Verde oliva</span>: TIR ≥ 25% (excelente,
                supera con holgura el hurdle CEHTA).
              </li>
              <li>
                <span className="font-medium">Trigo dorado</span>: TIR entre hurdle y
                25% (aceptable, defendible a directorio).
              </li>
              <li>
                <span className="font-medium">Borgoña</span>: TIR &lt; hurdle (zona de
                rechazo, requiere mitigación).
              </li>
              <li>
                Cuanto mayor el % zona segura, más robusto es el plan frente a shocks
                cross-variable.
              </li>
              <li>
                Default ejecutivo: precio × costo MMPP (los dos drivers más sensibles
                del tornado).
              </li>
            </ul>
          </section>
        </>
      )}
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: any) => void;
  options: string[];
}) {
  return (
    <label className="block">
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">
        {label}
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded border border-oliva/20 bg-white px-2 py-1 text-sm text-oliva-900"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {DRIVER_LABEL[o as Driver] ?? o}
          </option>
        ))}
      </select>
    </label>
  );
}

function Card({
  titulo,
  valor,
  detalle,
  tone = 'neutral',
}: {
  titulo: string;
  valor: string;
  detalle: string;
  tone?: 'ok' | 'warn' | 'bad' | 'neutral';
}) {
  const cls =
    tone === 'ok'
      ? 'border-oliva-700/30 bg-oliva-50/30'
      : tone === 'warn'
      ? 'border-trigo/40 bg-trigo/5'
      : tone === 'bad'
      ? 'border-borgoña/30 bg-borgoña/5'
      : 'border-oliva/10 bg-white';
  return (
    <div className={`card-hover rounded-lg border p-3 shadow-sm ${cls}`}>
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">
        {titulo}
      </div>
      <div className="mt-1 tabular text-2xl font-semibold text-oliva-900">
        {valor}
      </div>
      <div className="mt-1 text-xs text-oliva-700">{detalle}</div>
    </div>
  );
}
