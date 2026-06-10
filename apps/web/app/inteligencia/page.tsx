'use client';

import Link from 'next/link';
import { ConectadoCon } from '@/components/ConectadoCon';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Insight = {
  titulo: string; tipo: string; severidad: string;
  descripcion: string; impacto: string; accion_sugerida: string;
  modulos_origen: string[]; link_ui: string; score_prioridad: number;
};

type Completitud = { nombre: string; valor_pct: number; detalle: string; link: string };

type Sintesis = {
  score_global_inteligencia: number;
  completitud_subsistemas: Completitud[];
  insights: Insight[];
  insights_criticos: number;
  insights_altos: number;
  oportunidades: number;
  amenazas: number;
  plan_accion_top_5: Insight[];
  resumen_ejecutivo: string;
  metricas_clave: Record<string, any>;
  proximos_pasos: string[];
};

const SEV_COLOR: Record<string, string> = {
  critica: 'bg-red-50 text-red-700 border-red-300',
  alta: 'bg-orange-50 text-orange-700 border-orange-300',
  media: 'bg-yellow-50 text-yellow-700 border-yellow-300',
  baja: 'bg-blue-50 text-blue-700 border-blue-300',
  info: 'bg-brand-50 text-brand border-brand/30',
};

const TIPO_ICON: Record<string, string> = {
  oportunidad: '💡',
  amenaza: '⚠️',
  validacion: '📋',
  recomendacion: '👉',
  logro: '✅',
};

type Precision = {
  exactitud_global_pct: number;
  nivel_confianza: string;
  total_inputs: number;
  validados: number;
  provisorios: number;
  sin_validar: number;
  por_categoria: Record<string, { total: number; exactitud_pct: number }>;
  top_para_validar: { id: string; nombre: string; categoria: string; nivel: string; peso_impacto: number; prioridad: number; como_validar: string; fuente_sugerida: string; valor_actual: string }[];
  resumen: string;
};

type Banda = { nombre: string; esperado: number; p10: number; p50: number; p90: number; unidad: string; margen_error_pct: number };
type Prediccion = {
  n_simulaciones: number;
  bandas: Record<string, Banda>;
  margen_error_global_pct: number;
  nivel_confianza_modelo_pct: number;
  interpretacion: string;
  drivers_incertidumbre: { input: string; incertidumbre_pct: number; razon: string }[];
};

