# CONTEXTO CANÓNICO — TrongkAI (números vigentes del modelo)

> Fuente de verdad para TODOS los agentes y schedules. Si un número de acá
> contradice al API live, manda el API y este archivo se actualiza.
> Actualizado por: daily-pulse / improver / /trongkai:sync-context.
> Última actualización: 2026-06-12 (commit b953b0c).

## Infraestructura
- Backend: FastAPI · https://trongkai-engine.fly.dev (Fly.io app `trongkai-engine`, región gru)
- Frontend: Next.js 14 · https://trongkai-web.vercel.app (48 rutas)
- Repo: github.com/Nikolaaa11/TrongkAI (branch main)
- Tests: **623 verde** (pytest, apps/engine) · tsc strict verde
- Deploy: `flyctl deploy --remote-only` (apps/engine) + `npx vercel deploy --prod --yes` (apps/web)
- ⚠️ ESTADO: token Fly EXPIRADO 2026-06-12 → backend en commit `e2fe8c9`;
  el afinamiento `b953b0c` (fijos 12 meses) espera `flyctl auth login` + deploy.

## Modelo de costos — DOS universos (no mezclar)

### PILOTO (27,5 t/año producto · 100 t MMPP · `balances/`)
Cadena anclada: `simulador_temporal → simulacion_revenue → prediccion_intervalos`
(los 3 dan EXACTAMENTE el mismo costo).
- OPEX completo anual (código b953b0c, post-afinamiento): **433,7M CLP**
  → costo unitario **15.771 CLP/kg**
  (mientras Fly sirva e2fe8c9 el live muestra 370,1M / 13.458 — NO es bug, es deploy pendiente)
- Composición: arriendo PEF+Tricanter 272,4M (12 meses calendario) ·
  labor 109,2M (8 personas ×1,35) · energía 31,1M · agua 20,4M · flete 0,6M
- Fijos: 31,8M/mes calendario (corren aunque la planta pare) · variable ~52M/año
- CAPEX piloto: ~270,6M CLP (equipos 188,5M + instalación 25% + ingeniería 35M)
- Bottleneck: Prensa Oelwerk 25 kg/h · yield proceso ~27,5%
- Banda de confianza: ±18% · exactitud del modelo: **62,5%** ("aproximado")

### INDUSTRIAL (50k ton/año · `plan_builder` + `financial`)
- TIR **30,7%** · VAN **$3,5B CLP** @ WACC 18% · payback 54 meses
- Valuación exit año 5: EV ~$135,7B (rango 112,8–169,1) · MOIC ~9,0×
- Monte Carlo (300 runs con clima): P5 8% · P50 26,6% · P95 43,8% · prob>WACC 78%
- Escenarios: **CONSERVADOR** (25k t, VAN −0,4B) · **INDUSTRIAL** (50k t, recomendado) ·
  **EXPANSION** (80k t, VAN 3,1B)
- Readiness Score: **76,8/100** ("PROMETEDOR")

## Verdad estratégica (PROHIBIDO contradecirla sin recalcular)
| SKU | Precio | Margen piloto | Rentable desde |
|---|---|---|---|
| Nutracéutico premium | $12.000/kg | −104M | **x10** (payback ~0,9a) |
| Ingrediente humano | $4.500/kg | −310M | **x50** |
| Harina animal premium | $1.400/kg | −395M | nunca |
| Harina animal básica | $850/kg | −410M | nunca |

El piloto NO es rentable con ningún SKU — prueba tecnología. El costo de
proceso es el mismo para todos los SKU; el PRECIO define el negocio.
Fuente live: `GET /simulacion/margen-por-sku`.

## Inputs PD top a validar (cada validación estrecha la banda)
1. **Precio venta por SKU** — sin cotización firme (driver #1 del revenue)
2. **Arriendo PEF** — 18,5M/mes sin cotización final (~61% del costo)
3. Tarifa agua Essbio + caudalímetro · tarifa energía · yield medido en planta

## Convenciones de plataforma
- Navegación por persona: Directorio / Operación / Inversionista / Análisis / Sistema
- Fuente única: KPIs plan → `/api/snapshot` · costo piloto → `/simulacion/revenue`
- Todo número visible declara su calidad (badge CalidadDato / niveles PD-PROVISORIO-VALIDADO)
- Snapshots de readiness: POST `/readiness/snapshot` (alimenta el diff de /comando)

## Pendientes de humano (no automatizables)
- `flyctl auth login` → luego deploy backend (publica b953b0c)
- Completar /equipo (placeholders "Por definir" visibles a LPs)
- Cotizaciones firmes: precio SKU + arriendo PEF
- Subir docs del equipo a inbox/
