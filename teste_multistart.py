"""Diagnóstico multistart para a seção 400 x 600 mm do main.py.

Execute na raiz do projeto: python teste_multistart.py
Não altera nenhum módulo do projeto.
"""
from itertools import product
from math import degrees, radians

import numpy as np

from analise.equilibrio import resolver_equilibrio
from materiais.aco import Aco
from materiais.concreto import Concreto
from secao.barra import Barra
from secao.secao import Secao


def main():
    secao = Secao(
        contorno=[(0, 0), (400, 0), (400, 600), (0, 600)],
        barras=[
            Barra(40, 40, proporcao=0.25),
            Barra(360, 40, proporcao=0.25),
            Barra(360, 560, proporcao=0.25),
            Barra(40, 560, proporcao=0.25),
        ],
    )
    concreto = Concreto(fck=30)
    aco = Aco(fyk=500)
    solicitacoes = dict(Nsd=-1000e3, Msdx=150e6, Msdy=80e6)

    xs = (100.0, 300.0, 500.0)
    angulos = (-150, -90, -30, 30, 90, 150)
    areas = (1000.0, 3000.0, 6000.0)
    registros = []
    total = len(xs) * len(angulos) * len(areas)
    print(f"Executando {total} estimativas iniciais...", flush=True)

    for i, (x0, angulo0, As0) in enumerate(product(xs, angulos, areas), start=1):
        try:
            r = resolver_equilibrio(
                secao=secao, concreto=concreto, aco=aco,
                **solicitacoes, x0=x0, alfa0=radians(angulo0), As0=As0,
                multiplas_tentativas=False,
            )
            norma = float(np.linalg.norm(r.fun))
            registros.append((norma, x0, angulo0, As0, r))
            status = 'EQUILIBRIO' if r.success else 'sem equilibrio'
            print(f"{i:02d}/{total} x0={x0:5.0f} alfa0={angulo0:+4d} As0={As0:5.0f} "
                  f"-> norma={norma:.6e} [{status}]", flush=True)
        except Exception as exc:
            print(f"{i:02d}/{total} FALHA x0={x0} alfa0={angulo0} As0={As0}: {exc}", flush=True)

    if not registros:
        raise RuntimeError('Nenhuma tentativa produziu resultado.')

    registros.sort(key=lambda item: item[0])
    print('\n=== DEZ MELHORES RESULTADOS ===')
    for rank, (norma, x0, angulo0, As0, r) in enumerate(registros[:10], 1):
        x, alfa, As = r.x
        print(f"{rank:2d}. norma={norma:.8e} | x={x:.4f} mm | "
              f"alfa={degrees(alfa):.4f} graus | As={As:.4f} mm2 | "
              f"inicio=({x0:.0f}, {angulo0:+d}, {As0:.0f}) | "
              f"equilibrio={r.success}")

    melhor = registros[0][-1]
    print('\n=== MELHOR TENTATIVA ===')
    print('Convergencia/equilibrio:', melhor.success)
    print('Mensagem:', melhor.message)
    print('Residuos normalizados:', melhor.fun)
    print('Norma:', np.linalg.norm(melhor.fun))
    print('Esforcos resistentes aproximados:')
    escalas = np.array([max(abs(solicitacoes['Nsd']), 1e5),
                        max(abs(solicitacoes['Msdx']), abs(solicitacoes['Msdy']), 1e7),
                        max(abs(solicitacoes['Msdx']), abs(solicitacoes['Msdy']), 1e7)])
    resistentes = np.array(list(solicitacoes.values())) + melhor.fun * escalas
    print(f"Nr={resistentes[0]/1e3:.3f} kN; "
          f"Mrx={resistentes[1]/1e6:.3f} kN.m; "
          f"Mry={resistentes[2]/1e6:.3f} kN.m")
    print(f"Tentativas com equilibrio: {sum(r.success for *_, r in registros)}/{len(registros)}")
    print('Observacao: multistart nao prova inexistencia de solucao.')


if __name__ == '__main__':
    main()
