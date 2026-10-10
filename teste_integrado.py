"""Teste de recuperação de solução para flexão composta oblíqua.
Execute da raiz do projeto: python teste_integrado.py
"""
from math import radians, degrees
import numpy as np
from secao.secao import Secao
from secao.barra import Barra
from materiais.concreto import Concreto
from materiais.aco import Aco
from analise.estado_deformacao import EstadoDeformacao
from analise.esforcos import esforcos_resistentes
from analise.equilibrio import resolver_equilibrio


def main():
    contorno = [(0, 0), (400, 0), (400, 600), (0, 600)]
    # A área total é a incógnita. Cada barra representa 25% dela.
    barras = [Barra(40, 40, proporcao=.25),
              Barra(360, 40, proporcao=.25),
              Barra(360, 560, proporcao=.25),
              Barra(40, 560, proporcao=.25)]
    secao = Secao(contorno, barras=barras)
    concreto = Concreto(fck=30)
    aco = Aco(fyk=500)

    assert np.isclose(secao.area, 240000)
    assert np.isclose(secao.xc, 200)
    assert np.isclose(secao.yc, 300)
    assert np.isclose(secao.Ix, 400 * 600**3 / 12)
    assert np.isclose(secao.Iy, 600 * 400**3 / 12)
    assert np.isclose(secao.Ixy, 0, atol=1e-5)
    print('Geometria: OK')

    x_ref, alfa_ref, As_ref = 300., radians(30), 2000.
    estado = EstadoDeformacao(secao, x_ref, alfa_ref)
    assert np.isclose(estado.deformacao(estado.eta_s - x_ref), 0, atol=1e-12)
    for barra in secao.barras:
        _, eta = secao.coordenadas_rotacionadas(barra.posicao, alfa_ref)
        assert np.isclose(estado.deformacao_barra(barra), estado.deformacao(eta))
    print('Compatibilidade das deformações: OK')

    Nsd, Msdx, Msdy = esforcos_resistentes(
        secao, estado, concreto, aco, area_total=As_ref)
    print(f'Esforços de referência: N={Nsd/1e3:.3f} kN; '
          f'Mx={Msdx/1e6:.3f} kN.m; My={Msdy/1e6:.3f} kN.m')

    resultado = resolver_equilibrio(
        secao, concreto, aco, Nsd, Msdx, Msdy,
        x0=x_ref * 1.02, alfa0=alfa_ref + radians(1), As0=As_ref * 1.05)
    print('Convergência:', resultado.success)
    print('Mensagem:', resultado.message)
    print('Resultado: x={:.6f} mm; alfa={:.6f}°; As={:.6f} mm²'.format(
        resultado.x[0], degrees(resultado.x[1]), resultado.x[2]))
    print('Resíduos normalizados:', resultado.fun)
    assert resultado.success, 'O solucionador não convergiu'
    assert np.linalg.norm(resultado.fun) < 1e-6, 'Resíduos elevados'
    assert np.isclose(resultado.x[0], x_ref, rtol=1e-4, atol=1e-3)
    assert np.isclose(np.sin(resultado.x[1]-alfa_ref), 0, atol=1e-4)
    assert np.isclose(resultado.x[2], As_ref, rtol=1e-4, atol=1e-2)
    print('Teste integrado: OK')


if __name__ == '__main__':
    main()
