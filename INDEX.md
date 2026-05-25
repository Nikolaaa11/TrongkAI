# Trongkai Platform — Mapa Maestro

> Guía de orientación para encontrar cualquier cosa en el proyecto, saber dónde
> dejar información nueva, y entender cómo alimentar el modelo.

---

## 📂 Estructura general

```
trongkai-platform/                                          ← ROOT del proyecto
│
├── apps/                            ← Aplicaciones (motor + frontend)
│   ├── engine/                      ← Motor Python (FastAPI)
│   │   ├── trongkai_engine/         ← Código del motor (24 módulos .py)
│   │   │   ├── plan_builder.py      ← Inputs / supuestos del modelo
│   │   │   ├── financial.py         ← Cálculos TIR, VAN, payback
│   │   │   ├── mass_balance.py      ← Balance de masa MMPP → producto
│   │   │   ├── monte_carlo.py       ← Simulaciones probabilísticas
│   │   │   ├── sensitivity.py       ← Heatmap 2D + curvas 1D
│   │   │   ├── breakeven.py         ← Análisis de colchón por driver
│   │   │   ├── readiness_score.py   ← Score 0-100 (8 dimensiones)
│   │   │   ├── carbon_footprint.py  ← LCA + créditos CO₂
│   │   │   ├── compliance_rep.py    ← Ley REP timeline
│   │   │   ├── macro_chile.py       ← Banco Central live
│   │   │   ├── financing.py         ← DSCR / LLCR / mix deuda-equity
│   │   │   ├── slb.py               ← Sustainability-Linked Bonds
│   │   │   ├── tearsheet_pdf.py     ← Generador PDF ejecutivo
│   │   │   ├── main.py              ← FastAPI app + 28 endpoints
│   │   │   └── assets/              ← Logos para PDF
│   │   ├── tests/                   ← 245 tests pytest (100% pass)
│   │   ├── Dockerfile               ← Imagen para Fly.io
│   │   ├── fly.toml                 ← Config Fly.io
│   │   └── pyproject.toml           ← Dependencias Python
│   │
│   └── web/                         ← Frontend Next.js 14
│       ├── app/                     ← 17 páginas (rutas)
│       │   ├── page.tsx             ← / (home Apple-style)
│       │   ├── dashboard-directorio/← Vista ejecutiva
│       │   ├── readiness/           ← Investment Readiness Score
│       │   ├── sensitivity/         ← Heatmap + breakeven + curves
│       │   ├── plan/                ← Plan 5 años + tornado
│       │   ├── carbono/             ← LCA visual
│       │   ├── compliance/          ← Ley REP timeline
│       │   ├── financiamiento/      ← Mix deuda-equity
│       │   ├── macro/               ← Banco Central live
│       │   ├── api/                 ← API Explorer interactivo
│       │   └── ...                  ← (12 más)
│       ├── components/              ← Componentes echarts puros
│       │   ├── HeatmapChart.tsx
│       │   ├── CurvaSensibilidad.tsx
│       │   ├── SankeyChart.tsx
│       │   ├── TornadoChart.tsx
│       │   └── HistogramaChart.tsx
│       ├── lib/                     ← SDK TypeScript + seed data
│       ├── public/                  ← Logos + favicon
│       │   ├── icon-trongkai.png
│       │   ├── logo-trongkai-color.png
│       │   └── logo-trongkai-white.png
│       ├── tailwind.config.ts       ← Paleta Apple
│       └── package.json
│
├── docs/                            ← 🟢 DOCUMENTACIÓN — leer acá primero
│   ├── DATOS-MERCADO.md             ← Calibración papers + benchmarks
│   ├── PAPERS-CIENTIFICOS.md        ← 27 papers peer-reviewed
│   ├── DECISIONES.md                ← ADRs (decisiones arquitectónicas)
│   ├── BALANCE-MASA.md              ← Cierre ±0.5% del balance
│   ├── SUPUESTOS.md                 ← Registro PD/OK_PROVISORIO/OK_VALIDADO
│   ├── RIESGO-SUPUESTOS.md          ← Top 10 supuestos críticos
│   ├── PREGUNTAS-ABIERTAS.md        ← 🔴 Lo que falta resolver
│   ├── PROXIMOS-PASOS.md            ← Roadmap
│   ├── KNOWN-ISSUES.md              ← Bugs conocidos
│   ├── RUNBOOK.md                   ← Operación día a día
│   ├── INVENTARIO-EXCELS.md         ← Archivos contexto/
│   ├── GLOSARIO.md                  ← Diccionario términos
│   ├── ESTADO-ACTUAL.md             ← Snapshot del proyecto
│   ├── INTELIGENCIA-COMPETITIVA.md  ← Comparables M&A LATAM
│   ├── AGENTES-Y-SCHEDULES.md       ← 13 agentes Claude + 9 schedules
│   └── dumps/                       ← TSV extraídos de Excels originales
│
├── contexto/                        ← 🔵 INPUTS DEL EQUIPO — soltar acá info nueva
│   ├── Cuadro_PPTO_Variables_PD_Plan_5_Anos_A.xlsx
│   ├── Info_Plan_5_anos_Estructura_A.xlsx
│   ├── Presentacion_Trongkai_2025-10-22.pptx
│   ├── Presentacion_Trongkai_2026-10.pdf
│   └── Jaime.txt
│
├── backups/                         ← 🟡 OUTPUTS GENERADOS
│   ├── Trongkai-Master-*.xlsx       ← Excel 10 hojas con datos del motor
│   ├── Trongkai-Master-VBA-*.xlsm   ← Excel con macros buttons
│   ├── TrongkaiAPI.bas              ← Módulo VBA para importar
│   ├── README-EXCEL-MACROS.txt      ← Instrucciones de uso
│   ├── Presentacion-Lideres.html    ← Pitch one-pager Apple
│   └── Solicitud-Datos-Equipo.html  ← Brief para que el equipo mande info
│
├── scripts/                         ← Scripts utilitarios Python + PowerShell
│   ├── generar_excel_master.py      ← Genera el .xlsx con datos vivos
│   ├── generar_excel_macros_vba.py  ← Genera .xlsm + módulo VBA
│   ├── inventory_excels.py          ← Indexa Excels nuevos
│   ├── extract_presentation.py      ← Extrae texto de PPT/PDF
│   ├── audit_hardcodes.py           ← Detecta supuestos hardcoded
│   ├── backup_db.ps1                ← Backup automático
│   └── schedule_*.ps1               ← 5 schedules autónomos Windows
│
├── infra/                           ← Infraestructura como código
├── tests/                           ← Tests end-to-end de la web
├── packages/                        ← Paquetes compartidos (futuro)
├── logs/                            ← Logs de schedules
│
├── README.md                        ← Lee primero si llegas nuevo
├── CHANGELOG.md                     ← Historial de cambios
├── INDEX.md                         ← Este archivo
├── package.json                     ← Workspace pnpm
├── docker-compose.yml               ← Stack local
└── vercel.json                      ← Config deploy Vercel
```

