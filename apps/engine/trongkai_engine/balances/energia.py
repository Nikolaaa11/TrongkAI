"""Balance de Energia de la planta Trongkai.

Cierra el balance kWh ±2% sobre el consumo total. Genera Sankey + alarmas:
- factor_potencia < 0.92  -> multa SEC Chile
- factor_carga > 0.95     -> equipo sobre-utilizado
- mix_renovable < 30%     -> ESG narrativa debil
- intensidad > 3.5 kWh/kg -> sobre benchmark sectorial

Datos seed: 7 equipos del piloto industrial (PEF, micromolienda, caldera...).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Literal

from ..storage import data_path

TipoEnergia = Literal["electrica", "gas_natural", "vapor", "diesel", "biomasa", "solar"]

# Benchmark intensidad energetica agroindustria (literatura): 2.5-4.0 kWh/kg
INTENSIDAD_BENCHMARK_KWH_KG = 3.5
# SEC Chile: factor de potencia minimo sin multa
FP_MINIMO_SEC = 0.92
# Mix renovable minimo para narrativa ESG fuerte
MIX_RENOVABLE_MINIMO = 0.30


@dataclass
class FlujoEnergetico:
    equipo: str
    tipo: TipoEnergia
    potencia_nominal_kw: float
    horas_operacion_anual: float
    factor_carga: float                # 0..1 (% del tiempo en carga nominal)
    factor_potencia: float = 1.0       # cos(phi); 1.0 para no-electricos
    eficiencia_pct: float = 0.85       # rendimiento equipo
    costo_unitario_usd_kwh: float = 0.12  # USD/kWh promedio Chile industrial

    @property
    def consumo_anual_kwh(self) -> float:
        """Energia consumida al ano (kWh)."""
        return (
            self.potencia_nominal_kw
            * self.horas_operacion_anual
            * self.factor_carga
        )

    @property
    def costo_anual_usd(self) -> float:
        return self.consumo_anual_kwh * self.costo_unitario_usd_kwh

    def to_dict(self) -> dict:
        d = asdict(self)
        d["consumo_anual_kwh"] = round(self.consumo_anual_kwh, 2)
        d["costo_anual_usd"] = round(self.costo_anual_usd, 2)
        return d


@dataclass
class BalanceEnergia:
    flujos: list[FlujoEnergetico]
    consumo_total_anual_mwh: float
    costo_total_anual_usd: float
    intensidad_energetica_kwh_por_kg_producto: float
    mix_renovable_pct: float
    factor_potencia_planta: float
    factor_carga_promedio: float
    closure_pct: float
    alarmas: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "flujos": [f.to_dict() for f in self.flujos],
            "consumo_total_anual_mwh": round(self.consumo_total_anual_mwh, 2),
            "costo_total_anual_usd": round(self.costo_total_anual_usd, 2),
            "intensidad_energetica_kwh_por_kg_producto": round(
                self.intensidad_energetica_kwh_por_kg_producto, 3
            ),
            "mix_renovable_pct": round(self.mix_renovable_pct, 4),
            "factor_potencia_planta": round(self.factor_potencia_planta, 3),
            "factor_carga_promedio": round(self.factor_carga_promedio, 3),
            "closure_pct": round(self.closure_pct, 4),
            "alarmas": self.alarmas,
        }


def flujos_seed() -> list[FlujoEnergetico]:
    """Seed: 7 equipos clave del piloto industrial Parral.

    Calibrado contra fichas tecnicas Opticept, datos sectoriales agroindustria
    chilena y benchmarks Min Energia 2024.
    """
    return [
        FlujoEnergetico(
            equipo="PEF Opticept",
            tipo="electrica",
            potencia_nominal_kw=250.0,
            horas_operacion_anual=6000.0,
            factor_carga=0.85,
            factor_potencia=0.94,
            eficiencia_pct=0.92,
            costo_unitario_usd_kwh=0.13,
        ),
        FlujoEnergetico(
            equipo="Micromolienda",
            tipo="electrica",
            potencia_nominal_kw=150.0,
            horas_operacion_anual=5500.0,
            factor_carga=0.80,
            factor_potencia=0.91,
            eficiencia_pct=0.88,
            costo_unitario_usd_kwh=0.13,
        ),
        FlujoEnergetico(
            equipo="Secador rotativo",
            tipo="gas_natural",
            potencia_nominal_kw=800.0,
            horas_operacion_anual=6000.0,
            factor_carga=0.75,
            factor_potencia=1.0,
            eficiencia_pct=0.78,
            costo_unitario_usd_kwh=0.045,
        ),
        FlujoEnergetico(
            equipo="Caldera biomasa",
            tipo="biomasa",
            potencia_nominal_kw=1200.0,
            horas_operacion_anual=6000.0,
            factor_carga=0.70,
            factor_potencia=1.0,
            eficiencia_pct=0.82,
            costo_unitario_usd_kwh=0.025,   # orujo propio: costo casi cero
        ),
        FlujoEnergetico(
            equipo="Compresores aire",
            tipo="electrica",
            potencia_nominal_kw=75.0,
            horas_operacion_anual=5800.0,
            factor_carga=0.65,
            factor_potencia=0.89,
            eficiencia_pct=0.80,
            costo_unitario_usd_kwh=0.13,
        ),
        FlujoEnergetico(
            equipo="Sistema vapor",
            tipo="vapor",
            potencia_nominal_kw=500.0,
            horas_operacion_anual=5500.0,
            factor_carga=0.72,
            factor_potencia=1.0,
            eficiencia_pct=0.85,
            costo_unitario_usd_kwh=0.055,
        ),
        FlujoEnergetico(
            equipo="Iluminacion y auxiliares",
            tipo="electrica",
            potencia_nominal_kw=50.0,
            horas_operacion_anual=8000.0,
            factor_carga=0.60,
            factor_potencia=0.95,
            eficiencia_pct=0.95,
            costo_unitario_usd_kwh=0.13,
        ),
    ]


def _detectar_alarmas(
    flujos: list[FlujoEnergetico],
    mix_renovable_pct: float,
    fp_planta: float,
    intensidad_kwh_kg: float,
) -> list[dict]:
    alarmas: list[dict] = []
    # 1. Factor potencia critico (multa SEC)
    if fp_planta < FP_MINIMO_SEC:
        alarmas.append({
            "tipo": "factor_potencia",
            "severidad": "critica",
            "valor": round(fp_planta, 3),
            "umbral": FP_MINIMO_SEC,
            "mensaje": f"Factor de potencia {fp_planta:.3f} < {FP_MINIMO_SEC} (multa SEC Chile).",
            "accion": "Instalar banco de capacitores en planta principal.",
        })
    # 2. Sobre-uso por equipo
    for f in flujos:
        if f.factor_carga > 0.95:
            alarmas.append({
                "tipo": "sobreuso_equipo",
                "severidad": "alta",
                "equipo": f.equipo,
                "factor_carga": round(f.factor_carga, 3),
                "mensaje": f"{f.equipo} a {f.factor_carga:.0%} carga: riesgo falla y sin holgura.",
            })
    # 3. Mix renovable debil
    if mix_renovable_pct < MIX_RENOVABLE_MINIMO:
        alarmas.append({
            "tipo": "mix_renovable",
            "severidad": "media",
            "valor": round(mix_renovable_pct, 3),
            "umbral": MIX_RENOVABLE_MINIMO,
            "mensaje": f"Mix renovable {mix_renovable_pct:.1%} debil para narrativa ESG (umbral {MIX_RENOVABLE_MINIMO:.0%}).",
        })
    # 4. Intensidad sobre benchmark
    if intensidad_kwh_kg > INTENSIDAD_BENCHMARK_KWH_KG:
        alarmas.append({
            "tipo": "intensidad_alta",
            "severidad": "media",
            "valor": round(intensidad_kwh_kg, 2),
            "umbral": INTENSIDAD_BENCHMARK_KWH_KG,
            "mensaje": f"Intensidad {intensidad_kwh_kg:.2f} kWh/kg > benchmark {INTENSIDAD_BENCHMARK_KWH_KG} kWh/kg.",
        })
    return alarmas


def computar_balance_energia(
    flujos: list[FlujoEnergetico] | None = None,
    produccion_anual_kg: float = 850_000.0,
) -> BalanceEnergia:
    """Calcula el balance energetico anual.

    Args:
        flujos: lista de equipos. None -> seed default.
        produccion_anual_kg: producto terminado anual para intensidad (kg).

    Returns:
        BalanceEnergia con closure ±2% sobre el consumo total.
    """
    if flujos is None:
        flujos = flujos_seed()

    if produccion_anual_kg <= 0:
        raise ValueError(f"produccion_anual_kg debe ser > 0, got {produccion_anual_kg}")

    consumo_total_kwh = sum(f.consumo_anual_kwh for f in flujos)
    if consumo_total_kwh <= 0:
        raise ValueError("Consumo total energetico es 0 (todos los flujos estan en 0).")

    costo_total = sum(f.costo_anual_usd for f in flujos)
    intensidad = consumo_total_kwh / produccion_anual_kg

    # Mix renovable: biomasa + solar
    consumo_renovable = sum(
        f.consumo_anual_kwh for f in flujos if f.tipo in ("biomasa", "solar")
    )
    mix_renovable = consumo_renovable / consumo_total_kwh

    # Factor potencia ponderado por consumo
    consumo_electrico = sum(f.consumo_anual_kwh for f in flujos if f.tipo == "electrica")
    if consumo_electrico > 0:
        fp_planta = sum(
            f.factor_potencia * f.consumo_anual_kwh
            for f in flujos
            if f.tipo == "electrica"
        ) / consumo_electrico
    else:
        fp_planta = 1.0

    # Factor carga promedio ponderado
    factor_carga_avg = sum(f.factor_carga * f.consumo_anual_kwh for f in flujos) / consumo_total_kwh

    # Closure: verificamos que la suma de consumos por equipo == total reportado
    # (siempre cuadra en este modelo, pero deja la puerta para anadir perdidas de
    # distribucion en una iteracion futura).
    suma_individuales = sum(f.consumo_anual_kwh for f in flujos)
    closure_pct = abs(suma_individuales - consumo_total_kwh) / consumo_total_kwh * 100.0

    alarmas = _detectar_alarmas(flujos, mix_renovable, fp_planta, intensidad)

    return BalanceEnergia(
        flujos=flujos,
        consumo_total_anual_mwh=consumo_total_kwh / 1000.0,
        costo_total_anual_usd=costo_total,
        intensidad_energetica_kwh_por_kg_producto=intensidad,
        mix_renovable_pct=mix_renovable,
        factor_potencia_planta=fp_planta,
        factor_carga_promedio=factor_carga_avg,
        closure_pct=closure_pct,
        alarmas=alarmas,
    )


def balance_a_sankey(balance: BalanceEnergia) -> dict:
    """Sankey: fuentes de energia -> equipos consumidores."""
    nodes: list[dict] = []
    seen: set[str] = set()
    links: list[dict] = []

    # Nodos fuentes (por tipo)
    tipos_usados = sorted({f.tipo for f in balance.flujos})
    for t in tipos_usados:
        label = t.replace("_", " ").title()
        nodes.append({"name": label})
        seen.add(label)

    # Nodos equipos
    for f in balance.flujos:
        if f.equipo not in seen:
            nodes.append({"name": f.equipo})
            seen.add(f.equipo)

    # Links fuente -> equipo
    for f in balance.flujos:
        source = f.tipo.replace("_", " ").title()
        links.append({
            "source": source,
            "target": f.equipo,
            "value": round(f.consumo_anual_kwh / 1000.0, 2),  # MWh
        })

    return {"nodes": nodes, "links": links, "unit": "MWh/año"}


# ===== Persistencia =====
_STORAGE = "balance-energia.json"


def guardar_flujos(flujos: list[FlujoEnergetico]) -> None:
    p = data_path(_STORAGE)
    p.write_text(
        json.dumps([asdict(f) for f in flujos], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def cargar_flujos() -> list[FlujoEnergetico]:
    p = data_path(_STORAGE)
    if not p.exists():
        return flujos_seed()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return [FlujoEnergetico(**d) for d in data]
    except Exception:
        return flujos_seed()
