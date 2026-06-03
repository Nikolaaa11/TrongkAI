'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Trabajador = {
  id: string;
  nombre: string;
  categoria: string;
  turno: string;
  horas_contrato_semanal: number;
  horas_max_legales_sem: number;
  sueldo_base_clp: number;
  activo: boolean;
};

type Asignacion = {
  trabajador_id: string;
  semana_iso: string;
  horas_regulares: number;
  horas_extras: number;
  horas_totales: number;
  tareas: string[];
  equipo_asignado: string;
};

type Alarma = {
  tipo: string;
  severidad: 'critica' | 'alta' | 'media';
  trabajador?: string;
  mensaje: string;
  accion?: string;
};

type Balance = {
  trabajadores: Trabajador[];
  asignaciones_semana_actual: Asignacion[];
  semana_referencia: string;
  total_horas_disponibles_sem: number;
  total_horas_asignadas_sem: number;
  utilizacion_pct: number;
  costo_total_mensual_clp: number;
  costo_horas_extra_mensual_clp: number;
  productividad_kg_por_hh: number;
  closure_pct: number;
  rotacion_anual_pct: number;
  alarmas: Alarma[];
};

const COLOR_TURNO: Record<string, string> = {
  'mañana': 'bg-yellow-50 text-yellow-700',
  'tarde': 'bg-orange-50 text-orange-700',
  'noche': 'bg-indigo-50 text-indigo-700',
  'rotativo': 'bg-purple-50 text-purple-700',
};

