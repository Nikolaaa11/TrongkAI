// Fuente unica de la documentacion viva de la plataforma.
// La consumen /guia (manual completo) y AyudaSeccion (panel contextual global).
// REGLA: toda pagina nueva agrega su entrada aca -> gana guia + ayuda + busqueda.

export type Param = { nombre: string; donde: string; efecto: string };
export type Seccion = {
  href: string;
  titulo: string;
  icono: string;
  queEs: string;
  paraQue: string;
  funciones: string[];
  pasos: string[];
  parametros: Param[];
  fuente: string;     // de dónde saca los datos (endpoint / módulo / cálculo)
  reemplazar: string; // cómo se reemplazan por datos reales
};
export type Grupo = {
  persona: string;
  emoji: string;
  color: string;
  intro: string;
  secciones: Seccion[];
};

export const GUIA: Grupo[] = [
  {
    persona: 'Directorio',
    emoji: '🎯',
    color: 'text-brand',
    intro: 'La vista ejecutiva: el estado del negocio, el plan a 5 años y las decisiones a tomar — todo en vivo.',
    secciones: [
      {
        href: '/comando', titulo: 'Centro de Mando', icono: '⚡',
        queEs: 'El cockpit ejecutivo: todo el estado del proyecto en una sola pantalla, recalculado en vivo desde el motor (un solo fetch al snapshot).',
        paraQue: 'Para saber en 30 segundos cómo está el negocio y qué hacer hoy.',
        funciones: [
          'KPIs hero: Investment Readiness, TIR proyecto, VAN @18%, EV exit año 5 con MOIC.',
          'Banner "Inteligencia": score global, insights críticos y oportunidades.',
          'Banner "Qué cambió": diff vs el último snapshot (TIR, VAN, score).',
          'Strip de balances en vivo (masa, energía, agua, RRHH) con alarmas.',
          'Simulación operacional: piloto + escalas resumidas.',
          'Próxima acción recomendada (del Decision Engine) con dueño y uplift.',
          'Alertas activas por severidad + barras de progreso (readiness, data room, matriz).',
          'Monte Carlo P5/P50/P95 + prob. TIR>WACC.',
          'Descargas: LP Pack ZIP, Tearsheet PDF, Board Pack imprimible.',
        ],
        pasos: [
          'Leé la fila de KPIs grandes para el pulso general.',
          'Mirá "Qué cambió" para los movimientos desde ayer.',
          'Ejecutá la "Próxima acción recomendada" y revisá alertas.',
          'Usá "↻ Refresh" para el estado más reciente.',
        ],
        parametros: [
          { nombre: 'WACC y supuestos del plan', donde: '/financiamiento · /whatif-live', efecto: 'Mueven la TIR, el VAN y el EV que se muestran arriba.' },
          { nombre: 'Parámetros de planta (arriendo, sueldos, energía…)', donde: '/parametros', efecto: 'Cambian el costo del piloto que aparece en la simulación del cockpit.' },
          { nombre: 'Estado de validación de inputs (PD→VALIDADO)', donde: '/variables · /parametros', efecto: 'Sube el Investment Readiness y baja las alertas de datos.' },
        ],
        fuente: 'GET /api/snapshot — agrega TODO el modelo (plan, valuación, Monte Carlo, balances, simulación, readiness, alertas), cacheado 60s.',
        reemplazar: 'No se edita acá. Cambiá los datos en sus páginas de origen (/parametros, /equipos, /variables, /plan) y el cockpit los toma en el próximo refresh.',
      },
      {
        href: '/plan', titulo: 'Plan 5 años', icono: '📈',
        queEs: 'El modelo financiero industrial completo: EERR mensual a 60 meses, KPIs y tornado de sensibilidades.',
        paraQue: 'Para defender el caso de inversión ante directorio y bancos con números trazables.',
        funciones: [
          'EERR mensual a 60 meses (ingresos, EBITDA, margen, CapEx).',
          'KPIs: TIR proyecto, VAN @WACC, payback, margen EBITDA promedio.',
          'Tornado: ranking de variables que más mueven la TIR.',
          'Ingresos por marca/SKU y resumen anual.',
          'Exportación a Excel formato directorio.',
        ],
        pasos: [
          'Revisá los KPIs del plan arriba.',
          'Bajá al tornado para ver los drivers de la TIR.',
          'Exportá a Excel para llevar el modelo a una reunión.',
        ],
        parametros: [
          { nombre: 'Volumen objetivo (ton/año) y ramp por año', donde: 'modelo industrial (plan_builder)', efecto: 'Escala los ingresos y la curva de llegada a régimen.' },
          { nombre: 'Precios por SKU', donde: '/escalas (selector) · simulación', efecto: 'Define el revenue de cada línea.' },
          { nombre: 'OpEx mensual y CapEx anual', donde: 'modelo industrial', efecto: 'Determinan EBITDA, margen y payback.' },
          { nombre: 'WACC (18%)', donde: '/financiamiento', efecto: 'Tasa de descuento: mueve el VAN y el hurdle de la TIR.' },
        ],
        fuente: 'POST /plan — modelo industrial (módulo plan_builder) con supuestos a 5 años (volumen 50k ton/año, OpEx, CapEx, WACC). Es el universo INDUSTRIAL, distinto del piloto.',
        reemplazar: 'Los supuestos del plan industrial viven en el motor (código). Explorá variantes sin tocar nada en /whatif-live; para valores de mercado reales, el data-hunter (viernes) los propone con fuente para validarlos.',
      },
      {
        href: '/dashboard-directorio', titulo: 'Board Pack', icono: '🖨',
        queEs: 'Versión imprimible del plan para la reunión de directorio, alimentada por el snapshot (misma fuente que el resto).',
        paraQue: 'Para imprimir o exportar a PDF el material del board en un click.',
        funciones: [
          'Tabla de los 3 escenarios estratégicos con el RECOMENDADO marcado.',
          'Valuación exit con rango low / base / high + múltiplo EBITDA + MOIC.',
          'Bandas Monte Carlo P5/P50/P95 y prob. TIR>WACC.',
          'Tornado top-3 + strip ESG / Compliance / Macro.',
          'Botón imprimir y descarga de tearsheet PDF.',
        ],
        pasos: [
          'Revisá la tabla de escenarios (el recomendado va resaltado).',
          'Usá "🖨 Imprimir" para el board pack o "Tearsheet PDF" para la 1 página.',
        ],
        parametros: [
          { nombre: 'Mismos del Plan 5 años', donde: '/plan · /financiamiento', efecto: 'El board pack es solo-lectura del snapshot; cambia cuando cambia el plan.' },
          { nombre: 'Múltiplo EBITDA de salida', donde: 'modelo de valuación', efecto: 'Define el rango de EV exit (low/base/high).' },
        ],
        fuente: 'GET /api/snapshot — exactamente la misma fuente que el Centro de Mando (garantiza que los números coincidan).',
        reemplazar: 'Solo-lectura. Se actualiza al cambiar el plan (/plan), el financiamiento o los parámetros.',
      },
      {
        href: '/riesgo', titulo: 'Riesgo Integrado', icono: '⚠️',
        queEs: 'El análisis de riesgo lado a lado: Monte Carlo financiero, escenarios climáticos y riesgo regulatorio REP.',
        paraQue: 'Para entender cuán robusto es el plan ante sequías, heladas y shocks de precio/costo.',
        funciones: [
          'Monte Carlo financiero (miles de corridas) con bandas de TIR.',
          'Comparación con y sin riesgo climático, lado a lado.',
          'Tornado de sensibilidades + calendario de obligaciones REP.',
          'Probabilidad de TIR>WACC y de VAN>0.',
        ],
        pasos: [
          'Compará la TIR con y sin clima.',
          'Mirá la probabilidad de superar el WACC (robustez del caso).',
        ],
        parametros: [
          { nombre: 'Volatilidades (σ de precio, rendimiento, costo MMPP, OpEx, WACC)', donde: 'config Monte Carlo', efecto: 'Ensanchan o estrechan las bandas P5–P95.' },
          { nombre: 'Escenarios climáticos (prob. e impacto de sequía/granizada/helada)', donde: 'módulo clima', efecto: 'Bajan el rendimiento esperado y la TIR con clima.' },
        ],
        fuente: 'POST /plan/monte-carlo-integrado (financiero + clima) y el calendario de /compliance/rep-calendar. Las distribuciones son supuestos del modelo de riesgo.',
        reemplazar: 'Ajustá volatilidades y escenarios climáticos en los controles de la página; el plan base que se estresa sale de /plan.',
      },
      {
        href: '/decisiones', titulo: 'Decision Engine', icono: '🧭',
        queEs: 'Las 5 acciones priorizadas que más mejoran el proyecto, calculadas cruzando todas las matrices.',
        paraQue: 'Para saber dónde poner el foco esta semana con mayor retorno.',
        funciones: [
          'Top-5 acciones ordenadas por impacto (uplift de readiness).',
          'Quick-win score (facilidad de ejecución) por acción.',
          'Dueño sugerido y acción concreta a realizar.',
          'Recomendación priorizada cross-matriz.',
        ],
        pasos: [
          'Leé el top-5 ordenado por impacto y facilidad.',
          'Ejecutá la #1 (suele ser validar un input PD o completar un ítem de DD).',
        ],
        parametros: [
          { nombre: 'Celdas PD de la matriz', donde: '/variables', efecto: 'Cada celda PD pendiente genera/prioriza una acción.' },
          { nombre: 'Ítems pendientes del data room', donde: '/data-room', efecto: 'Los gaps de DD entran al ranking de acciones.' },
        ],
        fuente: 'GET /decisiones/top — el motor cruza el estado de la matriz de variables, el data room y el break-even para priorizar.',
        reemplazar: 'No se edita: cambia solo cuando validás inputs o completás ítems de DD. El ranking se recalcula con cada cambio.',
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
        funciones: [
          'Recorrido visual de los 8 pasos del proceso con fotos reales.',
          'Ficha emergente por equipo (proveedor, capacidad, potencia).',
          'KPIs: equipos catalogados y potencia total instalada.',
          'Desglose de CAPEX del piloto por equipo (barras ordenadas).',
        ],
        pasos: [
          'Recorré los pasos de recepción a ensacado.',
          'Click en un equipo para ver su ficha.',
          'Bajá al "CAPEX por equipo" para ver la inversión por máquina.',
        ],
        parametros: [
          { nombre: 'Capacidad y potencia de cada equipo', donde: '/equipos', efecto: 'La capacidad define el cuello de botella; la potencia, el consumo eléctrico.' },
          { nombre: 'CAPEX y modalidad (propio vs arriendo)', donde: '/equipos', efecto: 'Los equipos propios suman al CAPEX; los de arriendo (PEF, Tricanter) van por OPEX.' },
        ],
        fuente: 'GET /equipos/fichas (fichas técnicas) + GET /simulacion/capex-piloto. Las fichas y fotos provienen del documento técnico real de la planta de Talca.',
        reemplazar: 'Editá specs, CAPEX y fotos en /equipos; se reflejan acá al instante. Las fotos viven en /public/equipos.',
      },
      {
        href: '/simulacion', titulo: 'Simulación', icono: '⏱',
        queEs: 'El simulador de producción y OPEX completo por hora/día/mes/año, con estacionalidad de la materia prima.',
        paraQue: 'Para responder "cuánto produce y cuánto cuesta la planta" en cualquier período, con cada peso explicado.',
        funciones: [
          'Tabs de período: hora / día / mes / año.',
          'Sliders de operación: horas/día, días/mes, meses/año.',
          'Selector de MMPP principal (aplica estacionalidad).',
          'KPIs: producto total, costo total, costo unitario CLP/kg y USD/kg, kWh.',
          'Detección de cuello de botella de la línea.',
          'Composición del OPEX completo (6 componentes con % del total).',
          'Timeline mensual con costo fijo (ámbar) vs variable (verde) y meses parados marcados ⚠.',
          'Badge de exactitud del modelo + siguiente input a validar.',
        ],
        pasos: [
          'Elegí el período con los tabs.',
          'Ajustá horas/día, días/mes y meses/año con los sliders.',
          'Leé la "Composición del costo" para ver qué pesa más.',
          'En el timeline, fijate que los meses parados (⚠) igual pagan los fijos.',
        ],
        parametros: [
          { nombre: 'Horas/día · días/mes · meses/año', donde: 'sliders en esta página', efecto: 'Definen las horas totales → producto y costos variables (energía, agua, flete).' },
          { nombre: 'MMPP principal', donde: 'selector en esta página', efecto: 'Aplica la curva de estacionalidad al timeline mensual.' },
          { nombre: 'Arriendo PEF + Tricanter', donde: '/parametros', efecto: 'Costo fijo dominante (~52%): se paga los 12 meses calendario.' },
          { nombre: 'Sueldos × dotación', donde: '/parametros', efecto: 'Mano de obra (~30%): fijo mensual con factor de leyes sociales.' },
          { nombre: 'Tarifa eléctrica / agua / flete', donde: '/parametros', efecto: 'Costos variables: escalan con horas y toneladas procesadas.' },
          { nombre: 'Capacidad del cuello de botella (prensa) y yield del proceso', donde: '/equipos · /balance-etapas', efecto: 'Definen cuánto producto terminado sale por período.' },
        ],
        fuente: 'GET /simulacion/planta — combina las fichas de equipos, los parámetros de planta (parametros-planta.json) y la estacionalidad por MMPP. El OPEX se calcula con los 6 componentes reales.',
        reemplazar: 'Los costos se editan en /parametros y las capacidades en /equipos (persisten en el volumen). Los sliders y el selector de esta página son escenarios temporales: NO cambian los datos guardados.',
      },
      {
        href: '/balance-integral', titulo: 'Balances', icono: '⚖️',
        queEs: 'Los 4 balances en una vista: producto (masa), energía, agua y RRHH, con score de eficiencia y cross-checks.',
        paraQue: 'Para controlar la operación física y las alarmas (ej: horas extra fuera de norma).',
        funciones: [
          'Score global de eficiencia operativa.',
          'Balance de masa con cierre ±0.5% por SKU.',
          'Balance de energía: kWh, mix renovable, factor de potencia.',
          'Balance de agua: consumo, recirculación, cumplimiento DGA.',
          'Balance de RRHH: horas por trabajador con alarma de horas extra (CT Chile).',
          'Cross-checks entre balances + alarmas en rojo.',
        ],
        pasos: [
          'Mirá el score global arriba.',
          'Atendé cualquier alarma en rojo (típicamente RRHH o agua).',
        ],
        parametros: [
          { nombre: 'Rendimiento por MMPP', donde: '/balance-etapas', efecto: 'Cierra el balance de masa y el yield.' },
          { nombre: 'Mix renovable y factor de potencia', donde: '/parametros (energía)', efecto: 'Ajustan el balance energético y su costo.' },
          { nombre: 'Horas asignadas por trabajador', donde: '/balance-rrhh (editable)', efecto: 'Si superan el límite legal, salta la alarma de horas extra.' },
        ],
        fuente: 'GET /balance/integrado — consolida los 4 balances (módulos mass_balance, energia, agua, rrhh) con sus cross-checks.',
        reemplazar: 'RRHH es editable (asignar horas) en /balance-rrhh. Energía/agua/masa salen de /parametros y de los rendimientos por etapa.',
      },
      {
        href: '/balance-etapas', titulo: 'Proceso por Etapas', icono: '⚙️',
        queEs: 'Las 11 etapas reales de Agrosphere con throughput, cuello de botella y calibración dinámica.',
        paraQue: 'Para ver dónde se traba la línea y cuánto rinde cada etapa.',
        funciones: [
          'Las 11 etapas con su throughput (kg/h) y tiempo.',
          'Identificación del cuello de botella de la línea.',
          'Yield (rendimiento de masa) por etapa.',
          'Datos faltantes por etapa señalados.',
        ],
        pasos: [
          'Identificá la etapa cuello de botella (limita todo el flujo).',
          'Revisá el yield acumulado hasta producto terminado (~27.5%).',
        ],
        parametros: [
          { nombre: 'Capacidad de cada equipo por etapa', donde: '/equipos', efecto: 'La etapa más lenta define el throughput de toda la planta.' },
          { nombre: 'Humedad de la MMPP', donde: '/parametros (humedades)', efecto: 'Afecta el rendimiento del secado y el yield final.' },
        ],
        fuente: 'GET /balance/etapas — las 11 etapas con datos del Excel "Etapas X Costeo Agrosphere" + capacidades de las fichas de equipos.',
        reemplazar: 'Cambiás capacidades en /equipos y humedades en /parametros; el throughput y el cuello de botella se recalculan.',
      },
      {
        href: '/costeo', titulo: 'Costeo', icono: '💰',
        queEs: 'El costo en CLP/kg y USD/kg por etapa y por SKU, con desglose por concepto.',
        paraQue: 'Para saber cuánto cuesta producir cada kilo y dónde está el costo.',
        funciones: [
          'Costo unitario CLP/kg y USD/kg por SKU.',
          'Desglose por concepto (energía, mano de obra, agua, flete, arriendo).',
          'Comparativo de 5 rutas saco vs maxisaco (canon del equipo 03-jul-2026): el maxisaco ahorra ~90M CLP/mes.',
          'Chip de nivel de dato (PD/PROVISORIO) junto al costo unitario — click lleva a /variables.',
          'Flete de MMPP de entrada y de despacho de salida.',
          'Costo por etapa del proceso.',
        ],
        pasos: [
          'Mirá el costo unitario total y su desglose.',
          'Para cambiar los valores que lo alimentan, andá a /parametros.',
        ],
        parametros: [
          { nombre: 'Todos los parámetros de planta', donde: '/parametros', efecto: 'Sueldos, energía, agua, flete y arriendos arman el costo CLP/kg.' },
          { nombre: 'USD/CLP de referencia', donde: '/parametros', efecto: 'Convierte el costo a USD/kg.' },
          { nombre: 'Packaging (saco 3.000 vs maxisaco 10.000 CLP)', donde: 'what-if en GET /costos/procesos', efecto: 'El saco 25 kg es el 69% del costo de su ruta: decisión comercial n.°1.' },
        ],
        fuente: 'GET /costeo/etapas (parámetros vivos) + GET /costos/procesos (réplica canónica del Excel del equipo, 12 etapas y rutas saco/maxisaco).',
        reemplazar: 'Editá cualquier tarifa o sueldo en /parametros y el costeo se recalcula al instante.',
      },
      {
        href: '/parametros', titulo: 'Parámetros', icono: '🎛',
        queEs: 'El editor de los valores reales de la planta. Es el ORIGEN: cambiar acá recalcula simulación, costeo, escalas y predicción.',
        paraQue: 'Para calibrar el modelo con datos reales — el corazón de la exactitud.',
        funciones: [
          'Editar la planilla de sueldos (8 cargos × factor leyes sociales 1.35).',
          'Tarifa eléctrica (punta / resto / promedio).',
          'Calor residual La Gloria (fee de servicio).',
          'Tarifas de agua (pozo industrial, alcantarillado, recirculada, DGA).',
          'Flete (CLP/km, distancias MMPP y despacho, capacidad camión).',
          'Arriendos (PEF, Tricanter, otros).',
          'Pérdida de MMPP global, USD/CLP y humedades por MMPP.',
          'Cada valor muestra y permite subir su nivel: PD → PROVISORIO → VALIDADO.',
        ],
        pasos: [
          'Editá el valor que conocés (ej: tarifa eléctrica real de la cuenta).',
          'Guardá: simulación, costeo, escalas y predicción se actualizan solos.',
          'Marcá el nivel del dato según su respaldo (cotización = VALIDADO).',
        ],
        parametros: [
          { nombre: 'Sueldos', donde: 'esta página', efecto: 'Mano de obra del OPEX (≈30% del costo del piloto).' },
          { nombre: 'Arriendos PEF/Tricanter', donde: 'esta página', efecto: 'Costo fijo dominante (≈52%); driver #2 de incertidumbre.' },
          { nombre: 'Energía / agua / flete', donde: 'esta página', efecto: 'Costos variables del proceso.' },
          { nombre: 'Nivel de cada dato (PD/PROV/VALIDADO)', donde: 'esta página', efecto: 'Sube la exactitud del modelo y estrecha las bandas de predicción.' },
        ],
        fuente: 'GET /parametros — los valores se guardan en parametros-planta.json, persistido en el volumen de Fly (/data). Los valores iniciales (seed) son estimaciones de mercado (PD) hasta validarse.',
        reemplazar: 'ACÁ se reemplazan los datos del piloto, sin tocar código: editás el valor, "Guardar" lo escribe en el volumen, y marcás su nivel (PD/PROVISORIO/VALIDADO según el respaldo).',
      },
      {
        href: '/equipos', titulo: 'Fichas de Equipos', icono: '🏗',
        queEs: 'Las fichas técnicas editables de cada equipo: proveedor, potencia, capacidad, CAPEX.',
        paraQue: 'Para cargar y mantener los datos reales de cada máquina a medida que llegan del equipo.',
        funciones: [
          'Ficha por equipo: proveedor, modelo, capacidad kg/h, potencia kW.',
          'CAPEX, modalidad (propio / arriendo / leasing) y nivel de dato.',
          'Foto del equipo y notas técnicas.',
          'Edición y guardado de cada campo.',
        ],
        pasos: [
          'Abrí la ficha del equipo a actualizar.',
          'Editá los campos (capacidad, potencia, CAPEX) y guardá.',
        ],
        parametros: [
          { nombre: 'Capacidad (kg/h)', donde: 'esta página', efecto: 'Define el cuello de botella de la línea.' },
          { nombre: 'Potencia (kW)', donde: 'esta página', efecto: 'Define el consumo eléctrico y el costo de energía.' },
          { nombre: 'Arriendo mensual (si OPEX)', donde: 'esta página', efecto: 'Alimenta el costo fijo de arriendo del OPEX.' },
        ],
        fuente: 'GET /equipos/fichas — guardado en fichas-equipos.json (volumen Fly). Cargado del documento técnico real de la planta piloto de Talca.',
        reemplazar: 'Editás cada ficha en esta página y "Guardar" lo persiste en el volumen. A medida que el equipo manda specs reales, las actualizás acá.',
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
        funciones: [
          'Score global 0-100 con interpretación.',
          '10 dimensiones con su aporte al score.',
          'Histórico (timeline) de cómo evolucionó.',
          'Uplift potencial y marcado de hitos.',
        ],
        pasos: [
          'Mirá el score y su interpretación.',
          'Identificá la dimensión que más pesa y andá a /decisiones para subirla.',
        ],
        parametros: [
          { nombre: 'Validación de inputs (PD→VALIDADO)', donde: '/parametros · /variables', efecto: 'Cada validación sube la dimensión de calidad de datos.' },
          { nombre: 'Avance del data room', donde: '/data-room', efecto: 'Completar ítems sube la dimensión de DD.' },
          { nombre: 'KPIs financieros', donde: '/plan', efecto: 'TIR/VAN/DSCR alimentan la dimensión de retorno y bancabilidad.' },
        ],
        fuente: 'GET /readiness/score — 10 dimensiones ponderadas (retorno, datos, DD, ESG, compliance…). El histórico sale de los snapshots (POST /readiness/snapshot del pulso diario).',
        reemplazar: 'No se edita directo: sube al validar inputs (/parametros, /variables) y completar el data room. El pulso diario registra un snapshot para el histórico.',
      },
      {
        href: '/data-room', titulo: 'Data Room', icono: '🗂',
        queEs: 'El checklist de due diligence (41 ítems) organizado por categoría, con % de avance.',
        paraQue: 'Para preparar la sala de datos antes de un proceso de inversión.',
        funciones: [
          'Checklist de 41 ítems por categoría (legal, financiero, técnico, ESG…).',
          '% de avance global y por categoría.',
          'Link/acción por ítem para completar.',
        ],
        pasos: [
          'Revisá el % de avance por categoría.',
          'Completá los ítems pendientes (subiendo docs al inbox).',
        ],
        parametros: [
          { nombre: 'Estado de cada ítem (completo/pendiente)', donde: 'esta página · inbox/', efecto: 'Sube el % de avance y, con él, el readiness.' },
        ],
        fuente: 'GET /data-room/checklist — la lista de 41 ítems DD definida en el motor; el estado se actualiza al procesar documentos.',
        reemplazar: 'Completás ítems subiendo los documentos a la carpeta inbox/ del repo y corriendo el clasificador (python scripts/procesar_inbox.py); marca los ítems cubiertos.',
      },
      {
        href: '/carbono', titulo: 'Carbono / ESG', icono: '🌿',
        queEs: 'El análisis de huella de carbono (LCA, 3 escenarios) y el revenue potencial por créditos de CO₂.',
        paraQue: 'Para el pitch a fondos ESG: el proyecto es carbono-negativo.',
        funciones: [
          'LCA en 3 escenarios energéticos (baseline / 100% renovable / BECCS).',
          'Emisiones netas a 5 años (CO₂eq evitado vs vertedero).',
          'BECCS y captura adicional.',
          'Revenue por créditos de carbono según precio de tonelada.',
        ],
        pasos: [
          'Mirá las emisiones netas 5y (evitadas).',
          'Revisá el revenue por créditos según el precio de CO₂.',
        ],
        parametros: [
          { nombre: 'Volumen procesado', donde: '/plan (volumen)', efecto: 'A más toneladas, más emisión evitada.' },
          { nombre: 'Precio de la tonelada de CO₂', donde: 'módulo carbono', efecto: 'Define el revenue por créditos.' },
        ],
        fuente: 'POST /plan/carbon-footprint (módulo carbon_footprint) — LCA con factores de emisión de literatura científica (referenciada en /investigacion) y el volumen del plan.',
        reemplazar: 'El volumen sale de /plan; el precio del crédito de CO₂ y los factores LCA se ajustan en el módulo (el agente esg-analyst los mantiene).',
      },
      {
        href: '/compliance', titulo: 'Compliance REP', icono: '📜',
        queEs: 'El timeline de la Ley REP con hitos, severidad y costo, más obligaciones de la Hoja de Ruta 2040.',
        paraQue: 'Para demostrar que el proyecto cumple la normativa de economía circular.',
        funciones: [
          'Timeline de hitos regulatorios con fecha y severidad.',
          'Costo estimado de cumplimiento por hito.',
          'Obligaciones de la Hoja de Ruta Circular 2040.',
          'Alertas de vencimientos cercanos.',
        ],
        pasos: [
          'Revisá los próximos hitos y sus fechas.',
          'Atendé los de vencimiento cercano.',
        ],
        parametros: [
          { nombre: 'Fechas y metas de valorización', donde: 'agente compliance-officer', efecto: 'El agente actualiza el calendario ante cambios normativos.' },
        ],
        fuente: 'GET /compliance/rep-calendar — calendario de la Ley REP y la Hoja de Ruta Circular 2040 (normativa chilena vigente, módulo compliance_rep).',
        reemplazar: 'El agente compliance-officer refresca el calendario cuando cambia la normativa; las fechas y metas se editan en el módulo.',
      },
      {
        href: '/lp-pack', titulo: 'LP Pack', icono: '📦',
        queEs: 'El centro de descargas: tearsheet PDF, ZIP completo con todos los entregables, JSON de datos.',
        paraQue: 'Para enviar a un inversionista todo el material en un click.',
        funciones: [
          'Descarga del LP Pack ZIP completo.',
          'Tearsheet PDF de una página.',
          'Snapshot JSON (datos máquina-legibles).',
          'Copia de links a las secciones clave.',
        ],
        pasos: [
          'Descargá el ZIP completo o solo el tearsheet.',
          'Todo se genera en vivo con los datos del momento.',
        ],
        parametros: [
          { nombre: 'Todo el snapshot', donde: 'se genera en vivo', efecto: 'El contenido refleja el estado actual de TODO el modelo.' },
        ],
        fuente: 'GET /api/lp-pack.zip y /api/tearsheet.pdf — se generan en vivo desde el snapshot al momento de la descarga.',
        reemplazar: 'No se edita: el contenido refleja automáticamente lo que esté cargado en todo el modelo. Para mejorarlo, mejorá los datos fuente.',
      },
      {
        href: '/pipeline-lp', titulo: 'Pipeline LP', icono: '🤝',
        queEs: 'El CRM de inversionistas en roadshow: etapa, monto, próximo paso de cada LP.',
        paraQue: 'Para gestionar el fundraising y no perder ningún follow-up.',
        funciones: [
          'Kanban de LPs por etapa del pipeline.',
          'Monto potencial y probabilidad por LP.',
          'Próximo paso y notas por LP.',
          'Alta, edición y baja de LPs (CRUD).',
        ],
        pasos: [
          'Mové cada LP por las etapas a medida que avanza.',
          'Registrá montos y próximos pasos.',
        ],
        parametros: [
          { nombre: 'Datos de cada LP', donde: 'esta página (editable)', efecto: 'Alimentan el monto ponderado del pipeline.' },
        ],
        fuente: 'GET /lp/pipeline — CRM persistido en el motor (pipeline-lp.json en el volumen).',
        reemplazar: 'Editás cada LP directamente en la página (alta/edición/baja); los cambios se guardan vía POST /lp/upsert.',
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
        funciones: [
          'Tabla x1/x10/x50/x100: producto, costo unitario, revenue, margen, CAPEX, payback.',
          'Gráfico de margen operativo por escala.',
          'Tabla "¿Desde qué escala paga cada SKU?".',
          'Sliders de operación + selector de SKU.',
        ],
        pasos: [
          'Cambiá el SKU arriba (harina, ingrediente humano, nutracéutico).',
          'Mirá desde qué escala cada SKU se vuelve rentable.',
          'Observá el costo unitario bajando con la curva de aprendizaje.',
        ],
        parametros: [
          { nombre: 'SKU seleccionado (precio venta)', donde: 'selector en esta página', efecto: 'Define el revenue; el costo de proceso es igual para todos.' },
          { nombre: 'Operación (horas/días/meses)', donde: 'sliders en esta página', efecto: 'Cambian el volumen base del piloto que se escala.' },
          { nombre: 'Costo base del piloto', donde: '/parametros', efecto: 'Es el punto x1; baja con la curva 80% al escalar.' },
          { nombre: 'Curva de aprendizaje 80% y Williams 0.7', donde: 'modelo de escalas', efecto: 'Definen cómo bajan el costo unitario y el CAPEX al crecer.' },
        ],
        fuente: 'GET /simulacion/escalas + /simulacion/precios-sku + /simulacion/margen-por-sku. El costo base x1 viene del piloto real; los precios SKU son estimaciones de mercado (PD).',
        reemplazar: 'El costo base se cambia en /parametros. Los precios de venta por SKU hoy viven en el motor; el data-hunter (viernes) busca precios de mercado reales con fuente para que los valides.',
      },
      {
        href: '/whatif-live', titulo: 'What-if Live', icono: '🎚',
        queEs: 'Sliders en vivo de precio, costo, WACC y OPEX que recalculan TIR y VAN al instante.',
        paraQue: 'Para responder "¿qué pasa si...?" en segundos durante una reunión.',
        funciones: [
          'Sliders de precio, costo MMPP, WACC y OpEx.',
          'TIR y VAN recalculados al instante.',
          'Comparación contra el caso base.',
        ],
        pasos: [
          'Mové un slider y mirá el efecto inmediato en TIR/VAN.',
          'Combiná shocks para buscar el punto de equilibrio.',
        ],
        parametros: [
          { nombre: 'Precio · costo · WACC · OpEx (los 4 sliders)', donde: 'esta página', efecto: 'Cada uno recalcula TIR y VAN en vivo, sin tocar el modelo guardado.' },
        ],
        fuente: 'POST /whatif — corre el modelo financiero con los overrides de los sliders sobre el plan base.',
        reemplazar: 'Los sliders son temporales (no guardan nada). Para fijar un cambio de verdad, editá el parámetro real en /parametros o el supuesto en /plan.',
      },
      {
        href: '/sensitivity', titulo: 'Sensibilidad', icono: '🌡',
        queEs: 'Heatmap 2D (precio × costo), break-even por driver y curvas de TIR por variable.',
        paraQue: 'Para entender a qué es más sensible el proyecto y cuál es el precio mínimo viable.',
        funciones: [
          'Heatmap 2D: TIR según precio × costo MMPP.',
          'Break-even: precio mínimo para TIR = WACC.',
          'Curvas 1D de TIR por cada driver.',
        ],
        pasos: [
          'Leé el heatmap: verde = TIR sobre el hurdle, rojo = bajo.',
          'Revisá el precio break-even.',
        ],
        parametros: [
          { nombre: 'Rangos de precio y costo', donde: 'controles de esta página', efecto: 'Definen los ejes del heatmap.' },
          { nombre: 'WACC objetivo (hurdle)', donde: '/financiamiento', efecto: 'Es el umbral verde/rojo y el punto de break-even.' },
        ],
        fuente: 'POST /sensitivity/heatmap + GET /sensitivity/curves y /sensitivity/breakeven — recalculan el plan variando cada driver dentro de los rangos definidos.',
        reemplazar: 'Definís los rangos en los controles de la página; el WACC objetivo sale de /financiamiento.',
      },
      {
        href: '/inteligencia', titulo: 'Inteligencia', icono: '🧠',
        queEs: 'La síntesis cross-modular: insights, exactitud del modelo y predicción con bandas de confianza.',
        paraQue: 'Para saber cuán confiable es el modelo (hoy ~65%) y qué validar primero para mejorarlo.',
        funciones: [
          'Síntesis de insights por severidad (críticos, altos, oportunidades).',
          'Exactitud del modelo (% global) + ranking de qué validar.',
          'Predicción con bandas p10 / p50 / p90 (costo, producción, revenue, margen).',
          'Drivers de incertidumbre ordenados por impacto.',
        ],
        pasos: [
          'Mirá la exactitud del modelo y los insights priorizados.',
          'Revisá las bandas de predicción y el ranking de qué validar.',
        ],
        parametros: [
          { nombre: 'Nivel de validación de cada input', donde: '/parametros · /variables', efecto: 'Sube la exactitud y estrecha las bandas p10–p90.' },
          { nombre: 'Peso de cada componente del costo', donde: 'desglose OPEX', efecto: 'Pondera cuánto pesa cada incertidumbre en la banda final.' },
        ],
        fuente: 'GET /inteligencia/sintesis, /inteligencia/precision y /inteligencia/prediccion. La predicción está anclada al simulador real (mismo costo) y la incertidumbre se pondera por el nivel PD/PROV/VALIDADO de cada input.',
        reemplazar: 'La exactitud sube sola al validar inputs PD en /parametros y /variables. No hay nada que editar acá: es el termómetro del modelo.',
      },
      {
        href: '/financiamiento', titulo: 'Financiamiento', icono: '🏦',
        queEs: 'El mix deuda/equity con DSCR, LLCR, escudo fiscal y TIR del equity.',
        paraQue: 'Para estructurar el financiamiento antes de un pitch a bancos o CORFO.',
        funciones: [
          'Mix deuda/equity ajustable.',
          'DSCR y LLCR (ratios de bancabilidad).',
          'Escudo fiscal por intereses.',
          'TIR del equity y cronograma de deuda.',
        ],
        pasos: [
          'Ajustá el mix deuda/equity.',
          'Verificá que el DSCR sea bancable (>1.3) y mirá la TIR del equity.',
        ],
        parametros: [
          { nombre: '% deuda, tasa, plazo y período de gracia', donde: 'controles de esta página', efecto: 'Definen el servicio de deuda, el DSCR y la TIR del equity.' },
          { nombre: 'Tasa de impuesto', donde: 'controles de esta página', efecto: 'Determina el escudo fiscal por intereses.' },
          { nombre: 'CAPEX a financiar', donde: '/plan', efecto: 'Es la base sobre la que se arma el mix.' },
        ],
        fuente: 'POST /plan/financing — arma el mix sobre el CAPEX del plan con los supuestos de deuda que definís.',
        reemplazar: 'Ajustás mix, tasa, plazo y gracia en los controles de la página; el CAPEX base sale de /plan.',
      },
    ],
  },
  {
    persona: 'Sistema',
    emoji: '🔧',
    color: 'text-ink-600',
    intro: 'Las herramientas internas: la matriz de supuestos, el buzón de datos, la trazabilidad, la salud técnica y el mapa.',
    secciones: [
      {
        href: '/variables', titulo: 'Matriz de Variables', icono: '🗃',
        queEs: 'La matriz canónica de TODOS los supuestos del modelo (≈165 celdas) con su nivel de validación PD / OK_PROVISORIO / OK_VALIDADO.',
        paraQue: 'Para ver de un vistazo qué datos están firmes y cuáles son estimaciones, y subir la exactitud del modelo validando.',
        funciones: [
          'Las ≈165 celdas del modelo con su valor y nivel de validación.',
          '% de cobertura (cuántas están validadas vs PD).',
          'Variables Intelligence: auto-validación y sugerencias para celdas PD.',
          'Filtro por estado y por módulo.',
        ],
        pasos: [
          'Filtrá por celdas PD (las que más bajan la exactitud).',
          'Conseguí el dato real y cargalo en su página fuente (/parametros, /equipos).',
          'Subí el nivel a PROVISORIO o VALIDADO según el respaldo.',
        ],
        parametros: [
          { nombre: 'Nivel de cada celda (PD/PROVISORIO/VALIDADO)', donde: 'esta página · /parametros', efecto: 'La cobertura validada sube la exactitud del modelo y el readiness.' },
        ],
        fuente: 'GET /variables/matrix + /variables/intelligence — el estado canónico de los supuestos, derivado del Excel original y los parámetros cargados.',
        reemplazar: 'El valor se cambia en su página de origen (/parametros, /equipos); acá se gestiona el NIVEL de validación de cada uno.',
      },
      {
        href: '/inbox', titulo: 'Inbox de Datos', icono: '📥',
        queEs: 'El buzón donde el equipo deja documentos (PDF, Excel, Word, fotos) que el sistema clasifica y conecta con la matriz.',
        paraQue: 'Para incorporar información nueva del equipo sin tocar la app: la dejás en una carpeta y el clasificador la procesa.',
        funciones: [
          'Estado del buzón: archivos indexados, sugerencias detectadas, categorías.',
          'Clasificación automática por tipo y subcategoría.',
          'Sugerencias de qué celda de la matriz actualizar con cada archivo.',
          'Registro en el audit trail de lo incorporado.',
        ],
        pasos: [
          'Dejá los archivos en la carpeta inbox/ del repositorio.',
          'Ejecutá el procesador: python scripts/procesar_inbox.py.',
          'Revisá las sugerencias y validá los datos en su página fuente.',
        ],
        parametros: [
          { nombre: 'Archivos en la carpeta inbox/', donde: 'repo · script procesar_inbox', efecto: 'Cada archivo clasificado sugiere actualizaciones a la matriz y al data room.' },
        ],
        fuente: 'GET /inbox/status — índice de los archivos procesados por el clasificador (scripts/procesar_inbox.py).',
        reemplazar: 'Agregás información dejando archivos en inbox/ y corriendo el procesador; el clasificador los indexa y sugiere dónde aplican.',
      },
      {
        href: '/audit', titulo: 'Audit Trail', icono: '📝',
        queEs: 'El historial inmutable de todos los cambios al modelo: qué cambió, cuándo y con qué valor.',
        paraQue: 'Para trazabilidad y defensa en due diligence — un LP puede ver cómo evolucionó cada supuesto.',
        funciones: [
          'Registro cronológico de cambios al modelo.',
          'Quién/qué originó el cambio y el valor anterior vs nuevo.',
          'Base de evidencia para due diligence.',
        ],
        pasos: [
          'Revisá los cambios recientes ordenados por fecha.',
          'Usalo como respaldo cuando un LP pregunte por la evolución de un dato.',
        ],
        parametros: [
          { nombre: 'Eventos de cambio del modelo', donde: 'se registran solos', efecto: 'Cada edición de parámetros/fichas/validación queda asentada automáticamente.' },
        ],
        fuente: 'GET /audit/trail — registro append-only que el motor escribe ante cada cambio relevante.',
        reemplazar: 'No se edita (es inmutable por diseño): se llena solo a medida que se trabaja el modelo.',
      },
      {
        href: '/salud', titulo: 'Salud del Sistema', icono: '🩺',
        queEs: 'El panel técnico: estado del motor (engine), latencias, cache y checks de cada endpoint.',
        paraQue: 'Para verificar que la plataforma está sana — útil si algo se ve raro o lento.',
        funciones: [
          'Health checks del engine y de cada endpoint clave.',
          'Latencias de respuesta y estado de la cache.',
          'Botón para limpiar la cache.',
        ],
        pasos: [
          'Mirá que todos los checks estén en verde.',
          'Si un dato no se actualiza, limpiá la cache y refrescá.',
        ],
        parametros: [
          { nombre: 'TTL de la cache (60s snapshot)', donde: 'motor', efecto: 'Define cada cuánto se recalcula el snapshot que alimenta el cockpit.' },
        ],
        fuente: 'GET /health/full + /cache/stats — estado en vivo del backend en Fly.io.',
        reemplazar: 'No se edita: es monitoreo. El schedule trongkai-daily-pulse revisa esto cada mañana.',
      },
      {
        href: '/mapa', titulo: 'Mapa de la Plataforma', icono: '🗺',
        queEs: 'El sitemap completo: todas las páginas y cómo se conectan, para onboarding y navegación.',
        paraQue: 'Para tener la foto completa de la plataforma y encontrar cualquier sección.',
        funciones: [
          'Todas las páginas agrupadas por capa/función.',
          'Mini-diagrama del flujo de información (datos → planta → modelo → entregables).',
          'Acceso directo a cada sección.',
        ],
        pasos: [
          'Usalo como índice cuando no sabés dónde está algo.',
          'Para buscar más rápido, presioná ⌘K.',
        ],
        parametros: [
          { nombre: 'Estructura de páginas', donde: 'código del frontend', efecto: 'Refleja las rutas reales de la plataforma.' },
        ],
        fuente: 'Estático en el frontend + GET /inteligencia/sintesis para el resumen de estado.',
        reemplazar: 'Se actualiza al agregar/quitar páginas (lo hace el equipo de desarrollo o el improver).',
      },
    ],
  },
];

