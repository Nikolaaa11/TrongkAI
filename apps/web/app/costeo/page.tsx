'use client';

import Link from 'next/link';
import { ConectadoCon } from '@/components/ConectadoCon';
import { CalidadDato } from '@/components/CalidadDato';
import { useEffect, useState } from 'react';
import NivelDato from '@/components/NivelDato';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type CostoEtapa = {
  etapa_id: string;
  nombre: string;
  orden: number;
  costo_mo_clp_h: number;
  costo_energia_clp_h: number;
  costo_calor_clp_h: number;
  costo_agua_clp_h: number;
  costo_materiales_clp_h: number;
  costo_arriendo_clp_h: number;
  costo_total_clp_h: number;
  costo_por_kg_input_clp: number;
  costo_por_kg_output_clp: number;
  masa_input_kg_h: number;
  masa_output_kg_h: number;
};

type CostoSKU = {
  codigo: string;
  variante: string;
  rendimiento_msf_pct: number;
  costo_proceso_clp_kg: number;
  costo_flete_mmpp_clp_kg: number;
  costo_flete_despacho_clp_kg: number;
  costo_total_clp_kg: number;
  costo_total_usd_kg: number;
  tiene_proceso_definido: boolean;
};

type Costeo = {
  throughput_kg_h: number;
  masa_input_total_kg_h: number;
  masa_output_total_kg_h: number;
  costos_etapas: CostoEtapa[];
  costo_total_clp_h: number;
  costo_total_clp_kg_output: number;
  costo_total_usd_kg_output: number;
  costos_por_sku: CostoSKU[];
  parametros_utilizados: Record<string, number>;
  desglose_costos_clp_h: { mo: number; energia: number; calor: number; agua: number; materiales: number; arriendos: number };
};

type RutaV3 = { etapas: string[]; total_dia_clp: number; clp_ton_mp_seca: number; clp_kg_mp_seca: number; total_mes_clp: number };
type CostosV3 = {
  fuente: string;
  rutas: Record<string, RutaV3>;
  decision_packaging: { ahorro_maxisaco_clp_mes: number; factor: number; mensaje: string };
  mp_seca_final_ton_dia: number;
  por_validar: string[];
};

const RUTA_LABELS: Record<string, string> = {
  saco_base: 'SACO 25 kg (Excel equipo)',
  maxisaco_base: 'MAXISACO 800 kg (Excel equipo)',
  saco_calor_residual: 'Saco + calor residual La Gloria',
  maxisaco_calor_residual: 'Maxisaco + calor residual',
  maxisaco_tricanter_residual: 'Maxisaco + tricanter + residual (más barata)',
};

