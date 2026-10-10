"""Desenho de seção com armaduras, linha neutra e regiões de deformação.

Compatível com Secao e EstadoDeformacao do projeto Pyobliqua.
Ângulos em radianos; dimensões em mm; compressão: deformação negativa.
"""
from math import pi, sqrt, cos, sin, isfinite
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle


def _recortar_semiplano(vertices, valor, limite, manter_maior=True):
    """Recorta polígono pelo semiplano valor(p) >= limite (ou <=)."""
    if not vertices:
        return []
    def f(p):
        v = valor(p) - limite
        return v if manter_maior else -v
    saida = []
    anterior = vertices[-1]
    fa = f(anterior)
    for atual in vertices:
        fb = f(atual)
        if (fa >= 0) != (fb >= 0):
            t = fa / (fa - fb)
            saida.append((anterior[0] + t * (atual[0] - anterior[0]),
                          anterior[1] + t * (atual[1] - anterior[1])))
        if fb >= 0:
            saida.append(atual)
        anterior, fa = atual, fb
    return saida


def desenhar_secao(secao, area_total=None, *, ax=None, mostrar=True,
                   salvar_em=None, numerar_barras=False, mostrar_eixos=True,
                   titulo='Seção transversal', unidade='mm',
                   estado=None, x=None, alfa=None, mostrar_linha_neutra=True,
                   mostrar_regioes=True, mostrar_legenda=True,
                   esforcos=None, tipo_esforcos="solicitantes"):
    """Desenha seção, armaduras e, opcionalmente, linha neutra.

    Forneça `estado=EstadoDeformacao(secao, x, alfa)` OU `x` e `alfa`.
    `x` é a profundidade da linha neutra medida da fibra extrema comprimida.
    `alfa` é o ângulo em RADIANOS, na convenção de EstadoDeformacao.
    `esforcos=(N, Mx, My)` em N e N.mm; vetores no plano para momentos.
    N negativo é representado entrando no plano (⊗), positivo saindo (⊙).
    Se não forem fornecidos, desenha somente a geometria.
    """
    if estado is not None and (x is not None or alfa is not None):
        raise ValueError('Use estado OU o par (x, alfa), não ambos.')
    if estado is None and (x is None) != (alfa is None):
        raise ValueError('Informe x e alfa juntos.')
    if estado is None and x is not None:
        from analise.estado_deformacao import EstadoDeformacao
        estado = EstadoDeformacao(secao, x, alfa)
    if estado is not None and estado.secao is not secao:
        raise ValueError('O estado de deformação pertence a outra seção.')

    if esforcos is not None:
        if len(esforcos) != 3 or not all(isfinite(float(v)) for v in esforcos):
            raise ValueError('esforcos deve ser (N, Mx, My), com valores finitos.')
        if tipo_esforcos not in ('solicitantes', 'resistentes'):
            raise ValueError('tipo_esforcos deve ser solicitantes ou resistentes.')

    if ax is None:
        fig, ax = plt.subplots(figsize=(7.5, 7))
    else:
        fig = ax.figure

    def xy(poligono):
        return [(v.x, v.y) for v in poligono.vertices]

    externo = xy(secao.contorno)
    xs, ys = [p[0] for p in externo], [p[1] for p in externo]
    dim = max(max(xs) - min(xs), max(ys) - min(ys), 1.)
    ax.add_patch(Polygon(externo, closed=True, facecolor='#dbeafe',
                         edgecolor='#334155', linewidth=2, zorder=1,
                         label='Concreto (região tracionada)' if estado and mostrar_regioes else 'Concreto'))

    if estado is not None:
        angulo = estado.alfa
        eta_s = estado.eta_s
        eta_ln = eta_s - estado.x
        # eta = -(X-Xc)*sin(alfa) + (Y-Yc)*cos(alfa)
        def eta(p):
            return -(p[0] - secao.xc) * sin(angulo) + (p[1] - secao.yc) * cos(angulo)
        # epsilon(eta) = b*(eta - eta_ln); não presumir que b seja sempre negativo.
        if mostrar_regioes:
            comprimido = _recortar_semiplano(externo, eta, eta_ln,
                                              manter_maior=(estado.b < 0))
            if len(comprimido) >= 3:
                ax.add_patch(Polygon(comprimido, closed=True,
                                     facecolor='#fca5a5', edgecolor='none',
                                     alpha=.82, zorder=2, label='Região comprimida'))
        if mostrar_linha_neutra and abs(estado.b) > 1e-14:
            # eta constante: reta paralela a (cos(alfa), sin(alfa))
            px = secao.xc - eta_ln * sin(angulo)
            py = secao.yc + eta_ln * cos(angulo)
            alcance = 2.5 * dim
            dx, dy = alcance * cos(angulo), alcance * sin(angulo)
            ax.plot([px - dx, px + dx], [py - dy, py + dy],
                    color='#7c3aed', linewidth=2, linestyle='--', zorder=7,
                    label='Linha neutra (ε = 0)')

    # Furos devem cobrir as duas regiões coloridas, sem serem preenchidos.
    for furo in secao.furos:
        ax.add_patch(Polygon(xy(furo), closed=True, facecolor='white',
                             edgecolor='#334155', linewidth=1.8, zorder=4))

    for i, barra in enumerate(secao.barras, start=1):
        area = barra.area
        if area is None and barra.proporcao is not None and area_total is not None:
            area = barra.obter_area(area_total)
        if area is not None and area <= 0:
            raise ValueError(f'Área inválida na barra {i}: {area}')
        raio = sqrt(area / pi) if area is not None else dim * .012
        ax.add_patch(Circle((barra.x, barra.y), raio, facecolor='#9a3412',
                            edgecolor='#431407', linewidth=.8, zorder=6))
        if numerar_barras:
            ax.annotate(str(i), (barra.x, barra.y), xytext=(5, 5),
                        textcoords='offset points', fontsize=8, zorder=8)

    if mostrar_eixos:
        ax.axhline(secao.yc, color='#2563eb', ls=':', lw=1.0, alpha=.75, zorder=5)
        ax.axvline(secao.xc, color='#2563eb', ls=':', lw=1.0, alpha=.75, zorder=5)
        ax.plot(secao.xc, secao.yc, '+', color='#1d4ed8', ms=11, mew=2, zorder=8)

    # Representação vetorial das resultantes no centroide da seção.
    # N<0 (compressão) entra no plano: ⊗; N>0 (tração) sai: ⊙.
    # Mx e My são vetores axiais no plano, com sentido definido pelo sinal.
    if esforcos is not None:
        N, Mx, My = map(float, esforcos)
        cor_mx, cor_my = '#dc2626', '#1d4ed8'
        comprimento = .30 * dim
        cx, cy = secao.xc, secao.yc
        sufixo = 'sd' if tipo_esforcos == 'solicitantes' else 'r'
        if abs(N) > 1e-10:
            simbolo = '⊗' if N < 0 else '⊙'
            ax.text(cx, cy, simbolo, fontsize=23, color='#111827',
                    ha='center', va='center', zorder=12,
                    bbox=dict(facecolor='white', edgecolor='none', alpha=.8, pad=.05))
            ax.annotate(f'N$_{{{sufixo}}}$ = {N/1e3:+.2f} kN',
                        xy=(cx,cy), xytext=(cx+.07*dim,cy-.11*dim),
                        fontsize=9, color='#111827', zorder=12)
        else:
            ax.text(cx,cy, 'N = 0', ha='center',va='center',fontsize=9,
                    color='#111827',zorder=12,
                    bbox=dict(facecolor='white',alpha=.85,edgecolor='none'))
        # Setas dos dois momentos partem do mesmo centroide do símbolo de N.
        if abs(Mx) > 1e-8:
            direcao = 1 if Mx > 0 else -1
            ax.annotate('', xy=(cx+direcao*comprimento,cy),
                        xytext=(cx,cy),
                        arrowprops=dict(arrowstyle='-|>', lw=2.8,
                                        mutation_scale=18,color=cor_mx),zorder=11)
            ax.text(cx+direcao*comprimento/2,cy-.055*dim,
                    f'M$_{{x,{sufixo}}}$ = {Mx/1e6:+.2f} kN·m',
                    color=cor_mx,fontsize=9,ha='center',va='top',zorder=12)
        if abs(My) > 1e-8:
            direcao = 1 if My > 0 else -1
            ax.annotate('', xy=(cx,cy+direcao*comprimento),
                        xytext=(cx,cy),
                        arrowprops=dict(arrowstyle='-|>', lw=2.8,
                                        mutation_scale=18,color=cor_my),zorder=11)
            ax.text(cx-.04*dim,cy+direcao*comprimento/2,
                    f'M$_{{y,{sufixo}}}$ = {My/1e6:+.2f} kN·m',
                    color=cor_my,fontsize=9,ha='right',va='center',
                    rotation=90,zorder=12)

    margem = (.20 if esforcos is not None else .10) * dim
    ax.set_xlim(min(xs)-margem, max(xs)+margem)
    ax.set_ylim(min(ys)-margem, max(ys)+margem)
    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel(f'x ({unidade})')
    ax.set_ylabel(f'y ({unidade})')
    ax.set_title(titulo)
    if estado is not None:
        ax.text(.02, .02,
                f'x = {estado.x:.2f} {unidade}  |  α = {estado.alfa*180/pi:.2f}°',
                transform=ax.transAxes, fontsize=9, va='bottom',
                bbox=dict(facecolor='white', edgecolor='#cbd5e1', alpha=.95))
    if mostrar_legenda:
        ax.legend(loc='upper left', fontsize=8)
    fig.tight_layout()
    if salvar_em:
        fig.savefig(salvar_em, dpi=200, bbox_inches='tight')
    if mostrar:
        plt.show()
    return fig, ax
