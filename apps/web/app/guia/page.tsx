'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';

type Param = { nombre: string; donde: string; efecto: string };
type Seccion = {
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
          { nombre: 'Arriendo PEF + Tricanter', donde: '/parametros', efecto: 'Costo fijo dominante (~61%): se paga los 12 meses calendario.' },
          { nombre: 'Sueldos × dotación', donde: '/parametros', efecto: 'Mano de obra (~25%): fijo mensual con factor de leyes sociales.' },
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
        ],
        fuente: 'GET /costeo/etapas — calcula el costo con parametros-planta.json. Misma base que la simulación (coherencia garantizada).',
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
          { nombre: 'Sueldos', donde: 'esta página', efecto: 'Mano de obra del OPEX (≈25% del costo del piloto).' },
          { nombre: 'Arriendos PEF/Tricanter', donde: 'esta página', efecto: 'Costo fijo dominante (≈61%); driver #2 de incertidumbre.' },
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
          'LCA en 3 escenarios (conservador / base / optimista).',
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
        fuente: 'Módulo carbon_footprint — LCA con factores de emisión de literatura científica (referenciada en /investigacion) y el volumen del plan.',
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
        fuente: 'GET /lp/pipeline — CRM persistido en el motor (lp-pipeline.json en el volumen).',
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
        fuente: 'GET /sensitivity/heatmap, /sensitivity/curves y /sensitivity/breakeven — recalculan el plan variando cada driver dentro de los rangos definidos.',
        reemplazar: 'Definís los rangos en los controles de la página; el WACC objetivo sale de /financiamiento.',
      },
      {
        href: '/inteligencia', titulo: 'Inteligencia', icono: '🧠',
        queEs: 'La síntesis cross-modular: insights, exactitud del modelo y predicción con bandas de confianza.',
        paraQue: 'Para saber cuán confiable es el modelo (hoy ~62%) y qué validar primero para mejorarlo.',
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
  const [preview, setPreview] = useState<string | null>('/simulacion');
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
                      setPreview(next); // mostrar la imagen (preview en vivo) al abrir
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

                      {/* Columna derecha: preview en vivo (no se imprime) */}
                      <div className="min-h-[260px] rounded-xl border border-ink-100 bg-ink-50/40 print:hidden">
                        {preview === s.href ? (
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
