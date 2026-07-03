'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

import { GUIA, SCREENSHOTS, type Seccion, type Grupo } from '@/lib/guia-data';


const PRIMEROS_PASOS = [
  { persona: 'Soy del Directorio', emoji: '🎯', href: '/comando', label: 'Empezá en Centro de Mando', desc: 'El estado del negocio en una pantalla.' },
  { persona: 'Soy de Operación', emoji: '🏭', href: '/simulacion', label: 'Empezá en Simulación', desc: 'Cuánto produce y cuesta la planta.' },
  { persona: 'Soy Inversionista', emoji: '💼', href: '/readiness', label: 'Empezá en Readiness', desc: 'Madurez del proyecto y data room.' },
  { persona: 'Soy de Análisis', emoji: '📊', href: '/whatif-live', label: 'Empezá en What-if Live', desc: 'Jugá con los supuestos en vivo.' },
  { persona: 'Cargo datos reales', emoji: '🎛', href: '/parametros', label: 'Empezá en Parámetros', desc: 'El origen: editás y todo recalcula.' },
];

const COMO_FUNCIONA = [
  { icono: '🧭', titulo: 'Navegá por tu rol', texto: 'El menú de arriba está organizado por persona: Directorio, Operación, Inversionista, Análisis y Sistema. Buscá tu grupo y vas directo a lo tuyo.' },
  { icono: '⌘', titulo: 'Buscá con ⌘K', texto: 'Presioná ⌘K (Mac) o Ctrl+K (Windows) en cualquier momento para saltar a cualquier página escribiendo su nombre.' },
  { icono: '◍', titulo: 'Confiá en los datos', texto: 'Los números clave muestran su calidad: PD (sin validar), PROVISORIO o VALIDADO. El badge de "exactitud del modelo" te dice qué tan firme es cada predicción.' },
  { icono: '🔗', titulo: 'Seguí los hilos', texto: 'Al pie de cada página, el bloque "Conectado con" te lleva del número a sus supuestos, su desglose y su banda de confianza en un click.' },
];

const FUENTES = [
  {
    icono: '🎛', titulo: 'Datos de planta (editables sin código)',
    texto: 'Sueldos, tarifas (energía, agua, flete), arriendos, humedades y las fichas de equipos. Viven en parametros-planta.json y fichas-equipos.json, persistidos en el volumen de Fly.',
    comoReemplazar: 'Se editan desde la app en /parametros y /equipos. Guardás y queda — no se toca código.',
  },
  {
    icono: '🏭', titulo: 'Supuestos del plan industrial y precios SKU',
    texto: 'Volumen 50k ton/año, OpEx/CapEx industrial, WACC y los precios de venta por SKU. Hoy viven en el motor (código), como estimaciones de mercado.',
    comoReemplazar: 'Se exploran sin riesgo en /whatif-live. Para fijar valores reales, el data-hunter (schedule viernes) los busca con fuente y los deja listos para validar.',
  },
  {
    icono: '🌐', titulo: 'Datos externos (macro, papers, normativa)',
    texto: 'Tipo de cambio y tasas del Banco Central, literatura científica (rendimientos, LCA) y el calendario de la Ley REP.',
    comoReemplazar: 'Se refrescan solos por los agentes y schedules (macro-refresh, papers-refresh, compliance-officer).',
  },
];