// Secciones con screenshot real capturado (en /public/guia/<seccion>.png).
// Cobertura total: las 28 secciones tienen captura real.
// Regenerar con:  cd apps/web && node scripts/capturar-guia.mjs
export const SCREENSHOTS = new Set<string>([
  '/comando', '/plan', '/dashboard-directorio', '/riesgo', '/decisiones',
  '/planta', '/simulacion', '/balance-integral', '/balance-etapas', '/costeo',
  '/parametros', '/equipos', '/readiness', '/data-room', '/carbono',
  '/compliance', '/lp-pack', '/pipeline-lp', '/escalas', '/whatif-live',
  '/sensitivity', '/inteligencia', '/financiamiento', '/variables', '/inbox',
  '/audit', '/salud', '/mapa',
]);

// Acciones sugeridas por pantalla (Ola 3 dominio-total): "con este dato, lo siguiente es..."
// Se muestran en el panel de ayuda contextual. Solo rutas reales de la app.
export type Siguiente = { texto: string; href: string };
export const SIGUIENTES: Record<string, Siguiente[]> = {
  '/comando': [
    { texto: 'Profundizá en la síntesis cross-modular', href: '/inteligencia' },
    { texto: 'Mirá las 5 acciones priorizadas', href: '/decisiones' },
  ],
  '/plan': [
    { texto: 'Estresá esta TIR con los drivers', href: '/sensitivity' },
    { texto: 'Compará escenarios estratégicos', href: '/comparador' },
  ],
  '/dashboard-directorio': [
    { texto: 'Volvé al cockpit en vivo', href: '/comando' },
    { texto: 'Revisá el riesgo integrado antes de presentar', href: '/riesgo' },
  ],
  '/riesgo': [
    { texto: 'Probá el triple negativo', href: '/stress' },
    { texto: 'Jugá los supuestos en vivo', href: '/whatif-live' },
  ],
  '/decisiones': [
    { texto: 'Ejecutá la acción n.°1 en su pantalla', href: '/comando' },
    { texto: 'Validá el dato que la sustenta', href: '/variables' },
  ],
  '/planta': [
    { texto: 'Simulá cuánto produce esta planta', href: '/simulacion' },
    { texto: 'Editá las fichas de los equipos', href: '/equipos' },
  ],
  '/simulacion': [
    { texto: 'Mirá qué SKU deja margen a escala', href: '/escalas' },
    { texto: 'Ajustá tarifas y sueldos (recalcula todo)', href: '/parametros' },
  ],
  '/balance-integral': [
    { texto: 'Bajá al detalle por etapa', href: '/balance-etapas' },
    { texto: 'Convertí estos flujos en costos', href: '/costeo' },
  ],
  '/balance-etapas': [
    { texto: 'Mirá el costo de cada etapa', href: '/costeo' },
    { texto: 'Cambiá los parámetros de proceso', href: '/parametros' },
  ],
  '/costeo': [
    { texto: 'Decidí el packaging (saco vs maxisaco)', href: '/escalas' },
    { texto: 'Validá los supuestos del canon V3', href: '/variables' },
  ],
  '/parametros': [
    { texto: 'Mirá el efecto en la simulación', href: '/simulacion' },
    { texto: 'Chequeá qué nivel de dato quedó', href: '/variables' },
  ],
  '/equipos': [
    { texto: 'Vé estos equipos en el layout real', href: '/planta' },
    { texto: 'Su consumo vive en la simulación', href: '/simulacion' },
  ],
  '/readiness': [
    { texto: 'Cerrá los gaps del data room', href: '/data-room' },
    { texto: 'Subí el score validando variables', href: '/variables' },
  ],
  '/data-room': [
    { texto: 'Armá el paquete descargable para el LP', href: '/lp-pack' },
    { texto: 'Mirá cómo impacta en el readiness', href: '/readiness' },
  ],
  '/carbono': [
    { texto: 'Sumá los créditos CO2 al plan', href: '/plan' },
    { texto: 'Úsalo en el pack para LPs ESG', href: '/lp-pack' },
  ],
  '/compliance': [
    { texto: 'Agendá los hitos en el roadmap', href: '/roadmap' },
    { texto: 'Documentalo para due diligence', href: '/data-room' },
  ],
  '/lp-pack': [
    { texto: 'Trackeá a quién se lo mandaste', href: '/pipeline-lp' },
    { texto: 'Refrescá el readiness antes de enviar', href: '/readiness' },
  ],
  '/pipeline-lp': [
    { texto: 'Prepará el material para el próximo LP', href: '/lp-pack' },
    { texto: 'Refrescá los números del pitch', href: '/comando' },
  ],
  '/escalas': [
    { texto: 'Armá el plan a 5 años de la escala elegida', href: '/plan' },
    { texto: 'Mirá el financiamiento que requiere', href: '/financiamiento' },
  ],
  '/whatif-live': [
    { texto: 'Formalizá el escenario en el plan', href: '/plan' },
    { texto: 'Mirá el heatmap completo de drivers', href: '/sensitivity' },
  ],
  '/sensitivity': [
    { texto: 'Probá el peor caso combinado', href: '/stress' },
    { texto: 'Validá el driver más sensible', href: '/variables' },
  ],
  '/inteligencia': [
    { texto: 'Convertí el insight en acción', href: '/decisiones' },
    { texto: 'Validá lo que el modelo pide primero', href: '/variables' },
  ],
  '/financiamiento': [
    { texto: 'Simulá bonos ligados a sostenibilidad', href: '/slb' },
    { texto: 'Mirá el DSCR bajo estrés', href: '/stress' },
  ],
  '/variables': [
    { texto: 'Cargá el dato real que falta', href: '/inbox' },
    { texto: 'Mirá cuánto sube el readiness', href: '/readiness' },
  ],
  '/inbox': [
    { texto: 'Verificá que la matriz tomó el dato', href: '/variables' },
    { texto: 'Mirá el efecto en el modelo', href: '/inteligencia' },
  ],
  '/audit': [
    { texto: 'Compará snapshots antes/después', href: '/comando' },
    { texto: 'Revisá la salud del sistema', href: '/salud' },
  ],
  '/salud': [
    { texto: 'Mirá el mapa completo de la plataforma', href: '/mapa' },
    { texto: 'Revisá el historial de cambios', href: '/audit' },
  ],
  '/mapa': [
    { texto: 'Empezá por el Centro de Mando', href: '/comando' },
    { texto: 'Leé la guía de cada sección', href: '/guia' },
  ],
};
