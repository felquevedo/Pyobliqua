"""Exemplos 5.1 e 5.2: uso didático do núcleo de cálculo do Pyobliqua.

Execute na raiz do projeto (após instalar com pip install -e .):
    python -m pyobliqua.main

Unidades internas: mm, N, N.mm, mm² e MPa.
Convenção: compressão negativa.
"""

from math import degrees, radians

import matplotlib.pyplot as plt

from pyobliqua import (
    Secao, Barra, Concreto, Aco, EstadoDeformacao,
    resolver_equilibrio, resolver_verificacao,
    desenhar_secao, desenhar_diagramas_deformacoes_tensoes,
)

# Materiais usados nos dois exemplos
concreto = Concreto(fck=20, gamma_c=1.4)
aco = Aco(fyk=500, gamma_s=1.15, es=210000)

# ============================================================
# EXEMPLO 5.1 — DIMENSIONAMENTO DA ARMADURA
# ============================================================
print("\nEXEMPLO 5.1 — DIMENSIONAMENTO")

# Seção quadrada de 85 x 85 cm com furo central de 25 x 25 cm.
# A geometria é informada em cm e convertida para mm.
contorno_cm = [(0, 0), (85, 0), (85, 85), (0, 85)]
furo_cm = [(30, 30), (55, 30), (55, 55), (30, 55)]
barras_cm = [
    (5, 5), (20, 5), (35, 5), (50, 5), (65, 5), (80, 5),
    (5, 20), (5, 35), (5, 50), (5, 65), (5, 80),
    (80, 20), (80, 35), (80, 50), (80, 65), (80, 80),
    (20, 80), (35, 80), (50, 80), (65, 80),
]

secao = Secao(
    contorno=[(10 * x, 10 * y) for x, y in contorno_cm],
    furos=[[(10 * x, 10 * y) for x, y in furo_cm]],
    barras=[Barra(10 * x, 10 * y, proporcao=1 / 20) for x, y in barras_cm],
)

# Esforços solicitantes: kN e kN.m convertidos para N e N.mm
Nsd = -200e3
Msdx = -500e6
Msdy = 500e6

resultado = resolver_equilibrio(
    secao, concreto, aco, Nsd, Msdx, Msdy,
    x0=0.4 * secao.altura(0),
    alfa0=radians(-45),
    As0=3729.0,
    multiplas_tentativas=True,
)

print(f"Convergencia: {bool(resultado.success)}")
if resultado.success:
    x, alfa, As = resultado.x
    print(f"x = {x / 10:.6f} cm")
    print(f"alfa = {degrees(alfa):.6f} graus")
    print(f"As = {As / 100:.5f} cm²")

    # Gráfico do exemplo 5.1: seção, linha neutra, deformações e tensões.
    estado = EstadoDeformacao(secao, x, alfa, concreto)
    figura, eixo = plt.subplots(figsize=(12, 7))
    desenhar_secao(
        secao, area_total=As, estado=estado, ax=eixo, mostrar=False,
        esforcos=(Nsd, Msdx, Msdy), titulo="Exemplo 5.1 — Dimensionamento",
    )
    desenhar_diagramas_deformacoes_tensoes(eixo, secao, estado, concreto)
else:
    print("O dimensionamento não convergiu.")

# ============================================================
# EXEMPLO 5.2 — VERIFICAÇÃO DE UMA ARMADURA EXISTENTE
# ============================================================
print("\nEXEMPLO 5.2 — VERIFICACAO")

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

secao = Secao(
    contorno=[(10 * x, 10 * y) for x, y in contorno_cm],
    barras=[Barra(10 * x, 10 * y, proporcao=1 / 15) for x, y in barras_cm],
)

# Área de aço conhecida: 30 cm² = 3000 mm²
As = 3000.0
Nsd = 0.0
Msdx = -1000e6
Msdy = 0.0

resultado = resolver_verificacao(
    secao, concreto, aco,
    As=As, Nsd=Nsd, Msdx=Msdx, Msdy=Msdy,
    x0=140.0, alfa0=0.0, lambda0=0.93,
)

print(f"Convergencia: {bool(resultado.success)}")
if resultado.success:
    x, alfa, lam = resultado.x
    print(f"x = {x / 10:.6f} cm")
    print(f"alfa = {degrees(alfa):.6f} graus")
    print(f"As = {As / 100:.2f} cm²")
    print(f"lambda = {lam:.8f}")
    print("Resultado: " + ("ATENDE" if lam >= 1 else "NAO ATENDE"))

    # Gráfico do exemplo 5.2: seção, linha neutra, deformações e tensões.
    estado = EstadoDeformacao(secao, x, alfa, concreto)
    figura, eixo = plt.subplots(figsize=(12, 7))
    desenhar_secao(
        secao, area_total=As, estado=estado, ax=eixo, mostrar=False,
        esforcos=(lam * Nsd, lam * Msdx, lam * Msdy),
        tipo_esforcos="resistentes", titulo="Exemplo 5.2 — Verificação",
    )
    desenhar_diagramas_deformacoes_tensoes(eixo, secao, estado, concreto)
else:
    print("A verificação não convergiu.")

# Exibe os dois gráficos após a conclusão dos cálculos.
plt.show()
