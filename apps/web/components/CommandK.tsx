'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';

type SearchItem = {
  label: string;
  href: string;
  category: string;
  keywords: string[];
  icon?: string;
};

const ITEMS: SearchItem[] = [
  // ===== Dashboards =====
  { label: 'Centro de Mando', href: '/comando', category: 'Dashboard', icon: '⚡', keywords: ['cockpit', 'home', 'inicio', 'overview'] },
  { label: 'Dashboard Directorio', href: '/dashboard-directorio', category: 'Dashboard', icon: '📊', keywords: ['lp', 'roadshow', 'ejecutivo'] },
  { label: 'Investment Readiness', href: '/readiness', category: 'Dashboard', icon: '💯', keywords: ['score', '84.7', 'bankable'] },
  // ===== Análisis financiero =====
  { label: 'Plan 5 años', href: '/plan', category: 'Financiero', icon: '📈', keywords: ['eerr', 'tir', 'van', 'monte carlo', 'tornado'] },
  { label: 'Sensibilidad 2D', href: '/sensitivity', category: 'Financiero', icon: '🌡', keywords: ['heatmap', 'precio', 'costo', 'breakeven'] },
  { label: 'Stress Test', href: '/stress', category: 'Financiero', icon: '⚠️', keywords: ['triple negativo', 'recesion'] },
  { label: 'What-if Live', href: '/whatif-live', category: 'Financiero', icon: '🎚', keywords: ['sliders', 'simulacion', 'live'] },
  { label: 'Comparador Escenarios', href: '/comparador', category: 'Financiero', icon: '🔀', keywords: ['piloto', 'industrial', 'expansion'] },
  { label: 'Financiamiento', href: '/financiamiento', category: 'Financiero', icon: '🏦', keywords: ['deuda', 'equity', 'dscr', 'llcr'] },
  { label: 'SLB Calculator', href: '/slb', category: 'Financiero', icon: '🌱', keywords: ['sustainability', 'bonds', 'step up'] },
  // ===== Inteligencia =====
  { label: 'Decision Engine', href: '/decisiones', category: 'Inteligencia', icon: '🎯', keywords: ['top 5', 'acciones', 'prioridad'] },
  { label: 'Coherencia Cross-Matriz', href: '/coherencia', category: 'Inteligencia', icon: '🔗', keywords: ['gaps', 'sinergia'] },
  { label: 'Red Inteligente', href: '/red', category: 'Inteligencia', icon: '🕸', keywords: ['network graph', 'dependencias', 'modulos'] },
  // ===== Datos =====
  { label: 'Matriz Variables', href: '/variables', category: 'Datos', icon: '📑', keywords: ['165 celdas', 'pd', 'ok', 'excel original'] },
  { label: 'Datos faltantes', href: '/datos', category: 'Datos', icon: '📋', keywords: ['equipo', 'pendiente', 'pd'] },
  { label: 'Data Room DD', href: '/data-room', category: 'Datos', icon: '🗂', keywords: ['due diligence', '41 items', 'lp'] },
  { label: 'Supuestos', href: '/supuestos', category: 'Datos', icon: '📝', keywords: ['hardcoded'] },
  // ===== Operacional =====
  { label: 'Balance de Masa', href: '/balance', category: 'Operacional', icon: '⚖️', keywords: ['sankey', 'mmpp', 'rendimiento'] },
  { label: 'Agenda Camiones', href: '/agenda', category: 'Operacional', icon: '🚚', keywords: ['mmpp', 'estacional'] },
  { label: 'Compliance REP', href: '/compliance', category: 'Operacional', icon: '📜', keywords: ['ley rep', 'hitos', '8 timeline'] },
  { label: 'Carbon Footprint', href: '/carbono', category: 'Operacional', icon: '🌿', keywords: ['lca', 'beccs', 'co2', 'creditos'] },
  // ===== Roadshow / LP =====
  { label: 'Pipeline LP', href: '/pipeline-lp', category: 'Roadshow', icon: '💼', keywords: ['crm', 'kanban', 'bid', 'family office', 'dfi'] },
  { label: 'LP Pack', href: '/lp-pack', category: 'Roadshow', icon: '📦', keywords: ['zip', 'tearsheet', 'pdf'] },
  { label: 'Weekly Digest', href: '/digest', category: 'Roadshow', icon: '📧', keywords: ['email', 'semanal'] },
  { label: 'Equipo y Directorio', href: '/equipo', category: 'Roadshow', icon: '👥', keywords: ['fundadores', 'advisors', 'alianzas'] },
  // ===== Sistema =====
  { label: 'Audit Trail', href: '/audit', category: 'Sistema', icon: '📝', keywords: ['historial', 'cambios', 'dd'] },
  { label: 'Riesgo Integrado', href: '/riesgo', category: 'Sistema', icon: '⚠️', keywords: ['clima', 'financiero', 'regulatorio'] },
  { label: 'Macro Chile', href: '/macro', category: 'Sistema', icon: '🇨🇱', keywords: ['banco central', 'usd', 'uf', 'tpm', 'ipc'] },
  { label: 'API Explorer', href: '/api', category: 'Sistema', icon: '🔌', keywords: ['endpoints', 'rest', 'swagger'] },
  { label: 'Investigación', href: '/investigacion', category: 'Sistema', icon: '📚', keywords: ['papers', 'cientificos', 'damodaran'] },
];

