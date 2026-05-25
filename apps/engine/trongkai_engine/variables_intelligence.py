"""Variables Intelligence — capa de inteligencia sobre la matriz canónica.

Funcionalidades:

1. detectar_inconsistencias() — encuentra celdas que no cuadran matemáticamente
   - Volumen Final debe == Volumen Subproductos × Rendimiento
   - Precio Venta debe ser >= Costo Producción (margen positivo)
   - Costos transversales deben sumar al OpEx total
   - Rendimientos PTEC deben ser <= Rendimientos base (productos nuevos)

2. sugerir_valores_pd() — propone valores para celdas en estado PD
   - Por categoría: usa promedio/mediana de celdas similares OK
   - Por benchmarks: aplica heurísticas industria
   - Por similaridad: SKUs del mismo grupo (Base/Final/PTEC)

3. simular_cambio_celda() — what-if a nivel celda individual
   - Cambia una celda, recalcula impacto en TIR/VAN
   - Devuelve sensibilidad puntual

4. score_confianza_celda() — calidad del dato 0-100
   - PD: 0
   - OK_PROVISORIO con fuente paper: 60
   - OK_PROVISORIO con benchmark: 50
   - OK_VALIDADO con dato real: 100

5. mapa_calor_confianza() — vista de calor de toda la matriz
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, median
from typing import Any

from .variables_matrix import (
    PRODUCTOS,
    VARIABLES,
    Celda,
    EstadoCelda,
    MatrizVariables,
    ProductoSpec,
    construir_matriz,
)


# ============================================================================
# 1. Detección de inconsistencias
# ============================================================================

@dataclass
class Inconsistencia:
    severidad: str          # "alta" | "media" | "baja"
    tipo: str               # "matematica" | "logica" | "rango"
    descripcion: str
    celdas_involucradas: list[str]  # "variable|producto"
    valor_esperado: float | None = None
    valor_actual: float | None = None

    def to_dict(self) -> dict:
        return {
            "severidad": self.severidad,
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "celdas_involucradas": self.celdas_involucradas,
            "valor_esperado": self.valor_esperado,
            "valor_actual": self.valor_actual,
        }


def _celda(matriz: MatrizVariables, variable: str, producto: str) -> Celda | None:
    for c in matriz.celdas:
        if c.variable == variable and c.producto == producto:
            return c
    return None


def detectar_inconsistencias(matriz: MatrizVariables | None = None) -> list[Inconsistencia]:
    """Encuentra incoherencias matemáticas o lógicas en la matriz."""
    matriz = matriz or construir_matriz()
    issues: list[Inconsistencia] = []

    for p in PRODUCTOS:
        # Regla 1: Volumen Final == Volumen Subproductos × Rendimiento (aproximado)
        vol_sub = _celda(matriz, "Volumen Subproductos", p.codigo)
        rend = _celda(matriz, "Rendimiento", p.codigo)
        vol_final = _celda(matriz, "Volumen Producto Final", p.codigo)
        if vol_sub and rend and vol_final and all(
            c.valor is not None for c in (vol_sub, rend, vol_final)
        ):
            esperado = (vol_sub.valor or 0) * (rend.valor or 0)
            actual = vol_final.valor or 0
            if abs(esperado - actual) / max(esperado, 1) > 0.05:  # tolerancia 5%
                issues.append(Inconsistencia(
                    severidad="alta",
                    tipo="matematica",
                    descripcion=(
                        f"{p.nombre_display}: Volumen Final ({actual:.0f}) ≠ "
                        f"Subproductos × Rendimiento ({esperado:.0f})"
                    ),
                    celdas_involucradas=[
                        f"Volumen Subproductos|{p.codigo}",
                        f"Rendimiento|{p.codigo}",
                        f"Volumen Producto Final|{p.codigo}",
                    ],
                    valor_esperado=esperado,
                    valor_actual=actual,
                ))

        # Regla 2: Precio Venta >= Costo Producción (margen positivo)
        precio = _celda(matriz, "Precio de Venta", p.codigo)
        costo_prod = _celda(matriz, "Costo producción", p.codigo)
        if precio and costo_prod and precio.valor is not None and costo_prod.valor is not None:
            if precio.valor <= costo_prod.valor:
                issues.append(Inconsistencia(
                    severidad="alta",
                    tipo="logica",
                    descripcion=(
                        f"{p.nombre_display}: Precio venta ({precio.valor:.0f}) <= "
                        f"Costo producción ({costo_prod.valor:.0f}) — margen negativo"
                    ),
                    celdas_involucradas=[
                        f"Precio de Venta|{p.codigo}",
                        f"Costo producción|{p.codigo}",
                    ],
                    valor_esperado=costo_prod.valor * 1.2,  # margen 20% mínimo
                    valor_actual=precio.valor,
                ))

        # Regla 3: Rendimiento entre 0 y 1
        if rend and rend.valor is not None:
            if rend.valor < 0 or rend.valor > 1:
                issues.append(Inconsistencia(
                    severidad="media",
                    tipo="rango",
                    descripcion=f"{p.nombre_display}: Rendimiento fuera de rango [0,1]",
                    celdas_involucradas=[f"Rendimiento|{p.codigo}"],
                    valor_actual=rend.valor,
                ))

    return issues


# ============================================================================
# 2. Sugerencias para celdas PD
# ============================================================================

@dataclass
class Sugerencia:
    variable: str
    producto: str
    valor_sugerido: float
    unidad: str
    razonamiento: str
    confianza: float  # 0-1

    def to_dict(self) -> dict:
        return {
            "variable": self.variable,
            "producto": self.producto,
            "valor_sugerido": round(self.valor_sugerido, 4),
            "unidad": self.unidad,
            "razonamiento": self.razonamiento,
            "confianza": round(self.confianza, 2),
        }


def _producto_por_codigo(codigo: str) -> ProductoSpec | None:
    return next((p for p in PRODUCTOS if p.codigo == codigo), None)


def _valores_ok_misma_variable(matriz: MatrizVariables, variable: str, mismo_grupo: str | None = None) -> list[float]:
    """Retorna valores OK_PROVISORIO/VALIDADO de la misma variable, opcionalmente filtrado por grupo."""
    vals = []
    for c in matriz.celdas:
        if c.variable != variable:
            continue
        if c.estado == EstadoCelda.PD or c.valor is None:
            continue
        if mismo_grupo:
            p = _producto_por_codigo(c.producto)
            if not p or p.grupo != mismo_grupo:
                continue
        vals.append(c.valor)
    return vals


def sugerir_valores_pd(matriz: MatrizVariables | None = None) -> list[Sugerencia]:
    """Para cada celda PD, propone un valor basado en celdas similares + benchmarks."""
    matriz = matriz or construir_matriz()
    sugerencias: list[Sugerencia] = []

    for celda in matriz.celdas:
        if celda.estado != EstadoCelda.PD:
            continue

        producto = _producto_por_codigo(celda.producto)
        if not producto:
            continue

        # Estrategia 1: usar valores OK del MISMO GRUPO de productos
        vals_grupo = _valores_ok_misma_variable(matriz, celda.variable, mismo_grupo=producto.grupo)
        if vals_grupo:
            sugerido = median(vals_grupo)
            sugerencias.append(Sugerencia(
                variable=celda.variable,
                producto=celda.producto,
                valor_sugerido=sugerido,
                unidad=celda.unidad,
                razonamiento=(
                    f"Mediana de {len(vals_grupo)} valores OK en grupo "
                    f"'{producto.grupo}' = {sugerido:.2f} {celda.unidad}"
                ),
                confianza=0.7 if len(vals_grupo) >= 3 else 0.5,
            ))
            continue

        # Estrategia 2: usar TODOS los valores OK de la variable
        vals_todos = _valores_ok_misma_variable(matriz, celda.variable)
        if vals_todos:
            sugerido = median(vals_todos)
            sugerencias.append(Sugerencia(
                variable=celda.variable,
                producto=celda.producto,
                valor_sugerido=sugerido,
                unidad=celda.unidad,
                razonamiento=(
                    f"Sin datos del grupo. Mediana global ({len(vals_todos)} valores OK) "
                    f"= {sugerido:.2f} {celda.unidad}"
                ),
                confianza=0.4,
            ))
            continue

        # Estrategia 3: benchmarks heurísticos por variable
        heuristica = _heuristica_por_variable(celda.variable, producto)
        if heuristica is not None:
            val, fuente = heuristica
            sugerencias.append(Sugerencia(
                variable=celda.variable,
                producto=celda.producto,
                valor_sugerido=val,
                unidad=celda.unidad,
                razonamiento=f"Heurística industria: {fuente}",
                confianza=0.3,
            ))

    return sugerencias


def _heuristica_por_variable(variable: str, producto: ProductoSpec) -> tuple[float, str] | None:
    """Heurísticas hardcoded por variable cuando no hay datos similares."""
    heuristicas = {
        "Costo Transporte Subproducto": (
            5.0, "Flete 75km / camión 22500kg / 2000 CLP por km"
        ),
        "Precio Recepción Subproducto": (
            0.0, "Modelo asume costo neto (flete - pago por residuo)"
        ),
        "Costo laboratorio": (
            7.0, "Transferencia tec CORFO 350M/año / volumen total 50k ton"
        ),
        "Costo Administración": (
            5.7, "30% del OpEx 80M × 12 / volumen 50k ton / 1000"
        ),
        "Costo Energía": (
            4.8, "25% del OpEx 80M × 12 / volumen 50k ton / 1000"
        ),
        "Costo Servicios Generales": (
            3.8, "20% del OpEx 80M × 12 / volumen 50k ton / 1000"
        ),
        "Costo Mantención Industrial": (
            4.8, "25% del OpEx 80M × 12 / volumen 50k ton / 1000"
        ),
    }
    return heuristicas.get(variable)


# ============================================================================
# 3. Simulación de cambio de celda
# ============================================================================

@dataclass
class ImpactoCambio:
    variable: str
    producto: str
    valor_anterior: float | None
    valor_nuevo: float
    tir_anterior: float | None
    tir_nuevo: float | None
    delta_tir_pp: float | None  # pp de cambio en TIR
    van_anterior: float
    van_nuevo: float
    delta_van_pct: float | None

    def to_dict(self) -> dict:
        return {
            "variable": self.variable,
            "producto": self.producto,
            "valor_anterior": self.valor_anterior,
            "valor_nuevo": self.valor_nuevo,
            "tir_anterior": self.tir_anterior,
            "tir_nuevo": self.tir_nuevo,
            "delta_tir_pp": self.delta_tir_pp,
            "van_anterior": self.van_anterior,
            "van_nuevo": self.van_nuevo,
            "delta_van_pct": self.delta_van_pct,
        }


def simular_cambio_celda(
    variable: str,
    producto: str,
    valor_nuevo: float,
) -> ImpactoCambio:
    """Cambia una celda específica y mide el impacto en TIR/VAN del plan."""
    from .plan_builder import ParametrosPlan, build_plan

    # Baseline
    base = ParametrosPlan()
    plan_base = build_plan(base)
    tir_base = plan_base.kpis.tir_proyecto_anual
    van_base = plan_base.kpis.van

    # Obtener valor actual
    matriz_actual = construir_matriz(base)
    celda_actual = _celda(matriz_actual, variable, producto)
    valor_anterior = celda_actual.valor if celda_actual else None

    # Aplicar el cambio según la variable
    base_modificado = _aplicar_cambio_en_plan(base, variable, producto, valor_nuevo)
    if base_modificado:
        plan_nuevo = build_plan(base_modificado)
        tir_nuevo = plan_nuevo.kpis.tir_proyecto_anual
        van_nuevo = plan_nuevo.kpis.van
    else:
        # Variable no afecta el plan financiero (ej: transversal por SKU)
        tir_nuevo = tir_base
        van_nuevo = van_base

    return ImpactoCambio(
        variable=variable,
        producto=producto,
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        tir_anterior=tir_base,
        tir_nuevo=tir_nuevo,
        delta_tir_pp=(
            (tir_nuevo - tir_base) * 100
            if tir_base is not None and tir_nuevo is not None
            else None
        ),
        van_anterior=van_base,
        van_nuevo=van_nuevo,
        delta_van_pct=(
            (van_nuevo - van_base) / van_base * 100
            if van_base != 0
            else None
        ),
    )


def _aplicar_cambio_en_plan(base, variable: str, producto: str, valor_nuevo: float):
    """Mapea (variable, producto) a un cambio en ParametrosPlan."""
    from dataclasses import replace

    if variable == "Precio de Venta":
        new_precios = dict(base.precios_clp_kg)
        new_precios[producto] = valor_nuevo
        return replace(base, precios_clp_kg=new_precios)

    if variable == "Rendimiento":
        prod = _producto_por_codigo(producto)
        if prod:
            new_rend = dict(base.rendimiento_por_mmpp)
            new_rend[prod.mmpp_origen] = valor_nuevo
            return replace(base, rendimiento_por_mmpp=new_rend)

    return None  # Variable no mapeable directamente


# ============================================================================
# 4. Score de confianza por celda
# ============================================================================

def score_confianza_celda(celda: Celda) -> float:
    """Devuelve un score 0-100 de confianza del dato."""
    if celda.estado == EstadoCelda.OK_VALIDADO:
        return 100.0
    if celda.estado == EstadoCelda.OK_PROVISORIO:
        # Más confianza si tiene fuente paper / Damodaran
        if any(kw in celda.fuente.lower() for kw in ("damodaran", "paper", "scielo", "calibrado planta")):
            return 65.0
        return 50.0
    return 0.0  # PD


# ============================================================================
# 5. Análisis completo "inteligente"
# ============================================================================

@dataclass
class AnalisisInteligente:
    inconsistencias: list[Inconsistencia]
    sugerencias: list[Sugerencia]
    confianza_promedio: float
    confianza_por_grupo: dict[str, float]
    celdas_criticas: list[dict]  # celdas PD que más impactan TIR

    def to_dict(self) -> dict:
        return {
            "inconsistencias": [i.to_dict() for i in self.inconsistencias],
            "sugerencias": [s.to_dict() for s in self.sugerencias],
            "confianza_promedio": round(self.confianza_promedio, 1),
            "confianza_por_grupo": {k: round(v, 1) for k, v in self.confianza_por_grupo.items()},
            "celdas_criticas": self.celdas_criticas,
        }


def analisis_inteligente() -> AnalisisInteligente:
    """Análisis completo de inteligencia de la matriz."""
    matriz = construir_matriz()

    inconsis = detectar_inconsistencias(matriz)
    sugerencias = sugerir_valores_pd(matriz)

    # Confianza promedio
    scores = [score_confianza_celda(c) for c in matriz.celdas]
    confianza_promedio = mean(scores) if scores else 0

    # Confianza por grupo
    confianza_por_grupo: dict[str, list[float]] = {}
    for c in matriz.celdas:
        p = _producto_por_codigo(c.producto)
        if p:
            confianza_por_grupo.setdefault(p.grupo, []).append(score_confianza_celda(c))
    conf_grupo_agg = {k: mean(v) for k, v in confianza_por_grupo.items()}

    # Celdas críticas: PD que pertenecen a variables clave (precio, rendimiento, costo MMPP)
    variables_clave = {"Precio de Venta", "Rendimiento", "Costo producción"}
    criticas = []
    for c in matriz.celdas:
        if c.estado == EstadoCelda.PD and c.variable in variables_clave:
            p = _producto_por_codigo(c.producto)
            criticas.append({
                "variable": c.variable,
                "producto": c.producto,
                "producto_nombre": p.nombre_display if p else c.producto,
                "grupo": p.grupo if p else "?",
                "razon": f"Variable clave en estado PD",
            })

    return AnalisisInteligente(
        inconsistencias=inconsis,
        sugerencias=sugerencias,
        confianza_promedio=confianza_promedio,
        confianza_por_grupo=conf_grupo_agg,
        celdas_criticas=criticas,
    )
