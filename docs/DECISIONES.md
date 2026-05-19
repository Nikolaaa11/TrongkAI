# Architecture Decision Records (ADR)

> Decisiones arquitectónicas, su contexto y su trade-off. Nunca borrar un ADR — superseder con uno nuevo.

## ADR-001 — Stack fijado por SUPER_PROMPT

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: Next.js 14 + FastAPI Python 3.11 + Postgres + Prisma + Redis + Recharts/ECharts + Docker Compose en un solo servidor. Sin Kubernetes.
**Razón**: 6 usuarios internos, ningún requerimiento de escalado horizontal. La complejidad operacional la pagamos cero. Pandas/NumPy en Python obligado por balance de masa y scipy.optimize por mix.
**Consecuencias**: front y motor separados → tipos compartidos vía Zod schemas y FastAPI Pydantic generando OpenAPI consumido por tRPC client. Latencia interna no relevante (mismo host).

## ADR-002 — Estados granulares para `Supuesto.estado`

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: 6 estados en lugar de los 2 del Excel (PD/OK).
- `PD` — sin valor
- `OK_PROVISORIO` — equivalente a "OK\*" del cliente, no se incluye en reportes oficiales
- `OK_VALIDADO_JOSE` — balance de masa firmado por José
- `OK_VALIDADO_CLAUDIO` — balance de masa firmado por Claudio
- `OK_VALIDADO_JAIME` — proceso firmado por dueño
- `OK_VALIDADO_DIRECTORIO` — congelado en `VersionPlan` para presentación a directorio

**Razón**: la regla §8 del SUPER_PROMPT exige separar provisorios de validados por experto. Sin esto, un OK\* se cuela a un PDF de directorio y rompe credibilidad.
**Consecuencias**: cualquier query a EERR oficial filtra `estado IN ('OK_VALIDADO_*')`. Tests que verifiquen que `MixProduccionMensual` no use supuestos `PD` en versión final.

## ADR-003 — Doble modo de cálculo de balance de masa expuesto al usuario

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: el motor de masa implementa **modo A (base inicial)** y **modo B (base deshidratada)** simultáneamente. Cada `MixProduccionMensual` declara qué modo usa. Por defecto, modo A.
**Razón**: Jaime fue explícito (Excel `Base rendimiento` deja un "???" entre las dos), la diferencia es material (35% vs 38.5% en alperujo). No podemos forzar uno hasta que José/Claudio firmen.
**Consecuencias**: el motor expone `compute_mass_balance(mode: Literal["A","B"])`. La UI muestra ambos y un delta. La firma de José/Claudio se exige antes de fijar uno como default productivo.

## ADR-004 — Catálogo de proveedores expansible (Olivero 1..N, no fijo)

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: el Excel actual tiene Olivero 1..10 (solo 4 con datos). En DB usamos `Supplier` con FK por nombre + tipo MMPP, no slots fijos.
**Razón**: Trongkai escala incorporando proveedores. Hardcodear 10 oliveros + 10 tomateros + ... es un anti-patrón.
**Consecuencias**: la UI tiene un CRUD de proveedores. El seed inicial carga los 4 oliveros con datos del Excel, los 6 restantes quedan como `Supplier (status=PROSPECT)`.

## ADR-005 — Versión de plan inmutable por snapshot

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: cuando un `PlanAnual` se aprueba en directorio, se genera un `VersionPlan` con snapshot inmutable de todos los supuestos, mix, capex/opex y flujo. Diff visual antes de reemplazar.
**Razón**: regla §8 SUPER_PROMPT. Si llega CMF preguntando por el plan firmado en 2026-Q3, hay que devolver exactamente esos números, no los actuales.
**Consecuencias**: tabla `VersionPlan` con columna `payload jsonb` (snapshot completo). Trigger Postgres bloquea UPDATE/DELETE de versiones aprobadas.

## ADR-006 — Contradicciones detectadas entre transcripts

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: documentar como ADR cada contradicción entre Jaime y la voz Trongkai (regla §7.3 SUPER_PROMPT).

### Contradicción C1: ¿24/7 en temporada o planta de paso?
- **Jaime** (L270): "y cuando la, la temporada parte, esto es 24, 7".
- **Trongkai transcript** (L14-16): "lo que nosotros entramos por planta se procesa. No vamos a tener un proceso de almacenamiento."

