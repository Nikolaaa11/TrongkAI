"""Generador de tearsheet PDF para roadshow / directorio / LP DD.

Usa reportlab (sin browser, sin Chromium, deploy-friendly en Fly.io).
Paleta Trongkai: oliva oscuro #3F4A2B, oliva medio #7C8857, trigo #C8A961,
borgoña #7A1F1F, papel #FEFCF6.

Recibe el dict de /api/snapshot y produce un PDF A4 de ~3 páginas con:
- Header con logo + título + fecha
- KPIs grandes (TIR, VAN, Payback, EBITDA margin)
- Valoración exit + MOIC
- Recomendación estratégica entre 3 escenarios
- Monte Carlo bandas de confianza
- Carbono baseline + BECCS
- Próximos hitos regulatorios
- Disclaimer + fuente
"""

from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Ruta al logo (PNG) — empaquetado junto al módulo
ASSETS_DIR = Path(__file__).parent / "assets"
LOGO_COLOR_PATH = ASSETS_DIR / "logo-trongkai-color.png"
ICON_PATH = ASSETS_DIR / "icon-trongkai.png"


def _header_logo(width_cm: float = 5.5) -> RLImage | None:
    """Devuelve el logo Trongkai en color como Flowable. None si no existe."""
    if not LOGO_COLOR_PATH.exists():
        return None
    # Aspect ratio del logo: 2977 x 512 ≈ 5.81:1
    aspect_ratio = 512 / 2977
    img = RLImage(str(LOGO_COLOR_PATH))
    img.drawWidth = width_cm * cm
    img.drawHeight = width_cm * cm * aspect_ratio
    return img

# Paleta Trongkai
OLIVA_OSCURO = colors.HexColor("#3F4A2B")
OLIVA_MEDIO = colors.HexColor("#7C8857")
TRIGO = colors.HexColor("#C8A961")
BORGONA = colors.HexColor("#7A1F1F")
TIERRA = colors.HexColor("#8B5A3C")
PAPEL = colors.HexColor("#FEFCF6")
GRIS_SUAVE = colors.HexColor("#E8E5DD")


def _fmt_b(n: float | None) -> str:
    if n is None:
        return "—"
    return f"${n / 1e9:,.2f}B CLP"


def _fmt_pct(n: float | None) -> str:
    if n is None:
        return "—"
    return f"{n * 100:.2f}%"


def _fmt_ton(n: float) -> str:
    return f"{n:,.0f} ton".replace(",", ".")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TKTitle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=22, textColor=OLIVA_OSCURO, alignment=0, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "TKSubtitle", parent=base["Normal"], fontName="Helvetica",
            fontSize=10, textColor=OLIVA_MEDIO, spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "TKH2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=13, textColor=OLIVA_OSCURO, spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "TKBody", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, textColor=colors.black, leading=12,
        ),
        "small": ParagraphStyle(
            "TKSmall", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, textColor=OLIVA_MEDIO, leading=9.5,
        ),
        "kpi_label": ParagraphStyle(
            "TKKpiLabel", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, textColor=OLIVA_MEDIO, alignment=1,
        ),
        "kpi_value": ParagraphStyle(
            "TKKpiValue", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=15, textColor=OLIVA_OSCURO, alignment=1,
        ),
        "kpi_value_hl": ParagraphStyle(
            "TKKpiValueHL", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=15, textColor=TRIGO, alignment=1,
        ),
    }


