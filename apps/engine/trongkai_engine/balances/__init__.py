"""Balances integrales de la biorrefineria Trongkai.

4 balances interdependientes con closure controlado:
- producto (masa)      ±0.5%   - reusa mass_balance.py
- energia (kWh)        ±2%     - balances/energia.py
- agua (m3)            ±1%     - balances/agua.py
- rrhh (horas)         100%    - balances/rrhh.py    <- con alarmas horas extras

Integrado:
- balances/integrado.py        - cross-checks entre los 4

Persistencia: data/balance-{energia,agua,rrhh}.json via storage.data_path().
"""
from __future__ import annotations

from .energia import (
    BalanceEnergia,
    FlujoEnergetico,
    TipoEnergia,
    computar_balance_energia,
    flujos_seed,
)
from .agua import (
    BalanceAgua,
    FlujoAgua,
    FuenteAgua,
    DestinoAgua,
    computar_balance_agua,
    flujos_agua_seed,
)
from .rrhh import (
    BalanceRRHH,
    Trabajador,
    AsignacionHoras,
    computar_balance_rrhh,
    trabajadores_seed,
    asignaciones_seed,
    detectar_alarmas,
)
from .integrado import BalanceIntegrado, computar_balance_integrado
from .etapas import (
    BalancePorEtapas,
    EtapaPlanta,
    NivelDato,
    ProductoEtapas,
    computar_balance_etapas,
    etapas_seed,
    matriz_productos_x_etapas,
    productos_seed,
    resumen_datos_faltantes,
)
from .humedades_mmpp import HumedadMMPP, HUMEDADES_INGRESO, listar_humedades, humedad_por_mmpp
from .parametros_planta import (
    ArriendoEquipos,
    CalorResidualLaGloria,
    ParametrosPlanta,
    SueldoCargo,
    TarifaAgua,
    TarifaEnergia,
    TarifaFlete,
    actualizar_parametros,
    cargar_parametros,
    guardar_parametros,
    parametros_seed,
    sueldos_seed,
)
from .costeo_etapas import CostoEtapa, computar_costo_etapa, computar_costeo_completo

__all__ = [
    "BalancePorEtapas",
    "EtapaPlanta",
    "NivelDato",
    "ProductoEtapas",
    "computar_balance_etapas",
    "etapas_seed",
    "matriz_productos_x_etapas",
    "productos_seed",
    "resumen_datos_faltantes",
    "HumedadMMPP", "HUMEDADES_INGRESO", "listar_humedades", "humedad_por_mmpp",
    "ArriendoEquipos", "CalorResidualLaGloria", "ParametrosPlanta",
    "SueldoCargo", "TarifaAgua", "TarifaEnergia", "TarifaFlete",
    "actualizar_parametros", "cargar_parametros", "guardar_parametros",
    "parametros_seed", "sueldos_seed",
    "CostoEtapa", "computar_costo_etapa", "computar_costeo_completo",
    # energia
    "BalanceEnergia",
    "FlujoEnergetico",
    "TipoEnergia",
    "computar_balance_energia",
    "flujos_seed",
    # agua
    "BalanceAgua",
    "FlujoAgua",
    "FuenteAgua",
    "DestinoAgua",
    "computar_balance_agua",
    "flujos_agua_seed",
    # rrhh
    "BalanceRRHH",
    "Trabajador",
    "AsignacionHoras",
    "computar_balance_rrhh",
    "trabajadores_seed",
    "asignaciones_seed",
    "detectar_alarmas",
    # integrado
    "BalanceIntegrado",
    "computar_balance_integrado",
]
