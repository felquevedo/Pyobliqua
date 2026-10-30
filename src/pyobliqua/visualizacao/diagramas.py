"""Desenho independente da interface Tkinter dos diagramas de deformações e tensões."""

def desenhar_diagramas_deformacoes_tensoes(ax, secao, estado, concreto):
    """Diagramas ao lado da seção, com eixo longitudinal normal à linha neutra.

    O diagrama de tensões representa somente o concreto (tração desprezada).
    Deformações negativas indicam compressão. Não modifica o cálculo.
    """
    import numpy as np
    from math import sin, cos

    alfa = estado.alfa
    n = np.array([-sin(alfa), cos(alfa)])  # direção eta: normal à LN
    t = np.array([cos(alfa), sin(alfa)])   # direção paralela à LN
    pontos = np.array([(v.x, v.y) for v in secao.contorno.vertices], dtype=float)
    origem = np.array([secao.xc, secao.yc], dtype=float)
    proj_t = (pontos - origem) @ t
    proj_n = (pontos - origem) @ n
    eta_min, eta_max = float(min(proj_n)), float(max(proj_n))
    dim = max(np.ptp(pontos[:, 0]), np.ptp(pontos[:, 1]), 1.0)
    h = eta_max - eta_min
    etas = np.linspace(eta_min, eta_max, 180)
    deformacoes = np.array([estado.deformacao(float(eta)) for eta in etas])
    # Limita apenas a representação gráfica à deformação última do material.
    # A avaliação dos esforços resistentes permanece nos módulos de análise.
    tensoes = np.array([concreto.tensao(max(float(eps), -concreto.epsilon_cu))
                        for eps in deformacoes])

    def plotar_diagrama(indice, valores, cor, nome, unidade):
        # Baselines paralelas à normal da LN; valores plotados paralelos à LN.
        deslocamento = max(proj_t) + (0.27 + 0.69 * indice) * dim
        base = origem + np.outer(etas, n) + deslocamento * t
        maximo = max(float(np.max(np.abs(valores))), 1e-12)
        amplitude = 0.43 * dim
        perfil = base + np.outer(-valores / maximo * amplitude, t)
        ax.plot(base[:, 0], base[:, 1], color='#64748b', lw=1.1, ls='--', zorder=13)
        ax.plot(perfil[:, 0], perfil[:, 1], color=cor, lw=2, zorder=14)
        ax.fill(np.r_[base[:, 0], perfil[::-1, 0]],
                np.r_[base[:, 1], perfil[::-1, 1]], color=cor, alpha=.14, zorder=12)
        for eta, valor in ((etas[0], valores[0]), (etas[-1], valores[-1])):
            ponto = origem + eta * n + (deslocamento - valor / maximo * amplitude) * t
            ax.annotate(f'{valor:+.2f} {unidade}', xy=ponto, xytext=(4, 4),
                        textcoords='offset points', fontsize=7, color=cor, zorder=15)
        cabecalho = origem + (eta_max + .13 * max(h, dim)) * n + deslocamento * t
        ax.text(*cabecalho, nome, fontsize=9, color=cor, fontweight='bold',
                ha='center', va='center', zorder=15)
        return np.vstack([base, perfil, cabecalho])

    # Destaca as deformações das armaduras extremas no perfil linear.
    etas_barras = [(np.array([b.posicao.x, b.posicao.y]) - origem) @ n
                   for b in secao.barras]
    if etas_barras:
        for titulo_barra, eta_barra, marcador in (
            ('Armadura superior', max(etas_barras), 'o'),
            ('Armadura inferior', min(etas_barras), 's'),
        ):
            eps_barra = estado.deformacao(float(eta_barra)) * 1000
            max_eps = max(float(np.max(np.abs(deformacoes * 1000))), 1e-12)
            deslocamento = max(proj_t) + .27 * dim
            ponto = origem + eta_barra * n + (deslocamento - eps_barra / max_eps * .43 * dim) * t
            ax.scatter([ponto[0]], [ponto[1]], marker=marcador, s=45,
                       facecolor='white', edgecolor='#14532d', linewidth=1.6, zorder=20)
            ax.annotate(f'{titulo_barra}: {eps_barra:+.3f} ‰', xy=ponto,
                        xytext=(8, -12 if marcador == 'o' else 12),
                        textcoords='offset points', fontsize=8, color='#14532d', zorder=21,
                        bbox=dict(facecolor='white', alpha=.82, edgecolor='none', pad=1))

    pts_eps = plotar_diagrama(0, deformacoes * 1000, '#15803d', 'Deformações', '‰')
    pts_sig = plotar_diagrama(1, tensoes, '#b91c1c', 'Tensões no concreto', 'MPa')
    conjunto = np.vstack([pontos, pts_eps, pts_sig])
    borda = .16 * dim
    ax.set_xlim(min(conjunto[:, 0]) - borda, max(conjunto[:, 0]) + borda)
    ax.set_ylim(min(conjunto[:, 1]) - borda, max(conjunto[:, 1]) + borda)

