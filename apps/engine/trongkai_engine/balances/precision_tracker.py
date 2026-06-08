"""Precision Tracker: mide que tan EXACTO es el modelo hoy.

Responde la pregunta recurrente del usuario:
"necesito llegar a un parametro exacto o casi exacto"

Cada input del modelo tiene:
- nivel de validacion (PD / OK_PROVISORIO / OK_VALIDADO)
- peso de impacto en el costo/resultado final (0-1)

Exactitud global = suma(nivel_score * peso) / suma(peso)

Lista accionable: qué validar primero para subir mas la exactitud
(ordenado por impacto * gap de validacion).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Literal

NivelStr = Literal["PD", "OK_PROVISORIO", "OK_VALIDADO"]

# Score de exactitud por nivel
NIVEL_SCORE = {
    "PD": 0.20,
    "OK_PROVISORIO": 0.65,
    "OK_VALIDADO": 1.00,
}


@dataclass
class InputCritico:
    """Un input del modelo con su impacto en el resultado final."""
    id: str
    nombre: str
    categoria: str             # equipos, parametros, etapas, mmpp, comercial
    nivel: NivelStr
    peso_impacto: float        # 0-1, cuanto afecta el costo/resultado final
    valor_actual: str = ""     # valor que tiene hoy
    como_validar: str = ""     # accion concreta para validarlo
    fuente_sugerida: str = ""  # de donde sacar el dato real

    @property
    def exactitud_actual(self) -> float:
        return NIVEL_SCORE.get(self.nivel, 0.0)

    @property
    def gap(self) -> float:
        """Cuanto falta para exactitud total (1.0 - actual)."""
        return 1.0 - self.exactitud_actual

    @property
    def prioridad(self) -> float:
        """Impacto x gap = cuanto subiria la exactitud global si lo validas."""
        return self.peso_impacto * self.gap

    def to_dict(self) -> dict:
        d = asdict(self)
        d["exactitud_actual"] = round(self.exactitud_actual, 3)
        d["gap"] = round(self.gap, 3)
        d["prioridad"] = round(self.prioridad, 4)
        return d


@dataclass
class PrecisionReport:
    exactitud_global_pct: float
    nivel_confianza: str           # "estimado" / "aproximado" / "casi exacto" / "exacto"
    total_inputs: int
    validados: int
    provisorios: int
    sin_validar: int
    por_categoria: dict
    top_para_validar: list[dict]   # ordenado por prioridad
    quick_wins_exactitud: list[dict]
    resumen: str

    def to_dict(self) -> dict:
        return {
            "exactitud_global_pct": round(self.exactitud_global_pct, 1),
            "nivel_confianza": self.nivel_confianza,
            "total_inputs": self.total_inputs,
            "validados": self.validados,
            "provisorios": self.provisorios,
            "sin_validar": self.sin_validar,
            "por_categoria": self.por_categoria,
            "top_para_validar": self.top_para_validar,
            "quick_wins_exactitud": self.quick_wins_exactitud,
            "resumen": self.resumen,
        }


def _inputs_desde_equipos() -> list[InputCritico]:
    """Lee fichas equipos y arma inputs con peso por relevancia al costo."""
    from .fichas_equipos import cargar_fichas

    # Equipos con mayor impacto en costo (arriendo, energia alta, bottleneck)
    PESO_EQUIPO = {
        "PEF_OPTICEPT_ODIN": 0.95,           # arriendo $18.5M/mes - el mayor costo
        "PRENSA_OELWERK_510": 0.85,          # bottleneck define throughput
        "SECADOR_IKE_WRH300": 0.70,          # alto consumo energetico
        "MOLINO_MARTILLOS_HARINERO": 0.50,
        "ENSACADORA_AUTOMATICA": 0.45,
        "BOMBA_VALISI_VSHH4": 0.40,
    }
    out = []
    for f in cargar_fichas():
        peso = PESO_EQUIPO.get(f.id, 0.25)
        falta_capex = f.modalidad == "CAPEX_propio" and f.capex_clp == 0
        falta_arriendo = f.modalidad == "OPEX_arriendo" and f.arriendo_clp_mes == 0
        como = "Cotizar con proveedor: capacidad, kW, CAPEX o arriendo, mantencion."
        if falta_capex:
            como = "Falta CAPEX - pedir cotizacion de compra al proveedor."
        elif falta_arriendo:
            como = "Falta valor arriendo mensual - confirmar contrato."
        out.append(InputCritico(
            id=f"equipo_{f.id}",
            nombre=f"Equipo: {f.nombre}",
            categoria="equipos",
            nivel=f.nivel_dato,
            peso_impacto=peso,
            valor_actual=f"{f.capacidad_kg_h:g} kg/h, {f.potencia_kw:g} kW" if f.capacidad_kg_h else "sin specs",
            como_validar=como,
            fuente_sugerida=f.proveedor or "proveedor por definir",
        ))
    return out


def _inputs_desde_parametros() -> list[InputCritico]:
    """Lee parametros planta y arma inputs criticos."""
    from .parametros_planta import cargar_parametros

    p = cargar_parametros()
    out = []

    out.append(InputCritico(
        id="param_calor_residual",
        nombre="Calor residual La Gloria (costo termico)",
        categoria="parametros",
        nivel=p.calor_residual.nivel_dato,
        peso_impacto=0.80,   # la deshidratacion es clave y el calor define su costo
        valor_actual=f"{p.calor_residual.costo_kwh_termico_clp:g} CLP/kWh",
        como_validar="Firmar contrato de servicio con La Gloria + medir kWh termicos entregados.",
        fuente_sugerida="La Gloria SA (contrato + medidor)",
    ))
    out.append(InputCritico(
        id="param_agua",
        nombre="Tarifas agua (Essbio + pozo)",
        categoria="parametros",
        nivel=p.agua.nivel_dato,
        peso_impacto=0.35,
        valor_actual=f"llave {p.agua.agua_llave_clp_m3:g}, industrial {p.agua.agua_industrial_clp_m3:g} CLP/m3",
        como_validar="Boleta Essbio real + instalar caudalimetro en Pozo 1.",
        fuente_sugerida="Essbio + caudalimetro Pozo 1",
    ))
    out.append(InputCritico(
        id="param_arriendos",
        nombre="Arriendos OPEX (PEF + Tricanter)",
        categoria="parametros",
        nivel=p.arriendos.nivel_dato,
        peso_impacto=0.90,   # el arriendo PEF es el costo #1
        valor_actual=f"PEF {p.arriendos.arriendo_pef_clp_mes/1e6:.1f}M CLP/mes",
        como_validar="Cotizacion final OptiCept + Tricanter (contrato firmado).",
        fuente_sugerida="OptiCept Sweden + proveedor Tricanter",
    ))
    # Sueldos: validados si hay seed, pero peso medio
    sueldos_validados = len(p.sueldos) > 0
    out.append(InputCritico(
        id="param_sueldos",
        nombre="Sueldos planta (planilla real)",
        categoria="parametros",
        nivel="OK_PROVISORIO" if sueldos_validados else "PD",
        peso_impacto=0.45,
        valor_actual=f"{len(p.sueldos)} cargos cargados",
        como_validar="Subir planilla remuneraciones real del equipo contratado.",
        fuente_sugerida="RRHH / Nubox",
    ))
    return out


def _inputs_desde_etapas() -> list[InputCritico]:
    """Lee etapas y arma inputs por nivel de calibracion."""
    from .etapas import etapas_seed

    PESO_ETAPA = {
        "E3_PEF": 0.85,
        "E6A_DESHIDRATACION_PRINCIPAL": 0.75,
        "E4A_PRENSADO_MECANICO": 0.70,
        "E5_LIQUIDOS_RESIDUALES": 0.40,
    }
    out = []
    for e in etapas_seed():
        peso = PESO_ETAPA.get(e.id, 0.25)
        if not e.datos_faltantes:
            continue   # ya completa
        out.append(InputCritico(
            id=f"etapa_{e.id}",
            nombre=f"Etapa: {e.nombre}",
            categoria="etapas",
            nivel=e.nivel_calibracion.value,
            peso_impacto=peso,
            valor_actual=f"{len(e.datos_faltantes)} datos pendientes",
            como_validar=e.datos_faltantes[0] if e.datos_faltantes else "",
            fuente_sugerida="Medicion en planta piloto",
        ))
    return out


def _inputs_desde_mmpp() -> list[InputCritico]:
    """Yield MSF por producto - clave para revenue."""
    from .etapas import productos_seed

    out = []
    for p in productos_seed():
        nivel = "OK_PROVISORIO" if p.rendimiento_msf_pct > 0 else "PD"
        out.append(InputCritico(
            id=f"mmpp_{p.codigo}",
            nombre=f"Yield MSF: {p.codigo} ({p.variante})",
            categoria="mmpp",
            nivel=nivel,
            peso_impacto=0.60 if p.rendimiento_msf_pct > 0 else 0.30,
            valor_actual=f"MSF {p.rendimiento_msf_pct*100:.0f}%" if p.rendimiento_msf_pct else "sin definir",
            como_validar="Medir rendimiento real en piloto (kg producto / kg MMPP).",
            fuente_sugerida="Pruebas A/B centrifuga BioBase",
        ))
    return out


def _inputs_comerciales() -> list[InputCritico]:
    """Precio venta - el driver #1 del revenue."""
    return [
        InputCritico(
            id="comercial_precio_venta",
            nombre="Precio venta validado por SKU",
            categoria="comercial",
            nivel="PD",
            peso_impacto=1.00,   # el precio define todo el revenue
            valor_actual="estimacion mercado (sin cotizacion firme)",
            como_validar="Conseguir cotizaciones/LOI firmes de clientes ancla por SKU.",
            fuente_sugerida="Iansa, Sugal, Agrozzi (cartas intencion)",
        ),
        InputCritico(
            id="comercial_premium_pef",
            nombre="Premium price que habilita PEF",
            categoria="comercial",
            nivel="PD",
            peso_impacto=0.55,
            valor_actual="10% estimado",
            como_validar="Validar disposicion a pagar premium por calidad PEF con cliente.",
            fuente_sugerida="Test mercado con cliente nutraceutico",
        ),
    ]


