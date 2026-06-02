'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Compuesto = {
  nombre: string;
  porcentaje_tipico: number;
  funcion_bioactiva: string;
  valor_comercial: string;
};

type Aplicacion = {
  mercado: string;
  uso_especifico: string;
  formato_producto: string;
  precio_usd_kg_premium: number;
  tam_global_usd_anual: number;
  certificaciones_requeridas: string[];
  competidores_clave: string[];
};

type Perfil = {
  sku: string;
  nombre_comercial: string;
  mmpp_origen: string;
  descripcion_cientifica: string;
  proteina_pct: number | null;
  grasa_pct: number | null;
  fibra_dietetica_pct: number | null;
  humedad_pct: number;
  compuestos_activos: Compuesto[];
  aplicaciones: Aplicacion[];
  valor_nutricional_score: number;
  diferenciador_clave: string;
  riesgos_tecnicos: string[];
  papers_referencia: string[];
};

type Resumen = {
  n_perfiles: number;
  score_promedio_portfolio: number;
  tam_total_global_usd: number;
  n_aplicaciones_totales: number;
  n_compuestos_activos_catalogados: number;
  top_10_aplicaciones: Array<{
    sku: string;
    mercado: string;
    uso: string;
    precio_usd_kg: number;
    tam_global_usd: number;
    competidores: string[];
  }>;
  mercados_target: Record<string, {
    tam_total: number;
    skus_aplicables: string[];
    precio_promedio_premium: number;
    n_apps: number;
  }>;
};

const MERCADO_LABEL: Record<string, string> = {
  feed_acuicola: '🐟 Feed acuícola',
  feed_pet: '🐾 Feed pet',
  feed_ganaderia: '🐄 Feed ganadería',
  alimentos_humanos: '🍽 Alimentos humanos',
  nutraceutica: '💊 Nutracéutica',
  cosmetica: '💄 Cosmética',
  industrial_quimico: '🏭 Industrial',
  farma: '⚕️ Farma',
};

const VALOR_COMERCIAL_COLOR: Record<string, string> = {
  alto: 'text-brand bg-brand-50',
  medio: 'text-yellow-700 bg-yellow-50',
  bajo: 'text-ink-400 bg-ink-50',
};

