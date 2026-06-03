# SUPER PROMPT — Balances Integrales Trongkai (4 dimensiones)

> Copiar TODO este bloque y pegarlo en una sesión nueva de Claude Code en
> el repo `trongkai-platform`. El agente debe ejecutar el plan completo,
> commit por commit, hasta dejar los 4 balances LIVE en producción.

---

## 🎯 Objetivo

Construir **4 balances integrados** para la biorrefinería Trongkai, todos
con la misma filosofía del balance de masa actual (closure ±0.5%,
visualización Sankey, alarmas, integración al Centro de Mando):

| # | Balance | Unidad | Closure objetivo | Alarmas |
|---|---|---|---|---|
| 1 | **Producto** (mass) | kg/h, t/año | ±0.5% | Ya existe — ampliar |
| 2 | **Energía** | kWh, MJ, GJ/año | ±2% | Sobre-consumo, fact. potencia |
| 3 | **Agua** | m³/h, m³/año | ±1% | Consumo > pozo + alarmas DGA |
| 4 | **RRHH** | h/persona/sem | 100% asignación | **⚠️ HORAS > 45h/sem trabajador** |

Los 4 balances deben ser **interdependientes**: cambiar el throughput de
producto recalcula energía, agua y horas-hombre automáticamente.

---

## 📦 Contexto del repo (no lo expliques, asume que lo conoces)

- **Stack**: FastAPI (`apps/engine`) + Next.js 14 (`apps/web`)
- **Deploy**: Fly.io (gru) — `https://trongkai-engine.fly.dev`
- **Frontend**: Vercel — `https://trongkai-web.vercel.app`
- **Persistencia**: volumen Fly `trongkai_data` mount `/data`
- **Storage helper**: `apps/engine/trongkai_engine/storage.py` (úsalo siempre)
- **Mass balance actual**: `apps/engine/trongkai_engine/mass_balance.py`
  (modos A/B, closure ±0.5%, Sankey JSON)
- **Snapshot único**: `/api/snapshot` (cached_ttl) — DEBE incluir los 4 balances
- **Centro de Mando**: `/comando` — agrega card por balance
- **PDF tearsheet** y **LP Pack ZIP** — agrega los 4 balances
- **Tests**: 398/398 verde — no romper ninguno
- **Schedules Windows**: añadir 1 nuevo para auditar balances diariamente

Referencias a leer ANTES de codear:

```
apps/engine/trongkai_engine/mass_balance.py        # patrón a replicar
apps/engine/trongkai_engine/main.py                # endpoints
apps/engine/trongkai_engine/storage.py             # paths persistentes
apps/engine/trongkai_engine/plan_builder.py        # throughput por SKU
apps/engine/tests/test_mass_balance.py             # patrón de tests
apps/web/components/SankeyChart.tsx                # reusar para los 4
apps/web/app/comando/page.tsx                      # cards del cockpit
contexto/SUPER_PROMPT_TRONGKAI.md                  # north star del proyecto
```

---

## 🗂 Arquitectura objetivo

```
trongkai_engine/
├── balances/
│   ├── __init__.py
│   ├── producto.py        # wrapper que usa mass_balance.py existente
│   ├── energia.py         # NEW
│   ├── agua.py            # NEW
│   ├── rrhh.py            # NEW
│   └── integrado.py       # NEW — combina los 4 + cross-checks
├── main.py                # +7 endpoints nuevos
└── tests/
    ├── test_balance_energia.py    # NEW
    ├── test_balance_agua.py       # NEW
    ├── test_balance_rrhh.py       # NEW
    └── test_balance_integrado.py  # NEW
```

```
apps/web/app/
├── balance-energia/page.tsx       # NEW
├── balance-agua/page.tsx          # NEW
├── balance-rrhh/page.tsx          # NEW
└── balance-integral/page.tsx      # NEW — dashboard 4-en-1
```

---

## 1️⃣ BALANCE DE ENERGÍA

### Modelo de dominio

