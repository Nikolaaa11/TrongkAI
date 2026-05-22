"""Tests del módulo de depreciación y tax shield."""

from __future__ import annotations

from trongkai_engine.depreciation import (
    ActivoFijo,
    CategoriaActivo,
    MetodoDepreciacion,
    RegimenTributario,
    calcular_depreciacion,
    capex_a_activos_default,
    tax_shield,
)


def test_depreciacion_normal_lineal():
    """Maquinaria industrial 10 años → 10% por año."""
    a = ActivoFijo("Test maq", 1_000_000_000, ano_adquisicion=1, categoria=CategoriaActivo.MAQUINARIA_INDUSTRIAL)
    assert a.vida_util_aplicada() == 10
    assert a.depreciacion_anual_clp() == 100_000_000


def test_depreciacion_acelerada_divide_por_3():
    """Acelerada = vida útil / 3 (LIR Art 31 N°5)."""
    a = ActivoFijo("Maq acelerada", 1_000_000_000, ano_adquisicion=1,
                   categoria=CategoriaActivo.MAQUINARIA_INDUSTRIAL,
                   metodo=MetodoDepreciacion.ACELERADA)
    # 10 / 3 = 3 (floor)
    assert a.vida_util_aplicada() == 3
    # Depreciación anual = monto / 3
    assert abs(a.depreciacion_anual_clp() - 1_000_000_000 / 3) < 1


def test_depreciacion_instantanea_100pct_ano_1():
    a = ActivoFijo("Test inst", 1_000_000_000, ano_adquisicion=1,
                   categoria=CategoriaActivo.EQUIPO_ESPECIALIZADO,
                   metodo=MetodoDepreciacion.INSTANTANEA)
    assert a.vida_util_aplicada() == 1
    assert a.depreciacion_anual_clp() == 1_000_000_000


def test_cronograma_5_anos():
    """Activo año 1 con vida útil 10 → depreciación constante años 1-5."""
    activos = [ActivoFijo("X", 1_000_000_000, ano_adquisicion=1,
                          categoria=CategoriaActivo.MAQUINARIA_INDUSTRIAL)]
    cron = calcular_depreciacion(activos, horizonte_anos=5)
    assert len(cron) == 5
    for i in range(5):
        assert cron[i] == 100_000_000


def test_cronograma_activo_ano_3_solo_se_deprecia_desde_ano_3():
    """Activo comprado año 3 sólo se deprecia A3-A7. En horizonte 5 años → A3, A4, A5."""
    activos = [ActivoFijo("Y", 1_000_000_000, ano_adquisicion=3,
                          categoria=CategoriaActivo.MAQUINARIA_INDUSTRIAL)]
    cron = calcular_depreciacion(activos, horizonte_anos=5)
    assert cron[0] == 0
    assert cron[1] == 0
    assert cron[2] == 100_000_000
    assert cron[3] == 100_000_000
    assert cron[4] == 100_000_000


def test_tax_shield_general_27pct():
    ebitda = [1_000_000_000] * 5
    dep = [100_000_000] * 5
    out = tax_shield(ebitda, dep, regimen=RegimenTributario.GENERAL)
    # EBT = 1.000 - 100 = 900M. Impuesto = 900 × 0.27 = 243M.
    assert out["tasa_renta"] == 0.27
    assert abs(out["impuesto_anual"][0] - 243_000_000) < 1
    assert abs(out["utilidad_neta_anual"][0] - (900_000_000 - 243_000_000)) < 1
    # Tax shield = 100M × 0.27 = 27M ahorro fiscal
    assert abs(out["tax_shield_anual"][0] - 27_000_000) < 1


def test_tax_shield_propyme_25pct():
    ebitda = [1_000_000_000] * 5
    dep = [100_000_000] * 5
    out = tax_shield(ebitda, dep, regimen=RegimenTributario.PROPYME)
    assert out["tasa_renta"] == 0.25
    # EBT 900M × 0.25 = 225M impuesto
    assert abs(out["impuesto_anual"][0] - 225_000_000) < 1


def test_tax_shield_con_intereses_amplifica_shield():
    ebitda = [1_000_000_000] * 5
    dep = [100_000_000] * 5
    intereses = [50_000_000] * 5
    out_sin = tax_shield(ebitda, dep, regimen=RegimenTributario.GENERAL)
    out_con = tax_shield(ebitda, dep, intereses, regimen=RegimenTributario.GENERAL)
    # Con intereses: shield extra = 50M × 0.27 = 13.5M
    assert out_con["tax_shield_anual"][0] > out_sin["tax_shield_anual"][0]
    assert abs(out_con["tax_shield_anual"][0] - out_sin["tax_shield_anual"][0] - 13_500_000) < 1


def test_ebt_negativo_no_paga_impuesto():
    """Si EBT < 0, impuesto = 0 (la pérdida arrastra pero no genera reembolso)."""
    ebitda = [50_000_000] * 5  # pequeño
    dep = [200_000_000] * 5    # grande
    out = tax_shield(ebitda, dep, regimen=RegimenTributario.GENERAL)
    # EBT = 50 - 200 = -150M → impuesto debe ser 0
    assert out["impuesto_anual"][0] == 0
    # Utilidad neta = -150M (pérdida)
    assert out["utilidad_neta_anual"][0] < 0


def test_capex_a_activos_default_suma_capex():
    capex = {1: 1_000_000_000, 2: 500_000_000}
    activos = capex_a_activos_default(capex)
    # 4 categorías por año × 2 años = 8 activos
    assert len(activos) == 8
    # Suma de montos = capex total
    total = sum(a.monto_clp for a in activos)
    assert abs(total - 1_500_000_000) < 1


def test_capex_default_mix_60_25_10_5():
    """La heurística 60% maq + 25% esp + 10% edif + 5% mueb."""
    capex = {1: 1_000_000_000}
    activos = capex_a_activos_default(capex)
    by_cat = {a.categoria: a.monto_clp for a in activos}
    assert abs(by_cat[CategoriaActivo.MAQUINARIA_INDUSTRIAL] - 600_000_000) < 1
    assert abs(by_cat[CategoriaActivo.EQUIPO_ESPECIALIZADO] - 250_000_000) < 1
    assert abs(by_cat[CategoriaActivo.EDIFICIO] - 100_000_000) < 1
    assert abs(by_cat[CategoriaActivo.MUEBLES_INSTALACIONES] - 50_000_000) < 1
