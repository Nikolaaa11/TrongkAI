# Balances Integrales Trongkai

> 4 balances interdependientes con closure controlado + cross-checks.

## Resumen

| # | Balance | Unidad | Closure | Alarma estrella |
|---|---|---|---|---|
| 1 | Producto (masa) | t/año | ±0.5% | Closure no cuadra |
| 2 | Energia | MWh/año | ±2% | Factor potencia < 0.92 (multa SEC) |
| 3 | Agua | m³/año | ±1% | Uso > 80% derecho DGA |
| 4 | RRHH | h/sem | 100% | Sem >45h regulares · >57h totales · Mes >32h extras (CT Chile) |

## Endpoints

| Endpoint | Cache | Descripcion |
|---|---|---|
| `GET /balance/energia` | 120s | Balance + Sankey + alarmas |
| `GET /balance/energia/sankey` | - | Solo Sankey |
| `GET /balance/agua` | 120s | Balance + Sankey + DGA |
| `GET /balance/agua/sankey` | - | Solo Sankey |
| `GET /balance/agua/cumplimiento-dga` | - | Estado pozos vs derechos |
| `GET /balance/rrhh?semana=YYYY-Wnn` | 60s | Trabajadores + asignaciones + alarmas |
| `GET /balance/rrhh/alarmas` | - | Solo alarmas (para dashboard) |
| `POST /balance/rrhh/asignar` | - | Asignar horas (devuelve alarmas) |
| `GET /balance/integrado` | 120s | Los 4 + cross-checks + score 0-100 |

## UI

| Path | Descripcion |
|---|---|
| `/balance` | Producto (masa) - ya existia |
| `/balance-energia` | KPIs + tabla 7 equipos + Sankey |
| `/balance-agua` | KPIs + DGA + tabla flujos + Sankey |
| `/balance-rrhh` | Banner alarmas + barras de progreso + editor inline |
| `/balance-integral` | Dashboard 2x2 + score global + intensidades + costos |

Acceso por menu: grupo `⚖️ Balances` en NavMenu.

## Alarmas RRHH (CT Chile)

Tres niveles segun Codigo del Trabajo:

| Tipo | Umbral | Severidad |
|---|---|---|
| `exceso_contrato` | Sem regulares > horas_contrato_semanal | alta |
| `exceso_legal` | Sem totales > 57h (45 + 12 extras max) | **critica** |
| `extras_semanal_excedido` | Sem extras > 12h (Art. 31 CT) | **critica** |
| `extras_mensual_excedido` | Mes extras > 32h | **critica** |

`POST /balance/rrhh/asignar` devuelve `tiene_alarma_critica: true` para que el
frontend muestre warning rojo inmediato.

## Cross-checks (en /balance/integrado)

1. **producto_vs_hh**: HH necesarias para producir el plan vs HH disponibles
2. **producto_vs_energia**: intensidad kWh/kg fuera de rango [2-5]
3. **energia_vs_agua_vapor**: caldera consumiendo vapor debe tener agua suficiente
4. **turno_noche**: al menos 2 trabajadores por turno de noche

## Score eficiencia global (0-100)

- **40 pts**: closure de cada balance (10 c/u)
- **30 pts**: deduccion por alarmas (-5 critica, -2 alta, -1 media)
- **30 pts**: KPIs vs benchmarks (mix renovable, FP, recirc, productividad, utilizacion, rotacion)

## Snapshot

`/api/snapshot` ahora retorna `balances`:

```json
{
  "balances": {
    "score_eficiencia_global": 82.0,
    "alarmas_criticas": 0,
    "alarmas_total": 6,
    "energia": { ... },
    "agua": { ... },
    "rrhh": { "alarmas_criticas_horas": 0 },
    "intensidades": { "energia_kwh_kg": 15.39, "agua_l_kg": 50.82, "hh_kg": 0.04 },
    "costos_anuales_usd": 882163
  }
}
```

## Schedule autonomo

`TrongkAI-BalancesAudit` — cada 6 horas:
1. Fetch `/balance/integrado`
2. Genera `entregables/Balances-YYYYMMDD-HHMM.html` (Apple-style)
3. Si hay alarmas criticas escribe `logs/balances-alert-*.md`
4. Marca evento en audit_trail

Install: `.\scripts\schedule_balances_audit.ps1 -Install`

## Persistencia

Datos editables en runtime (sobreviven deploy/restart):
- `data/balance-energia.json`
- `data/balance-agua.json`
- `data/balance-rrhh-trabajadores.json`
- `data/balance-rrhh-asignaciones.json`

Via volumen Fly `trongkai_data` (1GB en `/data`).

## Tests

| Suite | Tests |
|---|---|
| `test_balance_energia.py` | 16 |
| `test_balance_agua.py` | 15 |
| `test_balance_rrhh.py` | 20 |
| `test_balance_integrado.py` | 9 |
| **Total nuevos** | **60** |
| **Suite completa** | **458 verdes** |

## Datos seed

- **Energia**: 7 equipos piloto Parral (PEF Opticept, Micromolienda, Secador rotativo, Caldera biomasa, Compresores, Sistema vapor, Iluminacion)
- **Agua**: 5 flujos (Pozo 1 Parral 3 flujos, Red Essbio, Recirculado interno)
- **RRHH**: 15 trabajadores piloto (5 operarios + 2 supervisores + 3 calidad + 2 mantenimiento + 3 admin)

## Referencias

- Codigo del Trabajo Chile: Art. 22 (45h/sem) · Art. 31 (12h extras/sem ≈ 32h/mes)
- DGA: Direccion General de Aguas - derechos de aprovechamiento
- SEC: Superintendencia de Electricidad y Combustibles - FP min 0.92
- Benchmarks agroindustria: 2.5-4 kWh/kg, 5-15 L/kg (literatura LCA olivar/tomate)