export function CommandK() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);

  // Global keyboard shortcut Cmd/Ctrl+K
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
        setQuery('');
        setSelectedIdx(0);
      }
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  // Filter items
  const filtered = useMemo(() => {
    if (!query.trim()) return ITEMS.slice(0, 12);
    const q = query.toLowerCase();
    return ITEMS
      .map((item) => {
        const labelMatch = item.label.toLowerCase().includes(q);
        const keywordMatch = item.keywords.some((k) => k.toLowerCase().includes(q));
        const categoryMatch = item.category.toLowerCase().includes(q);
        const score = (labelMatch ? 3 : 0) + (keywordMatch ? 2 : 0) + (categoryMatch ? 1 : 0);
        return { item, score };
      })
      .filter((x) => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .map((x) => x.item)
      .slice(0, 12);
  }, [query]);

  useEffect(() => {
    setSelectedIdx(0);
  }, [filtered]);

  // Arrow keys navigation
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIdx((i) => Math.min(i + 1, filtered.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIdx((i) => Math.max(i - 1, 0));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        const item = filtered[selectedIdx];
        if (item) {
          router.push(item.href);
          setOpen(false);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, filtered, selectedIdx, router]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 backdrop-blur-sm p-4 pt-[15vh]"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-xl rounded-appleLg bg-white shadow-appleLg ring-1 ring-ink-100"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-ink-100 px-4 py-3">
          <span className="text-ink-400">🔍</span>
          <input
            autoFocus
            type="text"
            placeholder="Buscar páginas, módulos, conceptos..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-base text-ink placeholder:text-ink-400 focus:outline-none"
          />
          <kbd className="rounded border border-ink-100 bg-ink-50 px-2 py-0.5 text-[10px] font-medium text-ink-400">ESC</kbd>
        </div>
        <div className="max-h-[400px] overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-ink-400">
              Sin resultados para "{query}"
            </div>
          ) : (
            filtered.map((item, idx) => (
              <button
                key={item.href}
                onClick={() => {
                  router.push(item.href);
                  setOpen(false);
                }}
                onMouseEnter={() => setSelectedIdx(idx)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition ${
                  idx === selectedIdx ? 'bg-brand-50' : 'hover:bg-ink-50'
                }`}
              >
                <span className="text-xl shrink-0">{item.icon || '📁'}</span>
                <div className="flex-1 min-w-0">
                  <div className={`text-sm font-medium ${idx === selectedIdx ? 'text-brand' : 'text-ink'}`}>
                    {item.label}
                  </div>
                  <div className="text-[11px] text-ink-400">{item.category} · {item.href}</div>
                </div>
                {idx === selectedIdx && (
                  <kbd className="rounded border border-brand/30 bg-white px-2 py-0.5 text-[10px] font-medium text-brand">↵</kbd>
                )}
              </button>
            ))
          )}
        </div>
        <div className="flex items-center justify-between border-t border-ink-100 px-4 py-2 text-[10px] text-ink-400">
          <div className="flex gap-3">
            <span><kbd className="rounded border border-ink-100 px-1">↑↓</kbd> navegar</span>
            <span><kbd className="rounded border border-ink-100 px-1">↵</kbd> abrir</span>
          </div>
          <span className="font-medium text-brand">⌘K Trongkai Search</span>
        </div>
      </div>
    </div>
  );
}
