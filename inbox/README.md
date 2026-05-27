# 📥 Inbox — Buzón inteligente de información

> **Aquí subes los archivos que descargas de Google Drive**, mails, WhatsApp, o cualquier fuente.
> El sistema los clasifica, indexa, conecta a la matriz de variables y actualiza el Investment Readiness Score automáticamente.

---

## 🚀 Flujo de uso

```
1. Tú recibes un archivo (cotización MMPP firmada, LOI cliente, OpEx real, etc)
            ↓
2. Lo dejas en la subcarpeta correcta de inbox/ (ver taxonomía abajo)
            ↓
3. Ejecutas:  python scripts/procesar_inbox.py
            ↓
4. El sistema:
   - Indexa el archivo (filename, size, hash, fecha)
   - Lo clasifica por keywords del path y contenido
   - Sugiere qué celdas de matriz actualizar
   - Registra evento en audit trail
   - Mueve archivo a inbox/_procesados/
   - Actualiza el Investment Readiness Score
            ↓
5. En /audit ves el nuevo evento
   En /readiness ves el delta del score
   En /variables ves las celdas actualizadas (si se confirman)
```

---

## 📂 Taxonomía de carpetas (7 categorías)

### 01-comercial/
Información comercial pura: clientes y proveedores.

| Subcarpeta | Qué subir | Impacto en matriz |
|---|---|---|
| `cotizaciones-mmpp/` | Cotizaciones firmes de olivar/tomatera/vinícolas | → `Precio Recepción Subproducto` (11 celdas PD) |
| `lois-clientes/` | LOI firmadas con compradores Feed/Food | → `Precio de Venta` (PTEC en PD) |
| `contratos-firmados/` | MSA, contratos comerciales formalizados | → Data Room item `contratos-clientes` |
| `pipeline-leads/` | CRM exports, listas de prospects | → Pipeline LP `/pipeline-lp` |

### 02-financiero/
Datos financieros, bancarios y contables.

| Subcarpeta | Qué subir | Impacto en matriz |
|---|---|---|
| `term-sheets-bancarios/` | Term sheets de BICE, Santander, etc | → DSCR / LLCR / financiamiento |
| `opex-real-mensual/` | Excel mensual contadora desglosado | → `Costo Administración/Energía/Servicios/Mantención` (44 celdas PD) |
| `capex-cotizaciones/` | Cotizaciones firmes equipos planta | → CapEx anual cronograma |
| `eerr-historicos/` | EERR auditados últimos 3 años | → Data Room `eerr-historico` |

### 03-operacional/
Mediciones técnicas y operacionales reales.

| Subcarpeta | Qué subir | Impacto en matriz |
|---|---|---|
| `rendimientos-medidos/` | Pruebas piloto ALPERUJO/TOMASA/POMASA | → `Rendimiento` (5 MMPP) |
| `consumo-energetico/` | kWh/ton por equipo | → LCA + costo energía |
| `capacidad-equipos/` | Specs secador / prensa / extracción | → Bottleneck módulo |
| `cronograma-obra/` | Gantt Project / fechas equipos | → CapEx mensual |

### 04-legal/
Documentos legales y permisos.

| Subcarpeta | Qué subir | Impacto en matriz |
|---|---|---|
| `escrituras-societarias/` | Escritura constitución, estatutos | → Data Room items legales |
| `permisos-rca-sag/` | RCA, RUP, permisos SAG/Seremi | → Data Room operacional |
| `certificaciones/` | HACCP, GMP+, B-Corp, ISO | → Data Room ESG |
| `patentes-marcas/` | Registro INAPI marca + procesos | → IP protection |

### 05-esg/
Sustentabilidad, carbono, compliance.

| Subcarpeta | Qué subir | Impacto en matriz |
|---|---|---|
| `reportes-lca/` | LCA medido por consultor | → `/carbono` validar baseline |
| `compliance-rep/` | Plan REP firmado MMA | → `/compliance` 8 hitos |
| `certificaciones-esg/` | Certificados B-Corp / SFDR | → Decision Engine acción ESG |

### 06-equipo/
Personas, advisors, alianzas.

| Subcarpeta | Qué subir | Impacto en matriz |
|---|---|---|
| `cvs-fundadores/` | CVs Nicolás/Jaime/Sergio + directorio | → `/equipo` actualizar |
| `advisors-directorio/` | Bios advisors + carta nombramiento | → `/equipo` |
| `alianzas-mous/` | MOUs CORFO/Universidades/partners | → Data Room |

### 07-mercado/
Inteligencia de mercado y research.

| Subcarpeta | Qué subir | Impacto en matriz |
|---|---|---|
| `papers-cientificos/` | Papers peer-reviewed sobre rendimientos | → `docs/PAPERS-CIENTIFICOS.md` |
| `comparables-ma/` | Transacciones M&A LATAM circular economy | → Valuation múltiplo |
| `benchmarks-precios/` | Reportes mercado precios SKU | → `Precio de Venta` calibración |

### 99-sin-clasificar/
Si no sabes dónde va, déjalo aquí. El clasificador lo va a etiquetar automáticamente.

### _procesados/
**No subir aquí.** El sistema mueve archivos después de procesarlos.

---

## 📝 Convención de nombres recomendada

Formato: `YYYY-MM-DD_<contraparte>_<descripcion-corta>.<ext>`

Ejemplos:
- `2026-06-05_Oliveros-XX_cotizacion-firme-alperujo.pdf`
- `2026-06-08_CliRente-Acuicola_LOI-harina-orujo-200ton.pdf`
- `2026-05-31_Contadora_opex-mayo-2026.xlsx`
- `2026-06-10_BICE_term-sheet-15M-USD-10y.pdf`

El clasificador usa estos nombres para inferir contexto automáticamente.

---

## 🔄 Procesamiento

```powershell
# Desde la raíz del proyecto:
cd "C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform"

# Procesar todo lo nuevo del inbox
python scripts/procesar_inbox.py

# Ver estado del inbox
python scripts/procesar_inbox.py --status

# Reprocesar todo (incluso lo ya en _procesados/)
python scripts/procesar_inbox.py --reprocess-all
```

O desde la plataforma web: **https://trongkai-web.vercel.app/inbox**

---

## 🤖 Cómo se vuelve más inteligente la plataforma

Cada archivo procesado:
1. Se registra en `inbox/_index.json` con hash MD5 (para detectar duplicados)
2. Se loggea en **audit trail** (`/audit`) con tipo `datos_equipo_recibidos`
3. El clasificador propone qué **celdas de matriz** actualizar (sugerencia)
4. Tú aprueba/rechaza la sugerencia en `/inbox` (UI web)
5. Al aprobar: celdas pasan de **PD → OK_VALIDADO**
6. El **readiness score sube** automáticamente
7. El **Decision Engine recalcula** sus top 5 acciones
8. Las **alertas relacionadas** se resuelven
9. El **LP Pack ZIP** próximo descargado incluye los datos nuevos

**Loop virtuoso**: más archivos en inbox → modelo más calibrado → score más alto → roadshow más sólido.

---

## 📊 Estado actual del inbox

Después de cada `procesar_inbox.py`, este README se actualiza con stats:
- archivos totales / procesados / pendientes
- por categoría
- último procesamiento

---

**Última actualización**: 30 mayo 2026
**Mantenedor**: Trongkai Platform
