"""Configuración del motor — variables de entorno tipadas."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://trongkai:trongkai_dev@localhost:5432/trongkai"
    redis_url: str = "redis://localhost:6379"
    log_level: str = "info"
    engine_api_key: str = "changeme-internal-only"

    # Tolerancia balance de masa (sobreescribe Supuesto.balance_tolerancia_pct si > 0)
    balance_tolerancia_pct: float = 0.005


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
