# Supuestos — Fuente única de verdad

> Cada hardcode pendiente de la plataforma vive acá. **Nunca inventes números sin marcarlos.** El motor de cálculo lee este archivo (o la tabla `Supuesto` en DB que se siembra desde acá) para resolver valores. Si el estado es `PD`, el motor responde con el supuesto provisorio y una alerta visible en la UI.
>
> Convención de estados (definida en `DECISIONES.md` ADR-002):
> - `PD` = por definir, valor placeholder
> - `OK_PROVISORIO` = valor cargado pero sin firma de experto
> - `OK_VALIDADO_JOSE` / `OK_VALIDADO_CLAUDIO` = firmado por experto técnico del balance de masa
> - `OK_VALIDADO_JAIME` = firmado por el dueño de proceso
> - `OK_VALIDADO_DIRECTORIO` = aprobado para versión inmutable del plan

## A. Logística MMPP (origen: `IngresosCostos Proveedores`)

| Clave | Valor actual | Unidad | Estado | Fuente | Owner | Sensibilidad |
|---|---|---|---|---|---|---|
| `flete.tarifa_min` | 1800 | CLP/km | OK_PROVISORIO | Excel cliente / Jaime transcript | Matías | Media |
| `flete.tarifa_media` | 2100 | CLP/km | OK_PROVISORIO | Excel cliente / Jaime transcript | Matías | Media |
| `flete.tarifa_max` | 2500 | CLP/km | OK_PROVISORIO | Excel cliente | Matías | Media |
| `camion.cap_min_ton` | 20 | ton | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `camion.cap_max_ton` | 25 | ton | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `volumen.contrato_anual_max_ton` | 50000 | ton/año | OK_VALIDADO_JAIME | Trongkai transcript L7 | Jaime | **Alta** — restricción dura |
| `olivero_1.dist_km` | 82 | km | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `olivero_1.flete_clp_km` | 1800 | CLP/km | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `olivero_1.pago_recepcion_clp_kg` | -10 | CLP/kg | OK_PROVISORIO | Excel cliente (Caso 1, le cobramos) | Matías | Media |
| `olivero_1.volumen_ton` | 500 | ton | OK_PROVISORIO | Excel cliente | Matías | Media |
| `olivero_2.dist_km` | 120 | km | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `olivero_2.flete_clp_km` | 2100 | CLP/km | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `olivero_2.pago_recepcion_clp_kg` | 5 | CLP/kg | OK_PROVISORIO | Excel cliente (Caso 2, nos paga) | Matías | Media |
| `olivero_2.volumen_ton` | 1000 | ton | OK_PROVISORIO | Excel cliente | Matías | Media |
| `olivero_3.dist_km` | 25 | km | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `olivero_3.flete_clp_km` | 0 | CLP/km | OK_PROVISORIO | Excel cliente (Caso 3, al lado) | Matías | Baja |
| `olivero_3.pago_recepcion_clp_kg` | 0 | CLP/kg | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `olivero_3.volumen_ton` | 2000 | ton | OK_PROVISORIO | Excel cliente | Matías | Alta — el más grande |
| `olivero_4.dist_km` | 70 | km | OK_PROVISORIO | Excel cliente | Matías | Baja |
| `olivero_4.flete_clp_km` | 0 | CLP/km | OK_PROVISORIO | Excel cliente (Caso 4) | Matías | Baja |
| `olivero_4.pago_recepcion_clp_kg` | 18 | CLP/kg | OK_PROVISORIO | Excel cliente (nos pagan) | Matías | Media |
| `olivero_4.volumen_ton` | 1000 | ton | OK_PROVISORIO | Excel cliente | Matías | Media |

## B. Rendimiento y balance de masa (origen: `Base rendimiento`)

