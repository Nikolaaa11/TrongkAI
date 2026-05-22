import Link from 'next/link';
import { seed, stats } from '@/lib/seed-data';

const accesos = [
  { href: '/dashboard-directorio', label: 'Dashboard Directorio', icon: '◈', desc: 'Vista ejecutiva consolidada' },
  { href: '/riesgo', label: 'Análisis de riesgo', icon: '◭', desc: 'Financiero + clima + regulatorio' },
  { href: '/plan', label: 'Plan 5 años', icon: '◊', desc: 'EERR + KPIs + tornado + escenarios' },
  { href: '/financiamiento', label: 'Financiamiento', icon: '◉', desc: 'Deuda/Equity + DSCR + TIR equity' },
  { href: '/slb', label: 'Sustainability Bonds', icon: '◐', desc: 'KPIs ESG con step-up' },
  { href: '/compliance', label: 'Compliance Ley REP', icon: '◇', desc: '8 hitos regulatorios' },
  { href: '/balance', label: 'Balance de masa', icon: '⬡', desc: 'Modo A vs B + Sankey' },
  { href: '/agenda', label: 'Agenda camiones', icon: '⬢', desc: 'Recepción MMPP por temporada' },
  { href: '/investigacion', label: 'Investigación', icon: '◍', desc: '27 papers peer-reviewed' },
  { href: '/whatif', label: 'What-if', icon: '◎', desc: '5 escenarios precargados' },
  { href: '/supuestos', label: 'Supuestos', icon: '◌', desc: '165 supuestos catalogados' },
  { href: '/about', label: 'Equipo', icon: '◯', desc: 'Liderazgo + directorio + alianzas' },
];