const GLOSARIO: { t: string; d: string }[] = [
  { t: 'TIR', d: 'Tasa Interna de Retorno: la rentabilidad anual del proyecto. Se compara contra el WACC; si TIR > WACC, crea valor.' },
  { t: 'VAN', d: 'Valor Actual Neto: la suma de los flujos futuros traídos a hoy (descontados al WACC). Positivo = el proyecto vale la pena.' },
  { t: 'WACC', d: 'Costo de capital (tasa de descuento). En el modelo es 18%; es el "mínimo a superar" (hurdle) de la TIR.' },
  { t: 'Payback', d: 'Cuántos meses/años tarda en recuperarse la inversión, sin descontar.' },
  { t: 'MOIC', d: 'Multiple On Invested Capital: cuántas veces se multiplica el capital al salir (ej. 9× = se recupera 9 veces).' },
  { t: 'EBITDA', d: 'Resultado operativo antes de intereses, impuestos y depreciación. Aproxima la caja que genera la operación.' },
  { t: 'OPEX', d: 'Costos de operación recurrentes: arriendo, mano de obra, energía, agua, flete. (En TrongkAI, el OPEX completo del piloto.)' },
  { t: 'CAPEX', d: 'Inversión en activos: equipos, instalación, ingeniería. Se paga una vez (no recurrente).' },
  { t: 'Costo fijo vs variable', d: 'Fijo = se paga aunque la planta pare (arriendo, planilla, 12 meses). Variable = escala con la producción (energía, agua, flete).' },
  { t: 'Yield / Rendimiento', d: 'Cuánto producto terminado sale por kilo de materia prima. En el piloto ≈27,5% (el resto es pérdida de masa: secado, separaciones).' },
  { t: 'Cuello de botella', d: 'El equipo más lento de la línea; limita cuánto puede producir toda la planta (hoy: la prensa, 25 kg/h).' },
  { t: 'MMPP', d: 'Materia Prima: el subproducto agroindustrial que entra (Tomasa, Orujo, Alperujo, Pomasa).' },
  { t: 'SKU', d: 'Cada producto vendible: harina animal básica/premium, ingrediente humano, nutracéutico. Mismo costo de proceso, distinto precio.' },
  { t: 'PD / PROVISORIO / VALIDADO', d: 'Nivel de un dato: PD = estimación sin respaldo · PROVISORIO = con benchmark · VALIDADO = cotización o medición real.' },
  { t: 'DSCR / LLCR', d: 'Ratios de bancabilidad: capacidad de pagar la deuda. DSCR > 1,3 = bancable para un banco.' },
  { t: 'LCA', d: 'Life Cycle Assessment: análisis de huella de carbono de todo el ciclo de vida (base del ESG y los créditos CO₂).' },
  { t: 'Ley REP', d: 'Responsabilidad Extendida del Productor: normativa chilena de economía circular con hitos y metas de valorización.' },
  { t: 'Monte Carlo', d: 'Simulación de miles de escenarios aleatorios para estimar el rango probable de la TIR/VAN, no un solo número.' },
  { t: 'Banda de confianza (p10/p50/p90)', d: 'El rango de un resultado: p50 = valor esperado; p10–p90 = el 80% de los escenarios caen ahí.' },
  { t: 'Exactitud del modelo', d: 'Qué tan firmes son los datos que alimentan el modelo (hoy ~62%). Sube al validar inputs PD; estrecha las bandas.' },
  { t: 'Snapshot', d: 'La foto completa del estado del modelo en un momento, que alimenta el cockpit, el board pack y el LP pack (coherentes).' },
  { t: 'Piloto vs Industrial', d: 'Piloto = la planta real chica (27,5 t/año, prueba tecnología, deficitaria). Industrial = el plan a escala (50k t/año, rentable).' },
];


