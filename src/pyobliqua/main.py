"""Exemplos de uso do Pyobliqua sem interface gráfica.

Na raiz do projeto:
    python main.py                 # executa os exemplos 5.1 e 5.2
    python main.py --exemplo 5.1   # somente dimensionamento
    python main.py --exemplo 5.2   # somente verificação
    python main.py --diagrama      # também calcula e mostra Mx-My

Unidades internas: mm, N, N.mm, mm² e MPa. Compressão negativa.
Referência: Campos Filho (2000), exemplos 5.1 e 5.2.
"""
import argparse
from math import degrees, radians

from pyobliqua.secao.secao import Secao
from pyobliqua.secao.barra import Barra
from pyobliqua.materiais.concreto import Concreto
from pyobliqua.materiais.aco import Aco
from pyobliqua.analise.estado_deformacao import EstadoDeformacao
from pyobliqua.analise.esforcos import esforcos_resistentes
from pyobliqua.analise.equilibrio import resolver_equilibrio
from pyobliqua.analise.verificacao import resolver_verificacao


def materiais():
    return Concreto(fck=20, gamma_c=1.4), Aco(fyk=500, gamma_s=1.15, es=210000)


def secao_exemplo_51():
    """Seção vazada 85x85 cm; furo 25x25 cm; 20 barras com 5% de As cada."""
    contorno_cm = [(0, 0), (85, 0), (85, 85), (0, 85)]
    furo_cm = [(30, 30), (55, 30), (55, 55), (30, 55)]
    barras_cm = [
        (5, 5), (20, 5), (35, 5), (50, 5), (65, 5), (80, 5),
        (5, 20), (5, 35), (5, 50), (5, 65), (5, 80),
        (80, 20), (80, 35), (80, 50), (80, 65), (80, 80),
        (20, 80), (35, 80), (50, 80), (65, 80),
    ]
    return Secao(
        contorno=[(10*x, 10*y) for x, y in contorno_cm],
        furos=[[(10*x, 10*y) for x, y in furo_cm]],
        barras=[Barra(10*x, 10*y, proporcao=0.05) for x, y in barras_cm],
    )


def secao_exemplo_52():
    """Seção assimétrica da apostila; 15 barras com mesma área."""
    contorno_cm = [
        (22.5, 0), (47.5, 0), (47.5, 10), (42.5, 15),
        (42.5, 95), (70, 110), (70, 120), (0, 120),
        (0, 110), (27.5, 95), (27.5, 15), (22.5, 10),
    ]
    barras_cm = [
        (27.5, 5), (32.5, 5), (37.5, 5), (42.5, 5),
        (27.5, 8), (32.5, 8), (37.5, 8), (42.5, 8),
        (32.5, 11), (37.5, 11),
        (5, 115), (20, 115), (35, 115), (50, 115), (65, 115),
    ]
    return Secao(
        contorno=[(10*x, 10*y) for x, y in contorno_cm],
        barras=[Barra(10*x, 10*y, proporcao=1/15) for x, y in barras_cm],
    )


def imprimir_estado(secao, concreto, aco, x, alfa, As):
    estado = EstadoDeformacao(secao, x, alfa)
    nr, mxr, myr = esforcos_resistentes(
        secao, estado, concreto, aco, area_total=As
    )
    print(f'  x = {x/10:.5f} cm | alfa = {degrees(alfa):+.5f} graus')
    print(f'  As = {As/100:.5f} cm²')
    print(f'  Nr = {nr/1e3:+.5f} kN')
    print(f'  Mrx = {mxr/1e6:+.5f} kN.m | Mry = {myr/1e6:+.5f} kN.m')
    print(f'  Dominio: {estado.dominio}')
    return nr, mxr, myr


def executar_51():
    print('\n' + '='*65 + '\nEXEMPLO 5.1 — DIMENSIONAMENTO\n' + '='*65)
    secao = secao_exemplo_51()
    concreto, aco = materiais()
    n, mx, my = -200e3, -500e6, 500e6
    print(f'Secao: {secao.area/100:.2f} cm² | barras: {len(secao.barras)}')
    print('Solicitacoes: N=-200 kN, Mx=-500 kN.m, My=+500 kN.m')
    resultado = resolver_equilibrio(
        secao, concreto, aco, n, mx, my,
        x0=0.4*secao.altura(0), alfa0=radians(-45), As0=3729.0,
        multiplas_tentativas=True,
    )
    print(f'Convergencia: {bool(resultado.success)}')
    if not resultado.success:
        print('ATENCAO: equilibrio nao confirmado. Diagrama omitido.')
        return None
    x, alfa, As = resultado.x
    nr, mxr, myr = imprimir_estado(secao, concreto, aco, x, alfa, As)
    print(f'  Residuos: dN={(nr-n)/1e3:+.4e} kN; '
          f'dMx={(mxr-mx)/1e6:+.4e} kN.m; dMy={(myr-my)/1e6:+.4e} kN.m')
    print('  Referencia da apostila: As ~ 37.29 cm² (comparar formulacoes).')
    return secao, concreto, aco, As, n, mx, my


