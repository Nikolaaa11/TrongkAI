'use client';

import Image from 'next/image';
import { useMemo, useState } from 'react';

type Estado = 'critico' | 'alta' | 'media' | 'baja' | 'ok';
type Dato = {
  id: string;
  titulo: string;
  descripcion: string;
  estado: Estado;
  categoria: 'operacional' | 'comercial' | 'financiero' | 'regulatorio' | 'esg' | 'equipo';
  responsable: string;
  formato: string;
  impacto: string;
  uplift_score: number; // cuántos puntos sube el readiness score si se recibe
};

const DATOS: Dato[] = [
  // ===== CRÍTICOS =====
  {
    id: 'capacidad-secador',
    titulo: 'Capacidad real del secador',
    descripcion: 'El secador es el cuello de botella declarado. Necesitamos kg/h en régimen pleno.',
    estado: 'critico',
    categoria: 'operacional',
    responsable: 'Jaime · Operaciones',
    formato: 'kg/hora + curva operación',
    impacto: 'Hoy se usa 250 kWh/ton como proxy. Recalcula OpEx + bottleneck.',
    uplift_score: 1.5,
  },
  {
    id: 'descomposicion-mmpp',
    titulo: 'Tiempo descomposición tomasa/pomasa',
    descripcion: 'Ventana segura entre recepción y procesamiento. Define agenda + buffer.',
    estado: 'critico',
    categoria: 'operacional',
    responsable: 'Operaciones + agrónomo',
    formato: 'horas por MMPP',
    impacto: 'Permite definir cámara de frío o pre-procesamiento.',
    uplift_score: 1.0,
  },
  {
    id: 'cotizacion-mmpp',
    titulo: 'Cotización firme MMPP 2026-2027',
    descripcion: 'Oferta firmada de al menos 3 proveedores para validar costo neto.',
    estado: 'critico',
    categoria: 'comercial',
    responsable: 'Sergio · Comercial',
    formato: 'PDF firmado',
    impacto: 'Driver más sensible del modelo. Hoy 30 CLP/kg neto.',
    uplift_score: 2.0,
  },
  {
    id: 'loi-clientes',
    titulo: 'Cartas de intención 2 clientes',
    descripcion: 'LOI firmadas con volumen mínimo y precio referencial. Tracción comercial.',
    estado: 'critico',
    categoria: 'comercial',
    responsable: 'Sergio · Comercial',
    formato: 'LOI PDF firmadas',
    impacto: 'Sin LOI = proyecto teórico. Con LOI = demanda comprobada.',
    uplift_score: 2.5,
  },

  // ===== OPERACIONALES =====
  {
    id: 'rendimiento-mmpp',
    titulo: 'Rendimiento real por MMPP',
    descripcion: 'Validar con muestras reales de tomatera y olivar. Hoy en benchmarks.',
    estado: 'alta',
    categoria: 'operacional',
    responsable: 'Operaciones',
    formato: 'fracción por MMPP',
    impacto: 'Calibra el balance de masa con datos propios.',
    uplift_score: 1.0,
  },
  {
    id: 'opex-real',
    titulo: 'OpEx real mensual operativo',
    descripcion: 'MO + mantención + energía + admin + seguros. Hoy CLP 80M/mes estimado.',
    estado: 'alta',
    categoria: 'financiero',
    responsable: 'Contadora · Finanzas',
    formato: 'Excel mensual desglosado',
    impacto: 'Reemplaza el supuesto OpEx con dato real.',
    uplift_score: 1.0,
  },
  {
    id: 'capex-gantt',
    titulo: 'Cronograma CapEx mensual',
    descripcion: 'Timing real de equipos y obra. Hoy distribuido por año.',
    estado: 'alta',
    categoria: 'financiero',
    responsable: 'Ingeniería + proveedores',
    formato: 'Gantt + cotizaciones',
    impacto: 'Ajusta working capital y necesidad de capital.',
    uplift_score: 0.8,
  },
  {
    id: 'energia-equipo',
    titulo: 'Consumo energético por equipo',
    descripcion: 'Refina LCA y cuenta energía. Hoy genérico.',
    estado: 'media',
    categoria: 'operacional',
    responsable: 'Operaciones',
    formato: 'kWh/ton por equipo',
    impacto: 'Mejora exactitud LCA carbono.',
    uplift_score: 0.5,
  },
  {
    id: 'aprendizaje-real',
    titulo: 'Curva de aprendizaje real',
    descripcion: 'Reducción costo unitario al duplicar volumen. Hoy 90% (Wright).',
    estado: 'media',
    categoria: 'operacional',
    responsable: 'Operaciones + tiempo',
    formato: 'CSV trimestral',
    impacto: 'Confirma o ajusta supuesto food processing.',
    uplift_score: 0.5,
  },
  {
    id: 'mermas',
    titulo: 'Tasa real de mermas y rechazo',
    descripcion: 'QC por SKU. Impacta rendimiento neto.',
    estado: 'media',
    categoria: 'operacional',
    responsable: 'QA / Operaciones',
    formato: '% por SKU',
    impacto: 'Refleja calidad real producto.',
    uplift_score: 0.5,
  },

  // ===== COMERCIALES =====
  {
    id: 'precios-sku',
    titulo: 'Precios firmes 12 SKUs',
    descripcion: 'Cotizaciones reales clientes target. Hoy con descuento nuevo entrante.',
    estado: 'alta',
    categoria: 'comercial',
    responsable: 'Comercial',
    formato: 'CLP/kg + condiciones',
    impacto: 'Driver más sensible. Valida o ajusta TIR.',
    uplift_score: 1.5,
  },
  {
    id: 'dso-dpo',
    titulo: 'Términos DSO/DPO reales',
    descripcion: 'Días cobro clientes / pago proveedores. Hoy 50/35.',
    estado: 'alta',
    categoria: 'financiero',
    responsable: 'Comercial + Finanzas',
    formato: 'días',
    impacto: 'Calibra working capital cíclico.',
    uplift_score: 0.7,
  },
  {
    id: 'termsheet-bancos',
    titulo: 'Term sheets bancarios reales',
    descripcion: 'Tasa, plazo, grace ofrecidos. Hoy 50/50, 10y, 2y grace.',
    estado: 'alta',
    categoria: 'financiero',
    responsable: 'Ricardo · Finanzas',
    formato: 'Term sheet PDF',
    impacto: 'Valida bancabilidad real (DSCR/LLCR).',
    uplift_score: 1.0,
  },
  {
    id: 'comparables-ma',
    titulo: 'Comparables M&A LATAM',
    descripcion: 'Transacciones recientes circular economy LATAM.',
    estado: 'media',
    categoria: 'comercial',
    responsable: 'Banca inversión / asesor',
    formato: 'Lista + valuaciones',
    impacto: 'Valida múltiplo EV/EBITDA 9,63×.',
    uplift_score: 0.5,
  },
  {
    id: 'pipeline-lp',
    titulo: 'Pipeline LPs interesados',
    descripcion: 'Fondos / FOs / DFIs en conversación, con etapa.',
    estado: 'media',
    categoria: 'comercial',
    responsable: 'Nicolás · IR',
    formato: 'CRM o Excel',
    impacto: 'Prioriza roadshow.',
    uplift_score: 0.5,
  },
  {
    id: 'competencia',
    titulo: 'Inteligencia competitiva detallada',
    descripcion: 'Empresas similares LATAM: volumen, precio, market share.',
    estado: 'baja',
    categoria: 'comercial',
    responsable: 'Comercial / investigación',
    formato: 'Brief mercado',
    impacto: 'Posicionamiento y narrativa LP.',
    uplift_score: 0.3,
  },

  // ===== REGULATORIOS / ESG =====
  {
    id: 'certificaciones',
    titulo: 'Avance certificaciones',
    descripcion: 'B-Corp, HACCP, GMP+. Estado + fecha esperada.',
    estado: 'alta',
    categoria: 'regulatorio',
    responsable: 'QA / Compliance',
    formato: 'Checklist + evidencias',
    impacto: 'Permite acceso a mercados premium.',
    uplift_score: 0.8,
  },
  {
    id: 'rca-permisos',
    titulo: 'RCA, RUP, permisos SAG/Seremi',
    descripcion: 'Permisos sanitarios vigentes.',
    estado: 'alta',
    categoria: 'regulatorio',
    responsable: 'Legal / Compliance',
    formato: 'PDFs originales',
    impacto: 'Riesgo regulatorio cuantificado.',
    uplift_score: 0.8,
  },
  {
    id: 'plan-rep',
    titulo: 'Plan respuesta Ley REP firmado',
    descripcion: 'Plan operativo declarado MMA. Hoy 8 hitos genéricos.',
    estado: 'media',
    categoria: 'regulatorio',
    responsable: 'Compliance',
    formato: 'PDF declaración',
    impacto: 'Reemplaza supuestos con declaración real.',
    uplift_score: 0.5,
  },
  {
    id: 'esg-medido',
    titulo: 'Reporte ESG / LCA medido',
    descripcion: 'Si hay consultor LCA midiendo huella real.',
    estado: 'media',
    categoria: 'esg',
    responsable: 'ESG officer',
    formato: 'PDF + datos brutos',
    impacto: 'Valida o ajusta carbono negativo declarado.',
    uplift_score: 0.5,
  },

  // ===== EQUIPO =====
  {
    id: 'cvs-equipo',
    titulo: 'CVs y bios actualizadas',
    descripcion: 'Nicolás, Jaime, Sergio, directorio, advisors.',
    estado: 'media',
    categoria: 'equipo',
    responsable: 'Cada uno',
    formato: 'PDF + foto profesional',
    impacto: 'Necesario para pitch deck y data room.',
    uplift_score: 0.3,
  },
  {
    id: 'alianzas',
    titulo: 'Alianzas y proveedores estratégicos',
    descripcion: 'MOUs con universidades, distribuidores, asesores.',
    estado: 'baja',
    categoria: 'equipo',
    responsable: 'Partnerships',
    formato: 'MOUs PDF',
    impacto: 'Credibilidad institucional.',
    uplift_score: 0.3,
  },
];

