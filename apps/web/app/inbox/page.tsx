'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Sugerencia = {
  tipo_dato: string;
  celdas_o_modulo: string[] | string;
  confianza: string;
};

type Archivo = {
  ruta: string;
  filename: string;
  hash_md5: string;
  categoria: string;
  subcategoria: string;
  size_kb: number;
  extension: string;
  fecha_procesado: string;
  sugerencias: Sugerencia[];
  duplicado_de?: string;
};

type InboxResp = {
  total: number;
  por_categoria: Record<string, number>;
  por_subcategoria: Record<string, number>;
  sugerencias_totales: number;
  ultimos_10: Archivo[];
  nota?: string;
};

const CATEGORIAS = [
  { id: '01-comercial', label: 'Comercial', icon: '💼', desc: 'Cotizaciones MMPP, LOIs clientes, contratos' },
  { id: '02-financiero', label: 'Financiero', icon: '💰', desc: 'Term sheets, OpEx, CapEx, EERR' },
  { id: '03-operacional', label: 'Operacional', icon: '⚙️', desc: 'Rendimientos, energía, capacidades' },
  { id: '04-legal', label: 'Legal', icon: '⚖️', desc: 'Escrituras, permisos, certificaciones, IP' },
  { id: '05-esg', label: 'ESG', icon: '🌱', desc: 'LCA medido, compliance REP, certificaciones' },
  { id: '06-equipo', label: 'Equipo', icon: '👥', desc: 'CVs, advisors, alianzas, MOUs' },
  { id: '07-mercado', label: 'Mercado', icon: '📊', desc: 'Papers, comparables M&A, benchmarks' },
];

