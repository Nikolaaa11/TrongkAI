'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const ENGINE_URL = process.env.NEXT_PUBLIC_ENGINE_URL ?? 'http://localhost:8000';

type Capa = {
  id: string;
  titulo: string;
  subtitulo: string;
  color: string;
  paginas: { href: string; label: string; desc: string; destacada?: boolean }[];
};

const ARQUITECTURA: Capa[] = [
  {
    id: 'inteligencia',
    titulo: '🧠 Capa 1 · Inteligencia',
    subtitulo: 'Síntesis cross-modular y plan acción auto-generado',
    color: 'from-purple-500 to-purple-600',
    paginas: [
      { href: '/inteligencia', label: 'Inteligencia consolidada', desc: 'Score global, insights priorizados, plan acción top 5', destacada: true },
      { href: '/comando', label: 'Centro de Mando', desc: 'Cockpit ejecutivo con KPIs financieros + balances + simulación' },
      { href: '/dashboard-directorio', label: 'Dashboard Directorio', desc: 'Vista board-friendly para reunión mensual' },
      { href: '/decisiones', label: 'Decision Engine', desc: 'Top 5 acciones priorizadas cross-matriz' },
    ],
  },
  {
    id: 'datos',
    titulo: '📥 Capa 2 · Datos & Calibración',
    subtitulo: 'Inputs, validación de supuestos, completitud',
    color: 'from-blue-500 to-blue-600',
    paginas: [
      { href: '/inbox', label: 'Inbox', desc: 'Archivos nuevos clasificados automáticamente' },
      { href: '/variables', label: 'Matriz Variables', desc: 'Todos los supuestos PD / OK_PROVISORIO / OK_VALIDADO' },
      { href: '/datos', label: 'Datos faltantes', desc: 'Checklist visual de gaps por módulo' },
      { href: '/coherencia', label: 'Coherencia', desc: 'Gaps entre matrices del modelo' },
      { href: '/red', label: 'Red Inteligente', desc: 'Grafo de dependencias entre módulos' },
      { href: '/data-room', label: 'Data Room DD', desc: 'Checklist due-diligence para LPs' },
      { href: '/investigacion', label: 'Investigación', desc: 'Papers científicos y benchmarks' },
    ],
  },
  {
    id: 'planta',
    titulo: '🏭 Capa 3 · Planta Operacional',
    subtitulo: 'Equipos, parámetros, etapas, fotos reales',
    color: 'from-brand to-brand-light',
    paginas: [
      { href: '/planta', label: 'Planta Visual', desc: 'Layout con fotos reales de los 15 equipos', destacada: true },
      { href: '/equipos', label: 'Fichas Equipos', desc: '20 fichas técnicas editables (proveedor, kW, CAPEX)' },
      { href: '/parametros', label: 'Parámetros Variables', desc: 'Sueldos, energía, agua, calor, flete, arriendos' },
      { href: '/balance-etapas', label: 'Etapas Proceso', desc: '11 etapas Agrosphere con tiempos + humedades' },
      { href: '/productos-etapas', label: 'Productos × Etapas', desc: 'Matriz MMPP por etapa con yield MSF' },
    ],
  },
  {
    id: 'balances',
    titulo: '⚖️ Capa 4 · Balances Integrales',
    subtitulo: '4 balances + alarmas en tiempo real',
    color: 'from-cyan-500 to-cyan-600',
    paginas: [
      { href: '/balance-integral', label: 'Vista Integral', desc: 'Los 4 balances en uno + score global', destacada: true },
      { href: '/balance', label: 'Producto (masa)', desc: 'Closure ±0.5% por SKU' },
      { href: '/balance-energia', label: 'Energía', desc: 'kWh + mix renovable + factor potencia' },
      { href: '/balance-agua', label: 'Agua', desc: 'Consumo + recirculación + DGA' },
      { href: '/balance-rrhh', label: 'RRHH ⚠️', desc: 'Horas + alarmas extras CT Chile' },
    ],
  },
  {
    id: 'simulacion',
    titulo: '⏱ Capa 5 · Simulación & Costeo',
    subtitulo: 'Producción + costos + escalas + revenue',
    color: 'from-orange-500 to-orange-600',
    paginas: [
      { href: '/simulacion', label: 'Simulación Temporal', desc: 'Producción + costos por hora/día/mes/año', destacada: true },
      { href: '/escalas', label: 'Escalas Piloto vs Industrial', desc: 'x1 vs x10 vs x50 vs x100 con CAPEX y payback' },
      { href: '/costeo', label: 'Costeo Dinámico', desc: 'Costo CLP/kg y USD/kg por SKU y etapa' },
      { href: '/pef-analisis', label: 'PEF A/B', desc: '¿Se justifica el arriendo del PEF?' },
    ],
  },
  {
    id: 'modelo',
    titulo: '📈 Capa 6 · Modelo Financiero',
    subtitulo: 'Plan 5 años, sensibilidad, valoración',
    color: 'from-red-500 to-red-600',
    paginas: [
      { href: '/plan', label: 'Plan 5 años', desc: 'EERR mensual + TIR + VAN + payback' },
      { href: '/sensitivity', label: 'Sensibilidad', desc: 'Tornado + heatmap 2D/3D' },
      { href: '/comparador', label: 'Comparador Escenarios', desc: 'PILOTO vs INDUSTRIAL vs EXPANSION' },
      { href: '/whatif-live', label: 'What-if Live', desc: 'Sliders en vivo' },
      { href: '/stress', label: 'Stress Test', desc: 'Triple negativo' },
      { href: '/financiamiento', label: 'Financiamiento', desc: 'Mix deuda/equity + DSCR' },
      { href: '/slb', label: 'SLB Calculator', desc: 'Sustainability-Linked Bonds' },
    ],
  },
  {
    id: 'comercial',
    titulo: '💼 Capa 7 · Comercial & LP',
    subtitulo: 'Clientes, productos, equipo, fundraising',
    color: 'from-pink-500 to-pink-600',
    paginas: [
      { href: '/clientes-reales', label: 'Clientes', desc: 'Catálogo real (Iansa, Sugal, Agrozzi)' },
      { href: '/commercial', label: 'Commercial Intel', desc: 'Pricing + HHI + tech ROI' },
      { href: '/nutrientes', label: 'Nutrientes', desc: 'Perfil científico por SKU + TAM $26.6B' },
      { href: '/tecnologias', label: 'Tech Stack', desc: 'Opticept, PEF, Micromolienda' },
      { href: '/pipeline-lp', label: 'Pipeline LP', desc: 'CRM de inversionistas' },
      { href: '/lp-pack', label: 'LP Pack', desc: 'Entregables descargables ZIP' },
      { href: '/equipo', label: 'Equipo', desc: 'Directorio + advisors' },
    ],
  },
  {
    id: 'compliance',
    titulo: '📜 Capa 8 · Compliance & Macro',
    subtitulo: 'Regulación, sustentabilidad, contexto',
    color: 'from-emerald-500 to-emerald-600',
    paginas: [
      { href: '/compliance', label: 'Compliance REP', desc: 'Ley REP timeline + alertas' },
      { href: '/carbono', label: 'Carbono', desc: 'LCA + revenue créditos CO₂' },
      { href: '/macro', label: 'Macro Chile', desc: 'USD/CLP, UF, TPM, IPC live' },
      { href: '/roadmap', label: 'Roadmap', desc: 'Timeline de hitos del proyecto' },
    ],
  },
  {
    id: 'sistema',
    titulo: '🔧 Capa 9 · Sistema',
    subtitulo: 'Estado técnico, auditoría',
    color: 'from-ink to-ink-700',
    paginas: [
      { href: '/readiness', label: 'Readiness Score', desc: 'Score 0-100 madurez para LPs' },
      { href: '/salud', label: 'Salud Sistema', desc: 'Health check técnico' },
      { href: '/audit', label: 'Audit Trail', desc: 'Historial de cambios' },
    ],
  },
];