const SCORE_ACTUAL = 84.7;

const ESTADO_COLOR: Record<Estado, string> = {
  critico: 'bg-red-50 text-red-600 ring-red-200',
  alta: 'bg-orange-50 text-orange-600 ring-orange-200',
  media: 'bg-yellow-50 text-yellow-700 ring-yellow-200',
  baja: 'bg-brand-50 text-brand ring-brand/20',
  ok: 'bg-brand-50 text-brand ring-brand/20',
};

const ESTADO_LABEL: Record<Estado, string> = {
  critico: 'Crítico',
  alta: 'Alta',
  media: 'Media',
  baja: 'Baja',
  ok: 'Recibido',
};

export default function DatosPage() {
  const [recibidos, setRecibidos] = useState<Set<string>>(new Set());
  const [filtro, setFiltro] = useState<'todos' | Estado>('todos');

  const scoreProyectado = useMemo(() => {
    const uplift = DATOS.filter((d) => recibidos.has(d.id)).reduce((s, d) => s + d.uplift_score, 0);
    return Math.min(100, SCORE_ACTUAL + uplift);
  }, [recibidos]);

  const datosFiltrados = useMemo(() => {
    if (filtro === 'todos') return DATOS;
    return DATOS.filter((d) => d.estado === filtro);
  }, [filtro]);

  const upliftTotal = DATOS.reduce((s, d) => s + d.uplift_score, 0);

  const toggleRecibido = (id: string) => {
    setRecibidos((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const stats = {
    critico: DATOS.filter((d) => d.estado === 'critico').length,
    alta: DATOS.filter((d) => d.estado === 'alta').length,
    media: DATOS.filter((d) => d.estado === 'media').length,
    baja: DATOS.filter((d) => d.estado === 'baja').length,
  };

  return (
    <div className="space-y-12">
      {/* Hero */}
      <header className="flex items-start gap-4">
        <Image src="/icon-trongkai.png" alt="Trongkai" width={56} height={56} priority className="shrink-0" />
        <div className="flex-1">
          <h1 className="font-serif text-3xl text-ink">Datos que necesita la plataforma</h1>
          <p className="mt-2 text-sm text-ink-400">
            Checklist interno de información pendiente. Cada dato que llega reemplaza un supuesto PD
            por un dato real y sube el Investment Readiness Score.
          </p>
        </div>
      </header>

      {/* Score proyectado */}
      <section className="rounded-appleXl bg-brand-50 p-8 ring-1 ring-brand/20">
        <div className="flex flex-col items-center gap-6 md:flex-row md:items-baseline md:justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
              Score actual del proyecto
            </div>
            <div className="mt-2 flex items-baseline gap-3">
              <div className="tabular text-6xl font-semibold text-ink">{SCORE_ACTUAL.toFixed(1)}</div>
              <div className="text-2xl text-ink-400">/ 100</div>
            </div>
            <div className="mt-1 text-sm text-ink-600">BANKABLE — listo para LP roadshow</div>
          </div>
          <div className="text-center md:text-right">
            <div className="text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
              Score proyectado con datos recibidos
            </div>
            <div className="mt-2 flex items-baseline justify-end gap-3">
              <div className="tabular text-6xl font-semibold text-brand">
                {scoreProyectado.toFixed(1)}
              </div>
              <div className="text-2xl text-ink-400">/ 100</div>
            </div>
            <div className="mt-1 text-sm text-ink-600">
              {recibidos.size} de {DATOS.length} datos · uplift máximo {upliftTotal.toFixed(1)} pts
            </div>
          </div>
        </div>

        {/* Barra */}
        <div className="mt-6">
          <div className="relative h-3 w-full overflow-hidden rounded-full bg-white">
            <div
              className="absolute h-full bg-ink-200 transition-all"
              style={{ width: `${SCORE_ACTUAL}%` }}
            />
            <div
              className="absolute h-full bg-gradient-to-r from-brand to-brand-700 transition-all"
              style={{ width: `${scoreProyectado}%` }}
            />
          </div>
        </div>
      </section>

      {/* Filtros */}
      <section className="flex flex-wrap items-center gap-2">
        <FiltroBtn label="Todos" count={DATOS.length} active={filtro === 'todos'} onClick={() => setFiltro('todos')} />
        <FiltroBtn label="Crítico" count={stats.critico} active={filtro === 'critico'} onClick={() => setFiltro('critico')} tone="red" />
        <FiltroBtn label="Alta" count={stats.alta} active={filtro === 'alta'} onClick={() => setFiltro('alta')} tone="orange" />
        <FiltroBtn label="Media" count={stats.media} active={filtro === 'media'} onClick={() => setFiltro('media')} tone="yellow" />
        <FiltroBtn label="Baja" count={stats.baja} active={filtro === 'baja'} onClick={() => setFiltro('baja')} tone="brand" />
      </section>

      {/* Lista de datos */}
      <section className="space-y-3">
        {datosFiltrados.map((d) => {
          const recibido = recibidos.has(d.id);
          return (
            <div
              key={d.id}
              className={`apple-card cursor-pointer ${recibido ? 'bg-brand-50 ring-1 ring-brand/30' : ''}`}
              onClick={() => toggleRecibido(d.id)}
            >
              <div className="flex items-start gap-4">
                <button
                  type="button"
                  className={`mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 transition ${
                    recibido
                      ? 'border-brand bg-brand text-white'
                      : 'border-ink-200 bg-white hover:border-ink-400'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleRecibido(d.id);
                  }}
                >
                  {recibido && <span className="text-xs font-bold">✓</span>}
                </button>
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className={`font-semibold text-ink ${recibido ? 'line-through opacity-60' : ''}`}>
                      {d.titulo}
                    </h3>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ring-1 ${ESTADO_COLOR[d.estado]}`}
                    >
                      {ESTADO_LABEL[d.estado]}
                    </span>
                    <span className="rounded-full bg-ink-50 px-2 py-0.5 text-[10px] font-medium text-ink-600">
                      {d.categoria}
                    </span>
                    {d.uplift_score > 0 && (
                      <span className="ml-auto text-[12px] font-medium text-brand">
                        +{d.uplift_score.toFixed(1)} pts
                      </span>
                    )}
                  </div>
                  <p className={`mt-1 text-sm ${recibido ? 'text-ink-400' : 'text-ink-600'}`}>
                    {d.descripcion}
                  </p>
                  <div className="mt-3 grid grid-cols-1 gap-2 border-t border-ink-100 pt-3 text-xs md:grid-cols-3">
                    <div>
                      <span className="font-semibold uppercase tracking-wider text-ink-400">Responsable</span>
                      <div className="mt-0.5 text-ink-600">{d.responsable}</div>
                    </div>
                    <div>
                      <span className="font-semibold uppercase tracking-wider text-ink-400">Formato esperado</span>
                      <div className="mt-0.5 text-ink-600">{d.formato}</div>
                    </div>
                    <div>
                      <span className="font-semibold uppercase tracking-wider text-ink-400">Impacto</span>
                      <div className="mt-0.5 text-ink-600">{d.impacto}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </section>

      {/* Cómo mandar */}
      <section className="rounded-appleXl bg-ink-50 p-8">
        <h2 className="font-semibold tracking-apple text-ink text-2xl">¿Cómo nos mandas estos datos?</h2>
        <p className="mt-2 text-sm text-ink-400">3 formas simples. Elige la que más te acomode.</p>
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="apple-card text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand">📧</div>
            <h3 className="font-semibold text-ink">Por mail</h3>
            <p className="mt-1 text-xs text-ink-400">Adjunto con asunto <code className="text-brand">[DATOS-TRONGKAI]</code></p>
            <a href="mailto:nicolasrietta@gmail.com?subject=%5BDATOS-TRONGKAI%5D" className="mt-3 block text-xs font-medium text-brand">nicolasrietta@gmail.com</a>
          </div>
          <div className="apple-card text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand">📂</div>
            <h3 className="font-semibold text-ink">Carpeta compartida</h3>
            <p className="mt-1 text-xs text-ink-400">Drive, OneDrive, WhatsApp</p>
            <div className="mt-3 text-xs font-medium text-brand">Carpeta contexto/</div>
          </div>
          <div className="apple-card text-center">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand">💬</div>
            <h3 className="font-semibold text-ink">Reunión 15 min</h3>
            <p className="mt-1 text-xs text-ink-400">Si requiere explicación</p>
            <div className="mt-3 text-xs font-medium text-brand">Calendly o WhatsApp</div>
          </div>
        </div>
      </section>

      {/* Cadencia */}
      <section>
        <h2 className="font-semibold tracking-apple text-ink text-2xl">Cadencia ideal</h2>
        <p className="mt-2 text-sm text-ink-400">Para que el modelo refleje la realidad sin ser una carga.</p>
        <div className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <CadenciaCard freq="Diario" what="Macro (auto) · Bug fixes" />
          <CadenciaCard freq="Semanal" what="Pipeline LPs · Status comercial" />
          <CadenciaCard freq="Mensual" what="OpEx real · Compliance · Certificaciones" />
          <CadenciaCard freq="Quarterly" what="Cotizaciones · CapEx Gantt · Aprendizaje" />
        </div>
      </section>
    </div>
  );
}

function FiltroBtn({
  label, count, active, onClick, tone,
}: { label: string; count: number; active: boolean; onClick: () => void; tone?: 'red' | 'orange' | 'yellow' | 'brand' }) {
  const activeColor =
    tone === 'red' ? 'bg-red-50 text-red-600 ring-red-200' :
    tone === 'orange' ? 'bg-orange-50 text-orange-600 ring-orange-200' :
    tone === 'yellow' ? 'bg-yellow-50 text-yellow-700 ring-yellow-200' :
    tone === 'brand' ? 'bg-brand-50 text-brand ring-brand/20' :
    'bg-ink text-white';

  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
        active ? `ring-1 ${activeColor}` : 'text-ink-600 hover:bg-ink-50'
      }`}
    >
      {label} <span className="ml-1 text-xs opacity-70">({count})</span>
    </button>
  );
}

function CadenciaCard({ freq, what }: { freq: string; what: string }) {
  return (
    <div className="apple-card text-center">
      <div className="text-2xl font-semibold text-brand">{freq}</div>
      <div className="mt-1 text-xs text-ink-600">{what}</div>
    </div>
  );
}
