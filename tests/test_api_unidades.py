"""Testes da fachada pública, sem conversões manuais."""
import pytest
from pyobliqua import Modelo, Unidades


def test_unidades_e_geometria():
    m = Modelo(Unidades(forca='tf', momento='tf.m', tensao='kgf/cm²'))
    secao = m.secao([(0, 0), (10, 0), (10, 20), (0, 20)],
                    barras=[m.barra(2, 3, area=1.5)])
    assert secao.area == pytest.approx(20000)
    assert secao.barras[0].x == pytest.approx(20)
    assert secao.barras[0].area == pytest.approx(150)
    assert m.concreto(20 / (9.80665 / 100)).fck == pytest.approx(20)
    assert m.aco(500 / (9.80665 / 100)).fyk == pytest.approx(500)
    assert m.aco(500 / (9.80665 / 100)).es == pytest.approx(210000)


def test_unidades_equivalentes():
    from pyobliqua.unidades import Unidades
    a = Unidades(forca='kN', momento='kN.m', tensao='MPa')
    b = Unidades(forca='tf', momento='tf.m', tensao='tf/cm²')
    for grandeza, valor in [('forca', 200), ('momento', 500), ('tensao', 20)]:
        fisico = a.para_interno(valor, grandeza)
        assert b.para_interno(b.de_interno(fisico, grandeza), grandeza) == pytest.approx(fisico)
