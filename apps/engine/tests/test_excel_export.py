"""Tests del export Excel del Plan 5 Años."""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

from trongkai_engine.excel_export import export_plan_to_excel
from trongkai_engine.plan_builder import build_plan


@pytest.fixture
def temp_xlsx(tmp_path: Path) -> Path:
    return tmp_path / "plan.xlsx"


def test_export_genera_archivo(temp_xlsx):
    plan = build_plan()
    path = export_plan_to_excel(plan, temp_xlsx)
    assert path.exists()
    assert path.stat().st_size > 5000


def test_export_tiene_4_hojas(temp_xlsx):
    plan = build_plan()
    export_plan_to_excel(plan, temp_xlsx)
    wb = openpyxl.load_workbook(temp_xlsx)
    assert "Supuestos" in wb.sheetnames
    assert "EERR_Mensual" in wb.sheetnames
    assert "KPIs" in wb.sheetnames
    assert "Resumen_Anual" in wb.sheetnames


def test_eerr_tiene_60_filas_de_datos(temp_xlsx):
    plan = build_plan()
    export_plan_to_excel(plan, temp_xlsx)
    wb = openpyxl.load_workbook(temp_xlsx)
    ws = wb["EERR_Mensual"]
    # Encabezado fila 3 + 60 meses + total
    primer_mes = ws.cell(row=4, column=1).value
    mes_60 = ws.cell(row=63, column=1).value
    assert primer_mes == 1
    assert mes_60 == 60


def test_kpis_se_escribe(temp_xlsx):
    plan = build_plan()
    export_plan_to_excel(plan, temp_xlsx)
    wb = openpyxl.load_workbook(temp_xlsx)
    ws = wb["KPIs"]
    rows_text = [ws.cell(row=r, column=1).value for r in range(1, 10)]
    assert any("TIR" in (t or "") for t in rows_text)
    assert any("VAN" in (t or "") for t in rows_text)
    assert any("Payback" in (t or "") for t in rows_text)