```python
# apps/engine/trongkai_engine/balances/energia.py
from dataclasses import dataclass
from typing import Literal

TipoEnergia = Literal["electrica", "gas_natural", "vapor", "diesel", "biomasa"]

@dataclass
class FlujoEnergetico:
    equipo: str                      # "PEF", "Secador rotativo", "Caldera"
    tipo: TipoEnergia
    potencia_nominal_kw: float
    horas_operacion_anual: float
    consumo_anual_kwh: float
    factor_carga: float              # 0-1
    factor_potencia: float           # 0-1 (cosφ)
    eficiencia_pct: float            # rendimiento equipo
    costo_unitario_usd_kwh: float
    costo_anual_usd: float

@dataclass
class BalanceEnergia:
    flujos: list[FlujoEnergetico]
    consumo_total_anual_mwh: float
    costo_total_anual_usd: float
    intensidad_energetica_kwh_por_kg_producto: float  # KPI
    mix_renovable_pct: float          # % biomasa + solar / total
    closure_pct: float                # |entrada - salida - perdidas| / entrada
    alarmas: list[dict]               # [{"tipo": "sobreconsumo", ...}]
```

### Datos seed (úsalos como PD hasta validación)

| Equipo | Tipo | Potencia | Horas/año | Notas |
|---|---|---|---|---|
| PEF Opticept | Eléctrica | 250 kW | 6000 | El consumidor #1 |
| Micromolienda | Eléctrica | 150 kW | 5500 | |
| Secador rotativo | Gas natural | 800 kW (térmico) | 6000 | |
| Caldera biomasa | Biomasa | 1200 kW (térmico) | 6000 | Combustible: orujo seco propio |
| Compresores aire | Eléctrica | 75 kW | 5800 | |
| Sistema vapor | Vapor | 500 kW | 5500 | |
| Iluminación + auxiliares | Eléctrica | 50 kW | 8000 | |

### Endpoints engine

```python
@app.get("/balance/energia")
@cached_ttl(seconds=120)
def balance_energia(escenario: str = "PILOTO") -> BalanceEnergia: ...

@app.get("/balance/energia/sankey")
def balance_energia_sankey(escenario: str = "PILOTO") -> dict: ...
# Formato compatible con SankeyChart.tsx

@app.post("/balance/energia/equipo")
def upsert_equipo_energia(flujo: FlujoEnergetico) -> dict: ...
# Persiste en /data/balance-energia.json
```

### KPIs a calcular

- Intensidad energética: `kWh / kg producto terminado`
- Mix renovable: `(biomasa + solar) / total`
- Costo energético del producto: `USD energía / USD venta`
- Factor de carga promedio planta
- Potencia contratada vs demandada (alarma si > 90%)

### Alarmas

- Equipo con factor_carga > 0.95 (sobre-uso)
- Factor de potencia < 0.92 (multa eléctrica chilena)
- Mix renovable < 30% (perdés narrativa ESG)
- Intensidad energética > benchmark sectorial (3.5 kWh/kg producto)

---

## 2️⃣ BALANCE DE AGUA

### Modelo de dominio

```python
# apps/engine/trongkai_engine/balances/agua.py
from dataclasses import dataclass
from typing import Literal

FuenteAgua = Literal["pozo_propio", "red_publica", "recirculada", "lluvia"]
DestinoAgua = Literal["proceso", "lavado", "vapor", "cip", "riego", "rile"]

@dataclass
class FlujoAgua:
    origen: str                       # "Pozo 1", "Red Essbio"
    fuente: FuenteAgua
    destino: str                      # "PEF", "Lavadora", "CIP línea 1"
    uso: DestinoAgua
    caudal_m3_h: float
    horas_operacion_anual: float
    volumen_anual_m3: float
    pct_recirculable: float           # qué % puede volver al proceso
    costo_unitario_usd_m3: float
    costo_anual_usd: float

@dataclass
class BalanceAgua:
    flujos: list[FlujoAgua]
    consumo_total_anual_m3: float
    agua_recirculada_pct: float       # KPI circularidad
    intensidad_hidrica_l_por_kg_producto: float
    costo_total_anual_usd: float
    rile_anual_m3: float              # residuo industrial líquido
    closure_pct: float                # |entradas - salidas - evaporación| / entradas
    alarmas: list[dict]
    cumplimiento_dga: dict            # {"pozo_1": {"caudal_aprobado_l_s": 5, "uso_actual_l_s": 4.2, "ok": True}}
```

