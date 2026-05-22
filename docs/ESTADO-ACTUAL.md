# Estado actual de la plataforma TrongkAI

> Snapshot al **2026-05-19**. Última actualización vive en `git log` del repo.

## 1. Capacidades funcionales (qué puede hacer la plataforma HOY)

### 1.1 Operación de planta

| Capacidad | Endpoint | UI | Estado |
|---|---|---|---|
| Cuello de botella por etapa | `POST /bottleneck` | en `/agenda` (semáforo) | ✅ Vivo |
| Agenda anual de camiones por proveedor | `POST /agenda` | `/agenda` con slots por mes | ✅ Vivo |
| Balance de masa Modo A vs B + Sankey | `POST /mass-balance` | `/balance` lado-a-lado | ✅ Vivo |
| Validación cierre ±0.5% | engine interno | alerta visual delta > 5pp | ✅ |
| Detección alerta ROJA tiempo descomposición | en `/bottleneck` | banner en `/agenda` | ✅ |

### 1.2 Plan financiero 5 años

| Capacidad | Endpoint | UI | Estado |
|---|---|---|---|
| EERR mensual a 60 meses + KPIs | `POST /plan` | `/plan` con 5 KPI cards | ✅ |
| Export Excel formato directorio (4 hojas) | `POST /plan/export` | botón descarga en `/plan` | ✅ |
| Desglose por marca (Feed / Food / Servicios) | en `/plan` | 3 cards con ramp anual | ✅ |
| TAM + penetración por marca | en `/plan` | en cards (rojo si > 15%) | ✅ |
| 3 escenarios estratégicos (PILOTO/INDUSTRIAL/EXPANSION) | `GET /plan/escenarios-estrategicos` | tabla comparativa con ★ recomendado | ✅ |
| Tornado de sensibilidades ±20% | `POST /plan/tornado` | _falta render UI_ | API ✅ / UI pendiente |
| What-if 5 escenarios precargados | `POST /whatif` | `/whatif` con 3 paneles | ✅ |
| Snapshots no destructivos con hash SHA-256 | engine interno | — | ✅ |

### 1.3 Trazabilidad y compliance

| Capacidad | Estado |
|---|---|
| 165 supuestos catalogados (PD / OK_PROVISORIO / OK_VALIDADO) | ✅ |
| 12 supuestos PD promovidos a OK_PROVISORIO con fuente WebSearch trazable | ✅ |
| Trigger inmutabilidad de VersionPlan (Postgres) | ✅ schema |
| AuditLog de cambios en supuestos | ✅ schema |
| 12 ADRs documentados | ✅ |
| Top 11 RIESGO-SUPUESTOS con owner y sensibilidad TIR | ✅ |
| 18 preguntas abiertas catalogadas | ✅ |

## 2. Infraestructura desplegada

| Servicio | URL / Path | Estado |
|---|---|---|
| **Engine FastAPI** (10 endpoints) | https://trongkai-engine.fly.dev | ✅ Healthy en Fly.io región `gru` |
| **Frontend Next.js 14** (7 páginas) | local `:3010-3011` + proyecto Vercel `trongkai` | ⏳ Pendiente primer build Vercel |
| **DB SQLite local** (165 supuestos seedados) | `scripts/trongkai_local.db` | ✅ Funcional |
| **DB Postgres** (Fly secret DATABASE_URL existe) | Fly | ⏳ Schema no aplicado aún |
| **Repo GitHub** | https://github.com/Nikolaaa11/TrongkAI | ✅ 40+ commits |
| **Logo, identidad visual** | `apps/web/public/logo-trongkai-*.png` | ✅ Oficial |

## 3. Inteligencia y automatización