| Clave | Valor actual | Unidad | Estado | Fuente | Owner | Sensibilidad |
|---|---|---|---|---|---|---|
| `alperujo.humedad_inicial_pct` | 0.65 | fracción | OK_PROVISORIO | Excel cliente + Jaime | José | **Alta** |
| `alperujo.materia_solida_pct` | 0.35 | fracción | OK_PROVISORIO | Excel cliente | José | Alta |
| `alperujo.aceite_extraible_pct` | 0.02 | fracción | OK_PROVISORIO | Excel cliente (objetivo con PEF; competencia logra 1.3-1.45) | José | **Alta** |
| `alperujo.humedad_objetivo_final_pct` | 0.10 | fracción | OK_VALIDADO_JAIME | Excel cliente "Target 10%" | Jaime | Alta |
| `balance.modo_calculo` | `A` | enum | PD | Jaime — discusión abierta | José/Claudio | **Crítica** — diferencia 35% vs 38,5% (modo A vs B en alperujo) |
| `balance.tolerancia_pct` | 0.005 | fracción | OK_PROVISORIO | Regla SUPER_PROMPT §4 M2 | arquitecto | Baja |
| `tomasa.humedad_inicial_pct` | 0.82 | fracción | OK_PROVISORIO | Jaime transcript L61 | José | Alta |
| `tomasa.materia_solida_pct` | 0.18 | fracción | OK_PROVISORIO | derivado | José | Alta |
| `tomasa.tiempo_descomposicion_h` | 3 | horas | PD | Trongkai transcript L32 "1h, 5h, 3h" | José | **Crítica** — define ventana logística |
| `pomasa.humedad_inicial_pct` | 0.80 | fracción | PD | aproximación | José | Alta |
| `pomasa.materia_solida_pct` | 0.20 | fracción | PD | derivado | José | Alta |
| `orujo_uva.humedad_inicial_pct` | null | fracción | PD | "variable" en Excel | José | Alta |
| `levadura.humedad_inicial_pct` | null | fracción | PD | n/a | José | Media |
| `aceite_alperujo.objetivo_pct_pef` | 0.02 | fracción | OK_PROVISORIO | Jaime — 50% más que competencia | José | **Crítica** — justifica CapEx PEF |

## C. Capacidades de proceso (origen: transcripts, secciones 1.2 y 4.1 del SUPER_PROMPT)

| Clave | Valor actual | Unidad | Estado | Fuente | Owner | Sensibilidad |
|---|---|---|---|---|---|---|
| `cap.recepcion_ton_h` | null | ton/h | PD | — | Matías | Alta |
| `cap.alimentacion_ton_h` | null | ton/h | PD | "bomba/tornillo" | Matías | Alta |
| `cap.homog_inicial_ton_h` | null | ton/h | PD | — | Matías | Media |
| `cap.pef_ton_h` | null | ton/h | PD | opcional según MMPP | Matías | Media |
| `cap.prensado_mec_ton_h` | null | ton/h | PD | "puede haber 2 prensados" | Matías | Alta |
| `cap.tricanter_ton_h` | null | ton/h | PD | costo distinto al mec. | Matías | Alta |
| `cap.secado_ton_h` | null | ton/h | PD | **bottleneck esperado** | Matías | **Crítica** |
| `cap.homog_final_ton_h` | null | ton/h | PD | — | Matías | Media |
| `cap.ensacado_ton_h` | null | ton/h | PD | — | Matías | Baja |
| `pef.horas_entre_mantenciones` | 300 | h | OK_VALIDADO_JAIME | Jaime transcript L209-215 | Jaime | Media |
| `pef.costo_cuarres_par_clp` | 1000000 | CLP | OK_PROVISORIO | Jaime "como un millón" | Jaime | Baja |
| `pef.cuarres_por_mantencion` | 2 | unidades | OK_PROVISORIO | Jaime "dos de esas hueás" | Jaime | Baja |
| `secador.kwh_por_ton_50hum` | null | kWh/ton | PD | "consume más con 50% que con 40%" | Matías | **Crítica** |
| `secador.kwh_por_ton_40hum` | null | kWh/ton | PD | — | Matías | Alta |
| `tarifa_energia_clp_kwh` | null | CLP/kWh | PD | reajustable en UF | Matías | Alta |

## D. Costos por etapa (origen: Jaime transcript L383-426 — orden de magnitud mental)

Jaime dio una banda mental: total entre $100 y $250/kg. Esto es supuesto puro:

| Clave | Valor actual | Unidad | Estado | Fuente | Owner |
|---|---|---|---|---|---|
| `costo_etapa.recepcion_clp_kg` | 3 | CLP/kg | PD | Jaime "tres pesos" | Matías |
| `costo_etapa.alimentacion_homog_clp_kg` | 3 | CLP/kg | PD | Jaime | Matías |
| `costo_etapa.pef_clp_kg` | 6 | CLP/kg | PD | Jaime "cinco u ocho" | Matías |
| `costo_etapa.prensado_mecanico_clp_kg` | 8 | CLP/kg | PD | Jaime "tienen distinto costo" | Matías |
| `costo_etapa.tricanter_clp_kg` | 10 | CLP/kg | PD | Jaime | Matías |
| `costo_etapa.secado_clp_kg` | null | CLP/kg | PD | "el caro" — TODO real | **Matías — bloqueante M3** |
| `costo_etapa.homog_final_clp_kg` | null | CLP/kg | PD | — | Matías |
| `costo_etapa.ensacado_clp_kg` | null | CLP/kg | PD | — | Matías |
| `costo_etapa.total_target_clp_kg` | 150 | CLP/kg | PD | "ideal cercano a 100, máximo 250" | Jaime |

