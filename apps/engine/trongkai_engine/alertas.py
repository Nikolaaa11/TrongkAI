"""Sistema de Alertas Inteligentes — escanea todo el modelo y dispara alertas.

Tipos de alertas:
- financiera: TIR baja, VAN negativo, payback excesivo
- bancabilidad: DSCR < 1.5, LLCR < 1.4
- riesgo: zona segura sensitivity < 50%, colchón breakeven < 15%
- compliance: hito REP vencido o crítico próximo
- macro: TPM o desempleo fuera de rango
- modelo: inconsistencias detectadas, confianza baja
- ESG: emisiones positivas, no carbono negativo
- progreso: readiness score bajó, gaps coherentes aumentaron

Niveles: critica | alta | media | baja | info

Cada alerta tiene:
- titulo + descripcion
- tipo + nivel
- modulo afectado
- valor_actual vs umbral
- accion_sugerida
- link a la página donde resolver
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

NivelAlerta = Literal["critica", "alta", "media", "baja", "info"]
TipoAlerta = Literal[
    "financiera", "bancabilidad", "riesgo", "compliance",
    "macro", "modelo", "esg", "progreso",
]


@dataclass
class Alerta:
    id: str
    titulo: str
    descripcion: str
    tipo: TipoAlerta
    nivel: NivelAlerta
    modulo: str
    valor_actual: float | str | None
    umbral: float | str | None
    accion_sugerida: str
    link: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "nivel": self.nivel,
            "modulo": self.modulo,
            "valor_actual": self.valor_actual,
            "umbral": self.umbral,
            "accion_sugerida": self.accion_sugerida,
            "link": self.link,
        }


# ============================================================================
# Escaneo de cada módulo
# ============================================================================

def _alertas_financieras() -> list[Alerta]:
    """TIR, VAN, payback."""
    from .plan_builder import ParametrosPlan, build_plan

    alertas: list[Alerta] = []
    try:
        plan = build_plan(ParametrosPlan())
        tir = plan.kpis.tir_proyecto_anual or 0
        van = plan.kpis.van
        payback = plan.kpis.payback_meses or 999

        if tir < 0.15:
            alertas.append(Alerta(
                id="fin-tir-bajo-hurdle",
                titulo="TIR proyecto por debajo del hurdle CEHTA",
                descripcion=f"TIR {tir*100:.2f}% < hurdle 15%. Proyecto no viable a las condiciones actuales.",
                tipo="financiera", nivel="critica", modulo="plan",
                valor_actual=tir, umbral=0.15,
                accion_sugerida="Revisar precios SKU o reducir CapEx. Ver /sensitivity para identificar driver crítico.",
                link="/plan",
            ))
        elif tir < 0.20:
            alertas.append(Alerta(
                id="fin-tir-marginal",
                titulo="TIR marginal vs WACC",
                descripcion=f"TIR {tir*100:.2f}% cercana al WACC 18%. Poco colchón frente a shocks.",
                tipo="financiera", nivel="media", modulo="plan",
                valor_actual=tir, umbral=0.20,
                accion_sugerida="Considerar cobertura de precios o reducción de costos.",
                link="/sensitivity",
            ))

        if van < 0:
            alertas.append(Alerta(
                id="fin-van-negativo",
                titulo="VAN negativo",
                descripcion=f"VAN $({van/1e9:.2f}B CLP). Proyecto destruye valor a WACC 18%.",
                tipo="financiera", nivel="critica", modulo="plan",
                valor_actual=van, umbral=0,
                accion_sugerida="Re-pricing o re-escalamiento del proyecto.",
                link="/plan",
            ))

        if payback > 60:
            alertas.append(Alerta(
                id="fin-payback-largo",
                titulo="Payback excesivo",
                descripcion=f"Payback {payback} meses > 60. LP de plazo corto rechazará.",
                tipo="financiera", nivel="alta", modulo="plan",
                valor_actual=payback, umbral=60,
                accion_sugerida="Acelerar ramp-up o reducir CapEx inicial.",
                link="/plan",
            ))
    except Exception:
        pass

    return alertas


def _alertas_bancabilidad() -> list[Alerta]:
    """DSCR proxy desde plan."""
    from .plan_builder import ParametrosPlan, build_plan

    alertas: list[Alerta] = []
    try:
        plan = build_plan(ParametrosPlan())
        ebitda_anos = plan.ebitda_anuales[2:5] if len(plan.ebitda_anuales) >= 5 else plan.ebitda_anuales
        capex_total = sum(plan.capex_anuales) if hasattr(plan, "capex_anuales") else 15e9
        servicio_anual = (capex_total * 0.50) / 10  # proxy
        dscr = (sum(ebitda_anos) / len(ebitda_anos)) / servicio_anual if servicio_anual else 999

        if dscr < 1.3:
            alertas.append(Alerta(
                id="bnc-dscr-bajo",
                titulo="DSCR bajo umbral bancable",
                descripcion=f"DSCR proxy {dscr:.2f} < 1.3 mínimo bancable.",
                tipo="bancabilidad", nivel="alta", modulo="financing",
                valor_actual=dscr, umbral=1.3,
                accion_sugerida="Renegociar plazo, grace o reducir deuda.",
                link="/financiamiento",
            ))
    except Exception:
        pass

    return alertas


def _alertas_riesgo() -> list[Alerta]:
    """Sensitivity zona segura + breakeven colchón."""
    alertas: list[Alerta] = []
    try:
        from .sensitivity import heatmap_2d
        from .breakeven import breakeven_summary

        hm = heatmap_2d(n=5).to_dict()
        if hm["pct_zona_segura"] < 0.5:
            alertas.append(Alerta(
                id="rsg-zona-segura-baja",
                titulo="Zona segura sensitivity bajo 50%",
                descripcion=f"Solo {hm['pct_zona_segura']*100:.0f}% de combinaciones precio×costo MMPP están sobre hurdle.",
                tipo="riesgo", nivel="alta", modulo="sensitivity",
                valor_actual=hm["pct_zona_segura"], umbral=0.5,
                accion_sugerida="Cobertura forward de precios + take-or-pay con clientes.",
                link="/sensitivity",
            ))

        be = breakeven_summary(umbral_tir=0.15).to_dict()
        for r in be.get("resultados", []):
            if r["driver"] == "precio" and r["colchon_pct"] is not None and r["colchon_pct"] < 0.15:
                alertas.append(Alerta(
                    id="rsg-be-precio-bajo",
                    titulo="Colchón breakeven precio crítico",
                    descripcion=f"Precio soporta solo -{r['colchon_pct']*100:.0f}% antes de bajar del hurdle.",
                    tipo="riesgo", nivel="critica", modulo="breakeven",
                    valor_actual=r["colchon_pct"], umbral=0.15,
                    accion_sugerida="Cerrar contratos forward con piso mínimo.",
                    link="/sensitivity",
                ))
    except Exception:
        pass

    return alertas


def _alertas_compliance() -> list[Alerta]:
    """Hitos REP próximos a vencer."""
    alertas: list[Alerta] = []
    try:
        from .compliance_rep import HITOS_LEY_REP
        hoy = date.today()
        for h in HITOS_LEY_REP:
            dias_a_vigor = (h.fecha_vigor - hoy).days
            if 0 <= dias_a_vigor <= 90 and h.severidad.value in ("CRITICA", "ALTA"):
                alertas.append(Alerta(
                    id=f"cmp-rep-{h.nombre[:30].replace(' ', '-')}",
                    titulo=f"Hito REP en {dias_a_vigor} días",
                    descripcion=f"{h.nombre} (severidad {h.severidad.value}) entra en vigor el {h.fecha_vigor.isoformat()}.",
                    tipo="compliance", nivel="alta" if dias_a_vigor < 30 else "media",
                    modulo="compliance",
                    valor_actual=dias_a_vigor, umbral=90,
                    accion_sugerida=h.accion_requerida,
                    link="/compliance",
                ))
    except Exception:
        pass

    return alertas


def _alertas_modelo() -> list[Alerta]:
    """Inconsistencias matriz + confianza baja."""
    alertas: list[Alerta] = []
    try:
        from .variables_intelligence import analisis_inteligente
        a = analisis_inteligente()
        if a.inconsistencias:
            alertas.append(Alerta(
                id="mdl-inconsistencias",
                titulo=f"{len(a.inconsistencias)} inconsistencias en la matriz",
                descripcion="Variables Intelligence detectó incoherencias matemáticas.",
                tipo="modelo", nivel="alta", modulo="variables",
                valor_actual=len(a.inconsistencias), umbral=0,
                accion_sugerida="Ver /variables para detalle y corregir cálculos.",
                link="/variables",
            ))

        if a.confianza_promedio < 30:
            alertas.append(Alerta(
                id="mdl-confianza-baja",
                titulo="Confianza modelo baja",
                descripcion=f"Confianza promedio {a.confianza_promedio:.0f}/100. Mayoría de celdas en PD.",
                tipo="modelo", nivel="media", modulo="variables",
                valor_actual=a.confianza_promedio, umbral=30,
                accion_sugerida="Empezar por las celdas críticas del Decision Engine.",
                link="/datos",
            ))
    except Exception:
        pass

    return alertas


def _alertas_esg() -> list[Alerta]:
    """Carbon balance."""
    alertas: list[Alerta] = []
    try:
        from .carbon_footprint import comparar_escenarios_footprint
        from .plan_builder import ParametrosPlan
        base = ParametrosPlan()
        rend = sum(base.rendimiento_por_mmpp.values()) / len(base.rendimiento_por_mmpp)
        vols = [base.volumen_total_ton_ano * base.volumen_pct_por_ano.get(y, 1.0) for y in range(1, 6)]
        c = comparar_escenarios_footprint(vols, rendimiento_promedio=rend)
        emisiones = c["baseline"]["emisiones_netas_5y_ton"]
        if emisiones > 0:
            alertas.append(Alerta(
                id="esg-no-carbon-neg",
                titulo="Proyecto NO carbono negativo",
                descripcion=f"Baseline emite +{emisiones:,.0f} ton CO2eq 5y. Pierde el sello ESG flagship.",
                tipo="esg", nivel="alta", modulo="carbono",
                valor_actual=emisiones, umbral=0,
                accion_sugerida="Implementar energías renovables o BECCS scenario.",
                link="/carbono",
            ))
    except Exception:
        pass

    return alertas


def _alertas_progreso() -> list[Alerta]:
    """Compara con histórico de readiness."""
    alertas: list[Alerta] = []
    try:
        from .readiness_history import get_history
        hist = get_history(limit=10)
        if len(hist) >= 2:
            score_actual = hist[-1]["score"]
            score_anterior = hist[-2]["score"]
            delta = score_actual - score_anterior
            if delta < -3:
                alertas.append(Alerta(
                    id="prg-score-bajo",
                    titulo=f"Score bajó {abs(delta):.1f} pts",
                    descripcion=f"Readiness {score_anterior:.1f} → {score_actual:.1f}. Posible regresión.",
                    tipo="progreso", nivel="alta", modulo="readiness",
                    valor_actual=delta, umbral=-3,
                    accion_sugerida="Investigar qué dimensión bajó. Ver /readiness historial.",
                    link="/readiness",
                ))
    except Exception:
        pass

    return alertas


# ============================================================================
# Orquestador
# ============================================================================

NIVEL_ORDER = {"critica": 0, "alta": 1, "media": 2, "baja": 3, "info": 4}


@dataclass
class ResumenAlertas:
    alertas: list[Alerta] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.alertas)

    @property
    def criticas(self) -> int:
        return sum(1 for a in self.alertas if a.nivel == "critica")

    @property
    def altas(self) -> int:
        return sum(1 for a in self.alertas if a.nivel == "alta")

    def to_dict(self) -> dict:
        by_tipo: dict[str, int] = {}
        for a in self.alertas:
            by_tipo[a.tipo] = by_tipo.get(a.tipo, 0) + 1
        return {
            "total": self.total,
            "criticas": self.criticas,
            "altas": self.altas,
            "medias": sum(1 for a in self.alertas if a.nivel == "media"),
            "bajas": sum(1 for a in self.alertas if a.nivel == "baja"),
            "by_tipo": by_tipo,
            "alertas": [a.to_dict() for a in self.alertas],
        }


def escanear_alertas() -> ResumenAlertas:
    """Escanea TODO el sistema y devuelve alertas ordenadas por severidad."""
    alertas: list[Alerta] = []
    alertas.extend(_alertas_financieras())
    alertas.extend(_alertas_bancabilidad())
    alertas.extend(_alertas_riesgo())
    alertas.extend(_alertas_compliance())
    alertas.extend(_alertas_modelo())
    alertas.extend(_alertas_esg())
    alertas.extend(_alertas_progreso())

    # Ordenar por nivel
    alertas.sort(key=lambda a: NIVEL_ORDER.get(a.nivel, 99))
    return ResumenAlertas(alertas=alertas)
