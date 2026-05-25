'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Accion = {
  id: string;
  titulo: string;
  descripcion: string;
  categoria: string;
  owner: string;
  impacto_tir: number;
  sinergia: number;
  uplift_readiness: number;
  quick_win: number;
  urgencia: number;
  prioridad: number;
  matrices_impactadas: string[];
  accion_concreta: string;
};

type DecisionesResp = {
  top_5: Accion[];
  todas: Accion[];
  total_acciones: number;
  impacto_potencial_tir_pp: number;
  uplift_potencial_readiness: number;
  quick_wins: Accion[];
};

const CAT_COLOR: Record<string, string> = {
  comercial: 'bg-brand-50 text-brand ring-brand/20',
  financiero: 'bg-orange-50 text-orange-600 ring-orange-200',
  operacional: 'bg-yellow-50 text-yellow-700 ring-yellow-200',
  esg: 'bg-brand-50 text-brand ring-brand/20',
  compliance: 'bg-red-50 text-red-600 ring-red-200',
  equipo: 'bg-ink-50 text-ink-600 ring-ink-100',
};

const CAT_ICON: Record<string, string> = {
  comercial: '💼',
  financiero: '💰',
  operacional: '⚙️',
  esg: '🌱',
  compliance: '📜',
  equipo: '👥',
};

