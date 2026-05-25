'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type GapCoherente = {
  descripcion: string;
  matrices_afectadas: string[];
  severidad: 'critica' | 'alta' | 'media';
  accion_recomendada: string;
  sinergia: number;
};

type CoherenciaResp = {
  gaps_coherentes: GapCoherente[];
  total_gaps: number;
  sinergia_total: number;
  matrices_evaluadas: string[];
};

const SEV_COLOR: Record<string, string> = {
  critica: 'bg-red-50 text-red-600 ring-red-200',
  alta: 'bg-orange-50 text-orange-600 ring-orange-200',
  media: 'bg-yellow-50 text-yellow-700 ring-yellow-200',
};

const SEV_BORDER: Record<string, string> = {
  critica: 'border-red-200',
  alta: 'border-orange-200',
  media: 'border-yellow-200',
};

const MATRIX_LABEL: Record<string, { label: string; href: string; icon: string }> = {
  variables_matrix: { label: 'Matriz Variables', href: '/variables', icon: '📊' },
  data_room: { label: 'Data Room', href: '/data-room', icon: '📋' },
  readiness_score: { label: 'Readiness Score', href: '/readiness', icon: '💯' },
  compliance_rep: { label: 'Compliance REP', href: '/compliance', icon: '📜' },
};

export default function CoherenciaPage() {
  const [data, setData] = useState<CoherenciaResp | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/matriz/coherencia`)
      .then((r) => (r.ok ? r.json() : Promise.reject(`HTTP ${r.status}`)))
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, []);

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Coherencia Cross-Matriz</h1>
          <p className="mt-2 text-sm text-ink-400">
            Auditoría cruzada entre todas las matrices del modelo. Detecta gaps que
            aparecen simultáneamente en múltiples lugares — y prioriza las acciones
            con mayor sinergia (un solo dato cierra múltiples celdas).
          </p>
        </div>
      </header>

      {err && (
        <div className="apple-card border border-red-200 bg-red-50/40 text-red-600">{err}</div>
      )}

      {data && (
        <>
          {/* Stats */}
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Matrices evaluadas" value={data.matrices_evaluadas.length} />
            <StatCard label="Gaps coherentes" value={data.total_gaps} tone="warn" />
            <StatCard label="Sinergia total" value={data.sinergia_total} sub="celdas / items afectados" tone="ok" />
            <StatCard label="Acciones para cerrar todo" value={data.gaps_coherentes.length} sub="acciones" />
          </section>

          {/* Gaps ordenados por sinergia */}
          <section className="space-y-3">
            <h2 className="text-2xl font-semibold tracking-apple text-ink">
              Gaps priorizados por sinergia
            </h2>
            <p className="text-sm text-ink-400">
              Los gaps con mayor sinergia están arriba: cerrarlos resuelve múltiples problemas a la vez.
            </p>
            {data.gaps_coherentes.map((g, idx) => (
              <div key={idx} className={`apple-card border ${SEV_BORDER[g.severidad]}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${SEV_COLOR[g.severidad]}`}>
                        {g.severidad}
                      </span>
                      <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-brand">
                        Sinergia: {g.sinergia} celdas/items
                      </span>
                    </div>
                    <h3 className="mt-2 font-semibold text-ink">{g.descripcion}</h3>
                    <div className="mt-2 rounded-lg bg-ink-50 p-3">
                      <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">
                        Acción recomendada
                      </div>
                      <p className="mt-1 text-sm text-ink-600">{g.accion_recomendada}</p>
                    </div>
                  </div>
                </div>

                {/* Matrices afectadas */}
                <div className="mt-3 flex flex-wrap gap-2 border-t border-ink-100 pt-3">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-ink-400">
                    Aparece en:
                  </span>
                  {g.matrices_afectadas.map((m) => {
                    const meta = MATRIX_LABEL[m] || { label: m, href: '/', icon: '📁' };
                    return (
                      <a
                        key={m}
                        href={meta.href}
                        className="inline-flex items-center gap-1 rounded-full bg-ink-50 px-2.5 py-0.5 text-[11px] font-medium text-ink-600 transition hover:bg-brand-50 hover:text-brand"
                      >
                        <span>{meta.icon}</span> {meta.label}
                      </a>
                    );
                  })}
                </div>
              </div>
            ))}
          </section>

          {/* Cómo se usa */}
          <section className="rounded-appleXl bg-ink-50 p-8">
            <h2 className="text-2xl font-semibold tracking-apple text-ink">¿Cómo usar esta matriz?</h2>
            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
              <FlujoCard num="1" titulo="Mira el gap top" desc="El gap con mayor sinergia es la próxima acción más rentable. Cerrarlo desbloquea múltiples problemas." />
              <FlujoCard num="2" titulo="Asigna responsable" desc="Cada gap indica owner sugerido. Pasa la responsabilidad y agenda follow-up semanal." />
              <FlujoCard num="3" titulo="Mide el impacto" desc="Cuando cierras un gap, marca un hito en /readiness para ver el delta del score." />
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function StatCard({ label, value, sub, tone }: { label: string; value: number; sub?: string; tone?: 'warn' | 'ok' }) {
  const cls = tone === 'warn' ? 'text-orange-600' : tone === 'ok' ? 'text-brand' : 'text-ink';
  return (
    <div className="apple-card text-center">
      <div className="text-[10px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className={`tabular mt-1 text-3xl font-semibold ${cls}`}>{value}</div>
      {sub && <div className="text-[11px] text-ink-400">{sub}</div>}
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
