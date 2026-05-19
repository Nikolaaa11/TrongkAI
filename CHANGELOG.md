# Changelog

Todo cambio relevante se registra acá. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Chore
- `apps/engine/pyproject.toml`: removida la opción `asyncio_mode = "auto"` que generaba `PytestConfigWarning` en cada corrida (el plugin `pytest-asyncio` no está instalado en el entorno y el repo no tiene tests async). 78 tests verdes sin warnings, ruff `check .` limpio. — 2026-05-19
- `apps/engine/trongkai_engine/whatif.py`: hoist `datetime` import al top-level (estaba dentro de `create_snapshot`), consistente con el refactor previo en `repository.py`. 78 tests verdes, ruff `check .` limpio. — 2026-05-19
- `apps/engine/trongkai_engine/plan_builder.py`: loop sobre `por_marca.items()` reemplazado por `.values()` ya que la clave `marca` no se usaba (lint B007). 78 tests verdes, ruff `check .` limpio. — 2026-05-19
- `scripts/seed_sqlite.py`: eliminada variable `counts` no usada (lint F841). Ruff `check .` queda limpio. — 2026-05-19
- `scripts/audit_hardcodes.py`: `if` anidados colapsados con `and` (SIM102). 78 tests verdes. — 2026-05-19
- `scripts/audit_hardcodes.py`: removidos `PATTERN_HARDCODE` y `OK_MARKERS` que estaban declarados pero nunca referenciados; docstring acotado a lo que el script realmente verifica (TODO sin ref a SUPUESTOS.md). 78 tests verdes, audit OK. — 2026-05-19
- `scripts/extract_presentation.py`: orden alfabético de imports `pptx` antes de `pypdf` (lint I001). 78 tests verdes, ruff `check .` limpio. — 2026-05-19

## [0.2.0] — 2026-05-18 — Fases 1-6 completas

### Added — Fase 1 (Modelo de datos + seed)
- Migración SQL inicial `packages/db/prisma/migrations/0001_init/migration.sql` con 13 tablas, 11 enums y trigger de inmutabilidad de `VersionPlan`.
- Módulo de repositorio Python (`apps/engine/trongkai_engine/repository.py`) con psycopg3 + UPSERTs idempotentes + snapshot ADR-005.
- Seed escribe a Postgres real con `--apply`. Modo `--dry-run` para iterar sin DB.
- Campo `marca` en Producto (FEED / FOOD / SERVICIOS) — ADR-009.
- 11 tests `test_seed.py` validan integridad referencial sin DB.

### Added — Fase 2 (Módulo 1)
- Motor de planificación de agenda (`agenda.py`) que respeta el bottleneck por MMPP/temporada.
- Endpoint REST `/agenda` con respuesta JSON estructurada.
- Página `/agenda` con sliders + tabla de slots por mes (drill-down expandible).
- Dashboard `/` rediseñado: cuota contractual, suppliers ACTIVOS, capacidades, bloqueantes.
- 5 tests `test_agenda.py`.

### Added — Fase 3 (Módulo 2 UI)
- Componente `<SankeyChart>` con ECharts (`apps/web/components/SankeyChart.tsx`).
- `/balance` con comparador A vs B side-by-side + Sankey individual + alerta si delta > 5pp.
- Presets por MMPP que cargan parámetros validados del SUPUESTOS.md.

### Added — Fase 4 (Módulo 3)
- `plan_builder.py` con Plan 5 Años: 60 flujos mensuales, KPIs, ramp-up, ingresos accesorios.
- `excel_export.py` con export formato directorio (azul inputs, verde links, paréntesis para negativos, 4 hojas).
- Endpoints `/plan` y `/plan/export` (FileResponse).
- Página `/plan` con parámetros editables + 5 KPIs + tabla anual + descarga Excel.
- 6 tests `test_plan_builder.py` + 4 tests `test_excel_export.py`. Incluye **entregable M3** verificando caso Olivero 1 ($147.600 flete / 5.904 CLP/kg).

### Added — Fase 5 (Módulo 4)
- `whatif.py` con motor de simulación de escenarios + snapshots no destructivos con hash SHA-256.
- Soporte de overrides dot-path con casting automático de keys numéricas (CapEx por año).
- Endpoint `/whatif`.
- Página `/whatif` con 3 paneles comparativos + 5 preguntas tipo precargadas + tabla comparativa completa.
- 5 tests `test_whatif.py`.

### Added — Fase 6 (Endurecimiento)
- `scripts/backup_db.ps1` con retención 14 días daily + 12 meses monthly.
- `scripts/audit_hardcodes.py` que falla CI si hay TODO sin ref a SUPUESTOS.md.
- Playwright config + 5 smoke tests e2e (`apps/web/e2e/smoke.spec.ts`).
- `RUNBOOK.md` extendido: levantar entorno, backup/restore, recuperación incidentes, schedules, deploy.

