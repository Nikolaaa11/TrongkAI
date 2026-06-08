'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Ficha = {
  id: string; nombre: string; tipo: string; etapa_asociada: string;
  proveedor: string; modelo: string;
  capacidad_kg_h: number; capacidad_unidad: string; potencia_kw: number;
  consumo_agua_l_h: number; dimensiones: string; peso_kg: number;
  modalidad: string; capex_clp: number; arriendo_clp_mes: number; instalacion_clp: number;
  frecuencia_mantencion_h: number; costo_mantencion_clp: number; vida_util_anos: number;
  notas: string; ficha_tecnica_url: string; contacto_proveedor: string;
  foto_url: string;
  fecha_creacion: string; nivel_dato: 'PD' | 'OK_PROVISORIO' | 'OK_VALIDADO';
};

type Resp = { fichas: Ficha[]; resumen: { total_fichas: number; por_nivel: any; completitud_pct: number; pendientes_PD: any[] } };

const NIVEL_COLOR: Record<string, string> = {
  PD: 'bg-red-100 text-red-700',
  OK_PROVISORIO: 'bg-yellow-100 text-yellow-700',
  OK_VALIDADO: 'bg-brand-50 text-brand',
};

export default function EquiposPage() {
  const [data, setData] = useState<Resp | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState<Partial<Ficha>>({});
  const [saving, setSaving] = useState(false);

  const load = () => fetch(`${ENGINE_URL}/equipos/fichas`).then((r) => r.json()).then(setData);
  useEffect(() => { load(); }, []);

  if (!data) return <p className="text-ink-400">Cargando fichas equipos…</p>;

  const save = async (id: string) => {
    setSaving(true);
    try {
      await fetch(`${ENGINE_URL}/equipos/fichas/actualizar`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ equipo_id: id, updates: draft }),
      });
      setEditing(null); setDraft({}); load();
    } finally { setSaving(false); }
  };

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Sistema captura por equipo</p>
        <h1 className="mt-2 text-4xl font-bold">🏗 Fichas técnicas de equipos</h1>
        <p className="mt-2 text-ink-500">
          Alimentá info detallada de cada equipo según vayas recibiendo de proveedores y técnicos.
          La completitud sube automáticamente y mejora la precisión del costeo.
        </p>
      </header>

      {/* Resumen */}
      <section className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[10px] uppercase text-ink-400">Total fichas</p>
          <p className="mt-1 text-2xl font-bold">{data.resumen.total_fichas}</p>
        </div>
        <div className="rounded-xl border border-brand bg-brand-50/40 p-4">
          <p className="text-[10px] uppercase text-ink-400">Completitud</p>
          <p className="mt-1 text-2xl font-bold text-brand">{data.resumen.completitud_pct}/100</p>
        </div>
        <div className="rounded-xl border border-yellow-200 bg-yellow-50/40 p-4">
          <p className="text-[10px] uppercase text-ink-400">Provisorio</p>
          <p className="mt-1 text-2xl font-bold text-yellow-700">{data.resumen.por_nivel.OK_PROVISORIO || 0}</p>
        </div>
        <div className="rounded-xl border border-red-200 bg-red-50/40 p-4">
          <p className="text-[10px] uppercase text-ink-400">Sin validar (PD)</p>
          <p className="mt-1 text-2xl font-bold text-red-600">{data.resumen.por_nivel.PD || 0}</p>
        </div>
      </section>

      <section className="space-y-3">
        {data.fichas.map((f) => {
          const isEdit = editing === f.id;
          const v = (k: keyof Ficha) => (draft[k] !== undefined ? draft[k] : (f[k] as any));
          return (
            <div key={f.id} className={`rounded-xl border overflow-hidden ${isEdit ? 'border-brand bg-brand-50/20' : 'border-ink-100 bg-white'}`}>
              <div className="grid grid-cols-1 md:grid-cols-[180px,1fr]">
                {/* FOTO */}
                {f.foto_url ? (
                  <div className="bg-ink-50/40 flex items-center justify-center p-2 md:border-r border-ink-100">
                    <img src={f.foto_url} alt={f.nombre}
                      className="max-h-32 md:max-h-full w-full object-cover rounded-lg" />
                  </div>
                ) : (
                  <div className="bg-ink-50/30 flex items-center justify-center text-3xl text-ink-300 p-4 md:border-r border-ink-100">
                    📦
                  </div>
                )}
                <div className="p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-lg font-semibold">{f.nombre}</h3>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${NIVEL_COLOR[f.nivel_dato]}`}>{f.nivel_dato}</span>
                    <span className="text-[10px] text-ink-400">{f.etapa_asociada}</span>
                  </div>
                  <p className="mt-1 text-xs text-ink-500">{f.tipo} · {f.modalidad}</p>
                </div>
                {!isEdit && (
                  <button onClick={() => { setEditing(f.id); setDraft({}); }} className="rounded-full bg-ink px-3 py-1 text-xs font-semibold text-white">
                    Alimentar info
                  </button>
                )}
              </div>

              {isEdit ? (
                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <Field label="Proveedor" value={v('proveedor')} onChange={(x) => setDraft({ ...draft, proveedor: x })} />
                  <Field label="Modelo" value={v('modelo')} onChange={(x) => setDraft({ ...draft, modelo: x })} />
                  <Field label="Capacidad" value={v('capacidad_kg_h')} type="number" onChange={(x) => setDraft({ ...draft, capacidad_kg_h: +x })} suffix="kg/h" />
                  <Field label="Potencia" value={v('potencia_kw')} type="number" onChange={(x) => setDraft({ ...draft, potencia_kw: +x })} suffix="kW" />
                  <Field label="Consumo agua" value={v('consumo_agua_l_h')} type="number" onChange={(x) => setDraft({ ...draft, consumo_agua_l_h: +x })} suffix="L/h" />
                  <Field label="Dimensiones" value={v('dimensiones')} onChange={(x) => setDraft({ ...draft, dimensiones: x })} />
                  <Field label="CAPEX" value={v('capex_clp')} type="number" onChange={(x) => setDraft({ ...draft, capex_clp: +x })} suffix="CLP" />
                  <Field label="Arriendo OPEX" value={v('arriendo_clp_mes')} type="number" onChange={(x) => setDraft({ ...draft, arriendo_clp_mes: +x })} suffix="CLP/mes" />
                  <Field label="Mantención cada" value={v('frecuencia_mantencion_h')} type="number" onChange={(x) => setDraft({ ...draft, frecuencia_mantencion_h: +x })} suffix="h" />
                  <Field label="Costo mantención" value={v('costo_mantencion_clp')} type="number" onChange={(x) => setDraft({ ...draft, costo_mantencion_clp: +x })} suffix="CLP" />
                  <Field label="Vida útil" value={v('vida_util_anos')} type="number" onChange={(x) => setDraft({ ...draft, vida_util_anos: +x })} suffix="años" />
                  <Field label="Contacto proveedor" value={v('contacto_proveedor')} onChange={(x) => setDraft({ ...draft, contacto_proveedor: x })} />
                  <div className="col-span-2">
                    <label className="text-xs text-ink-500">Notas técnicas</label>
                    <textarea value={v('notas')} onChange={(e) => setDraft({ ...draft, notas: e.target.value })} className="w-full mt-1 rounded border border-ink-200 px-2 py-1 text-sm" rows={2} />
                  </div>
                  <div className="col-span-2 flex items-center justify-between">
                    <select value={v('nivel_dato')} onChange={(e) => setDraft({ ...draft, nivel_dato: e.target.value as any })} className="rounded border border-ink-200 px-3 py-1 text-sm">
                      <option value="PD">PD (placeholder)</option>
                      <option value="OK_PROVISORIO">OK_PROVISORIO (validado literatura)</option>
                      <option value="OK_VALIDADO">OK_VALIDADO (validado en planta)</option>
                    </select>
                    <div className="flex gap-2">
                      <button onClick={() => { setEditing(null); setDraft({}); }} className="rounded-full bg-ink-100 px-4 py-1 text-sm">Cancelar</button>
                      <button onClick={() => save(f.id)} disabled={saving} className="rounded-full bg-brand px-4 py-1 text-sm font-semibold text-white">
                        {saving ? '…' : '💾 Guardar'}
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-ink-600 md:grid-cols-4">
                  {f.proveedor && <span>📍 {f.proveedor}</span>}
                  {f.modelo && <span>🔧 {f.modelo}</span>}
                  {f.capacidad_kg_h > 0 && <span>📊 {f.capacidad_kg_h} {f.capacidad_unidad}</span>}
                  {f.potencia_kw > 0 && <span>⚡ {f.potencia_kw} kW</span>}
                  {f.capex_clp > 0 && <span>💰 CAPEX ${(f.capex_clp / 1e6).toFixed(1)}M</span>}
                  {f.arriendo_clp_mes > 0 && <span>📅 Arriendo ${(f.arriendo_clp_mes / 1e6).toFixed(1)}M/mes</span>}
                  {f.notas && <p className="col-span-full text-ink-500 italic">{f.notas}</p>}
                </div>
              )}
                </div>
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', suffix }: { label: string; value: any; onChange: (x: string) => void; type?: string; suffix?: string }) {
  return (
    <div>
      <label className="text-xs text-ink-500">{label}{suffix && ` (${suffix})`}</label>
      <input type={type} value={value || ''} onChange={(e) => onChange(e.target.value)}
        className="w-full mt-1 rounded border border-ink-200 px-2 py-1 text-sm" />
    </div>
  );
}