---

## 🌐 Producción (URLs en vivo)

| Recurso | URL |
|---|---|
| 🏠 Plataforma web | https://trongkai-web.vercel.app |
| ⚙️ Motor REST API | https://trongkai-engine.fly.dev |
| 📚 Swagger/OpenAPI | https://trongkai-engine.fly.dev/docs |
| 📄 PDF tearsheet | https://trongkai-engine.fly.dev/api/tearsheet.pdf |
| 📊 Repo GitHub | https://github.com/Nikolaaa11/TrongkAI |

---

## 🟢 Dónde dejar información nueva (por categoría)

### 1. Documentos del proyecto (legales, comerciales, financieros)
→ `contexto/`
- PDFs de presentaciones
- Excels que llegan de Jaime / Sergio / consultores
- Contratos firmados
- Cartas de intención

### 2. Información de mercado (benchmarks, precios, rendimientos)
→ Anotar en `docs/DATOS-MERCADO.md`
→ Si es un paper nuevo, agregarlo a `docs/PAPERS-CIENTIFICOS.md`
→ Modificar el valor real en `apps/engine/trongkai_engine/plan_builder.py`

### 3. Supuestos que pasan de PD a OK
→ Anotar transición en `docs/SUPUESTOS.md`
→ Actualizar `docs/RIESGO-SUPUESTOS.md`

