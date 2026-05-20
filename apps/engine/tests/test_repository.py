"""Tests del módulo repository — partes que no requieren Postgres real.

Cubre:
- `_require_dsn()` cuando `DATABASE_URL` no está definido (rama de error).
- `_with_mmpp_defaults()`: merge de defaults sin pisar valores provistos.
- `DatabaseUnavailableError` es subclase de `RuntimeError` y tiene alias
  retro-compatible `DatabaseUnavailable`.
- `connect()` propaga `DatabaseUnavailableError` cuando no hay DSN.

Las funciones de I/O contra Postgres (upsert_*, list_*, snapshot_plan) no se
cubren acá porque requieren una DB de integración — quedan para tests e2e.
"""

from __future__ import annotations

import pytest

from trongkai_engine import repository


def test_database_unavailable_es_runtime_error():
    """`DatabaseUnavailableError` debe heredar de `RuntimeError` para que el
    caller pueda atraparlo con `except RuntimeError` si quiere."""
    assert issubclass(repository.DatabaseUnavailableError, RuntimeError)


def test_database_unavailable_alias_retrocompat():
    """`DatabaseUnavailable` es alias retro-compatible que apunta a la misma
    clase (documentado en el comentario del módulo)."""
    assert repository.DatabaseUnavailable is repository.DatabaseUnavailableError


def test_require_dsn_sin_database_url_lanza(monkeypatch):
    """Sin `DATABASE_URL` en el entorno, `_require_dsn()` debe lanzar
    `DatabaseUnavailableError` con mensaje explícito (no un KeyError genérico)."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(repository.DatabaseUnavailableError, match="DATABASE_URL"):
        repository._require_dsn()


def test_connect_sin_database_url_lanza(monkeypatch):
    """El context manager `connect()` propaga el mismo error si no hay DSN
    (no debería abrir conexión silenciosa contra un default)."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(repository.DatabaseUnavailableError):
        with repository.connect():
            pass  # pragma: no cover - nunca entra si lanza antes


def test_with_mmpp_defaults_completa_campos_opcionales():
    """`_with_mmpp_defaults` debe agregar las claves opcionales con sus
    defaults documentados cuando el item no las trae."""
    item = {"codigo": "TOMATE", "nombre": "Tomate industrial"}
    out = repository._with_mmpp_defaults(item)
    assert out["aceiteExtraiblePct"] == 0.0
    assert out["licopenoPct"] == 0.0
    assert out["pectinaPct"] == 0.0
    assert out["tiempoDescomposicionH"] is None
    assert out["notas"] is None
    # Y mantiene los campos originales
    assert out["codigo"] == "TOMATE"
    assert out["nombre"] == "Tomate industrial"


def test_with_mmpp_defaults_no_pisa_valores_explicitos():
    """Si el item ya trae `licopenoPct`, el default 0.0 NO debe pisarlo."""
    item = {
        "codigo": "TOMATE",
        "nombre": "Tomate",
        "licopenoPct": 0.012,
        "notas": "Variedad H9888",
    }
    out = repository._with_mmpp_defaults(item)
    assert out["licopenoPct"] == 0.012
    assert out["notas"] == "Variedad H9888"
    # Los otros opcionales sí toman default
    assert out["aceiteExtraiblePct"] == 0.0
    assert out["tiempoDescomposicionH"] is None
