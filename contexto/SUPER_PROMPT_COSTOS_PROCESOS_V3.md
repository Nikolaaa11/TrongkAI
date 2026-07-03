# SUPER PROMPT — COSTOS POR PROCESOS V3 (canon 03-jul-2026)

> **Fuente canónica:** `costos por procesos (3).xlsx` (equipo Agrosphere, recibido 03-jul-2026).
> Este documento ES la verdad para costos variables de procesamiento del piloto.
> Reemplaza toda estimación anterior de tarifas, sueldos operativos y consumos por equipo.
> Cualquier agente (improver, financial, supuestos, data-hunter) que toque costos DEBE leer esto primero.

---

## 0. LA REGLA DE ORO — dos métricas que NO se mezclan

| Métrica | Valor | Qué incluye | Dónde vive |
|---|---|---|---|
| **Costo variable de procesamiento** | **194.722 CLP/ton MP seca (saco)** · **77.938 CLP/ton (maxisaco)** | RRHH por hora, energía, agua limpieza, insumos, repuestos PEF, packaging | `balances/costos_procesos.py` (nuevo) — réplica del Excel |
| **OPEX completo piloto** | ~15.771 CLP/kg SKU (pre-V3; sube con tarifa 270) | Todo lo anterior + arriendos PEF/Tricanter (12 meses calendario), leyes sociales ×1.35, fletes MMPP, overhead | `balances/simulador_temporal.py` `_opex_completo()` |

El Excel del equipo mide **costo de proceso por tonelada de materia seca**. NO es el costo
del kg de SKU final ni incluye costos fijos. Nunca comparar 194 CLP/kg contra 15.771 CLP/kg:
son universos distintos y ambos correctos.

---

## 1. PARÁMETROS CANÓNICOS (Hoja1 del Excel)

### 1.1 RRHH (sueldo bruto mensual / 160 h/mes)

| Cargo | Sueldo mes CLP | CLP/hora (Excel, sin leyes sociales) |
|---|---|---|
| Laboratorista | 1.500.000 | 9.375 |
| Recepcionista | 1.000.000 | 6.250 |
| Operario planta | 1.000.000 | 6.250 |
| Supervisor de planta | 1.500.000 | 9.375 |

- El Excel usa **160 h/mes** y NO aplica leyes sociales. La plataforma mantiene factor ×1,35
  para OPEX completo; el módulo `costos_procesos` replica el Excel puro (sin factor) para trazabilidad.
- Dotación mensual estimada (Hoja2 F39-43): Laboratorista 3 (0,75 FTE efectivo), Recepcionista 4,
  Supervisor 1,5, Operario 4. **Ambiguo — por validar con el equipo.**

### 1.2 Operación

| Parámetro | Valor | Nota |
|---|---|---|
| Volumen por camión | 22 ton | |
| Camiones/día | 3 | 66 ton/día MMPP |
| Turnos | 2 × 8 h = **16 h/día** | |
| Recepción mensual | **2.000 ton/mes** | |
| Humedad ingreso MMPP | **60%** | → 26,4 ton MP seca/día |
| Agua incorporada en estandarización | 0,25 m³/ton | 66 → **82,5 ton/día a procesar** |
| Pérdida por etapa | **0,5%** (uniforme, todas las etapas) | |
| 1 ton | 1.000 kg | |

### 1.3 Tarifas y cambio

| Parámetro | Valor V3 | Valor anterior plataforma | Δ |
|---|---|---|---|
| **Energía eléctrica** | **270 CLP/kWh** | 109 promedio (165 punta/95 resto) | **+148%** |
| **Agua** | **800 CLP/m³** | 1.450 | −45% |
| **Alcantarillado/tratamiento** | **950 CLP/m³** ⚠️ por validar si aplica | 1.200 | −21% |
| Agua limpieza por etapa | 1.750 CLP/día (= 1 m³ a tarifa llena) | — | nuevo |
| Calor residual | 100 CLP/m³ | 5 CLP/kWh térmico | redefinido |
| EUR/CLP | 1.050 | — | nuevo |
| USD/CLP | 900 | 920 | −2% |
| Costo por muestra lab | 1.500 CLP | — | nuevo |

### 1.4 Consumo eléctrico por equipo (kW promedio en operación, 16 h/día)