| Pieza | Función | Frecuencia |
|---|---|---|
| Agente `trongkai-architect` | Arquitectura, ADRs, decisiones estructurales | manual / on-demand |
| Agente `trongkai-data-hunter` | Refresh benchmarks via WebSearch | trimestral (manual hoy) |
| Agente `trongkai-financial` | Modelador financiero | manual |
| Agente `trongkai-improver` | Refactor lint, dead code, tests de cobertura | **cada 1 hora** (Task Scheduler) |
| Agente `trongkai-qa` | Suite tests, e2e | manual / pre-commit |
| Agente `trongkai-supuestos` | Detecta hardcodes, promueve PDs | manual |
| Agente `trongkai-mass-balance` | Validador del balance Sankey | manual |
| Agente `trongkai-bottleneck` | Calcula bottleneck + agenda camiones | manual |
| Schedule `TrongkAI-SupuestosAudit` | Auditoría semanal | lunes 09:00 |
| Schedule `TrongkAI-ValidateBalance` | Validación diaria del balance | diario 08:00 |
| Schedule `TrongkAI-Backup` | Backup Postgres diario | diario 03:00 |

## 4. Métricas de calidad

| Métrica | Valor |
|---|---|
| **Tests Python** | **120 / 120 verde** (subió de 21 → 78 → 120 esta sesión) |
| Tests e2e Playwright | 5 skeletons, no ejecutados aún |
| Cobertura engine | 67% promedio (agenda y whatif al 100%) |
| Lint ruff | limpio |
| Audit hardcodes | OK |
| Líneas Python producto | ~2.000 |
| Líneas Python tests | ~1.000 |
| Endpoints REST con auth graceful | 10/10 |

## 5. KPIs del plan base (calibrado con datos de mercado reales)

| KPI | Valor |
|---|---|
| **TIR proyecto anual** | **49,32%** sobre WACC 18% |
| **VAN @ WACC 18%** | $7,47B CLP (~USD 8M) |
| **Payback descontado** | 46 meses (3,8 años) |
| **EBITDA margin promedio** | 45% (industria) |
| **Ratio CapEx / Ventas** | 19,5% |

| Marca | Ingresos A5 | Volumen A5 | TAM | Penetración A5 |
|---|---|---|---|---|
| Trongkai FEED | $14,67B CLP | 6.450 ton | $165,6B | 8,86% |
| Trongkai FOOD | $12,00B CLP | 5.250 ton | $110,0B | 10,91% |
| Trongkai SERVICIOS | $0,10B CLP | (maquilas) | $3,0B | 3,20% |

## 6. Escenarios estratégicos comparados

| Escenario | Vol A5 | CapEx total | TIR | VAN | Payback |
|---|---|---|---|---|---|
| PILOTO | 25k ton | $9,0B | 29,75% | $1,43B | 55m |
| **★ INDUSTRIAL** | 50k ton | $15,0B | 49,32% | $7,47B | 46m |
| EXPANSION | 80k ton | $28,0B | 42,40% | $9,42B | 48m |

Recomendación heurística: **INDUSTRIAL**.

## 7. Documentación viva

12 documentos en `docs/`:
- `BALANCE-MASA.md` — spec del Módulo 2
- `DATOS-MERCADO.md` — benchmarks con fuentes URL trazables
- `DECISIONES.md` — 12 ADRs
- `GLOSARIO.md` — terminología técnica + comercial
- `INTELIGENCIA-COMPETITIVA.md` — TAM, salmoneras, regulación
- `INVENTARIO-EXCELS.md` — qué leyó el seed
- `KNOWN-ISSUES.md` — 6 issues priorizados
- `PREGUNTAS-ABIERTAS.md` — 18 preguntas + 6 al equipo Trongkai
- `PRESENTACION-INSIGHTS.md` — tesis comercial extraída
- `RIESGO-SUPUESTOS.md` — top 11 sensibilidades
- `RUNBOOK.md` — operación, backup, deploy
- `SUPUESTOS.md` — registro completo de 165 supuestos

## 8. Lo que NO puede hacer todavía

- Carga de Recepciones reales (no hay UI; sólo schema DB)
- Visualización del tornado de sensibilidades (endpoint sí, gráfica no)
- Login multi-usuario (es interno hoy, sin auth de usuarios)
- Generación automática de actas de directorio
- Integración con Nubox / SII / IMAP correo entrante
- Multi-tenant (sólo Trongkai por ahora, no Cehta o otros)
- Detección de anomalías financieras en tiempo real
- Generación automática de tearsheets PDF