export default function CosteoPage() {
  const [data, setData] = useState<Costeo | null>(null);
  const [v3, setV3] = useState<CostosV3 | null>(null);
  const [throughput, setThroughput] = useState(2000);
  const [respaldo, setRespaldo] = useState(false);

  useEffect(() => {
    fetch(`${ENGINE_URL}/costeo/etapas?throughput_kg_h=${throughput}&incluir_respaldo=${respaldo}`)
      .then((r) => r.json()).then(setData);
  }, [throughput, respaldo]);

  useEffect(() => {
    fetch(`${ENGINE_URL}/costos/procesos`)
      .then((r) => r.json()).then(setV3).catch(() => setV3(null));
  }, []);

  if (!data) return <p className="text-ink-400">Calculando costeo…</p>;

  const desgloseTotal = Object.values(data.desglose_costos_clp_h).reduce((a, b) => a + b, 0);
  const desgloseColors: Record<string, string> = {
    mo: 'bg-blue-500', energia: 'bg-yellow-500', calor: 'bg-red-500',
    agua: 'bg-cyan-500', materiales: 'bg-purple-500', arriendos: 'bg-orange-500',
  };

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Costeo dinámico</p>
        <h1 className="mt-2 text-4xl font-bold">💰 Costo por etapa y por SKU</h1>
        <p className="mt-2 text-ink-500">
          MO + energía + calor residual + agua + materiales + arriendo. Usa los <Link className="text-brand underline" href="/parametros">parámetros</Link> actuales.
        </p>
      </header>

      {/* Calidad del dato (FASE D super-prompt) */}
      <CalidadDato />

      {/* Slider */}
      <section className="rounded-2xl border border-ink-100 bg-white p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-ink-500">Throughput</p>
            <p className="mt-1 text-3xl font-bold">{throughput.toLocaleString()} kg/h</p>
          </div>
          <input type="range" min="500" max="5000" step="100" value={throughput}
            onChange={(e) => setThroughput(+e.target.value)} className="w-64 accent-brand" />
          <label className="flex items-center gap-2 text-xs">
            <input type="checkbox" checked={respaldo} onChange={(e) => setRespaldo(e.target.checked)} className="accent-orange-500" />
            Usar deshidratación de respaldo
          </label>
        </div>
      </section>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KPI label="Costo total/hora" valor={`$${(data.costo_total_clp_h / 1000).toFixed(0)}k CLP`} sub="planta operando" />
        <KPI label="Costo unitario" valor={`$${data.costo_total_clp_kg_output.toFixed(0)} CLP/kg`} sub="producto final" badge={<NivelDato kpi="costo_piloto" />} />
        <KPI label="Costo USD" valor={`$${data.costo_total_usd_kg_output.toFixed(2)} USD/kg`} sub="referencia internacional" />
        <KPI label="Throughput producto" valor={`${(data.masa_output_total_kg_h / 1000).toFixed(2)} t/h`} sub="output final" />
      </div>

      {/* Costos por procesos V3 — canon Excel equipo 03-jul-2026 */}
      {v3 && (
        <section className="rounded-2xl border border-ink-100 bg-white p-6">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="flex items-center gap-2 text-xl font-bold">📦 Costos por procesos — canon del equipo <NivelDato kpi="costos_procesos" /></h2>
            <p className="text-[11px] text-ink-400">{v3.fuente} · costo variable por ton de materia seca</p>
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm tabular-nums">
              <thead>
                <tr className="border-b border-ink-100 text-left text-[11px] uppercase tracking-wider text-ink-400">
                  <th className="py-2 pr-4">Ruta</th>
                  <th className="py-2 pr-4 text-right">CLP/día</th>
                  <th className="py-2 pr-4 text-right">CLP/ton MP seca</th>
                  <th className="py-2 text-right">CLP/mes</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(v3.rutas).map(([k, r]) => (
                  <tr key={k} className={`border-b border-ink-50 ${k === 'maxisaco_base' ? 'bg-green-50/60 font-semibold' : ''}`}>
                    <td className="py-2 pr-4">{RUTA_LABELS[k] ?? k}</td>
                    <td className="py-2 pr-4 text-right">${r.total_dia_clp.toLocaleString('es-CL', { maximumFractionDigits: 0 })}</td>
                    <td className="py-2 pr-4 text-right">${r.clp_ton_mp_seca.toLocaleString('es-CL', { maximumFractionDigits: 0 })}</td>
                    <td className="py-2 text-right">${(r.total_mes_clp / 1e6).toFixed(1)}M</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 rounded-xl bg-ink-50/70 p-3 text-[13px] text-ink-600">
            💡 <strong>{v3.decision_packaging.mensaje}</strong>{' '}
            Ahorro maxisaco: ${(v3.decision_packaging.ahorro_maxisaco_clp_mes / 1e6).toFixed(1)}M CLP/mes
            (factor {v3.decision_packaging.factor}x). {v3.por_validar.length} supuestos por validar — ver Excel
            &quot;Costos-Por-Procesos-v3&quot; en entregables.
          </p>
        </section>
      )}

      {/* Desglose por concepto */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Desglose de costos por concepto</h2>
        <div className="rounded-2xl border border-ink-100 bg-white p-6">
          <div className="space-y-3">
            {Object.entries(data.desglose_costos_clp_h).map(([k, v]) => {
              const pct = (v / desgloseTotal) * 100;
              return (
                <div key={k}>
                  <div className="flex justify-between text-sm">
                    <span className="capitalize font-medium">{k}</span>
                    <span className="tabular text-ink-500">
                      ${v.toLocaleString()} CLP/h ({pct.toFixed(1)}%)
                    </span>
                  </div>
                  <div className="mt-1 h-3 overflow-hidden rounded-full bg-ink-50">
                    <div className={`h-full ${desgloseColors[k]}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Costo por SKU */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Costo por SKU/producto</h2>
        <div className="overflow-x-auto rounded-xl border border-ink-100 bg-white">
          <table className="min-w-full text-sm">
            <thead className="bg-ink-50/40 text-xs uppercase text-ink-500">
              <tr>
                <th className="px-3 py-2 text-left">Producto</th>
                <th className="px-3 py-2 text-right">MSF</th>
                <th className="px-3 py-2 text-right">Proceso CLP/kg</th>
                <th className="px-3 py-2 text-right">Flete MMPP</th>
                <th className="px-3 py-2 text-right">Flete despacho</th>
                <th className="px-3 py-2 text-right">Total CLP/kg</th>
                <th className="px-3 py-2 text-right">USD/kg</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-50">
              {data.costos_por_sku.map((s) => (
                <tr key={s.codigo} className={s.tiene_proceso_definido ? '' : 'opacity-50'}>
                  <td className="px-3 py-2 font-medium">{s.codigo.replace('_', ' ')} <span className="text-ink-400 text-xs">({s.variante})</span></td>
                  <td className="px-3 py-2 text-right tabular">{s.rendimiento_msf_pct > 0 ? `${(s.rendimiento_msf_pct * 100).toFixed(0)}%` : '—'}</td>
                  <td className="px-3 py-2 text-right tabular">${s.costo_proceso_clp_kg.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right tabular">${s.costo_flete_mmpp_clp_kg.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right tabular">${s.costo_flete_despacho_clp_kg.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right tabular font-bold text-brand">${s.costo_total_clp_kg.toLocaleString()}</td>
                  <td className="px-3 py-2 text-right tabular font-semibold">${s.costo_total_usd_kg.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Costo por etapa */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Costo por etapa</h2>
        <div className="space-y-2">
          {data.costos_etapas.sort((a, b) => b.costo_total_clp_h - a.costo_total_clp_h).map((e) => (
            <div key={e.etapa_id} className="rounded-xl border border-ink-100 bg-white p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold">{e.nombre}</p>
                  <p className="text-xs text-ink-500 mt-0.5">
                    MO ${e.costo_mo_clp_h.toLocaleString()} · Energía ${e.costo_energia_clp_h.toLocaleString()} ·
                    Calor ${e.costo_calor_clp_h.toLocaleString()} · Agua ${e.costo_agua_clp_h.toLocaleString()} ·
                    Materiales ${e.costo_materiales_clp_h.toLocaleString()} · Arriendo ${e.costo_arriendo_clp_h.toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold tabular">${e.costo_total_clp_h.toLocaleString()}</p>
                  <p className="text-xs text-ink-400">CLP/hora</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Parámetros usados */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Parámetros aplicados</h2>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
          {Object.entries(data.parametros_utilizados).map(([k, v]) => (
            <div key={k} className="rounded-xl border border-ink-100 bg-white p-3">
              <p className="text-[10px] uppercase text-ink-400">{k.replace(/_/g, ' ')}</p>
              <p className="mt-1 text-base font-bold tabular">${(v as number).toLocaleString()}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-ink-500">
          → Editar valores en <Link href="/parametros" className="text-brand underline">/parametros</Link>
        </p>
      </section>

      <ConectadoCon links={[
        { href: '/parametros', label: 'Parámetros', razon: 'Los valores editables detrás del costo' },
        { href: '/balance-etapas', label: 'Por Etapas', razon: 'El flujo másico de cada etapa' },
        { href: '/simulacion', label: 'Simulación', razon: 'El costo en el tiempo (OPEX completo)' },
        { href: '/escalas', label: 'Escalas', razon: 'Cómo baja el costo unitario al escalar' },
      ]} />
    </div>
  );
}

function KPI({ label, valor, sub, badge }: { label: string; valor: string; sub?: string; badge?: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-ink-100 bg-white p-4">
      <p className="flex items-center gap-1.5 text-[11px] uppercase text-ink-400">{label}{badge}</p>
      <p className="mt-1 text-xl font-bold tabular">{valor}</p>
      {sub && <p className="text-xs text-ink-400">{sub}</p>}
    </div>
  );
}