export default function Home() {
  return (
    <div className="space-y-8">
      <header className="border-b border-oliva/10 pb-6">
        <div className="flex items-baseline justify-between">
          <div>
            <h1 className="font-serif text-4xl text-oliva-900">Trongkai</h1>
            <p className="mt-2 text-base text-oliva-700">Innovación en Nutrición Circular</p>
          </div>
          <div className="text-right text-xs text-oliva-500">
            <div>{new Date().toLocaleDateString('es-CL', { day: 'numeric', month: 'long', year: 'numeric' })}</div>
            <div className="mt-1 inline-flex items-center gap-1">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-oliva-700 animate-pulse" />
              Engine: trongkai-engine.fly.dev
            </div>
          </div>
        </div>
      </header>

      {/* === Síntesis ejecutiva en 3 grandes === */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="card-hover rounded-xl border-2 border-oliva-900/15 bg-white p-6">
          <div className="text-[10px] uppercase tracking-[0.1em] text-oliva-600">Tesis comercial</div>
          <h2 className="mt-2 font-serif text-2xl text-oliva-900">Bioeconomía circular</h2>
          <p className="mt-2 text-sm leading-relaxed text-oliva-700">
            Transforma 800.000 ton/año de subproductos agroindustriales chilenos en{' '}
            <strong>ingredientes funcionales</strong> para acuicultura, mascotas y humanos.
          </p>
          <div className="mt-4 grid grid-cols-3 gap-2 border-t border-oliva/10 pt-3 text-xs">
            <Mini label="Cuota contractual" value={`${(stats.volumenContratoTon / 1000).toFixed(0)}k`} unit="ton/año" />
            <Mini label="Comprometido" value={`${((stats.volumenComprometidoActual / stats.volumenContratoTon) * 100).toFixed(0)}%`} unit="de la cuota" />
            <Mini label="SKUs Feed/Food" value={`${stats.productosFeed}/${stats.productosFood}`} unit="catálogo" />
          </div>
        </div>

        <div className="card-hover rounded-xl border-2 border-trigo/30 bg-trigo/5 p-6">
          <div className="text-[10px] uppercase tracking-[0.1em] text-trigo">Performance financiera</div>
          <h2 className="mt-2 font-serif text-2xl text-oliva-900">Defendible a directorio</h2>
          <p className="mt-2 text-sm leading-relaxed text-oliva-700">
            TIR <strong className="tabular">29,4%</strong> con working capital + cobro real.
            Apalancado <strong className="tabular">131%</strong>. LLCR 6,06 ✓ bancable.
          </p>
          <div className="mt-4 grid grid-cols-3 gap-2 border-t border-trigo/20 pt-3 text-xs">
            <Mini label="VAN @ 18%" value="$5,5B" unit="CLP" />
            <Mini label="Payback" value="52" unit="meses" />
            <Mini label="EV exit 5y" value="$131B" unit="9,6x EBITDA" />
          </div>
        </div>

        <div className="card-hover rounded-xl border-2 border-oliva-700/25 bg-oliva-50/40 p-6">
          <div className="text-[10px] uppercase tracking-[0.1em] text-oliva-600">Impacto ESG</div>
          <h2 className="mt-2 font-serif text-2xl text-oliva-900">Carbono negativo</h2>
          <p className="mt-2 text-sm leading-relaxed text-oliva-700">
            <strong>-53.000 ton CO₂eq</strong> 5 años por evitar descomposición en vertedero (LCA baseline).
            Revenue créditos: <strong>$736M CLP</strong>.
          </p>
          <div className="mt-4 grid grid-cols-3 gap-2 border-t border-oliva-700/20 pt-3 text-xs">
            <Mini label="Net BECCS" value="-138k" unit="ton CO₂eq" />
            <Mini label="Papers ESG" value="27" unit="peer-reviewed" />
            <Mini label="B-Corp" value="✓" unit="certificada" />
          </div>
        </div>
      </section>

      {/* === Bloqueantes + alertas === */}
      <section className="rounded-lg border border-borgoña/20 bg-borgoña/5 p-4">
        <h2 className="font-serif text-lg text-borgoña">Bloqueantes & alertas activas</h2>
        <ul className="mt-2 grid grid-cols-1 gap-1 text-sm text-oliva-700 md:grid-cols-2">
          <li>• <strong>Capacidad del secador</strong> aún PD — limita agenda real.</li>
          <li>• <strong>Tiempo descomposición tomasa/pomasa</strong> sin medición de planta.</li>
          <li>• <strong>{stats.supuestosPD} supuestos PD</strong> activos (de {stats.supuestosPD + stats.supuestosOK} totales).</li>
          <li>• <strong>Reglamento sanitario MMA</strong> vigor 14-jul-2026 — ajustar instalaciones.</li>
        </ul>
      </section>

      {/* === 12 accesos === */}
      <section>
        <h2 className="font-serif text-xl text-oliva-900">Secciones</h2>
        <p className="mt-1 text-sm text-oliva-600">Navegación rápida a las 12 áreas de la plataforma.</p>
        <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
          {accesos.map((a) => (
            <Link
              key={a.href}
              href={a.href}
              className="card-hover group rounded-lg border border-oliva/10 bg-white p-3 transition"
            >
              <div className="flex items-baseline gap-2">
                <span className="text-2xl text-oliva-700 group-hover:text-trigo">{a.icon}</span>
                <span className="font-medium text-oliva-900">{a.label}</span>
              </div>
              <p className="mt-1 text-xs text-oliva-600">{a.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* === Pie con stats técnicas === */}
      <section className="grid grid-cols-2 gap-3 rounded-lg border border-oliva/10 bg-white p-4 md:grid-cols-6">
        <TechStat label="Endpoints REST" value="23" />
        <TechStat label="Tests Python" value="201/201" tone="ok" />
        <TechStat label="Páginas UI" value="13" />
        <TechStat label="Módulos engine" value="20" />
        <TechStat label="Papers citados" value="27" />
        <TechStat label="Commits main" value="60+" />
      </section>
    </div>
  );
}

function Mini({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div>
      <div className="text-[9px] uppercase tracking-wide text-oliva-500">{label}</div>
      <div className="tabular text-sm font-semibold text-oliva-900">{value}</div>
      <div className="text-[9px] text-oliva-500">{unit}</div>
    </div>
  );
}

function TechStat({ label, value, tone }: { label: string; value: string; tone?: 'ok' }) {
  return (
    <div>
      <div className="text-[9px] uppercase tracking-wide text-oliva-500">{label}</div>
      <div className={`tabular text-lg font-semibold ${tone === 'ok' ? 'text-oliva-700' : 'text-oliva-900'}`}>
        {value}
      </div>
    </div>
  );
}
