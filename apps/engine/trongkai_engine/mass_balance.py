"""Motor de balance de masa — Módulo 2.

Spec viva: docs/BALANCE-MASA.md.

Reglas duras (no negociables, falla en runtime si se violan):
- suma(productos) + masa_evaporada + perdidas == masa_input  ± tolerancia
- humedad_final ∈ [0, 1)
- masa_input > 0

Modos:
- A: rendimientos aplicados sobre la masa inicial (`base inicial`).
- B: rendimientos aplicados sobre la materia seca post-secado (`base deshidratada`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class BalanceMode(StrEnum):
    A_INITIAL_BASE = "A"
    B_DEHYDRATED_BASE = "B"


class MassBalanceError(ValueError):
    """El balance no cuadra dentro de la tolerancia o los inputs son inválidos."""


@dataclass(frozen=True)
class MateriaPrimaSpec:
    """Spec mínima de una MMPP para el balance."""

    codigo: str  # ALPERUJO, TOMASA, POMASA, ORUJO_UVA, LEVADURA
    humedad_inicial_pct: float  # 0..1
    materia_solida_pct: float  # 0..1
    aceite_extraible_pct: float = 0.0  # fracción del input inicial
    licopeno_pct: float = 0.0
    pectina_pct: float = 0.0

    def __post_init__(self) -> None:
        if not 0 <= self.humedad_inicial_pct < 1:
            raise MassBalanceError(
                f"humedad_inicial_pct fuera de rango: {self.humedad_inicial_pct}"
            )
        # Permite tolerancia de redondeo en la suma h + ms
        if abs((self.humedad_inicial_pct + self.materia_solida_pct) - 1) > 0.02:
            raise MassBalanceError(
                f"humedad ({self.humedad_inicial_pct}) + ms ({self.materia_solida_pct})"
                f" debe ≈ 1 para {self.codigo}"
            )


@dataclass
class MassBalanceResult:
    mmpp: str
    mode: BalanceMode
    input_ton: float
    humedad_final_pct: float

    materia_seca_pura_ton: float
    aceite_extraido_ton: float
    licopeno_extraido_ton: float
    pectina_extraida_ton: float
    harina_final_ton: float  # MS + humedad residual del 10%
    agua_evaporada_ton: float
    perdidas_ton: float

    # Para diagnóstico
    suma_outputs_ton: float
    delta_balance_pct: float

    sankey: dict = field(default_factory=dict)

    @property
    def materia_seca_neta_pct(self) -> float:
        """Fracción del input que termina como producto seco vendible."""
        if self.input_ton == 0:
            return 0.0
        return (
            self.harina_final_ton
            + self.aceite_extraido_ton
            + self.licopeno_extraido_ton
            + self.pectina_extraida_ton
        ) / self.input_ton


def _compute_outputs(
    spec: MateriaPrimaSpec,
    input_ton: float,
    mode: BalanceMode,
    humedad_final_pct: float,
    perdidas_pct: float,
) -> tuple[float, float, float, float, float]:
    """Retorna (harina_final, aceite, licopeno, pectina, perdidas) en ton."""
    perdidas = input_ton * perdidas_pct

    if mode is BalanceMode.A_INITIAL_BASE:
        # Modo A: extracciones sobre input inicial.
        aceite = input_ton * spec.aceite_extraible_pct
        licopeno = input_ton * spec.licopeno_pct
        pectina = input_ton * spec.pectina_pct
        # MS pura = input * ms% - lo extraído (estos vienen de la MS)
        ms_pura_para_harina = input_ton * spec.materia_solida_pct - aceite - licopeno - pectina
        if ms_pura_para_harina < 0:
            raise MassBalanceError(
                f"MS insuficiente para extracciones: {ms_pura_para_harina:.4f}"
            )
        # Harina queda con humedad_final_pct
        harina_final = ms_pura_para_harina / (1 - humedad_final_pct)
    else:
        # Modo B: extracciones sobre base deshidratada (MS pura).
        ms_total = input_ton * spec.materia_solida_pct
        aceite = ms_total * spec.aceite_extraible_pct
        licopeno = ms_total * spec.licopeno_pct
        pectina = ms_total * spec.pectina_pct
        ms_pura_para_harina = ms_total - aceite - licopeno - pectina
        if ms_pura_para_harina < 0:
            raise MassBalanceError(
                f"MS insuficiente para extracciones modo B: {ms_pura_para_harina:.4f}"
            )
        harina_final = ms_pura_para_harina / (1 - humedad_final_pct)

    return harina_final, aceite, licopeno, pectina, perdidas


def compute_mass_balance(
    spec: MateriaPrimaSpec,
    input_ton: float,
    mode: BalanceMode = BalanceMode.A_INITIAL_BASE,
    humedad_final_pct: float = 0.10,
    perdidas_pct: float = 0.031,  # default conservador, ver SUPUESTOS §B
    tolerancia_pct: float = 0.005,
) -> MassBalanceResult:
    """Calcula el balance de masa para una MMPP y un lote.

    Raises:
        MassBalanceError: si los inputs son inválidos o la suma no cuadra.
    """
    if input_ton <= 0:
        raise MassBalanceError(f"input_ton debe ser > 0, got {input_ton}")
    if not 0 <= humedad_final_pct < 1:
        raise ValueError(f"humedad_final_pct ∈ [0,1), got {humedad_final_pct}")
    if not 0 <= perdidas_pct < 1:
        raise MassBalanceError(f"perdidas_pct ∈ [0,1), got {perdidas_pct}")

    harina_final, aceite, licopeno, pectina, perdidas = _compute_outputs(
        spec, input_ton, mode, humedad_final_pct, perdidas_pct
    )

    suma_solidos_outputs = harina_final + aceite + licopeno + pectina
    # El agua evaporada es lo que falta para cuadrar (incluye el agua original y resta humedad
    # residual de la harina, las extracciones se asumen secas / sin humedad)
    agua_evaporada = input_ton - suma_solidos_outputs - perdidas

    if agua_evaporada < -tolerancia_pct * input_ton:
        raise MassBalanceError(
            f"Agua evaporada negativa: {agua_evaporada:.4f} ton (mmpp={spec.codigo}, mode={mode.value})"
        )

    suma_total = suma_solidos_outputs + agua_evaporada + perdidas
    delta_pct = abs(suma_total - input_ton) / input_ton
    if delta_pct > tolerancia_pct:
        raise MassBalanceError(
            f"Balance no cuadra: suma={suma_total:.6f}, input={input_ton:.6f}, "
            f"delta={delta_pct:.4%} > tol {tolerancia_pct:.4%}"
        )

    ms_pura = harina_final * (1 - humedad_final_pct)

    result = MassBalanceResult(
        mmpp=spec.codigo,
        mode=mode,
        input_ton=input_ton,
        humedad_final_pct=humedad_final_pct,
        materia_seca_pura_ton=ms_pura,
        aceite_extraido_ton=aceite,
        licopeno_extraido_ton=licopeno,
        pectina_extraida_ton=pectina,
        harina_final_ton=harina_final,
        agua_evaporada_ton=max(agua_evaporada, 0.0),
        perdidas_ton=perdidas,
        suma_outputs_ton=suma_total,
        delta_balance_pct=delta_pct,
    )
    result.sankey = _to_sankey(result)
    return result


def _to_sankey(r: MassBalanceResult) -> dict:
    """Diagrama Sankey listo para ECharts."""
    nodes = [
        {"name": f"Input {r.mmpp}"},
        {"name": "Materia Sólida"},
        {"name": "Agua"},
        {"name": "Harina final (10%)"},
        {"name": "Aceite"},
        {"name": "Licopeno"},
        {"name": "Pectina"},
        {"name": "Agua Evaporada"},
        {"name": "Pérdidas"},
    ]
    ms_total = r.materia_seca_pura_ton + r.aceite_extraido_ton + r.licopeno_extraido_ton + r.pectina_extraida_ton
    links = [
        {"source": f"Input {r.mmpp}", "target": "Materia Sólida", "value": round(ms_total, 4)},
        {
            "source": f"Input {r.mmpp}",
            "target": "Agua",
            "value": round(r.input_ton - ms_total, 4),
        },
        {"source": "Materia Sólida", "target": "Harina final (10%)", "value": round(r.harina_final_ton * (1 - r.humedad_final_pct), 4)},
        {"source": "Materia Sólida", "target": "Aceite", "value": round(r.aceite_extraido_ton, 4)},
        {"source": "Agua", "target": "Harina final (10%)", "value": round(r.harina_final_ton * r.humedad_final_pct, 4)},
        {"source": "Agua", "target": "Agua Evaporada", "value": round(r.agua_evaporada_ton, 4)},
        {"source": f"Input {r.mmpp}", "target": "Pérdidas", "value": round(r.perdidas_ton, 4)},
    ]
    if r.licopeno_extraido_ton > 0:
        links.append(
            {"source": "Materia Sólida", "target": "Licopeno", "value": round(r.licopeno_extraido_ton, 4)}
        )
    if r.pectina_extraida_ton > 0:
        links.append(
            {"source": "Materia Sólida", "target": "Pectina", "value": round(r.pectina_extraida_ton, 4)}
        )
    return {"nodes": nodes, "links": [link for link in links if link["value"] > 0]}
