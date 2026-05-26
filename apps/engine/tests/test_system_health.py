"""Tests del system health."""

from __future__ import annotations

from trongkai_engine.system_health import health_checks, system_health_report


def test_health_checks_corre():
    checks = health_checks()
    assert len(checks) >= 5  # Al menos 5 checks


def test_health_checks_tienen_estructura():
    checks = health_checks()
    for c in checks:
        assert hasattr(c, "healthy")
        assert hasattr(c, "nombre")
        assert hasattr(c, "detalle")
        assert isinstance(c.healthy, bool)


def test_report_completo():
    r = system_health_report()
    assert "version" in r
    assert "uptime_seconds" in r
    assert "modulos_count" in r
    assert "health_checks" in r
    assert "salud_global_pct" in r
    assert "artifacts" in r
    assert 0 <= r["salud_global_pct"] <= 100


def test_modulos_count_no_trivial():
    r = system_health_report()
    # Hay al menos 30 módulos
    assert r["modulos_count"] >= 30


def test_health_check_basicos_healthy():
    """Plan builder + matriz variables + decision engine deben estar OK."""
    checks = health_checks()
    by_nombre = {c.nombre: c for c in checks}
    assert by_nombre["Plan Builder"].healthy
    assert by_nombre["Variables Matrix"].healthy
    assert by_nombre["Decision Engine"].healthy
