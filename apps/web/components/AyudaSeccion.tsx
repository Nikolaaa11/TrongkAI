'use client';

/**
 * Ayuda contextual global — "dominio total" dentro de cada pantalla.
 *
 * Boton flotante "?" presente en toda pagina documentada en lib/guia-data.ts.
 * Abre un panel lateral con: que es, para que sirve, funciones, como usarla,
 * parametros que influyen (y donde se trabajan), de donde salen los datos y
 * como reemplazarlos. Misma fuente de verdad que /guia — cero divergencia.
 */
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { GUIA, SCREENSHOTS, type Seccion } from '@/lib/guia-data';

export default function AyudaSeccion() {
  const pathname = usePathname();
  const [abierto, setAbierto] = useState(false);

  const hit = useMemo(() => {
    for (const g of GUIA) {
      const s = g.secciones.find((x) => x.href === pathname);
      if (s) return { grupo: g, seccion: s as Seccion };
    }
    return null;
  }, [pathname]);

  // Cerrar al navegar y con ESC
  useEffect(() => setAbierto(false), [pathname]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setAbierto(false);
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  if (!hit) return null;
  const { grupo, seccion: s } = hit;

  return (
    <>
      {/* Boton flotante */}
      <button
        onClick={() => setAbierto(true)}
        title={`¿Cómo funciona ${s.titulo}?`}
        aria-label="Ayuda de esta pantalla"
        className="fixed bottom-5 right-5 z-50 flex h-11 w-11 items-center justify-center rounded-full bg-ink text-[17px] font-semibold text-white shadow-xl transition hover:scale-105 hover:bg-ink-700 print:hidden"
      >
        ?
      </button>

      {abierto && (
        <div className="print:hidden">
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-[59] bg-ink/25 backdrop-blur-[2px]"
            onClick={() => setAbierto(false)}
          />
          {/* Panel */}
          <aside className="fixed right-0 top-0 z-[60] flex h-full w-[440px] max-w-[94vw] flex-col overflow-y-auto bg-white shadow-2xl">
            <div className="sticky top-0 z-10 border-b border-ink-100 bg-white/95 px-6 py-4 backdrop-blur">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-400">
                    {grupo.emoji} {grupo.persona} · Cómo funciona
                  </p>
                  <h2 className="mt-1 text-xl font-bold text-ink">
                    {s.icono} {s.titulo}
                  </h2>
                </div>
                <button
                  onClick={() => setAbierto(false)}
                  aria-label="Cerrar"
                  className="rounded-full p-2 text-ink-400 transition hover:bg-ink-50 hover:text-ink"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M1 1L13 13M13 1L1 13" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="space-y-6 px-6 py-5 text-[13px] leading-relaxed text-ink-600">
              <div>
                <p><strong className="text-ink">{s.queEs}</strong></p>
                <p className="mt-1.5 text-ink-500">{s.paraQue}</p>
              </div>

              {SCREENSHOTS.has(s.href) && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={`/guia${s.href}.png`}
                  alt={`Captura de ${s.titulo}`}
                  className="w-full rounded-xl border border-ink-100"
                  loading="lazy"
                />
              )}

              {s.funciones.length > 0 && (
                <section>
                  <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-400">Funciones</h3>
                  <ul className="space-y-1.5">
                    {s.funciones.map((f) => (
                      <li key={f} className="flex gap-2">
                        <span className="text-brand">•</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {s.pasos.length > 0 && (
                <section>
                  <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-400">Cómo usarla</h3>
                  <ol className="space-y-1.5">
                    {s.pasos.map((p, i) => (
                      <li key={p} className="flex gap-2">
                        <span className="font-semibold tabular-nums text-ink-400">{i + 1}.</span>
                        <span>{p}</span>
                      </li>
                    ))}
                  </ol>
                </section>
              )}

              {s.parametros.length > 0 && (
                <section>
                  <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-400">
                    Parámetros que influyen
                  </h3>
                  <div className="space-y-2.5">
                    {s.parametros.map((p) => (
                      <div key={p.nombre} className="rounded-xl border border-ink-100 p-3">
                        <p className="font-semibold text-ink">{p.nombre}</p>
                        <p className="mt-0.5 text-[12px] text-ink-500">
                          <span className="font-medium text-ink-600">Se trabaja en:</span> {p.donde}
                        </p>
                        <p className="text-[12px] text-ink-500">
                          <span className="font-medium text-ink-600">Efecto:</span> {p.efecto}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              <section className="rounded-xl bg-ink-50/70 p-4">
                <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-500">
                  📡 De dónde salen los datos
                </h3>
                <p><span className="font-medium text-ink">Fuente:</span> {s.fuente}</p>
                <p className="mt-1.5"><span className="font-medium text-ink">Reemplazar:</span> {s.reemplazar}</p>
              </section>
            </div>

            <div className="sticky bottom-0 mt-auto border-t border-ink-100 bg-white/95 px-6 py-3 backdrop-blur">
              <div className="flex items-center justify-between text-[12px]">
                <Link href="/guia" className="font-medium text-brand hover:underline">
                  📖 Ver guía completa →
                </Link>
                <span className="text-ink-300">ESC para cerrar · ⌘K buscar</span>
              </div>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
