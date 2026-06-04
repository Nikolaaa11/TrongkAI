'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Params = {
  sueldos: { cargo: string; sueldo_bruto_clp: number; costo_total_clp: number; costo_hora_clp: number; factor_leyes_sociales: number }[];
  energia: any;
  calor_residual: any;
  agua: any;
  flete: any;
  arriendos: any;
  perdida_mmpp_global_pct: number;
  usd_clp_referencia: number;
  fecha_actualizacion: string;
  checklist_pendientes: string[];
};

type Humedad = {
  codigo: string;
  nombre_legible: string;
  humedad_min_pct: number;
  humedad_max_pct: number;
  humedad_promedio_pct: number;
  variabilidad_pct: number;
  notas: string;
};

export default function ParametrosPage() {
  const [data, setData] = useState<Params | null>(null);
  const [humedades, setHumedades] = useState<Humedad[]>([]);
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<any>({});

  const load = () => {
    fetch(`${ENGINE_URL}/parametros`).then((r) => r.json()).then(setData);
    fetch(`${ENGINE_URL}/parametros/humedades-mmpp`).then((r) => r.json()).then((d) => setHumedades(d.humedades || []));
  };

  useEffect(() => { load(); }, []);

  if (!data) return <p className="text-ink-400">Cargando parámetros…</p>;

  const updateField = (group: string, key: string, value: any) => {
    setDraft((p: any) => ({
      ...p,
      [group]: { ...(p[group] || {}), [key]: value },
    }));
  };

  const saveDraft = async () => {
    if (Object.keys(draft).length === 0) return;
    setSaving(true);
    try {
      await fetch(`${ENGINE_URL}/parametros/actualizar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(draft),
      });
      setDraft({});
      load();
    } finally {
      setSaving(false);
    }
  };

  const Field = ({ group, k, label, value, suffix, step = 1 }: any) => (
    <div className="flex items-center justify-between gap-3 py-1.5">
      <label className="text-sm text-ink-600 flex-1">{label}</label>
      <div className="flex items-center gap-2">
        <input
          type="number"
          step={step}
          defaultValue={value}
          onChange={(e) => updateField(group, k, +e.target.value)}
          className="w-32 rounded border border-ink-200 px-2 py-1 text-sm text-right font-mono"
        />
        <span className="text-xs text-ink-400 w-12">{suffix}</span>
      </div>
    </div>
  );

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Planilla de antecedentes variables</p>
        <h1 className="mt-2 text-4xl font-bold">⚙️ Parámetros de planta</h1>
        <p className="mt-2 text-ink-500">
          Editar acá afecta TODOS los cálculos de costeo. Actualizado: {data.fecha_actualizacion}.
        </p>
      </header>

      {/* Checklist pendientes */}
      {data.checklist_pendientes.length > 0 && (
        <section className="rounded-2xl border-l-4 border-orange-500 bg-orange-50 p-5">
          <h3 className="font-bold text-orange-700">📋 Pendientes para validar</h3>
          <ul className="mt-2 space-y-1 text-sm text-orange-700">
            {data.checklist_pendientes.map((p, i) => <li key={i}>• {p}</li>)}
          </ul>
        </section>
      )}

      {/* Save bar */}
      {Object.keys(draft).length > 0 && (
        <div className="sticky top-20 z-30 rounded-2xl border-2 border-brand bg-white p-4 shadow-lg">
          <div className="flex items-center justify-between gap-4">
            <p className="text-sm">
              <strong>{Object.keys(draft).length}</strong> grupos modificados sin guardar
            </p>
            <div className="flex gap-2">
              <button onClick={() => setDraft({})} className="rounded-full bg-ink-100 px-4 py-2 text-sm font-semibold">
                Descartar
              </button>
              <button onClick={saveDraft} disabled={saving} className="rounded-full bg-brand px-4 py-2 text-sm font-semibold text-white">
                {saving ? 'Guardando…' : '💾 Guardar cambios'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sueldos */}
      <Card title="👥 Sueldos de planta" subtitle={`Factor leyes sociales ${(data.sueldos[0]?.factor_leyes_sociales || 1.35).toFixed(2)} (gratificación, AFP, salud, seguros)`}>
        <table className="w-full text-sm">
          <thead className="text-xs text-ink-500 uppercase">
            <tr><th className="text-left py-2">Cargo</th><th className="text-right">Bruto CLP/mes</th><th className="text-right">Costo total CLP/mes</th><th className="text-right">CLP/hora</th></tr>
          </thead>
          <tbody>
            {data.sueldos.map((s, i) => (
              <tr key={i} className="border-t border-ink-100">
                <td className="py-2 font-medium">{s.cargo}</td>
                <td className="py-2 text-right tabular">${s.sueldo_bruto_clp.toLocaleString()}</td>
                <td className="py-2 text-right tabular text-brand">${s.costo_total_clp.toLocaleString()}</td>
                <td className="py-2 text-right tabular">${s.costo_hora_clp.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Energía */}
      <Card title="⚡ Energía eléctrica" subtitle={data.energia.notas}>
        <Field group="energia" k="tarifa_energia_punta_clp_kwh" label="Tarifa hora PUNTA (18-23h invierno)" value={data.energia.tarifa_energia_punta_clp_kwh} suffix="CLP/kWh" />
        <Field group="energia" k="tarifa_energia_resto_clp_kwh" label="Tarifa hora RESTO" value={data.energia.tarifa_energia_resto_clp_kwh} suffix="CLP/kWh" />
        <Field group="energia" k="cargo_potencia_clp_kw_mes" label="Cargo potencia" value={data.energia.cargo_potencia_clp_kw_mes} suffix="CLP/kW·mes" />
        <Field group="energia" k="cargo_fijo_clp_mes" label="Cargo fijo" value={data.energia.cargo_fijo_clp_mes} suffix="CLP/mes" />
        <Field group="energia" k="pct_horas_punta" label="% horas punta" value={data.energia.pct_horas_punta} suffix="" step={0.01} />
        <p className="mt-3 text-xs text-ink-500">
          → Tarifa promedio ponderada: <strong>{data.energia.tarifa_promedio_clp_kwh} CLP/kWh</strong> ({data.energia.tarifa_promedio_usd_kwh} USD/kWh)
        </p>
      </Card>

      {/* Calor residual */}
      <Card title="🔥 Calor residual La Gloria" subtitle={data.calor_residual.notas}>
        <Field group="calor_residual" k="costo_kwh_termico_clp" label="Costo por kWh térmico" value={data.calor_residual.costo_kwh_termico_clp} suffix="CLP/kWh" />
        <Field group="calor_residual" k="capacidad_kwh_termico_mes" label="Capacidad mensual disponible" value={data.calor_residual.capacidad_kwh_termico_mes} suffix="kWh/mes" />
        <Field group="calor_residual" k="costo_servicio_clp_mes" label="Costo fijo servicio (si hay)" value={data.calor_residual.costo_servicio_clp_mes} suffix="CLP/mes" />
        <p className="mt-3 text-xs text-ink-500">
          Equivalente: <strong>{data.calor_residual.costo_kwh_usd} USD/kWh</strong> · Nivel: {data.calor_residual.nivel_dato}
        </p>
      </Card>

      {/* Agua */}
      <Card title="💧 Agua llave + industrial" subtitle={data.agua.notas}>
        <Field group="agua" k="agua_llave_clp_m3" label="Agua llave (Essbio)" value={data.agua.agua_llave_clp_m3} suffix="CLP/m³" />
        <Field group="agua" k="alcantarillado_clp_m3" label="Alcantarillado" value={data.agua.alcantarillado_clp_m3} suffix="CLP/m³" />
        <Field group="agua" k="agua_industrial_clp_m3" label="Agua industrial (pozo)" value={data.agua.agua_industrial_clp_m3} suffix="CLP/m³" />
        <Field group="agua" k="agua_recirculada_clp_m3" label="Agua recirculada" value={data.agua.agua_recirculada_clp_m3} suffix="CLP/m³" />
        <Field group="agua" k="derecho_dga_l_s" label="Derecho DGA Pozo 1" value={data.agua.derecho_dga_l_s} suffix="L/s" step={0.1} />
      </Card>

      {/* Flete */}
      <Card title="🚚 Flete / traslados" subtitle={data.flete.notas}>
        <Field group="flete" k="flete_clp_km" label="Tarifa por km" value={data.flete.flete_clp_km} suffix="CLP/km" />
        <Field group="flete" k="flete_minimo_clp_viaje" label="Flete mínimo por viaje" value={data.flete.flete_minimo_clp_viaje} suffix="CLP" />
        <Field group="flete" k="distancia_promedio_mmpp_km" label="Distancia MMPP entrada" value={data.flete.distancia_promedio_mmpp_km} suffix="km" />
        <Field group="flete" k="distancia_promedio_despacho_km" label="Distancia despacho" value={data.flete.distancia_promedio_despacho_km} suffix="km" />
        <p className="mt-3 text-xs text-ink-500">
          → MMPP: <strong>${data.flete.costo_promedio_mmpp_clp_ton.toLocaleString()} CLP/ton</strong> ·
          Despacho: <strong>${data.flete.costo_promedio_despacho_clp_ton.toLocaleString()} CLP/ton</strong>
        </p>
      </Card>

      {/* Arriendos */}
      <Card title="🏗 Arriendos equipos (OPEX)" subtitle={data.arriendos.notas}>
        <Field group="arriendos" k="arriendo_pef_clp_mes" label="PEF Opticept" value={data.arriendos.arriendo_pef_clp_mes} suffix="CLP/mes" />
        <Field group="arriendos" k="arriendo_tricanter_clp_mes" label="Tricanter" value={data.arriendos.arriendo_tricanter_clp_mes} suffix="CLP/mes" />
        <Field group="arriendos" k="arriendo_otros_clp_mes" label="Otros equipos" value={data.arriendos.arriendo_otros_clp_mes} suffix="CLP/mes" />
        <p className="mt-3 text-xs text-ink-500">
          → Total arriendo mensual: <strong>${data.arriendos.arriendo_total_clp_mes.toLocaleString()} CLP</strong>
          ({data.arriendos.arriendo_total_usd_mes} USD)
        </p>
      </Card>

      {/* Humedades MMPP */}
      <Card title="💧 Humedades de ingreso por MMPP" subtitle="Variabilidad por condiciones climáticas">
        <table className="w-full text-sm">
          <thead className="text-xs text-ink-500 uppercase">
            <tr><th className="text-left py-2">MMPP</th><th className="text-right">Mín</th><th className="text-right">Promedio</th><th className="text-right">Máx</th><th className="text-left pl-3">Notas</th></tr>
          </thead>
          <tbody>
            {humedades.map((h) => (
              <tr key={h.codigo} className="border-t border-ink-100">
                <td className="py-2 font-medium">{h.nombre_legible}</td>
                <td className="py-2 text-right tabular">{(h.humedad_min_pct * 100).toFixed(0)}%</td>
                <td className="py-2 text-right tabular text-brand font-semibold">{(h.humedad_promedio_pct * 100).toFixed(0)}%</td>
                <td className="py-2 text-right tabular">{(h.humedad_max_pct * 100).toFixed(0)}%</td>
                <td className="py-2 pl-3 text-xs text-ink-500">{h.notas}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Globales */}
      <Card title="🌍 Globales">
        <Field group="" k="perdida_mmpp_global_pct" label="Pérdida MMPP global (5%)" value={data.perdida_mmpp_global_pct} suffix="" step={0.01} />
        <Field group="" k="usd_clp_referencia" label="USD/CLP referencia" value={data.usd_clp_referencia} suffix="CLP" />
      </Card>
    </div>
  );
}

function Card({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-ink-100 bg-white p-6">
      <h2 className="text-xl font-bold">{title}</h2>
      {subtitle && <p className="mt-1 text-xs text-ink-500">{subtitle}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}