def computar_precision() -> PrecisionReport:
    """Computa la exactitud global del modelo + qué validar."""
    inputs: list[InputCritico] = []
    inputs.extend(_inputs_desde_equipos())
    inputs.extend(_inputs_desde_parametros())
    inputs.extend(_inputs_desde_etapas())
    inputs.extend(_inputs_desde_mmpp())
    inputs.extend(_inputs_comerciales())

    if not inputs:
        return PrecisionReport(0, "sin datos", 0, 0, 0, 0, {}, [], [], "Sin inputs.")

    # Exactitud global ponderada por impacto
    suma_peso = sum(i.peso_impacto for i in inputs)
    suma_exactitud = sum(i.exactitud_actual * i.peso_impacto for i in inputs)
    exactitud_global = (suma_exactitud / suma_peso * 100) if suma_peso > 0 else 0

    # Nivel de confianza textual
    if exactitud_global >= 90:
        nivel_confianza = "exacto"
    elif exactitud_global >= 75:
        nivel_confianza = "casi exacto"
    elif exactitud_global >= 55:
        nivel_confianza = "aproximado"
    else:
        nivel_confianza = "estimado"

    validados = sum(1 for i in inputs if i.nivel == "OK_VALIDADO")
    provisorios = sum(1 for i in inputs if i.nivel == "OK_PROVISORIO")
    sin_validar = sum(1 for i in inputs if i.nivel == "PD")

    # Por categoria
    por_cat: dict = {}
    for i in inputs:
        c = i.categoria
        if c not in por_cat:
            por_cat[c] = {"total": 0, "exactitud_suma": 0.0, "peso_suma": 0.0}
        por_cat[c]["total"] += 1
        por_cat[c]["exactitud_suma"] += i.exactitud_actual * i.peso_impacto
        por_cat[c]["peso_suma"] += i.peso_impacto
    for c in por_cat:
        ps = por_cat[c]["peso_suma"]
        por_cat[c]["exactitud_pct"] = round(
            (por_cat[c]["exactitud_suma"] / ps * 100) if ps > 0 else 0, 1)
        del por_cat[c]["exactitud_suma"]
        del por_cat[c]["peso_suma"]

    # Top para validar: ordenado por prioridad (impacto x gap)
    pendientes = [i for i in inputs if i.gap > 0]
    pendientes.sort(key=lambda i: -i.prioridad)
    top = [i.to_dict() for i in pendientes[:10]]

    # Quick wins: alto impacto + estan en PROVISORIO (faltan poco)
    quick = [i.to_dict() for i in pendientes
             if i.nivel == "OK_PROVISORIO" and i.peso_impacto >= 0.6][:5]

    # Resumen
    falta_pts = 100 - exactitud_global
    top_3_nombres = ", ".join(p["nombre"].split(":")[0] for p in top[:3])
    resumen = (
        f"El modelo es '{nivel_confianza}' ({exactitud_global:.0f}/100). "
        f"Faltan {falta_pts:.0f} puntos para exactitud total. "
        f"Lo de mayor impacto a validar: {top_3_nombres}."
    )

    return PrecisionReport(
        exactitud_global_pct=exactitud_global,
        nivel_confianza=nivel_confianza,
        total_inputs=len(inputs),
        validados=validados,
        provisorios=provisorios,
        sin_validar=sin_validar,
        por_categoria=por_cat,
        top_para_validar=top,
        quick_wins_exactitud=quick,
        resumen=resumen,
    )
