# Changelog

Todo cambio relevante se registra acá. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

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
