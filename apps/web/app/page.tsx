import Image from 'next/image';
import Link from 'next/link';
import { stats } from '@/lib/seed-data';

const accesos = [
  { href: '/dashboard-directorio', label: 'Dashboard Directorio', desc: 'Vista ejecutiva consolidada' },
  { href: '/readiness', label: 'Investment Readiness', desc: 'Score 0-100 de madurez' },
  { href: '/plan', label: 'Plan 5 años', desc: 'EERR + KPIs + tornado' },
  { href: '/sensitivity', label: 'Análisis de Sensibilidad', desc: 'Heatmap 2D + breakeven + curvas 1D' },
  { href: '/stress', label: 'Stress Test', desc: 'Triple-negativo simultáneo' },
  { href: '/financiamiento', label: 'Financiamiento', desc: 'Deuda/Equity + DSCR + LLCR' },
  { href: '/slb', label: 'Sustainability Bonds', desc: 'KPIs ESG con step-up' },
  { href: '/compliance', label: 'Compliance Ley REP', desc: '8 hitos regulatorios' },
  { href: '/carbono', label: 'Carbon Footprint', desc: 'LCA 3 escenarios + créditos CO₂' },
  { href: '/macro', label: 'Macro Chile', desc: 'Banco Central en vivo' },
  { href: '/api', label: 'API Explorer', desc: '10 endpoints try-it-now' },
  { href: '/investigacion', label: 'Research', desc: '27 papers peer-reviewed' },
];

