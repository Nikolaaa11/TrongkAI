'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

type Item = { href: string; label: string; desc?: string };
type Group = { id: string; label: string; emoji?: string; items: Item[] };

/**
 * Menu organizado por PERSONA DE USUARIO (no por capas tecnicas):
 * Directorio (board) / Operacion (planta) / Inversionista (LP) / Analisis (financiero)
 * + Sistema (admin tecnico).
 * Las paginas que salieron del menu siguen vivas via Cmd+K y cross-links:
 * /dashboard-directorio (board pack imprimible, link desde /comando),
 * /balance /balance-energia /balance-agua (links desde /balance-integral),
 * /productos-etapas /pef-analisis (links desde balances), /coherencia (link
 * desde /decisiones), /investigacion /clientes-reales /commercial /nutrientes
 * /tecnologias (links desde /lp-pack y Cmd+K).
 */
const GROUPS: Group[] = [
  {
    id: 'directorio',
    label: 'Directorio',
    emoji: '🎯',
    items: [
      { href: '/comando', label: 'Centro de Mando', desc: 'Cockpit ejecutivo en tiempo real' },
      { href: '/inteligencia', label: '🧠 Inteligencia', desc: 'Síntesis cross-modular + plan acción' },
      { href: '/plan', label: 'Plan 5 años', desc: 'EERR mensual + TIR/VAN + tornado' },
      { href: '/comparador', label: 'Escenarios', desc: 'CONSERVADOR vs INDUSTRIAL vs EXPANSION' },
      { href: '/riesgo', label: 'Riesgo Integrado', desc: 'Monte Carlo + clima + regulatorio' },
      { href: '/decisiones', label: 'Decision Engine', desc: 'Top 5 acciones priorizadas' },
      { href: '/roadmap', label: 'Roadmap', desc: 'Timeline de hitos' },
    ],
  },
  {
    id: 'operacion',
    label: 'Operación',
    emoji: '🏭',
    items: [
      { href: '/planta', label: 'Planta (visual)', desc: 'Layout con fotos reales de equipos' },
      { href: '/simulacion', label: '⏱ Simulación', desc: 'Producción + OPEX completo por periodo' },
      { href: '/balance-integral', label: '⚖️ Balances', desc: 'Producto, energía, agua, RRHH en uno' },
      { href: '/balance-etapas', label: 'Por Etapas', desc: '11 etapas reales Agrosphere · dinámico' },
      { href: '/costeo', label: '💰 Costeo', desc: 'Costo por etapa y SKU (CLP/kg, USD/kg)' },
      { href: '/parametros', label: '⚙️ Parámetros', desc: 'Sueldos, energía, agua, flete editables' },
      { href: '/equipos', label: 'Equipos', desc: 'Fichas técnicas editables' },
    ],
  },
  {
    id: 'inversionista',
    label: 'Inversionista',
    emoji: '💼',
    items: [
      { href: '/readiness', label: 'Readiness Score', desc: 'Madurez del proyecto 0-100' },
      { href: '/data-room', label: 'Data Room', desc: 'Checklist DD para LPs' },
      { href: '/lp-pack', label: 'LP Pack', desc: 'Tearsheet + entregables descargables' },
      { href: '/pipeline-lp', label: 'Pipeline LP', desc: 'CRM de inversionistas en roadshow' },
      { href: '/carbono', label: 'Carbono / ESG', desc: 'LCA + créditos CO₂' },
      { href: '/compliance', label: 'Compliance', desc: 'Ley REP + normativa' },
      { href: '/equipo', label: 'Equipo', desc: 'Directorio + advisors' },
    ],
  },
  {
    id: 'analisis',
    label: 'Análisis',
    emoji: '📈',
    items: [
      { href: '/whatif-live', label: 'What-if Live', desc: 'Sliders en vivo → TIR/VAN' },
      { href: '/sensitivity', label: 'Sensibilidad', desc: 'Heatmap + breakeven + curvas' },
      { href: '/stress', label: 'Stress Test', desc: 'Triple negativo' },
      { href: '/escalas', label: 'Escalas', desc: 'Piloto vs industrial (x10, x50, x100)' },
      { href: '/financiamiento', label: 'Financiamiento', desc: 'Deuda/equity + DSCR' },
      { href: '/slb', label: 'SLB Calculator', desc: 'Sustainability-Linked Bonds' },
      { href: '/macro', label: 'Macro Chile', desc: 'USD/CLP, UF, TPM en vivo' },
    ],
  },
  {
    id: 'sistema',
    label: 'Sistema',
    emoji: '🔧',
    items: [
      { href: '/variables', label: 'Matriz Variables', desc: 'PD / OK_PROVISORIO / OK_VALIDADO' },
      { href: '/inbox', label: 'Inbox', desc: 'Archivos nuevos del equipo' },
      { href: '/audit', label: 'Audit Trail', desc: 'Historial de cambios al modelo' },
      { href: '/salud', label: 'Salud del Sistema', desc: 'Health check técnico' },
      { href: '/mapa', label: '🗺 Mapa Plataforma', desc: 'Todas las páginas y su flujo' },
    ],
  },
];

