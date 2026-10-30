"""Visualização do diagrama de interação Mx–My (unidades de entrada N·mm).

Este módulo não realiza cálculos estruturais e não certifica a envoltória.
"""
import numpy as np


def desenhar_diagrama_interacao(ax, resultado, momento_solicitante=None,
                                ligar_pontos=True, aproveitamento=None):
    """Desenha estados resistentes no eixo Matplotlib fornecido.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Eixo existente, inclusive quando incorporado ao Tkinter.
    resultado : analise.interacao.ResultadoInteracao
        Resultado do cálculo de interação.
    momento_solicitante : tuple[float, float] | None
        (Msdx, Msdy) em N·mm.
    ligar_pontos : bool
        Conecta visualmente apenas quando há uma raiz por orientação
        e nenhuma orientação sem solução; não representa certificação.
    """
    ax.clear()
    pontos = resultado.momentos_kNm
    if len(pontos):
        if ligar_pontos and not resultado.angulos_sem_solucao:
            angulos = np.array([p.alfa for p in resultado.pontos])
            if len(np.unique(np.round(angulos, 10))) == len(angulos) and len(pontos) >= 3:
                ordem = np.argsort(angulos)
                curva = np.vstack([pontos[ordem], pontos[ordem][0]])
                ax.plot(curva[:, 0], curva[:, 1], '--', linewidth=1,
                        label='Ligação visual (não validada)')
        ax.scatter(pontos[:, 0], pontos[:, 1], s=18,
                   label='Estados resistentes', zorder=3)
    if momento_solicitante is not None:
        mx, my = momento_solicitante
        ax.scatter([mx/1e6], [my/1e6], marker='x', s=125,
                   color='tab:red', linewidths=2.5, zorder=4,
                   label='Solicitação')
    if aproveitamento is not None and aproveitamento.confiavel_para_interpolacao:
        rx = aproveitamento.Mx_resistente / 1e6
        ry = aproveitamento.My_resistente / 1e6
        ax.scatter([rx], [ry], marker='o', s=85, facecolors='none',
                   edgecolors='tab:green', linewidths=2, zorder=5,
                   label=f'Resistência interpolada (λ≈{aproveitamento.lambda_estimado:.4f})')
        if momento_solicitante is not None:
            ax.plot([0, momento_solicitante[0]/1e6],
                    [0, momento_solicitante[1]/1e6], ':',
                    color='tab:red', linewidth=1, zorder=2)
    ax.axhline(0, color='gray', linewidth=.8)
    ax.axvline(0, color='gray', linewidth=.8)
    ax.set_xlabel('Mx (kN·m)')
    ax.set_ylabel('My (kN·m)')
    ax.set_title(f'Diagrama Mx–My | N = {resultado.Nsd/1e3:g} kN | '
                 f'As = {resultado.As/100:g} cm²')
    ax.grid(True, alpha=.25)
    ax.set_aspect('equal', adjustable='datalim')
    ax.legend(loc='upper center', bbox_to_anchor=(.5, -.13),
              ncol=2, fontsize=8)
    return ax
