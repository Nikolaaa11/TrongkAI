"""Tests de la matriz canónica 11 productos × 15 variables."""

from __future__ import annotations

from trongkai_engine.variables_matrix import (
    PRODUCTOS,
    VARIABLES,
    EstadoCelda,
    construir_matriz,
    stats_resumen,
)


def test_productos_son_11():
    assert len(PRODUCTOS) == 11


def test_variables_son_15():
    assert len(VARIABLES) == 15


def test_matriz_completa_11x15():
    m = construir_matriz()
    # 11 productos × 15 variables = 165 celdas
    assert len(m.celdas) == 11 * 15
    assert len(m.celdas) == 165


def test_todas_las_celdas_tienen_estado_valido():
    m = construir_matriz()
    estados_validos = {EstadoCelda.PD, EstadoCelda.OK_PROVISORIO, EstadoCelda.OK_VALIDADO}
    for c in m.celdas:
        assert c.estado in estados_validos


def test_estadisticas_correctas():
    s = stats_resumen(construir_matriz())
    assert s["total"] == 165
    assert s["PD"] + s["OK_PROVISORIO"] + s["OK_VALIDADO"] == 165
    # Pct cubierto debe estar entre 0 y 100
    assert 0 <= s["pct_cubierto"] <= 100


def test_serializa_to_dict():
    m = construir_matriz()
    d = m.to_dict()
    assert "productos" in d
    assert "variables" in d
    assert "celdas" in d
    assert "stats" in d
    assert len(d["productos"]) == 11
    assert len(d["variables"]) == 15
    assert len(d["celdas"]) == 165


def test_grupos_productos():
    """Verificar agrupación productos."""
    grupos = {p.grupo for p in PRODUCTOS}
    assert grupos == {"Base Harinas y Aceite", "Productos Finales II", "Productos PTEC"}


def test_precio_venta_harina_alperujo():
    """Validar que el precio venta de H. Alperujo sea consistente con plan_builder."""
    m = construir_matriz()
    celda = next(c for c in m.celdas if c.variable == "Precio de Venta" and c.producto == "HARINA_ALPERUJO")
    # Plan builder: HARINA_ALPERUJO 800 CLP/kg
    assert celda.valor == 800
    assert celda.estado == EstadoCelda.OK_PROVISORIO


def test_productos_ptec_son_PD_en_precio():
    """Productos PTEC nuevos deben estar marcados PD en precio (no firmados)."""
    m = construir_matriz()
    ptec_codes = [p.codigo for p in PRODUCTOS if p.grupo == "Productos PTEC"]
    for codigo in ptec_codes:
        celda = next(c for c in m.celdas if c.variable == "Precio de Venta" and c.producto == codigo)
        assert celda.estado == EstadoCelda.PD


def test_pct_cubierto_es_no_trivial():
    """Al menos 30% de las celdas deben tener algún valor (PD puro <70%)."""
    s = stats_resumen(construir_matriz())
    assert s["pct_cubierto"] >= 30