export default function BalanceRRHHPage() {
  const [data, setData] = useState<Balance | null>(null);
  const [editing, setEditing] = useState<Record<string, { regulares: number; extras: number }>>({});
  const [savingId, setSavingId] = useState<string | null>(null);

  const load = () => {
    fetch(`${ENGINE_URL}/balance/rrhh`).then((r) => r.json()).then(setData);
  };

  useEffect(() => { load(); }, []);

  if (!data) return <p className="text-ink-400">Cargando balance RRHH…</p>;

  const criticas = data.alarmas.filter((a) => a.severidad === 'critica');
  const altas = data.alarmas.filter((a) => a.severidad === 'alta');
  const trabajadorById = new Map(data.trabajadores.map((t) => [t.id, t]));

  const saveAsignacion = async (trabId: string, semana: string) => {
    const e = editing[trabId];
    if (!e) return;
    setSavingId(trabId);
    try {
      const res = await fetch(`${ENGINE_URL}/balance/rrhh/asignar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trabajador_id: trabId,
          semana_iso: semana,
          horas_regulares: e.regulares,
          horas_extras: e.extras,
        }),
      });
      const json = await res.json();
      if (json.tiene_alarma_critica) {
        alert(`🚨 ALARMA CRÍTICA disparada:\n\n${json.alarmas_disparadas.map((a: Alarma) => a.mensaje).join('\n')}`);
      }
      setEditing((p) => {
        const next = { ...p };
        delete next[trabId];
        return next;
      });
      load();
    } finally {
      setSavingId(null);
    }
  };

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Balance de RRHH</p>
        <h1 className="mt-2 text-4xl font-bold">👥 {data.trabajadores.length} trabajadores · semana {data.semana_referencia}</h1>
        <p className="mt-2 text-ink-500">Alarmas activas según CT Chile (Art. 22 y 31)</p>
      </header>

      {/* BANNER CRÍTICO */}
      {criticas.length > 0 && (
        <div className="rounded-2xl border-l-4 border-red-500 bg-red-50 p-5">
          <h3 className="text-lg font-bold text-red-700">
            🚨 {criticas.length} alarmas CRÍTICAS de horas
          </h3>
          <ul className="mt-3 space-y-1 text-sm text-red-700">
            {criticas.map((a, i) => (
              <li key={i}>
                <span className="font-semibold">{a.mensaje}</span>
                {a.accion && <span className="block pl-4 text-red-600">→ {a.accion}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {altas.length > 0 && (
        <div className="rounded-xl border-l-4 border-orange-500 bg-orange-50 p-4">
          <h3 className="font-bold text-orange-700">⚠️ {altas.length} alarmas altas (excede contrato)</h3>
          <ul className="mt-2 space-y-1 text-sm text-orange-700">
            {altas.map((a, i) => (<li key={i}>{a.mensaje}</li>))}
          </ul>
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[11px] uppercase text-ink-400">HH disponibles/sem</p>
          <p className="mt-1 text-xl font-bold">{data.total_horas_disponibles_sem}h</p>
        </div>
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[11px] uppercase text-ink-400">HH asignadas/sem</p>
          <p className="mt-1 text-xl font-bold">{data.total_horas_asignadas_sem}h</p>
        </div>
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[11px] uppercase text-ink-400">Utilización</p>
          <p className="mt-1 text-xl font-bold">{(data.utilizacion_pct * 100).toFixed(0)}%</p>
        </div>
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[11px] uppercase text-ink-400">Productividad</p>
          <p className="mt-1 text-xl font-bold">{data.productividad_kg_por_hh.toFixed(1)} kg/hh</p>
        </div>
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[11px] uppercase text-ink-400">Costo mensual</p>
          <p className="mt-1 text-xl font-bold">${(data.costo_total_mensual_clp / 1e6).toFixed(1)}M CLP</p>
        </div>
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[11px] uppercase text-ink-400">Extras mensuales</p>
          <p className="mt-1 text-xl font-bold">${(data.costo_horas_extra_mensual_clp / 1e3).toFixed(0)}k CLP</p>
        </div>
      </div>

      {/* Tabla trabajadores con barras de progreso */}
      <section>
        <h2 className="mb-4 text-xl font-bold">Trabajadores · semana {data.semana_referencia}</h2>
        <div className="space-y-2">
          {data.asignaciones_semana_actual.map((a) => {
            const t = trabajadorById.get(a.trabajador_id);
            if (!t) return null;
            const total = a.horas_totales;
            const isOverContract = a.horas_regulares > t.horas_contrato_semanal;
            const isOverLegal = total > t.horas_max_legales_sem;
            const isOverExtras = a.horas_extras > 12;
            const pctRegular = Math.min(100, (a.horas_regulares / 45) * 100);
            const pctExtras = Math.min(100, (a.horas_extras / 12) * 100);
            const isEditing = editing[t.id];
            return (
              <div key={t.id} className={`rounded-xl border p-4 ${isOverLegal || isOverExtras ? 'border-red-300 bg-red-50' : isOverContract ? 'border-orange-300 bg-orange-50' : 'border-ink-100 bg-white'}`}>
                <div className="flex items-center justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{t.nombre}</span>
                      <span className="text-xs text-ink-400">{t.id}</span>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${COLOR_TURNO[t.turno] || 'bg-ink-50 text-ink-600'}`}>{t.turno}</span>
                      <span className="rounded-full bg-ink-50 px-2 py-0.5 text-[10px] uppercase text-ink-600">{t.categoria}</span>
                    </div>
                    <div className="mt-3 space-y-2">
                      <div>
                        <div className="flex justify-between text-xs">
                          <span>Regulares: <strong>{a.horas_regulares}h</strong> / 45h</span>
                          <span className={isOverContract ? 'font-bold text-red-600' : 'text-ink-400'}>
                            {isOverContract && '⚠️ Excede contrato'}
                          </span>
                        </div>
                        <div className="mt-1 h-2 overflow-hidden rounded-full bg-ink-100">
                          <div className={`h-full ${isOverContract ? 'bg-red-500' : 'bg-brand'}`} style={{ width: `${pctRegular}%` }} />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-xs">
                          <span>Extras: <strong>{a.horas_extras}h</strong> / 12h máx legal</span>
                          <span className={isOverExtras ? 'font-bold text-red-600' : 'text-ink-400'}>
                            {isOverExtras && '🚨 Excede Art. 31 CT'}
                          </span>
                        </div>
                        <div className="mt-1 h-2 overflow-hidden rounded-full bg-ink-100">
                          <div className={`h-full ${isOverExtras ? 'bg-red-500' : a.horas_extras > 6 ? 'bg-orange-500' : 'bg-brand'}`} style={{ width: `${pctExtras}%` }} />
                        </div>
                      </div>
                      <p className="text-xs text-ink-500">
                        Total: <span className={`font-semibold ${isOverLegal ? 'text-red-600' : ''}`}>{total}h</span> · Equipo: {a.equipo_asignado}
                      </p>
                    </div>
                  </div>

                  {/* Editor inline */}
                  <div className="flex flex-col items-end gap-1">
                    {!isEditing ? (
                      <button
                        onClick={() => setEditing({ ...editing, [t.id]: { regulares: a.horas_regulares, extras: a.horas_extras } })}
                        className="rounded-full bg-ink px-3 py-1 text-xs font-semibold text-white hover:bg-ink-700"
                      >
                        Editar
                      </button>
                    ) : (
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 text-xs">
                          <label className="w-12">Reg</label>
                          <input
                            type="number"
                            value={isEditing.regulares}
                            onChange={(e) => setEditing({ ...editing, [t.id]: { ...isEditing, regulares: +e.target.value } })}
                            className="w-16 rounded border border-ink-200 px-2 py-0.5"
                            step="0.5"
                            min="0"
                            max="80"
                          />
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <label className="w-12">Extras</label>
                          <input
                            type="number"
                            value={isEditing.extras}
                            onChange={(e) => setEditing({ ...editing, [t.id]: { ...isEditing, extras: +e.target.value } })}
                            className="w-16 rounded border border-ink-200 px-2 py-0.5"
                            step="0.5"
                            min="0"
                            max="30"
                          />
                        </div>
                        <div className="flex gap-1">
                          <button
                            onClick={() => saveAsignacion(t.id, a.semana_iso)}
                            disabled={savingId === t.id}
                            className="rounded-full bg-brand px-3 py-1 text-xs font-semibold text-white"
                          >
                            {savingId === t.id ? '…' : 'Guardar'}
                          </button>
                          <button
                            onClick={() => setEditing((p) => { const n = { ...p }; delete n[t.id]; return n; })}
                            className="rounded-full bg-ink-100 px-3 py-1 text-xs font-semibold text-ink-600"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <p className="text-xs text-ink-400">
        Referencias: Código del Trabajo Chile Art. 22 (45h/sem) · Art. 31 (12h extras/sem, ~32h/mes) · Multas DT 5-20 UTM por trabajador en exceso.
      </p>
    </div>
  );
}
