'use client';

import { useMemo, useState } from 'react';
import { seed, suppliersActivos } from '@/lib/seed-data';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

const TEMPORADAS_DEFAULT = [
  { mmpp_codigo: 'ALPERUJO', mes_inicio: 4, mes_fin: 6, tiempo_descomposicion_h: 8 },
  { mmpp_codigo: 'TOMASA', mes_inicio: 1, mes_fin: 3, tiempo_descomposicion_h: 3 },
  { mmpp_codigo: 'POMASA', mes_inicio: 3, mes_fin: 5, tiempo_descomposicion_h: 4 },
];

const CAPACIDADES_HIPOTESIS = [
  { etapa: 'RECEPCION', ton_por_hora: 10, tiempo_residencia_h: 0.2, aplica: true },
  { etapa: 'ALIMENTACION', ton_por_hora: 8, tiempo_residencia_h: 0.1, aplica: true },
  { etapa: 'HOMOG_1', ton_por_hora: 8, tiempo_residencia_h: 0.1, aplica: true },
  { etapa: 'PEF', ton_por_hora: 6, tiempo_residencia_h: 0.1, aplica: true },
  { etapa: 'PRENSADO_MECANICO', ton_por_hora: 5, tiempo_residencia_h: 0.2, aplica: true },
  { etapa: 'SECADO', ton_por_hora: 2.5, tiempo_residencia_h: 1.5, aplica: true },
  { etapa: 'HOMOG_2', ton_por_hora: 5, tiempo_residencia_h: 0.1, aplica: true },
  { etapa: 'ENSACADO', ton_por_hora: 5, tiempo_residencia_h: 0.1, aplica: true },
];

type AgendaSlot = {
  fecha: string;
  supplier: string;
  mmpp: string;
  ton_dia: number;
  camiones_dia: number;
};

type AgendaResponse = {
  total_ton_planificadas: number;
  total_camiones: number;
  advertencias: string[];
  bottleneck: { etapa: string; flujo_max_ton_h: number; camiones_max_dia: number; alerta: string } | null;
  slots: AgendaSlot[];
};