| Equipo | kW | CLP/día (kW×16h×270) |
|---|---|---|
| Homogenizador (100-150 bar, 75-90 kW nominal) | 5 | 21.600 |
| Bomba recepción (50-100 m³/h) | 4 | 17.280 |
| Bomba tornillo | 4,2 | 18.144 |
| **PEF** | **14** | 60.480 |
| Prensa | 20 | 86.400 |
| Tricanter | 17,6 | 76.032 |
| Secador 3 ton/batch (batch 9 h) | 75 | — |
| Bomba de calor (secado 5.1) | 80 | 345.600 |
| Calor secado vía residual (5.2) | 10 | 43.200 |
| Enfriamiento (paletas/ventiladores) | 10 | 43.200 |
| Molino | 61,6 | 266.112 |
| Elevador | 3,08 | 13.305,6 |
| Ensacado | 1,4 | 6.048 |
| Yale (grúa horquilla) | 5 | 21.600 |

### 1.5 Repuestos PEF (amortizados por tonelada procesada)

| Repuesto | Precio | Duración | Ton por juego | CLP/ton |
|---|---|---|---|---|
| Electrodos | 802,33 EUR | 300 h ⚠️ (sistema dice 200 h — por validar) | 1.200 | **702,04** |
| Cámara geometría específica | 2.855,99 EUR | 600 h | 2.400 | **1.249,50** |

A 82,5 ton/día: electrodos 57.918 CLP/día + cámara 103.083 CLP/día.

### 1.6 Packaging (el driver decisivo)

| Ítem | Valor |
|---|---|
| Saco 25 kg | 3.000 CLP/u |
| Maxisaco 800 kg | 10.000 CLP/u |
| Pallet (40 sacos) | 28.000 CLP costo + 1.000 CLP/mes arriendo |
| Desinfectantes por etapa | 802,33 CLP/día ⚠️ (idéntico al EUR de electrodos — posible error de copia, por validar) |

---

## 2. LAS 12 ETAPAS Y LA CADENA DE MASA (Hoja2)

Flujo diario: 66 ton MMPP (60% humedad) + 16,5 m³ agua = **82,5 ton** → pérdida 0,5% por etapa →
**28,3 ton producto (8% humedad)** = **25,36 ton MP seca**.

| Etapa | Proceso | Ton in → out | Humedad in → out | Costo/día CLP | CLP/ton MP seca |
|---|---|---|---|---|---|
| 1 | Recepción MP | 66 | 60% | 60.177 | 2.279 |
| 2 | Estandarización (+agua 0,25 m³/ton) | 66 → 82,5 | 60% → 68% | 96.005 | 3.655 |
| 3 | PEF | 82,5 | 68% | 277.159 | 10.604 |
| 4.1 | Prensado tradicional | 82,5 → 43,6 | 68% → 40% | 149.982 | 5.767 |
| 4.2 | Tricanter (alternativa) | 82,5 → 37,3 | 68% → 30% | 139.614 | 5.369 |
| 5.1 | Deshidratación bomba de calor | 37,2 → 28,9 | 30% → 10% | 391.902 | 15.145 |
| 5.2 | Deshidratación calor residual (alternativa) | 37,2 → 28,9 | 30% → 10% | 89.502 | 3.459 |
| 6 | Enfriador eléctrico | 28,8 → 28,1 | 10% → 8% | 89.502 | 3.476 |
| 7 | Molienda | 28,0 | 8% | 312.414 | 12.195 |
| 8.1 | Homogenizador → **Saco 25 kg** (1.114 sacos/día) | 27,8 | 8% | **3.408.613** | **133.725** |
| 8.2 | Homogenizador → **Maxisaco 800 kg** (35 u/día) | 27,7 | 8% → 10% | **446.697** | **17.613** |
| 9 | Etiquetado y almacenamiento | 28,3 → 25,36 seca | | 152.858 | 6.027 |

### 2.1 Rutas y totales canónicos (verificados contra el Excel al centavo)

**Ruta base del Excel** = E1+E2+E3+**E4.1**+**E5.1**+E6+E7+E8.x+E9:

| Ruta | Total CLP/día | CLP/ton MP seca | CLP/kg MP seca |
|---|---|---|---|
| **SACO** | **4.938.613,20** | **194.722,64** | 194,72 |
| **MAXISACO** | **1.976.697,40** | **77.938,42** | 77,94 |

