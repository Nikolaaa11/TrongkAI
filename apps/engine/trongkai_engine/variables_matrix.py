"""Matriz canónica del Excel original "Variables Ingredientes Plan 5 Años".

Replica la grilla 11 productos × 15 variables del Excel maestro de Trongkai,
manteniendo trazabilidad del estado por celda (PD / OK_PROVISORIO / OK_VALIDADO).

Cada celda tiene:
- valor (numérico o None si PD)
- estado (PD | OK_PROVISORIO | OK_VALIDADO)
- unidad
- fuente (de dónde viene el dato)
- supuesto_id (link al módulo de supuestos)

Esto es lo que el directorio espera ver y poder defender línea por línea.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .plan_builder import ParametrosPlan


class EstadoCelda(StrEnum):
    PD = "PD"                       # Por Definir — necesita dato del equipo
    OK_PROVISORIO = "OK_PROVISORIO" # Estimación con benchmark / paper
    OK_VALIDADO = "OK_VALIDADO"     # Dato real del equipo / cotización firme


# ============================================================================
# Productos (columnas de la matriz)
# ============================================================================

@dataclass(frozen=True)
class ProductoSpec:
    codigo: str
    nombre_display: str
    grupo: str  # "Base Harinas y Aceite" | "Productos Finales II" | "Productos PTEC"
    mmpp_origen: str  # ALPERUJO | TOMASA | POMASA | ORUJO_UVA | LEVADURA


PRODUCTOS: tuple[ProductoSpec, ...] = (
    # ----- Base Harinas y Aceite -----
    ProductoSpec("HARINA_ALPERUJO",  "H. Alperujo",   "Base Harinas y Aceite", "ALPERUJO"),
    ProductoSpec("ACEITE_ALPERUJO",  "Ac. Alperujo",  "Base Harinas y Aceite", "ALPERUJO"),
    ProductoSpec("HARINA_ORUJO",     "H. Orujo",      "Base Harinas y Aceite", "ORUJO_UVA"),
    ProductoSpec("HARINA_TOMASA",    "H. Tomasa",     "Base Harinas y Aceite", "TOMASA"),
    ProductoSpec("HARINA_POMASA",    "H. Pomasa",     "Base Harinas y Aceite", "POMASA"),
    # ----- Productos Finales II -----
    ProductoSpec("PECTINA",          "Pectina*",      "Productos Finales II",  "POMASA"),
    ProductoSpec("LICOPENO",         "Licopeno*",     "Productos Finales II",  "TOMASA"),
    # ----- Productos PTEC -----
    ProductoSpec("PROTEINA_UNICEL",  "Proteína Unicel","Productos PTEC",       "LEVADURA"),
    ProductoSpec("ANTIOXIDANTE",     "Antioxidante",  "Productos PTEC",        "ALPERUJO"),
    ProductoSpec("AGLOMERANTE",      "Aglomerante",   "Productos PTEC",        "ORUJO_UVA"),
    ProductoSpec("UMAMI",            "Umami",         "Productos PTEC",        "LEVADURA"),
)


# ============================================================================
# Variables (filas de la matriz)
# ============================================================================

VARIABLES = (
    "Volumen Subproductos",
    "Costo Transporte Subproducto",
    "Precio Recepción Subproducto",
    "Rendimiento",
    "Volumen Producto Final",
    "Precio de Venta",
    "Costo producción",
    "Material de envase",
    "Costo Almacenamiento",
    "Costo Transporte Almac. y Clientes",
    "Costo laboratorio",
    "Costo Administración",
    "Costo Energía",
    "Costo Servicios Generales",
    "Costo Mantención Industrial",
)


# ============================================================================
# Estructuras de la matriz
# ============================================================================

@dataclass
class Celda:
    variable: str
    producto: str  # código
    valor: float | None
    unidad: str
    estado: EstadoCelda
    fuente: str
    nota: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "variable": self.variable,
            "producto": self.producto,
            "valor": self.valor,
            "unidad": self.unidad,
            "estado": self.estado.value,
            "fuente": self.fuente,
            "nota": self.nota,
        }


@dataclass
class MatrizVariables:
    celdas: list[Celda] = field(default_factory=list)
    productos: list[ProductoSpec] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        # Stats
        total = len(self.celdas)
        pd = sum(1 for c in self.celdas if c.estado == EstadoCelda.PD)
        ok_prov = sum(1 for c in self.celdas if c.estado == EstadoCelda.OK_PROVISORIO)
        ok_val = sum(1 for c in self.celdas if c.estado == EstadoCelda.OK_VALIDADO)
        return {
            "productos": [
                {
                    "codigo": p.codigo,
                    "nombre": p.nombre_display,
                    "grupo": p.grupo,
                    "mmpp_origen": p.mmpp_origen,
                }
                for p in self.productos
            ],
            "variables": list(self.variables),
            "celdas": [c.to_dict() for c in self.celdas],
            "stats": {
                "total": total,
                "PD": pd,
                "OK_PROVISORIO": ok_prov,
                "OK_VALIDADO": ok_val,
                "pct_cubierto": round((ok_prov + ok_val) / total * 100, 1) if total > 0 else 0,
                "pct_validado": round(ok_val / total * 100, 1) if total > 0 else 0,
            },
        }


# ============================================================================
# Builder
# ============================================================================

def _peso_volumen_maduro(codigo: str) -> float:
    """Peso del SKU en el mix de productos final."""
    pesos = {
        "HARINA_ALPERUJO": 0.22, "ACEITE_ALPERUJO": 0.04, "HARINA_ORUJO": 0.16,
        "HARINA_TOMASA": 0.15, "HARINA_POMASA": 0.12, "PECTINA": 0.02,
        "LICOPENO": 0.0005, "PROTEINA_UNICEL": 0.18, "ANTIOXIDANTE": 0.04,
        "AGLOMERANTE": 0.04, "UMAMI": 0.01,
    }
    return pesos.get(codigo, 0.0)


def construir_matriz(base: ParametrosPlan | None = None) -> MatrizVariables:
    """Construye la matriz completa 11 productos × 15 variables.

    Cada celda combina:
    - El valor del plan_builder (si existe)
    - El estado de validación (PD / OK_PROVISORIO / OK_VALIDADO)
    - La fuente del dato
    """
    base = base or ParametrosPlan()
    celdas: list[Celda] = []

    # ===== Volumen MMPP por producto (rendimiento × peso × volumen total) =====
    for p in PRODUCTOS:
        peso = _peso_volumen_maduro(p.codigo)
        vol_mmpp = base.volumen_total_ton_ano * peso  # aproximado
        # Estado: OK_PROVISORIO porque está calculado desde supuesto de mix
        celdas.append(Celda(
            variable="Volumen Subproductos",
            producto=p.codigo,
            valor=vol_mmpp,
            unidad="ton/año",
            estado=EstadoCelda.OK_PROVISORIO,
            fuente=f"Plan: peso mix maduro × volumen total ({base.volumen_total_ton_ano} ton/año)",
            nota="Calibrar con volumen real cuando llegue cotización MMPP",
        ))

    # ===== Costo Transporte Subproducto =====
    for p in PRODUCTOS:
        # Hoy mezclado dentro de costo_mmpp_clp_kg neto (30 CLP/kg)
        celdas.append(Celda(
            variable="Costo Transporte Subproducto",
            producto=p.codigo,
            valor=None,
            unidad="CLP/kg",
            estado=EstadoCelda.PD,
            fuente="No desglosado — incluido en costo_mmpp_clp_kg neto",
            nota="Pedir a Sergio: cotización flete por MMPP origen-planta",
        ))

    # ===== Precio Recepción Subproducto =====
    for p in PRODUCTOS:
        celdas.append(Celda(
            variable="Precio Recepción Subproducto",
            producto=p.codigo,
            valor=None,
            unidad="CLP/kg",
            estado=EstadoCelda.PD,
            fuente="No definido — modelado como costo neto",
            nota="Cotización firme con 3 proveedores",
        ))

    # ===== Rendimiento =====
    for p in PRODUCTOS:
        rendimiento = base.rendimiento_por_mmpp.get(p.mmpp_origen, 0.25)
        # Estado: OK_PROVISORIO para los base, PD para PTEC nuevos
        estado = (
            EstadoCelda.OK_PROVISORIO
            if p.grupo in ("Base Harinas y Aceite", "Productos Finales II")
            else EstadoCelda.PD
        )
        celdas.append(Celda(
            variable="Rendimiento",
            producto=p.codigo,
            valor=rendimiento,
            unidad="ton out/in",
            estado=estado,
            fuente="plan_builder.rendimiento_por_mmpp — calibrado planta industrial referencia",
            nota="Validar con muestras reales tomatera y olivar" if estado == EstadoCelda.OK_PROVISORIO else "PTEC: validar con piloto",
        ))

    # ===== Volumen Producto Final =====
    for p in PRODUCTOS:
        peso = _peso_volumen_maduro(p.codigo)
        vol_final = base.volumen_total_ton_ano * peso
        estado = (
            EstadoCelda.OK_PROVISORIO
            if p.grupo in ("Base Harinas y Aceite", "Productos Finales II")
            else EstadoCelda.PD
        )
        celdas.append(Celda(
            variable="Volumen Producto Final",
            producto=p.codigo,
            valor=vol_final,
            unidad="ton/año",
            estado=estado,
            fuente=f"Plan: peso mix maduro {peso * 100:.2f}% × volumen total",
            nota="",
        ))

    # ===== Precio de Venta =====
    for p in PRODUCTOS:
        precio = base.precios_clp_kg.get(p.codigo, 0)
        # Base + Productos Finales II = OK_PROVISORIO (calibrado a benchmarks)
        # PTEC = PD (productos nuevos sin precio firme)
        estado = (
            EstadoCelda.OK_PROVISORIO
            if p.grupo in ("Base Harinas y Aceite", "Productos Finales II")
            else EstadoCelda.PD
        )
        celdas.append(Celda(
            variable="Precio de Venta",
            producto=p.codigo,
            valor=precio,
            unidad="CLP/kg",
            estado=estado,
            fuente="plan_builder.precios_clp_kg — Damodaran + benchmarks mundiales × descuento nuevo entrante",
            nota="Pedir LOI firmada de cliente para mover a OK_VALIDADO",
        ))

    # ===== Costo Producción =====
    for p in PRODUCTOS:
        # Suma de costos por etapa = ~330 CLP/kg
        costo_prod = sum(base.costo_etapa_clp_kg.values())
        estado = (
            EstadoCelda.OK_PROVISORIO
            if p.grupo == "Base Harinas y Aceite"
            else EstadoCelda.PD
        )
        celdas.append(Celda(
            variable="Costo producción",
            producto=p.codigo,
            valor=costo_prod if estado == EstadoCelda.OK_PROVISORIO else None,
            unidad="CLP/kg",
            estado=estado,
            fuente="Suma costo_etapa_clp_kg (recepción + alimentación + homog + PEF + prensado + tricanter + extracción + secado + ensacado)",
            nota="Productos PTEC requieren proceso adicional (extracción solventes, fermentación) — cotizar separado",
        ))

    # ===== Material de envase =====
    for p in PRODUCTOS:
        # Heurística: 5% del precio de venta
        precio = base.precios_clp_kg.get(p.codigo, 0)
        celdas.append(Celda(
            variable="Material de envase",
            producto=p.codigo,
            valor=precio * 0.05 if precio > 0 else None,
            unidad="CLP/kg",
            estado=EstadoCelda.OK_PROVISORIO,
            fuente="Heurística 5% del precio venta (benchmark industria alimentaria)",
            nota="Validar con cotización proveedor envase",
        ))

    # ===== Costo Almacenamiento =====
    for p in PRODUCTOS:
        # Heurística: 8 CLP/kg para harinas, 25 para PTEC (refrigerado)
        if p.grupo == "Productos PTEC":
            valor = 25
        elif p.grupo == "Productos Finales II":
            valor = 15
        else:
            valor = 8
        celdas.append(Celda(
            variable="Costo Almacenamiento",
            producto=p.codigo,
            valor=valor,
            unidad="CLP/kg",
            estado=EstadoCelda.OK_PROVISORIO,
            fuente="Benchmark logística alimentaria Chile",
            nota="Validar con cotización bodega + rotación real",
        ))

    # ===== Costo Transporte Almac. y Clientes =====
    for p in PRODUCTOS:
        # Heurística: 12 CLP/kg promedio
        celdas.append(Celda(
            variable="Costo Transporte Almac. y Clientes",
            producto=p.codigo,
            valor=12,
            unidad="CLP/kg",
            estado=EstadoCelda.OK_PROVISORIO,
            fuente="Benchmark logística 75 km × 2000 CLP / 22500 kg",
            nota="Refinar por ruta cliente cuando se cierren contratos",
        ))

    # ===== Costo Laboratorio =====
    for p in PRODUCTOS:
        # Constante ~CLP 350M/año = 7 CLP/kg con 50k ton
        celdas.append(Celda(
            variable="Costo laboratorio",
            producto=p.codigo,
            valor=7,
            unidad="CLP/kg",
            estado=EstadoCelda.PD,
            fuente="Transferencia tec CORFO 350M/año / volumen total",
            nota="Pedir presupuesto QA específico por SKU",
        ))

    # ===== Costos transversales (Administración, Energía, Servicios Generales, Mantención) =====
    # Estos están en opex_mensual_clp = 80M agregado
    opex_anual = base.opex_mensual_clp * 12
    # Distribución aproximada:
    # Administración: 30% = 28.8M/mes
    # Energía: 25% = 24M/mes
    # Servicios generales: 20% = 19.2M/mes
    # Mantención: 25% = 24M/mes
    desglose_opex = {
        "Costo Administración": (opex_anual * 0.30) / base.volumen_total_ton_ano / 1000,  # CLP/kg
        "Costo Energía": (opex_anual * 0.25) / base.volumen_total_ton_ano / 1000,
        "Costo Servicios Generales": (opex_anual * 0.20) / base.volumen_total_ton_ano / 1000,
        "Costo Mantención Industrial": (opex_anual * 0.25) / base.volumen_total_ton_ano / 1000,
    }

    for variable_nombre, valor in desglose_opex.items():
        for p in PRODUCTOS:
            celdas.append(Celda(
                variable=variable_nombre,
                producto=p.codigo,
                valor=valor,
                unidad="CLP/kg",
                estado=EstadoCelda.PD,
                fuente=f"Aproximado desde opex_mensual_clp {base.opex_mensual_clp / 1e6:.0f}M × 12 / volumen",
                nota="Pedir a Contadora: desglose real OpEx mensual",
            ))

    return MatrizVariables(
        celdas=celdas,
        productos=list(PRODUCTOS),
        variables=list(VARIABLES),
    )


def stats_resumen(matriz: MatrizVariables) -> dict[str, Any]:
    """Stats agregados de la matriz."""
    d = matriz.to_dict()
    return d["stats"]
