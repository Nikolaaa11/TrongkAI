'use client';

/**
 * Provenance por numero — Ola 2 del SUPER_PROMPT_DOMINIO_TOTAL.
 *
 * Chip de nivel de dato (PD / PROVISORIO / VALIDADO) junto a un KPI critico.
 * El nivel se deriva EN VIVO de GET /parametros (nivel_dato de los drivers del
 * KPI); si el fetch falla usa el fallback documentado. Tooltip explica que
 * driver manda y como validarlo. Click -> /variables.
 */
import Link from 'next/link';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Nivel = 'PD' | 'OK_PROVISORIO' | 'OK_VALIDADO';

type KpiDef = {
  fallback: Nivel;
  drivers: string;                 // explicacion para el tooltip
  /** deriva el nivel desde el JSON de /parametros; null = usar fallback */
  derivar?: (p: Record<string, { nivel_dato?: Nivel }>) => Nivel | null;
};

const PEOR: Record<Nivel, number> = { OK_VALIDADO: 0, OK_PROVISORIO: 1, PD: 2 };
const peor = (...niveles: (Nivel | undefined)[]): Nivel => {
  const efectivos = niveles.filter(Boolean) as Nivel[];
  if (!efectivos.length) return 'PD';
  return efectivos.reduce((a, b) => (PEOR[b] > PEOR[a] ? b : a));
};

const KPIS: Record<string, KpiDef> = {
  // OPEX y costo/kg del piloto: manda el peor driver (arriendos PD ~52% del costo)
  costo_piloto: {
    fallback: 'PD',
    drivers:
      'Drivers: arriendo PEF+Tricanter (PD, cotización pendiente, ~52% del costo) · energía 270 CLP/kWh y sueldos (PROVISORIO, Excel equipo 03-jul-2026) · agua (PROVISORIO).',
    derivar: (p) => peor(p.arriendos?.nivel_dato, p.agua?.nivel_dato, 'OK_PROVISORIO'),
  },
  // TIR/VAN del plan industrial: precios SKU sin cotización firme
  tir_van: {
    fallback: 'PD',
    drivers:
      'Drivers: precio de venta por SKU (PD, sin cotización firme — driver #1) · CAPEX industrial (PD) · volumen MMPP (PROVISORIO).',
  },
  // Costos por procesos V3: canon Excel equipo con pendientes por validar
  costos_procesos: {
    fallback: 'OK_PROVISORIO',
    drivers:
      'Fuente: Excel equipo 03-jul-2026 (canon V3). Pendientes: alcantarillado 950, duración electrodos 200 vs 300 h, tarifa con/sin potencia.',
  },
};

const ESTILO: Record<Nivel, { txt: string; cls: string; titulo: string }> = {
  PD: {
    txt: 'PD · estimado',
    cls: 'border-amber-200 bg-amber-50 text-amber-700',
    titulo: 'Por Definir: estimación calibrada, falta el dato real.',
  },
  OK_PROVISORIO: {
    txt: 'PROVISORIO',
    cls: 'border-blue-200 bg-blue-50 text-blue-700',
    titulo: 'Dato del equipo con fuente trazable, pendiente validación final.',
  },
  OK_VALIDADO: {
    txt: 'VALIDADO',
    cls: 'border-green-200 bg-green-50 text-green-700',
    titulo: 'Dato validado con documento/contrato/medición real.',
  },
};

// Cache modulo-level: /parametros se pide una sola vez por sesion de pagina.
let parametrosCache: Promise<Record<string, { nivel_dato?: Nivel }> | null> | null = null;
function fetchParametros() {
  if (!parametrosCache) {
    parametrosCache = fetch(`${ENGINE_URL}/parametros`)
      .then((r) => r.json())
      .then((d) => d?.parametros ?? d ?? null)
      .catch(() => null);
  }
  return parametrosCache;
}

export default function NivelDato({ kpi }: { kpi: keyof typeof KPIS }) {
  const def = KPIS[kpi];
  const [nivel, setNivel] = useState<Nivel>(def?.fallback ?? 'PD');

  useEffect(() => {
    if (!def?.derivar) return;
    let vivo = true;
    fetchParametros().then((p) => {
      if (!vivo || !p) return;
      const n = def.derivar!(p);
      if (n) setNivel(n);
    });
    return () => { vivo = false; };
  }, [def]);

  if (!def) return null;
  const e = ESTILO[nivel];

  return (
    <Link
      href="/variables"
      title={`${e.titulo}\n${def.drivers}\nClick: matriz de variables para validar.`}
      className={`inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 align-middle text-[9px] font-semibold uppercase tracking-wide transition hover:opacity-75 print:hidden ${e.cls}`}
    >
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />
      {e.txt}
    </Link>
  );
}
