"""Exemplo de visualização da seção vazada da apostila (Exemplo 5.1)."""
from secao.secao import Secao
from secao.barra import Barra
from visualizacao.desenho_secao import desenhar_secao


def main():
    contorno = [(0, 0), (850, 0), (850, 850), (0, 850)]
    furo = [(300, 300), (550, 300), (550, 550), (300, 550)]
    posicoes_cm = [
        (5, 5), (20, 5), (35, 5), (50, 5), (65, 5), (80, 5),
        (5, 20), (5, 35), (5, 50), (5, 65), (5, 80),
        (80, 20), (80, 35), (80, 50), (80, 65), (80, 80),
        (20, 80), (35, 80), (50, 80), (65, 80),
    ]
    barras = [Barra(10*x, 10*y, proporcao=0.05) for x, y in posicoes_cm]
    secao = Secao(contorno, furos=[furo], barras=barras)
    desenhar_secao(secao, area_total=3729, numerar_barras=True,
                   titulo='Exemplo 5.1 — seção vazada',
                   salvar_em='secao_exemplo_5_1.png')


if __name__ == '__main__':
    main()