def _kpi_cards(snap: dict, st: dict) -> Table:
    """Fila de 5 KPI cards grandes."""
    k = snap["plan"]["kpis"]
    val = snap["valuation"]
    cells = [
        [
            Paragraph("TIR Proyecto", st["kpi_label"]),
            Paragraph("VAN @ WACC 18%", st["kpi_label"]),
            Paragraph("Payback", st["kpi_label"]),
            Paragraph("EBITDA margin", st["kpi_label"]),
            Paragraph("MOIC exit 5y", st["kpi_label"]),
        ],
        [
            Paragraph(_fmt_pct(k["tir"]), st["kpi_value_hl"]),
            Paragraph(_fmt_b(k["van"]), st["kpi_value"]),
            Paragraph(f'{k["payback_meses"] or "—"} meses', st["kpi_value"]),
            Paragraph(_fmt_pct(k["ebitda_margin_promedio"]), st["kpi_value"]),
            Paragraph(f'{val["moic"]:.1f}x' if val.get("moic") else "—", st["kpi_value_hl"]),
        ],
    ]
    t = Table(cells, colWidths=[3.4 * cm] * 5, rowHeights=[0.5 * cm, 1.1 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAPEL),
        ("BOX", (0, 0), (-1, -1), 0.5, OLIVA_MEDIO),
        ("LINEAFTER", (0, 0), (-2, -1), 0.3, GRIS_SUAVE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _tabla_anual(snap: dict) -> Table:
    """EERR resumido por año."""
    plan = snap["plan"]
    ingresos = plan["ingresos_anuales"]
    ebitda = plan["ebitda_anuales"]
    capex = plan["capex_anuales"]
    rows = [["Año", "Ingresos", "EBITDA", "EBITDA %", "CapEx"]]
    for i, (ing, ebi, cap) in enumerate(zip(ingresos, ebitda, capex), 1):
        margin = (ebi / ing * 100) if ing else 0
        rows.append([
            f"A{i}",
            f"${ing / 1e9:.2f}B",
            f"${ebi / 1e9:.2f}B",
            f"{margin:.1f}%",
            f"${cap / 1e9:.2f}B",
        ])
    rows.append([
        "Total 5y",
        f"${sum(ingresos) / 1e9:.2f}B",
        f"${sum(ebitda) / 1e9:.2f}B",
        "—",
        f"${sum(capex) / 1e9:.2f}B",
    ])
    t = Table(rows, colWidths=[2.5 * cm] + [3.0 * cm] * 4)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), OLIVA_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), PAPEL),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, -1), (-1, -1), GRIS_SUAVE),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, OLIVA_OSCURO),
        ("LINEABOVE", (0, -1), (-1, -1), 0.5, OLIVA_OSCURO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [PAPEL, colors.white]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _tabla_escenarios(snap: dict) -> Table:
    escs = snap["escenarios_estrategicos"]["escenarios"]
    rec = snap["escenarios_estrategicos"]["recomendacion"]
    rows = [["Escenario", "CapEx 5y", "TIR", "VAN", "Payback"]]
    for e in escs:
        marker = " ★" if e["nombre"] == rec["elegido"] else ""
        rows.append([
            f'{e["nombre"]}{marker}',
            f'${e["capex_total"] / 1e9:.1f}B',
            _fmt_pct(e["tir"]),
            f'${e["van"] / 1e9:.2f}B',
            f'{e["payback_meses"] or "—"} m',
        ])
    t = Table(rows, colWidths=[4.0 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.0 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), OLIVA_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), PAPEL),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 2), (-1, 2), TRIGO.clone(alpha=0.3)),  # destaca INDUSTRIAL si es la rec
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PAPEL, colors.white, PAPEL]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _tabla_mc(snap: dict, st: dict) -> Table:
    mc = snap["monte_carlo_integrado"]
    rows = [
        [Paragraph("<b>Monte Carlo integrado (precios + clima)</b>", st["body"]), ""],
        ["Corridas", f'{mc["n_runs"]:,}'.replace(",", ".")],
        ["TIR P5 (peor 5%)", _fmt_pct(mc["tir_p5"])],
        ["TIR P50 (mediana)", _fmt_pct(mc["tir_p50"])],
        ["TIR P95 (mejor 5%)", _fmt_pct(mc["tir_p95"])],
        ["Prob TIR > WACC", _fmt_pct(mc["prob_tir_supera_wacc"])],
        ["Prob VAN > 0", _fmt_pct(mc["prob_van_positivo"])],
        ["Años con evento crítico promedio", f'{mc["promedio_anos_critico"]:.2f} / 5'],
    ]
    t = Table(rows, colWidths=[8.5 * cm, 4.5 * cm])
    t.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), OLIVA_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), PAPEL),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PAPEL, colors.white]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _tabla_carbono(snap: dict, st: dict) -> Table:
    c = snap["carbon_footprint"]
    rows = [
        [Paragraph("<b>Footprint carbono · LCA</b>", st["body"]), "", ""],
        ["Escenario", "Emisiones netas 5y", "Revenue créditos 5y"],
        ["Baseline", _fmt_ton(c["baseline"]["emisiones_netas_5y_ton"]), _fmt_b(c["baseline"]["revenue_creditos_5y_clp"])],
        ["BECCS (futuro)", _fmt_ton(c["beccs"]["emisiones_netas_5y_ton"]), _fmt_b(c["beccs"]["revenue_creditos_5y_clp"])],
    ]
    t = Table(rows, colWidths=[4.5 * cm, 4.5 * cm, 4.5 * cm])
    t.setStyle(TableStyle([
        ("SPAN", (0, 0), (2, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), OLIVA_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), PAPEL),
        ("BACKGROUND", (0, 1), (-1, 1), GRIS_SUAVE),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8.5),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _tabla_compliance(snap: dict, st: dict) -> Table:
    rep = snap["compliance_rep"]
    rows = [[Paragraph("<b>Próximos hitos regulatorios (Ley REP)</b>", st["body"]), "", ""]]
    rows.append(["Hito", "Vigor", "Severidad"])
    for h in rep["proximos_3"]:
        nombre = h["nombre"][:60] + ("…" if len(h["nombre"]) > 60 else "")
        rows.append([nombre, h["fecha_vigor"], h["severidad"]])
    t = Table(rows, colWidths=[8.5 * cm, 2.5 * cm, 2.5 * cm])
    t.setStyle(TableStyle([
        ("SPAN", (0, 0), (2, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), OLIVA_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), PAPEL),
        ("BACKGROUND", (0, 1), (-1, 1), GRIS_SUAVE),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 2), (-1, -1), [PAPEL, colors.white, PAPEL]),
    ]))
    return t


