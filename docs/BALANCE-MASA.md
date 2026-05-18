# Memoria de cálculo — Balance de masa Trongkai

> Este documento es la **especificación viva** del motor del Módulo 2. Cada cambio de fórmula se versiona acá con su PR asociado. Validación obligatoria con **José y Claudio** antes de promover a `OK_VALIDADO_*`.

## 1. Definiciones

- $m_{\text{in}}$: masa total que entra a planta (ton).
- $h_{\text{in}}$: humedad inicial fracción (ej. 0.65 = 65%).
- $s_{\text{in}} = 1 - h_{\text{in}}$: materia sólida inicial.
- $h_{\text{out}}$: humedad objetivo final (default 0.10).
- $r_{\text{aceite}}$, $r_{\text{licopeno}}$, $r_{\text{pectina}}$: rendimientos de extracción de cada subproducto (sobre la **base elegida**).
- $m_{\text{evap}}$: masa de agua evaporada en secado.
- $m_{\text{prod,i}}$: masa de producto final $i$.
- $m_{\text{perdida}}$: pérdidas no recuperables (mermas mecánicas, residuos no valorizados).

## 2. Restricción dura

Para todo lote:

$$\sum_i m_{\text{prod},i} + m_{\text{evap}} + m_{\text{perdida}} = m_{\text{in}} \pm 0.5\%$$

Si la igualdad falla, el motor **lanza `MassBalanceError`** y no permite persistir el `MixProduccionMensual` ni el `Recepcion`. Tolerancia parametrizable en `Supuesto: balance.tolerancia_pct`.

## 3. Modo A — Base inicial

$$m_{\text{prod,base}} = m_{\text{in}} \cdot s_{\text{in}} \cdot (1 + \text{factor humedad residual})$$

Ejemplo SUPER_PROMPT, alperujo:

| Var | Valor |
|---|---|
| $m_{\text{in}}$ | 1.0 (normalizado) |
| $h_{\text{in}}$ | 0.65 |
| $s_{\text{in}}$ | 0.35 |
| $r_{\text{aceite}}$ | 0.02 |
| $h_{\text{out}}$ | 0.10 |

Cálculo:
- Materia seca real = $1.0 \times 0.35 = 0.35$
- Aceite extraído = $1.0 \times 0.02 = 0.02$ (sobre base inicial)
- Harina (MS final + humedad residual) = $0.35 \times (1 / (1 - 0.10)) - 0.02 \approx 0.369$
- Agua evaporada = $1.0 - 0.369 - 0.02 - \text{pérdidas} \approx 0.611$ (con pérdidas 0%)

**Materia seca neta entregada** ≈ 35% del input.

## 4. Modo B — Base deshidratada

$$m_{\text{prod,base}} = (m_{\text{in}} \cdot s_{\text{in}}) \cdot \frac{1}{1 - h_{\text{out}}}$$

Mismo ejemplo:
- Materia seca pura = $0.35$
- Producto final con 10% humedad incorporada = $0.35 / 0.90 = 0.389$ → **38.9% del input**

**Diferencia material vs modo A**: 38.9% vs 35% ≈ **+11% relativo** en peso entregado al cliente. Esto **mueve la TIR** porque la facturación se hace por kg vendido.

## 5. Bandera de modo

```python
class BalanceMode(str, Enum):
    A_INITIAL_BASE = "A"
    B_DEHYDRATED_BASE = "B"

def compute_mass_balance(
    input_ton: float,
    mmpp: MateriaPrima,
    mode: BalanceMode = BalanceMode.A_INITIAL_BASE,
    yield_overrides: dict[str, float] | None = None,
) -> MassBalanceResult: ...
```

La UI muestra siempre ambos resultados con un delta visual hasta que José/Claudio firmen ADR-003 con uno definitivo.

## 6. Casos de test obligatorios (Módulo 2)

| Caso | Input | Output esperado (A) | Output esperado (B) |
|---|---|---|---|
| **Alperujo base** | 1 ton, h=0.65, ms=0.35, aceite=0.02 | MS neta 0.350, aceite 0.02, agua evap. 0.611, pérdida 0.019 | MS neta 0.389, aceite 0.022, agua evap. 0.589 |
| **Tomasa h=0.82** | 1 ton, h=0.82, ms=0.18 | MS neta 0.180 | MS neta 0.200 |
| **Cero pérdidas** | cualquier | balance cierra ±0.5% | balance cierra ±0.5% |
| **Pérdida = 100%** | cualquier | `MassBalanceError` (suma negativa) | `MassBalanceError` |
| **Humedad final 0%** | cualquier | OK (caso extremo) | OK |
| **Humedad final 100%** | cualquier | `ValueError` (sin sentido físico) | `ValueError` |

## 7. Pérdidas y mermas — supuestos iniciales

Hasta tener datos de planta piloto:

| Etapa | Pérdida estimada | Estado |
|---|---|---|
| Recepción → Alimentación | 0.5% | PD |
| Alimentación → Homogenización | 0.3% | PD |
| Homogenización → PEF | 0.2% | PD |
| PEF → Prensado | 1.0% | PD |
| Prensado → Extracción | 0.5% | PD |
| Extracción → Secado | 0.3% | PD |
| Secado → Homogenización final | 0.2% | PD |
| Homogenización final → Ensacado | 0.1% | PD |
| **Total acumulado** | **~3.1%** | PD |

## 8. Entregable de validación M2 (sección 4 del SUPER_PROMPT)

Replicar exactamente el caso alperujo del Excel `Base rendimiento` y obtener:
- **Modo A**: MS final = 35% del input, humedad residual = 10%.
- **Modo B**: MS final = 38.9% (~38.5%) del input, humedad residual = 10%.
- Diferencia documentada en este archivo en versión final del PR.

## 9. Sankey

El motor expone `to_sankey_dict()` que retorna:

```json
{
  "nodes": ["Recepción", "Alimentación", "PEF", "Prensado", "Extracción", "Secado", "Homog. Final", "Ensacado",
            "Aceite Alperujo", "Harina Alperujo", "Agua Evaporada", "Pérdidas"],
  "links": [{"source": "Recepción", "target": "Alimentación", "value": 0.995}, ...]
}
```

Cifras en ton normalizadas a 1 (o ton reales si se llama con lote concreto). Renderizado en frontend con **ECharts Sankey** (no Recharts, no soporta Sankey nativo).
