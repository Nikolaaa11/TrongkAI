"""Tests del módulo config — instanciación de Settings y defaults.

Cubre la línea 24 de `config.py` (`return Settings()` dentro de `get_settings()`),
que estaba sin tocar porque el resto de la suite stubea `main.get_settings`
directamente con un lambda y nunca invoca el `get_settings()` real.
"""

from __future__ import annotations

import importlib

from trongkai_engine import config


def test_get_settings_devuelve_instancia_settings():
    """`get_settings()` debe devolver una instancia válida de `Settings`."""
    # Limpiar caché por si otro test la pobló
    config.get_settings.cache_clear()
    s = config.get_settings()
    assert isinstance(s, config.Settings)


def test_get_settings_es_cacheado_lru():
    """`get_settings()` está decorado con `@lru_cache` → la misma instancia
    en llamadas sucesivas (mismo objeto, no sólo igual)."""
    config.get_settings.cache_clear()
    s1 = config.get_settings()
    s2 = config.get_settings()
    assert s1 is s2


def test_settings_defaults_documentados():
    """Los defaults de `Settings` son los documentados (sin .env real).

    No validamos `database_url` ni `redis_url` exactos porque pueden venir
    de variables de entorno locales; sí validamos los campos numéricos
    y el sentinel `engine_api_key='changeme-internal-only'` que controla
    el modo abierto vs autenticado.
    """
    # Reload para que pydantic-settings no use un .env cacheado de otros tests
    importlib.reload(config)
    s = config.Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.engine_api_key == "changeme-internal-only"
    assert s.log_level == "info"
    assert s.balance_tolerancia_pct == 0.005
