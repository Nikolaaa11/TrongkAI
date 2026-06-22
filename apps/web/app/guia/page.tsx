'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

type Seccion = {
  href: string;
  titulo: string;
  icono: string;
  queEs: string;
  paraQue: string;
  pasos: string[];
};

type Grupo = {
  persona: string;
  emoji: string;
  color: string;
  intro: string;
  secciones: Seccion[];
};

const GUIA: Grupo[] = [
  {
    persona: 'Directorio',
    emoji: '🎯',
    color: 'text-brand',
    intro: 'La vista ejecutiva: el estado del negocio, el plan a 5 años y las decisiones a tomar — todo en vivo.',
    secciones: [
      {
        href: '/comando', titulo: 'Centro de Mando', icono: '⚡',
        queEs: 'El cockpit ejecutivo: todo el estado del proyecto en una sola pantalla, recalculado en vivo desde el motor.',
        paraQue: 'Para saber en 30 segundos cómo está el negocio: readiness, TIR, VAN, alertas, qué cambió desde ayer y cuál es la próxima acción recomendada.',
        pasos: [
          'Mirá la fila de KPIs grandes arriba: Readiness, TIR, VAN, EV exit.',
          'Revisá el banner "Qué cambió" para ver los movimientos desde el último snapshot.',
          'Leé la "Próxima acción recomendada" (la sugiere el Decision Engine) y las alertas activas.',
          'Usá "↻ Refresh" para traer el estado más reciente.',
        ],
      },
      {
        href: '/plan', titulo: 'Plan 5 años', icono: '📈',
        queEs: 'El modelo financiero industrial completo: EERR mensual a 60 meses, TIR, VAN, payback y tornado de sensibilidades.',
        paraQue: 'Para defender el caso de inversión ante el directorio y bancos con números trazables.',
        pasos: [
          'Revisá los KPIs del plan (TIR, VAN, payback) arriba.',
          'Bajá al tornado para ver qué variables mueven más la TIR.',
          'Exportá a Excel con el botón de descarga para llevar el modelo a una reunión.',
        ],
      },
      {
        href: '/dashboard-directorio', titulo: 'Board Pack', icono: '🖨',
        queEs: 'Versión imprimible del plan para reunión de directorio: escenarios, valuación con rango, Monte Carlo y ESG.',
        paraQue: 'Para imprimir o exportar a PDF el material de la reunión mensual del board.',
        pasos: [
          'Revisá la tabla de los 3 escenarios estratégicos (el RECOMENDADO está marcado).',
          'Usá "🖨 Imprimir" para generar el board pack, o "Tearsheet PDF" para la versión de una página.',
        ],
      },
      {
        href: '/riesgo', titulo: 'Riesgo Integrado', icono: '⚠️',
        queEs: 'El análisis de riesgo lado a lado: Monte Carlo financiero, escenarios climáticos y riesgo regulatorio REP.',
        paraQue: 'Para entender cuán robusto es el plan ante sequías, heladas y shocks de precio/costo.',
        pasos: [
          'Compará la TIR con y sin riesgo climático.',
          'Mirá la probabilidad de que la TIR supere el WACC (robustez del caso).',
        ],
      },
      {
        href: '/decisiones', titulo: 'Decision Engine', icono: '🧭',
        queEs: 'Las 5 acciones priorizadas que más mejoran el proyecto, calculadas cruzando todas las matrices.',
        paraQue: 'Para saber dónde poner el foco esta semana con mayor retorno.',
        pasos: [
          'Leé el top-5 ordenado por impacto (uplift de readiness) y facilidad (quick-win).',
          'Cada acción dice quién es el dueño y qué hacer concretamente.',
        ],
      },
    ],
  },
  {
    persona: 'Operación',
    emoji: '🏭',
    color: 'text-blue-600',
    intro: 'La planta: simular producción y costos, ver el proceso por etapas, editar los parámetros reales.',
    secciones: [
      {
        href: '/planta', titulo: 'Planta Visual', icono: '🏭',
        queEs: 'El layout del proceso con fotos reales de los equipos, paso a paso, más el CAPEX por equipo.',
        paraQue: 'Para entender el flujo físico de la planta y cuánto cuesta cada máquina.',
        pasos: [
          'Recorré los 8 pasos del proceso, de recepción a ensacado.',
          'Hacé click en cualquier equipo para ver su ficha técnica.',
          'Bajá al "CAPEX por equipo" para ver la inversión por máquina.',
        ],
      },
      {
        href: '/simulacion', titulo: 'Simulación', icono: '⏱',
        queEs: 'El simulador de producción y OPEX completo por hora/día/mes/año, con estacionalidad de la materia prima.',
        paraQue: 'Para responder "cuánto produce y cuánto cuesta la planta" en cualquier período.',
        pasos: [
          'Elegí el período (hora/día/mes/año) con los tabs.',
          'Ajustá horas/día, días/mes y meses/año con los sliders.',
          'Mirá la "Composición del costo (OPEX completo)": arriendo, mano de obra, energía, agua, flete.',
          'En el timeline mensual, la barra ámbar es el costo fijo y la verde el variable — los meses parados (⚠) igual pagan los fijos.',
        ],
      },
      {
        href: '/balance-integral', titulo: 'Balances', icono: '⚖️',
        queEs: 'Los 4 balances en una vista: producto (masa), energía, agua y RRHH, con score de eficiencia y cross-checks.',
        paraQue: 'Para controlar la operación física y las alarmas (ej: horas extra fuera de norma).',
        pasos: [
          'Mirá el score global de eficiencia arriba.',
          'Revisá cada balance y atendé las alarmas en rojo.',
        ],
      },
      {
        href: '/balance-etapas', titulo: 'Proceso por Etapas', icono: '⚙️',
        queEs: 'Las 11 etapas reales de Agrosphere con throughput, cuello de botella y calibración dinámica.',
        paraQue: 'Para ver dónde se traba la línea y cuánto rinde cada etapa.',
        pasos: [
          'Identificá el cuello de botella (la etapa que limita todo el flujo).',
          'Revisá el yield (rendimiento) de cada etapa.',
        ],
      },
      {
        href: '/costeo', titulo: 'Costeo', icono: '💰',
        queEs: 'El costo en CLP/kg y USD/kg por etapa y por SKU, con desglose por concepto.',
        paraQue: 'Para saber cuánto cuesta producir cada kilo y dónde está el costo.',
        pasos: [
          'Mirá el costo unitario total y su desglose.',
          'Para cambiar los valores que lo alimentan, andá a Parámetros.',
        ],
      },
      {
        href: '/parametros', titulo: 'Parámetros', icono: '🎛',
        queEs: 'El editor de los valores reales de la planta: sueldos, tarifa eléctrica, agua, flete, arriendos.',
        paraQue: 'Para que TODO el modelo se recalcule con datos reales — es el corazón de la calibración.',
        pasos: [
          'Editá el valor que conocés (ej: tarifa eléctrica real).',
          'Guardá: la simulación, el costeo y la predicción se actualizan solos.',
          'Cada valor tiene su nivel: PD (sin validar) → PROVISORIO → VALIDADO.',
        ],
      },
      {
        href: '/equipos', titulo: 'Fichas de Equipos', icono: '🏗',
        queEs: 'Las fichas técnicas editables de cada equipo: proveedor, potencia, capacidad, CAPEX.',
        paraQue: 'Para cargar y mantener los datos reales de cada máquina a medida que llegan del equipo.',
        pasos: [
          'Abrí la ficha del equipo que querés actualizar.',
          'Editá los campos y guardá.',
        ],
      },
    ],
  },
  {
    persona: 'Inversionista',
    emoji: '💼',
    color: 'text-purple-600',
    intro: 'El material para LPs: madurez del proyecto, data room, ESG, compliance y los entregables descargables.',
    secciones: [
      {
        href: '/readiness', titulo: 'Investment Readiness', icono: '💯',
        queEs: 'El score 0-100 de madurez del proyecto para inversión, con histórico y las dimensiones que más pesan.',
        paraQue: 'Para mostrar a un LP cuán listo está el proyecto y qué falta para subir el puntaje.',
        pasos: [
          'Mirá el score global y su interpretación.',
          'Revisá qué dimensión pesa más y andá a Decisiones para subirla.',
        ],
      },
      {
        href: '/data-room', titulo: 'Data Room', icono: '🗂',
        queEs: 'El checklist de due diligence (41 ítems) organizado por categoría, con % de avance.',
        paraQue: 'Para preparar la sala de datos antes de un proceso de inversión.',
        pasos: [
          'Revisá el % de avance por categoría.',
          'Completá los ítems pendientes para subir el readiness.',
        ],
      },
      {
        href: '/carbono', titulo: 'Carbono / ESG', icono: '🌿',
        queEs: 'El análisis de huella de carbono (LCA, 3 escenarios) y el revenue potencial por créditos de CO₂.',
        paraQue: 'Para el pitch a fondos ESG: el proyecto es carbono-negativo.',
        pasos: [
          'Mirá las emisiones netas a 5 años (evitadas vs vertedero).',
          'Revisá el revenue por créditos de carbono.',
        ],
      },
      {
        href: '/compliance', titulo: 'Compliance REP', icono: '📜',
        queEs: 'El timeline de la Ley REP con hitos, severidad y costo, más obligaciones de la Hoja de Ruta 2040.',
        paraQue: 'Para demostrar que el proyecto cumple la normativa de economía circular.',
        pasos: [
          'Revisá los próximos hitos regulatorios y sus fechas.',
          'Atendé los que tengan vencimiento cercano.',
        ],
      },
      {
        href: '/lp-pack', titulo: 'LP Pack', icono: '📦',
        queEs: 'El centro de descargas: tearsheet PDF, ZIP completo con todos los entregables, JSON de datos.',
        paraQue: 'Para enviar a un inversionista todo el material en un click.',
        pasos: [
          'Descargá el LP Pack ZIP completo, o solo el tearsheet PDF.',
          'Todo se genera en vivo con los datos del momento.',
        ],
      },
      {
        href: '/pipeline-lp', titulo: 'Pipeline LP', icono: '🤝',
        queEs: 'El CRM de inversionistas en roadshow: etapa, monto, próximo paso de cada LP.',
        paraQue: 'Para gestionar el fundraising y no perder ningún follow-up.',
        pasos: [
          'Movés cada LP por las etapas del pipeline.',
          'Registrás montos y próximos pasos.',
        ],
      },
    ],
  },
  {
    persona: 'Análisis',
    emoji: '📊',
    color: 'text-amber-600',
    intro: 'Las herramientas para explorar el modelo: simulaciones what-if, sensibilidad, escalas y financiamiento.',
    secciones: [
      {
        href: '/escalas', titulo: 'Escalas', icono: '🚀',
        queEs: 'La comparación piloto vs industrial (x10, x50, x100) con costo unitario, margen, CAPEX y payback por escala.',
        paraQue: 'Para ver la tesis central: el piloto prueba tecnología; la rentabilidad llega a escala con el SKU correcto.',
        pasos: [
          'Cambiá el SKU arriba (harina, ingrediente humano, nutracéutico).',
          'Mirá la tabla "¿Desde qué escala paga cada SKU?": nutracéutico desde x10, harinas nunca.',
          'Revisá el costo unitario bajando con la curva de aprendizaje.',
        ],
      },
      {
        href: '/whatif-live', titulo: 'What-if Live', icono: '🎚',
        queEs: 'Sliders en vivo de precio, costo, WACC y OPEX que recalculan TIR y VAN al instante.',
        paraQue: 'Para responder "¿qué pasa si...?" en segundos durante una reunión.',
        pasos: [
          'Movés cualquier slider y los KPIs se actualizan al instante.',
          'Probás combinaciones para encontrar el punto de equilibrio.',
        ],
      },
      {
        href: '/sensitivity', titulo: 'Sensibilidad', icono: '🌡',
        queEs: 'Heatmap 2D (precio × costo), break-even por driver y curvas de TIR por variable.',
        paraQue: 'Para entender a qué es más sensible el proyecto y cuál es el precio mínimo viable.',
        pasos: [
          'Leé el heatmap: verde = TIR sobre el hurdle, rojo = bajo.',
          'Revisá el break-even (precio mínimo para TIR = WACC).',
        ],
      },
      {
        href: '/inteligencia', titulo: 'Inteligencia', icono: '🧠',
        queEs: 'La síntesis cross-modular: insights, exactitud del modelo y predicción con bandas de confianza.',
        paraQue: 'Para saber cuán confiable es el modelo (hoy ~62%) y qué validar primero para mejorarlo.',
        pasos: [
          'Mirá la exactitud del modelo y los insights priorizados.',
          'Revisá la predicción con bandas (rango p10–p90) y el ranking de qué validar.',
        ],
      },
      {
        href: '/financiamiento', titulo: 'Financiamiento', icono: '🏦',
        queEs: 'El mix deuda/equity con DSCR, LLCR, escudo fiscal y TIR del equity.',
        paraQue: 'Para estructurar el financiamiento antes de un pitch a bancos o CORFO.',
        pasos: [
          'Ajustá el mix deuda/equity.',
          'Verificá que el DSCR sea bancable (>1.3) y mirá la TIR del equity.',
        ],
      },
    ],
  },
];

