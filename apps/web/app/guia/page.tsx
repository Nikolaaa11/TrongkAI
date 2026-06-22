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
  const [abierta, setAbierta] = useState<string | null>('/simulacion');

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
          s.parametros.some((p) => p.nombre.toLowerCase().includes(t) || p.efecto.toLowerCase().includes(t)),
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
          Cada sección con TODAS sus funciones, qué parámetros la influyen y cómo se trabajan — más una
          vista previa en vivo de cada pantalla. Para que cualquiera del equipo tenga dominio total.
        </p>
        <div className="mx-auto mt-6 max-w-md">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar función o parámetro… (ej: arriendo, TIR, yield)"
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

      {/* Cómo fluyen los parámetros */}
      <section className="rounded-appleXl border border-brand/20 bg-brand-50/40 p-8">
        <h2 className="text-2xl font-semibold tracking-apple text-ink">🔄 Cómo fluyen los parámetros</h2>
        <p className="mt-2 max-w-3xl text-ink-600">
          La plataforma tiene <strong>una sola fuente de verdad por número</strong>. Editás un parámetro en su
          página de origen y el motor recalcula TODO lo que depende de él, en cascada:
        </p>
        <div className="mt-5 grid grid-cols-1 gap-3 text-sm md:grid-cols-5 md:items-center">
          {[
            { t: '1 · Editás', d: 'Parámetros de planta, fichas de equipos o supuestos del plan.', c: 'bg-white' },
            { t: '→', d: '', c: 'bg-transparent text-center text-2xl text-brand' },
            { t: '2 · Recalcula el motor', d: 'Simulación, costeo, escalas, balances y predicción.', c: 'bg-white' },
            { t: '→', d: '', c: 'bg-transparent text-center text-2xl text-brand' },
            { t: '3 · Se refleja', d: 'Cockpit, board pack, readiness, LP pack — coherentes.', c: 'bg-white' },
          ].map((s, i) => (
            <div key={i} className={`rounded-xl p-4 ${s.c}`}>
              <div className="font-semibold text-ink">{s.t}</div>
              {s.d && <div className="mt-1 text-[13px] text-ink-500">{s.d}</div>}
            </div>
          ))}
        </div>
        <p className="mt-4 text-[13px] text-ink-500">
          Por eso, en cada sección de abajo verás el bloque <strong>"Parámetros que influyen"</strong>: te dice
          exactamente qué dato cambia esa pantalla, dónde editarlo y qué efecto tiene.
        </p>
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
              const open = abierta === s.href || !!q.trim();
              return (
                <div key={s.href} className="overflow-hidden rounded-2xl border border-ink-100 bg-white">
                  {/* Cabecera clickable */}
                  <button
                    onClick={() => setAbierta(abierta === s.href ? null : s.href)}
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
                    <span className={`text-ink-300 transition-transform ${open ? 'rotate-180' : ''}`}>▾</span>
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

                      {/* Columna derecha: preview en vivo */}
                      <div className="min-h-[260px] rounded-xl border border-ink-100 bg-ink-50/40">
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
          <Link href="/parametros" className="rounded-full border border-white/40 bg-white/10 px-5 py-2.5 text-[14px] font-medium text-white transition hover:bg-white/20">
            Editar parámetros
          </Link>
        </div>
      </section>
    </div>
  );
}
