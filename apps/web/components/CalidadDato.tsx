'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'https://trongkai-engine.fly.dev';

type Precision = {
  exactitud_global_pct: number;
  nivel_confianza: string;
  top_para_validar?: { nombre: string }[];
};

/**
 * Badge de calidad del dato (principio 3 del super-prompt: "el dato sabe su
 * calidad"). Junto a los KPIs clave del piloto muestra la exactitud global
 * del modelo y el primer input a validar — nunca falsa precision.
 */
export function CalidadDato() {
  const [p, setP] = useState<Precision | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/inteligencia/precision`)
      .then((r) => r.json())
      .then(setP)
      .catch(() => {});
  }, []);

  if (!p) return null;

  const pct = p.exactitud_global_pct;
  const tone = pct >= 85 ? 'text-brand bg-brand-50 ring-brand/20'
    : pct >= 60 ? 'text-amber-700 bg-amber-50 ring-amber-200'
    : 'text-orange-700 bg-orange-50 ring-orange-200';
  const siguiente = p.top_para_validar?.[0]?.nombre;

  return (
    <Link
      href="/inteligencia"
      className={`inline-flex flex-wrap items-center gap-2 rounded-full px-3.5 py-1.5 text-[12px] font-medium ring-1 transition hover:opacity-80 ${tone}`}
      title="Exactitud ponderada de los inputs del modelo (PD / PROVISORIO / VALIDADO). Click para ver bandas de confianza y qué validar."
    >
      <span aria-hidden>◍</span>
      <span>Exactitud del modelo: {pct.toFixed(0)}%</span>
      {siguiente && <span className="opacity-70">· siguiente a validar: {siguiente}</span>}
      <span aria-hidden>→</span>
    </Link>
  );
}