export default function NutrientesPage() {
  const [resumen, setResumen] = useState<Resumen | null>(null);
  const [perfiles, setPerfiles] = useState<Perfil[]>([]);
  const [expandido, setExpandido] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/nutrientes`).then(r => r.ok && r.json()).then(setResumen);
    fetch(`${ENGINE_URL}/nutrientes/perfiles`).then(r => r.ok && r.json()).then(d => setPerfiles(d.perfiles));
  }, []);

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">🧬 Nutrient Intelligence</h1>
          <p className="mt-2 text-sm text-ink-400">
            Perfil científico de cada SKU: compuestos bioactivos, aplicaciones comerciales,
            mercados target con TAM, certificaciones, premium pricing y respaldo papers.
          </p>
        </div>
      </header>

      {/* Hero stats */}
      {resumen && (
        <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
          <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">SKUs catalogados</div>
              <div className="tabular mt-2 text-4xl font-semibold text-ink">{resumen.n_perfiles}</div>
              <div className="text-xs text-ink-600">{resumen.n_compuestos_activos_catalogados} compuestos activos</div>
            </div>
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Score portfolio</div>
              <div className="tabular mt-2 text-4xl font-semibold text-brand">{resumen.score_promedio_portfolio}/100</div>
              <div className="text-xs text-ink-600">valor nutricional promedio</div>
            </div>
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">TAM global agregado</div>
              <div className="tabular mt-2 text-4xl font-semibold text-ink">${(resumen.tam_total_global_usd / 1e9).toFixed(1)}B</div>
              <div className="text-xs text-ink-600">USD anual mercados target</div>
            </div>
            <div>
              <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Aplicaciones</div>
              <div className="tabular mt-2 text-4xl font-semibold text-ink">{resumen.n_aplicaciones_totales}</div>
              <div className="text-xs text-ink-600">casos de uso documentados</div>
            </div>
          </div>
        </section>
      )}

      {/* Mercados target */}
      {resumen && (
        <section>
          <h2 className="mb-4 text-2xl font-semibold tracking-apple text-ink">🎯 Mercados Target</h2>
          <p className="mb-4 text-sm text-ink-400">
            TAM agregado por mercado. Estrategia comercial debe priorizar los TAM mayores con SKUs aplicables.
          </p>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
            {Object.entries(resumen.mercados_target)
              .sort(([, a], [, b]) => b.tam_total - a.tam_total)
              .map(([mercado, info]) => (
                <div key={mercado} className="apple-card">
                  <div className="text-xs font-medium text-ink-600">{MERCADO_LABEL[mercado] ?? mercado}</div>
                  <div className="tabular mt-2 text-2xl font-semibold text-ink">
                    ${(info.tam_total / 1e9).toFixed(2)}B
                  </div>
                  <div className="text-xs text-ink-400">USD/año TAM</div>
                  <div className="mt-2 text-[11px] text-ink-600">
                    {info.skus_aplicables.length} SKUs · ~${info.precio_promedio_premium.toFixed(1)}/kg premium
                  </div>
                </div>
              ))}
          </div>
        </section>
      )}

      {/* Top 10 aplicaciones */}
      {resumen && (
        <section className="apple-card overflow-x-auto p-0">
          <div className="border-b border-ink-100 p-4">
            <h2 className="text-xl font-semibold tracking-apple text-ink">🏆 Top 10 Aplicaciones por TAM</h2>
            <p className="mt-1 text-sm text-ink-400">Mercados específicos con mayor oportunidad económica global.</p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-100 bg-ink-50/50">
                <th className="p-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">SKU</th>
                <th className="p-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">Mercado</th>
                <th className="p-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-400">Uso</th>
                <th className="p-3 text-right text-[11px] font-semibold uppercase tracking-wider text-ink-400">Precio premium</th>
                <th className="p-3 text-right text-[11px] font-semibold uppercase tracking-wider text-ink-400">TAM global</th>
              </tr>
            </thead>
            <tbody>
              {resumen.top_10_aplicaciones.map((a, i) => (
                <tr key={i} className="border-b border-ink-100 last:border-0">
                  <td className="p-3 font-mono text-xs text-ink">{a.sku}</td>
                  <td className="p-3 text-ink-600">{MERCADO_LABEL[a.mercado] ?? a.mercado}</td>
                  <td className="p-3 text-xs text-ink-600">{a.uso}</td>
                  <td className="p-3 tabular text-right text-brand">${a.precio_usd_kg.toFixed(2)}/kg</td>
                  <td className="p-3 tabular text-right font-semibold text-ink">${(a.tam_global_usd / 1e6).toFixed(0)}M</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {/* Perfiles SKU expandibles */}
      <section>
        <h2 className="mb-4 text-2xl font-semibold tracking-apple text-ink">📋 Perfiles científicos por SKU</h2>
        <div className="space-y-3">
          {perfiles.map((p) => (
            <div key={p.sku} className="apple-card">
              <button
                onClick={() => setExpandido(expandido === p.sku ? null : p.sku)}
                className="flex w-full items-start justify-between gap-4 text-left"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-ink">{p.nombre_comercial}</h3>
                    <code className="rounded bg-ink-50 px-2 py-0.5 text-[10px] text-ink-600">{p.sku}</code>
                    <span className="ml-auto tabular text-xs font-semibold text-brand">Score {p.valor_nutricional_score}/100</span>
                  </div>
                  <p className="mt-1 text-xs text-ink-600">{p.diferenciador_clave}</p>
                  <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-ink-400">
                    {p.proteina_pct !== null && <span>Proteína {p.proteina_pct}%</span>}
                    {p.fibra_dietetica_pct !== null && <span>Fibra {p.fibra_dietetica_pct}%</span>}
                    {p.grasa_pct !== null && <span>Grasa {p.grasa_pct}%</span>}
                    <span>{p.aplicaciones.length} aplicaciones</span>
                    <span>{p.compuestos_activos.length} compuestos activos</span>
                  </div>
                </div>
                <span className="text-ink-400">{expandido === p.sku ? '▼' : '▶'}</span>
              </button>

              {expandido === p.sku && (
                <div className="mt-4 space-y-4 border-t border-ink-100 pt-4">
                  {/* Descripción */}
                  <p className="text-sm text-ink-600">{p.descripcion_cientifica}</p>

                  {/* Compuestos activos */}
                  <div>
                    <h4 className="mb-2 text-sm font-semibold text-ink">🧬 Compuestos bioactivos</h4>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                      {p.compuestos_activos.map((c, i) => (
                        <div key={i} className="rounded-lg bg-ink-50 p-3">
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-ink">{c.nombre}</span>
                            <span className={`rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${VALOR_COMERCIAL_COLOR[c.valor_comercial] ?? 'bg-ink-100 text-ink-600'}`}>
                              {c.valor_comercial}
                            </span>
                          </div>
                          <div className="mt-1 text-[11px] text-ink-400">{c.porcentaje_tipico}% típico</div>
                          <div className="mt-1 text-xs text-ink-600">{c.funcion_bioactiva}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Aplicaciones */}
                  <div>
                    <h4 className="mb-2 text-sm font-semibold text-ink">💼 Aplicaciones comerciales</h4>
                    <div className="space-y-2">
                      {p.aplicaciones.map((a, i) => (
                        <div key={i} className="rounded-lg border border-ink-100 p-3">
                          <div className="flex items-baseline justify-between">
                            <div>
                              <span className="text-xs font-semibold text-ink">{MERCADO_LABEL[a.mercado] ?? a.mercado}</span>
                              <span className="ml-2 text-xs text-ink-600">{a.uso_especifico}</span>
                            </div>
                            <div className="text-right">
                              <div className="tabular text-sm font-semibold text-brand">${a.precio_usd_kg_premium}/kg</div>
                              <div className="text-[10px] text-ink-400">TAM ${(a.tam_global_usd_anual / 1e6).toFixed(0)}M</div>
                            </div>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-2 text-[10px]">
                            <span className="text-ink-400">Formato: <strong>{a.formato_producto}</strong></span>
                            <span className="text-ink-400">Cert: {a.certificaciones_requeridas.slice(0, 3).join(', ')}</span>
                            <span className="text-ink-400">vs: {a.competidores_clave.slice(0, 2).join(', ')}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Riesgos */}
                  {p.riesgos_tecnicos.length > 0 && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold text-ink">⚠️ Riesgos técnicos</h4>
                      <ul className="space-y-1 text-xs text-ink-600">
                        {p.riesgos_tecnicos.map((r, i) => <li key={i}>• {r}</li>)}
                      </ul>
                    </div>
                  )}

                  {/* Papers */}
                  {p.papers_referencia.length > 0 && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold text-ink">📚 Papers de respaldo</h4>
                      <ul className="space-y-1 text-xs text-ink-600">
                        {p.papers_referencia.map((paper, i) => <li key={i}>• {paper}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