export default function AgendaPage() {
  const [ano, setAno] = useState(2027);
  const [data, setData] = useState<AgendaResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const suppliersPayload = useMemo(
    () =>
      suppliersActivos().map((s) => ({
        nombre: s.nombre,
        mmpp_codigo: s.mmppCodigo,
        volumen_anual_ton: s.volumenAnualComprometidoTon,
        capacidad_camion_ton: s.capacidadCamionTon,
      })),
    [],
  );

  async function planificar() {
    setLoading(true);
    setErr(null);
    setData(null);
    try {
      const t0 = performance.now();
      const r = await fetch(`${ENGINE_URL}/agenda`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          ano,
          capacidades: CAPACIDADES_HIPOTESIS,
          temporadas: TEMPORADAS_DEFAULT,
          suppliers: suppliersPayload,
          horas_operativas_dia: 24,
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
      const json = (await r.json()) as AgendaResponse;
      const elapsed = performance.now() - t0;
      console.log(`Agenda calculada en ${elapsed.toFixed(0)} ms`);
      setData(json);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  const slotsPorMes = useMemo(() => {
    if (!data) return {} as Record<string, AgendaSlot[]>;
    const acc: Record<string, AgendaSlot[]> = {};
    for (const s of data.slots) {
      const key = s.fecha.slice(0, 7);
      acc[key] = acc[key] || [];
      acc[key].push(s);
    }
    return acc;
  }, [data]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Agenda de camiones — Módulo 1</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Planificación de recepciones por día, respetando el cuello de botella del proceso. Las capacidades aquí son
          hipótesis hasta que <strong>Matías</strong> confirme valores reales.
        </p>
      </header>

      <section className="flex items-end gap-4">
        <label className="text-sm">
          Año a planificar
          <input
            type="number"
            value={ano}
            onChange={(e) => setAno(parseInt(e.target.value, 10))}
            className="ml-2 w-24 rounded border border-oliva/20 px-2 py-1"
          />
        </label>
        <button
          onClick={planificar}
          className="rounded bg-oliva-900 px-4 py-2 text-sm text-crema hover:bg-oliva-600 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? 'Calculando...' : 'Calcular agenda'}
        </button>
        {err && <span className="text-sm text-borgoña">{err}</span>}
      </section>

      {data && (
        <>
          <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-oliva/10 bg-white p-4">
              <div className="text-xs uppercase tracking-wide text-oliva-600">Total camiones {ano}</div>
              <div className="mt-1 text-2xl font-semibold text-oliva-900">
                {data.total_camiones.toLocaleString('es-CL')}
              </div>
            </div>
            <div className="rounded-lg border border-oliva/10 bg-white p-4">
              <div className="text-xs uppercase tracking-wide text-oliva-600">Toneladas planificadas</div>
              <div className="mt-1 text-2xl font-semibold text-oliva-900">
                {Math.round(data.total_ton_planificadas).toLocaleString('es-CL')}
              </div>
            </div>
            {data.bottleneck && (
              <>
                <div className="rounded-lg border border-oliva/10 bg-white p-4">
                  <div className="text-xs uppercase tracking-wide text-oliva-600">Etapa bottleneck</div>
                  <div className="mt-1 text-xl font-semibold text-borgoña">{data.bottleneck.etapa}</div>
                  <div className="text-xs text-oliva-600">
                    {data.bottleneck.flujo_max_ton_h.toFixed(2)} ton/h
                  </div>
                </div>
                <div className="rounded-lg border border-oliva/10 bg-white p-4">
                  <div className="text-xs uppercase tracking-wide text-oliva-600">Camiones máx/día</div>
                  <div className="mt-1 text-2xl font-semibold text-oliva-900">
                    {data.bottleneck.camiones_max_dia}
                  </div>
                  <div className="text-xs text-trigo">Alerta: {data.bottleneck.alerta}</div>
                </div>
              </>
            )}
          </section>

          {data.advertencias.length > 0 && (
            <section className="rounded-lg border border-borgoña/20 bg-borgoña/5 p-4">
              <h3 className="font-medium text-borgoña">Advertencias</h3>
              <ul className="mt-2 list-disc pl-6 text-sm text-oliva-700">
                {data.advertencias.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h2 className="font-serif text-xl text-oliva-900">Slots por mes</h2>
            <div className="mt-3 space-y-3">
              {Object.entries(slotsPorMes)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([mes, slots]) => {
                  const tonMes = slots.reduce((a, s) => a + s.ton_dia, 0);
                  const camionesMes = slots.reduce((a, s) => a + s.camiones_dia, 0);
                  return (
                    <details key={mes} className="rounded-lg border border-oliva/10 bg-white">
                      <summary className="cursor-pointer px-4 py-2 hover:bg-oliva-50">
                        <span className="font-medium text-oliva-900">{mes}</span>
                        <span className="ml-3 text-sm text-oliva-600">
                          {slots.length} slots · {camionesMes} camiones ·{' '}
                          {Math.round(tonMes).toLocaleString('es-CL')} ton
                        </span>
                      </summary>
                      <div className="overflow-x-auto px-4 pb-3">
                        <table className="w-full text-xs">
                          <thead className="text-oliva-600">
                            <tr>
                              <th className="py-1 text-left">Fecha</th>
                              <th className="py-1 text-left">Supplier</th>
                              <th className="py-1 text-left">MMPP</th>
                              <th className="py-1 text-right">Camiones</th>
                              <th className="py-1 text-right">Ton</th>
                            </tr>
                          </thead>
                          <tbody>
                            {slots.map((s, i) => (
                              <tr key={i} className="border-t border-oliva/5">
                                <td className="py-1">{s.fecha}</td>
                                <td className="py-1">{s.supplier}</td>
                                <td className="py-1">{s.mmpp}</td>
                                <td className="py-1 text-right">{s.camiones_dia}</td>
                                <td className="py-1 text-right">{s.ton_dia.toFixed(1)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </details>
                  );
                })}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