export default function InteligenciaPage() {
  const [data, setData] = useState<Sintesis | null>(null);
  const [precision, setPrecision] = useState<Precision | null>(null);
  const [prediccion, setPrediccion] = useState<Prediccion | null>(null);
  const [skuPred, setSkuPred] = useState('nutraceutico_premium');
  const [filtroTipo, setFiltroTipo] = useState<string>('todos');

  useEffect(() => {
    fetch(`${ENGINE_URL}/inteligencia/precision`).then((r) => r.json()).then(setPrecision).catch(() => {});
  }, []);

  useEffect(() => {
    fetch(`${ENGINE_URL}/inteligencia/prediccion?sku_principal=${skuPred}`).then((r) => r.json()).then(setPrediccion).catch(() => {});
  }, [skuPred]);

  useEffect(() => {
    fetch(`${ENGINE_URL}/inteligencia/sintesis`).then((r) => r.json()).then(setData);
  }, []);

  if (!data) return <p className="text-ink-400">Sintetizando inteligencia de toda la plataforma…</p>;

  const insightsFiltrados = filtroTipo === 'todos'
    ? data.insights
    : data.insights.filter((i) => i.tipo === filtroTipo);

  const scoreColor = data.score_global_inteligencia >= 80 ? 'text-brand'
    : data.score_global_inteligencia >= 60 ? 'text-yellow-600'
    : 'text-orange-600';

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Capa de síntesis cross-modular</p>
        <h1 className="mt-2 text-4xl font-bold">🧠 Inteligencia Trongkai</h1>
        <p className="mt-2 text-ink-500">
          El sistema consolida TODOS los módulos y genera insights accionables, ordenados por impacto.
        </p>
      </header>

      {/* Hero score */}
      <section className="rounded-2xl border border-ink-100 bg-gradient-to-br from-fbfbfd to-white p-8 text-center">
        <p className="text-xs uppercase tracking-wider text-ink-500 font-semibold">Score Global Inteligencia</p>
        <p className={`mt-2 text-7xl font-bold tabular ${scoreColor}`}>
          {data.score_global_inteligencia.toFixed(0)}
          <span className="text-3xl text-ink-400">/100</span>
        </p>
        <p className="mt-4 max-w-3xl mx-auto text-ink-600 text-base">{data.resumen_ejecutivo}</p>
      </section>

      {/* KPIs principales */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KPI label="🔴 Críticas" valor={data.insights_criticos} color="text-red-600" />
        <KPI label="🟠 Altas" valor={data.insights_altos} color="text-orange-600" />
        <KPI label="💡 Oportunidades" valor={data.oportunidades} color="text-brand" />
        <KPI label="⚠️ Amenazas" valor={data.amenazas} color="text-orange-600" />
      </div>

      {/* PRECISIÓN DEL MODELO — qué validar para llegar a exacto */}
      {precision && (
        <section className="rounded-2xl border-2 border-brand/30 bg-gradient-to-br from-brand-50/40 to-white p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold">🎯 Exactitud del modelo</h2>
              <p className="text-sm text-ink-500 mt-1">{precision.resumen}</p>
            </div>
            <div className="text-right">
              <p className="text-5xl font-bold tabular" style={{ background: 'linear-gradient(135deg,#1a8a1a,#34a853)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                {precision.exactitud_global_pct.toFixed(0)}<span className="text-xl text-ink-400">/100</span>
              </p>
              <p className="text-xs uppercase tracking-wider font-bold text-brand">{precision.nivel_confianza}</p>
            </div>
          </div>

          {/* Barra de exactitud */}
          <div className="mt-4 h-4 overflow-hidden rounded-full bg-ink-100">
            <div className="h-full bg-gradient-to-r from-orange-400 via-yellow-400 to-brand transition-all"
              style={{ width: `${precision.exactitud_global_pct}%` }} />
          </div>
          <div className="mt-1 flex justify-between text-[10px] text-ink-400">
            <span>estimado</span><span>aproximado</span><span>casi exacto</span><span>exacto</span>
          </div>

          {/* Por categoría */}
          <div className="mt-5 grid grid-cols-2 gap-2 md:grid-cols-5">
            {Object.entries(precision.por_categoria).map(([cat, d]) => (
              <div key={cat} className="rounded-xl border border-ink-100 bg-white p-3">
                <p className="text-[10px] uppercase text-ink-400">{cat}</p>
                <p className={`mt-1 text-lg font-bold tabular ${d.exactitud_pct >= 75 ? 'text-brand' : d.exactitud_pct >= 50 ? 'text-yellow-600' : 'text-orange-600'}`}>
                  {d.exactitud_pct.toFixed(0)}%
                </p>
                <p className="text-[10px] text-ink-400">{d.total} inputs</p>
              </div>
            ))}
          </div>

          {/* Top a validar */}
          <div className="mt-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-ink-500 mb-3">
              📋 Qué validar primero (mayor impacto en la exactitud)
            </h3>
            <div className="space-y-2">
              {precision.top_para_validar.slice(0, 6).map((t, i) => (
                <div key={t.id} className="rounded-xl border border-ink-100 bg-white p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="rounded-full bg-ink text-white text-xs font-bold w-6 h-6 flex items-center justify-center shrink-0">{i + 1}</span>
                        <span className="font-semibold text-sm">{t.nombre}</span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${t.nivel === 'PD' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>{t.nivel}</span>
                      </div>
                      <p className="mt-1 pl-8 text-xs text-ink-600">👉 {t.como_validar}</p>
                      <p className="mt-0.5 pl-8 text-[11px] text-ink-400">📍 Fuente: {t.fuente_sugerida} · Valor actual: {t.valor_actual}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-xs text-ink-400">impacto</p>
                      <div className="w-16 h-1.5 rounded-full bg-ink-100 mt-1">
                        <div className="h-full rounded-full bg-brand" style={{ width: `${t.peso_impacto * 100}%` }} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Métricas clave */}
      {data.metricas_clave && Object.keys(data.metricas_clave).length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-bold">📊 Métricas clave consolidadas</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
            {Object.entries(data.metricas_clave).map(([k, v]) => (
              <div key={k} className="rounded-xl border border-ink-100 bg-white p-3">
                <p className="text-[10px] uppercase text-ink-400">{k.replace(/_/g, ' ')}</p>
                <p className="mt-1 text-base font-bold tabular">
                  {typeof v === 'number' ? (
                    k.includes('clp') ? `$${(v / 1e6).toFixed(0)}M` :
                    k.includes('pct') ? `${(v * 100).toFixed(0)}%` :
                    v.toLocaleString()
                  ) : (v ?? '—')}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Completitud subsistemas */}
      <section>
        <h2 className="mb-4 text-xl font-bold">🎯 Completitud por subsistema</h2>
        <div className="space-y-2">
          {data.completitud_subsistemas.map((c) => (
            <Link key={c.nombre} href={c.link} className="block rounded-xl border border-ink-100 bg-white p-4 hover:border-brand transition">
              <div className="flex items-center justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-baseline justify-between text-sm">
                    <span className="font-semibold">{c.nombre}</span>
                    <span className={`tabular font-bold ${c.valor_pct >= 80 ? 'text-brand' : c.valor_pct >= 60 ? 'text-yellow-600' : 'text-orange-600'}`}>
                      {c.valor_pct.toFixed(0)}/100
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-ink-500">{c.detalle}</p>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-ink-50">
                    <div
                      className={`h-full transition-all ${c.valor_pct >= 80 ? 'bg-brand' : c.valor_pct >= 60 ? 'bg-yellow-500' : 'bg-orange-500'}`}
                      style={{ width: `${c.valor_pct}%` }}
                    />
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* PREDICCIÓN CON BANDAS DE CONFIANZA */}
      {prediccion && (
        <section className="rounded-2xl border-2 border-blue-200 bg-gradient-to-br from-blue-50/40 to-white p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold">🔮 Predicción con bandas de confianza</h2>
              <p className="text-sm text-ink-500 mt-1">
                {prediccion.n_simulaciones.toLocaleString()} simulaciones Monte Carlo · margen de error ±{prediccion.margen_error_global_pct.toFixed(0)}%
              </p>
            </div>
            <select value={skuPred} onChange={(e) => setSkuPred(e.target.value)}
              className="rounded border border-ink-200 px-3 py-2 text-sm">
              <option value="harina_animal_basica">Harina animal básica</option>
              <option value="harina_animal_premium">Harina animal premium</option>
              <option value="ingrediente_humano">Ingrediente humano</option>
              <option value="nutraceutico_premium">Nutracéutico premium</option>
            </select>
          </div>

          {/* Bandas como rangos visuales */}
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {Object.entries(prediccion.bandas).map(([k, b]) => {
              const rango = b.p90 - b.p10;
              const posEsperado = rango > 0 ? ((b.esperado - b.p10) / rango) * 100 : 50;
              const fmt = (v: number) => b.unidad.includes('CLP/kg') || b.unidad.includes('M CLP')
                ? v.toLocaleString(undefined, { maximumFractionDigits: 0 })
                : v.toLocaleString(undefined, { maximumFractionDigits: 1 });
              return (
                <div key={k} className="rounded-xl border border-ink-100 bg-white p-4">
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-semibold">{b.nombre}</span>
                    <span className="text-xs text-ink-400">±{(b.margen_error_pct * 100).toFixed(0)}%</span>
                  </div>
                  <p className="mt-1 text-2xl font-bold tabular">
                    {fmt(b.esperado)} <span className="text-sm font-normal text-ink-400">{b.unidad}</span>
                  </p>
                  {/* Barra de rango p10-p90 */}
                  <div className="mt-3 relative h-2 rounded-full bg-gradient-to-r from-orange-200 via-yellow-200 to-brand-50">
                    <div className="absolute top-1/2 -translate-y-1/2 w-2 h-4 rounded bg-ink" style={{ left: `calc(${Math.max(0, Math.min(100, posEsperado))}% - 4px)` }} />
                  </div>
                  <div className="mt-1 flex justify-between text-[10px] text-ink-400 tabular">
                    <span>p10: {fmt(b.p10)}</span>
                    <span>p90: {fmt(b.p90)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Drivers de incertidumbre */}
          <div className="mt-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-500 mb-2">
              ⚡ Qué reduce más el margen de error (validar en este orden)
            </p>
            <div className="space-y-1.5">
              {prediccion.drivers_incertidumbre.slice(0, 4).map((d, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <span className="rounded-full bg-blue-100 text-blue-700 text-xs font-bold w-6 h-6 flex items-center justify-center shrink-0">{i + 1}</span>
                  <span className="font-medium w-40 shrink-0">{d.input}</span>
                  <div className="flex-1 h-1.5 rounded-full bg-ink-100">
                    <div className="h-full rounded-full bg-orange-400" style={{ width: `${Math.min(100, d.incertidumbre_pct * 2)}%` }} />
                  </div>
                  <span className="text-xs text-ink-400 w-12 text-right">±{d.incertidumbre_pct}%</span>
                </div>
              ))}
            </div>
          </div>

          <p className="mt-4 text-sm text-blue-900 bg-blue-50/60 rounded-lg p-3">{prediccion.interpretacion}</p>
        </section>
      )}

      {/* Plan acción top 5 */}
      <section>
        <h2 className="mb-4 text-xl font-bold">🎯 Plan de acción priorizado (top 5)</h2>
        <div className="space-y-3">
          {data.plan_accion_top_5.map((i, idx) => (
            <Link key={idx} href={i.link_ui || '#'} className={`block rounded-xl border-l-4 p-5 hover:shadow-md transition ${SEV_COLOR[i.severidad]}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-2xl">{TIPO_ICON[i.tipo] || '•'}</span>
                    <h3 className="text-lg font-bold">{i.titulo}</h3>
                    <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold uppercase">
                      Prioridad {i.score_prioridad.toFixed(0)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm">{i.descripcion}</p>
                  {i.impacto && <p className="mt-2 text-xs italic font-semibold">📌 Impacto: {i.impacto}</p>}
                  {i.accion_sugerida && (
                    <div className="mt-3 rounded-lg bg-white/60 p-3 text-xs">
                      <p className="font-semibold mb-1">👉 Acción sugerida:</p>
                      <p className="whitespace-pre-line">{i.accion_sugerida}</p>
                    </div>
                  )}
                </div>
                <span className="text-2xl shrink-0">#{idx + 1}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Todos los insights con filtro */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-bold">📋 Todos los insights ({data.insights.length})</h2>
          <select value={filtroTipo} onChange={(e) => setFiltroTipo(e.target.value)}
            className="rounded border border-ink-200 px-3 py-1 text-sm">
            <option value="todos">Todos</option>
            <option value="oportunidad">Solo oportunidades</option>
            <option value="amenaza">Solo amenazas</option>
            <option value="validacion">Solo validación</option>
            <option value="logro">Solo logros</option>
          </select>
        </div>
        <div className="space-y-2">
          {insightsFiltrados.map((i, idx) => (
            <div key={idx} className={`rounded-xl border p-3 ${SEV_COLOR[i.severidad]}`}>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-lg">{TIPO_ICON[i.tipo]}</span>
                <span className="font-semibold flex-1">{i.titulo}</span>
                <span className="text-xs">P{i.score_prioridad.toFixed(0)}</span>
                {i.link_ui && (
                  <Link href={i.link_ui} className="text-xs underline">Ver →</Link>
                )}
              </div>
              <p className="mt-1 text-xs opacity-80 pl-7">{i.descripcion}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Próximos pasos */}
      {data.proximos_pasos.length > 0 && (
        <section className="rounded-2xl bg-ink p-6 text-white">
          <h2 className="text-xl font-bold mb-4">🎯 Próximos pasos accionables</h2>
          <ol className="space-y-2">
            {data.proximos_pasos.map((p, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span className="rounded-full bg-brand text-white text-xs font-bold w-6 h-6 flex items-center justify-center shrink-0">
                  {i + 1}
                </span>
                <span>{p}</span>
              </li>
            ))}
          </ol>
        </section>
      )}

      <ConectadoCon links={[
        { href: '/variables', label: 'Matriz Variables', razon: 'Celdas PD que bajan la exactitud' },
        { href: '/parametros', label: 'Parámetros', razon: 'Validar los inputs PD detectados' },
        { href: '/simulacion', label: 'Simulación', razon: 'El motor detrás de la predicción' },
        { href: '/decisiones', label: 'Decision Engine', razon: 'Plan de acción ejecutable' },
      ]} />
    </div>
  );
}

function KPI({ label, valor, color }: { label: string; valor: number; color: string }) {
  return (
    <div className="rounded-xl border border-ink-100 bg-white p-4">
      <p className="text-[11px] uppercase text-ink-400">{label}</p>
      <p className={`mt-1 text-3xl font-bold tabular ${color}`}>{valor}</p>
    </div>
  );
}
