"""Varredura diagnóstica para As fixo = 2000 mm².
Execute na raiz do projeto: python teste_armadura_fixa.py
Não altera os módulos e não prova existência/inexistência de equilíbrio.
"""
from math import degrees, radians
import numpy as np
from secao.secao import Secao
from secao.barra import Barra
from materiais.concreto import Concreto
from materiais.aco import Aco
from analise.estado_deformacao import EstadoDeformacao
from analise.esforcos import esforcos_resistentes

AS = 2000.0
SOLICITADOS = np.array([-1000e3, 150e6, 80e6])
ESCALAS = np.array([1e6, 150e6, 150e6])


def main():
    secao = Secao(
        contorno=[(0, 0), (400, 0), (400, 600), (0, 600)],
        barras=[Barra(40, 40, proporcao=.25),
                Barra(360, 40, proporcao=.25),
                Barra(360, 560, proporcao=.25),
                Barra(40, 560, proporcao=.25)],
    )
    concreto, aco = Concreto(fck=30), Aco(fyk=500)
    resultados = []
    # Amostra x/h; cobre flexão com linha neutra interna e domínio 5.
    # Uma varredura discreta não é uma busca exaustiva.
    for angulo in range(-180, 180, 10):
        alfa = radians(angulo)
        h = secao.altura(alfa)
        for razao in np.concatenate((np.linspace(.03, 1., 30),
                                      np.array([1.2, 1.5, 2., 3., 5.]))):
            x = float(razao * h)
            try:
                estado = EstadoDeformacao(secao, x, alfa)
                resistentes = np.asarray(esforcos_resistentes(
                    secao, estado, concreto, aco, area_total=AS), dtype=float)
                residuos = (resistentes - SOLICITADOS) / ESCALAS
                norma = float(np.linalg.norm(residuos))
                resultados.append((norma, abs(residuos[0]), x, angulo,
                                   resistentes, residuos))
            except (ValueError, ZeroDivisionError, FloatingPointError) as exc:
                print(f'Estado ignorado: x={x:.2f}, alfa={angulo}°: {exc}')

    if not resultados:
        raise RuntimeError('Nenhum estado foi avaliado.')
    print(f'Area de aco fixa: {AS:.1f} mm2 (4 barras de {AS/4:.1f} mm2)')
    print(f'Estados avaliados: {len(resultados)}')
    print('Solicitacoes: N=-1000 kN, Mx=150 kN.m, My=80 kN.m')
    print('\n=== 10 MENORES NORMAS DE RESIDUOS ===')
    for norma, erro_n, x, angulo, (n, mx, my), _ in sorted(resultados)[:10]:
        print(f'x={x:8.2f} mm; alfa={angulo:+4d}°; '
              f'N={n/1e3:9.2f} kN; Mx={mx/1e6:9.2f} kN.m; '
              f'My={my/1e6:9.2f} kN.m; norma={norma:.6f}')
    print('\n=== 10 ESTADOS COM NORMAL MAIS PROXIMA DE -1000 kN ===')
    for norma, erro_n, x, angulo, (n, mx, my), _ in sorted(
            resultados, key=lambda item: (item[1], item[0]))[:10]:
        print(f'x={x:8.2f} mm; alfa={angulo:+4d}°; '
              f'N={n/1e3:9.2f} kN; Mx={mx/1e6:9.2f} kN.m; '
              f'My={my/1e6:9.2f} kN.m; norma={norma:.6f}')
    print('\nEsta varredura nao demonstra a inexistencia de uma solucao.')


if __name__ == '__main__':
    main()
