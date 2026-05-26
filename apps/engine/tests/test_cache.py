"""Tests del cache in-memory."""

from __future__ import annotations

import time

from trongkai_engine.cache import cache_stats, cached_ttl, clear_all


def test_cache_hit_misma_funcion():
    counter = {"calls": 0}

    @cached_ttl(seconds=5)
    def expensive():
        counter["calls"] += 1
        return counter["calls"]

    clear_all()
    expensive.cache_clear()  # type: ignore[attr-defined]

    r1 = expensive()
    r2 = expensive()
    r3 = expensive()
    # Solo 1 llamada real
    assert counter["calls"] == 1
    assert r1 == r2 == r3 == 1


def test_cache_expira():
    counter = {"calls": 0}

    @cached_ttl(seconds=1)
    def expensive():
        counter["calls"] += 1
        return counter["calls"]

    clear_all()
    expensive.cache_clear()  # type: ignore[attr-defined]

    r1 = expensive()
    assert counter["calls"] == 1
    time.sleep(1.1)
    r2 = expensive()
    # Re-ejecutado tras expirar
    assert counter["calls"] == 2
    assert r2 == 2


def test_cache_keys_diferentes_args():
    counter = {"calls": 0}

    @cached_ttl(seconds=5)
    def expensive(x: int):
        counter["calls"] += 1
        return x * 2

    clear_all()
    expensive.cache_clear()  # type: ignore[attr-defined]

    expensive(1)
    expensive(2)
    expensive(1)
    # 2 args distintos = 2 entries
    assert counter["calls"] == 2


def test_clear_all_vacia():
    @cached_ttl(seconds=60)
    def f():
        return 42

    f()
    n = clear_all()
    assert n >= 1
    stats = cache_stats()
    assert stats["total_entries"] == 0


def test_cache_stats():
    clear_all()

    @cached_ttl(seconds=60)
    def f():
        return "x"

    f()
    stats = cache_stats()
    assert stats["total_entries"] >= 1
    assert stats["active"] >= 1
