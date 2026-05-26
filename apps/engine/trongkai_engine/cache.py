"""Simple in-memory TTL cache para endpoints caros del motor.

Sin dependencias externas. Solo un dict con timestamps.

Uso:
    @cached_ttl(seconds=300)
    def costly_function():
        ...

Performance objetivo:
- /api/snapshot: 5s → <50ms (en cache)
- /decisiones/top: 1s → <50ms
- /readiness/score: 4s → <50ms
"""

from __future__ import annotations

import threading
import time
from functools import wraps
from typing import Any, Callable

_cache: dict[str, tuple[float, Any]] = {}
_lock = threading.Lock()


def cached_ttl(seconds: int = 300):
    """Decorator que cachea el resultado por N segundos."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Cache key: function name + args + kwargs (simplified)
            key = f"{fn.__module__}.{fn.__name__}:{args}:{tuple(sorted(kwargs.items()))}"
            now = time.monotonic()

            with _lock:
                if key in _cache:
                    expires_at, value = _cache[key]
                    if now < expires_at:
                        return value
                    # Expirado
                    del _cache[key]

            # Calcular
            result = fn(*args, **kwargs)

            with _lock:
                _cache[key] = (now + seconds, result)

            return result
        # Permitir invalidación manual
        wrapper.cache_clear = lambda: _clear_for_function(fn)  # type: ignore[attr-defined]
        return wrapper
    return decorator


def _clear_for_function(fn: Callable) -> None:
    """Limpia todos los entries de una función específica."""
    prefix = f"{fn.__module__}.{fn.__name__}:"
    with _lock:
        keys_to_remove = [k for k in _cache if k.startswith(prefix)]
        for k in keys_to_remove:
            del _cache[k]


def clear_all() -> int:
    """Limpia todo el cache. Devuelve número de entries eliminadas."""
    with _lock:
        n = len(_cache)
        _cache.clear()
    return n


def cache_stats() -> dict[str, Any]:
    """Stats del cache para debugging."""
    now = time.monotonic()
    with _lock:
        active = sum(1 for exp, _ in _cache.values() if exp > now)
        expired = len(_cache) - active
        # Top 5 keys por TTL restante
        details = sorted(
            [
                {
                    "key": k.split(":")[0][:60],
                    "ttl_restante": max(0, int(exp - now)),
                    "expirado": exp <= now,
                }
                for k, (exp, _) in _cache.items()
            ],
            key=lambda x: -x["ttl_restante"],
        )[:10]
    return {
        "total_entries": len(details),
        "active": active,
        "expired": expired,
        "top_entries": details,
    }
