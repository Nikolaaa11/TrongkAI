# Top 10 — Variables cuyo error > 10% tumba la TIR del Plan 5 años

> Mapa de sensibilidad solicitado por SUPER_PROMPT §9.4. Estimación preliminar basada en el modelo financiero clásico de planta de procesos. Se refinará con el `Sensibility Tornado Chart` del Módulo 3 una vez cargados precios reales.

| # | Variable | Supuesto actual | Por qué pega tan fuerte | Sensibilidad estimada de TIR a un ±10% de error | Owner |
|---|---|---|---|---|---|
| 1 | **Precio de venta del aceite de alperujo** | PD (Jaime mencionó $1.200/kg como dato suelto) | Es el producto base con mayor margen unitario y volumen alcanzable en año 1. Driver principal del ingreso temprano. | ±4-6 pp TIR | Jaime + Comercial |
| 2 | **Precio de venta del licopeno** | PD | Producto AGREGADO de año 2-3, precio internacional volátil (USD 80-200/kg según pureza). Justifica el CapEx del tren de extracción. | ±3-5 pp TIR | Jaime + Comercial |
| 3 | **Rendimiento aceite de alperujo con PEF** (`alperujo.aceite_extraible_pct`) | 2% (objetivo Jaime) | Competencia logra 1.3-1.45%. Si llegamos solo a 1.5%, perdemos 25% del producto premium. **Justifica todo el PEF**. | ±5-7 pp TIR | José + planta piloto |
| 4 | **Capacidad nominal del secador** (`cap.secado_ton_h`) | PD | Bottleneck del sistema. Define throughput máximo = ton procesadas/año = ingreso total. Si está 10% bajo el target, no se llega a 50.000 ton. | ±4-6 pp TIR | Matías + ingeniería |
| 5 | **WACC** (`wacc_pct`) | PD | Es la tasa de descuento. ±10% de error en WACC mueve directamente VAN y TIR objetivo. Específicamente bajo: define payback. | ±3-4 pp en VAN; tumba decisión de inversión si WACC real > TIR estimada | Directorio + AFIS |
| 6 | **Costo de energía del secador** (`secador.kwh_por_ton` × `tarifa_energia`) | PD (ambos) | El secador es el equipo más caro de operar. Una tarifa eléctrica 10% sobre target levanta el OpEx unitario por kg producto final significativamente. | ±2-4 pp TIR | Matías |
| 7 | **Tiempo de descomposición real de tomasa** (`tomasa.tiempo_descomposicion_h`) | 3 h (PD) | Si en realidad es 1.5h, hay que rechazar camiones → 30-50% del volumen tomasa no procesable → pérdida de ingreso de la familia tomasa+licopeno+pectina entera. | ±2-3 pp TIR (asimétrica: solo riesgo a la baja) | José |
| 8 | **Volumen comprometido de Olivero 3 (gratis, al lado)** | 2.000 ton | Es el proveedor más grande con costo logístico cero. Si se cae, hay que reemplazarlo con oliveros lejanos pagando $1.800-2.500/km. | ±2-3 pp TIR | Matías |
| 9 | **CapEx total año 1 (planta piloto + industrial)** | PD | Driver del payback. Si CapEx real es 30% sobre estimado, payback se extiende del año 4 al 6+. Combinado con régimen de depreciación. | ±3-5 pp TIR | Jaime + ingeniería |
| 10 | **Precios de los 4 PTEC (proteína unicelular, antioxidante, aglomerante, umami)** | PD (Jaime: "del umami no tengo idea") | Estos productos entran año 3-5 y son el upside del plan. Si los precios son la mitad de lo modelado, el plan se vuelve aceitero puro. | ±3-6 pp TIR (asimétrica: upside) | Jaime + I+D + Comercial |

## Top 5 variables con efecto cruzado (no independientes)

- **Modo balance A vs B** (ADR-003): cambia el peso entregado en +11% relativo. Si la decisión va por B, el precio efectivo por kg cobrado baja vs A. Tiene que evaluarse contractualmente: ¿se vende ton de producto seco al 10% humedad o ton de MS pura?
- **Mix de proveedores caso 1 vs caso 4**: la diferencia entre pagar al proveedor o que el proveedor pague mueve el costo unitario MMPP en el orden de $30-50/kg producto final.
- **Decisión PEF sí/no** acopla rendimiento aceite (#3) con costo mantención (300h × $1MM × 2 cuarres = $2MM cada 12 días operativos).
- **Régimen 24/7 en temporada vs 5×8**: cambia dotación, salarios nocturnos y mantenciones. Driver MO total.
- **Decisión maquilas yes/no**: ingreso accesorio que ocupa capacidad en valles. Si la planta nunca tiene valle, sale del modelo.

## Cómo se va a refinar este mapa

1. Módulo 3 entrega un **tornado chart** con las 8 variables clave (sección 4 SUPER_PROMPT) parametrizadas. Las cifras de "±X pp TIR" arriba son estimadas a ojo; el tornado las medirá.
2. Cada vez que un `Supuesto` pase de PD a `OK_VALIDADO_*`, este mapa se recalcula y el riesgo asociado se ajusta o sale del top 10.
3. El agente `trongkai-supuestos` corre cada hora y agrega al `CHANGELOG.md` los movimientos del top 10.
