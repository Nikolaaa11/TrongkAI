"""LP Pack Generator — ZIP con todos los entregables listos para LP roadshow.

Contenido del ZIP:
- 01-Trongkai-Tearsheet-Ejecutivo.pdf       (PDF 3 páginas con readiness + DR + matriz)
- 02-Snapshot-Modelo.json                   (estado completo del modelo)
- 03-Readiness-Score.json                   (score detallado 10 dimensiones)
- 04-Data-Room-Checklist.json               (41 items DD)
- 05-Matriz-Variables.json                  (165 celdas modeladas)
- 06-Sensitivity-Heatmap.json               (49 sims 2D)
- README.txt                                (cómo usar el pack)

Output: bytes del ZIP listo para download.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime
from typing import Any


def generar_lp_pack(
    snap: dict[str, Any],
    readiness: dict[str, Any] | None = None,
    data_room: dict[str, Any] | None = None,
    matriz: dict[str, Any] | None = None,
    sensitivity: dict[str, Any] | None = None,
    pdf_bytes: bytes | None = None,
) -> bytes:
    """Genera el ZIP con todos los entregables.

    Args:
        snap: snapshot completo del modelo (de /api/snapshot)
        readiness: resultado de /readiness/score
        data_room: resultado de /data-room/checklist
        matriz: resultado de /variables/matrix
        sensitivity: resultado de /sensitivity/heatmap (opcional)
        pdf_bytes: bytes del PDF tearsheet (opcional)

    Returns:
        bytes del ZIP
    """
    buf = io.BytesIO()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # 01 - PDF tearsheet
        if pdf_bytes:
            zf.writestr("01-Trongkai-Tearsheet-Ejecutivo.pdf", pdf_bytes)

        # 02 - Snapshot modelo
        zf.writestr(
            "02-Snapshot-Modelo.json",
            json.dumps(snap, indent=2, ensure_ascii=False, default=str),
        )

        # 03 - Readiness
        if readiness:
            zf.writestr(
                "03-Readiness-Score.json",
                json.dumps(readiness, indent=2, ensure_ascii=False, default=str),
            )

        # 04 - Data Room
        if data_room:
            zf.writestr(
                "04-Data-Room-Checklist.json",
                json.dumps(data_room, indent=2, ensure_ascii=False, default=str),
            )

        # 05 - Matriz canónica
        if matriz:
            zf.writestr(
                "05-Matriz-Variables.json",
                json.dumps(matriz, indent=2, ensure_ascii=False, default=str),
            )

        # 06 - Sensitivity (opcional)
        if sensitivity:
            zf.writestr(
                "06-Sensitivity-Heatmap.json",
                json.dumps(sensitivity, indent=2, ensure_ascii=False, default=str),
            )

        # README
        readme = _readme_text(snap, readiness, data_room, matriz, timestamp)
        zf.writestr("README.txt", readme)

    return buf.getvalue()


def _readme_text(
    snap: dict,
    readiness: dict | None,
    data_room: dict | None,
    matriz: dict | None,
    timestamp: str,
) -> str:
    kpis = snap.get("plan", {}).get("kpis", {})
    val = snap.get("valuation", {})

    score = readiness.get("score_total") if readiness else None
    interp = readiness.get("interpretacion") if readiness else ""
    dr_pct = data_room.get("pct_avance") if data_room else None
    mat_pct = matriz.get("pct_cubierto") if matriz else None

    return f"""TRONGKAI — LP PACK
==================

Pack ejecutivo para Limited Partners / comité de inversión / DFI.
Generado: {timestamp}

ESTADO DEL MODELO
-----------------
  TIR proyecto:                  {(kpis.get('tir') or 0) * 100:.2f}%
  VAN @ WACC 18%:                ${(kpis.get('van') or 0) / 1e9:.2f}B CLP
  EV exit año 5:                 ${(val.get('ev_base_clp') or 0) / 1e9:.0f}B CLP
  MOIC:                          {val.get('moic') or 0:.2f}x
  Payback:                       {kpis.get('payback_meses') or '—'} meses
  EBITDA margin promedio:        {(kpis.get('ebitda_margin_promedio') or 0) * 100:.1f}%

INVESTMENT READINESS SCORE
--------------------------
  Score consolidado:             {score or '—'}/100
  Interpretación:                {interp}
  Data Room avance:              {dr_pct or '—'}%
  Matriz variables cobertura:    {mat_pct or '—'}%

CONTENIDO DEL PACK
------------------
  01-Trongkai-Tearsheet-Ejecutivo.pdf
       PDF profesional 3 páginas con logo, KPIs, valoración, escenarios,
       Monte Carlo, readiness score, data room, matriz canónica, carbono,
       compliance y macro Chile. Listo para mandar a LP.

  02-Snapshot-Modelo.json
       Estado completo del modelo en formato JSON. Útil para auditores y
       asesores que quieran auditar el modelo programáticamente.

  03-Readiness-Score.json
       Investment Readiness Score detallado: 10 dimensiones evaluadas,
       peso por dimensión, score 0-100, aporte total, detalle por celda.

  04-Data-Room-Checklist.json
       Due Diligence checklist: 41 items en 6 categorías (corporativo,
       financiero, comercial, operacional, ESG, equipo). Estado: faltante /
       parcial / completo + responsable + formato esperado.

  05-Matriz-Variables.json
       Matriz canónica del Excel original: 11 productos × 15 variables =
       165 celdas con estado PD / OK_PROVISORIO / OK_VALIDADO.

  06-Sensitivity-Heatmap.json (opcional)
       Análisis de sensibilidad 2D: TIR vs combinaciones de precio × costo
       MMPP. 49 simulaciones con zona segura identificada.

PLATAFORMA EN VIVO
------------------
  Web:      https://trongkai-web.vercel.app
  API:      https://trongkai-engine.fly.dev
  Swagger:  https://trongkai-engine.fly.dev/docs

CONTACTO
--------
  Nicolás Rietta — COO Trongkai
  nicolasrietta@gmail.com

CONFIDENCIALIDAD
----------------
Este pack contiene información confidencial sobre Trongkai. No distribuir
sin autorización del COO. Las proyecciones financieras están basadas en
supuestos OK_PROVISORIO calibrados con benchmarks; validación pendiente
del directorio.

"En la naturaleza no existen los residuos, solo recursos."
— Trongkai · 2026
"""
