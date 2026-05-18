# Trongkai Platform — Biorrefinería Agrosphere

Plataforma inteligente para planificar, operar y simular la biorrefinería de **Trongkai** (filial industrial del FIP CEHTA ESG). Reemplaza los 3 Excels actuales por un sistema que:

- **Hace just-in-time real en planta** (Módulo 1)
- **Cuadra el balance de masa por construcción** (Módulo 2)
- **Produce un plan a 5 años defendible frente a directorio y CMF** (Módulo 3)
- **Permite decidir en horas, no en semanas** si conviene procesar tomasa o ampliar perujo (Módulo 4)

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui |
| Motor de cálculo | Python 3.11 + FastAPI + NumPy/Pandas/SciPy |
| Base de datos | PostgreSQL 15 + Prisma ORM |
| Cache / colas | Redis + BullMQ |
| Charts | Recharts + ECharts (Sankey) |
| Deploy | Docker Compose en servidor único |

Decisiones detalladas en [docs/DECISIONES.md](docs/DECISIONES.md).

## Estructura

```
trongkai-platform/
├── apps/
│   ├── web/                  # Next.js (UI + tRPC)
│   └── engine/               # FastAPI + motor de cálculo
├── packages/
│   ├── shared-types/         # Tipos compartidos (Zod schemas)
│   └── db/                   # Prisma schema + migrations + seed
├── contexto/                 # Excels y transcripts originales (no commitear a repo público)
├── docs/                     # Documentación viva
├── scripts/                  # Tooling (seed, exports, inventarios)
├── tests/
└── infra/                    # Docker Compose, observabilidad
```

## Quick start (después de Fase 1)

```powershell
# Levantar DB + Redis
docker compose up -d postgres redis

# Migrar
pnpm --filter @trongkai/db prisma migrate dev

# Sembrar desde los Excels del cliente
python scripts/seed-from-excel.py

# Arrancar motor Python
uv run --directory apps/engine fastapi dev

# Arrancar web
pnpm --filter @trongkai/web dev
```

## Estado

- **Fase 0** — Inventario y supuestos. ✅ Completada
- **Fase 1** — Modelo de datos + seed. 🚧 En curso
- **Fase 2-6** — Pendientes

## Documentación clave

- [SUPUESTOS.md](docs/SUPUESTOS.md) — Fuente única para hardcodes pendientes (~70 PDs hoy)
- [BALANCE-MASA.md](docs/BALANCE-MASA.md) — Especificación del motor de masa
- [PREGUNTAS-ABIERTAS.md](docs/PREGUNTAS-ABIERTAS.md) — Bloqueantes por fase
- [RIESGO-SUPUESTOS.md](docs/RIESGO-SUPUESTOS.md) — Top 10 variables que tumban la TIR
- [GLOSARIO.md](docs/GLOSARIO.md) — MMPP, PEF, PTEC, modos A/B, etc.
- [DECISIONES.md](docs/DECISIONES.md) — ADRs

## Confidencialidad

Los archivos en `contexto/*.txt` (transcripts) son **internos** y nunca se referencian en UI, exports a directorio o respuestas a CMF. ADR-008.
