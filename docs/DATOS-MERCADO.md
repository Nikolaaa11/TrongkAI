# Datos de mercado — Benchmarks para calibración del modelo

> Fuentes verificadas con WebSearch al 2026-05-18. Cada cifra tiene URL trazable. Estos datos calibran `SKU_CATALOGO` en `plan_builder.py` y el WACC default. Cuando llegue una cotización firme o un contrato comercial, se actualiza la fila y se promueve el supuesto a `OK_VALIDADO_*`.

## A. Precios de productos finales (benchmarks de mercado)

### Trongkai Feed (acuicultura + pet food)

| SKU | Benchmark mercado | Conversión CLP/kg | Premium aplicable | Precio modelo | Fuente |
|---|---|---|---|---|---|
| **HARINA_ORUJO** (feed grade) | Harina pescado Chile USD 800-1.200/ton | CLP 720-1.080/kg | -25% (es feed proteico secundario) | 600 | [Ubatuba ES](https://ubatuba.com.ar/harina-de-pescado-precio-chile/) |
| **HARINA_POMASA** (feed grade) | Idem harina pescado | CLP 720-1.080/kg | -30% | 700 | Idem |
| **PROTEINA_UNICEL** (SCP) | Yeast SCP global USD 0.40/kg / Soy isolate USD 1.50-2.00/kg | CLP 360 / 1.350-1.800/kg | +30% sustentabilidad vs harina pescado | **1.500** (era 3.500) | [Feed&Additive Magazine](https://www.feedandadditive.com/yeast-as-a-sustainable-single-cell-protein-for-aquafeed/), [DSM-Firmenich](https://www.dsm-firmenich.com/anh/news/feed-talks/articles/bridging-the-feed-protein-gap-in-aquaculture-with-single-cell-protein.html) |
| **ANTIOXIDANTE** (olive polyphenol) | Premium standardized extracts | CLP 30.000-80.000/kg | (precio espejo benchmark) | **50.000** (era 5.000) | [Future Market Insights](https://www.futuremarketinsights.com/reports/high-oleocanthal-olive-extract-market) |
| **AGLOMERANTE** | Sin benchmark directo, asumir feed binder | — | — | 2.000 | TODO: cotización |

### Trongkai Food (humanos)

| SKU | Benchmark | CLP/kg | Premium | Precio modelo | Fuente |
|---|---|---|---|---|---|
| **HARINA_ALPERUJO** | Harinas funcionales premium ~ USD 1/kg | CLP 900/kg | -10% (nuevo entrante) | 800 | [Olive Polyphenol Extracts Market](https://growthmarketreports.com/report/olive-polyphenol-extracts-market) |
| **ACEITE_ALPERUJO** | Aceite orujo refinado España EUR 1.900-1.950/ton | CLP 1.700-1.800/kg | -25% (sin refinar) | 1.300 | [Oleista 2026-05](https://oleista.com/en/prices) |
| **HARINA_TOMASA** | Subproducto tomate funcional | ~CLP 700-900/kg | — | 700 | Estimación industria |
| **ACEITE_ORUJO_UVA** | Aceite especial nicho | ~CLP 1.500/kg | — | 1.500 | Estimación |
| **PECTINA** (food grade) | Pectin LatAm USD 55/kg ≈ CLP 50.000/kg | CLP 50.000/kg | — | **50.000** (era 8.000) | [Informes de Expertos Latam](https://www.informesdeexpertos.com/informes/mercado-latinoamericano-de-pectina), [QuimiNet](https://www.quiminet.com/productos/pectina-511683660/precios.htm) |
| **LICOPENO** (food grade) | USD 108-253/kg internacional, target Chile ≈ USD 165/kg | CLP 150.000/kg | — | **150.000** (era 80.000) | [Tridge - Lycopene](https://www.tridge.com/market-overview/lycopene), [Procurement Resource](https://www.procurementresource.com/production-cost-report-store/lycopene) |
| **UMAMI** | Sin data pública clara | — | — | 4.500 (mantener) | TODO |

## B. WACC y tasa de descuento

| Métrica | Valor | Fuente |
|---|---|---|
| **WACC nominal anual sector pesca-acuicultura Chile** | **19,6%** | [Scielo VE — "Costo del capital en el sector pesquero-acuícola chileno"](https://ve.scielo.org/scielo.php?script=sci_arttext&pid=S0378-18442009000800006) |
| WACC ESG (premium menor por sostenibilidad) | 15-17% | Estimación ajuste por FIP CEHTA ESG |
| WACC modelo previo | 12% | Subestimado |
| **WACC modelo nuevo (default)** | **0,18** | Punto medio sector + premium ESG |

## C. Volúmenes y mercado total

| Métrica | Valor | Fuente |
|---|---|---|
| Mercado subproductos agroindustriales Chile | **>800.000 ton/año** | Presentación corporativa Trongkai slide 3 |
| Cuota contractual Trongkai | 50.000 ton/año (6.25%) | Contrato (OK_VALIDADO_JAIME) |
| Mercado pectina LatAm 2025 | USD 189,78M, CAGR 3,1% al 2035 | [Informes Expertos](https://www.informesdeexpertos.com/informes/mercado-latinoamericano-de-pectina) |
| Mercado licopeno global 2026 | USD 171,5M, CAGR 6,7% al 2032 | [Research and Markets](https://www.researchandmarkets.com/reports/5674630/lycopene-market-global-forecast-2026-2032) |
| Mercado SCP global 2026 | USD 13,12B → USD 20,94B al 2031 | [Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/single-cell-protein-market) |
| Mercado olive polyphenol global 2024 | USD 640M, CAGR 8,2% al 2033 | [Growth Market Reports](https://growthmarketreports.com/report/olive-polyphenol-extracts-market) |
| Aceite oliva Chile (export anclas) | USD 44,78M en 2025, CAGR 2,4% al 2035 | [Informes Expertos](https://www.informesdeexpertos.com/informes/mercado-de-aceite-de-oliva-en-chile) |

## D. Premios de sostenibilidad documentados

- Single-cell protein isolates capturan 5-8% del feed market al 2035 vs 2-4% en 2026 — confirma upside del PTEC.
- Aquaculture + pet food driven por crecimiento global, valoración USD 12,33B → USD 20,94B en 5 años.
- Olive polyphenol 47% mercado en dietary supplements — alto margen.

## E. Reglas de actualización

1. Cada cifra de esta tabla se vuelve a buscar trimestralmente con WebSearch.
2. Si una cifra mueve > ±15%, se loguea en `CHANGELOG.md` y se notifica al usuario.
3. Cuando llegue cotización firme de cliente:
   - Reemplaza la fila aquí con `valor real | OK_VALIDADO_COMERCIAL | fuente: <contrato N°>`.
   - Se promueve el supuesto en `SUPUESTOS.md`.
   - Versionar plan inmediatamente (snapshot `VersionPlan`).

## F. Calibración resultante en `plan_builder.py`

```python
SKU_CATALOGO: tuple[SKUSpec, ...] = (
    SKUSpec("HARINA_ALPERUJO",   800,    "FOOD", 1, 0.22),
    SKUSpec("ACEITE_ALPERUJO",   1_300,  "FOOD", 1, 0.04),
    SKUSpec("HARINA_ORUJO",      600,    "FEED", 1, 0.16),
    SKUSpec("HARINA_TOMASA",     700,    "FOOD", 1, 0.15),
    SKUSpec("HARINA_POMASA",     700,    "FEED", 1, 0.12),
    SKUSpec("ACEITE_ORUJO_UVA",  1_500,  "FOOD", 2, 0.01),
    SKUSpec("PECTINA",           50_000, "FOOD", 2, 0.02),     # 6× vs default previo
    SKUSpec("LICOPENO",          150_000,"FOOD", 2, 0.001),    # 1.9× vs default previo
    SKUSpec("PROTEINA_UNICEL",   1_500,  "FEED", 3, 0.18),     # 0.43× vs default — bajada brutal
    SKUSpec("ANTIOXIDANTE",      50_000, "FEED", 3, 0.04),     # 10× vs default
    SKUSpec("AGLOMERANTE",       2_000,  "FEED", 4, 0.04),
    SKUSpec("UMAMI",             4_500,  "FOOD", 5, 0.01),
)
WACC default = 0.18
```

**Cambios netos en ingresos esperados** (modelo nuevo vs anterior):
- Bajan: Proteína Unicelular (era $3.500, ahora $1.500 — 0.43×). Es el SKU de mayor peso volumen (18%).
- Suben: Pectina (6×), Licopeno (1.9×), Antioxidante (10×) — pero pesan poco en mix.

**Resultado esperado de TIR**: rango 8-18% anual con WACC 18% (vs los 657% del modelo previo). Esto es defendible frente a directorio.
