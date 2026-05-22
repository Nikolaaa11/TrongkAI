'use client';

import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Hito = {
  nombre: string;
  fecha_vigor: string;
  fuente: string;
  severidad: 'CRITICA' | 'ALTA' | 'MEDIA' | 'INFORMATIVA';
  impacto_trongkai: string;
  accion_requerida: string;
  costo_estimado_clp: number | null;
};

type Calendar = {
  total_hitos: number;
  por_estado: { VIGENTE: Hito[]; CERCANA: Hito[]; FUTURA: Hito[]; LEJANA: Hito[] };
  proximos: Hito[];
  costo_compliance_5y_clp: { total_clp: number; detalle: { nombre: string; costo_clp: number }[] };
};

const SEV_COLOR: Record<string, string> = {
  CRITICA: 'border-borgoña bg-borgoña/5 text-borgoña',
  ALTA: 'border-borgoña/60 bg-borgoña/5 text-borgoña',
  MEDIA: 'border-trigo bg-trigo/5 text-oliva-900',
  INFORMATIVA: 'border-oliva/30 bg-oliva-50/30 text-oliva-700',
};

const ESTADO_LABEL: Record<string, string> = {
  VIGENTE: '✓ Vigente',
  CERCANA: '⚠ Cercana (< 12 meses)',
  FUTURA: '◔ Futura (1-3 años)',
  LEJANA: '◯ Lejana (> 3 años)',
};

const fmtFecha = (iso: string) =>
  new Date(iso).toLocaleDateString('es-CL', { year: 'numeric', month: 'long' });

const fmtCLP = (n: number) => `$${(n / 1e6).toFixed(0)}M CLP`;

export default function CompliancePage() {
  const [data, setData] = useState<Calendar | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void cargar();
  }, []);

  async function cargar() {
    try {
      const r = await fetch(`${ENGINE_URL}/compliance/rep-calendar`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setData(await r.json());
    } catch (e) {
      setErr(String(e));
    }
  }

  if (err) return <div className="p-8 text-borgoña">Error: {err}</div>;
  if (!data) return <div className="p-8 text-oliva-600">Cargando compliance...</div>;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-serif text-3xl text-oliva-900">Compliance & Regulación</h1>
        <p className="mt-2 text-sm text-oliva-600">
          Calendario de obligaciones Ley REP Chile + Hoja de Ruta Circular 2040 + estándares export.
          {' '}Cada hito tiene fuente trazable, costo estimado y acción requerida.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Card label="Hitos totales" value={data.total_hitos.toString()} />
        <Card label="Vigentes" value={data.por_estado.VIGENTE.length.toString()} tone="ok" />
        <Card label="Cercanas (<12m)" value={data.por_estado.CERCANA.length.toString()} tone="warn" />
        <Card
          label="Costo compliance 5y"
          value={fmtCLP(data.costo_compliance_5y_clp.total_clp)}
          tone="info"
        />
      </section>

      {data.proximos.length > 0 && (
        <section className="rounded-lg border border-borgoña/30 bg-borgoña/5 p-4">
          <h2 className="font-medium text-borgoña">⚠ Próximos hitos</h2>
          <p className="mt-1 text-xs text-oliva-600">Los siguientes 5 cambios regulatorios:</p>
          <div className="mt-3 space-y-2">
            {data.proximos.slice(0, 5).map((h, i) => (
              <div key={i} className="flex items-start justify-between rounded bg-white p-3">
                <div className="flex-1">
                  <div className="font-medium text-oliva-900">{h.nombre}</div>
                  <div className="text-xs text-oliva-600">{h.impacto_trongkai}</div>
                </div>
                <div className="ml-3 text-right">
                  <div className="text-xs text-oliva-500">{fmtFecha(h.fecha_vigor)}</div>
                  <div className={`text-xs font-medium ${h.severidad === 'CRITICA' || h.severidad === 'ALTA' ? 'text-borgoña' : 'text-oliva-700'}`}>
                    {h.severidad}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="space-y-4">
        {(['VIGENTE', 'CERCANA', 'FUTURA', 'LEJANA'] as const).map((estado) => {
          const hitos = data.por_estado[estado];
          if (hitos.length === 0) return null;
          return (
            <div key={estado}>
              <h2 className="font-serif text-xl text-oliva-900">
                {ESTADO_LABEL[estado]} <span className="text-sm text-oliva-500">({hitos.length})</span>
              </h2>
              <div className="mt-3 space-y-3">
                {hitos.map((h, i) => (
                  <article
                    key={i}
                    className={`card-hover rounded-lg border-l-4 bg-white p-4 ${SEV_COLOR[h.severidad]}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-oliva-900">{h.nombre}</h3>
                        <p className="mt-1 text-sm text-oliva-700">{h.impacto_trongkai}</p>
                        <p className="mt-2 text-xs text-oliva-600">
                          <strong>Acción:</strong> {h.accion_requerida}
                        </p>
                        <a
                          href={h.fuente}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-1 inline-block text-xs text-trigo hover:underline"
                        >
                          {h.fuente.length > 70 ? h.fuente.substring(0, 70) + '…' : h.fuente}
                        </a>
                      </div>
                      <div className="ml-4 text-right">
                        <div className="text-xs uppercase tracking-wide text-oliva-500">Vigor</div>
                        <div className="font-semibold tabular text-oliva-900">{fmtFecha(h.fecha_vigor)}</div>
                        <div className="mt-1 text-[10px] uppercase font-bold">{h.severidad}</div>
                        {h.costo_estimado_clp && (
                          <div className="mt-1 text-xs text-trigo tabular">{fmtCLP(h.costo_estimado_clp)}</div>
                        )}
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          );
        })}
      </section>

      {data.costo_compliance_5y_clp.detalle.length > 0 && (
        <section className="rounded-lg border border-oliva/10 bg-white p-4">
          <h2 className="font-medium text-oliva-900">Costo compliance estimado próximos 5 años</h2>
          <table className="mt-3 w-full text-sm">
            <thead className="text-xs uppercase tracking-wide text-oliva-600">
              <tr>
                <th className="text-left">Item</th>
                <th className="text-right">Costo CLP</th>
              </tr>
            </thead>
            <tbody>
              {data.costo_compliance_5y_clp.detalle.map((d, i) => (
                <tr key={i} className="border-t border-oliva/5">
                  <td className="py-2">{d.nombre}</td>
                  <td className="py-2 text-right tabular">{fmtCLP(d.costo_clp)}</td>
                </tr>
              ))}
              <tr className="border-t-2 border-oliva/20 bg-oliva-50/50">
                <td className="py-2 font-semibold">TOTAL 5y</td>
                <td className="py-2 text-right font-semibold tabular">
                  {fmtCLP(data.costo_compliance_5y_clp.total_clp)}
                </td>
              </tr>
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}

function Card({ label, value, tone }: { label: string; value: string; tone?: 'ok' | 'warn' | 'info' }) {
  const border =
    tone === 'ok' ? 'border-oliva-700/40' : tone === 'warn' ? 'border-borgoña/40 bg-borgoña/5' : 'border-trigo/40 bg-trigo/5';
  return (
    <div className={`card-hover rounded-lg border bg-white p-4 ${tone ? border : 'border-oliva/10'}`}>
      <div className="text-[10px] uppercase tracking-[0.08em] text-oliva-600">{label}</div>
      <div className="tabular mt-1 text-2xl font-bold text-oliva-900">{value}</div>
    </div>
  );
}
