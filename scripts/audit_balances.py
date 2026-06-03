"""Audit autonomo de los 4 balances integrales.

Corre cada 6h por el schedule TrongkAI-BalancesAudit:
1. Llama /balance/integrado
2. Si alarmas criticas > 0 -> escribe logs/balances-alert-YYYYMMDD-HHMM.md
3. Genera reporte HTML resumen en entregables/Balances-YYYYMMDD-HHMM.html
4. Si hay alarma critica de horas extras, marca evento en audit_trail
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent.parent
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ENGINE_URL = "https://trongkai-engine.fly.dev"
LOG_DIR = ROOT / "logs"
ENTREGABLES_DIR = ROOT / "entregables"
LOG_DIR.mkdir(exist_ok=True)
ENTREGABLES_DIR.mkdir(exist_ok=True)


def fetch_json(path: str, timeout: int = 30) -> dict | None:
    try:
        with urlopen(f"{ENGINE_URL}{path}", timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}


def post_json(path: str, body: dict, timeout: int = 30) -> dict | None:
    try:
        data = json.dumps(body).encode("utf-8")
        req = Request(
            f"{ENGINE_URL}{path}", data=data, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"_error": str(e)}


def generar_html_resumen(integ: dict, ts: str) -> str:
    score = integ.get("score_eficiencia_global", 0)
    criticas = sum(
        1 for a in integ.get("alarmas_consolidadas", [])
        if a.get("severidad") == "critica"
    )
    altas = sum(
        1 for a in integ.get("alarmas_consolidadas", [])
        if a.get("severidad") == "alta"
    )
    bal = {b: integ.get(b, {}) for b in ("energia", "agua", "rrhh", "producto")}
    color_score = "#1a8a1a" if score >= 70 else "#c66200" if score >= 50 else "#d92626"

    rows_alarmas = ""
    for a in integ.get("alarmas_consolidadas", [])[:20]:
        sev = a.get("severidad", "media")
        color = {"critica": "#fee", "alta": "#ffe8d6"}.get(sev, "#f5f5f7")
        rows_alarmas += f"""<tr style="background:{color}">
            <td>[{a.get('balance', '?')}]</td>
            <td><strong>{sev.upper()}</strong></td>
            <td>{a.get('mensaje', '')}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="es-CL"><head><meta charset="UTF-8" /><title>Balances Trongkai {ts}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif;
       background:#fff; color:#1d1d1f; margin:0; padding:48px; max-width:1100px; margin:0 auto; }}