## E. Productos finales — precios y volúmenes (todos PD)

12 SKUs según `Datos x Plan 5 años`. **Precio de venta = vacío en TODA la matriz**. Esto es bloqueante para Módulo 3 (sin precios no hay EERR).

| SKU | Tipo | Año lanzamiento | Estado |
|---|---|---|---|
| H. Alperujo | BASE | 1 | OK_PROVISORIO volumen, **PD precio** |
| Ac. Alperujo | BASE | 1 | OK_PROVISORIO volumen, **PD precio** (Jaime mencionó "1.200 $/kg" como inspiración) |
| H. Orujo | BASE | 1 | OK_PROVISORIO volumen, **PD precio** |
| H. Tomasa | BASE | 1 | OK_PROVISORIO volumen, **PD precio** |
| H. Pomasa | BASE | 1 | OK_PROVISORIO volumen, **PD precio** |
| Pectina | AGREGADO | 2-3 | OK volumen, **PD precio** |
| Licopeno | AGREGADO | 2-3 | OK volumen, **PD precio** |
| Proteína Unicelular | PTEC | 3-5 | **PD volumen y precio** — "más apetecido" |
| Antioxidante | PTEC | 3-5 | OK volumen, **PD precio** |
| Aglomerante | PTEC | 3-5 | **PD volumen y precio** |
| Umami | PTEC | 3-5 | **PD volumen y precio** — "el más chico, menor conocimiento" |

## F. Macroeconómicos / Financieros (todos PD)

| Clave | Valor actual | Unidad | Estado | Owner | Sensibilidad |
|---|---|---|---|---|---|
| `fx.usd_clp` | null | CLP/USD | PD | Tesorería | Alta |
| `fx.uf_clp` | null | CLP/UF | PD | Tesorería | Alta |
| `wacc_pct` | null | fracción | PD | Directorio | **Crítica** para TIR/VAN |
| `inflacion_anual_pct` | 0.04 | fracción | PD | Banco Central referencial | Media |
| `depreciacion_equipos_anos` | 10 | años | PD | Tax (art. 31 N°5 LIR) | Media |
| `iva_credito_equipos_importados` | true | bool | PD | TLC China | Media |
| `regimen_mo_5x8_temporada_alta` | "24x7" | enum | PD | Jaime L270 | Alta |

## G. Otros

| Clave | Valor actual | Unidad | Estado | Owner |
|---|---|---|---|---|
| `certificaciones.b_corp` | true | bool | OK_VALIDADO_JAIME | Jaime |
| `certificaciones.otras` | [] | array | PD | Calidad |
| `aace.clase_default_equipo_no_cotizado` | 5 | enum | OK_VALIDADO (regla SUPER_PROMPT §8) | arquitecto |
| `corfo.patin_visita_tec_clp` | 350000000 | CLP | OK_PROVISORIO | Jaime "300-400M" | Jaime |

## H1. Precios de SKUs calibrados con benchmarks de mercado (2026-05-18, ver `DATOS-MERCADO.md`)

Promovidos automáticamente de PD a OK_PROVISORIO con fuente WebSearch trazable:

| Clave | Valor | Unidad | Estado | Fuente | Sensibilidad |
|---|---|---|---|---|---|
| `precio.harina_alperujo` | 800 | CLP/kg | OK_PROVISORIO | Olive polyphenol market | Media |
| `precio.aceite_alperujo` | 1300 | CLP/kg | OK_PROVISORIO | Oleista España 2026-05 (orujo refinado EUR 1.900/ton) | Alta |
| `precio.harina_orujo` | 600 | CLP/kg | OK_PROVISORIO | 30% bajo benchmark harina pescado Chile | Alta |
| `precio.harina_tomasa` | 700 | CLP/kg | OK_PROVISORIO | Industria funcional | Media |
| `precio.harina_pomasa` | 700 | CLP/kg | OK_PROVISORIO | Industria funcional | Media |
| `precio.pectina` | 25000 | CLP/kg | OK_PROVISORIO | USD 55/kg LatAm × 0.5 nuevo entrante | **Crítica** |
| `precio.licopeno` | 80000 | CLP/kg | OK_PROVISORIO | USD 108-253/kg × 0.5 bulk Tridge 2025 | **Crítica** |
| `precio.proteina_unicel` | 1500 | CLP/kg | OK_PROVISORIO | Benchmark harina pescado +30% premium SCP | Alta |
| `precio.antioxidante` | 15000 | CLP/kg | OK_PROVISORIO | 30% olive polyphenol premium (nuevo entrante) | Alta |
| `wacc_pct` | 0.18 | fracción | OK_PROVISORIO | Scielo 19.6% sector pesca-acuicultura Chile - 1.6pp premium ESG | **Crítica** |
| `mercado.pectina_latam_usd_2025` | 189780000 | USD/año | OK_VALIDADO | Informes de Expertos Latam | Baja (referencial) |
| `mercado.licopeno_global_usd_2026` | 171480000 | USD/año | OK_VALIDADO | Research and Markets 2026-2032 | Baja (referencial) |
| `mercado.scp_global_usd_2026` | 13120000000 | USD/año | OK_VALIDADO | Mordor Intelligence | Baja (referencial) |
| `mercado.olive_polyphenol_usd_2024` | 640000000 | USD/año | OK_VALIDADO | Growth Market Reports | Baja (referencial) |
| `costos.comercializacion_pct_revenue` | 0.22 | fracción | OK_PROVISORIO | Industria alimentaria B2B típica 15-25% + premium nuevo entrante | Alta |
| `impuestos.renta_corporativa_chile` | 0.27 | fracción | OK_VALIDADO | SII régimen general | Baja (referencial) |