type Sintesis = {
  score_global_inteligencia: number;
  insights_criticos: number;
  oportunidades: number;
};

export default function MapaPage() {
  const [sintesis, setSintesis] = useState<Sintesis | null>(null);

  useEffect(() => {
    fetch(`${ENGINE_URL}/inteligencia/sintesis`).then((r) => r.json()).then(setSintesis).catch(() => {});
  }, []);

  const totalPaginas = ARQUITECTURA.reduce((s, c) => s + c.paginas.length, 0);

  return (
    <div className="space-y-10">
      <header>
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Arquitectura de la plataforma</p>
        <h1 className="mt-2 text-4xl font-bold">🗺 Mapa Trongkai</h1>
        <p className="mt-2 text-ink-500">
          Las {totalPaginas} páginas organizadas en 9 capas interconectadas. Click en cualquier card para navegar.
        </p>
      </header>

      {/* KPIs globales */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[10px] uppercase text-ink-400">Páginas activas</p>
          <p className="mt-1 text-3xl font-bold">{totalPaginas}</p>
        </div>
        <div className="rounded-xl border border-ink-100 bg-white p-4">
          <p className="text-[10px] uppercase text-ink-400">Capas funcionales</p>
          <p className="mt-1 text-3xl font-bold">{ARQUITECTURA.length}</p>
        </div>
        {sintesis && (
          <>
            <div className="rounded-xl border border-brand bg-brand-50/40 p-4">
              <p className="text-[10px] uppercase text-ink-400">Score inteligencia</p>
              <p className="mt-1 text-3xl font-bold text-brand">{sintesis.score_global_inteligencia.toFixed(0)}<span className="text-base text-ink-400">/100</span></p>
            </div>
            <div className="rounded-xl border border-ink-100 bg-white p-4">
              <p className="text-[10px] uppercase text-ink-400">Insights detectados</p>
              <p className="mt-1 text-3xl font-bold">{sintesis.oportunidades + sintesis.insights_criticos}</p>
            </div>
          </>
        )}
      </div>

      {/* Flujo de información - mini diagrama */}
      <section className="rounded-2xl border border-ink-100 bg-gradient-to-br from-fbfbfd to-white p-6">
        <h2 className="text-lg font-bold mb-4">Cómo fluye la información</h2>
        <div className="flex flex-wrap items-center justify-center gap-2 text-sm">
          <Flow label="📥 Datos" link="/inbox" />
          <Arrow />
          <Flow label="🏭 Planta" link="/planta" />
          <Arrow />
          <Flow label="⚖️ Balances" link="/balance-integral" />
          <Arrow />
          <Flow label="⏱ Simulación" link="/simulacion" />
          <Arrow />
          <Flow label="📈 Modelo" link="/plan" />
          <Arrow />
          <Flow label="🧠 Inteligencia" link="/inteligencia" primary />
          <Arrow />
          <Flow label="📦 Entregables" link="/lp-pack" />
        </div>
      </section>

      {/* Capas */}
      <section className="space-y-6">
        {ARQUITECTURA.map((capa) => (
          <div key={capa.id} className="rounded-2xl border border-ink-100 bg-white p-6">
            <div className={`mb-4 inline-block rounded-lg bg-gradient-to-r ${capa.color} px-4 py-2`}>
              <h3 className="text-white font-bold">{capa.titulo}</h3>
              <p className="text-white/90 text-xs">{capa.subtitulo}</p>
            </div>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {capa.paginas.map((p) => (
                <Link
                  key={p.href}
                  href={p.href}
                  className={`rounded-xl border p-3 transition-all hover:shadow-md hover:scale-[1.02] ${
                    p.destacada ? 'border-brand bg-brand-50/30' : 'border-ink-100 bg-fbfbfd'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <p className="text-sm font-semibold flex items-center gap-1">
                        {p.destacada && <span className="text-xs text-brand">⭐</span>}
                        {p.label}
                      </p>
                      <p className="mt-1 text-xs text-ink-500 leading-tight">{p.desc}</p>
                    </div>
                    <span className="text-ink-300 text-xs">→</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </section>

      {/* Footer info */}
      <section className="rounded-2xl bg-ink p-6 text-white text-center">
        <h3 className="text-lg font-bold mb-2">⚡ Atajos rápidos</h3>
        <p className="text-sm opacity-90">
          Apretá <kbd className="rounded bg-white/20 px-2 py-0.5 text-xs">⌘K</kbd> en cualquier momento para buscar en toda la plataforma.
        </p>
        <p className="text-xs opacity-70 mt-2">
          Engine: 90+ endpoints REST · Frontend: {totalPaginas} páginas · Tests: 581/581 verde
        </p>
      </section>
    </div>
  );
}

function Flow({ label, link, primary }: { label: string; link: string; primary?: boolean }) {
  return (
    <Link
      href={link}
      className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
        primary ? 'bg-brand text-white' : 'bg-white border border-ink-200 text-ink-700 hover:border-brand'
      }`}
    >
      {label}
    </Link>
  );
}

function Arrow() {
  return <span className="text-ink-300 text-lg">→</span>;
}