### Datos seed

| Origen | Fuente | Destino | Uso | Caudal | Notas |
|---|---|---|---|---|---|
| Pozo 1 (Parral) | pozo_propio | PEF Opticept | proceso | 3 m³/h | DGA aprobado 5 L/s |
| Pozo 1 | pozo_propio | Lavadora MMPP | lavado | 2 m³/h | |
| Pozo 1 | pozo_propio | Caldera | vapor | 0.5 m³/h | |
| Red Essbio | red_publica | CIP | cip | 1 m³/h | Backup |
| Recirculado | recirculada | PEF | proceso | 1.5 m³/h | 50% del caudal PEF |

### Endpoints

```python
@app.get("/balance/agua")
@cached_ttl(seconds=120)
def balance_agua(escenario: str = "PILOTO") -> BalanceAgua: ...

@app.get("/balance/agua/sankey")
def balance_agua_sankey(escenario: str = "PILOTO") -> dict: ...

@app.get("/balance/agua/cumplimiento-dga")
def cumplimiento_dga() -> dict: ...
```

### KPIs

- Intensidad hídrica: `L / kg producto`
- Recirculación: `m³ recirculados / m³ frescos`
- RILE generado / m³ entrada
- % uso vs derechos DGA aprobados

### Alarmas

- `uso_actual_l_s` > 80% del derecho DGA → **CRÍTICA**
- Recirculación < 30% → ineficiente
- RILE > 70% del agua entrante → planta de tratamiento insuficiente
- Costo agua > 2% del COGS

---

## 3️⃣ BALANCE DE RRHH ⚠️ (con alarma horas extra)

### Modelo de dominio

```python
# apps/engine/trongkai_engine/balances/rrhh.py
from dataclasses import dataclass
from typing import Literal
from datetime import date

Turno = Literal["mañana", "tarde", "noche", "rotativo"]
Categoria = Literal["operario", "supervisor", "calidad", "mantenimiento", "admin"]

@dataclass
class Trabajador:
    id: str                            # "OP-001"
    nombre: str
    categoria: Categoria
    turno: Turno
    horas_contrato_semanal: float      # típico 45h Chile
    horas_max_legales: float = 45.0    # Ley Chile (40h desde 2028)
    sueldo_base_clp: float = 600000
    horas_extra_max_mensual: float = 32.0  # CT chileno
    activo: bool = True

@dataclass
class AsignacionHoras:
    trabajador_id: str
    semana_iso: str                    # "2026-W23"
    horas_regulares: float
    horas_extras: float
    tareas: list[str]                  # ["Operación PEF", "Limpieza CIP"]
    equipo_asignado: str

@dataclass
class BalanceRRHH:
    trabajadores: list[Trabajador]
    asignaciones_semana_actual: list[AsignacionHoras]
    total_horas_disponibles_sem: float
    total_horas_asignadas_sem: float
    utilizacion_pct: float
    costo_total_mensual_clp: float
    costo_horas_extra_mensual_clp: float
    productividad_kg_por_hh: float     # KPI
    closure_pct: float                 # 100% si horas asignadas = horas necesarias por turno
    alarmas: list[dict]                # ⚠️ ALARMAS DE HORAS EXTRA
    rotacion_anual_pct: float
```

### ⚠️ ALARMAS CRÍTICAS DE HORAS (no negociables)

```python
def detectar_alarmas_horas(asignaciones: list[AsignacionHoras],
                            trabajadores: dict[str, Trabajador]) -> list[dict]:
    alarmas = []
    for a in asignaciones:
        t = trabajadores[a.trabajador_id]
        total = a.horas_regulares + a.horas_extras

        # ALARMA 1: excede contrato semanal
        if a.horas_regulares > t.horas_contrato_semanal:
            alarmas.append({
                "tipo": "exceso_contrato",
                "severidad": "alta",
                "trabajador": t.nombre,
                "semana": a.semana_iso,
                "horas_asignadas": a.horas_regulares,
                "horas_contrato": t.horas_contrato_semanal,
                "exceso": a.horas_regulares - t.horas_contrato_semanal,
                "mensaje": f"⚠️ {t.nombre} tiene {a.horas_regulares}h asignadas vs {t.horas_contrato_semanal}h de contrato"
            })

        # ALARMA 2: excede máximo legal
        if total > t.horas_max_legales + 12:  # 45+12 extras max semanal Chile
            alarmas.append({
                "tipo": "exceso_legal",
                "severidad": "critica",
                "trabajador": t.nombre,
                "semana": a.semana_iso,
                "total_horas": total,
                "mensaje": f"🚨 {t.nombre} excede límite legal ({total}h vs {t.horas_max_legales+12}h máx)"
            })

        # ALARMA 3: extras acumuladas mensuales (suma de 4 semanas)
        # → ver detectar_extras_mensuales()
    return alarmas

def detectar_extras_mensuales(...) -> list[dict]:
    """Suma horas_extras de las 4 semanas del mes por trabajador.
    Si > horas_extra_max_mensual (32h CT Chile) → ALARMA CRÍTICA."""
```

