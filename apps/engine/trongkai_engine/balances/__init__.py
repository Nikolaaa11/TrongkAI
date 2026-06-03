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

__all__ = [
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
