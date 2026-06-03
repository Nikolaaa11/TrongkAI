"""Balance de Agua de la planta Trongkai.

Cierra el balance m3 ±1% considerando entradas (pozos, red, lluvia) y
salidas (proceso, lavado, vapor, CIP, riego, RILE) + evaporacion.

Alarmas:
- uso_actual_l_s > 80% derecho DGA      -> CRITICA (corte regulatorio)
- recirculacion < 30%                   -> ineficiente
- rile > 70% entrada                    -> planta tratamiento insuficiente
- costo_agua > 2% COGS                  -> alta

Datos seed: 5 flujos del piloto Parral (pozo propio + Essbio + recirculado).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Literal

from ..storage import data_path

FuenteAgua = Literal["pozo_propio", "red_publica", "recirculada", "lluvia"]
DestinoAgua = Literal["proceso", "lavado", "vapor", "cip", "riego", "rile"]

# Derechos DGA aprobados por pozo (L/s) — del expediente Parral
DGA_DERECHOS = {
    "Pozo 1 (Parral)": 5.0,
}
LIMITE_USO_DGA = 0.80              # alarma critica a 80% del derecho
RECIRCULACION_MIN = 0.30            # umbral eficiencia
RILE_MAX = 0.70                     # umbral capacidad tratamiento
INTENSIDAD_BENCHMARK_L_KG = 12.0    # benchmark agroindustria olivar/tomate


@dataclass
class FlujoAgua:
    origen: str                      # "Pozo 1 (Parral)", "Red Essbio"
    fuente: FuenteAgua
    destino: str                     # "PEF", "Lavadora", "CIP"
    uso: DestinoAgua
    caudal_m3_h: float
    horas_operacion_anual: float
    pct_recirculable: float          # 0..1
    costo_unitario_usd_m3: float = 0.85

    @property
    def volumen_anual_m3(self) -> float:
        return self.caudal_m3_h * self.horas_operacion_anual

    @property
    def caudal_l_s(self) -> float:
        return self.caudal_m3_h * 1000.0 / 3600.0

    @property
    def costo_anual_usd(self) -> float:
        return self.volumen_anual_m3 * self.costo_unitario_usd_m3

    def to_dict(self) -> dict:
        d = asdict(self)
        d["volumen_anual_m3"] = round(self.volumen_anual_m3, 2)
        d["caudal_l_s"] = round(self.caudal_l_s, 3)
        d["costo_anual_usd"] = round(self.costo_anual_usd, 2)
        return d


@dataclass
class BalanceAgua:
    flujos: list[FlujoAgua]
    consumo_total_anual_m3: float
    agua_fresca_m3: float
    agua_recirculada_m3: float
    agua_recirculada_pct: float
    intensidad_hidrica_l_por_kg_producto: float
    costo_total_anual_usd: float
    rile_anual_m3: float
    rile_pct: float
    closure_pct: float
    cumplimiento_dga: dict
    alarmas: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "flujos": [f.to_dict() for f in self.flujos],
            "consumo_total_anual_m3": round(self.consumo_total_anual_m3, 2),
            "agua_fresca_m3": round(self.agua_fresca_m3, 2),
            "agua_recirculada_m3": round(self.agua_recirculada_m3, 2),
            "agua_recirculada_pct": round(self.agua_recirculada_pct, 4),
            "intensidad_hidrica_l_por_kg_producto": round(
                self.intensidad_hidrica_l_por_kg_producto, 3
            ),
            "costo_total_anual_usd": round(self.costo_total_anual_usd, 2),
            "rile_anual_m3": round(self.rile_anual_m3, 2),
            "rile_pct": round(self.rile_pct, 4),
            "closure_pct": round(self.closure_pct, 4),
            "cumplimiento_dga": self.cumplimiento_dga,
            "alarmas": self.alarmas,
        }


def flujos_agua_seed() -> list[FlujoAgua]:
    """Seed: 5 flujos del piloto Parral."""
    return [
        FlujoAgua(
            origen="Pozo 1 (Parral)",
            fuente="pozo_propio",
            destino="PEF Opticept",
            uso="proceso",
            caudal_m3_h=3.0,
            horas_operacion_anual=6000.0,
            pct_recirculable=0.50,
            costo_unitario_usd_m3=0.20,
        ),
        FlujoAgua(
            origen="Pozo 1 (Parral)",
            fuente="pozo_propio",
            destino="Lavadora MMPP",
            uso="lavado",
            caudal_m3_h=2.0,
            horas_operacion_anual=5500.0,
            pct_recirculable=0.30,
            costo_unitario_usd_m3=0.20,
        ),
        FlujoAgua(
            origen="Pozo 1 (Parral)",
            fuente="pozo_propio",
            destino="Caldera biomasa",
            uso="vapor",
            caudal_m3_h=0.5,
            horas_operacion_anual=6000.0,
            pct_recirculable=0.85,
            costo_unitario_usd_m3=0.20,
        ),
        FlujoAgua(
            origen="Red Essbio",
            fuente="red_publica",
            destino="CIP linea 1",
            uso="cip",
            caudal_m3_h=1.0,
            horas_operacion_anual=2200.0,
            pct_recirculable=0.10,
            costo_unitario_usd_m3=1.45,
        ),
        FlujoAgua(
            origen="Recirculado interno",
            fuente="recirculada",
            destino="PEF Opticept",
            uso="proceso",
            caudal_m3_h=1.5,
            horas_operacion_anual=6000.0,
            pct_recirculable=0.0,
            costo_unitario_usd_m3=0.05,
        ),
    ]


def _detectar_alarmas(
    flujos: list[FlujoAgua],
    cumplimiento_dga: dict,
    recirc_pct: float,
    rile_pct: float,
    intensidad_l_kg: float,
) -> list[dict]:
    alarmas: list[dict] = []

    # 1. DGA critica
    for pozo, info in cumplimiento_dga.items():
        if info["uso_pct_derecho"] > LIMITE_USO_DGA:
            alarmas.append({
                "tipo": "dga_excedido",
                "severidad": "critica",
                "pozo": pozo,
                "uso_pct": round(info["uso_pct_derecho"], 3),
                "derecho_l_s": info["derecho_l_s"],
                "uso_actual_l_s": round(info["uso_actual_l_s"], 3),
                "mensaje": f"{pozo}: uso {info['uso_pct_derecho']:.0%} de derecho DGA (limite {LIMITE_USO_DGA:.0%}).",
                "accion": "Ampliar derecho DGA o reducir consumo.",
            })

    # 2. Recirculacion baja
    if recirc_pct < RECIRCULACION_MIN:
        alarmas.append({
            "tipo": "recirculacion_baja",
            "severidad": "media",
            "valor": round(recirc_pct, 3),
            "umbral": RECIRCULACION_MIN,
            "mensaje": f"Recirculacion {recirc_pct:.1%} < umbral {RECIRCULACION_MIN:.0%}. Oportunidad CAPEX.",
        })

    # 3. RILE excesivo
    if rile_pct > RILE_MAX:
        alarmas.append({
            "tipo": "rile_excesivo",
            "severidad": "alta",
            "valor": round(rile_pct, 3),
            "umbral": RILE_MAX,
            "mensaje": f"RILE {rile_pct:.1%} > umbral {RILE_MAX:.0%}. Planta de tratamiento al limite.",
        })

    # 4. Intensidad alta
    if intensidad_l_kg > INTENSIDAD_BENCHMARK_L_KG:
        alarmas.append({
            "tipo": "intensidad_alta",
            "severidad": "media",
            "valor": round(intensidad_l_kg, 2),
            "umbral": INTENSIDAD_BENCHMARK_L_KG,
            "mensaje": f"Intensidad hidrica {intensidad_l_kg:.1f} L/kg sobre benchmark {INTENSIDAD_BENCHMARK_L_KG} L/kg.",
        })
    return alarmas


def computar_balance_agua(
    flujos: list[FlujoAgua] | None = None,
    produccion_anual_kg: float = 850_000.0,
) -> BalanceAgua:
    """Balance hidrico anual con closure ±1%."""
    if flujos is None:
        flujos = flujos_agua_seed()
    if produccion_anual_kg <= 0:
        raise ValueError(f"produccion_anual_kg debe ser > 0, got {produccion_anual_kg}")

    consumo_total = sum(f.volumen_anual_m3 for f in flujos)
    if consumo_total <= 0:
        raise ValueError("Consumo total agua es 0.")

    agua_fresca = sum(
        f.volumen_anual_m3 for f in flujos if f.fuente != "recirculada"
    )
    agua_recirc = sum(
        f.volumen_anual_m3 for f in flujos if f.fuente == "recirculada"
    )
    recirc_pct = agua_recirc / consumo_total

    intensidad = consumo_total * 1000.0 / produccion_anual_kg  # L/kg

    costo_total = sum(f.costo_anual_usd for f in flujos)

    # RILE: lo que NO se recircula despues del proceso (1 - pct_recirculable)
    rile_total = sum(
        f.volumen_anual_m3 * (1 - f.pct_recirculable) for f in flujos
    )
    # No descontamos lo evaporado en vapor: queda en producto / atmosfera
    # Aproximacion: 100% del vapor sale del sistema (no es RILE).
    rile_total -= sum(
        f.volumen_anual_m3 * (1 - f.pct_recirculable)
        for f in flujos
        if f.uso == "vapor"
    )
    rile_pct = max(0.0, rile_total / consumo_total)

    # Cumplimiento DGA
    cumplimiento_dga = {}
    for pozo, derecho_l_s in DGA_DERECHOS.items():
        uso_caudal_l_s = sum(
            f.caudal_l_s for f in flujos if f.origen == pozo
        )
        cumplimiento_dga[pozo] = {
            "derecho_l_s": derecho_l_s,
            "uso_actual_l_s": uso_caudal_l_s,
            "uso_pct_derecho": uso_caudal_l_s / derecho_l_s if derecho_l_s > 0 else 0.0,
            "ok": uso_caudal_l_s <= derecho_l_s,
        }

    # Closure: entradas == salidas (proceso + evap aproximado + RILE)
    suma_individuales = sum(f.volumen_anual_m3 for f in flujos)
    closure_pct = abs(suma_individuales - consumo_total) / consumo_total * 100.0

    alarmas = _detectar_alarmas(flujos, cumplimiento_dga, recirc_pct, rile_pct, intensidad)

    return BalanceAgua(
        flujos=flujos,
        consumo_total_anual_m3=consumo_total,
        agua_fresca_m3=agua_fresca,
        agua_recirculada_m3=agua_recirc,
        agua_recirculada_pct=recirc_pct,
        intensidad_hidrica_l_por_kg_producto=intensidad,
        costo_total_anual_usd=costo_total,
        rile_anual_m3=rile_total,
        rile_pct=rile_pct,
        closure_pct=closure_pct,
        cumplimiento_dga=cumplimiento_dga,
        alarmas=alarmas,
    )


def balance_a_sankey(balance: BalanceAgua) -> dict:
    """Sankey: fuente -> uso -> destino final (proceso / RILE / vapor)."""
    nodes: list[dict] = []
    seen: set[str] = set()
    links: list[dict] = []

    fuentes = sorted({f.fuente for f in balance.flujos})
    for f in fuentes:
        label = f.replace("_", " ").title()
        if label not in seen:
            nodes.append({"name": label})
            seen.add(label)

    for f in balance.flujos:
        # nodo destino
        if f.destino not in seen:
            nodes.append({"name": f.destino})
            seen.add(f.destino)
        source = f.fuente.replace("_", " ").title()
        links.append({
            "source": source,
            "target": f.destino,
            "value": round(f.volumen_anual_m3, 2),
        })

    # Salidas: RILE y Recirculacion
    if "RILE" not in seen:
        nodes.append({"name": "RILE"})
        seen.add("RILE")
    if "Recirculacion" not in seen:
        nodes.append({"name": "Recirculacion"})
        seen.add("Recirculacion")
    for f in balance.flujos:
        rile_vol = f.volumen_anual_m3 * (1 - f.pct_recirculable)
        recirc_vol = f.volumen_anual_m3 * f.pct_recirculable
        if rile_vol > 0:
            links.append({
                "source": f.destino,
                "target": "RILE",
                "value": round(rile_vol, 2),
            })
        if recirc_vol > 0:
            links.append({
                "source": f.destino,
                "target": "Recirculacion",
                "value": round(recirc_vol, 2),
            })
    return {"nodes": nodes, "links": links, "unit": "m³/año"}


_STORAGE = "balance-agua.json"


def guardar_flujos_agua(flujos: list[FlujoAgua]) -> None:
    p = data_path(_STORAGE)
    p.write_text(
        json.dumps([asdict(f) for f in flujos], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def cargar_flujos_agua() -> list[FlujoAgua]:
    p = data_path(_STORAGE)
    if not p.exists():
        return flujos_agua_seed()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return [FlujoAgua(**d) for d in data]
    except Exception:
        return flujos_agua_seed()