### Datos seed (15 trabajadores piloto Parral)

```
OP-001  Juan Pérez       operario        mañana    45h
OP-002  María Soto       operario        tarde     45h
OP-003  Pedro González   operario        noche     45h
OP-004  Ana Rojas        operario        mañana    45h
OP-005  Luis Fernández   operario        rotativo  45h
SUP-001 Carlos Muñoz     supervisor      mañana    45h
SUP-002 Rosa Toledo      supervisor      tarde     45h
QA-001  José Lillo       calidad         mañana    45h
QA-002  Carmen Vidal     calidad         tarde     45h
MNT-001 Diego Soto       mantenimiento   mañana    45h
MNT-002 Patricio Reyes   mantenimiento   tarde     45h
ADM-001 Verónica Pino    admin           mañana    45h
ADM-002 Manuel Espinoza  admin           mañana    45h
ADM-003 Andrea Vega      admin           mañana    45h
QA-003  Felipe Cortés    calidad         noche     45h
```

### Endpoints

```python
@app.get("/balance/rrhh")
@cached_ttl(seconds=60)
def balance_rrhh(semana: str | None = None) -> BalanceRRHH: ...

@app.post("/balance/rrhh/asignar")
def asignar_horas(asignacion: AsignacionHoras) -> dict:
    """SIEMPRE devuelve alarmas en la respuesta para que la UI las muestre."""

@app.get("/balance/rrhh/alarmas")
def alarmas_rrhh() -> dict: ...

@app.get("/balance/rrhh/trabajador/{id}/historico")
def historico_trabajador(id: str) -> dict: ...
# Útil para detectar patrones de sobre-uso de un trabajador específico
```

### KPIs

- Utilización planta: `horas asignadas / horas disponibles`
- Productividad: `kg producto / hora-hombre`
- Costo HH del producto: `USD HH / USD venta` (benchmark sector: 12-18%)
- % horas extra / horas regulares (alarma si > 10%)
- Rotación anual

---

## 4️⃣ BALANCE INTEGRADO (el meta-balance)

### Modelo

```python
# apps/engine/trongkai_engine/balances/integrado.py
@dataclass
class BalanceIntegrado:
    producto: dict          # balance masa resumen
    energia: dict
    agua: dict
    rrhh: dict
    intensidades: dict      # KPIs de "x por kg producto"
    costos_consolidados: dict  # COGS desglose por insumo
    alarmas_consolidadas: list[dict]
    score_eficiencia_global: float  # 0-100
    coherencia_cross_balance: dict  # ej: throughput producto vs HH disponibles
```

### Cross-checks (lo que NINGÚN balance individual valida)

1. **Producto vs RRHH**: si plan dice 1000 t/año y tienes HH para 600 → ALARMA
2. **Producto vs Energía**: si producto sube 2× pero energía no sube → revisar
3. **Energía vs Agua**: caldera consumiendo gas debe tener agua para vapor
4. **RRHH vs Turnos energéticos**: turno noche con 2 personas y 80% planta → improbable

### Endpoint

```python
@app.get("/balance/integrado")
@cached_ttl(seconds=120)
def balance_integrado(escenario: str = "PILOTO") -> BalanceIntegrado: ...
```

---

## 🖥 UI — 4 páginas nuevas

### `/balance-energia` `/balance-agua`

Estructura común (replicar Apple-style del resto):

