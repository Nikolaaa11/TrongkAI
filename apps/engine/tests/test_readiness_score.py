"""Tests del Investment Readiness Score."""

from __future__ import annotations

import pytest

from trongkai_engine.readiness_score import (
    DimensionScore,
    ReadinessScore,
    _score_bancabilidad,
    _score_compliance,
    _score_esg,
    _score_retorno,
    _score_robustez,
    calcular_readiness_score,
)


def test_score_retorno_tir_30pct():
    s, _ = _score_retorno(0.30, hurdle=0.15)
    # 30 - 15 = 15pp; lineal 15/20 = 75
    assert 70 < s < 80


def test_score_retorno_tir_bajo_hurdle():
    s, _ = _score_retorno(0.10, hurdle=0.15)
    assert s == 0.0


def test_score_retorno_tir_excelente():
    s, _ = _score_retorno(0.50, hurdle=0.15)
    assert s == 100.0


def test_score_robustez_alto():
    s, _ = _score_robustez(0.85)
    assert s == 85.0


def test_score_robustez_none():
    s, _ = _score_robustez(None)
    assert s == 0.0


def test_score_bancabilidad_holgado():
    s, _ = _score_bancabilidad(2.0)
    assert s == 100.0


def test_score_bancabilidad_no_bancable():
    s, _ = _score_bancabilidad(0.8)
    assert s == 0.0


def test_score_esg_carbono_negativo():
    carbon = {"baseline": {"emisiones_netas_5y_ton": -50_000}}
    s, _ = _score_esg(carbon)
    assert s == 100.0


def test_score_esg_carbono_positivo():
    carbon = {"baseline": {"emisiones_netas_5y_ton": 10_000}}
    s, _ = _score_esg(carbon)
    assert s < 80


def test_score_compliance_full():
    rep = {"vigentes": 10, "total_hitos": 10}
    s, _ = _score_compliance(rep)
    assert s == 100.0


def test_score_compliance_parcial():
    rep = {"vigentes": 5, "total_hitos": 10}
    s, _ = _score_compliance(rep)
    assert s == 50.0


def test_calcular_readiness_score_completo():
    rs = calcular_readiness_score(n_sims_mc=100)
    assert isinstance(rs, ReadinessScore)
    assert 0 <= rs.score_total <= 100
    assert len(rs.dimensiones) == 8
    # Suma de pesos = 1.0
    assert abs(sum(d.peso for d in rs.dimensiones) - 1.0) < 0.01
    # Score total = suma de aportes
    suma_aportes = sum(d.aporte_total() for d in rs.dimensiones)
    assert abs(rs.score_total - suma_aportes) < 0.1


def test_readiness_to_dict_serializa():
    rs = calcular_readiness_score(n_sims_mc=100)
    d = rs.to_dict()
    assert "score_total" in d
    assert "dimensiones" in d
    assert "interpretacion" in d
    assert len(d["dimensiones"]) == 8
    for dim in d["dimensiones"]:
        assert "nombre" in dim
        assert "peso" in dim
        assert "score_0_100" in dim
        assert "aporte_total" in dim


def test_interpretacion_bankable():
    """Con score >= 80, interpretacion debe contener BANKABLE."""
    rs = calcular_readiness_score(n_sims_mc=100)
    if rs.score_total >= 80:
        assert "BANKABLE" in rs.interpretacion
