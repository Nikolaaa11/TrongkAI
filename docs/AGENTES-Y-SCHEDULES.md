# Agentes Claude + Skills + Schedules autónomos TrongkAI

> Inventario completo de la inteligencia automatizada de la plataforma.

## A. Agentes Claude especializados (10 agentes)

Cada uno vive en `~/.claude/agents/`. Se invocan vía `Task` o automáticamente desde schedules.

| Agente | Misión | Cuándo se invoca |
|---|---|---|
| `trongkai-architect` | Decisiones arquitectónicas, ADRs, refactors estructurales | Manual + on-demand |
| `trongkai-improver` | Refactor lint, dead code, cobertura tests | **Cada 1h** auto (TrongkAI-Improver) |
| `trongkai-supuestos` | Detecta hardcodes, promueve PDs → OK_PROVISORIO | Lunes 09:00 (TrongkAI-SupuestosAudit) |
| `trongkai-qa` | Test suite + e2e + regresiones | Diario 08:00 (TrongkAI-ValidateBalance) |
| `trongkai-mass-balance` | Valida balance Sankey + ±0.5% closure | Manual + en CI |
| `trongkai-bottleneck` | Calcula bottleneck + agenda camiones | Manual operacional |
| `trongkai-financial` | Modela escenarios financieros + tornado | Manual + antes de directorio |
| `trongkai-data-hunter` | WebSearch trimestral de benchmarks + precios | Trimestral manual |
| **`trongkai-esg-analyst`** (nuevo) | Carbon footprint + LCA + revenue créditos CO₂ | Mensual + roadshow ESG (TrongkAI-CarbonAudit) |
| **`trongkai-compliance-officer`** (nuevo) | Monitor Ley REP + cambios normativos | Lunes 09:00 (TrongkAI-ComplianceMonitor) |
| **`trongkai-banker`** (nuevo) | DSCR/LLCR/TIR equity + SLB + tax shield | Pre-pitch bancos / CORFO |
| **`trongkai-board-prep`** (nuevo) | Material directorio (Excel + summary + email) | Antes de cada reunión directorio |
| **`trongkai-monitor`** (nuevo) | SRE health check de toda la plataforma | **Cada 6h** auto (TrongkAI-MonitorHealth) |

## B. Skills `/trongkai:*` (10 skills)

Cada skill vive en `~/.claude/skills/trongkai/<nombre>/SKILL.md`. Se invocan con `/trongkai:nombre` o desde agentes.

| Skill | Función |
|---|---|
| `/trongkai:hunt-data` | Refresh trimestral benchmarks precios SKU |
| `/trongkai:start` | Bootstrap del proyecto en una sesión nueva |
| **`/trongkai:macro-refresh`** (nuevo) | Actualiza snapshot macro Chile (mindicador.cl) |
| **`/trongkai:carbon-audit`** (nuevo) | LCA 3 escenarios + revenue créditos CO₂ |
| **`/trongkai:compliance-check`** (nuevo) | Hitos REP próximos + alertas |
| **`/trongkai:directorio-pack`** (nuevo) | Material directorio one-command |
| **`/trongkai:financial-stress`** (nuevo) | Stress test triple negativo |
| **`/trongkai:papers-refresh`** (nuevo) | WebSearch papers científicos últimos 90 días |
| **`/trongkai:risk-report`** (nuevo) | Reporte risk committee consolidado |

## C. Schedules autónomos Windows (9 tareas)

Todos visibles con `Get-ScheduledTask | Where TaskName -like 'TrongkAI-*'`.

| Tarea | Cadencia | Owner | Acción |
|---|---|---|---|
| **TrongkAI-Improver** | Cada 1h | improver | Mejoras lint + dead code + tests cobertura |
| **TrongkAI-SupuestosAudit** | Lunes 09:00 | trongkai-supuestos | Audit PDs |
| **TrongkAI-ValidateBalance** | Diario 08:00 | trongkai-qa | Test suite + regresiones |
| **TrongkAI-Backup** | Diario 03:00 | backup_db.ps1 | Postgres snapshot |
| **TrongkAI-MacroRefresh** (nuevo) | Diario 06:00 | trongkai-data-hunter | Refresh macro Chile |
| **TrongkAI-ComplianceMonitor** (nuevo) | Lunes 09:00 | trongkai-compliance-officer | Hitos REP próximos |
| **TrongkAI-CarbonAudit** (nuevo) | Día 1 mensual 07:00 | trongkai-esg-analyst | Footprint + créditos CO₂ |
| **TrongkAI-MonitorHealth** (nuevo) | Cada 6h | trongkai-monitor | Health check end-to-end |
| **TrongkAI-PapersRefresh** (nuevo) | Trimestral (13 semanas) Dom 10:00 | trongkai-data-hunter | Búsqueda papers nuevos |

## D. Flujo de auto-mejora

```
TrongkAI-Improver (cada 1h)
  ↓ refactors + tests
TrongkAI-MonitorHealth (cada 6h)
  ↓ detecta breakage → revierte
TrongkAI-MacroRefresh (diario 06:00)
  ↓ Banco Central → snapshot interno
TrongkAI-ValidateBalance (diario 08:00)
  ↓ test suite verde mantiene release stability
TrongkAI-Backup (diario 03:00)
  ↓ snapshot Postgres
TrongkAI-ComplianceMonitor (lunes 09:00)
  ↓ alerta sobre hitos REP cercanos
TrongkAI-SupuestosAudit (lunes 09:00)
  ↓ promueve PDs → OK_PROVISORIO con fuente
TrongkAI-CarbonAudit (mensual 07:00)
  ↓ reporte LCA para sustainability office
TrongkAI-PapersRefresh (trimestral)
  ↓ literatura científica fresca → docs/PAPERS-CIENTIFICOS.md
```

## E. Cómo verificar que todo corre

```powershell
# Estado de schedules
Get-ScheduledTask | Where TaskName -like 'TrongkAI-*' | Format-Table TaskName, State, @{n='Próxima';e={(Get-ScheduledTaskInfo $_).NextRunTime}}

# Última corrida de cada uno
Get-ScheduledTask | Where TaskName -like 'TrongkAI-*' | Format-Table TaskName, @{n='LastRun';e={(Get-ScheduledTaskInfo $_).LastRunTime}}, @{n='LastResult';e={(Get-ScheduledTaskInfo $_).LastTaskResult}}

# Logs de la última semana
ls C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform\logs | Sort-Object LastWriteTime -Descending | Select-Object -First 15
```

## F. Recuperación si algo falla

1. **Schedule no corre**: verificar permisos + claude CLI path.
2. **Improver rompe tests**: TrongkAI-MonitorHealth detecta y propone revert.
3. **Macro refresh falla** (API down): fallback snapshot interno se usa.
4. **Engine prod down**: trongkai-monitor levanta alerta + propone `flyctl deploy`.

## G. Stats consolidadas de inteligencia automatizada

- **13 agentes especializados** trabajando sobre dominios distintos.
- **10 skills** para invocaciones rápidas.
- **9 schedules** corriendo 24/7 sin intervención humana.
- **Cada hora**: el improver mejora código.
- **Cada 6h**: monitor verifica que todo siga vivo.
- **Diario**: macro Chile actualizado, tests corridos, backup creado.
- **Semanal**: compliance + supuestos auditados.
- **Mensual**: footprint carbono reportado.
- **Trimestral**: papers científicos refreshed.

Es un sistema que se cuida solo.
