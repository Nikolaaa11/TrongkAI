# Próximos pasos para que la plataforma siga creciendo

> Lista priorizada de **qué necesito del lado humano** (cosas que no puedo hacer solo) y **qué puedo seguir construyendo** (acciones autónomas o semi-autónomas).

---

## A. NECESITO DEL USUARIO (datos / decisiones / accesos)

### A1 — Bloqueantes inmediatos para defender el plan a directorio

| # | Pregunta | Owner sugerido | Bloqueante de |
|---|---|---|---|
| 1 | ¿Cuál es la cuota de mercado real de cada SKU año 1-5? (cuotas comerciales firmes por producto) | Jaime + Comercial | KI-001 fix definitivo, calibración TIR |
| 2 | Capacidad real del **secador** (ton/h) — el bottleneck del proceso | Matías | Toda la agenda dinámica y bottleneck real |
| 3 | Capacidad real del PEF Opticept (¿modelo L7 confirmado?) | José + Jaime | Capacidad pico + límite de extracción aceite |
| 4 | Tiempo real de descomposición de tomasa / pomasa (medición planta) | Matías | Ventana segura recepción |
| 5 | Firma del **Modo Balance A vs B** | José + Claudio (ADR-003) | Cierre Fase 3 + cifras al directorio |
| 6 | **WACC firmado** por directorio | Directorio CEHTA | TIR/VAN defendibles |
| 7 | Precios de venta firmes por SKU (idealmente con contratos LOI) | Comercial | KI-001, top 10 RIESGO |

### A2 — Decisiones comerciales pendientes (alto leverage)

| # | Pregunta | Decisión esperada |
|---|---|---|
| 8 | ¿Hay LOI o MOU firmado con AquaChile / Cermaq / Mowi / Cooke? | Convierte TAM Feed teórico → pipeline real |
| 9 | ¿Pet Food Factory / Cannae son partners o competencia? | Define canal y precio pet food |
| 10 | ¿Quién paga el Opticept L7 HC? (lease / compra / equity) | Define CapEx año 1-2 firme |
| 11 | ¿Qué es **Axolot** exactamente? (no aparece en búsqueda web) | Define alianza + costo |
| 12 | ¿Cuáles son las certificaciones target? (BRC / FSSC 22000 / ISO 22000) | OpEx anual certificaciones |
| 13 | ¿Cuánto vale el contrato CORFO patines? (300M / 350M / 400M CLP) | Ingreso transferencia tec firme |

### A3 — Accesos / infraestructura (NO operacional hoy)

| # | Necesidad | Para qué |
|---|---|---|
| 14 | Habilitar Postgres en Fly o crear Supabase project | Persistir datos reales (hoy solo SQLite local) |
| 15 | Domain custom para frontend Vercel (ej: `trongkai-platform.com`) | Compartir con directorio sin URL fea |
| 16 | Si querés activar `X-API-Key` auth en engine | comando: `flyctl secrets set ENGINE_API_KEY=$(openssl rand -hex 32) -a trongkai-engine` |
| 17 | Conectar IMAP corporativo Trongkai (si existe) | Ingesta automática de docs de Jaime/José |
| 18 | API key de Banco Central Chile (TC + inflación oficial) | Refresh automático de supuestos macroeconómicos |

---

## B. ACCIONES AUTÓNOMAS QUE PUEDO SEGUIR HACIENDO

### B1 — Sin tu input, mientras esperás respuestas

| Acción | Impacto | Esfuerzo |
|---|---|---|
| Render visual del **tornado de sensibilidades** en `/plan` (Bar chart horizontal) | Visual directorio | 1 turno |
| Export Excel con **5ta hoja "Escenarios Estratégicos"** + 6ta "TAM y Penetración" | Material directorio | 1 turno |
| Página `/dashboard-directorio` consolidada (3 KPIs grandes + tabla escenarios + Sankey) | Pitch a inversionistas | 1-2 turnos |
| Generar tearsheet PDF auto desde `/plan` (con identidad visual Trongkai) | Material LP / directorio | 2 turnos |
| Implementar **flujos de caja descontados con WACC variable año a año** (más realista) | Modelo más sofisticado | 1 turno |
| Agregar **stress test triple negativo** (precio↓ + costo↑ + delay año 1) automatizado | Análisis de riesgo | 1 turno |
| Refinamiento del rendimiento por MMPP con **DOE simulado** (Monte Carlo 10k corridas) | Bandas de confianza TIR | 2 turnos |
| Skill `/trongkai:directorio-pack` que genera PDF + Excel + email draft | One-click reporte | 2 turnos |
| Lista de pendientes regulatorios Ley REP 2026 (alertas automáticas) | Compliance proactivo | 1 turno |
| Calibración trimestral automática vía `trongkai-data-hunter` schedule cron | Datos siempre frescos | 30 min |