export default function NavMenu() {
  const pathname = usePathname();
  const [openGroup, setOpenGroup] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navRef = useRef<HTMLDivElement>(null);

  // Cerrar dropdown al click fuera
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setOpenGroup(null);
      }
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  // Cerrar dropdown al cambiar de ruta
  useEffect(() => {
    setOpenGroup(null);
    setMobileOpen(false);
  }, [pathname]);

  const isActive = (href: string) => pathname === href;
  const groupActive = (g: Group) => g.items.some((i) => isActive(i.href));

  return (
    <header className="sticky top-0 z-50 border-b border-ink-100 bg-white/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-3" ref={navRef}>
        {/* ===== Logo ===== */}
        <div className="flex shrink-0 items-center gap-3">
          <Link href="/" className="flex items-center gap-2">
            <Image
              src="/logo-trongkai-color.png"
              alt="Trongkai"
              width={140}
              height={32}
              priority
              className="h-7 w-auto"
            />
          </Link>
          <span
            className="hidden md:inline-flex items-center gap-1 rounded-full border border-ink-100 bg-ink-50/50 px-2.5 py-1 text-[11px] font-medium text-ink-400 cursor-help"
            title="Cmd+K (Mac) o Ctrl+K (Windows)"
          >
            <kbd className="text-[10px] font-semibold text-ink-600">⌘K</kbd>
            <span>Buscar</span>
          </span>
        </div>

        {/* ===== Desktop nav ===== */}
        <nav className="hidden lg:flex items-center gap-1">
          <Link
            href="/"
            className={`rounded-full px-4 py-1.5 text-[13px] font-medium transition-colors ${
              isActive('/')
                ? 'bg-ink text-white'
                : 'text-ink-600 hover:bg-ink-50 hover:text-ink'
            }`}
          >
            Inicio
          </Link>

          {GROUPS.map((g) => (
            <div key={g.id} className="relative">
              <button
                type="button"
                onClick={() => setOpenGroup(openGroup === g.id ? null : g.id)}
                onMouseEnter={() => setOpenGroup(g.id)}
                className={`flex items-center gap-1.5 rounded-full px-4 py-1.5 text-[13px] font-medium transition-colors ${
                  groupActive(g) || openGroup === g.id
                    ? 'bg-ink-50 text-ink'
                    : 'text-ink-600 hover:bg-ink-50 hover:text-ink'
                }`}
                aria-haspopup="true"
                aria-expanded={openGroup === g.id}
              >
                <span aria-hidden>{g.emoji}</span>
                <span>{g.label}</span>
                <svg
                  width="10"
                  height="6"
                  viewBox="0 0 10 6"
                  fill="none"
                  className={`transition-transform ${openGroup === g.id ? 'rotate-180' : ''}`}
                  aria-hidden
                >
                  <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>

              {openGroup === g.id && (
                <div
                  onMouseLeave={() => setOpenGroup(null)}
                  className="absolute right-0 top-full mt-2 w-[360px] rounded-2xl border border-ink-100 bg-white/95 p-2 shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-top-2 duration-150"
                >
                  {g.items.map((it) => (
                    <Link
                      key={it.href}
                      href={it.href}
                      className={`flex flex-col gap-0.5 rounded-xl px-3 py-2.5 transition-colors ${
                        isActive(it.href)
                          ? 'bg-ink-50'
                          : 'hover:bg-ink-50/70'
                      }`}
                    >
                      <span className={`text-[13px] font-semibold ${isActive(it.href) ? 'text-ink' : 'text-ink-700'}`}>
                        {it.label}
                      </span>
                      {it.desc && (
                        <span className="text-[11px] text-ink-400 leading-snug">{it.desc}</span>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>

        {/* ===== Mobile burger ===== */}
        <button
          type="button"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="lg:hidden inline-flex h-9 w-9 items-center justify-center rounded-full border border-ink-100 bg-white text-ink hover:bg-ink-50"
          aria-label="Menu"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            {mobileOpen ? (
              <path d="M3 3L15 15M15 3L3 15" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            ) : (
              <>
                <path d="M2 5H16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                <path d="M2 9H16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                <path d="M2 13H16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </>
            )}
          </svg>
        </button>
      </div>

      {/* ===== Mobile drawer ===== */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-ink-100 bg-white max-h-[80vh] overflow-y-auto">
          <div className="mx-auto max-w-7xl px-6 py-4 space-y-4">
            <Link
              href="/"
              className={`block rounded-xl px-4 py-3 text-[15px] font-semibold ${
                isActive('/') ? 'bg-ink text-white' : 'text-ink hover:bg-ink-50'
              }`}
            >
              🏠 Inicio
            </Link>

            {GROUPS.map((g) => (
              <div key={g.id}>
                <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-400">
                  {g.emoji} {g.label}
                </div>
                <div className="space-y-1">
                  {g.items.map((it) => (
                    <Link
                      key={it.href}
                      href={it.href}
                      className={`block rounded-lg px-4 py-2 text-[14px] ${
                        isActive(it.href)
                          ? 'bg-ink-50 font-semibold text-ink'
                          : 'text-ink-700 hover:bg-ink-50'
                      }`}
                    >
                      {it.label}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