export default function InboxPage() {
  const [data, setData] = useState<InboxResp | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void cargar();
  }, []);

  async function cargar() {
    setLoading(true);
    try {
      const r = await fetch(`${ENGINE_URL}/inbox/status`);
      if (r.ok) setData(await r.json());
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
          <div>
            <h1 className="font-serif text-3xl text-ink">📥 Inbox Inteligente</h1>
            <p className="mt-2 text-sm text-ink-400">
              Buzón de información que sube el equipo. El clasificador detecta tipo de dato
              y sugiere actualizaciones a la matriz. Cada archivo te hace más inteligente la plataforma.
            </p>
          </div>
        </div>
        <button onClick={cargar} disabled={loading} className="btn-apple btn-apple-ghost text-xs">
          {loading ? '...' : '↻ Refresh'}
        </button>
      </header>

      {/* Cómo subir */}
      <section className="rounded-appleXl bg-brand-50 p-6 ring-1 ring-brand/20">
        <h2 className="text-lg font-semibold text-ink">📂 Cómo subir información</h2>
        <p className="mt-2 text-sm text-ink-600">
          Coloca cualquier archivo (PDF, Excel, Word, imagen) en la carpeta correcta de{' '}
          <code className="rounded bg-white px-1 text-xs">inbox/</code> y ejecuta:
        </p>
        <pre className="mt-3 overflow-x-auto rounded-lg bg-ink text-white p-3 text-xs">
{`cd "C:\\Users\\nicol\\OneDrive\\Documentos\\0.1.1 TrongkAI\\trongkai-platform"
python scripts/procesar_inbox.py`}
        </pre>
        <p className="mt-3 text-xs text-ink-600">
          El sistema clasifica automáticamente · sugiere qué celdas de matriz actualizar · registra en audit trail · sube el Investment Readiness Score.
        </p>
      </section>

      {/* Hero stats */}
      {data && (
        <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Archivos indexados" value={data.total} icon="📁" />
          <StatCard label="Sugerencias detectadas" value={data.sugerencias_totales} icon="💡" tone="ok" />
          <StatCard label="Categorías activas" value={Object.keys(data.por_categoria).length} icon="🏷" />
          <StatCard label="Subcategorías usadas" value={Object.keys(data.por_subcategoria).length} icon="📂" />
        </section>
      )}

      {/* Cards de categorías */}
      <section>
        <h2 className="mb-4 text-xl font-semibold tracking-apple text-ink">Categorías del Inbox</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          {CATEGORIAS.map((cat) => {
            const count = data?.por_categoria[cat.id] ?? 0;
            return (
              <div key={cat.id} className="apple-card">
                <div className="flex items-baseline justify-between">
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl">{cat.icon}</span>
                    <h3 className="font-semibold text-ink">{cat.label}</h3>
                  </div>
                  <span className={`tabular text-sm font-semibold ${count > 0 ? 'text-brand' : 'text-ink-400'}`}>
                    {count}
                  </span>
                </div>
                <p className="mt-1 text-xs text-ink-600">{cat.desc}</p>
                <code className="mt-2 inline-block rounded bg-ink-50 px-2 py-0.5 text-[10px] text-ink-400">
                  inbox/{cat.id}/
                </code>
              </div>
            );
          })}
        </div>
      </section>

      {/* Últimos 10 archivos */}
      {data && data.ultimos_10.length > 0 && (
        <section>
          <h2 className="mb-4 text-xl font-semibold tracking-apple text-ink">
            📥 Últimos {data.ultimos_10.length} archivos procesados
          </h2>
          <div className="space-y-2">
            {data.ultimos_10.map((a) => (
              <div key={a.hash_md5} className="apple-card">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-ink-400">{new Date(a.fecha_procesado).toLocaleString('es-CL')}</span>
                      <span className="rounded-full bg-ink-50 px-2 py-0.5 text-[10px] font-medium text-ink-600">
                        {a.categoria}/{a.subcategoria}
                      </span>
                      <span className="text-[10px] text-ink-400">{a.size_kb.toFixed(1)} KB</span>
                      {a.duplicado_de && (
                        <span className="rounded-full bg-yellow-50 px-2 py-0.5 text-[10px] text-yellow-700">
                          duplicado
                        </span>
                      )}
                    </div>
                    <div className="mt-1 truncate font-medium text-ink">{a.filename}</div>
                    {a.sugerencias.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {a.sugerencias.map((s, i) => (
                          <div key={i} className="flex items-start gap-2 rounded bg-brand-50 p-2 text-xs">
                            <span className="shrink-0 text-brand">💡</span>
                            <div>
                              <span className="font-semibold text-brand">{s.tipo_dato}</span>
                              <span className="ml-2 rounded-full bg-white px-1.5 py-0.5 text-[9px] text-ink-600">
                                confianza {s.confianza}
                              </span>
                              <div className="mt-0.5 text-ink-600">
                                Sugiere actualizar:{' '}
                                <strong>
                                  {Array.isArray(s.celdas_o_modulo)
                                    ? s.celdas_o_modulo.join(', ')
                                    : s.celdas_o_modulo}
                                </strong>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {data?.nota && (
        <section className="apple-card border border-yellow-200 bg-yellow-50/50 text-sm text-yellow-800">
          ⚠ {data.nota}
        </section>
      )}

      {/* Loop virtuoso */}
      <section className="rounded-appleXl bg-ink-50 p-8">
        <h2 className="text-2xl font-semibold tracking-apple text-ink">🔄 Loop virtuoso de inteligencia</h2>
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-4">
          <FlujoCard num="1" titulo="Subes archivo" desc="A la subcarpeta correcta (ej cotización en 01-comercial/cotizaciones-mmpp/)" />
          <FlujoCard num="2" titulo="Procesador clasifica" desc="Detecta tipo, sugiere celdas, registra en audit trail" />
          <FlujoCard num="3" titulo="Actualizas matriz" desc="Editas plan_builder.py + variables_matrix.py: celdas PD → OK_VALIDADO" />
          <FlujoCard num="4" titulo="Score sube" desc="Readiness +N pts · Alertas resueltas · LP Pack ZIP refresca" />
        </div>
      </section>
    </div>
  );
}

function StatCard({ label, value, icon, tone }: { label: string; value: number; icon: string; tone?: 'ok' }) {
  const cls = tone === 'ok' ? 'text-brand' : 'text-ink';
  return (
    <div className="apple-card text-center">
      <div className="text-3xl">{icon}</div>
      <div className={`tabular mt-2 text-3xl font-semibold ${cls}`}>{value}</div>
      <div className="text-[11px] uppercase tracking-wider text-ink-400">{label}</div>
    </div>
  );
}

function FlujoCard({ num, titulo, desc }: { num: string; titulo: string; desc: string }) {
  return (
    <div className="apple-card">
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">{num}</div>
      <h3 className="mt-3 font-semibold text-ink">{titulo}</h3>
      <p className="mt-1 text-xs text-ink-600">{desc}</p>
    </div>
  );
}