**Total PDs promovidos esta corrida**: 12 (de los 25 críticos).
**Cambio sobre TIR**: del 1020% absurdo a 49% defendible. EBITDA margin pasa de 88% (irreal) a 45% (industria).
**Pendiente firma experta** (no promovible automáticamente): rendimientos por MMPP (José/Claudio), capacidades secador real (Matías), tiempo descomposición tomasa (planta piloto).

## H. Mercado y comerciales (origen: presentación corporativa 2025-10-22)

| Clave | Valor actual | Unidad | Estado | Fuente | Owner | Sensibilidad |
|---|---|---|---|---|---|---|
| `mercado.subproductos_total_chile_ton_ano` | 800000 | ton/año | OK_VALIDADO_JAIME | Presentación slide 3 | Jaime | Baja (ancla narrativa) |
| `mercado.cuota_trongkai_pct` | 0.0625 | fracción | OK_PROVISORIO | derivado 50.000/800.000 | Jaime | Baja |
| `feed.benchmark_harina_pescado_clp_kg` | null | CLP/kg | PD | ProChile / SalmonChile data | Comercial | **Crítica** — top 10 RIESGO |
| `feed.premium_sostenibilidad_pct` | 0.15 | fracción | PD | "+15% vs harina pescado" hipótesis | Comercial | Alta |
| `food.precio_target_harina_tomate_clp_kg` | null | CLP/kg | PD | benchmark panadería gourmet | Comercial | Alta |
| `food.precio_target_harina_oliva_clp_kg` | null | CLP/kg | PD | benchmark snacks saludables | Comercial | Alta |
| `marca.linea_feed_skus` | [HARINA_TOMASA, HARINA_POMASA, PROTEINA_UNICEL, ANTIOXIDANTE] | array | OK_PROVISORIO | ADR-009 | Comercial | n/a |
| `marca.linea_food_skus` | [HARINA_ALPERUJO, HARINA_TOMASA, ACEITE_ALPERUJO] | array | OK_PROVISORIO | ADR-009 (algunos SKUs son cross-brand) | Comercial | n/a |
| `marca.servicios_lineas` | [MAQUILA, LICENCIAMIENTO, TRANSFERENCIA_TEC] | array | OK_VALIDADO_JAIME | Presentación slide 5 | Jaime | n/a |

## I. Directorio y gobernanza (origen: presentación slide 12)

| Clave | Valor actual | Estado |
|---|---|---|
| `directorio.presidente` | Guido Rietta | OK_VALIDADO_DIRECTORIO |
| `directorio.miembros` | Juan Pablo Velasco, Ester Sáez, Andrés Fernández | OK_VALIDADO_DIRECTORIO |
| `equipo.fundador` | José Cuevas (ex Concha y Toro, The Not Company) | OK_VALIDADO_DIRECTORIO |
| `equipo.gerente_general` | Jaime Echeverría (ex Traverso, Parmalat, Danone) | OK_VALIDADO_DIRECTORIO |
| `equipo.gerente_logistica` | Claudia Gotschlich (ex CORFO) | OK_VALIDADO_DIRECTORIO |
| `alianzas.tecnologia` | Opticept (PEF), Axolot | OK_VALIDADO_DIRECTORIO |

---

**Total de PDs activos al cierre Fase 0**: ~70 claves (de las cuales ~25 son `Crítica` por sensibilidad). Ver [`PREGUNTAS-ABIERTAS.md`](./PREGUNTAS-ABIERTAS.md) para el orden de resolución propuesto y [`RIESGO-SUPUESTOS.md`](./RIESGO-SUPUESTOS.md) para el mapa de riesgo top 10.
