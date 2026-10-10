"""Demonstra linha neutra e regiões da seção do Exemplo 5.1."""
from math import radians
from secao.secao import Secao
from secao.barra import Barra
from analise.estado_deformacao import EstadoDeformacao
from visualizacao.desenho_secao import desenhar_secao

contorno = [(0, 0), (850, 0), (850, 850), (0, 850)]
furo = [(300, 300), (550, 300), (550, 550), (300, 550)]
posicoes_cm = [
    (5, 5), (20, 5), (35, 5), (50, 5), (65, 5), (80, 5),
    (5, 20), (5, 35), (5, 50), (5, 65), (5, 80),
    (80, 20), (80, 35), (80, 50), (80, 65), (80, 80),
    (20, 80), (35, 80), (50, 80), (65, 80),
]
barras = [Barra(10*a, 10*b, proporcao=.05) for a, b in posicoes_cm]
secao = Secao(contorno, furos=[furo], barras=barras)
# Valores aproximados de referência do exemplo 5.1.
# Para usar a solução exata, substitua x e alfa pelos resultados do solver.
estado = EstadoDeformacao(secao, x=345.946, alfa=radians(-45))
desenhar_secao(secao, area_total=3728.896, estado=estado,
               numerar_barras=True, mostrar=False,
               titulo='Exemplo 5.1 — linha neutra e regiões',
               salvar_em='secao_linha_neutra.png')
print('Figura salva em secao_linha_neutra.png')