export default function DecisionesPage() {
  const [data, setData] = useState<DecisionesResp | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [mostrarTodas, setMostrarTodas] = useState(false);

  useEffect(() => {
    fetch(`${ENGINE_URL}/decisiones/top`)
      .then((r) => (r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`)))
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Decision Engine</h1>
          <p className="mt-2 text-sm text-ink-400">
            El cerebro que une toda la plataforma. Combina variables, data room, coherencia,
            breakeven, sensitivity y readiness para producir las acciones que más mueven la aguja.
          </p>
        </div>
      </header>

      {err && <div className="apple-card border border-red-200 bg-red-50/40 text-red-600">{err}</div>}

      {data && (
        <>
          {/* Hero stats */}
          <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
                  Acciones detectadas
                </div>
                <div className="tabular mt-2 text-5xl font-semibold text-ink">{data.total_acciones}</div>
                <div className="text-sm text-ink-600">priorizadas por impacto</div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
                  Uplift potencial readiness
                </div>
                <div className="tabular mt-2 text-5xl font-semibold text-brand">
                  +{data.uplift_potencial_readiness.toFixed(0)}
                </div>
                <div className="text-sm text-ink-600">pts si se cierra todo</div>
              </div>
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
                  Quick wins
                </div>
                <div className="tabular mt-2 text-5xl font-semibold text-ink">{data.quick_wins.length}</div>
                <div className="text-sm text-ink-600">{'<'} 1 mes de ejecución</div>
              </div>
            </div>
          </section>

          {/* Quick wins */}
          {data.quick_wins.length > 0 && (
            <section>
              <h2 className="mb-4 text-2xl font-semibold tracking-apple text-ink">
                ⚡ Quick wins — empieza por estas
              </h2>
              <p className="mb-6 text-sm text-ink-400">
                Acciones que se pueden completar en días o semanas. Máximo retorno por esfuerzo mínimo.
              </p>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {data.quick_wins.map((a) => (
                  <div key={a.id} className="apple-card bg-brand-50 ring-1 ring-brand/20">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{CAT_ICON[a.categoria] || '📁'}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${CAT_COLOR[a.categoria]}`}>
                        {a.categoria}
                      </span>
                    </div>
                    <h3 className="mt-3 font-semibold text-ink">{a.titulo}</h3>
                    <p className="mt-1 text-xs text-ink-600">{a.owner}</p>
                    <div className="mt-3 flex items-baseline gap-3 text-xs">
                      <span className="text-brand"><strong className="tabular">+{a.uplift_readiness}</strong> pts</span>
                      <span className="text-ink-400">Quick-win <strong className="tabular">{a.quick_win}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* TOP 5 acciones priorizadas */}
          <section>
            <h2 className="mb-4 text-2xl font-semibold tracking-apple text-ink">
              🎯 Top 5 acciones priorizadas
            </h2>
            <p className="mb-6 text-sm text-ink-400">
              Ordenadas por prioridad: impacto TIR (30%) + sinergia (25%) + uplift readiness (20%) + quick-win (15%) + urgencia (10%).
            </p>
            <div className="space-y-4">
              {data.top_5.map((a, idx) => (
                <AccionCard key={a.id} a={a} ranking={idx + 1} />
              ))}
            </div>
          </section>

          {/* Toggle ver todas */}
          {data.todas.length > 5 && (
            <section>
              <button
                onClick={() => setMostrarTodas((v) => !v)}
                className="btn-apple btn-apple-ghost"
              >
                {mostrarTodas ? 'Ocultar' : `Ver ${data.todas.length - 5} acciones adicionales`}
              </button>
              {mostrarTodas && (
                <div className="mt-4 space-y-4">
                  {data.todas.slice(5).map((a, idx) => (
                    <AccionCard key={a.id} a={a} ranking={idx + 6} />
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Cómo se calcula */}
          <section className="rounded-appleXl bg-ink-50 p-8">
            <h2 className="text-2xl font-semibold tracking-apple text-ink">¿Cómo se prioriza una acción?</h2>
            <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-5">
              <ScoreLeyenda peso="30%" label="Impacto TIR" desc="Cuánto sube TIR si se cierra" />
              <ScoreLeyenda peso="25%" label="Sinergia" desc="Cuántos otros gaps cierra" />
              <ScoreLeyenda peso="20%" label="Uplift Readiness" desc="Puntos que suma al score" />
              <ScoreLeyenda peso="15%" label="Quick Win" desc="100=días, 0=meses" />
              <ScoreLeyenda peso="10%" label="Urgencia" desc="Bloqueante o no" />
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function AccionCard({ a, ranking }: { a: Accion; ranking: number }) {
  return (
    <div className="apple-card">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
          {ranking}
        </div>
        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xl">{CAT_ICON[a.categoria] || '📁'}</span>
            <h3 className="text-lg font-semibold text-ink">{a.titulo}</h3>
            <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${CAT_COLOR[a.categoria]}`}>
              {a.categoria}
            </span>
            <span className="ml-auto rounded-full bg-brand-50 px-2.5 py-0.5 text-[11px] font-semibold text-brand">
              Prioridad: {a.prioridad.toFixed(1)}
            </span>
          </div>
          <p className="mt-2 text-sm text-ink-600">{a.descripcion}</p>

          {/* Acción concreta */}
          <div className="mt-3 rounded-lg bg-ink-50 p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">
              Acción concreta
            </div>
            <p className="mt-1 text-sm text-ink-900">{a.accion_concreta}</p>
            <p className="mt-2 text-xs text-ink-400">Owner: <strong className="text-ink-600">{a.owner}</strong></p>
          </div>

          {/* Scoring bars */}
          <div className="mt-4 grid grid-cols-5 gap-2 border-t border-ink-100 pt-3">
            <ScoreBar label="Impacto TIR" value={a.impacto_tir} />
            <ScoreBar label="Sinergia" value={a.sinergia} />
            <ScoreBar label="Uplift" value={a.uplift_readiness * 10} actualValue={a.uplift_readiness} />
            <ScoreBar label="Quick-win" value={a.quick_win} />
            <ScoreBar label="Urgencia" value={a.urgencia} />
          </div>
        </div>
      </div>
    </div>
  );
}

function ScoreBar({ label, value, actualValue }: { label: string; value: number; actualValue?: number }) {
  const display = actualValue !== undefined ? actualValue : value;
  return (
    <div className="text-center">
      <div className="text-[9px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className="tabular mt-0.5 text-sm font-semibold text-ink">{display.toFixed(0)}</div>
      <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-ink-100">
        <div className="h-full bg-brand transition-all" style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  );
}

function ScoreLeyenda({ peso, label, desc }: { peso: string; label: string; desc: string }) {
  return (
    <div className="apple-card text-center">
      <div className="tabular text-2xl font-semibold text-brand">{peso}</div>
      <div className="mt-1 text-sm font-semibold text-ink">{label}</div>
      <div className="mt-1 text-[11px] text-ink-400">{desc}</div>
    </div>
  );
}
