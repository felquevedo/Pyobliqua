"""Curva Mx-My para N fixo e armadura fixa.
Execute na raiz do projeto: python curva_interacao_N_fixo.py
Requer scipy, numpy e matplotlib.
"""
from math import radians
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq

from secao.secao import Secao
from secao.barra import Barra
from materiais.concreto import Concreto
from materiais.aco import Aco
from analise.estado_deformacao import EstadoDeformacao
from analise.esforcos import esforcos_resistentes

AS = 2000.0            # mm2, quatro barras de 500 mm2
N_ALVO = -1000e3       # N; compressao negativa
MX_ALVO = 150e6        # N.mm
MY_ALVO = 80e6         # N.mm
ANGULOS = np.arange(-180, 180, 2.0)  # graus
N_AMOSTRAS_X = 140
TOL_N = 1.0            # N, tolerancia de fechamento da normal


def calcular(secao, concreto, aco, x, alfa):
    estado = EstadoDeformacao(secao, float(x), float(alfa))
    return np.asarray(
        esforcos_resistentes(secao, estado, concreto, aco, area_total=AS),
        dtype=float
    )


def raizes_para_angulo(secao, concreto, aco, alfa):
    h = secao.altura(alfa)
    # Escala logaritmica: cobre linhas neutras rasas e compressao total.
    xs = np.geomspace(max(1e-4 * h, 1e-5), 20.0 * h, N_AMOSTRAS_X)
    # Acrescenta transicoes de dominio e suas vizinhancas.
    d = secao.altura_util(alfa)
    transicoes = [d * (0.0035 / 0.0135), d, h]
    for t in transicoes:
        if t > 0:
            xs = np.append(xs, [t * (1 - 1e-7), t, t * (1 + 1e-7)])
    xs = np.unique(np.sort(xs))

    def erro_normal(x):
        return calcular(secao, concreto, aco, x, alfa)[0] - N_ALVO

    erros = []
    for x in xs:
        try:
            erros.append(float(erro_normal(x)))
        except (ValueError, ZeroDivisionError, FloatingPointError):
            erros.append(float("nan"))

    raizes = []
    for i in range(len(xs) - 1):
        e1, e2 = erros[i], erros[i + 1]
        if not (np.isfinite(e1) and np.isfinite(e2)):
            continue
        if abs(e1) <= TOL_N:
            raiz = float(xs[i])
        elif e1 * e2 < 0:
            try:
                raiz = float(brentq(erro_normal, xs[i], xs[i + 1],
                                   xtol=1e-8, rtol=1e-12))
            except (ValueError, ZeroDivisionError, FloatingPointError):
                continue
        else:
            continue
        if not any(abs(raiz - r) <= max(1e-4, 1e-6 * raiz) for r in raizes):
            raizes.append(raiz)
    return sorted(raizes)


def main():
    secao = Secao(
        contorno=[(0, 0), (400, 0), (400, 600), (0, 600)],
        barras=[
            Barra(40, 40, proporcao=.25),
            Barra(360, 40, proporcao=.25),
            Barra(360, 560, proporcao=.25),
            Barra(40, 560, proporcao=.25),
        ],
    )
    concreto, aco = Concreto(fck=30), Aco(fyk=500)
    pontos = []
    sem_raiz = 0

    for angulo in ANGULOS:
        alfa = radians(float(angulo))
        raizes = raizes_para_angulo(secao, concreto, aco, alfa)
        if not raizes:
            sem_raiz += 1
        for x in raizes:
            n, mx, my = calcular(secao, concreto, aco, x, alfa)
            if abs(n - N_ALVO) > TOL_N:
                continue
            distancia = np.hypot((mx - MX_ALVO) / 1e6,
                                  (my - MY_ALVO) / 1e6)
            pontos.append((float(angulo), x, n / 1e3,
                           mx / 1e6, my / 1e6, distancia))

    if not pontos:
        print("Nao foram encontradas raizes N(x, alfa) = N_alvo.")
        print("Isso nao prova que nao existam; amplie a busca em x.")
        return

    pontos.sort(key=lambda p: (p[0], p[1]))
    tabela = np.asarray(pontos, dtype=float)
    arquivo_csv = Path("curva_interacao_N_fixo.csv")
    np.savetxt(arquivo_csv, tabela, delimiter=",",
               header="alfa_graus,x_mm,N_kN,Mx_kNm,My_kNm,distancia_kNm",
               comments="", fmt="%.10g")

    melhor = min(pontos, key=lambda p: p[-1])
    print(f"As = {AS:.1f} mm2; N alvo = {N_ALVO/1e3:.1f} kN")
    print(f"Angulos avaliados: {len(ANGULOS)}; sem raiz: {sem_raiz}")
    print(f"Estados com N equilibrado: {len(pontos)}")
    print("Ponto solicitado: Mx=150.00 kN.m, My=80.00 kN.m")
    print("\n=== PONTO MAIS PROXIMO NA AMOSTRAGEM ===")
    print(f"alfa={melhor[0]:.2f} graus; x={melhor[1]:.3f} mm; "
          f"N={melhor[2]:.3f} kN")
    print(f"Mx={melhor[3]:.3f} kN.m; My={melhor[4]:.3f} kN.m")
    print(f"Distancia no plano Mx-My = {melhor[5]:.3f} kN.m")
    print("AVISO: distancia amostrada nao prova viabilidade ou inviabilidade.")
    print(f"Dados salvos em: {arquivo_csv.resolve()}")

    fig, ax = plt.subplots(figsize=(8, 7))
    # Plotar cada ramo separadamente para nao unir raizes distintas.
    # A nuvem de pontos e mais segura que ligar pontos de ramos desconhecidos.
    ax.scatter(tabela[:, 3], tabela[:, 4], s=12,
               label="Estados com N = -1000 kN")
    ax.scatter([MX_ALVO/1e6], [MY_ALVO/1e6], marker="x", s=110,
               label="Solicitacao (150, 80)")
    ax.scatter([melhor[3]], [melhor[4]], marker="o", s=65,
               facecolors="none", edgecolors="black",
               label="Amostra mais proxima")
    ax.set_xlabel("Mx (kN.m)")
    ax.set_ylabel("My (kN.m)")
    ax.set_title("Interacao Mx-My | N = -1000 kN | As = 2000 mm2")
    ax.grid(True, alpha=.3)
    ax.axis("equal")
    ax.legend()
    fig.tight_layout()
    arquivo_png = Path("curva_interacao_N_fixo.png")
    fig.savefig(arquivo_png, dpi=180)
    print(f"Grafico salvo em: {arquivo_png.resolve()}")
    plt.show()


if __name__ == "__main__":
    main()