const COMO_FUNCIONA = [
  { icono: '🧭', titulo: 'Navegá por tu rol', texto: 'El menú de arriba está organizado por persona: Directorio, Operación, Inversionista, Análisis y Sistema. Buscá tu grupo y vas directo a lo tuyo.' },
  { icono: '⌘', titulo: 'Buscá con ⌘K', texto: 'Presioná ⌘K (Mac) o Ctrl+K (Windows) en cualquier momento para saltar a cualquier página escribiendo su nombre.' },
  { icono: '◍', titulo: 'Confiá en los datos', texto: 'Los números clave muestran su calidad: PD (sin validar), PROVISORIO o VALIDADO. El badge de "exactitud del modelo" te dice qué tan firme es cada predicción.' },
  { icono: '🔗', titulo: 'Seguí los hilos', texto: 'Al pie de cada página, el bloque "Conectado con" te lleva del número a sus supuestos, su desglose y su banda de confianza en un click.' },
];

export default function GuiaPage() {
  const [q, setQ] = useState('');
  const [preview, setPreview] = useState<string | null>(null);

  const grupos = useMemo(() => {
    if (!q.trim()) return GUIA;
    const t = q.toLowerCase();
    return GUIA.map((g) => ({
      ...g,
      secciones: g.secciones.filter(
        (s) => s.titulo.toLowerCase().includes(t) || s.queEs.toLowerCase().includes(t) || s.paraQue.toLowerCase().includes(t),
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
          Qué hace cada sección, para qué sirve y cómo usarla — con una vista previa en vivo de cada pantalla.
          Pensada para que cualquiera del equipo arranque en minutos.
        </p>
        <div className="mx-auto mt-6 max-w-md">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar una sección… (ej: costo, escalas, LP)"
            className="w-full rounded-full border border-ink-200 px-5 py-2.5 text-sm focus:border-brand focus:outline-none"
          />
        </div>
      </header>

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

      {/* Secciones por persona */}
      {grupos.map((g) => (
        <section key={g.persona}>
          <div className="mb-5 flex items-baseline gap-3">
            <span className="text-2xl">{g.emoji}</span>
            <h2 className={`text-2xl font-semibold tracking-apple ${g.color}`}>{g.persona}</h2>
          </div>
          <p className="mb-6 max-w-3xl text-ink-500">{g.intro}</p>

          <div className="space-y-4">
            {g.secciones.map((s) => (
              <div key={s.href} className="overflow-hidden rounded-2xl border border-ink-100 bg-white">
                <div className="grid grid-cols-1 gap-6 p-6 lg:grid-cols-2">
                  {/* Texto */}
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{s.icono}</span>
                      <h3 className="text-xl font-bold text-ink">{s.titulo}</h3>
                      <code className="rounded bg-ink-50 px-2 py-0.5 text-[11px] text-ink-400">{s.href}</code>
                    </div>
                    <p className="mt-3 text-[15px] leading-relaxed text-ink-700">
                      <span className="font-semibold text-ink">Qué es: </span>{s.queEs}
                    </p>
                    <p className="mt-2 text-[15px] leading-relaxed text-ink-700">
                      <span className="font-semibold text-ink">Para qué: </span>{s.paraQue}
                    </p>
                    <div className="mt-3">
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
                    <div className="mt-4 flex gap-2">
                      <Link href={s.href} className="btn-apple text-sm">Abrir sección →</Link>
                      <button
                        onClick={() => setPreview(preview === s.href ? null : s.href)}
                        className="btn-apple btn-apple-ghost text-sm"
                      >
                        {preview === s.href ? 'Ocultar preview' : '👁 Ver en vivo'}
                      </button>
                    </div>
                  </div>

                  {/* Preview en vivo (lazy) */}
                  <div className="min-h-[260px] rounded-xl border border-ink-100 bg-ink-50/40">
                    {preview === s.href ? (
                      <div className="relative h-[320px] overflow-hidden rounded-xl">
                        <iframe
                          src={s.href}
                          title={`Preview ${s.titulo}`}
                          className="absolute left-0 top-0 origin-top-left"
                          style={{ width: '200%', height: '640px', transform: 'scale(0.5)', border: 0 }}
                          loading="lazy"
                        />
                        <Link
                          href={s.href}
                          className="absolute bottom-3 right-3 rounded-full bg-ink/90 px-3 py-1.5 text-[12px] font-medium text-white backdrop-blur transition hover:bg-ink"
                        >
                          Abrir página completa →
                        </Link>
                      </div>
                    ) : (
                      <button
                        onClick={() => setPreview(s.href)}
                        className="flex h-full min-h-[260px] w-full flex-col items-center justify-center gap-2 text-ink-300 transition hover:text-brand"
                      >
                        <span className="text-4xl">{s.icono}</span>
                        <span className="text-sm font-medium">Ver vista previa en vivo</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      ))}

      {grupos.length === 0 && (
        <p className="text-center text-ink-400">Sin resultados para "{q}". Probá otro término.</p>
      )}

      {/* CTA final */}
      <section className="rounded-appleXl bg-brand px-6 py-14 text-center text-white">
        <h2 className="text-2xl font-semibold tracking-apple">¿Listo para empezar?</h2>
        <p className="mx-auto mt-2 max-w-xl text-white/85">
          Abrí el Centro de Mando para ver el estado del negocio, o presioná ⌘K para buscar cualquier sección.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link href="/comando" className="rounded-full bg-white px-5 py-2.5 text-[14px] font-medium text-brand transition hover:scale-105">
            Ir al Centro de Mando
          </Link>
          <Link href="/mapa" className="rounded-full border border-white/40 bg-white/10 px-5 py-2.5 text-[14px] font-medium text-white transition hover:bg-white/20">
            Ver mapa completo
          </Link>
        </div>
      </section>
    </div>
  );
}
