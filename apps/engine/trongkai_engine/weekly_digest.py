"""Weekly Digest — generador HTML Apple-style con resumen semanal.

Output: HTML standalone listo para mandar por email (inline CSS).

Incluye:
- Hero con score actual + delta semanal
- Top 3 acciones recomendadas
- 3 alertas más críticas
- Próximos hitos REP (próximos 30 días)
- Cambios al modelo en la semana (audit trail)
- KPIs financieros core
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _kpi_card_html(label: str, value: str, sub: str = "", color: str = "#1A8A1A") -> str:
    return f"""
    <td style="padding: 16px; border-radius: 12px; background: #F5F5F7; width: 25%; vertical-align: top;">
      <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: #86868B; font-weight: 600;">
        {label}
      </div>
      <div style="font-size: 28px; font-weight: 600; color: {color}; margin-top: 6px; letter-spacing: -0.022em;">
        {value}
      </div>
      <div style="font-size: 11px; color: #86868B; margin-top: 4px;">{sub}</div>
    </td>
    """


def generar_weekly_digest(
    snap: dict[str, Any],
    score_anterior: float | None = None,
    audit_entries_semana: list[dict] | None = None,
) -> str:
    """Genera el HTML del digest semanal."""
    now = datetime.now(timezone.utc)
    semana_iso = now.isocalendar()
    fecha = now.strftime("%d %B %Y")

    plan = snap.get("plan", {})
    kpis = plan.get("kpis", {})
    tir = (kpis.get("tir") or 0) * 100
    van = kpis.get("van") or 0
    val = snap.get("valuation", {})
    rs = snap.get("readiness_score", {}) or {}
    score = rs.get("score_total", 0)
    interp = rs.get("interpretacion", "")
    dec = snap.get("decisiones", {}) or {}
    top_acciones = dec.get("top_5", [])[:3]
    alr = snap.get("alertas", {}) or {}
    top_alertas = alr.get("alertas", [])[:3]
    dr = snap.get("data_room", {}) or {}
    vm = snap.get("variables_matrix", {}) or {}
    cmp_rep = snap.get("compliance_rep", {}) or {}

    delta_score = (score - score_anterior) if (score_anterior is not None) else None
    delta_str = ""
    delta_color = "#86868B"
    if delta_score is not None:
        if delta_score > 0:
            delta_str = f"↑ +{delta_score:.1f} pts vs semana anterior"
            delta_color = "#1A8A1A"
        elif delta_score < 0:
            delta_str = f"↓ {delta_score:.1f} pts vs semana anterior"
            delta_color = "#FF3B30"
        else:
            delta_str = "sin cambios vs semana anterior"

    # Top alertas HTML
    alertas_html = ""
    NIVEL_BG = {
        "critica": "#FFEBEA", "alta": "#FFF3E0", "media": "#FFFBEB",
        "baja": "#EAF6EA", "info": "#F5F5F7",
    }
    NIVEL_COLOR = {
        "critica": "#FF3B30", "alta": "#FF9500", "media": "#8B6F00",
        "baja": "#1A8A1A", "info": "#86868B",
    }
    if top_alertas:
        for a in top_alertas:
            nivel = a.get("nivel", "info")
            alertas_html += f"""
            <tr><td style="padding: 10px 14px; background: {NIVEL_BG.get(nivel, '#F5F5F7')}; border-left: 3px solid {NIVEL_COLOR.get(nivel, '#86868B')}; border-radius: 8px; margin-bottom: 6px;">
              <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; color: {NIVEL_COLOR.get(nivel, '#86868B')}; font-weight: 700;">{nivel}</div>
              <div style="font-size: 14px; color: #1D1D1F; font-weight: 600; margin-top: 2px;">{a.get('titulo', '')}</div>
              <div style="font-size: 12px; color: #515154; margin-top: 4px;">{a.get('accion_sugerida', '')}</div>
            </td></tr>
            <tr><td style="height: 8px;"></td></tr>
            """
    else:
        alertas_html = '<tr><td style="padding: 12px; color: #86868B; font-size: 13px;">✓ Sin alertas activas esta semana.</td></tr>'

    # Top acciones HTML
    acciones_html = ""
    for i, acc in enumerate(top_acciones, 1):
        acciones_html += f"""
        <tr><td style="padding: 12px 14px; background: #FFFFFF; border: 1px solid #E8E8ED; border-radius: 10px;">
          <table cellspacing="0" cellpadding="0" style="width: 100%;">
            <tr>
              <td style="width: 32px; vertical-align: top;">
                <div style="width: 28px; height: 28px; border-radius: 50%; background: #1A8A1A; color: white; text-align: center; line-height: 28px; font-size: 12px; font-weight: 700;">{i}</div>
              </td>
              <td>
                <div style="font-size: 14px; color: #1D1D1F; font-weight: 600;">{acc.get('titulo', '')}</div>
                <div style="font-size: 12px; color: #515154; margin-top: 4px;">{acc.get('accion_concreta', '')[:140]}</div>
                <div style="font-size: 11px; color: #86868B; margin-top: 6px;">👤 {acc.get('owner', '')} · 📈 +{acc.get('uplift_readiness', 0):.0f} pts · Quick-win {acc.get('quick_win', 0):.0f}</div>
              </td>
            </tr>
          </table>
        </td></tr>
        <tr><td style="height: 8px;"></td></tr>
        """
    if not acciones_html:
        acciones_html = '<tr><td style="padding: 12px; color: #86868B; font-size: 13px;">Sin acciones detectadas.</td></tr>'

    # Audit trail de la semana
    audit_html = ""
    if audit_entries_semana:
        for e in audit_entries_semana[:5]:
            audit_html += f"""
            <tr><td style="padding: 8px 14px; background: #F5F5F7; border-radius: 8px; font-size: 12px;">
              <span style="color: #86868B;">{e.get('timestamp', '')[:10]}</span>
              <span style="color: #1A8A1A; margin: 0 6px;">·</span>
              <span style="color: #1D1D1F; font-weight: 500;">{e.get('tipo', '')}</span>
              <div style="color: #515154; margin-top: 2px;">{e.get('descripcion', '')}</div>
            </td></tr>
            <tr><td style="height: 6px;"></td></tr>
            """
    else:
        audit_html = '<tr><td style="padding: 12px; color: #86868B; font-size: 13px;">Sin cambios registrados esta semana.</td></tr>'

    score_color = "#1A8A1A" if score >= 80 else ("#FF9500" if score >= 60 else "#FF3B30")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<title>Trongkai · Weekly Digest semana {semana_iso.week} {semana_iso.year}</title>
</head>
<body style="margin: 0; padding: 0; background: #F5F5F7; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Inter', system-ui, sans-serif; color: #1D1D1F; -webkit-font-smoothing: antialiased;">
<table cellspacing="0" cellpadding="0" style="width: 100%; max-width: 720px; margin: 0 auto; background: #FFFFFF;">
  <!-- Hero -->
  <tr><td style="padding: 40px 32px 24px;">
    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #1A8A1A; font-weight: 700;">Trongkai · Weekly Digest</div>
    <div style="font-size: 28px; font-weight: 600; letter-spacing: -0.022em; margin-top: 8px;">Semana {semana_iso.week} · {fecha}</div>
    <div style="font-size: 14px; color: #86868B; margin-top: 4px;">Resumen ejecutivo para directorio</div>
  </td></tr>

  <!-- Score -->
  <tr><td style="padding: 0 32px 24px;">
    <div style="background: #EAF6EA; border: 1px solid #C8E7C8; border-radius: 16px; padding: 28px; text-align: center;">
      <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #1A8A1A; font-weight: 600;">Investment Readiness Score</div>
      <div style="font-size: 64px; font-weight: 700; color: {score_color}; line-height: 1; margin-top: 8px; letter-spacing: -0.04em;">{score:.1f}</div>
      <div style="font-size: 14px; color: #515154; margin-top: 4px;">/ 100</div>
      <div style="font-size: 14px; color: #1D1D1F; font-weight: 600; margin-top: 12px;">{interp}</div>
      {f'<div style="font-size: 13px; color: {delta_color}; margin-top: 6px; font-weight: 500;">{delta_str}</div>' if delta_str else ''}
    </div>
  </td></tr>

  <!-- KPIs -->
  <tr><td style="padding: 0 32px 24px;">
    <table cellspacing="6" cellpadding="0" style="width: 100%;">
      <tr>
        {_kpi_card_html("TIR Proyecto", f"{tir:.1f}%", "Hurdle 15%")}
        {_kpi_card_html("VAN @ 18%", f"${van/1e9:.1f}B", "CLP")}
        {_kpi_card_html("EV exit 5y", f"${val.get('ev_base_clp', 0)/1e9:.0f}B", f"MOIC {val.get('moic', 0):.1f}×")}
        {_kpi_card_html("Compliance REP", f"{cmp_rep.get('vigentes', 0)}/{cmp_rep.get('total_hitos', 0)}", "hitos vigentes")}
      </tr>
    </table>
  </td></tr>

  <!-- Top Acciones -->
  <tr><td style="padding: 8px 32px 24px;">
    <div style="font-size: 18px; font-weight: 600; letter-spacing: -0.018em; margin-bottom: 12px;">🎯 Top 3 acciones recomendadas</div>
    <table cellspacing="0" cellpadding="0" style="width: 100%;">
      {acciones_html}
    </table>
  </td></tr>

  <!-- Alertas -->
  <tr><td style="padding: 8px 32px 24px;">
    <div style="font-size: 18px; font-weight: 600; letter-spacing: -0.018em; margin-bottom: 12px;">🚨 Alertas activas ({alr.get('total', 0)})</div>
    <table cellspacing="0" cellpadding="0" style="width: 100%;">
      {alertas_html}
    </table>
  </td></tr>

  <!-- Progreso modelo -->
  <tr><td style="padding: 8px 32px 24px;">
    <div style="font-size: 18px; font-weight: 600; letter-spacing: -0.018em; margin-bottom: 12px;">📊 Progreso del modelo</div>
    <table cellspacing="0" cellpadding="0" style="width: 100%; background: #F5F5F7; border-radius: 12px; padding: 16px;">
      <tr><td style="padding: 8px 16px;">
        <div style="font-size: 12px; color: #86868B;">Data Room avance</div>
        <div style="font-size: 22px; font-weight: 600;">{dr.get('pct_avance', 0):.0f}%</div>
        <div style="font-size: 11px; color: #86868B;">{dr.get('completos', 0)}/{dr.get('total', 0)} items</div>
      </td>
      <td style="padding: 8px 16px;">
        <div style="font-size: 12px; color: #86868B;">Matriz Variables cubierta</div>
        <div style="font-size: 22px; font-weight: 600;">{vm.get('pct_cubierto', 0):.0f}%</div>
        <div style="font-size: 11px; color: #86868B;">{vm.get('OK_PROVISORIO', 0)} OK* + {vm.get('OK_VALIDADO', 0)} OK</div>
      </td></tr>
    </table>
  </td></tr>

  <!-- Audit semanal -->
  <tr><td style="padding: 8px 32px 24px;">
    <div style="font-size: 18px; font-weight: 600; letter-spacing: -0.018em; margin-bottom: 12px;">📝 Cambios al modelo esta semana</div>
    <table cellspacing="0" cellpadding="0" style="width: 100%;">
      {audit_html}
    </table>
  </td></tr>

  <!-- CTA -->
  <tr><td style="padding: 16px 32px 40px;">
    <div style="background: #1A8A1A; border-radius: 14px; padding: 24px; text-align: center;">
      <div style="font-size: 16px; color: white; font-weight: 600; margin-bottom: 6px;">¿Quieres profundizar?</div>
      <div style="font-size: 13px; color: rgba(255,255,255,0.85); margin-bottom: 16px;">Toda la plataforma en vivo + LP Pack ZIP descargable.</div>
      <a href="https://trongkai-web.vercel.app/comando" style="display: inline-block; padding: 10px 20px; background: white; color: #1A8A1A; text-decoration: none; border-radius: 980px; font-size: 13px; font-weight: 600; margin: 4px;">⚡ Centro de Mando</a>
      <a href="https://trongkai-engine.fly.dev/api/lp-pack.zip" style="display: inline-block; padding: 10px 20px; background: rgba(255,255,255,0.15); color: white; text-decoration: none; border-radius: 980px; font-size: 13px; font-weight: 600; margin: 4px; border: 1px solid rgba(255,255,255,0.3);">📦 LP Pack ZIP</a>
    </div>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding: 24px 32px; text-align: center; background: #F5F5F7; border-top: 1px solid #E8E8ED;">
    <div style="font-size: 12px; color: #86868B; font-style: italic;">"En la naturaleza no existen los residuos, solo recursos."</div>
    <div style="font-size: 11px; color: #86868B; margin-top: 6px;">Trongkai · Innovación en Nutrición Circular · {fecha}</div>
  </td></tr>
</table>
</body>
</html>
"""
