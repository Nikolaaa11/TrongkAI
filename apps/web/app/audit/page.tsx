'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Entry = {
  timestamp: string;
  tipo: string;
  actor: string;
  descripcion: string;
  valor_anterior: any;
  valor_nuevo: any;
  metadata: any;
  impacto_estimado: string | null;
};

type AuditResp = {
  entries: Entry[];
  stats: {
    total_eventos: number;
    by_tipo: Record<string, number>;
    by_actor: Record<string, number>;
    primer_evento: string | null;
    ultimo_evento: string | null;
  };
};

const TIPO_COLOR: Record<string, string> = {
  matriz_celda_actualizada: 'bg-brand-50 text-brand',
  supuesto_cambiado: 'bg-orange-50 text-orange-600',
  decision_marcada: 'bg-yellow-50 text-yellow-700',
  hito_completado: 'bg-brand-50 text-brand',
  datos_equipo_recibidos: 'bg-brand-50 text-brand',
  snapshot_creado: 'bg-ink-50 text-ink-600',
  alerta_resuelta: 'bg-brand-50 text-brand',
  deploy: 'bg-ink-50 text-ink-600',
  modelo_recalibrado: 'bg-orange-50 text-orange-600',
  otro: 'bg-ink-50 text-ink-600',
};

export default function AuditPage() {
  const [data, setData] = useState<AuditResp | null>(null);
  const [filtroTipo, setFiltroTipo] = useState<string>('todos');
  const [logModalAbierto, setLogModalAbierto] = useState(false);

  useEffect(() => {
    void cargar();
  }, [filtroTipo]);

  async function cargar() {
    const url = filtroTipo === 'todos'
      ? `${ENGINE_URL}/audit/trail?limit=100`
      : `${ENGINE_URL}/audit/trail?limit=100&tipo=${filtroTipo}`;
    const r = await fetch(url);
    if (r.ok) setData(await r.json());
  }

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
          <div>
            <h1 className="font-serif text-3xl text-ink">Audit Trail</h1>
            <p className="mt-2 text-sm text-ink-400">
              Historial inmutable de cambios al modelo. Para defenderse en due diligence
              y trazabilidad de decisiones.
            </p>
          </div>
        </div>
        <button onClick={() => setLogModalAbierto(true)} className="btn-apple text-xs">
          + Registrar evento
        </button>
      </header>

      {data && (
        <>
          {/* Stats */}
          <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Total eventos" value={data.stats.total_eventos} />
            <StatCard label="Tipos distintos" value={Object.keys(data.stats.by_tipo).length} />
            <StatCard label="Actores" value={Object.keys(data.stats.by_actor).length} />
            <StatCard label="Primer evento" value={data.stats.primer_evento?.slice(0, 10) ?? '—'} sub="" small />
          </section>

          {/* Filtros */}
          <section className="flex flex-wrap items-center gap-2">
            <FiltroBtn label="Todos" count={data.stats.total_eventos} active={filtroTipo === 'todos'} onClick={() => setFiltroTipo('todos')} />
            {Object.entries(data.stats.by_tipo).map(([tipo, n]) => (
              <FiltroBtn key={tipo} label={tipo} count={n} active={filtroTipo === tipo} onClick={() => setFiltroTipo(tipo)} />
            ))}
          </section>

          {/* Lista de eventos */}
          <section className="space-y-2">
            {data.entries.length === 0 ? (
              <div className="apple-card text-center text-ink-400">
                No hay eventos aún. Usa "+ Registrar evento" para empezar a trackear cambios.
              </div>
            ) : (
              data.entries.map((e, idx) => (
                <div key={idx} className="apple-card">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 text-xs">
                        <span className="text-ink-400">{new Date(e.timestamp).toLocaleString('es-CL')}</span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${TIPO_COLOR[e.tipo] || 'bg-ink-50 text-ink-600'}`}>
                          {e.tipo}
                        </span>
                        <span className="text-ink-600">por <strong>{e.actor}</strong></span>
                      </div>
                      <div className="mt-1.5 font-medium text-ink">{e.descripcion}</div>
                      {(e.valor_anterior !== null || e.valor_nuevo !== null) && (
                        <div className="mt-2 flex items-center gap-3 text-sm">
                          {e.valor_anterior !== null && (
                            <span className="rounded bg-red-50 px-2 py-0.5 text-red-600 line-through">{String(e.valor_anterior)}</span>
                          )}
                          {e.valor_anterior !== null && e.valor_nuevo !== null && <span className="text-ink-400">→</span>}
                          {e.valor_nuevo !== null && (
                            <span className="rounded bg-brand-50 px-2 py-0.5 font-semibold text-brand">{String(e.valor_nuevo)}</span>
                          )}
                        </div>
                      )}
                      {e.impacto_estimado && (
                        <div className="mt-2 text-xs text-ink-600 italic">📈 {e.impacto_estimado}</div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </section>
        </>
      )}

      {/* Modal para registrar evento */}
      {logModalAbierto && (
        <LogEventoModal
          onClose={() => setLogModalAbierto(false)}
          onSaved={() => {
            setLogModalAbierto(false);
            void cargar();
          }}
        />
      )}
    </div>
  );
}

function StatCard({ label, value, sub, small }: { label: string; value: number | string; sub?: string; small?: boolean }) {
  return (
    <div className="apple-card text-center">
      <div className="text-[10px] uppercase tracking-wider text-ink-400">{label}</div>
      <div className={`tabular mt-1 ${small ? 'text-base' : 'text-3xl'} font-semibold text-ink`}>{value}</div>
      {sub && <div className="text-[11px] text-ink-400">{sub}</div>}
    </div>
  );
}

function FiltroBtn({ label, count, active, onClick }: { label: string; count: number; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-xs font-medium transition ${
        active ? 'bg-ink text-white' : 'bg-ink-50 text-ink-600 hover:bg-ink-100'
      }`}
    >
      {label} <span className="opacity-70">({count})</span>
    </button>
  );
}

function LogEventoModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [tipo, setTipo] = useState('matriz_celda_actualizada');
  const [descripcion, setDescripcion] = useState('');
  const [actor, setActor] = useState('Nicolás');
  const [valorAnterior, setValorAnterior] = useState('');
  const [valorNuevo, setValorNuevo] = useState('');
  const [saving, setSaving] = useState(false);

  async function guardar() {
    if (!descripcion.trim()) return;
    setSaving(true);
    await fetch(`${ENGINE_URL}/audit/log`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        tipo,
        descripcion,
        actor,
        valor_anterior: valorAnterior || null,
        valor_nuevo: valorNuevo || null,
      }),
    });
    setSaving(false);
    onSaved();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="apple-card w-full max-w-lg bg-white" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-xl font-semibold text-ink">Registrar evento</h3>
        <div className="mt-4 space-y-3">
          <Field label="Tipo">
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm">
              <option>matriz_celda_actualizada</option>
              <option>supuesto_cambiado</option>
              <option>decision_marcada</option>
              <option>hito_completado</option>
              <option>datos_equipo_recibidos</option>
              <option>alerta_resuelta</option>
              <option>modelo_recalibrado</option>
              <option>otro</option>
            </select>
          </Field>
          <Field label="Descripción *">
            <textarea value={descripcion} onChange={(e) => setDescripcion(e.target.value)} placeholder="Ej: Cotización firme MMPP recibida de Oliveros XX" rows={2} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <Field label="Actor">
            <input value={actor} onChange={(e) => setActor(e.target.value)} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Valor anterior">
              <input value={valorAnterior} onChange={(e) => setValorAnterior(e.target.value)} placeholder="opcional" className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
            </Field>
            <Field label="Valor nuevo">
              <input value={valorNuevo} onChange={(e) => setValorNuevo(e.target.value)} placeholder="opcional" className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
            </Field>
          </div>
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="btn-apple btn-apple-ghost text-sm">Cancelar</button>
          <button onClick={guardar} disabled={saving || !descripcion.trim()} className="btn-apple text-sm">
            {saving ? 'Guardando...' : 'Registrar'}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-ink-400">{label}</div>
      {children}
    </label>
  );
}
