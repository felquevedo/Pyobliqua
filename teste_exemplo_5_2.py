"""Exemplo 5.2 de Campos Filho (2000), pp. 32-34.

Execute na raiz do projeto: python teste_exemplo_5_2.py
Requer analise/verificacao.py.
"""
from math import degrees
from secao.secao import Secao
from secao.barra import Barra
from materiais.concreto import Concreto
from materiais.aco import Aco
from analise.verificacao import resolver_verificacao
from analise.estado_deformacao import EstadoDeformacao
from analise.esforcos import esforcos_resistentes
from visualizacao.desenho_secao import desenhar_secao

# Coordenadas originais em cm, convertidas para mm.
CONTORNO_CM = [
    (22.5,0), (47.5,0), (47.5,10), (42.5,15), (42.5,95),
    (70,110), (70,120), (0,120), (0,110), (27.5,95),
    (27.5,15), (22.5,10)
]
BARRAS_CM = [
    (27.5,5), (32.5,5), (37.5,5), (42.5,5),
    (27.5,8), (32.5,8), (37.5,8), (42.5,8),
    (32.5,11), (37.5,11),
    (5,115), (20,115), (35,115), (50,115), (65,115)
]


def main():
    secao = Secao(
        contorno=[(10*x,10*y) for x,y in CONTORNO_CM],
        barras=[Barra(10*x,10*y,proporcao=1/15) for x,y in BARRAS_CM]
    )
    # Apostila: Es=21000 kN/cm2 = 210000 MPa; As=30 cm2 = 3000 mm2
    concreto = Concreto(fck=20, gamma_c=1.4)
    aco = Aco(fyk=500, gamma_s=1.15, es=210000)
    r = resolver_verificacao(
        secao, concreto, aco, As=3000.0,
        Nsd=0.0, Msdx=-1000e6, Msdy=0.0,
        x0=140.0, alfa0=0.0, lambda0=0.93
    )
    x, alfa, lam = r.x
    print('=== EXEMPLO 5.2 — VERIFICACAO ===')
    print(f'Area geometrica: {secao.area:.3f} mm2; barras: {len(secao.barras)}')
    print(f'Equilibrio atendido: {r.success}; tentativas: {r.tentativas}')
    print(f'x = {x:.6f} mm; alfa = {degrees(alfa):.6f} graus')
    print(f'lambda = {lam:.8f}; referencia apostila = 0.9346')
    print(f'diferenca lambda = {lam - 0.9346:+.8f}')
    print(f'norma dos residuos = {r.norma_residuos:.3e}')
    if r.success:
        estado = EstadoDeformacao(secao, x, alfa)
        Nr, Mrx, Mry = esforcos_resistentes(
            secao, estado, concreto, aco, area_total=3000.0
        )
        desenhar_secao(
            secao, area_total=3000.0, estado=estado, numerar_barras=True,
            titulo=f'Exemplo 5.2 — Verificacao (lambda = {lam:.4f})',
            esforcos=(Nr, Mrx, Mry), tipo_esforcos='resistentes',
            salvar_em='secao_exemplo_5_2_resultado.png',
        )
    if not r.success:
        print('ATENCAO: nao houve convergencia; mostrando apenas geometria e barras.')
        desenhar_secao(
            secao, area_total=3000.0, numerar_barras=True,
            titulo='Exemplo 5.2 — NÃO HOUVE CONVERGÊNCIA',
            salvar_em='secao_exemplo_5_2_resultado.png',
        )
    elif abs(lam - 0.9346) > 0.002:
        print('ATENCAO: divergencia relevante frente a referencia; revisar modelo.')


if __name__ == '__main__':
    main()
