import Link from 'next/link';

export type LinkContextual = {
  href: string;
  label: string;
  razon: string; // por qué esta página se conecta con la otra (relación de datos real)
};

/**
 * Bloque "Conectado con" al pie de cada página: links contextuales basados en
 * el flujo REAL de datos (no decorativos). Patrón del super-prompt: quien ve
 * un número puede saltar a su desglose, sus supuestos y su banda de confianza.
 */
export function ConectadoCon({ links }: { links: LinkContextual[] }) {
  if (!links.length) return null;
  return (
    <section className="mt-12 border-t border-ink-100 pt-6">
      <h3 className="text-[12px] font-semibold uppercase tracking-[0.08em] text-ink-400">
        🔗 Conectado con
      </h3>
      <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {links.map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className="group rounded-xl border border-ink-100 bg-white px-4 py-3 transition hover:border-brand/30 hover:bg-brand-50/40"
          >
            <div className="flex items-center justify-between">
              <span className="text-[13px] font-semibold text-ink group-hover:text-brand">{l.label}</span>
              <span className="text-ink-200 transition-transform group-hover:translate-x-0.5 group-hover:text-brand">→</span>
            </div>
            <div className="mt-0.5 text-[11px] leading-snug text-ink-400">{l.razon}</div>
          </Link>
        ))}
      </div>
    </section>
  );
}