def executar_52():
    print('\n' + '='*65 + '\nEXEMPLO 5.2 — VERIFICACAO\n' + '='*65)
    secao = secao_exemplo_52()
    concreto, aco = materiais()
    As, n, mx, my = 3000.0, 0.0, -1000e6, 0.0
    print(f'Secao: {secao.area/100:.2f} cm² | barras: {len(secao.barras)}')
    print('Solicitacoes: N=0 kN, Mx=-1000 kN.m, My=0 kN.m')
    print(f'Area de aco fornecida: {As/100:.2f} cm²')
    resultado = resolver_verificacao(
        secao, concreto, aco, As=As, Nsd=n, Msdx=mx, Msdy=my,
        x0=140.0, alfa0=0.0, lambda0=0.93,
    )
    print(f'Convergencia: {bool(resultado.success)}')
    if not resultado.success:
        print('ATENCAO: equilibrio nao confirmado. Diagrama omitido.')
        return None
    x, alfa, lam = resultado.x
    imprimir_estado(secao, concreto, aco, x, alfa, As)
    print(f'  lambda = {lam:.8f} (referencia ~ 0.9346)')
    print('  Resultado: ' + ('ATENDE' if lam >= 1 else 'NAO ATENDE'))
    print(f'  Norma dos residuos = {resultado.norma_residuos:.3e}')
    return secao, concreto, aco, As, n, mx, my


def mostrar_diagrama(dados, titulo):
    """Diagrama opcional; usa a área As retornada pelo exemplo executado."""
    from analise.interacao import calcular_diagrama_interacao, estimar_aproveitamento_radial
    import matplotlib.pyplot as plt
    secao, concreto, aco, As, n, mx, my = dados
    print('\nCalculando diagrama Mx-My (72 orientacoes)...')
    resultado = calcular_diagrama_interacao(secao, concreto, aco, As, n, n_angulos=72)
    print(f'  Pontos: {len(resultado.pontos)}; orientacoes sem solucao: '
          f'{len(resultado.angulos_sem_solucao)}')
    if not resultado.pontos:
        print('  Nao foram encontrados pontos para plotagem.')
        return
    pontos = sorted(resultado.pontos, key=lambda p: p.alfa)
    xs = [p.Mx/1e6 for p in pontos]
    ys = [p.My/1e6 for p in pontos]
    fig, ax = plt.subplots(figsize=(8, 6))
    # Apenas estados calculados: nao fechar nem unir ramos potencialmente distintos.
    ax.scatter(xs, ys, s=16, label='Estados resistentes calculados')
    ax.scatter([mx/1e6], [my/1e6], marker='x', s=90, c='red',
               label='Solicitacao')
    estimativa = estimar_aproveitamento_radial(resultado, mx, my)
    if estimativa.confiavel_para_interpolacao:
        ax.scatter([estimativa.Mx_resistente/1e6],
                   [estimativa.My_resistente/1e6], marker='o',
                   facecolors='none', edgecolors='green', s=100,
                   label=f'Resistencia interpolada (λ≈{estimativa.lambda_estimado:.4f})')
        print(f'  lambda interpolado = {estimativa.lambda_estimado:.6f}')
    else:
        print(f'  Interpolacao indisponivel: {estimativa.observacao}')
    ax.axhline(0, color='gray', lw=0.7)
    ax.axvline(0, color='gray', lw=0.7)
    ax.set_xlabel('Mx (kN.m)')
    ax.set_ylabel('My (kN.m)')
    ax.set_title(f'{titulo} | N={n/1e3:g} kN | As={As/100:.3f} cm²')
    ax.grid(alpha=0.3)
    ax.legend(loc='best')
    fig.tight_layout()
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exemplo', choices=['5.1', '5.2', 'ambos'], default='ambos')
    parser.add_argument('--diagrama', action='store_true', help='Exibir diagrama Mx-My')
    args = parser.parse_args()
    figuras = []
    if args.exemplo in ('5.1', 'ambos'):
        dados = executar_51()
        if args.diagrama and dados is not None:
            figuras.append(mostrar_diagrama(dados, 'Exemplo 5.1'))
    if args.exemplo in ('5.2', 'ambos'):
        dados = executar_52()
        if args.diagrama and dados is not None:
            figuras.append(mostrar_diagrama(dados, 'Exemplo 5.2'))
    if any(fig is not None for fig in figuras):
        import matplotlib.pyplot as plt
        plt.show()


if __name__ == '__main__':
    main()