### Added — Presentación corporativa integrada
- `docs/PRESENTACION-INSIGHTS.md` con tesis comercial, 3 líneas de negocio (Feed / Food / Servicios), equipo, mercado 800k ton/año.
- Logos oficiales en `apps/web/public/` + página `/about` con equipo, directorio, asesores, modelo circular en 3 pasos y compromiso ACV+SOPs.
- ADR-009 (estrategia de marca dual) + ADR-010 (identidad visual).
- Glosario ampliado: Trongkai Feed, Trongkai Food, Opticept, Axolot, ACV, SOPs, valorización en cascada, fraccionamiento inteligente, harina de pescado como benchmark.
- Top 10 RIESGO-SUPUESTOS actualizado con precio harina de pescado como variable #11.

### Stats finales
- **Tests**: 52/52 verdes (engine) + 5 e2e (web).
- **Endpoints REST**: 8 (`/health`, `/mass-balance`, `/bottleneck`, `/agenda`, `/financial/kpis`, `/plan`, `/plan/export`, `/whatif`).
- **Páginas Next.js**: 7 (`/`, `/agenda`, `/balance`, `/plan`, `/whatif`, `/supuestos`, `/about`).
- **Líneas Python**: ~1.500 producto + 380 tests.

## [Unreleased]

### Changed
- `apps/engine/trongkai_engine/main.py`: los 4 endpoints REST ahora declaran `tags`, `summary` y `description` para una documentación OpenAPI/Swagger autocontenida.

### Fixed
- Limpieza de lint en `apps/engine`: removidos 4 imports no usados (`BottleneckResult` en `main.py` y `tests/test_bottleneck.py`, `KPIsFinancieros` en `main.py`, `dataclasses.field` en `financial.py`) y migrado `typing.Iterable` → `collections.abc.Iterable` (UP035). Ruff baja de 7 a 2 errores; tests 21/21 verdes.

## [0.0.1] — 2026-05-18 — Fase 0 cerrada

### Added
- Estructura del monorepo `trongkai-platform/` con apps web/engine y packages db/shared-types.
- Motor de balance de masa Python (`apps/engine/trongkai_engine/mass_balance.py`) con modos A y B, validación de cierre ±0.5% y Sankey listo para ECharts.
- Motor de cuello de botella (`bottleneck.py`) con semáforo verde/amarilla/roja.
- Motor financiero base (`financial.py`) con TIR, VAN, payback descontado y armado para tornado chart.
- FastAPI con tres endpoints REST tipados (`/mass-balance`, `/bottleneck`, `/financial/kpis`).
- Suite de tests pytest: **21 tests, 21 pasando**, incluyendo el entregable de validación M2 (caso alperujo).
- Prisma schema completo con 13 modelos (Supplier, MateriaPrima, Recepcion, CapacidadEquipo, Producto, Supuesto, SupuestoAudit, PlanAnual, MixProduccionMensual, CapEx, OpEx, FlujoCaja, AuditLog, VersionPlan, TipoCambio).
- Script `scripts/seed-from-excel.py` que extrae 5 MMPP, 9 suppliers, 12 productos, 165 supuestos y 10 capacidades del Excel del cliente (dry-run sin DB OK).
- Frontend Next.js 14 + Tailwind con páginas: Dashboard operacional, Balance de masa (calculadora de modos A/B), Plan, What-if, Supuestos. Paleta tierra/oliva/trigo según §6 SUPER_PROMPT.
- Documentación completa: `SUPUESTOS.md` (~70 PDs catalogados), `GLOSARIO.md`, `DECISIONES.md` (8 ADRs incluyendo las contradicciones resueltas Jaime-vs-Trongkai), `BALANCE-MASA.md`, `PREGUNTAS-ABIERTAS.md` (18 preguntas bloqueantes/no bloqueantes), `RIESGO-SUPUESTOS.md` (top 10 sensibilidad TIR), `INVENTARIO-EXCELS.md`.
- Docker Compose con Postgres + Redis + engine + web.
- CI con tests + lint de confidencialidad (ADR-008: bloquea jerga de transcripts en código).

### Notas
- Capacidades de proceso (`SECADO`, `RECEPCION`, etc.) están todas en PD — bloqueante para Módulo 1 productivo.
- Precios de venta de los 12 SKUs están todos en PD — bloqueante para Módulo 3.
- Modo balance default (A o B) en PD hasta firma de José + Claudio (ADR-003).
