"""Knowledge Builder Agent - corre diariamente, aprende solo.

Tareas autonomas:
1. Procesar inbox (si hay archivos nuevos)
2. Re-sync al engine
3. Auditar coherencia y detectar nuevas inconsistencias
4. Generar reporte diario en logs/knowledge-builder-YYYYMMDD.md
5. Marcar nuevo snapshot de readiness en historico
6. Detectar gaps coherentes nuevos

Ejecucion: scripts/schedule_knowledge_builder.ps1 instala como Windows Task diaria.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "apps" / "engine"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ENGINE_URL = "https://trongkai-engine.fly.dev"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


def fetch_json(path: str, timeout: int = 30) -> dict | None:
    try:
        with urlopen(f"{ENGINE_URL}{path}", timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}


def post_json(path: str, body: dict, timeout: int = 30) -> dict | None:
    try:
        data = json.dumps(body).encode("utf-8")
        req = Request(f"{ENGINE_URL}{path}", data=data, method="POST",
                      headers={"Content-Type": "application/json"})
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}


def step_1_procesar_inbox() -> dict:
    """Step 1: corre procesar_inbox.py."""
    print("[Step 1/6] Procesando inbox...")
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "procesar_inbox.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        out = result.stdout[-500:] if result.stdout else ""
        return {"ok": result.returncode == 0, "tail": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def step_2_snapshot_readiness() -> dict:
    """Step 2: marcar snapshot de readiness con evento diario."""
    print("[Step 2/6] Marcando snapshot readiness...")
    fecha = datetime.now().strftime("%Y-%m-%d")
    r = post_json(f"/readiness/snapshot?evento=daily-{fecha}", {})
    if r and "entry" in r:
        return {"ok": True, "score": r["entry"]["score"]}
    return {"ok": False, "error": str(r)}


def step_3_health_check() -> dict:
    """Step 3: verificar salud del motor."""
    print("[Step 3/6] Health check...")
    r = fetch_json("/health/full")
    if not r or "_error" in r:
        return {"ok": False, "error": str(r)}
    return {
        "ok": r.get("salud_global_pct", 0) == 100,
        "salud_global": r.get("salud_global_pct"),
        "memory_mb": r.get("memory_mb"),
        "checks_failed": [c["nombre"] for c in r.get("health_checks", []) if not c["healthy"]],
    }


def step_4_alertas_y_coherencia() -> dict:
    """Step 4: detectar alertas y gaps nuevos."""
    print("[Step 4/6] Alertas + coherencia...")
    al = fetch_json("/alertas")
    coh = fetch_json("/matriz/coherencia")
    decisiones = fetch_json("/decisiones/top")
    return {
        "alertas_criticas": al.get("criticas", 0) if al else 0,
        "alertas_total": al.get("total", 0) if al else 0,
        "gaps_coherentes": coh.get("total_gaps", 0) if coh else 0,
        "decisiones_top": [
            {"titulo": a["titulo"], "owner": a["owner"], "prioridad": a["prioridad"]}
            for a in (decisiones.get("top_5", [])[:3] if decisiones else [])
        ],
    }


def step_5_commercial_intel() -> dict:
    """Step 5: insights comerciales del dia."""
    print("[Step 5/6] Commercial intel...")
    ci = fetch_json("/commercial/intelligence")
    if not ci or "_error" in ci:
        return {"ok": False}
    r = ci.get("resumen_ejecutivo", {})
    return {
        "ok": True,
        "revenue_5y": r.get("revenue_total_5y_usd"),
        "hhi": r.get("hhi_concentracion"),
        "skus_headroom": r.get("skus_con_headroom_alto"),
        "tech_npv": r.get("tech_npv_total_5y_usd"),
    }


def step_6_log_evento() -> dict:
    """Step 6: registrar evento knowledge builder en audit trail."""
    print("[Step 6/6] Log audit trail...")
    body = {
        "tipo": "snapshot_creado",
        "descripcion": f"Knowledge Builder daily run {datetime.now().isoformat()[:10]}",
        "actor": "knowledge-builder-bot",
        "metadata": {"automated": True, "schedule": "daily"},
    }
    r = post_json("/audit/log", body)
    return {"ok": "logged" in str(r)}


def generar_reporte_diario(resultados: dict, fecha: str) -> str:
    """Genera reporte markdown del dia."""
    md = f"""# Knowledge Builder Daily Report — {fecha}

Generado: {datetime.now().isoformat()}

## 1. Inbox Processing
- Estado: {'OK' if resultados['step_1']['ok'] else 'FAIL'}
- Tail output:
```
{resultados['step_1'].get('tail', '')[:300]}
```

## 2. Readiness Snapshot
- Score actual: **{resultados['step_2'].get('score', '?')}/100**

## 3. Health Check
- Salud global: **{resultados['step_3'].get('salud_global', '?')}%**
- Memory: {resultados['step_3'].get('memory_mb', '?')} MB
- Checks fallidos: {resultados['step_3'].get('checks_failed', [])}

## 4. Alertas + Coherencia
- Alertas criticas: **{resultados['step_4']['alertas_criticas']}**
- Total alertas: {resultados['step_4']['alertas_total']}
- Gaps coherentes: {resultados['step_4']['gaps_coherentes']}
- Top 3 decisiones del dia:
"""
    for d in resultados["step_4"]["decisiones_top"]:
        md += f"  - **{d['titulo']}** (owner: {d['owner']}, prioridad: {d['prioridad']:.1f})\n"

    md += f"""

## 5. Commercial Intelligence
- Revenue 5y proyectado: ${resultados['step_5'].get('revenue_5y', 0)/1e6:.1f}M USD
- HHI concentracion: {resultados['step_5'].get('hhi', 0)}
- SKUs con headroom alto: {resultados['step_5'].get('skus_headroom', 0)}
- Tech NPV total: ${resultados['step_5'].get('tech_npv', 0)/1e6:.2f}M USD

## 6. Audit Log
- Evento registrado: {'OK' if resultados['step_6']['ok'] else 'FAIL'}

---

_Reporte generado automaticamente por knowledge_builder.py_
_Para correr manual: `python scripts/knowledge_builder.py`_
"""
    return md


def main():
    fecha = datetime.now().strftime("%Y%m%d")
    print(f"=== Knowledge Builder Daily Run {fecha} ===")
    print()

    resultados = {}
    resultados["step_1"] = step_1_procesar_inbox()
    resultados["step_2"] = step_2_snapshot_readiness()
    resultados["step_3"] = step_3_health_check()
    resultados["step_4"] = step_4_alertas_y_coherencia()
    resultados["step_5"] = step_5_commercial_intel()
    resultados["step_6"] = step_6_log_evento()

    # Generar reporte
    reporte = generar_reporte_diario(resultados, fecha)
    log_file = LOG_DIR / f"knowledge-builder-{fecha}.md"
    log_file.write_text(reporte, encoding="utf-8")
    print()
    print(f"OK Reporte guardado en: {log_file}")
    print()

    # Resumen one-line
    score = resultados["step_2"].get("score", "?")
    alertas = resultados["step_4"]["alertas_total"]
    revenue = resultados["step_5"].get("revenue_5y", 0)
    print(f"SUMMARY: score={score}/100  alertas={alertas}  revenue_5y=${revenue/1e6:.1f}M")


if __name__ == "__main__":
    main()