### 4. Decisiones de directorio / comité
→ ADR nuevo en `docs/DECISIONES.md`

### 5. Bugs encontrados
→ Anotar en `docs/KNOWN-ISSUES.md`

### 6. Preguntas que aún no tienen respuesta
→ Agregar a `docs/PREGUNTAS-ABIERTAS.md`

---

## 🔵 Cómo regenerar outputs

```powershell
# Excel Master con datos vivos (10 hojas)
python scripts/generar_excel_master.py
# → backups/Trongkai-Master-YYYYMMDD-HHMM.xlsx

# Excel con macros VBA
python scripts/generar_excel_macros_vba.py
# → backups/Trongkai-Master-VBA-YYYYMMDD-HHMM.xlsm + TrongkaiAPI.bas

# PDF tearsheet ejecutivo
curl -o tearsheet.pdf https://trongkai-engine.fly.dev/api/tearsheet.pdf
# o desde la plataforma: botón "Descargar PDF tearsheet" en /dashboard-directorio

# Inventario de Excels en contexto/
python scripts/inventory_excels.py
```

---

## 📊 Estado actual del modelo (snapshot)

| Métrica | Valor |
|---|---|
| **TIR proyecto** | 30,73% |
| **VAN @ WACC 18%** | $5,5B CLP |
| **Payback** | 52 meses |
| **EV exit año 5** | $131B CLP (9,63× EBITDA) |
| **Investment Readiness Score** | 84,7/100 (BANKABLE) |
| **Zona segura sensibilidad (precio×costo)** | 76% |
| **Break-even precio** | -13,9% antes de bajar del hurdle |
| **Carbono baseline 5y** | -53.000 ton CO₂eq (negativo) |
| **Hitos REP vigentes** | 2/8 |
| **Tests engine** | 245/245 verde |
| **Endpoints REST** | 28 documentados |
| **Páginas web** | 17 |

---

## 🤖 Agentes y schedules autónomos (operando 24/7)

| Schedule | Frecuencia | Qué hace |
|---|---|---|
| `improver` | cada 1h | Mejora código, corre tests, commit |
| `macro_refresh` | cada 4h | Refresca USD/UF/IPC desde Banco Central |
| `data_hunter` | semanal | Busca papers + benchmarks nuevos |
| `compliance_monitor` | diaria | Audita cumplimiento Ley REP |
| `carbon_audit` | mensual | Recalcula LCA y créditos CO₂ |
| `monitor_health` | cada 30 min | Health-check engine + web |

Ver `docs/AGENTES-Y-SCHEDULES.md` para detalle completo.

---

## 🚦 Próximos pasos sugeridos

1. **Validar el Investment Readiness Score con un LP real** para confirmar que el threshold 80=BANKABLE es relevante para el mercado chileno
2. **Subir presentaciones nuevas** a `contexto/` cuando lleguen del equipo
3. **Revisar `docs/PREGUNTAS-ABIERTAS.md`** y empezar a resolver las que están abiertas
4. **Conectar Nubox** en producción para alimentar el modelo con cifras reales
5. **Custom domain** (`platform.trongkai.cl` por ejemplo)
6. **Auth multi-usuario** para diferentes niveles de acceso (directorio / equipo / LP)

---

**Última actualización**: 25 mayo 2026
**Generado por**: TrongkAI Platform