def generar_tearsheet_pdf(snap: dict) -> bytes:
    """Genera el PDF y devuelve bytes."""
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
        title="Trongkai · Tearsheet ejecutivo",
        author="TrongkAI Platform",
    )

    story: list[Any] = []
    fecha = datetime.now().strftime("%d %B %Y, %H:%M")
    macro = snap.get("macro_chile", {})

    # === Header con logo ===
    logo = _header_logo(width_cm=5.0)
    if logo is not None:
        # Tabla 2 columnas: logo izquierda + título derecha
        header_tbl = Table(
            [[
                logo,
                [
                    Paragraph("Tearsheet Ejecutivo", st["title"]),
                    Paragraph(
                        f"Innovación en Nutrición Circular · Plan 5 Años · Generado {fecha}",
                        st["subtitle"],
                    ),
                ],
            ]],
            colWidths=[5.5 * cm, 12.0 * cm],
        )
        header_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_tbl)
        story.append(Spacer(1, 6 * mm))
    else:
        # Fallback sin logo
        story.append(Paragraph("Trongkai · Tearsheet Ejecutivo", st["title"]))
        story.append(Paragraph(
            f"Innovación en Nutrición Circular · Plan 5 Años · Generado {fecha}",
            st["subtitle"],
        ))

    # === KPIs grandes ===
    story.append(_kpi_cards(snap, st))
    story.append(Spacer(1, 6 * mm))

    # === Valoración ===
    val = snap["valuation"]
    story.append(Paragraph("Valoración exit año 5", st["h2"]))
    val_body = (
        f"EBITDA año 5 estimado <b>${val['ebitda_ano5_clp'] / 1e9:.2f}B CLP</b>. "
        f"Aplicando múltiplo food processing global <b>{val['multiplo_base']:.2f}x</b> (Damodaran 2026), "
        f"<b>EV base ${val['ev_base_clp'] / 1e9:.1f}B CLP</b> "
        f"(rango ${val['ev_rango_clp'][0] / 1e9:.0f}B – ${val['ev_rango_clp'][1] / 1e9:.0f}B). "
        f"MOIC sobre CapEx total 5y: <b>{val['moic']:.2f}x</b>."
    )
    story.append(Paragraph(val_body, st["body"]))
    story.append(Spacer(1, 4 * mm))

    # === Tabla anual ===
    story.append(Paragraph("EERR resumido por año", st["h2"]))
    story.append(_tabla_anual(snap))
    story.append(Spacer(1, 4 * mm))

    # === Escenarios estratégicos ===
    rec = snap["escenarios_estrategicos"]["recomendacion"]
    story.append(Paragraph("Recomendación estratégica de escala", st["h2"]))
    story.append(Paragraph(
        f"<b>Recomendado: {rec['elegido']}</b> — {rec['razon']}",
        st["body"],
    ))
    story.append(Spacer(1, 3 * mm))
    story.append(_tabla_escenarios(snap))

    story.append(PageBreak())

    # === Análisis de riesgo ===
    story.append(Paragraph("Análisis de riesgo integrado", st["h2"]))
    story.append(_tabla_mc(snap, st))
    story.append(Spacer(1, 4 * mm))

    # === Top sensibilidades tornado ===
    tornado_top = snap.get("top_3_tornado", [])
    if tornado_top:
        story.append(Paragraph("Top 3 sensibilidades TIR (±20%)", st["h2"]))
        rows = [["Variable", "TIR shock -20%", "TIR shock +20%", "Magnitud"]]
        for s in tornado_top:
            rows.append([
                s["variable"],
                _fmt_pct(s["tir_baja"]),
                _fmt_pct(s["tir_alta"]),
                f'{s["magnitud_tir"] * 100:.1f} pp',
            ])
        t = Table(rows, colWidths=[5.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), OLIVA_OSCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), PAPEL),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PAPEL, colors.white]),
        ]))
        story.append(t)
        story.append(Spacer(1, 5 * mm))

    # === Carbono + Compliance ===
    story.append(Paragraph("Impacto ESG y compliance", st["h2"]))
    story.append(_tabla_carbono(snap, st))
    story.append(Spacer(1, 4 * mm))
    story.append(_tabla_compliance(snap, st))

    # === Macro Chile context ===
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Contexto macroeconómico Chile", st["h2"]))
    if macro:
        macro_text = (
            f"Tipo de cambio observado: <b>${macro.get('dolar_clp', '—')} CLP/USD</b>. "
            f"UF: ${macro.get('uf_clp', '—')}. "
            f"TPM: {macro.get('tpm_pct', '—')}%. "
            f"IPC mensual: {macro.get('ipc_pct_mensual', '—')}%. "
            f"Desempleo: {macro.get('tasa_desempleo_pct', '—')}%. "
            f"Fuente: {macro.get('fuente', '—')}. "
            f"<br/>VAN del plan en USD ≈ <b>USD {snap['plan']['kpis']['van'] / (macro.get('dolar_clp', 920) or 920) / 1e6:.2f}M</b>."
        )
        story.append(Paragraph(macro_text, st["body"]))

    # === Footer ===
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        f'Generado por TrongkAI Platform v{snap.get("version", "?")} · '
        f'{snap.get("generated_at", "")[:19]} · '
        '"En la naturaleza no existen los residuos, solo recursos."',
        st["small"],
    ))
    story.append(Paragraph(
        "Datos calibrados con 27 papers peer-reviewed (Damodaran 2026, Scielo sector pesca-acuicultura Chile, "
        "ACS Sustainable Chem Eng, IPCC, mindicador.cl). "
        "Material confidencial · Trongkai Feed + Trongkai Food + Servicios Tecnológicos. "
        "TIR y proyecciones basadas en supuestos OK_PROVISORIO — validación José Cuevas / "
        "Jaime Echeverría / directorio pendiente.",
        st["small"],
    ))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