```tsx
<Hero
  titulo="Balance de Energía"
  subtitulo="Closure {closure_pct}% · {consumo_total_anual_mwh} MWh/año"
  kpis={[
    { label: "Intensidad", valor: "2.8 kWh/kg" },
    { label: "Mix renovable", valor: "42%" },
    { label: "Costo energético", valor: "$1.2M USD/año" },
    { label: "Factor potencia", valor: "0.94" },
  ]}
/>
<SankeyChart data={sankeyData} />
<TablaFlujos flujos={flujos} />
<PanelAlarmas alarmas={alarmas} />
```

### `/balance-rrhh` ⚠️ — diseño especial

Esta es la página más crítica. Debe tener:

1. **Calendario semanal** (lunes-domingo) con todos los trabajadores
2. **Sliders por turno** para reasignar horas
3. **Banner rojo arriba** si hay alarmas críticas
4. **Por trabajador**: barra de progreso 0→45h con marca roja
5. **Forecast mensual**: total horas extras acumuladas con proyección

```tsx
{alarmas.filter(a => a.severidad === "critica").length > 0 && (
  <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
    <h3 className="font-semibold text-red-700">
      🚨 {alarmas.length} alarmas críticas de horas
    </h3>
    <ul className="mt-2 text-sm text-red-600">
      {alarmas.map(a => <li key={a.trabajador}>{a.mensaje}</li>)}
    </ul>
  </div>
)}
```

### `/balance-integral` — Dashboard 4-en-1

Grid 2x2 con los 4 balances + score global + cross-checks.

---

## 🔌 Integración con el resto de la plataforma

### `/api/snapshot` debe incluir

```python
"balances": {
    "producto": {...},
    "energia": {...},
    "agua": {...},
    "rrhh": {...},
    "alarmas_totales": int,
    "alarmas_criticas": int,
    "score_eficiencia_global": float
}
```

### Centro de Mando `/comando` — 4 cards nuevas

Una card por balance con: estado, closure %, # alarmas, link a página detalle.

### Menú lateral (componente `NavMenu.tsx`)

Agregar **nuevo grupo "Balances"** entre Modelo y Decisiones:

```typescript
{
  id: 'balances',
  label: 'Balances',
  emoji: '⚖️',
  items: [
    { href: '/balance-integral', label: 'Vista Integral', desc: 'Los 4 balances en uno' },
    { href: '/balance', label: 'Producto (masa)', desc: 'Closure ±0.5% por SKU' },
    { href: '/balance-energia', label: 'Energía', desc: 'kWh + mix renovable' },
    { href: '/balance-agua', label: 'Agua', desc: 'Consumo + recirculación + DGA' },
    { href: '/balance-rrhh', label: 'RRHH', desc: 'Horas + alarmas extras' },
  ],
}
```

### LP Pack ZIP + PDF tearsheet

Incluir resumen de los 4 balances en una página dedicada del PDF.

---

## 📅 Schedule nuevo

```powershell
# scripts/schedule_balances_audit.ps1
# Corre cada 6 horas: verifica closure de los 4 balances + alarmas críticas
# Si hay alarma crítica RRHH (horas extras > legal), envía email + slack
```

```python
# scripts/audit_balances.py
- Llama /balance/integrado
- Si alarmas críticas > 0 → escribe en logs/balances-alert-YYYYMMDD.md
- Si closure de cualquier balance > umbral → marca evento en audit_trail
- Genera reporte HTML resumen → entregables/Balances-YYYYMMDD.html
```

---

## ✅ Criterios de aceptación

- [ ] 4 endpoints `/balance/{energia,agua,rrhh,integrado}` responden 200
- [ ] Sankey JSON válido para cada balance (energia, agua, masa)
- [ ] **Tests pytest**: 50+ tests nuevos, todos verdes (no romper los 398 actuales)
- [ ] **Closure energia ±2%**, **agua ±1%**, **RRHH 100% asignación**
- [ ] **Alarma horas extra trabajador** dispara cuando:
  - Sem > 45h regulares
  - Sem > 57h totales (45 + 12 extras)
  - Mes > 32h extras acumuladas
