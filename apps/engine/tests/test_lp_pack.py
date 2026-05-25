"""Tests del LP Pack ZIP generator."""

from __future__ import annotations

import io
import json
import zipfile

from trongkai_engine.lp_pack import generar_lp_pack


def _snap_minimo():
    return {
        "plan": {
            "kpis": {
                "tir": 0.30,
                "van": 5_000_000_000,
                "payback_meses": 52,
                "ebitda_margin_promedio": 0.45,
            },
        },
        "valuation": {
            "ebitda_ano5_clp": 14e9,
            "ev_base_clp": 131e9,
            "moic": 9.0,
        },
    }


def test_lp_pack_genera_zip():
    snap = _snap_minimo()
    zip_bytes = generar_lp_pack(snap=snap)
    # Magic bytes ZIP
    assert zip_bytes[:4] == b"PK\x03\x04"
    assert len(zip_bytes) > 100


def test_lp_pack_contiene_snapshot_y_readme():
    snap = _snap_minimo()
    zip_bytes = generar_lp_pack(snap=snap)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "02-Snapshot-Modelo.json" in names
        assert "README.txt" in names


def test_lp_pack_con_todos_archivos():
    snap = _snap_minimo()
    readiness = {"score_total": 80.0, "interpretacion": "BANKABLE", "dimensiones": []}
    data_room = {"items": [], "resumen": {"pct_avance": 50}}
    matriz = {"celdas": [], "stats": {"pct_cubierto": 42, "total": 165}}
    sens = {"celdas": []}

    zip_bytes = generar_lp_pack(
        snap=snap,
        readiness=readiness,
        data_room=data_room,
        matriz=matriz,
        sensitivity=sens,
        pdf_bytes=b"%PDF-1.4 dummy",
    )

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        assert "01-Trongkai-Tearsheet-Ejecutivo.pdf" in names
        assert "02-Snapshot-Modelo.json" in names
        assert "03-Readiness-Score.json" in names
        assert "04-Data-Room-Checklist.json" in names
        assert "05-Matriz-Variables.json" in names
        assert "06-Sensitivity-Heatmap.json" in names
        assert "README.txt" in names


def test_lp_pack_snapshot_json_parseable():
    snap = _snap_minimo()
    zip_bytes = generar_lp_pack(snap=snap)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        snap_json = json.loads(zf.read("02-Snapshot-Modelo.json"))
        assert snap_json["plan"]["kpis"]["tir"] == 0.30


def test_lp_pack_readme_contiene_metricas():
    snap = _snap_minimo()
    readiness = {"score_total": 84.7, "interpretacion": "BANKABLE", "dimensiones": []}
    zip_bytes = generar_lp_pack(snap=snap, readiness=readiness)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        readme = zf.read("README.txt").decode("utf-8")
        assert "TRONGKAI" in readme
        assert "84.7" in readme
        assert "30.00" in readme  # TIR
        assert "BANKABLE" in readme