h1 {{ font-size:48px; font-weight:700; letter-spacing:-0.025em; }}
.score {{ font-size:96px; font-weight:700; color:{color_score}; line-height:1; }}
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin:32px 0; }}
.card {{ background:#fbfbfd; border:1px solid #f0f0f2; border-radius:18px; padding:24px; }}
.card h3 {{ font-size:14px; color:#6e6e73; text-transform:uppercase; margin:0 0 8px; }}
.card .v {{ font-size:32px; font-weight:700; }}
.card .a {{ font-size:12px; color:#1a8a1a; margin-top:6px; }}
.card .crit {{ color:#d92626; font-weight:600; }}
table {{ width:100%; border-collapse:collapse; margin-top:24px; font-size:14px; }}
th, td {{ padding:10px; text-align:left; border-bottom:1px solid #f0f0f2; }}
.eyebrow {{ color:#1a8a1a; text-transform:uppercase; font-size:13px; font-weight:600; letter-spacing:1.2px; }}
</style></head><body>
<p class="eyebrow">Audit autonomo · {ts}</p>
<h1>Balances Integrales Trongkai</h1>
<p style="color:#6e6e73; font-size:18px">Score global, alarmas activas y KPIs por dimension.</p>

<div style="text-align:center; padding:48px 0;">
  <div style="color:#6e6e73; font-size:14px;">Score Eficiencia Global</div>
  <div class="score">{score:.0f}<span style="font-size:32px;color:#a1a1a6">/100</span></div>
</div>

<div class="grid">
  <div class="card">
    <h3>Producto</h3>
    <div class="v">{bal['producto'].get('produccion_anual_kg', 0)/1000:.0f}t/año</div>
    <div class="a">Closure {bal['producto'].get('closure_pct', 0):.2f}%</div>
  </div>
  <div class="card">
    <h3>Energia</h3>
    <div class="v">{bal['energia'].get('consumo_total_anual_mwh', 0):.0f} MWh</div>
    <div class="a">Mix renovable {bal['energia'].get('mix_renovable_pct', 0)*100:.0f}% · {len(bal['energia'].get('alarmas', []))} alarmas</div>
  </div>
  <div class="card">
    <h3>Agua</h3>
    <div class="v">{bal['agua'].get('consumo_total_anual_m3', 0):.0f} m³</div>
    <div class="a">Recirc {bal['agua'].get('agua_recirculada_pct', 0)*100:.0f}% · {len(bal['agua'].get('alarmas', []))} alarmas</div>
  </div>
  <div class="card">
    <h3>RRHH</h3>
    <div class="v">{bal['rrhh'].get('utilizacion_pct', 0)*100:.0f}%</div>
    <div class="a {'crit' if any(a.get('severidad')=='critica' for a in bal['rrhh'].get('alarmas', [])) else ''}">
      {len([a for a in bal['rrhh'].get('alarmas', []) if a.get('severidad')=='critica'])} criticas HH
    </div>
  </div>
</div>

<h2 style="margin-top:48px;">Alarmas activas ({criticas} criticas, {altas} altas)</h2>
<table>
  <thead><tr><th>Balance</th><th>Severidad</th><th>Mensaje</th></tr></thead>
  <tbody>{rows_alarmas or '<tr><td colspan=3 style="color:#1a8a1a">Sin alarmas activas.</td></tr>'}</tbody>
</table>

<p style="margin-top:48px; font-size:12px; color:#a1a1a6">
Generado automaticamente por audit_balances.py · {ts} · Trongkai Platform
</p>
</body></html>"""


def main():
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    print(f"=== Balances Audit {ts} ===")

    integ = fetch_json("/balance/integrado")
    if not integ or "_error" in integ:
        print(f"ERROR fetch /balance/integrado: {integ}")
        return 1

    score = integ.get("score_eficiencia_global", 0)
    criticas = [a for a in integ.get("alarmas_consolidadas", []) if a.get("severidad") == "critica"]
    altas = [a for a in integ.get("alarmas_consolidadas", []) if a.get("severidad") == "alta"]

    print(f"Score global: {score:.1f}/100")
    print(f"Alarmas criticas: {len(criticas)}")
    print(f"Alarmas altas: {len(altas)}")

    # HTML resumen
    html_path = ENTREGABLES_DIR / f"Balances-{ts}.html"
    html_path.write_text(generar_html_resumen(integ, ts), encoding="utf-8")
    print(f"OK HTML resumen: {html_path}")

    # Alert MD si hay criticas
    if criticas:
        alert_path = LOG_DIR / f"balances-alert-{ts}.md"
        md = f"""# ALERTA Balances Trongkai — {ts}

Score eficiencia: **{score:.0f}/100**

## {len(criticas)} ALARMAS CRITICAS

"""
        for a in criticas:
            md += f"- **[{a.get('balance', '?')}]** {a.get('mensaje', '')}\n"
            if a.get("accion"):
                md += f"  - Accion: {a['accion']}\n"
        if altas:
            md += f"\n## {len(altas)} altas\n\n"
            for a in altas:
                md += f"- [{a.get('balance', '?')}] {a.get('mensaje', '')}\n"
        alert_path.write_text(md, encoding="utf-8")
        print(f"ALERTA escrita: {alert_path}")

        # Audit trail
        post_json("/audit/log", {
            "tipo": "alarma_critica_balance",
            "descripcion": f"Audit balances detecto {len(criticas)} alarmas criticas",
            "actor": "audit_balances",
            "metadata": {"score": score, "criticas": len(criticas)},
        })

    print(f"SUMMARY: score={score:.0f}/100 criticas={len(criticas)} altas={len(altas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
