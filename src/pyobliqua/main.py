"""Exemplos 5.1 e 5.2: uso didático do núcleo de cálculo do Pyobliqua.

Execute na raiz do projeto (após instalar com pip install -e .):
    python -m pyobliqua.main

Entrada/saída: unidades definidas no Modelo; núcleo: mm, N, N.mm e MPa.
Convenção: compressão negativa.
"""

from math import degrees
import matplotlib.pyplot as plt
from pyobliqua import Modelo, Unidades

# Definindo as unidades do modelo. As unidades geométricas são fixas: cm.
modelo = Modelo(Unidades(forca="kN", momento="kN.m", tensao="MPa"))

# Materiais usados nos dois exemplos
concreto = modelo.concreto(fck=20, gamma_c=1.4)
aco = modelo.aco(fyk=500, gamma_s=1.15)

# ============================================================
# EXEMPLO 5.1 — DIMENSIONAMENTO DA ARMADURA
# ============================================================
print("\nEXEMPLO 5.1 — DIMENSIONAMENTO")

# Seção quadrada de 85 x 85 cm.
contorno = [(0, 0), 
            (85, 0), 
            (85, 85), 
            (0, 85)]

# Definição do furo quadrado de 25 x 25 cm.
furo = [(30, 30), 
        (55, 30), 
        (55, 55), 
        (30, 55)]

# Posição das 20 barras de aço cm.
barras = [
    (5, 5), (20, 5), (35, 5), (50, 5), (65, 5), (80, 5),
    (5, 20), (5, 35), (5, 50), (5, 65), (5, 80),
    (80, 20), (80, 35), (80, 50), (80, 65), (80, 80),
    (20, 80), (35, 80), (50, 80), (65, 80),
]

# Definição da seção e a proporção de cada barra
secao = modelo.secao(
    contorno=contorno, 
    furos=[furo],
    barras=[modelo.barra(x, y, proporcao=1 / 20) for x, y in barras],
)

# Esforços solicitantes nas unidades escolhidas
Nsd = -200
Msdx = -500
Msdy = 500

# Chamando o dimensionamento da armadura
resultado = modelo.dimensionar(
    secao, concreto, aco, Nsd, Msdx, Msdy,
)

# Imprimindo os resultados
print(f"Convergencia: {bool(resultado.success)}")
if resultado.success:
    x, alfa, As = resultado.x
    print(f"x = {x:.6f} cm")
    print(f"alfa = {degrees(alfa):.6f} graus")
    print(f"As = {As:.5f} cm²")

    modelo.grafico(resultado, esforcos=(Nsd, Msdx, Msdy), titulo="Exemplo 5.1 — Dimensionamento")
else:
    print("O dimensionamento não convergiu.")

# ============================================================
# EXEMPLO 5.2 — VERIFICAÇÃO DE UMA ARMADURA EXISTENTE
# ============================================================
print("\nEXEMPLO 5.2 — VERIFICACAO")

# Contorno da seção I de concreto com mesas diferentes
contorno = [
    (22.5, 0), 
    (47.5, 0), 
    (47.5, 10), 
    (42.5, 15),
    (42.5, 95), 
    (70, 110), 
    (70, 120), 
    (0, 120),
    (0, 110), 
    (27.5, 95), 
    (27.5, 15), 
    (22.5, 10),
]

# Posição das 15 barras de aço cm.
barras = [
    (27.5, 5), 
    (32.5, 5), 
    (37.5, 5), 
    (42.5, 5),
    (27.5, 8), 
    (32.5, 8), 
    (37.5, 8), 
    (42.5, 8),
    (32.5, 11), 
    (37.5, 11),
    (5, 115), 
    (20, 115), 
    (35, 115), 
    (50, 115), 
    (65, 115),
]

secao = modelo.secao(
    contorno=contorno,
    barras=[modelo.barra(x, y, proporcao=1 / 15) for x, y in barras],
)

# Área de aço conhecida: 30 cm²
As = 30

# Esforços solicitantes nas unidades escolhidas
Nsd = 0
Msdx = -1000
Msdy = 0

# Chamando a verificação da armadura existente
resultado = modelo.verificar(
    secao, concreto, aco,
    As=As, Nsd=Nsd, Msdx=Msdx, Msdy=Msdy,
)

# Imprimindo os resultados
print(f"Convergencia: {bool(resultado.success)}")
if resultado.success:
    x, alfa, lam = resultado.x
    print(f"x = {x:.6f} cm")
    print(f"alfa = {degrees(alfa):.6f} graus")
    print(f"As = {As:.2f} cm²")
    print(f"lambda = {lam:.8f}")
    print("Resultado: " + ("ATENDE" if lam >= 1 else "NAO ATENDE"))

    modelo.grafico(resultado, As=As, esforcos=(Nsd, Msdx, Msdy), titulo="Exemplo 5.2 — Verificação")
else:
    print("A verificação não convergiu.")

# Exibe os dois gráficos após a conclusão dos cálculos.
plt.show()