export default function Home() {
  return (
    <div className="space-y-24">
      {/* ===== Hero Apple-style ===== */}
      <section className="apple-hero">
        <div className="mx-auto flex max-w-3xl flex-col items-center">
          <Image
            src="/icon-trongkai.png"
            alt="Trongkai"
            width={88}
            height={88}
            priority
            className="mb-6"
          />
          <h1 className="text-[clamp(2.5rem,5vw,4.5rem)] font-semibold tracking-apple text-ink">
            Trongkai
          </h1>
          <p className="mt-3 text-xl font-medium text-ink-600">
            Innovación en Nutrición Circular.
          </p>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-400">
            La plataforma inteligente que transforma 800.000 toneladas de subproductos
            agroindustriales chilenos en ingredientes funcionales — con modelo financiero,
            ESG y compliance integrado.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <Link href="/dashboard-directorio" className="btn-apple">
              Ver Dashboard Directorio
            </Link>
            <Link href="/readiness" className="btn-apple btn-apple-ghost">
              Investment Readiness Score
            </Link>
          </div>
          <div className="mt-6 flex items-center gap-2 text-[12px] text-ink-400">
            <span className="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-brand" />
            Engine en vivo · trongkai-engine.fly.dev
          </div>
        </div>
      </section>

      {/* ===== 3 valor agregado === */}
      <section>
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-[clamp(1.75rem,3vw,2.5rem)] font-semibold tracking-apple text-ink">
            Una sola plataforma. Tres pilares.
          </h2>
          <p className="mt-3 text-lg text-ink-400">
            Comercial, financiero y ESG — integrados en tiempo real.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <PilarCard
            tag="Tesis comercial"
            titulo="Bioeconomía circular"
            descripcion="800.000 ton/año de subproductos agroindustriales convertidos en ingredientes funcionales para acuicultura, mascotas y humanos."
            stats={[
              { label: 'Cuota contractual', value: `${(stats.volumenContratoTon / 1000).toFixed(0)}k`, unit: 'ton/año' },
              { label: 'Comprometido', value: `${((stats.volumenComprometidoActual / stats.volumenContratoTon) * 100).toFixed(0)}%`, unit: 'de la cuota' },
              { label: 'SKUs Feed/Food', value: `${stats.productosFeed}/${stats.productosFood}`, unit: 'catálogo' },
            ]}
          />
          <PilarCard
            tag="Performance financiera"
            titulo="Defendible a directorio"
            descripcion="TIR 30,7% con working capital + cobro real. LLCR 6,06 — bancable. Investment Readiness Score 84,7/100."
            stats={[
              { label: 'TIR proyecto', value: '30,7%', unit: 'anual' },
              { label: 'VAN @ 18%', value: '$5,5B', unit: 'CLP' },
              { label: 'EV exit 5y', value: '$131B', unit: '9,6× EBITDA' },
            ]}
            highlight
          />
          <PilarCard
            tag="Impacto ESG"
            titulo="Carbono negativo"
            descripcion="-53.000 ton CO₂eq en 5 años por evitar descomposición en vertedero (LCA baseline). Listo para fondos ESG europeos."
            stats={[
              { label: 'Net 5y', value: '-53k', unit: 'ton CO₂eq' },
              { label: 'BECCS', value: '-139k', unit: 'ton CO₂eq' },
              { label: 'Revenue créditos', value: '$736M', unit: 'CLP 5y' },
            ]}
          />
        </div>
      </section>

      {/* ===== Numbers que importan ===== */}
      <section className="rounded-appleXl bg-ink-50 px-6 py-16">
        <div className="mx-auto mb-12 max-w-2xl text-center">
          <h2 className="text-[clamp(1.75rem,3vw,2.5rem)] font-semibold tracking-apple text-ink">
            Los números que importan.
          </h2>
          <p className="mt-3 text-lg text-ink-400">
            Recalculados en vivo desde el motor en cada visita.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          <BigNumber value="245" unit="tests verde" detail="100% pass" />
          <BigNumber value="25+" unit="endpoints REST" detail="documentados" />
          <BigNumber value="15+" unit="módulos engine" detail="Python 3.12" />
          <BigNumber value="27" unit="papers científicos" detail="peer-reviewed" />
        </div>
      </section>

      {/* ===== Secciones ===== */}
      <section>
        <div className="mb-10">
          <h2 className="text-[clamp(1.75rem,3vw,2.5rem)] font-semibold tracking-apple text-ink">
            Todas las herramientas.
          </h2>
          <p className="mt-2 text-lg text-ink-400">
            Navegación rápida a las 12 áreas de la plataforma.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {accesos.map((a) => (
            <Link
              key={a.href}
              href={a.href}
              className="apple-card group flex items-center justify-between"
            >
              <div>
                <div className="font-semibold text-ink">{a.label}</div>
                <div className="mt-1 text-[13px] text-ink-400">{a.desc}</div>
              </div>
              <span className="ml-4 text-ink-200 transition-transform group-hover:translate-x-1 group-hover:text-brand">
                →
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* ===== CTA final ===== */}
      <section className="rounded-appleXl bg-brand px-6 py-20 text-center text-white">
        <h2 className="text-[clamp(1.75rem,3vw,2.5rem)] font-semibold tracking-apple">
          ¿Listo para mostrarlo a inversionistas?
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-lg text-white/85">
          Descarga el tearsheet ejecutivo en PDF — 3 páginas con KPIs, valoración, Monte Carlo, carbono y compliance. Generado en vivo.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <a
            href={`${process.env.NEXT_PUBLIC_ENGINE_URL ?? 'https://trongkai-engine.fly.dev'}/api/lp-pack.zip`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full bg-white px-5 py-2.5 text-[14px] font-medium text-brand transition hover:scale-105"
          >
            📦 LP Pack completo (ZIP)
          </a>
          <a
            href={`${process.env.NEXT_PUBLIC_ENGINE_URL ?? 'https://trongkai-engine.fly.dev'}/api/tearsheet.pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full border border-white/40 bg-white/10 px-5 py-2.5 text-[14px] font-medium text-white transition hover:bg-white/20"
          >
            📄 Solo PDF tearsheet
          </a>
          <Link
            href="/api"
            className="rounded-full border border-white/30 px-5 py-2.5 text-[14px] font-medium text-white transition hover:bg-white/10"
          >
            Explorar API
          </Link>
        </div>
      </section>
    </div>
  );
}

function PilarCard({
  tag,
  titulo,
  descripcion,
  stats,
  highlight,
}: {
  tag: string;
  titulo: string;
  descripcion: string;
  stats: { label: string; value: string; unit: string }[];
  highlight?: boolean;
}) {
  return (
    <div className={`apple-card flex flex-col ${highlight ? 'bg-brand-50 ring-1 ring-brand/20' : ''}`}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
        {tag}
      </div>
      <h3 className="mt-2 text-2xl font-semibold tracking-apple text-ink">{titulo}</h3>
      <p className="mt-3 flex-1 text-[15px] leading-relaxed text-ink-600">{descripcion}</p>
      <div className="mt-6 grid grid-cols-3 gap-3 border-t border-ink-100 pt-4">
        {stats.map((s) => (
          <div key={s.label}>
            <div className="text-[10px] uppercase tracking-wide text-ink-400">{s.label}</div>
            <div className="tabular mt-0.5 text-base font-semibold text-ink">{s.value}</div>
            <div className="text-[10px] text-ink-400">{s.unit}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function BigNumber({ value, unit, detail }: { value: string; unit: string; detail: string }) {
  return (
    <div className="text-center">
      <div className="tabular text-[clamp(2.5rem,4vw,3.5rem)] font-semibold tracking-apple text-ink">
        {value}
      </div>
      <div className="mt-1 text-sm font-medium text-ink">{unit}</div>
      <div className="text-[12px] text-ink-400">{detail}</div>
    </div>
  );
}