export default function GuiaPage() {
  const [q, setQ] = useState('');
  const [preview, setPreview] = useState<string | null>(null);
  const [abierta, setAbierta] = useState<string | null>('/simulacion');
  const [printMode, setPrintMode] = useState(false);

  function imprimir() {
    setPrintMode(true);
    setTimeout(() => {
      window.print();
      setTimeout(() => setPrintMode(false), 500);
    }, 400);
  }

  const grupos = useMemo(() => {
    if (!q.trim()) return GUIA;
    const t = q.toLowerCase();
    return GUIA.map((g) => ({
      ...g,
      secciones: g.secciones.filter(
        (s) =>
          s.titulo.toLowerCase().includes(t) ||
          s.queEs.toLowerCase().includes(t) ||
          s.paraQue.toLowerCase().includes(t) ||
          s.funciones.some((f) => f.toLowerCase().includes(t)) ||
          s.parametros.some((p) => p.nombre.toLowerCase().includes(t) || p.efecto.toLowerCase().includes(t)) ||
          s.fuente.toLowerCase().includes(t) ||
          s.reemplazar.toLowerCase().includes(t),
      ),
    })).filter((g) => g.secciones.length > 0);
  }, [q]);

  return (
    <div className="space-y-12">
      {/* Hero */}
      <header className="text-center">
        <p className="text-[13px] font-semibold uppercase tracking-wider text-brand">Guía de usuario</p>
        <h1 className="mt-2 text-[clamp(2rem,4vw,3rem)] font-semibold tracking-apple text-ink">
          Dominá la plataforma
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-lg text-ink-400">
          Cada sección con sus funciones, qué parámetros la influyen, <strong>de dónde salen los datos y cómo
          reemplazarlos</strong> — más una vista previa en vivo. Para que cualquiera del equipo tenga dominio total.
        </p>
        <div className="mx-auto mt-6 flex max-w-xl flex-col items-center gap-3 print:hidden sm:flex-row sm:justify-center">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar función, parámetro o fuente… (ej: arriendo, snapshot, TIR)"
            className="w-full rounded-full border border-ink-200 px-5 py-2.5 text-sm focus:border-brand focus:outline-none"
          />
          <button onClick={imprimir} className="btn-apple shrink-0 text-sm whitespace-nowrap">
            📄 Descargar guía (PDF)
          </button>
        </div>
        <p className="mt-2 text-[12px] text-ink-400 print:hidden">
          "Descargar guía (PDF)" abre el diálogo de impresión con todas las secciones expandidas — elegí "Guardar como PDF".
        </p>
      </header>

      {/* Primeros pasos — onboarding por rol */}
      <section>
        <h2 className="mb-1 text-center text-2xl font-semibold tracking-apple text-ink">¿Primera vez? Empezá por tu rol</h2>
        <p className="mb-6 text-center text-ink-400">Un punto de entrada por persona. En 1 click estás trabajando.</p>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {PRIMEROS_PASOS.map((p) => (
            <Link key={p.href} href={p.href} className="apple-card group flex flex-col items-start transition hover:border-brand/30">
              <span className="text-3xl">{p.emoji}</span>
              <span className="mt-2 text-[12px] font-semibold uppercase tracking-wide text-ink-400">{p.persona}</span>
              <span className="mt-1 font-semibold text-ink group-hover:text-brand">{p.label} →</span>
              <span className="mt-1 text-[13px] text-ink-400">{p.desc}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Cómo funciona */}
      <section className="rounded-appleXl bg-ink-50 p-8">
        <h2 className="mb-6 text-center text-2xl font-semibold tracking-apple text-ink">4 cosas que hacen fácil todo</h2>
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
          {COMO_FUNCIONA.map((c) => (
            <div key={c.titulo} className="rounded-xl bg-white p-5">
              <div className="text-3xl">{c.icono}</div>
              <h3 className="mt-2 font-semibold text-ink">{c.titulo}</h3>
              <p className="mt-1 text-[13px] leading-relaxed text-ink-400">{c.texto}</p>
            </div>
          ))}
        </div>
      </section>

      {/* De dónde vienen los datos */}
      <section className="rounded-appleXl border border-brand/20 bg-brand-50/40 p-8">
        <h2 className="text-2xl font-semibold tracking-apple text-ink">📡 De dónde vienen los datos · cómo reemplazarlos</h2>
        <p className="mt-2 max-w-3xl text-ink-600">
          Todo número de la plataforma sale de una de estas 3 fuentes. Cada sección, más abajo, dice exactamente
          de cuál saca los suyos y cómo cambiarlos por datos reales.
        </p>
        <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-3">
          {FUENTES.map((f) => (
            <div key={f.titulo} className="rounded-xl bg-white p-5">
              <div className="text-3xl">{f.icono}</div>
              <h3 className="mt-2 font-semibold text-ink">{f.titulo}</h3>
              <p className="mt-1 text-[13px] leading-relaxed text-ink-500">{f.texto}</p>
              <p className="mt-2 text-[13px] leading-relaxed text-brand">
                <span className="font-semibold">Reemplazar: </span>{f.comoReemplazar}
              </p>
            </div>
          ))}
        </div>
        <div className="mt-5 rounded-xl bg-white p-4 text-[13px] text-ink-600">
          <span className="font-semibold text-ink">🔄 Cascada: </span>
          editás en su origen (/parametros, /equipos, /plan) → el motor recalcula simulación, costeo, escalas,
          balances y predicción → se refleja coherente en cockpit, board pack, readiness y LP pack.
          Cada dato lleva su nivel: <span className="font-semibold">PD</span> (estimación) ·
          <span className="font-semibold"> PROVISORIO</span> (con respaldo) ·
          <span className="font-semibold"> VALIDADO</span> (cotización/medición real).
        </div>
      </section>

      {/* Secciones por persona */}
      {grupos.map((g) => (
        <section key={g.persona}>
          <div className="mb-5 flex items-baseline gap-3">
            <span className="text-2xl">{g.emoji}</span>
            <h2 className={`text-2xl font-semibold tracking-apple ${g.color}`}>{g.persona}</h2>
          </div>
          <p className="mb-6 max-w-3xl text-ink-500">{g.intro}</p>

          <div className="space-y-4">
            {g.secciones.map((s) => {
              const open = printMode || abierta === s.href || !!q.trim();
              return (
                <div key={s.href} className="overflow-hidden rounded-2xl border border-ink-100 bg-white">
                  {/* Cabecera clickable */}
                  <button
                    onClick={() => {
                      const next = abierta === s.href ? null : s.href;
                      setAbierta(next);
                      setPreview(null); // al abrir se ve la imagen estatica; "Ver en vivo" carga el iframe
                    }}
                    className="flex w-full items-center gap-3 p-5 text-left transition hover:bg-ink-50/40"
                  >
                    <span className="text-2xl">{s.icono}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-bold text-ink">{s.titulo}</h3>
                        <code className="rounded bg-ink-50 px-2 py-0.5 text-[11px] text-ink-400">{s.href}</code>
                      </div>
                      <p className="mt-0.5 text-[13px] text-ink-400">{s.queEs}</p>
                    </div>
                    <span className={`text-ink-300 transition-transform print:hidden ${open ? 'rotate-180' : ''}`}>▾</span>
                  </button>

                  {open && (
                    <div className="grid grid-cols-1 gap-6 border-t border-ink-100 p-6 lg:grid-cols-2">
                      {/* Columna izquierda: detalle */}
                      <div className="space-y-5">
                        <p className="text-[14px] leading-relaxed text-ink-700">
                          <span className="font-semibold text-ink">Para qué: </span>{s.paraQue}
                        </p>

                        <div>
                          <p className="text-[12px] font-semibold uppercase tracking-wide text-ink-400">Funciones</p>
                          <ul className="mt-1.5 space-y-1">
                            {s.funciones.map((f, i) => (
                              <li key={i} className="flex gap-2 text-[14px] text-ink-600">
                                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                                <span>{f}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <p className="text-[12px] font-semibold uppercase tracking-wide text-ink-400">Cómo usarla</p>
                          <ol className="mt-1.5 space-y-1.5">
                            {s.pasos.map((p, i) => (
                              <li key={i} className="flex gap-2.5 text-[14px] text-ink-600">
                                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-50 text-[11px] font-bold text-brand">{i + 1}</span>
                                <span>{p}</span>
                              </li>
                            ))}
                          </ol>
                        </div>

                        {/* Parámetros que influyen */}
                        <div>
                          <p className="text-[12px] font-semibold uppercase tracking-wide text-amber-600">⚙️ Parámetros que influyen · cómo se trabajan</p>
                          <div className="mt-2 overflow-hidden rounded-xl border border-ink-100">
                            <table className="w-full text-[13px]">
                              <thead className="bg-ink-50/50 text-[11px] uppercase text-ink-400">
                                <tr>
                                  <th className="px-3 py-2 text-left">Parámetro</th>
                                  <th className="px-3 py-2 text-left">Se trabaja en</th>
                                  <th className="px-3 py-2 text-left">Efecto</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-ink-50">
                                {s.parametros.map((p, i) => (
                                  <tr key={i} className="align-top">
                                    <td className="px-3 py-2 font-medium text-ink">{p.nombre}</td>
                                    <td className="px-3 py-2 text-ink-500">{p.donde}</td>
                                    <td className="px-3 py-2 text-ink-600">{p.efecto}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>

                        {/* De dónde salen los datos · cómo reemplazarlos */}
                        <div className="rounded-xl border border-brand/15 bg-brand-50/30 p-4">
                          <p className="text-[12px] font-semibold uppercase tracking-wide text-brand">📡 De dónde salen los datos · cómo reemplazarlos</p>
                          <p className="mt-2 text-[13px] leading-relaxed text-ink-700">
                            <span className="font-semibold text-ink">Fuente: </span>{s.fuente}
                          </p>
                          <p className="mt-1.5 text-[13px] leading-relaxed text-ink-700">
                            <span className="font-semibold text-ink">Reemplazar: </span>{s.reemplazar}
                          </p>
                        </div>

                        <div className="flex gap-2">
                          <Link href={s.href} className="btn-apple text-sm">Abrir sección →</Link>
                          <button
                            onClick={() => setPreview(preview === s.href ? null : s.href)}
                            className="btn-apple btn-apple-ghost text-sm"
                          >
                            {preview === s.href ? 'Ocultar preview' : '👁 Ver en vivo'}
                          </button>
                        </div>
                      </div>

                      {/* Columna derecha: imagen estática (instantánea) o preview en vivo */}
                      <div className="min-h-[260px] overflow-hidden rounded-xl border border-ink-100 bg-ink-50/40">
                        {preview === s.href && !printMode ? (
                          <div className="relative h-[360px] overflow-hidden rounded-xl">
                            <iframe
                              src={s.href}
                              title={`Preview ${s.titulo}`}
                              className="absolute left-0 top-0 origin-top-left"
                              style={{ width: '200%', height: '720px', transform: 'scale(0.5)', border: 0 }}
                              loading="lazy"
                            />
                            <Link
                              href={s.href}
                              className="absolute bottom-3 right-3 rounded-full bg-ink/90 px-3 py-1.5 text-[12px] font-medium text-white backdrop-blur transition hover:bg-ink print:hidden"
                            >
                              Abrir página completa →
                            </Link>
                          </div>
                        ) : SCREENSHOTS.has(s.href) ? (
                          <div className="relative">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={`/guia${s.href}.png`}
                              alt={`Captura de ${s.titulo}`}
                              className="w-full rounded-xl border-b border-ink-100"
                              loading="lazy"
                            />
                            <button
                              onClick={() => setPreview(s.href)}
                              className="absolute bottom-3 right-3 rounded-full bg-ink/90 px-3 py-1.5 text-[12px] font-medium text-white backdrop-blur transition hover:bg-ink print:hidden"
                            >
                              ▶ Ver en vivo
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setPreview(s.href)}
                            className="flex h-full min-h-[260px] w-full flex-col items-center justify-center gap-2 text-ink-300 transition hover:text-brand print:hidden"
                          >
                            <span className="text-4xl">{s.icono}</span>
                            <span className="text-sm font-medium">Ver vista previa en vivo</span>
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      ))}

      {grupos.length === 0 && (
        <p className="text-center text-ink-400">Sin resultados para "{q}". Probá otro término.</p>
      )}

      {/* Glosario */}
      <section>
        <h2 className="mb-1 text-2xl font-semibold tracking-apple text-ink">📖 Glosario</h2>
        <p className="mb-5 text-ink-400">Los términos del modelo en palabras simples — para que nadie se pierda con la jerga financiera o técnica.</p>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {GLOSARIO.filter((g) => {
            if (!q.trim()) return true;
            const t = q.toLowerCase();
            return g.t.toLowerCase().includes(t) || g.d.toLowerCase().includes(t);
          }).map((g) => (
            <div key={g.t} className="rounded-xl border border-ink-100 bg-white p-4">
              <div className="text-[14px] font-bold text-brand">{g.t}</div>
              <div className="mt-1 text-[13px] leading-relaxed text-ink-600">{g.d}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA final */}
      <section className="rounded-appleXl bg-brand px-6 py-14 text-center text-white">
        <h2 className="text-2xl font-semibold tracking-apple">¿Listo para empezar?</h2>
        <p className="mx-auto mt-2 max-w-xl text-white/85">
          Abrí el Centro de Mando para ver el estado del negocio, o andá a Parámetros para cargar datos reales.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link href="/comando" className="rounded-full bg-white px-5 py-2.5 text-[14px] font-medium text-brand transition hover:scale-105">
            Ir al Centro de Mando
          </Link>
          <Link href="/parametros" className="rounded-full border border-white/40 bg-white/10 px-5 py-2.5 text-[14px] font-medium text-white transition hover:bg-white/20">
            Editar parámetros
          </Link>
        </div>
      </section>
    </div>
  );
}