### B2 — Si activás infraestructura adicional

| Acción | Pre-requisito |
|---|---|
| Migración real de schema a Postgres + seed --apply | Fly Postgres habilitado |
| Multi-tenant: agregar segunda empresa al mismo schema (ej: Cehta) | Postgres + ADR-009 v2 |
| OAuth login (Google Workspace para José / Jaime / Claudia) | Decisión IDP |
| Webhooks a Slack del FIP CEHTA cuando hay alerta operacional roja | Slack workspace + webhook |
| Sincronización con Nubox para gastos reales | Acceso API Nubox Cehta |
| Integración Whisper para transcripts de reuniones → AuditLog | Carpeta compartida o sistema |

### B3 — Mejoras de modelo (sin requerir datos nuevos)

| Acción | Impacto |
|---|---|
| Modelar **estacionalidad** de precios (precio licopeno baja en cosecha de tomate) | Mejor stagger anual |
| Implementar **depreciación por activo** (no flat 10 años) | Mejor impuesto y EBITDA |
| Agregar **WACC term-structure** (más alto año 1-2, baja con derisking) | Más realista que WACC plano |
| **Working capital cíclico** (compra MMPP en temporada, paga 30-60 días después) | Cashflow real, no devengado |
| Modelo de **financiamiento** (mix deuda 60% / equity 40%) con escudo fiscal | Apalanca TIR |
| Régimen tributario **PYME ProPyme 25%** vs General 27% — toggle | Sensibilidad al régimen |
| Subsidios CORFO timing (cuándo entra la plata real) | Cashflow año 1-2 |

---

## C. DEPLOY A VERCEL — checklist

| Paso | Estado |
|---|---|
| Proyecto Vercel `nicolasrietta-1798s-projects/trongkai` creado | ✅ |
| GitHub repo linkeado (`Nikolaaa11/TrongkAI`) | ✅ |
| ENV var `NEXT_PUBLIC_ENGINE_URL` configurada (prod + preview + dev) | ✅ |
| `.vercelignore` excluye `apps/engine/**` para no triggerear FastAPI build | ✅ |
| Build command (`pnpm --filter @trongkai/web build`) | ✅ en `vercel.json` |
| Rate limit Vercel free 100/24h | ⏳ reseteado ~24h después del último deploy intentado |
| Primer deploy exitoso | ⏳ |

Una vez que deploye, la URL será:
- Production: `https://trongkai.vercel.app` o `https://trongkai-nicolasrietta-1798s-projects.vercel.app`
- Preview branches: auto en cada PR

---

## D. Priorización sugerida (los próximos 3 turnos)

1. **Intentar deploy Vercel** (rate limit debería haberse reseteado).
2. **Render del tornado de sensibilidades en UI** (alto valor visual con esfuerzo bajo).
3. **Página `/dashboard-directorio` consolidada** (KPIs + escenarios + Sankey en una vista).

Después de eso, decidir entre:
- **Modelo más sofisticado** (Monte Carlo + working capital + depreciación variable)
- **Compliance proactivo** (Ley REP 2026 alerts)
- **Material directorio** (PDF tearsheet auto + email draft)
- **Avanzar bloqueantes humanos** (esperar respuestas A1)

---

## E. Métricas para medir crecimiento de la plataforma

| Métrica | Target Q3 2026 | Hoy |
|---|---|---|
| Endpoints REST | 15+ | 10 |
| Páginas UI | 10+ | 7 |
| Supuestos OK_VALIDADO_DIRECTORIO | 25+ | 0 |
| Supuestos OK_PROVISORIO | 100+ | 63 |
| Tests verdes | 200+ | 120 |
| Cobertura motor | 85% | 67% |
| Documentos en docs/ | 15+ | 12 |
| Schedules autónomos | 8+ | 4 |
| Días sin downtime engine prod | meta 90+ | track desde hoy |
| Reuniones de directorio donde se usó el modelo | 4 anuales | 0 (aún) |
