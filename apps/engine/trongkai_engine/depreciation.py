"""Depreciación tributaria por categoría de activo + tax shield Chile.

Fuente normativa: DL 824 LIR + Tabla vida útil SII (Resolución 43/2002).
https://www.sii.cl/valores_y_fechas/tabla_vida_util.html

Categorías típicas de Trongkai (años vida útil normal SII):
- Maquinaria industrial alimentos: 10 años
- Equipos PEF / Opticept / extractores: 10 años (maquinaria especializada)
- Edificios y obras civiles: 50-80 años (depende construcción)
- Muebles e instalaciones: 7 años
- Vehículos (camiones recepción MMPP): 7 años
- Equipos computacionales y software: 6 años

Métodos disponibles:
- NORMAL: vida útil tabla SII (depreciación lineal sobre los años de vida útil).
- ACELERADA: vida útil / 3 (LIR Art 31 N°5), aplica a bienes nuevos.
- INSTANTANEA: 100% año 1 (PYME ProPyme Régimen 14 D N°3).

Régimen tributario:
- General: 27% renta corporativa.
- ProPyme Régimen 14 D N°3: 25% renta corporativa + depreciación instantánea.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CategoriaActivo(StrEnum):
    MAQUINARIA_INDUSTRIAL = "MAQUINARIA_INDUSTRIAL"  # 10 años SII
    EQUIPO_ESPECIALIZADO = "EQUIPO_ESPECIALIZADO"    # 10 años (PEF, extractores)
    EDIFICIO = "EDIFICIO"                            # 50 años (estructura básica)
    VEHICULO = "VEHICULO"                            # 7 años
    MUEBLES_INSTALACIONES = "MUEBLES_INSTALACIONES"  # 7 años
    EQUIPO_COMPUTACIONAL = "EQUIPO_COMPUTACIONAL"    # 6 años


class MetodoDepreciacion(StrEnum):
    NORMAL = "NORMAL"
    ACELERADA = "ACELERADA"
    INSTANTANEA = "INSTANTANEA"


class RegimenTributario(StrEnum):
    GENERAL = "GENERAL"  # 27%
    PROPYME = "PROPYME"  # 25%


# Vida útil normal por categoría (años) — tabla SII
VIDA_UTIL_NORMAL: dict[CategoriaActivo, int] = {
    CategoriaActivo.MAQUINARIA_INDUSTRIAL: 10,
    CategoriaActivo.EQUIPO_ESPECIALIZADO: 10,
    CategoriaActivo.EDIFICIO: 50,
    CategoriaActivo.VEHICULO: 7,
    CategoriaActivo.MUEBLES_INSTALACIONES: 7,
    CategoriaActivo.EQUIPO_COMPUTACIONAL: 6,
}


TASA_RENTA_POR_REGIMEN: dict[RegimenTributario, float] = {
    RegimenTributario.GENERAL: 0.27,
    RegimenTributario.PROPYME: 0.25,
}


@dataclass
class ActivoFijo:
    """Un activo fijo individual con su perfil de depreciación."""
    descripcion: str
    monto_clp: float
    ano_adquisicion: int  # 1..5
    categoria: CategoriaActivo
    metodo: MetodoDepreciacion = MetodoDepreciacion.NORMAL

    def vida_util_aplicada(self) -> int:
        normal = VIDA_UTIL_NORMAL[self.categoria]
        if self.metodo is MetodoDepreciacion.NORMAL:
            return normal
        if self.metodo is MetodoDepreciacion.ACELERADA:
            return max(1, normal // 3)
        if self.metodo is MetodoDepreciacion.INSTANTANEA:
            return 1
        return normal

    def depreciacion_anual_clp(self) -> float:
        """Depreciación lineal anual sobre la vida útil aplicada."""
        return self.monto_clp / self.vida_util_aplicada()


@dataclass
class DepreciacionResult:
    """Cronograma de depreciación a 5 años."""
    depreciacion_por_ano: list[float]  # ano 1..5
    activos: list[ActivoFijo]
    metodo_predominante: MetodoDepreciacion
    regimen: RegimenTributario

    @property
    def total_depreciacion_5y(self) -> float:
        return sum(self.depreciacion_por_ano)


def calcular_depreciacion(
    activos: list[ActivoFijo],
    horizonte_anos: int = 5,
) -> list[float]:
    """Devuelve list[float] de depreciación anual sumando todos los activos."""
    deprec = [0.0] * horizonte_anos
    for a in activos:
        anos_aplicada = a.vida_util_aplicada()
        anual = a.depreciacion_anual_clp()
        # Depreciar desde el año de adquisición hasta agotar vida útil o horizonte
        for offset in range(anos_aplicada):
            ano_target = a.ano_adquisicion - 1 + offset  # índice 0
            if 0 <= ano_target < horizonte_anos:
                deprec[ano_target] += anual
    return deprec


def tax_shield(
    ebitda_anual: list[float],
    depreciacion_anual: list[float],
    intereses_anual: list[float] | None = None,
    regimen: RegimenTributario = RegimenTributario.GENERAL,
) -> dict:
    """Calcula utilidad neta y tax shield por año.

    Fórmula:
      EBT (Earnings Before Tax) = EBITDA - Depreciación - Intereses
      Si EBT > 0: impuesto = EBT × tasa_renta. Si EBT < 0: pérdida arrastrada (0 impuesto este año).
      Utilidad neta = EBT - impuesto
      Tax shield = (Depreciación + Intereses) × tasa_renta (ahorro fiscal vs sin depreciar)
    """
    tasa = TASA_RENTA_POR_REGIMEN[regimen]
    intereses_anual = intereses_anual or [0.0] * len(ebitda_anual)

    ebt = []
    impuesto = []
    util_neta = []
    shield = []

    for ebitda, dep, intereses in zip(ebitda_anual, depreciacion_anual, intereses_anual):
        ebt_ano = ebitda - dep - intereses
        imp_ano = max(0.0, ebt_ano * tasa)
        un_ano = ebt_ano - imp_ano
        sh_ano = (dep + intereses) * tasa
        ebt.append(ebt_ano)
        impuesto.append(imp_ano)
        util_neta.append(un_ano)
        shield.append(sh_ano)

    return {
        "regimen": regimen.value,
        "tasa_renta": tasa,
        "ebt_anual": ebt,
        "impuesto_anual": impuesto,
        "utilidad_neta_anual": util_neta,
        "tax_shield_anual": shield,
        "total_impuesto_5y": sum(impuesto),
        "total_utilidad_neta_5y": sum(util_neta),
        "total_tax_shield_5y": sum(shield),
    }


# ============================================================================
# Helper: convertir capex_anual_clp del ParametrosPlan en lista de ActivoFijo
# ============================================================================

def capex_a_activos_default(
    capex_anual_clp: dict[int, float],
    metodo: MetodoDepreciacion = MetodoDepreciacion.NORMAL,
) -> list[ActivoFijo]:
    """Convierte el CapEx anual genérico a una lista de ActivoFijo con mix realista.

    Heurística para Trongkai:
      - 60% Maquinaria industrial (etapas proceso)
      - 25% Equipo especializado (Opticept, tricánter)
      - 10% Edificio / instalaciones
      - 5% Muebles + equipos computacionales

    Cuando lleguen activos reales con factura, reemplazar este helper por una
    lista concreta cargada desde DB.
    """
    activos: list[ActivoFijo] = []
    for ano, monto in capex_anual_clp.items():
        activos.append(ActivoFijo(
            descripcion=f"Maquinaria industrial año {ano}",
            monto_clp=monto * 0.60,
            ano_adquisicion=ano,
            categoria=CategoriaActivo.MAQUINARIA_INDUSTRIAL,
            metodo=metodo,
        ))
        activos.append(ActivoFijo(
            descripcion=f"Equipo especializado año {ano}",
            monto_clp=monto * 0.25,
            ano_adquisicion=ano,
            categoria=CategoriaActivo.EQUIPO_ESPECIALIZADO,
            metodo=metodo,
        ))
        activos.append(ActivoFijo(
            descripcion=f"Edificio / instalaciones año {ano}",
            monto_clp=monto * 0.10,
            ano_adquisicion=ano,
            categoria=CategoriaActivo.EDIFICIO,
            metodo=MetodoDepreciacion.NORMAL,  # edificios no aplican acelerada típicamente
        ))
        activos.append(ActivoFijo(
            descripcion=f"Muebles y equipos año {ano}",
            monto_clp=monto * 0.05,
            ano_adquisicion=ano,
            categoria=CategoriaActivo.MUEBLES_INSTALACIONES,
            metodo=metodo,
        ))
    return activos
