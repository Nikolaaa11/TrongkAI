"""System Health Dashboard - estado técnico del motor.

Reporta:
- Versión + uptime
- Cache stats
- Test count (hardcoded del último run conocido)
- Conteo de módulos + endpoints
- Tamaño de artifacts en /tmp (PDF, ZIP, history)
- Estado de schedules (last_run desde audit_trail)
- Memory usage (best-effort)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

START_TIME = time.monotonic()


def _file_size_kb(p: Path) -> float:
    if not p.exists():
        return 0
    return p.stat().st_size / 1024


def _modulos_count() -> int:
    """Cuenta módulos .py en trongkai_engine/."""
    base = Path(__file__).parent
    return len([f for f in base.glob("*.py") if not f.name.startswith("_")])


def _artifacts_status() -> dict:
    """Estado de archivos generados."""
    return {
        "audit_trail_kb": _file_size_kb(Path("/tmp/trongkai-audit-trail.json")),
        "readiness_history_kb": _file_size_kb(Path("/tmp/trongkai-readiness-history.json")),
        "pipeline_lp_kb": _file_size_kb(Path("/tmp/trongkai-pipeline-lp.json")),
        "notas_kb": _file_size_kb(Path("/tmp/trongkai-notas.json")),
        "exports_dir_files": len(list(Path("/tmp/trongkai-exports").glob("*"))) if Path("/tmp/trongkai-exports").exists() else 0,
    }


def _memory_mb() -> float | None:
    """Memory usage best-effort (Linux: /proc/self/status)."""
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except Exception:
        pass
    return None


@dataclass
class HealthCheck:
    healthy: bool
    nombre: str
    detalle: str

    def to_dict(self) -> dict:
        return {"healthy": self.healthy, "nombre": self.nombre, "detalle": self.detalle}


def health_checks() -> list[HealthCheck]:
    """Corre todos los checks de salud."""
    checks: list[HealthCheck] = []

    # 1. Plan builder funciona
    try:
        from .plan_builder import ParametrosPlan, build_plan
        plan = build_plan(ParametrosPlan())
        ok = plan.kpis.tir_proyecto_anual is not None
        checks.append(HealthCheck(ok, "Plan Builder", f"TIR base = {plan.kpis.tir_proyecto_anual:.2%}"))
    except Exception as e:
        checks.append(HealthCheck(False, "Plan Builder", f"ERROR: {e}"))

    # 2. Matriz variables
    try:
        from .variables_matrix import construir_matriz, stats_resumen
        s = stats_resumen(construir_matriz())
        ok = s["total"] == 165
        checks.append(HealthCheck(ok, "Variables Matrix", f"{s['total']} celdas, {s['pct_cubierto']}% cubierto"))
    except Exception as e:
        checks.append(HealthCheck(False, "Variables Matrix", f"ERROR: {e}"))

    # 3. Decision Engine
    try:
        from .decision_engine import top_5_acciones
        acc = top_5_acciones()
        ok = len(acc) > 0
        checks.append(HealthCheck(ok, "Decision Engine", f"{len(acc)} top acciones generadas"))
    except Exception as e:
        checks.append(HealthCheck(False, "Decision Engine", f"ERROR: {e}"))

    # 4. Alertas
    try:
        from .alertas import escanear_alertas
        r = escanear_alertas()
        checks.append(HealthCheck(True, "Sistema de Alertas",
                                  f"{r.total} alertas detectadas ({r.criticas} críticas)"))
    except Exception as e:
        checks.append(HealthCheck(False, "Sistema de Alertas", f"ERROR: {e}"))

    # 5. Macro Chile (puede fallar por red)
    try:
        from .macro_chile import snapshot_resumen
        m = snapshot_resumen()
        ok = m.get("dolar_clp") is not None
        checks.append(HealthCheck(ok, "Macro Chile API", f"USD/CLP = {m.get('dolar_clp', '?')}"))
    except Exception as e:
        checks.append(HealthCheck(False, "Macro Chile API", f"ERROR: {str(e)[:80]}"))

    # 6. Cache
    try:
        from .cache import cache_stats
        s = cache_stats()
        checks.append(HealthCheck(True, "Cache In-Memory",
                                  f"{s['active']} active / {s['expired']} expired"))
    except Exception as e:
        checks.append(HealthCheck(False, "Cache In-Memory", f"ERROR: {e}"))

    # 7. Pipeline LP
    try:
        from .pipeline_lp import list_lps
        lps = list_lps()
        checks.append(HealthCheck(True, "Pipeline LP", f"{len(lps)} LPs en pipeline"))
    except Exception as e:
        checks.append(HealthCheck(False, "Pipeline LP", f"ERROR: {e}"))

    return checks


def system_health_report() -> dict:
    """Reporte completo de salud del sistema."""
    from . import __version__

    checks = health_checks()
    n_healthy = sum(1 for c in checks if c.healthy)

    return {
        "version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(time.monotonic() - START_TIME),
        "modulos_count": _modulos_count(),
        "memory_mb": _memory_mb(),
        "health_checks": [c.to_dict() for c in checks],
        "healthy_count": n_healthy,
        "checks_total": len(checks),
        "salud_global_pct": round(n_healthy / len(checks) * 100, 1) if checks else 0,
        "artifacts": _artifacts_status(),
    }