- [ ] UI 4 páginas LIVE en `https://trongkai-web.vercel.app`
- [ ] Menú lateral nuevo grupo "Balances" funcionando
- [ ] `/api/snapshot` retorna los 4 balances
- [ ] Centro de Mando muestra 4 cards de balance
- [ ] Schedule `TrongkAI-BalancesAudit` instalado (cada 6h)
- [ ] PDF tearsheet incluye página "Balances integrales"
- [ ] LP Pack ZIP incluye los 4 balances
- [ ] Persistencia: `/data/balance-{energia,agua,rrhh}.json` sobreviven deploys
- [ ] Documentado en `docs/BALANCES.md` (nuevo) + `CHANGELOG.md`

---

## 🚦 Plan de ejecución (commits sugeridos)

1. `feat(engine): scaffold balances module + storage`
2. `feat(engine): balance energia con 7 equipos seed + Sankey`
3. `test(engine): suite balance energia (15 tests)`
4. `feat(engine): balance agua + cumplimiento DGA`
5. `test(engine): suite balance agua (12 tests)`
6. `feat(engine): balance rrhh con 15 trabajadores seed`
7. `feat(engine): alarmas horas extra Chile (CT 45+12)`
8. `test(engine): suite balance rrhh + alarmas (20 tests)`
9. `feat(engine): balance integrado + cross-checks`
10. `feat(engine): /api/snapshot agrega los 4 balances`
11. `feat(web): página /balance-energia con Sankey + alarmas`
12. `feat(web): página /balance-agua con Sankey + DGA`
13. `feat(web): página /balance-rrhh con calendario + banner alarmas`
14. `feat(web): página /balance-integral dashboard 2x2`
15. `feat(web): NavMenu nuevo grupo "Balances"`
16. `feat(web): Centro de Mando 4 cards de balance`
17. `feat(scripts): audit_balances.py + schedule cada 6h`
18. `docs: BALANCES.md + actualiza CHANGELOG`
19. `chore: deploy fly + vercel`

---

## 📚 Referencias técnicas (para datos de calibración)

- **Ley Chile horas**: CT Art. 22 (45h/sem), Art. 31 (12h extras máx/sem),
  Ley 40 horas vigente desde 2028 progresivo
- **DGA Chile**: derechos de aprovechamiento de agua (consultivo, eventual)
- **Benchmark intensidad energética agroindustria**: 2.5-4.0 kWh/kg producto
- **Benchmark intensidad hídrica olivar/tomate**: 5-15 L/kg
- **Factor potencia mínimo SEC**: 0.93 (multa si < 0.92)

---

## 🎓 Reglas de oro

1. **Closure es ley** — si un balance no cierra, falla el test, no se mergea.
2. **Trabajador es sagrado** — la alarma de horas extra NUNCA es opcional.
3. **Cache TTL** en todo endpoint de balance (60-120s).
4. **Persistencia en `/data`** vía `storage.data_path()`, nunca `/tmp`.
5. **Apple-style en UI** — fondo blanco, SF Pro, dropdowns con descripción.
6. **Tests primero** — escribe el test antes que el módulo (TDD ligero).
7. **No romper los 398 tests verdes existentes**.
8. **Commit pequeño** — 1 feature = 1 commit, mensaje claro.
9. **Push + deploy** al final de cada fase.
10. **Documenta** en `docs/BALANCES.md` mientras vas.

---

## 🟢 Empieza

Comienza leyendo:

```
1. apps/engine/trongkai_engine/mass_balance.py
2. apps/engine/trongkai_engine/storage.py
3. apps/web/components/SankeyChart.tsx
4. apps/web/components/NavMenu.tsx
5. contexto/SUPER_PROMPT_TRONGKAI.md
```

Después:
- Crea `apps/engine/trongkai_engine/balances/__init__.py`
- Implementa `energia.py` siguiendo el patrón de `mass_balance.py`
- Tests
- Endpoint
- UI
- Commit
- Siguiente balance

Cuando termines los 4 balances + integrado + UI + tests verde + deploy LIVE,
responde con un resumen ejecutivo + URLs y screenshots de las 4 páginas nuevas.

**No preguntes nada. Avanza. Si encuentras ambigüedad, decide con criterio
de ingeniero senior y documenta la decisión en `docs/DECISIONES.md`.**
