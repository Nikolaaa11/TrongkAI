# Inventario de Excels del cliente

> Generado automáticamente por `scripts/inventory_excels.py` a partir de los 3 archivos en `/contexto/`. Cada hoja se vuelca como TSV en `docs/dumps/<archivo>/<hoja>.tsv` para revisión.

## 1. `Info_Plan_5_anos_Estructura_A.xlsx`

Define la **estructura base** de proveedores y rendimiento. Es el archivo que aterriza el modelo logístico de Jaime y la doble base de cálculo (A inicial / B deshidratada).

| Hoja | Dim | Rol |
|---|---|---|
| **IngresosCostos Proveedores** | 16×12 | Matriz Olivero 1..10 con distancia, valor flete ($1.800 / $2.100 / $2.500 por km), pago x recepción ($/kg), volumen comprometido (ton), capacidad camión (ton). Codifica los 4 casos logísticos. Ejemplo: Olivero 1 = 82 km, flete $1.800/km → costo flete unitario 5,904 $/kg, paga residuo $-10/kg, 500 ton, camión 20 ton (Caso 1). |
| **Base rendimiento** | 14×12 | Ejemplo alperujo con humedad 65%, materia sólida 35%, aceite extraíble 2%. Compara modo A (s/base inicial) que da MS final = 0,35 contra modo B (s/base deshidratada) que da 0,405. **Marca un "???" sobre cuál es correcta — punto de discusión con José/Claudio**. |
| Hoja1 | 1×1 | Vacía. |

## 2. `Cuadro_PPTO_Variables_PD_Plan_5_Anos_A.xlsx`

El **panel de control de supuestos pendientes**. Cada celda dice OK, OK*, PD o PD/2 por SKU × variable. **123 celdas PD vs 17 OK** — el plan está hoy mayoritariamente sin definir.

| Hoja | Dim | Rol |
|---|---|---|
| **Datos x Plan 5 años** | 26×15 | Matriz de 23 variables × 12 SKUs (5 base, 2 valor agregado, 4 PTEC, + columna H. Pomasa y H. Tomasa). Variables: Volumen Subproductos, Costo Transporte, Precio Recepción, Rendimiento, Volumen Producto Final, Precio Venta (totalmente vacío), Costo producción*, Material envase, Almacenamiento, Transporte Almac./Clientes, Laboratorio, Administración, Energía, Servicios Generales, Mantención Industrial, Estructuración Modelo, Opex/Capex, Ingresos Maquilas, Ingresos Transferencia Tecnológica. **Total contractual fijado: 50.000 ton anuales**. |
| **Propuesta Timing** | 6×8 | Roadmap del cliente: A) supuestos 1 al **2026-05-29**, B) supuestos 2 al **2026-06-30**, C) estructura final al **2026-07-15**, D) operacional afinado al **2026-07-31**. |

## 3. `Tareas_Plan_5_anos.xlsx`

Briefing original que Jaime dio al "analista de presupuesto y costos" (hoy lo absorbe la plataforma).

| Hoja | Dim | Rol |
|---|---|---|
| **Visión Planillas** | 25×11 | 14 tareas listadas: planillas de volúmenes/precios de productos base y PTEC, MMPP logística, transferencia tecnológica, maquilas, rendimiento materia seca, costos por etapa de proceso (homog./PEF/extracción/secado), MO, mantención, calidad/certificaciones, energía, envase/almacén, limpieza, gastos fijos admin, CapEx/OpEx año 1-5, EERR 5 años + índices de rentabilidad. Es el **mapa de módulos a construir**. |

## Equivalencias inmediatas con el modelo Prisma (sección 3 del SUPER_PROMPT)

- `IngresosCostos Proveedores` → `Supplier` + `MateriaPrima`
- `Base rendimiento` → `Producto` + parámetros del motor de balance de masa (Módulo 2)
- `Datos x Plan 5 años` → `Supuesto` (estado PD/OK) + `PlanAnual`/`MixProduccionMensual`/`OpEx`/`CapEx`/`FlujoCaja`
- `Visión Planillas` → backlog de épicas funcionales

## Estado inicial del campo `Supuesto.estado`

Mapeo directo desde la hoja Datos x Plan 5 años:

| Texto en Excel | Estado en DB |
|---|---|
| `OK` | `OK_VALIDADO` |
| `OK*` | `OK_PROVISORIO` |
| `PD` | `PD` |
| `PD/2` | `PD` (con tag `parcial_proteinaunicel`) |
| en blanco | `NO_APLICA` |
