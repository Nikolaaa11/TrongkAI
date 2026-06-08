"""Capa de sintesis inteligente: consolida datos de TODOS los modulos
y genera insights, oportunidades, amenazas y plan de accion priorizado.

Esta capa NO genera nuevos datos sino que cruza los existentes:
- balances (energia, agua, RRHH, etapas)
- fichas equipos (completitud, validacion)
- parametros planta (sueldos, energia, agua, calor, flete, arriendos)
- simulacion temporal + revenue + escalas
- analisis PEF (justificacion economica)

Output: Insight cross-modular accionable.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

Severidad = Literal["critica", "alta", "media", "baja", "info"]
Tipo = Literal["oportunidad", "amenaza", "validacion", "recomendacion", "logro"]


@dataclass
class Insight:
    """Una observacion accionable cross-modular."""
    titulo: str
    tipo: Tipo
    severidad: Severidad
    descripcion: str
    impacto: str = ""             # impacto cuantitativo si aplica
    accion_sugerida: str = ""
    modulos_origen: list[str] = field(default_factory=list)
    link_ui: str = ""             # ruta UI relacionada
    score_prioridad: float = 0.0  # 0-100, mayor = mas urgente

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CompletitudSubsistema:
    nombre: str
    valor_pct: float
    detalle: str = ""
    link: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SintesisInteligente:
    score_global_inteligencia: float    # 0-100 ponderado de completitud + alarmas
    completitud_subsistemas: list[CompletitudSubsistema]
    insights: list[Insight]
    insights_criticos: int
    insights_altos: int
    oportunidades: int
    amenazas: int
    plan_accion_top_5: list[Insight]
    resumen_ejecutivo: str
    metricas_clave: dict
    proximos_pasos: list[str]

    def to_dict(self) -> dict:
        return {
            "score_global_inteligencia": round(self.score_global_inteligencia, 1),
            "completitud_subsistemas": [c.to_dict() for c in self.completitud_subsistemas],
            "insights": [i.to_dict() for i in self.insights],
            "insights_criticos": self.insights_criticos,
            "insights_altos": self.insights_altos,
            "oportunidades": self.oportunidades,
            "amenazas": self.amenazas,
            "plan_accion_top_5": [i.to_dict() for i in self.plan_accion_top_5],
            "resumen_ejecutivo": self.resumen_ejecutivo,
            "metricas_clave": self.metricas_clave,
            "proximos_pasos": self.proximos_pasos,
        }


# =========================================================================
# DETECTORES DE INSIGHTS POR DOMINIO
# =========================================================================
def _insights_equipos() -> list[Insight]:
    """Analiza fichas equipos: cuello botella, validacion, CAPEX."""
    from .fichas_equipos import cargar_fichas

    out: list[Insight] = []
    fichas = cargar_fichas()
    sin_validar = [f for f in fichas if f.nivel_dato == "PD"]
    en_linea = [f for f in fichas if f.capacidad_kg_h > 0]
    if not en_linea:
        return out
    bottleneck = min(en_linea, key=lambda f: f.capacidad_kg_h)

    # Oportunidad: ampliar bottleneck
    out.append(Insight(
        titulo=f"Cuello de botella: {bottleneck.nombre}",
        tipo="oportunidad",
        severidad="alta",
        descripcion=(
            f"{bottleneck.nombre} limita toda la planta a {bottleneck.capacidad_kg_h:g} kg/h. "
            "Equipos aguas arriba operan subutilizados."
        ),
        impacto=f"Ampliar este equipo libera todo el throughput aguas arriba (hasta el siguiente bottleneck).",
        accion_sugerida="Cotizar segunda prensa o prensa de mayor capacidad. Evaluar ROI vs throughput x2.",
        modulos_origen=["fichas_equipos", "simulacion_temporal"],
        link_ui="/planta",
        score_prioridad=85.0,
    ))

    # Validacion: equipos sin info
    if sin_validar:
        out.append(Insight(
            titulo=f"{len(sin_validar)} equipos sin validar (nivel PD)",
            tipo="validacion",
            severidad="media",
            descripcion=f"Estos equipos tienen datos placeholder: {', '.join(f.nombre[:30] for f in sin_validar[:3])}{'...' if len(sin_validar) > 3 else ''}",
            accion_sugerida="Alimentar fichas en /equipos con info real (proveedor, modelo, kW, CAPEX).",
            modulos_origen=["fichas_equipos"],
            link_ui="/equipos",
            score_prioridad=60.0,
        ))

    return out


def _insights_simulacion() -> list[Insight]:
    """Analiza simulacion + revenue + escalas: rentabilidad."""
    from .simulacion_revenue import comparar_escalas, simular_con_revenue

    out: list[Insight] = []
    try:
        s = simular_con_revenue(periodo="ano")
        escalas = comparar_escalas()
    except Exception:
        return out

    # Amenaza: piloto deficitario
    if s.margen_total_clp < 0:
        out.append(Insight(
            titulo="Piloto deficitario en operacion anual",
            tipo="amenaza",
            severidad="critica",
            descripcion=(
                f"Piloto produce {s.producto_total_kg/1000:.0f} t/ano por "
                f"${s.costo_total_clp/1e6:.0f}M pero solo factura "
                f"${s.revenue_total_clp/1e6:.0f}M. Margen: "
                f"${s.margen_total_clp/1e6:.0f}M ({s.margen_pct*100:.0f}%)."
            ),
            impacto=f"Sin escalar, perdida anual ${abs(s.margen_total_clp)/1e6:.0f}M CLP.",
            accion_sugerida=(
                "1) Ampliar cuello de botella (prensa) para subir throughput. "
                "2) Validar precio premium con clientes ancla. "
                "3) Planificar escalado x10 ASAP (rentable desde alli)."
            ),
            modulos_origen=["simulacion_temporal", "simulacion_revenue", "fichas_equipos"],
            link_ui="/escalas",
            score_prioridad=95.0,
        ))

    # Oportunidad: escala industrial
    x100 = next((e for e in escalas["escalas"] if e["escala"] == 100), None)
    if x100 and x100["margen_pct"] > 0.6:
        out.append(Insight(
            titulo=f"Escalado x100 alcanza margen {x100['margen_pct']*100:.0f}%",
            tipo="oportunidad",
            severidad="alta",
            descripcion=(
                f"A {x100['producto_t_ano']:,.0f} t/ano, costo unitario baja a "
                f"${x100['costo_unitario_clp_kg']:,.0f} CLP/kg. Margen ${x100['margen_clp']/1e6:.0f}M CLP/ano."
            ),
            impacto=f"Payback simple: {x100['payback_anos']:.1f} anos. CAPEX requerido: ${x100['capex_clp']/1e6:.0f}M CLP.",
            accion_sugerida=(
                "Levantar capital para industrial. Roadmap sugerido: "
                "piloto -> x10 (validacion mercado) -> x50/x100 (escala comercial)."
            ),
            modulos_origen=["simulacion_revenue", "comparar_escalas"],
            link_ui="/escalas",
            score_prioridad=80.0,
        ))

    return out


def _insights_pef() -> list[Insight]:
    """Analiza si el PEF se justifica."""
    from .pef_analisis import analizar_pef_vs_sin_pef

    out: list[Insight] = []
    try:
        a = analizar_pef_vs_sin_pef()
    except Exception:
        return out

    margen_con = a.supuestos.get("margen_con_clp_h", 0)
    margen_sin = a.supuestos.get("margen_sin_clp_h", 0)
    diff = margen_con - margen_sin

    if diff > 0:
        out.append(Insight(
            titulo="PEF se justifica economicamente",
            tipo="logro",
            severidad="info",
            descripcion=(
                f"Con PEF margen +${diff:,.0f} CLP/h vs sin PEF "
                f"(+${diff*16*300/1e6:.0f}M CLP/ano operando 16h/dia 300 dias)."
            ),
            impacto=f"Diferencia margen anual: +${diff*16*300/1e6:.0f}M CLP.",
            accion_sugerida="Confirmar contrato arriendo OptiCept ODIN y avanzar con la decision.",
            modulos_origen=["pef_analisis"],
            link_ui="/pef-analisis",
            score_prioridad=50.0,
        ))
    else:
        out.append(Insight(
            titulo="PEF NO se justifica con calor residual barato",
            tipo="amenaza",
            severidad="alta",
            descripcion=(
                "Con calor residual La Gloria a costo casi cero, el ahorro en secado por "
                "PEF no compensa su arriendo ($18.5M/mes)."
            ),
            impacto=f"Diferencia margen: ${diff:,.0f} CLP/h. PEF debe justificarse via uplift de yield + premium price.",
            accion_sugerida=(
                "Validar A/B con centrifuga BioBase: PEF vs sin PEF -> medir % uplift yield real. "
                "Si no se demuestra +5% yield + 10% premium, abandonar arriendo PEF."
            ),
            modulos_origen=["pef_analisis", "parametros_planta"],
            link_ui="/pef-analisis",
            score_prioridad=75.0,
        ))

    return out


def _insights_balances() -> list[Insight]:
    """Analiza los 4 balances integrales."""
    out: list[Insight] = []
    try:
        from .integrado import computar_balance_integrado
        b = computar_balance_integrado()
    except Exception:
        return out

    criticas = sum(1 for a in b.alarmas_consolidadas if a.get("severidad") == "critica")
    if criticas > 0:
        out.append(Insight(
            titulo=f"{criticas} alarmas criticas en balances",
            tipo="amenaza",
            severidad="critica",
            descripcion=f"Balances detectan {criticas} alarmas criticas que requieren accion inmediata.",
            accion_sugerida="Revisar dashboard de balances integrales y atender alarmas.",
            modulos_origen=["balance_integrado"],
            link_ui="/balance-integral",
            score_prioridad=90.0,
        ))

    if b.score_eficiencia_global >= 80:
        out.append(Insight(
            titulo=f"Score eficiencia global {b.score_eficiencia_global:.0f}/100",
            tipo="logro",
            severidad="info",
            descripcion="Los 4 balances operacionales estan en buen estado.",
            modulos_origen=["balance_integrado"],
            link_ui="/balance-integral",
            score_prioridad=20.0,
        ))

    return out


def _insights_parametros() -> list[Insight]:
    """Analiza completitud de parametros."""
    from .parametros_planta import cargar_parametros

    out: list[Insight] = []
    p = cargar_parametros()
    pendientes = p.to_dict().get("checklist_pendientes", [])

    if pendientes:
        out.append(Insight(
            titulo=f"{len(pendientes)} parametros pendientes de validar",
            tipo="validacion",
            severidad="media",
            descripcion="Algunos parametros estan en nivel PD y deben validarse con datos reales.",
            accion_sugerida="\n".join(f"• {p}" for p in pendientes),
            modulos_origen=["parametros_planta"],
            link_ui="/parametros",
            score_prioridad=55.0,
        ))

    return out


# =========================================================================
# COMPLETITUD POR SUBSISTEMA
# =========================================================================
def _completitud_subsistemas() -> list[CompletitudSubsistema]:
    """Calcula % de calibracion/validacion de cada subsistema."""
    out: list[CompletitudSubsistema] = []

    # Equipos
    try:
        from .fichas_equipos import resumen_completitud_fichas
        r = resumen_completitud_fichas()
        out.append(CompletitudSubsistema(
            nombre="Fichas Equipos",
            valor_pct=r["completitud_pct"],
            detalle=f"{r['por_nivel'].get('OK_VALIDADO', 0)}/{r['total_fichas']} validadas",
            link="/equipos",
        ))
    except Exception:
        pass

    # Etapas
    try:
        from .etapas import resumen_datos_faltantes
        r = resumen_datos_faltantes()
        out.append(CompletitudSubsistema(
            nombre="Etapas Proceso",
            valor_pct=r["completitud_promedio_pct"],
            detalle=f"{r['validadas']}/{r['total_etapas']} validadas",
            link="/balance-etapas",
        ))
    except Exception:
        pass

    # Parametros
    try:
        from .parametros_planta import cargar_parametros
        p = cargar_parametros()
        pendientes = p.to_dict().get("checklist_pendientes", [])
        # 4 bloques principales: calor, agua, arriendos, sueldos
        completos = 4 - len(pendientes)
        pct = (completos / 4) * 100
        out.append(CompletitudSubsistema(
            nombre="Parametros Variables",
            valor_pct=pct,
            detalle=f"{completos}/4 grupos validados",
            link="/parametros",
        ))
    except Exception:
        pass

    # Balances integrales (energia, agua, rrhh, etapas)
    try:
        from .integrado import computar_balance_integrado
        b = computar_balance_integrado()
        out.append(CompletitudSubsistema(
            nombre="Balances Operacionales",
            valor_pct=b.score_eficiencia_global,
            detalle="Energia + Agua + RRHH + Etapas",
            link="/balance-integral",
        ))
    except Exception:
        pass

    return out


# =========================================================================
# SINTESIS PRINCIPAL
# =========================================================================
def computar_sintesis() -> SintesisInteligente:
    """Genera la sintesis inteligente completa."""
    insights: list[Insight] = []
    insights.extend(_insights_equipos())
    insights.extend(_insights_simulacion())
    insights.extend(_insights_pef())
    insights.extend(_insights_balances())
    insights.extend(_insights_parametros())

    # Orden por prioridad
    insights.sort(key=lambda i: -i.score_prioridad)

    completitud = _completitud_subsistemas()
    score_global = (sum(c.valor_pct for c in completitud) / max(len(completitud), 1)) if completitud else 0.0

    # Penalizacion por alarmas criticas
    criticas = sum(1 for i in insights if i.severidad == "critica")
    altas = sum(1 for i in insights if i.severidad == "alta")
    score_global = max(0, score_global - criticas * 5 - altas * 2)

    # Metricas clave consolidadas
    metricas = {}
    try:
        from .simulacion_revenue import simular_con_revenue
        s = simular_con_revenue(periodo="ano")
        metricas["produccion_anual_t"] = round(s.producto_total_kg / 1000, 1)
        metricas["revenue_anual_clp"] = s.revenue_total_clp
        metricas["margen_anual_clp"] = s.margen_total_clp
        metricas["margen_pct"] = round(s.margen_pct, 4)
        metricas["capex_total_clp"] = s.capex_total_clp
        metricas["payback_anos"] = (
            s.payback_simple_anos if s.payback_simple_anos != float("inf") else None
        )
    except Exception:
        pass

    # Resumen ejecutivo auto-generado
    resumen = _generar_resumen(score_global, insights, metricas)

    # Proximos pasos accionables
    proximos = _generar_proximos_pasos(insights)

    return SintesisInteligente(
        score_global_inteligencia=score_global,
        completitud_subsistemas=completitud,
        insights=insights,
        insights_criticos=criticas,
        insights_altos=altas,
        oportunidades=sum(1 for i in insights if i.tipo == "oportunidad"),
        amenazas=sum(1 for i in insights if i.tipo == "amenaza"),
        plan_accion_top_5=insights[:5],
        resumen_ejecutivo=resumen,
        metricas_clave=metricas,
        proximos_pasos=proximos,
    )


def _generar_resumen(score: float, insights: list[Insight], metricas: dict) -> str:
    """Genera un resumen ejecutivo de 2-3 oraciones."""
    estado = ("excelente" if score >= 80 else
              "bueno" if score >= 60 else
              "en desarrollo" if score >= 40 else
              "incipiente")
    partes = [
        f"Estado plataforma: {estado} ({score:.0f}/100)."
    ]

    if metricas:
        prod = metricas.get("produccion_anual_t", 0)
        margen = metricas.get("margen_anual_clp", 0)
        if prod > 0:
            partes.append(
                f"Piloto produce {prod:.0f} t/año con margen "
                f"{'POSITIVO' if margen > 0 else 'NEGATIVO'} "
                f"(${abs(margen)/1e6:.0f}M CLP)."
            )

    criticas = [i for i in insights if i.severidad == "critica"]
    if criticas:
        partes.append(
            f"⚠️ {len(criticas)} alarmas criticas requieren accion inmediata: "
            f"'{criticas[0].titulo}'."
        )

    oportunidades = [i for i in insights if i.tipo == "oportunidad"]
    if oportunidades:
        partes.append(
            f"💡 {len(oportunidades)} oportunidades detectadas, "
            f"top: '{oportunidades[0].titulo}'."
        )

    return " ".join(partes)


def _generar_proximos_pasos(insights: list[Insight]) -> list[str]:
    """Lista accionable de proximos pasos (top 5 insights)."""
    return [
        f"{i.titulo} → {i.accion_sugerida.split('.')[0]}."
        for i in insights[:5]
        if i.accion_sugerida
    ]
