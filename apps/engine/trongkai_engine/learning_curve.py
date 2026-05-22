"""Curva de aprendizaje (Wright's Law) sobre costos de proceso.

Fuente: Wright 1936 + extensión Bass.
Fórmula: Costo(N) = Costo(1) × N^(-b), donde b = -log2(learning_rate).
- learning_rate = 0.85 → -15% por doblamiento (manufactura típica).
- learning_rate = 0.90 → -10% por doblamiento (food processing).
- learning_rate = 0.80 → -20% por doblamiento (electrónica / curva pronunciada).

Para Trongkai usamos 0.90 conservador: cada vez que la producción acumulada
dobla, los costos unitarios de las etapas de proceso bajan 10%.

References:
- https://medium.com/10x-curiosity/learning-curves-and-wrights-law-744b85b897a2
- https://ourworldindata.org/learning-curve
"""

from __future__ import annotations

import math


def factor_descuento_aprendizaje(
    volumen_acumulado: float,
    volumen_base: float,
    learning_rate: float = 0.90,
) -> float:
    """Factor multiplicativo a aplicar al costo unitario.

    Devuelve 1.0 si volumen_acumulado <= volumen_base.
    Devuelve < 1.0 si hay aprendizaje aplicado.

    Ejemplo: learning_rate=0.90, vol_base=1000, vol_acum=2000 → factor=0.90 (-10%).
    """
    if volumen_acumulado <= volumen_base or volumen_base <= 0:
        return 1.0
    if not (0 < learning_rate <= 1):
        raise ValueError(f"learning_rate ∈ (0, 1], got {learning_rate}")
    if learning_rate == 1.0:
        return 1.0
    b = -math.log2(learning_rate)
    ratio = volumen_acumulado / volumen_base
    return ratio ** (-b)


def aplicar_curva_aprendizaje_a_costos(
    costo_etapa_base_clp_kg: dict[str, float],
    volumen_anual_ton: list[float],
    learning_rate: float = 0.90,
) -> list[dict[str, float]]:
    """Devuelve costo_etapa por año (5 años) aplicando curva de aprendizaje.

    Volumen base = volumen año 1 (ton). Cada año el volumen acumulado dobla
    cuando se acumulan otras (vol_base) unidades.

    Solo aplica a costos de etapas (no a costos MMPP que dependen del proveedor,
    no del aprendizaje).
    """
    if not volumen_anual_ton:
        return []
    vol_base = volumen_anual_ton[0] if volumen_anual_ton[0] > 0 else 1.0
    vol_acumulado = 0.0
    out = []
    for vol in volumen_anual_ton:
        vol_acumulado += vol
        factor = factor_descuento_aprendizaje(vol_acumulado, vol_base, learning_rate)
        out.append({etapa: costo * factor for etapa, costo in costo_etapa_base_clp_kg.items()})
    return out


def ahorro_por_aprendizaje_clp(
    costos_etapa_base_clp_kg: dict[str, float],
    volumen_anual_ton: list[float],
    learning_rate: float = 0.90,
) -> dict:
    """Ahorro total 5 años en CLP por aplicar curva de aprendizaje vs costo plano.

    Útil para reportar el upside del aprendizaje al directorio.
    """
    base_total_kg = sum(volumen_anual_ton) * 1_000
    costo_unit_base = sum(costos_etapa_base_clp_kg.values())
    costo_sin_curva = base_total_kg * costo_unit_base

    costos_por_ano = aplicar_curva_aprendizaje_a_costos(
        costos_etapa_base_clp_kg, volumen_anual_ton, learning_rate
    )
    costo_con_curva = sum(
        vol * 1_000 * sum(costos.values())
        for vol, costos in zip(volumen_anual_ton, costos_por_ano)
    )

    ahorro = costo_sin_curva - costo_con_curva
    return {
        "learning_rate": learning_rate,
        "costo_sin_curva_clp": costo_sin_curva,
        "costo_con_curva_clp": costo_con_curva,
        "ahorro_total_clp": ahorro,
        "ahorro_pct": ahorro / costo_sin_curva if costo_sin_curva else 0.0,
        "costo_unitario_ano1_clp_kg": sum(costos_por_ano[0].values()) if costos_por_ano else 0,
        "costo_unitario_ano5_clp_kg": sum(costos_por_ano[-1].values()) if costos_por_ano else 0,
    }
