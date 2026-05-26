'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type LP = {
  id: string;
  nombre: string;
  tipo: string;
  pais: string;
  ticket_esperado_usd: number;
  etapa: string;
  prob_cierre: number;
  ticket_ponderado_usd?: number;
  proxima_accion: string;
  proxima_accion_owner: string;
  proxima_accion_fecha: string;
  notas: string;
  fecha_ultimo_contacto?: string;
};

type PipelineResp = {
  lps: LP[];
  resumen: {
    total_lps: number;
    por_etapa: Record<string, number>;
    ticket_pipeline_usd: number;
    ticket_ponderado_usd: number;
    objetivo_usd: number;
    pct_objetivo_pipeline: number;
    pct_objetivo_ponderado: number;
    proximas_acciones_7d: number;
  };
};

const ETAPAS = [
  { id: 'prospect', label: 'Prospect', color: 'bg-ink-50 text-ink-600 border-ink-100' },
  { id: 'contactado', label: 'Contactado', color: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
  { id: 'reunion', label: 'Reunión', color: 'bg-orange-50 text-orange-600 border-orange-200' },
  { id: 'dd', label: 'Due Diligence', color: 'bg-brand-50 text-brand border-brand/20' },
  { id: 'comprometido', label: 'Comprometido', color: 'bg-brand-50 text-brand border-brand/40' },
  { id: 'ganado', label: 'Ganado ✓', color: 'bg-brand-100 text-brand-700 border-brand/60' },
];

const TIPO_LABEL: Record<string, string> = {
  fondo: '🏦 Fondo',
  family_office: '🏰 Family Office',
  dfi: '🌍 DFI',
  banco: '🏛 Banco',
  particular: '👤 Particular',
  corporativo: '🏢 Corporativo',
};

export default function PipelineLPPage() {
  const [data, setData] = useState<PipelineResp | null>(null);
  const [editingLP, setEditingLP] = useState<LP | null>(null);
  const [modalNuevo, setModalNuevo] = useState(false);

  useEffect(() => {
    void cargar();
  }, []);

  async function cargar() {
    const r = await fetch(`${ENGINE_URL}/lp/pipeline`);
    if (r.ok) setData(await r.json());
  }

  async function guardarLP(lp: Partial<LP>) {
    await fetch(`${ENGINE_URL}/lp/upsert`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(lp),
    });
    setEditingLP(null);
    setModalNuevo(false);
    void cargar();
  }

  async function eliminarLP(id: string) {
    if (!confirm('¿Eliminar este LP del pipeline?')) return;
    await fetch(`${ENGINE_URL}/lp/${id}`, { method: 'DELETE' });
    setEditingLP(null);
    void cargar();
  }

  if (!data) {
    return <div className="apple-card text-ink-400">Cargando pipeline...</div>;
  }

  return (
    <div className="space-y-8">
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
          <div>
            <h1 className="font-serif text-3xl text-ink">Pipeline LP (CRM)</h1>
            <p className="mt-2 text-sm text-ink-400">
              Tracking de Limited Partners en roadshow. Kanban por etapa con ticket ponderado por probabilidad de cierre.
            </p>
          </div>
        </div>
        <button onClick={() => setModalNuevo(true)} className="btn-apple text-sm">
          + Nuevo LP
        </button>
      </header>

      {/* Hero stats */}
      <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Pipeline total</div>
            <div className="tabular mt-2 text-3xl font-semibold text-ink">
              ${(data.resumen.ticket_pipeline_usd / 1e6).toFixed(1)}M
            </div>
            <div className="text-xs text-ink-600">{data.resumen.total_lps} LPs activos</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Ponderado por prob.</div>
            <div className="tabular mt-2 text-3xl font-semibold text-brand">
              ${(data.resumen.ticket_ponderado_usd / 1e6).toFixed(1)}M
            </div>
            <div className="text-xs text-ink-600">{data.resumen.pct_objetivo_ponderado.toFixed(0)}% objetivo</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Objetivo round</div>
            <div className="tabular mt-2 text-3xl font-semibold text-ink">
              ${(data.resumen.objetivo_usd / 1e6).toFixed(0)}M
            </div>
            <div className="text-xs text-ink-600">target round Trongkai</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Acciones próx. 7d</div>
            <div className="tabular mt-2 text-3xl font-semibold text-orange-600">
              {data.resumen.proximas_acciones_7d}
            </div>
            <div className="text-xs text-ink-600">próximas tareas vencen</div>
          </div>
        </div>

        {/* Barra de progreso */}
        <div className="mt-6">
          <div className="relative h-3 w-full overflow-hidden rounded-full bg-white">
            <div
              className="absolute h-full bg-ink-200 transition-all"
              style={{ width: `${Math.min(100, data.resumen.pct_objetivo_pipeline)}%` }}
            />
            <div
              className="absolute h-full bg-brand transition-all"
              style={{ width: `${Math.min(100, data.resumen.pct_objetivo_ponderado)}%` }}
            />
          </div>
          <div className="mt-1 flex justify-between text-[11px] text-ink-400">
            <span>$0M</span>
            <span>${(data.resumen.objetivo_usd / 1e6).toFixed(0)}M (target)</span>
          </div>
        </div>
      </section>

      {/* Kanban */}
      <section className="overflow-x-auto">
        <div className="flex gap-3" style={{ minWidth: '900px' }}>
          {ETAPAS.map((etapa) => {
            const lpsEnEtapa = data.lps.filter((lp) => lp.etapa === etapa.id);
            const ticketEtapa = lpsEnEtapa.reduce((s, lp) => s + (lp.ticket_esperado_usd || 0), 0);
            return (
              <div key={etapa.id} className="flex-1 min-w-[170px]">
                <div className={`rounded-t-lg border ${etapa.color} px-3 py-2`}>
                  <div className="flex items-baseline justify-between">
                    <span className="text-[11px] font-semibold uppercase tracking-wider">{etapa.label}</span>
                    <span className="text-xs">{lpsEnEtapa.length}</span>
                  </div>
                  <div className="tabular mt-1 text-xs">${(ticketEtapa / 1e6).toFixed(1)}M</div>
                </div>
                <div className="space-y-2 rounded-b-lg border border-t-0 border-ink-100 bg-ink-50/50 p-2 min-h-[200px]">
                  {lpsEnEtapa.map((lp) => (
                    <button
                      key={lp.id}
                      onClick={() => setEditingLP(lp)}
                      className="w-full rounded-lg border border-ink-100 bg-white p-3 text-left transition hover:border-brand/40 hover:shadow-apple"
                    >
                      <div className="font-semibold text-ink text-sm">{lp.nombre}</div>
                      <div className="mt-1 text-[10px] text-ink-400">{TIPO_LABEL[lp.tipo] || lp.tipo} · {lp.pais}</div>
                      <div className="mt-2 tabular text-base font-semibold text-brand">
                        ${(lp.ticket_esperado_usd / 1e6).toFixed(1)}M
                      </div>
                      <div className="text-[10px] text-ink-400">prob {lp.prob_cierre}% · pond ${((lp.ticket_ponderado_usd ?? lp.ticket_esperado_usd * lp.prob_cierre / 100) / 1e6).toFixed(1)}M</div>
                      {lp.proxima_accion && (
                        <div className="mt-2 rounded bg-ink-50 px-1.5 py-1 text-[10px] text-ink-600">
                          📅 {lp.proxima_accion_fecha} · {lp.proxima_accion.slice(0, 30)}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Modal editor */}
      {(editingLP || modalNuevo) && (
        <LPModal
          lp={editingLP}
          onClose={() => { setEditingLP(null); setModalNuevo(false); }}
          onSave={guardarLP}
          onDelete={editingLP ? () => eliminarLP(editingLP.id) : undefined}
        />
      )}
    </div>
  );
}

function LPModal({
  lp,
  onClose,
  onSave,
  onDelete,
}: {
  lp: LP | null;
  onClose: () => void;
  onSave: (lp: Partial<LP>) => void;
  onDelete?: () => void;
}) {
  const [form, setForm] = useState<Partial<LP>>(
    lp ?? {
      nombre: '',
      tipo: 'fondo',
      pais: 'Chile',
      ticket_esperado_usd: 1_000_000,
      etapa: 'prospect',
      prob_cierre: 20,
      proxima_accion: '',
      proxima_accion_owner: 'Nicolás',
      proxima_accion_fecha: '',
      notas: '',
    }
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="apple-card w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-xl font-semibold text-ink">{lp ? `Editar ${lp.nombre}` : 'Nuevo LP'}</h3>
        <div className="mt-4 grid grid-cols-2 gap-3">
          <Field label="Nombre *">
            <input value={form.nombre || ''} onChange={(e) => setForm({ ...form, nombre: e.target.value })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <Field label="País">
            <input value={form.pais || ''} onChange={(e) => setForm({ ...form, pais: e.target.value })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <Field label="Tipo">
            <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm">
              <option value="fondo">Fondo</option>
              <option value="family_office">Family Office</option>
              <option value="dfi">DFI</option>
              <option value="banco">Banco</option>
              <option value="particular">Particular</option>
              <option value="corporativo">Corporativo</option>
            </select>
          </Field>
          <Field label="Etapa">
            <select value={form.etapa} onChange={(e) => setForm({ ...form, etapa: e.target.value })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm">
              <option value="prospect">Prospect</option>
              <option value="contactado">Contactado</option>
              <option value="reunion">Reunión</option>
              <option value="dd">Due Diligence</option>
              <option value="comprometido">Comprometido</option>
              <option value="ganado">Ganado ✓</option>
              <option value="perdido">Perdido</option>
            </select>
          </Field>
          <Field label="Ticket esperado USD">
            <input type="number" value={form.ticket_esperado_usd || 0} onChange={(e) => setForm({ ...form, ticket_esperado_usd: Number(e.target.value) })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <Field label="Prob cierre (0-100)">
            <input type="number" min={0} max={100} value={form.prob_cierre || 0} onChange={(e) => setForm({ ...form, prob_cierre: Number(e.target.value) })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <Field label="Próxima acción">
            <input value={form.proxima_accion || ''} onChange={(e) => setForm({ ...form, proxima_accion: e.target.value })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <Field label="Owner">
            <input value={form.proxima_accion_owner || ''} onChange={(e) => setForm({ ...form, proxima_accion_owner: e.target.value })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <Field label="Fecha próxima acción">
            <input type="date" value={form.proxima_accion_fecha || ''} onChange={(e) => setForm({ ...form, proxima_accion_fecha: e.target.value })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <Field label="Fecha último contacto">
            <input type="date" value={form.fecha_ultimo_contacto || ''} onChange={(e) => setForm({ ...form, fecha_ultimo_contacto: e.target.value })} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
          </Field>
          <div className="col-span-2">
            <Field label="Notas">
              <textarea value={form.notas || ''} onChange={(e) => setForm({ ...form, notas: e.target.value })} rows={3} className="w-full rounded-lg border border-ink-100 px-3 py-2 text-sm" />
            </Field>
          </div>
        </div>
        <div className="mt-5 flex justify-between gap-2">
          <div>
            {onDelete && (
              <button onClick={onDelete} className="rounded-full px-4 py-2 text-sm text-red-600 hover:bg-red-50">
                Eliminar
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <button onClick={onClose} className="btn-apple btn-apple-ghost text-sm">Cancelar</button>
            <button onClick={() => onSave(form)} disabled={!form.nombre} className="btn-apple text-sm">
              Guardar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-ink-400">{label}</div>
      {children}
    </label>
  );
}
