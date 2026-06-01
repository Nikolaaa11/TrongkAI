'use client';

import Image from 'next/image';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Tecnologia = {
  id: string;
  nombre: string;
  proveedor: string;
  funcion: string;
  etapa_proceso: string;
  trl: number;
  capex_usd: number;
  opex_kwh_ton: number | null;
  impacto_rendimiento_pct: number | null;
  impacto_calidad_pct: number | null;
  estado_validacion: string;
  descripcion: string;
  referencias_dossier: string[];
  pros: string[];
  contras: string[];
};

type Resp = {
  tecnologias: Tecnologia[];
  resumen: {
    total_tecnologias: number;
    capex_stack_usd: number;
    trl_promedio: number;
    por_estado_validacion: Record<string, number>;
    por_etapa_proceso: Record<string, number>;
  };
};

const ETAPA_ICON: Record<string, string> = {
  recepcion: '📦',
  pretratamiento: '🧹',
  permeabilizacion: '⚡',
  secado: '☀️',
  molienda: '⚙️',
  extraccion: '🧪',
  concentracion: '💧',
  envasado: '📥',
};

const ESTADO_COLOR: Record<string, string> = {
  idea: 'bg-ink-50 text-ink-600',
  lab: 'bg-yellow-50 text-yellow-700',
  piloto: 'bg-orange-50 text-orange-600',
  industrial: 'bg-brand-50 text-brand',
  produccion: 'bg-brand-100 text-brand-700',
};

export default function TecnologiasPage() {
  const [data, setData] = useState<Resp | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/tecnologias`).then(r => r.ok && r.json()).then(setData);
  }, []);

  if (!data) return <div className="apple-card text-ink-400">Cargando catálogo...</div>;

  return (
    <div className="space-y-8">
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">⚙️ Stack Tecnológico</h1>
          <p className="mt-2 text-sm text-ink-400">
            Tecnologías clave de la planta Trongkai identificadas en el dossier P1.
            PEF, infrasonido, micro-molienda — cada una con su TRL, CapEx, impacto y validación.
          </p>
        </div>
      </header>

      {/* Hero stats */}
      <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
        <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Tecnologías</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">{data.resumen.total_tecnologias}</div>
            <div className="text-xs text-ink-600">en el stack</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">CapEx stack</div>
            <div className="tabular mt-2 text-4xl font-semibold text-brand">
              ${(data.resumen.capex_stack_usd / 1e6).toFixed(2)}M
            </div>
            <div className="text-xs text-ink-600">USD inversión total</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">TRL promedio</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">{data.resumen.trl_promedio}<span className="text-2xl text-ink-400">/9</span></div>
            <div className="text-xs text-ink-600">Technology Readiness Level</div>
          </div>
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">Etapas cubiertas</div>
            <div className="tabular mt-2 text-4xl font-semibold text-ink">{Object.keys(data.resumen.por_etapa_proceso).length}</div>
            <div className="text-xs text-ink-600">del proceso productivo</div>
          </div>
        </div>
      </section>

      {/* Cards tecnologías */}
      <section className="space-y-4">
        {data.tecnologias.map((t) => (
          <TecCard key={t.id} t={t} />
        ))}
      </section>
    </div>
  );
}

function TecCard({ t }: { t: Tecnologia }) {
  return (
    <div className="apple-card">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="text-3xl">{ETAPA_ICON[t.etapa_proceso] ?? '⚙️'}</span>
          <div>
            <h3 className="text-xl font-semibold tracking-apple text-ink">{t.nombre}</h3>
            <div className="mt-0.5 text-xs text-ink-400">Proveedor: <strong className="text-ink-600">{t.proveedor}</strong></div>
            <div className="mt-0.5 text-xs text-ink-400">Etapa: <strong className="text-ink-600">{t.etapa_proceso}</strong></div>
          </div>
        </div>
        <div className="flex gap-2">
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${ESTADO_COLOR[t.estado_validacion] ?? 'bg-ink-50 text-ink-600'}`}>
            {t.estado_validacion}
          </span>
          <span className="rounded-full bg-ink px-2 py-0.5 text-[10px] font-semibold text-white">
            TRL {t.trl}/9
          </span>
        </div>
      </div>

      <p className="mt-3 text-sm text-ink-600 leading-relaxed">{t.descripcion}</p>

      {/* KPIs */}
      <div className="mt-4 grid grid-cols-2 gap-3 border-y border-ink-100 py-3 md:grid-cols-4">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-ink-400">CapEx</div>
          <div className="tabular text-base font-semibold text-ink">${(t.capex_usd / 1000).toLocaleString('es-CL')}k</div>
        </div>
        {t.opex_kwh_ton !== null && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-ink-400">Energía</div>
            <div className="tabular text-base font-semibold text-ink">{t.opex_kwh_ton} kWh/ton</div>
          </div>
        )}
        {t.impacto_rendimiento_pct !== null && t.impacto_rendimiento_pct > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-ink-400">↑ Rendimiento</div>
            <div className="tabular text-base font-semibold text-brand">+{t.impacto_rendimiento_pct}%</div>
          </div>
        )}
        {t.impacto_calidad_pct !== null && t.impacto_calidad_pct > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-ink-400">↑ Calidad</div>
            <div className="tabular text-base font-semibold text-brand">+{t.impacto_calidad_pct}%</div>
          </div>
        )}
      </div>

      {/* Pros / Contras */}
      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-brand">✓ Pros</div>
          <ul className="mt-1 space-y-1">
            {t.pros.map((p, i) => (
              <li key={i} className="text-xs text-ink-600">• {p}</li>
            ))}
          </ul>
        </div>
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-orange-600">⚠ Contras</div>
          <ul className="mt-1 space-y-1">
            {t.contras.map((c, i) => (
              <li key={i} className="text-xs text-ink-600">• {c}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Referencias */}
      {t.referencias_dossier.length > 0 && (
        <div className="mt-3 border-t border-ink-100 pt-2">
          <div className="text-[10px] uppercase tracking-wider text-ink-400 mb-1">Dossier técnico</div>
          <div className="flex flex-wrap gap-1">
            {t.referencias_dossier.slice(0, 3).map((ref, i) => (
              <code key={i} className="rounded bg-ink-50 px-1.5 py-0.5 text-[10px] text-ink-600">{ref}</code>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
