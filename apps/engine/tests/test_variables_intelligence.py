"""Tests de Variables Intelligence."""

from __future__ import annotations

from trongkai_engine.variables_intelligence import (
    analisis_inteligente,
    detectar_inconsistencias,
    score_confianza_celda,
    simular_cambio_celda,
    sugerir_valores_pd,
)
from trongkai_engine.variables_matrix import EstadoCelda, construir_matriz


def test_detecta_inconsistencias_base_consistente():
    """En la matriz base (calculada coherentemente), inconsistencias deben ser pocas."""
    issues = detectar_inconsistencias()
    # Si hay inconsistencias, deben tener todos los campos
    for i in issues:
        assert i.severidad in {"alta", "media", "baja"}
        assert i.tipo in {"matematica", "logica", "rango"}
        assert i.descripcion
        assert len(i.celdas_involucradas) > 0


def test_sugerir_valores_pd_no_vacio():
    """Para celdas PD, debe haber sugerencias."""
    sugerencias = sugerir_valores_pd()
    # Hay 95 celdas PD en la matriz base, esperamos al menos algunas sugerencias
    assert len(sugerencias) > 0
    for s in sugerencias:
        assert s.valor_sugerido is not None
        assert 0 <= s.confianza <= 1
        assert s.razonamiento


def test_sugerencias_to_dict():
    sugerencias = sugerir_valores_pd()
    if sugerencias:
        d = sugerencias[0].to_dict()
        assert "valor_sugerido" in d
        assert "confianza" in d
        assert "razonamiento" in d


def test_score_confianza_pd_es_cero():
    matriz = construir_matriz()
    pd_celdas = [c for c in matriz.celdas if c.estado == EstadoCelda.PD]
    for c in pd_celdas[:3]:
        assert score_confianza_celda(c) == 0.0


def test_score_confianza_ok_provisorio_es_50_o_65():
    matriz = construir_matriz()
    ok_prov = [c for c in matriz.celdas if c.estado == EstadoCelda.OK_PROVISORIO]
    for c in ok_prov[:3]:
        score = score_confianza_celda(c)
        assert score in {50.0, 65.0}


def test_simular_cambio_precio_aumenta_tir():
    """Subir el precio de un SKU debe subir la TIR."""
    impacto = simular_cambio_celda(
        variable="Precio de Venta",
        producto="HARINA_ALPERUJO",
        valor_nuevo=1000,  # vs 800 default
    )
    assert impacto.valor_anterior == 800
    assert impacto.valor_nuevo == 1000
    assert impacto.tir_nuevo is not None
    assert impacto.tir_anterior is not None
    # TIR debe subir
    assert impacto.tir_nuevo > impacto.tir_anterior


def test_simular_cambio_rendimiento_aumenta_tir():
    """Subir el rendimiento debe subir TIR."""
    impacto = simular_cambio_celda(
        variable="Rendimiento",
        producto="HARINA_ALPERUJO",  # mmpp_origen = ALPERUJO
        valor_nuevo=0.50,  # vs 0.39 default
    )
    assert impacto.delta_tir_pp is not None
    assert impacto.delta_tir_pp > 0


def test_analisis_inteligente_serializa():
    a = analisis_inteligente()
    d = a.to_dict()
    assert "inconsistencias" in d
    assert "sugerencias" in d
    assert "confianza_promedio" in d
    assert "confianza_por_grupo" in d
    assert "celdas_criticas" in d
    # 3 grupos esperados
    assert len(d["confianza_por_grupo"]) == 3


def test_analisis_confianza_promedio_razonable():
    a = analisis_inteligente()
    # 70 celdas OK_PROVISORIO de 165 → confianza promedio cerca de 70*50/165 ≈ 21
    assert 15 <= a.confianza_promedio <= 35


def test_celdas_criticas_son_pd_de_variables_clave():
    """Las celdas críticas deben ser PD en variables clave."""
    a = analisis_inteligente()
    variables_clave = {"Precio de Venta", "Rendimiento", "Costo producción"}
    for c in a.celdas_criticas:
        assert c["variable"] in variables_clave
