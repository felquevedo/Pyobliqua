"""Validação com o Exemplo 5.1 (Campos Filho, 2000, pp. 30-32).

Coloque este arquivo na raiz do projeto e execute:
    python teste_exemplo_5_1.py

Unidades internas: mm, N, MPa e N.mm.
O programa apenas compara resultados; não modifica os módulos existentes.
"""
from math import degrees, radians
import numpy as np

from secao.secao import Secao
from secao.barra import Barra
from materiais.concreto import Concreto
from materiais.aco import Aco
from analise.estado_deformacao import EstadoDeformacao
from analise.esforcos import esforcos_resistentes
from analise.equilibrio import resolver_equilibrio
from visualizacao.desenho_secao import desenhar_secao


# Apostila: contorno 85 x 85 cm, vazio central 25 x 25 cm.
# Coordenadas convertidas de cm para mm.
CONTORNO = [(0, 0), (850, 0), (850, 850), (0, 850)]
FURO = [(300, 300), (550, 300), (550, 550), (300, 550)]

# Vinte barras, cada uma com 5% da área total, conforme página 31.
BARRAS_CM = [
    (5, 5), (20, 5), (35, 5), (50, 5), (65, 5), (80, 5),
    (5, 20), (5, 35), (5, 50), (5, 65), (5, 80),
    (80, 20), (80, 35), (80, 50), (80, 65), (80, 80),
    (20, 80), (35, 80), (50, 80), (65, 80),
]

# Esforços da apostila, página 31: N=-200 kN; Mx=-500 kN.m; My=+500 kN.m.
N_SD = -200e3
MX_SD = -500e6
MY_SD = 500e6
AS_REFERENCIA = 37.29 * 100  # cm2 -> mm2
ALFA_REFERENCIA = -45.0      # graus


def montar_secao():
    barras = [Barra(10*x, 10*y, proporcao=0.05) for x, y in BARRAS_CM]
    return Secao(contorno=CONTORNO, furos=[FURO], barras=barras)


def imprimir_esforcos(secao, concreto, aco, x, alfa, As):
    estado = EstadoDeformacao(secao, x, alfa)
    n, mx, my = esforcos_resistentes(
        secao, estado, concreto, aco, area_total=As
    )
    print(f'  N={n/1e3:+.4f} kN; Mx={mx/1e6:+.4f} kN.m; '
          f'My={my/1e6:+.4f} kN.m')
    print(f'  Residuos: dN={(n-N_SD)/1e3:+.4f} kN; '
          f'dMx={(mx-MX_SD)/1e6:+.4f} kN.m; '
          f'dMy={(my-MY_SD)/1e6:+.4f} kN.m')
    return estado


def main():
    secao = montar_secao()
    concreto = Concreto(fck=20, gamma_c=1.4)
    aco = Aco(fyk=500, gamma_s=1.15, es=210000)

    print('=== EXEMPLO 5.1 - CAMPOS FILHO (2000) ===')
    print(f'Area liquida: {secao.area:.2f} mm2 '
          f'(referencia geometrica: 660000 mm2)')
    print(f'Centroide: ({secao.xc:.2f}, {secao.yc:.2f}) mm')
    print(f'Barras: {len(secao.barras)}; soma proporcoes: '
          f'{sum(b.proporcao for b in secao.barras):.6f}')
    assert np.isclose(secao.area, 850**2 - 250**2)
    assert np.isclose(secao.xc, 425)
    assert np.isclose(secao.yc, 425)
    assert len(secao.barras) == 20
    assert np.isclose(sum(b.proporcao for b in secao.barras), 1.0)

    print('\nSolicitacoes: N=-200 kN; Mx=-500 kN.m; My=+500 kN.m')
    print('Referencia: As=3729 mm2; alfa=-45 graus; '
          'eps_superior=-3.5 por mil; eps_inferior=+7.946 por mil')

    # x não está impresso na saída do exemplo. Testamos diversas estimativas.
    # O limite superior da área é numérico, não uma verificação normativa.
    melhores = []
    for alfa0 in (-45, -30, -60, 135):
        for x0 in (120, 300, 500, 750):
            try:
                resultado = resolver_equilibrio(
                    secao, concreto, aco, N_SD, MX_SD, MY_SD,
                    x0=float(x0), alfa0=radians(alfa0),
                    As0=AS_REFERENCIA,
                    taxa_max=0.08, fator_x_max=5.0,
                    multiplas_tentativas=False,
                )
                melhores.append((float(np.linalg.norm(resultado.fun)), resultado))
            except (ValueError, ArithmeticError, FloatingPointError) as exc:
                print(f'Inicio x={x0} mm, alfa={alfa0} graus: erro: {exc}')

    if not melhores:
        print('ATENCAO: nao houve convergencia (nenhuma tentativa avaliada).')
        desenhar_secao(
            secao, area_total=None, numerar_barras=True,
            titulo='Exemplo 5.1 — NÃO HOUVE CONVERGÊNCIA',
            salvar_em='secao_exemplo_5_1_resultado.png',
            esforcos=(N_SD, MX_SD, MY_SD), tipo_esforcos='solicitantes',
        )
        return

    norma, resultado = min(melhores, key=lambda item: item[0])
    x, alfa, As = resultado.x
    print('\n=== MELHOR RESULTADO DO MODELO PYTHON ===')
    print(f'Equilibrio atendido: {resultado.success}')
    print(f'Mensagem: {resultado.message}')
    print(f'x={x:.5f} mm; alfa={degrees(alfa):.5f} graus; '
          f'As={As:.5f} mm2 ({As/100:.5f} cm2)')
    print(f'Diferenca As vs apostila: {As-AS_REFERENCIA:+.5f} mm2 '
          f'({100*(As/AS_REFERENCIA-1):+.3f}%)')
    print(f'Norma residuos normalizados: {norma:.6e}')
    print('Esforcos resistentes no estado calculado:')
    estado = imprimir_esforcos(secao, concreto, aco, x, alfa, As)
    print(f'eps superior = {estado.epsilon_s*1e3:+.5f} por mil')
    print(f'eps inferior (atributo original) = {estado.epsilon_i*1e3:+.5f} por mil')
    if resultado.success:
        desenhar_secao(
            secao, area_total=As, estado=estado, numerar_barras=True,
            titulo='Exemplo 5.1 — Dimensionamento',
            salvar_em='secao_exemplo_5_1_resultado.png',
            esforcos=(N_SD, MX_SD, MY_SD), tipo_esforcos='solicitantes',
        )
    else:
        print('ATENCAO: nao houve convergencia; mostrando apenas geometria e barras.')
        desenhar_secao(
            secao, area_total=None, numerar_barras=True,
            titulo='Exemplo 5.1 — NÃO HOUVE CONVERGÊNCIA',
            salvar_em='secao_exemplo_5_1_resultado.png',
            esforcos=(N_SD, MX_SD, MY_SD), tipo_esforcos='solicitantes',
        )
    print('\nAVISO: divergencias podem decorrer de convencoes, '
          'formulações ou regras de dominio. Nao validar apenas pelo success.')


if __name__ == '__main__':
    main()