**Resolución**: ambos son ciertos y compatibles. La planta opera **24/7 en temporada alta de cada MMPP** (Ene-Mar tomasa, Abr-Jun alperujo y orujo, Mar-May pomasa) **sin almacenamiento intermedio**. Modelo: turnos × días × meses por MMPP, con factor de utilización por etapa.

### Contradicción C2: ¿tiempo de fermentación de tomasa?
- Trongkai transcript (L32): cita tres tiempos (1, 5, 3 horas) sin fijar uno.
- Jaime (L42): "imposible, yo no te acepto" — el límite es duro pero el tiempo no está.

**Resolución**: tratar como `tomasa.tiempo_descomposicion_h = 3` con estado `PD` y solicitar a José medición real en planta piloto. Sensibilidad **crítica** para el solver del Módulo 1.

### Contradicción C3: ¿alperujo 35% MS o 38.5% MS?
- Excel `Base rendimiento`: muestra ambos cálculos y deja "???".

**Resolución**: ADR-003 (doble modo) cubre esto.

## ADR-007 — Idioma y nomenclatura

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: UI 100% español de Chile. Código en inglés (variables, funciones, archivos). Comentarios de código en español. Nombres de dominio en español (`alperujo`, `tomasa`, `pomasa`) sin traducir.
**Razón**: regla §6 SUPER_PROMPT.
**Consecuencias**: i18n no necesario hoy. Si mañana hay que internacionalizar, se hace contra `messages.es-CL.json` ya estructurado.

## ADR-009 — Estrategia de marca dual: Feed y Food

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: Trongkai opera bajo dos sub-marcas comerciales que comparten plataforma productiva:
- **Trongkai Feed** — nutrición animal (acuicultura + pet food).
- **Trongkai Food** — humanos (panadería, snacks).

Plus la línea de **Servicios de Plataforma Tecnológica** (maquila + licenciamiento + transferencia + alianzas Opticept/Axolot).

**Razón**: la presentación corporativa (2025-10-22) define explícitamente las dos marcas con audiencias y reguladores distintos (Sernapesca + INDAP para Feed, ISP/Aduanas para Food). Plus el directorio aprobó nombres comerciales.

**Consecuencias**:
- En DB: cada `Producto` lleva campo `marca` (`FEED` | `FOOD` | `SERVICIOS`). Se sembra en seed Fase 1.
- En UI: `/plan` agrupa por marca; exports a directorio respetan el agrupamiento.
- En finanzas: el modelo financiero distingue precio target Feed vs Food. Para Feed, el benchmark es precio mayorista de harina de pescado en Chile (variable nueva en `RIESGO-SUPUESTOS.md`).
- En glosario: agregadas las entradas FEED, FOOD, Opticept, Axolot, ACV, SOPs.

## ADR-010 — Identidad visual

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: usar logos oficiales provistos por el usuario en `apps/web/public/logo-trongkai-*`. Versión color sobre fondos claros, versión blanco sobre fondos oscuros. Icono aislado para favicon y elementos chicos.
**Razón**: la presentación corporativa fija la identidad. Cualquier deriva (paleta, tipografía custom) genera fricción con el material que ya circula en directorio.
**Consecuencias**: header del sitio muestra el logo en lugar del placeholder de texto. La paleta tierra/oliva del ADR-001 sigue activa para todas las UI internas (dashboard operacional, supuestos), porque combina con el verde oliva del logo.

## ADR-008 — Confidencialidad de transcripts

**Fecha**: 2026-05-18
**Estado**: Aceptado
**Decisión**: los `.txt` de transcripts viven en `/contexto/` y **nunca** se referencian textualmente en UI, exports, comentarios de código que vayan a directorio, ni respuestas a CMF. La jerga de Jaime se mapea a vocabulario neutro vía `GLOSARIO.md`.
**Razón**: regla §0.7 SUPER_PROMPT.
**Consecuencias**: lint custom detecta tokens como "hueón", "chucha", "cachai" en código y falla CI. `/contexto/*.txt` agregado a `.gitignore` para repos públicos (si los hubiera) — en este caso el repo es privado del cliente, pero igual lo aplicamos a builds de prod.