- El packaging en saco 25 kg cuesta **3,34M CLP/día solo en sacos** (69% del costo total de la ruta).
  El maxisaco reduce el costo total del proceso **2,5×**. Decisión comercial de primer orden.
- Fila alternativa del Excel (F32): 174.374 / 69.794 CLP/ton = ruta con E5.2 (calor residual)
  en vez de E5.1. El calor residual de La Gloria ahorra ~20.350 CLP/ton MP seca adicionales.

### 2.2 ⚠️ Inconsistencias detectadas en el Excel del equipo (corregidas en el entregable V3)

1. **Ruta cruzada:** el costo total usa E4.1 (prensa) pero la cadena de masa sigue E4.2
   (tricanter: 5.x recibe 37,15 ton = salida tricanter ×0,995). El entregable V3 separa las
   4 rutas coherentes: {prensa|tricanter} × {bomba calor|calor residual} × {saco|maxisaco}.
2. **Desinfectantes 802,33 CLP** = exactamente el precio EUR de los electrodos → copia probable.
3. **E5.2 y E6 con total idéntico** (89.502,33) pese a componentes distintos.
4. **Electrodos 300 h vs 200 h** según sistema de la máquina → el CLP/ton podría ser +50%.
5. Los sueldos del Excel no aplican leyes sociales (×1,35) → subestima RRHH ~35% para EERR formal.

---

## 3. QUÉ SE ACTUALIZA EN LA PLATAFORMA

| # | Módulo | Cambio | Impacto |
|---|---|---|---|
| 1 | `balances/costos_procesos.py` **(nuevo)** | Réplica canónica del Excel: 12 etapas, 4 rutas, saco vs maxisaco | endpoint `GET /costos/procesos` |
| 2 | `balances/parametros_planta.py` | Energía 270 flat · agua 800+950 · sueldos V3 (Lab/Sup 1,5M; Recep/Op 1M) · EUR 1050 · USD 900 · fecha | ripple a simulador/costeo/OPEX |
| 3 | `balances/etapas.py` | Pérdida uniforme 0,5% (E3 0→0,005; E7 0,010→0,005; E8 0,003→0,005) | balance masa |
| 4 | Datos vivos Fly | POST `/parametros/actualizar` post-deploy (JSON persistido pisa seeds) | producción |
| 5 | UI `/costeo` | Bloque comparativo Saco vs Maxisaco desde el endpoint nuevo | visible al equipo |
| 6 | Tests | Recalibrar asserts de tarifas/costos afectados | 623+ verdes |

**Consecuencia esperada:** el OPEX completo del piloto SUBE (energía +148%, sueldos operativos
casi ×2) — el costo/kg SKU live va a superar los 15.771 CLP/kg previos. Es correcto: la verdad
manda sobre la estética. `margen-por-sku` y la narrativa "deficitario por diseño" se refuerzan.

## 4. REGLAS DE COHERENCIA (post-actualización)

1. `simulador_temporal` = `simulacion_revenue` = `prediccion_intervalos` = `costeo_etapas`
   usan TODOS `cargar_parametros()` — una sola fuente de tarifas.
2. `costos_procesos.py` NO usa `cargar_parametros()`: replica el Excel con sus propios valores
   canónicos congelados + función de re-cálculo con overrides (para what-if).
3. Nada de números mágicos en UI: todo desde endpoints.
4. Niveles de dato: tarifa energía y sueldos pasan a **OK_PROVISORIO** (fuente: Excel equipo
   03-jul-2026); alcantarillado, duración electrodos, desinfectantes quedan **PD por validar**.

## 5. PENDIENTES QUE SOLO EL EQUIPO PUEDE CERRAR

- [ ] ¿Se paga alcantarillado/tratamiento (950 CLP/m³)? → define agua a 800 o 1.750
- [ ] Duración real electrodos PEF: ¿200 h o 300 h?
- [ ] Precio real productos desinfectantes por etapa (hoy: valor copiado)
- [ ] Dotación mensual RRHH (¿3 laboratoristas o 0,75 FTE?)
- [ ] Confirmar ruta operativa real: ¿prensa Y tricanter en serie, o alternativas?
- [ ] Tarifa eléctrica: ¿270 CLP/kWh incluye potencia y cargos fijos, o es solo energía?
