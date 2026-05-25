"""Intelligence Graph — mapa de dependencias entre módulos del modelo.

Modela explícitamente cómo cada módulo de la plataforma impacta a los otros.
Útil para:
- Visualización tipo network graph en /coherencia
- Detectar cuándo un cambio en X obliga a revalidar Y
- Comunicar a stakeholders cómo se conecta el modelo

Nodos: módulos (plan, sensitivity, carbon, compliance, etc)
Edges: dependencias direccionadas (X impacta Y)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

TipoNodo = Literal["matriz", "calculo", "decisión", "input", "output"]
TipoEdge = Literal["alimenta", "valida", "deriva", "afecta"]


@dataclass
class Nodo:
    id: str
    label: str
    tipo: TipoNodo
    descripcion: str
    plataforma_url: str = ""


@dataclass
class Edge:
    desde: str       # nodo id
    hacia: str       # nodo id
    tipo: TipoEdge
    peso: float      # 0-1 fuerza de la dependencia
    descripcion: str = ""


# ============================================================================
# Definición del grafo
# ============================================================================

NODOS: tuple[Nodo, ...] = (
    # Inputs (datos del equipo)
    Nodo("equipo-input", "Equipo: datos", "input", "Datos del equipo (LOIs, cotizaciones, OpEx)"),
    Nodo("macro-bce", "Banco Central", "input", "USD/CLP, UF, IPC, TPM live"),
    Nodo("papers", "Papers científicos", "input", "27 papers peer-reviewed calibran benchmarks"),

    # Matrices base
    Nodo("matriz-variables", "Matriz Variables", "matriz",
         "165 celdas: 11 productos × 15 variables", "/variables"),
    Nodo("data-room", "Data Room", "matriz",
         "41 items DD", "/data-room"),
    Nodo("compliance", "Compliance REP", "matriz",
         "8 hitos Ley REP timeline", "/compliance"),

    # Cálculos derivados
    Nodo("plan-5y", "Plan 5 años", "calculo",
         "EERR mensual a 60 meses + KPIs", "/plan"),
    Nodo("sensitivity", "Sensitivity", "calculo",
         "Heatmap 2D + 3D + curvas + breakeven", "/sensitivity"),
    Nodo("monte-carlo", "Monte Carlo", "calculo",
         "10k sims integradas con clima", "/plan"),
    Nodo("carbon", "Carbon Footprint", "calculo",
         "LCA 3 escenarios + revenue créditos", "/carbono"),
    Nodo("financing", "Financiamiento", "calculo",
         "Deuda/Equity + DSCR + LLCR", "/financiamiento"),
    Nodo("valuation", "Valoración", "calculo",
         "EV/EBITDA 9.63× exit año 5"),

    # Capas inteligentes
    Nodo("variables-intel", "Variables Intelligence", "calculo",
         "Detecta inconsistencias + sugerencias"),
    Nodo("coherencia", "Coherencia Cross-Matriz", "calculo",
         "Gaps que aparecen en múltiples matrices", "/coherencia"),
    Nodo("readiness", "Investment Readiness", "calculo",
         "Score 0-100 con 10 dimensiones", "/readiness"),
    Nodo("decision", "Decision Engine", "decisión",
         "Top 5 acciones priorizadas", "/decisiones"),

    # Outputs
    Nodo("pdf-tearsheet", "PDF Tearsheet", "output",
         "3 páginas ejecutivas para LP"),
    Nodo("lp-pack", "LP Pack ZIP", "output",
         "Pack completo para roadshow", "/lp-pack"),
    Nodo("excel-master", "Excel Master", "output",
         "12 hojas con datos + macros VBA"),
)

EDGES: tuple[Edge, ...] = (
    # Inputs → matrices
    Edge("equipo-input", "matriz-variables", "alimenta", 1.0, "LOIs / cotizaciones cambian celdas de PD a OK_VALIDADO"),
    Edge("equipo-input", "data-room", "alimenta", 1.0, "Documentos del equipo cierran items DD"),
    Edge("macro-bce", "plan-5y", "alimenta", 0.3, "USD/CLP afecta conversión y benchmarks"),
    Edge("papers", "matriz-variables", "valida", 0.7, "Benchmarks calibran celdas OK_PROVISORIO"),

    # Matriz Variables alimenta cálculos
    Edge("matriz-variables", "plan-5y", "alimenta", 1.0, "Precios, rendimientos, costos = inputs del plan"),
    Edge("matriz-variables", "variables-intel", "alimenta", 1.0, "Intelligence lee la matriz para detectar inconsistencias"),
    Edge("matriz-variables", "coherencia", "alimenta", 1.0, "Coherencia detecta gaps cross con otras matrices"),

    # Plan → cálculos secundarios
    Edge("plan-5y", "sensitivity", "alimenta", 1.0, "Sensitivity simula shocks sobre el plan base"),
    Edge("plan-5y", "monte-carlo", "alimenta", 1.0, "MC corre 10k simulaciones del plan"),
    Edge("plan-5y", "valuation", "alimenta", 1.0, "EV/EBITDA usa EBITDA año 5"),
    Edge("plan-5y", "financing", "alimenta", 1.0, "DSCR/LLCR sobre EBITDA proyectado"),
    Edge("plan-5y", "carbon", "alimenta", 0.5, "Volúmenes anuales calibran LCA"),

    # Matrices alimentan readiness
    Edge("matriz-variables", "readiness", "alimenta", 0.5, "Dimensión 'Calidad datos' del readiness"),
    Edge("data-room", "readiness", "alimenta", 0.5, "Dimensión 'Avance Data Room' del readiness"),
    Edge("plan-5y", "readiness", "alimenta", 1.0, "TIR, VAN → dimensión 'Retorno'"),
    Edge("monte-carlo", "readiness", "alimenta", 0.7, "Prob TIR > WACC → dimensión 'Robustez'"),
    Edge("financing", "readiness", "alimenta", 0.6, "DSCR → dimensión 'Bancabilidad'"),
    Edge("carbon", "readiness", "alimenta", 0.5, "Carbono negativo → dimensión 'ESG'"),
    Edge("compliance", "readiness", "alimenta", 0.5, "% hitos vigentes → dimensión 'Compliance'"),

    # Coherencia y intel → decision
    Edge("coherencia", "decision", "alimenta", 1.0, "Decision Engine usa gaps coherentes como insumo"),
    Edge("variables-intel", "decision", "alimenta", 0.7, "Sugerencias inteligentes alimentan acciones"),
    Edge("sensitivity", "decision", "alimenta", 0.6, "Breakeven informa urgencia de cobertura"),
    Edge("readiness", "decision", "alimenta", 0.5, "Score determina dimensiones débiles"),

    # Outputs
    Edge("plan-5y", "pdf-tearsheet", "deriva", 1.0, "PDF resume KPIs del plan"),
    Edge("readiness", "pdf-tearsheet", "deriva", 0.8, "Score y dimensiones en PDF"),
    Edge("data-room", "pdf-tearsheet", "deriva", 0.7, "Avance DD en PDF"),
    Edge("matriz-variables", "pdf-tearsheet", "deriva", 0.7, "Matriz canónica en PDF"),
    Edge("pdf-tearsheet", "lp-pack", "deriva", 1.0, "ZIP incluye el PDF"),
    Edge("plan-5y", "excel-master", "deriva", 1.0, "Excel exporta el plan completo"),
)


def grafo_completo() -> dict:
    """Devuelve nodos + edges en formato JSON-serializable para echarts."""
    return {
        "nodos": [
            {
                "id": n.id,
                "label": n.label,
                "tipo": n.tipo,
                "descripcion": n.descripcion,
                "plataforma_url": n.plataforma_url,
            }
            for n in NODOS
        ],
        "edges": [
            {
                "desde": e.desde,
                "hacia": e.hacia,
                "tipo": e.tipo,
                "peso": e.peso,
                "descripcion": e.descripcion,
            }
            for e in EDGES
        ],
        "stats": {
            "total_nodos": len(NODOS),
            "total_edges": len(EDGES),
            "tipos_nodo": list({n.tipo for n in NODOS}),
        },
    }


def impacto_de_cambio(modulo_origen: str, profundidad: int = 3) -> list[dict]:
    """Si cambia modulo_origen, qué otros se afectan (BFS hasta profundidad)."""
    visitados: dict[str, int] = {modulo_origen: 0}
    cola = [(modulo_origen, 0)]
    impactados = []

    while cola:
        nodo, dist = cola.pop(0)
        if dist >= profundidad:
            continue
        for e in EDGES:
            if e.desde == nodo and e.hacia not in visitados:
                visitados[e.hacia] = dist + 1
                cola.append((e.hacia, dist + 1))
                # Encontrar el nodo destino
                nodo_dst = next((n for n in NODOS if n.id == e.hacia), None)
                if nodo_dst:
                    impactados.append({
                        "id": nodo_dst.id,
                        "label": nodo_dst.label,
                        "distancia": dist + 1,
                        "tipo_edge": e.tipo,
                        "peso": e.peso,
                        "descripcion_impacto": e.descripcion,
                    })

    return impactados
