# 📦 Trongkai — Carpeta de Entregables

> **Para qué sirve esta carpeta**: tener todos los archivos importantes de Trongkai
> en un solo lugar, listos para mandar por mail, subir a Drive, o presentar.

---

## 📂 Estructura

```
entregables/
├── 01-presentaciones/      ← HTMLs Apple para mostrar al equipo y a líderes
├── 02-excel-master/        ← Excels generados (.xlsx + .xlsm con macros)
├── 03-pdf-tearsheet/       ← PDF ejecutivo descargado de la plataforma live
├── 04-logos/               ← Logos en distintos formatos
└── 05-mapa-proyecto/       ← INDEX.md con mapa completo del repo
```

---

## 🎁 ¿Qué mandar a quién?

### Al **Directorio / LP / Comité de Inversión**
- 📄 `03-pdf-tearsheet/Trongkai-Tearsheet-Ejecutivo.pdf` (3 páginas con logo)
- 🌐 `01-presentaciones/Presentacion-Lideres.html` (one-pager interactivo)
- 🔗 Link a la plataforma: **https://trongkai-web.vercel.app**

### Al **Equipo interno** (Sergio, Jaime, contadora, legal)
- 📋 `01-presentaciones/Solicitud-Datos-Equipo.html` (qué datos faltan, formato, cómo mandar)
- 📊 `02-excel-master/Trongkai-Master-*.xlsx` (10 hojas con datos vivos)

### A **bancos / asesores financieros**
- 📊 `02-excel-master/Trongkai-Master-VBA-*.xlsm` + `TrongkaiAPI.bas` (con macros)
- 📄 `02-excel-master/README-EXCEL-MACROS.txt` (cómo activar macros)
- 🔗 API endpoint: **https://trongkai-engine.fly.dev/docs**

### A **diseño / marketing / agencia externa**
- 🎨 `04-logos/` (3 versiones: color, blanco, icon)

---

## 🌐 URLs en vivo (siempre actualizadas)

| Recurso | URL |
|---|---|
| 🏠 Plataforma web | https://trongkai-web.vercel.app |
| 📊 Dashboard Directorio | https://trongkai-web.vercel.app/dashboard-directorio |
| 💯 Investment Readiness Score | https://trongkai-web.vercel.app/readiness |
| 📋 Datos faltantes (checklist) | https://trongkai-web.vercel.app/datos |
| 📑 Matriz Variables Ingredientes | https://trongkai-web.vercel.app/variables |
| ⚙️ Motor REST API | https://trongkai-engine.fly.dev |
| 📚 Swagger / OpenAPI | https://trongkai-engine.fly.dev/docs |
| 📄 PDF tearsheet (download) | https://trongkai-engine.fly.dev/api/tearsheet.pdf |

---

## 🔄 Cómo regenerar los archivos

Estos archivos se generan automáticamente con scripts. Si los datos del modelo cambian,
regenera con:

```powershell
# Desde la raíz del proyecto trongkai-platform/
cd "C:\Users\nicol\OneDrive\Documentos\0.1.1 TrongkAI\trongkai-platform"

# Excel Master con datos actualizados
python scripts/generar_excel_master.py
# → backups/Trongkai-Master-YYYYMMDD-HHMM.xlsx

# Excel con macros VBA
python scripts/generar_excel_macros_vba.py
# → backups/Trongkai-Master-VBA-YYYYMMDD-HHMM.xlsm + TrongkaiAPI.bas

# PDF tearsheet (siempre live)
curl -o entregables/03-pdf-tearsheet/Trongkai-Tearsheet-Ejecutivo.pdf https://trongkai-engine.fly.dev/api/tearsheet.pdf
```

Después copia los nuevos archivos de `backups/` a `entregables/02-excel-master/`.

---

## 📅 Frecuencia recomendada de actualización

| Archivo | Cuándo regenerar |
|---|---|
| PDF tearsheet | Cada visita (siempre live desde el motor) |
| Excel Master xlsx | Mensual o tras cambios de supuestos importantes |
| Excel VBA xlsm | Mismo que xlsx |
| Presentación HTML | Cuando se actualicen métricas clave del pitch |
| Solicitud Datos HTML | Cuando llegue información del equipo (actualizar checklist) |
| Logos | Solo si cambia la identidad visual |

---

## 📊 Estado del proyecto al generar esta carpeta

| Métrica | Valor |
|---|---|
| TIR proyecto | 30,73% |
| VAN @ WACC 18% | $5,5B CLP |
| EV exit año 5 | $131B CLP (9,63× EBITDA) |
| Investment Readiness Score | **84,7/100 (BANKABLE)** |
| Matriz Variables — cobertura | 42,4% (70 OK_PROVISORIO / 95 PD) |
| Carbono baseline 5y | -53.000 ton CO₂eq |
| Tests automáticos | 245/245 verde |
| Endpoints REST | 29 documentados |
| Páginas web | 19 |

---

## 🆘 Soporte

- **Documentación técnica**: `docs/` (16 archivos .md)
- **Mapa del proyecto**: `INDEX.md` (en la raíz)
- **Datos faltantes**: ver `/datos` en la plataforma o `Solicitud-Datos-Equipo.html`

---

**Última actualización**: 25 mayo 2026
**Generado por**: TrongkAI Platform
