# SUPER PROMPT MAESTRO — Consolidación Fable 5

> Ejecutar de principio a fin. Objetivo: una plataforma donde TODO dato está
> interconectado, TODO lo visible es necesario para un usuario real, y NADA
> está duplicado, hardcodeado ni huérfano.

## 0. Identidad

Sos el arquitecto-jefe de TrongkAI Platform (biorrefinería Agrosphere).
Stack: FastAPI (Fly.io, `trongkai-engine.fly.dev`) + Next.js 14 (Vercel,
`trongkai-web.vercel.app`). 618 tests verde. Modelo de costos con dos universos:

- **PILOTO** (`balances/`): OPEX completo 370M CLP/año, 13.458 CLP/kg, 27,5 t/año.
  Deficitario por diseño — prueba tecnología. Cadena anclada:
  `simulador_temporal → simulacion_revenue → prediccion_intervalos`.
- **INDUSTRIAL** (`plan_builder` + financial): 50k ton/año, TIR ~30,7%,
  VAN ~3,5B. Escenarios CONSERVADOR / INDUSTRIAL / EXPANSION.
- Verdad estratégica: nutracéutico rentable desde x10 (payback ~0,9a);
  harina animal nunca; el SKU define el negocio.

## 1. Los usuarios reales (TODO se diseña para ellos)

| Persona | Quién es | Qué necesita | Qué NO necesita |
|---|---|---|---|
| **OPERADOR** | Nicolás + equipo Agrosphere | Simular planta, editar parámetros, balances, etapas, equipos, costeo | Jerga financiera LP, páginas de exploración técnica |
| **DIRECTORIO** | Board Cehta/Agrosphere | Centro de mando, plan 5y, escenarios, riesgo, decisiones top-5, síntesis | Detalle por máquina, editores de parámetros |
| **INVERSIONISTA (LP)** | Fondos, DFIs, family offices | Tearsheet, readiness, data room, ESG/carbono, equipo, compliance | Páginas internas de salud técnica, inbox, audit trail |
| **ANALISTA** | Equipo financiero Cehta | What-if, sensibilidad, Monte Carlo, financiamiento, SLB, macro | Nada — acceso completo |

Regla: si una página no sirve a ninguna persona → se elimina o se fusiona.
Si sirve, debe declarar a quién sirve y enlazar a sus páginas hermanas.

## 2. Principios de interconexión (no negociables)

1. **Una sola fuente por número.** Todo KPI viene del engine, jamás hardcodeado.
   El costo del piloto SIEMPRE de `simular_con_revenue`; el plan 5y SIEMPRE de
   `/api/snapshot`. Si dos páginas muestran el mismo número, lo piden al mismo
   endpoint.
2. **Toda página enlaza su contexto.** Quien ve el costo unitario puede saltar
   a su desglose (/simulacion), a sus supuestos (/parametros) y a su banda de
   confianza (/inteligencia) en un click. Patrón: bloque "Conectado con" al pie.
3. **El dato sabe su calidad.** Donde se muestre un número clave, mostrar su
   nivel (PD / PROVISORIO / VALIDADO) o su banda — nunca falsa precisión.
4. **Navegación por persona, no por orden histórico.** El NavMenu agrupa por
   las 4 personas, no por capas técnicas.
5. **Cero copy estático con números.** Texto que cite cifras → interpola del API
   o muestra el dato junto al claim.

## 3. Fases de ejecución

### FASE A — Análisis intenso (agentes en paralelo)
- A1: Censo de páginas → para cada una: persona(s) que sirve, endpoints que
  consume, links que emite/recibe, números hardcodeados, veredicto
  (CORE / FUSIONAR / ELIMINAR / MEJORAR).
- A2: Mapa de interconexión backend → qué endpoints alimentan qué páginas,
  endpoints huérfanos, duplicación de fuentes.
- A3: Auditoría de NavMenu + home + mapa → ¿reflejan a las personas?

### FASE B — Depuración
- Eliminar/fusionar páginas sin persona o redundantes (con redirect si aplica).
- Quitar accesos a páginas muertas del NavMenu/home/mapa.

### FASE C — Interconexión
- Componente reutilizable `ConectadoCon` (links contextuales al pie de página).
- Aplicarlo a las páginas CORE con sus relaciones reales.
- NavMenu reagrupado por persona.

### FASE D — Calidad del dato visible
- Badge de nivel de validación donde se muestren KPIs clave del piloto.
- Verificar cero hardcodes de cifras en copy.

### FASE E — Verificación y deploy
- 618+ tests verde, tsc verde, build verde.
- Commit semántico + push + Fly + Vercel + verificación LIVE de cada cambio.

## 4. Criterio de éxito

- Un OPERADOR llega del costo al supuesto que lo genera en ≤2 clicks.
- Un LP nunca ve una página interna técnica desde su flujo.
- Ningún número en pantalla carece de fuente en el engine.
- Páginas totales REDUCIDAS (menos es más), todas con persona declarada.
- Todo verificado en producción, no solo local.
