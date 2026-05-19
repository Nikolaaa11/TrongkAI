# Known Issues — TrongkAI Platform

> Bugs y limitaciones conocidas que NO bloquean la operación pero deben corregirse cuando lleguen datos validados.

## KI-001 — TIR astronómica por precio promedio sin ponderar

**Severidad**: Calibración (no bug de código).
**Endpoint afectado**: `/plan`, `/plan/tornado`, `/plan/export`, `/whatif`.
**Síntoma**: La TIR del proyecto sale en órdenes de millones (37.000.000+) en lugar de los esperados ~10-25% anual.

**Causa raíz**: en `plan_builder.py:108` se calcula el precio promedio así:
```python
precio_promedio_clp_kg = sum(p.precios_clp_kg.values()) / len(p.precios_clp_kg)
```
Esto promedia 12 SKUs incluyendo el **licopeno a $80.000/kg** y la **proteína unicelular a $3.500/kg** como si **todo el volumen** se vendiera a ese precio promedio. Resultado: precio efectivo ~ $9.000/kg cuando el realismo dicta $1.200-$2.000/kg para la masa de productos base.

**Workaround actual**: ignorar la TIR absoluta; **los deltas relativos entre escenarios siguen siendo válidos** (la sensibilidad de tornado funciona porque opera sobre la misma base). La validación de "modo A vs modo B" en balance de masa NO se ve afectada.

**Fix correcto** (Fase 7 / cuando lleguen datos):
1. Agregar `volumen_pct_por_sku: dict[str, float]` en `ParametrosPlan` con la fracción de volumen total que va a cada SKU.
2. Calcular `precio_promedio_clp_kg = sum(precio[sku] * volumen_pct[sku]) / sum(volumen_pct[sku])`.
3. Bonus: separar la línea **Trongkai Feed** vs **Trongkai Food** y calcular EERR por marca.
4. Datos requeridos: cuota de mercado estimada de cada SKU en años 1-5 (PD bloqueante — owner Jaime + Comercial).

**Estimación de impacto**: con calibración correcta, la TIR base debería caer al rango 12-30% anual (depende del WACC). Esto invierte la firma de algunos escenarios (un escenario que hoy "mejora" la TIR podría empeorarla en realidad).

---

## KI-002 — Frontend Vercel sin deploy automático hoy (rate limit)

**Severidad**: Operacional.
**Síntoma**: el proyecto `nicolasrietta-1798s-projects/trongkai` está linkeado al repo pero el primer deploy fue rechazado con `api-deployments-free-per-day: more than 100`.

**Causa**: el improver autónomo (cada 1h) y otros proyectos del usuario en la cuenta personal consumieron el cupo gratuito de 100 deploys/24h.

**Workaround**: el próximo `git push` después de las ~24h reset gatilla deploy automáticamente. Alternativamente, upgrade a Vercel Pro.

**Validación**: una vez que deploye, las páginas `/`, `/agenda`, `/balance`, `/plan`, `/whatif`, `/supuestos`, `/about` consumirán automáticamente https://trongkai-engine.fly.dev vía `NEXT_PUBLIC_ENGINE_URL`.

---

## KI-003 — Engine en modo auth graceful (default abierto)

**Severidad**: Seguridad.
**Síntoma**: el engine en producción no requiere `X-API-Key` porque el secret `ENGINE_API_KEY` está unset (modo graceful — ver `main.py:require_api_key`).

**Justificación**: durante MVP, prioridad es UX del frontend funcionando. La auth requiere refactorizar el frontend para usar Next.js route handlers que inyecten el header server-side (no expone la key al cliente).

**Fix para activar auth en prod**:
```powershell
flyctl secrets set ENGINE_API_KEY=$(openssl rand -hex 32) -a trongkai-engine
# Setear el MISMO valor en Vercel como var server-side (sin NEXT_PUBLIC_):
npx vercel env add ENGINE_API_KEY production
# Refactorizar páginas a route handlers en apps/web/app/api/
```

---

## KI-004 — Default rendimiento_por_mmpp es aproximación

**Severidad**: Calibración.
**Síntoma**: `ParametrosPlan.rendimiento_por_mmpp` tiene valores hardcoded (ALPERUJO=0.39, TOMASA=0.20, etc.) que son aproximaciones razonables pero **NO validadas por José/Claudio**.

**Workaround**: los valores son consistentes con `MMPP_CATALOGO` del seed (alperujo MS 35% + 10% humedad residual ≈ 39%). En la UI, advertencia visible si el plan se exporta sin firma experta.

**Fix**: leer rendimientos efectivos del último `MixProduccionMensual` validado en DB cuando exista historia operativa real.

---

## KI-005 — Volúmenes anuales fijos sin curva de ramp-up por SKU

**Severidad**: Modelo financiero.
**Síntoma**: `volumen_pct_por_ano = {1:0.3, 2:0.55, 3:0.8, 4:0.95, 5:1.0}` aplica a **todo** el volumen, sin distinguir entre productos base (lanzamiento año 1) y PTEC (año 3-5).

**Fix**: matriz de ramp-up por SKU según `Producto.anoLanzamiento`.

---

## KI-006 — Capacidades de proceso default usadas en `/agenda` UI

**Severidad**: Modelo operacional.
**Síntoma**: la página `/agenda` envía capacidades hipotéticas en `CAPACIDADES_HIPOTESIS` (secador 2.5 ton/h) en lugar de leer de la DB.

**Fix**: cuando exista seed real en Postgres, leer de `CapacidadEquipo` vía tRPC o endpoint nuevo `/capacidades`.

---

## Resumen de prioridades

| ID | Prioridad | Bloqueante para | Owner |
|---|---|---|---|
| KI-001 | **Alta** | Reporte a directorio | Jaime + Comercial (cuotas volumen) |
| KI-005 | Alta | Reporte a directorio | Jaime |
| KI-004 | Media | Cierre Fase 3 | José + Claudio |
| KI-003 | Media | Hardening seguridad | Nicolás |
| KI-006 | Media | UX operacional | Matías (capacidades reales) |
| KI-002 | Baja | Demo pública | upgrade Vercel o esperar reset |
