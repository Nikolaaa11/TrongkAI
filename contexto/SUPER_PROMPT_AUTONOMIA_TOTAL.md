# SUPER PROMPT MAESTRO — Autonomía Total TrongkAI

> El negocio funciona solo. Este documento define la fuerza de trabajo
> autónoma (agentes + skills + schedules), sus contratos y sus límites.
> Todo agente/schedule DEBE leer `contexto/CONTEXTO_CANONICO.md` antes de
> actuar: ahí viven los números vigentes del modelo.

## 0. Misión

TrongkAI Platform opera, se audita, se mejora y reporta **sin intervención
humana diaria**. Nicolás interviene solo para: decisiones de negocio,
validación de inputs PD (cotizaciones reales) y aprobaciones externas.
Todo lo demás lo hace la fuerza de trabajo autónoma.

## 1. Arquitectura de la fuerza de trabajo

### Capa 1 — SCHEDULES (el latido, corren solos)
| Schedule | Cadencia | Qué hace | Agente que invoca |
|---|---|---|---|
| `trongkai-daily-pulse` | diario 08:30 | Health live + registra snapshot (historial diff) + lee alertas/decisiones + brief de 5 líneas | monitor |
| `trongkai-improver` | diario 15:00 | Una mejora real con tests verdes, commit, push, deploy si hay token | improver |
| `trongkai-weekly-audit` | lunes 09:00 | Coherencia de los 3 módulos de costo + tests + páginas live + reporte | qa |
| `trongkai-data-hunter` | viernes 10:00 | WebSearch de precios SKU / tarifas / macro → propone PD→PROVISORIO con fuente | data-hunter |

Reglas de los schedules:
- Cada run arranca SIN memoria → el prompt es autosuficiente.
- Primero leer `CONTEXTO_CANONICO.md`; si el run cambia números canónicos,
  ACTUALIZARLO y commitearlo.
- Nada se reporta como hecho sin verificarse contra producción
  (`trongkai-engine.fly.dev` / `trongkai-web.vercel.app`).
- Si Fly no tiene token (`flyctl auth whoami` falla), NO deployar backend:
  commitear, pushear y avisar "deploy pendiente de flyctl auth login".

### Capa 2 — AGENTES (especialistas bajo demanda, en `~/.claude/agents/`)
| Agente | Rol | Cuándo se activa |
|---|---|---|
| trongkai-architect | Decisiones estructurales, fases, ADRs | Cambios grandes |
| trongkai-improver | Mejora continua autónoma (NUNCA rompe tests) | Schedule diario |
| trongkai-monitor | SRE: health engine+web, schedules vivos | Daily pulse |
| trongkai-qa | Suite pytest + coherencia + lint confidencialidad | Pre-commit / lunes |
| trongkai-financial | Plan 5y, EERR, TIR/VAN, tornado | Análisis financiero |
| trongkai-banker | Deuda/equity, DSCR, SLB, pitch bancos | Pre-reunión financiamiento |
| trongkai-esg-analyst | Carbono, LCA, créditos CO₂, fondos ESG | Pre-roadshow ESG |
| trongkai-compliance-officer | Ley REP, Hoja Ruta 2040, certificaciones | Cambios normativos |
| trongkai-data-hunter | Calibración trimestral con fuentes web | Schedule viernes |
| trongkai-supuestos | Custodio PD→OK_PROVISORIO→OK_VALIDADO | Cambios numéricos |
| trongkai-mass-balance | Cierre ±0.5%, Sankey, modos A/B | Cambios mass_balance |
| trongkai-bottleneck | Flujo máximo, agenda camiones | Cambios capacidades |
| trongkai-board-prep | Material directorio en 5 min | Pre-reunión board |

### Capa 3 — SKILLS (comandos del usuario, en `~/.claude/skills/trongkai/`)
`/trongkai:status` (estado total) · `/trongkai:improve` (pasada de mejora) ·
`/trongkai:eerr` · `/trongkai:directorio-pack` · `/trongkai:hunt-data` ·
`/trongkai:validate-balance` · `/trongkai:supuestos-audit` ·
`/trongkai:financial-stress` · `/trongkai:risk-report` · `/trongkai:carbon-audit` ·
`/trongkai:compliance-check` · `/trongkai:macro-refresh` · `/trongkai:papers-refresh` ·
`/trongkai:fase-checkpoint` · `/trongkai:sync-context` (regenera CONTEXTO_CANONICO)

## 2. Contratos no negociables (TODOS los agentes/schedules)

1. **Verdad única**: el costo del piloto viene de `simular_con_revenue`;
   los KPIs del plan, de `/api/snapshot`. Nunca recalcular por fuera ni
   citar números de memoria — leer CONTEXTO_CANONICO o el API live.
2. **Cadena anclada**: simulador → revenue → predicción dan EL MISMO número.
   Cualquier cambio al modelo corre `pytest tests/` (623+) antes de commit.
3. **Honestidad del modelo**: el piloto es deficitario por diseño; la
   rentabilidad emerge a escala con SKU de valor. PROHIBIDO maquillar.
4. **Niveles de dato**: todo número nuevo entra como PD con fuente y fecha;
   solo Nicolás o una cotización firme lo sube a VALIDADO.
5. **Commits semánticos** + push a main. Deploy: Fly (backend) y
   `vercel deploy --prod --yes` (frontend) + verificación LIVE con curl.
   Los pipelines NUNCA se encadenan con `| tail` sin chequear el error real.
6. **Presupuesto de cambio**: el improver hace UNA mejora por run, chica y
   completa, antes que tres a medias. Si los tests fallan → revert, reporta.
7. **Lo que NO se hace solo**: enviar emails/mensajes externos, publicar
   fuera de la plataforma, gastar dinero, tocar otros proyectos Cehta,
   cambiar supuestos VALIDADOS. Eso se PROPONE y espera a Nicolás.

## 3. Flujo de información

```
WebSearch/inbox → data-hunter → propuestas PD (con fuente)
                                  ↓
Nicolás valida → parametros/variables → motor recalcula TODO
                                  ↓
daily-pulse registra snapshot → diff "qué cambió" en /comando
                                  ↓
weekly-audit verifica coherencia → improver corrige drift
                                  ↓
board-prep/LP-pack consumen snapshot → directorio e inversionistas
```

## 4. Estado pendiente de humano (revisar en cada daily-pulse)

- `flyctl auth login` si el token expiró (bloquea deploy backend).
- Completar `/equipo` (placeholders visibles a LPs).
- Validar inputs PD top: precio venta por SKU, arriendo PEF.
- Subir archivos del equipo a `inbox/`.

## 5. Criterio de éxito de la autonomía

- Cada mañana hay un brief fresco sin que nadie lo pida.
- El historial de snapshots crece solo → el diff de /comando siempre vivo.
- La exactitud del modelo solo puede SUBIR (nadie degrada validaciones).
- Cero números divergentes entre páginas, PDF, Excel y agentes.
- Nicolás dedica su tiempo a decisiones, no a operación.
