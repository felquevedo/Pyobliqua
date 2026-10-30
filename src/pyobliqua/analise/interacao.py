"""Diagrama de interação Mx-My para força normal constante.

Unidades internas: N, N.mm, mm, mm² e radianos.
Compressão negativa. O resultado contém pontos de equilíbrio normal;
não constitui, por si só, certificação da envoltória resistente global.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.optimize import brentq
from pyobliqua.analise.estado_deformacao import EstadoDeformacao
from pyobliqua.analise.esforcos import esforcos_resistentes


@dataclass(frozen=True)
class PontoInteracao:
    alfa: float
    x: float
    N: float
    Mx: float
    My: float
    dominio: str
    residuo_normal: float


@dataclass
class ResultadoInteracao:
    Nsd: float
    As: float
    pontos: list[PontoInteracao]
    angulos_sem_solucao: list[float]
    n_angulos: int

    @property
    def momentos_kNm(self):
        return np.asarray([(p.Mx / 1e6, p.My / 1e6) for p in self.pontos], dtype=float).reshape(-1, 2)


@dataclass(frozen=True)
class ResultadoAproveitamento:
    """Interseção radial com a polilinha AMOSTRADA (não certificada)."""
    lambda_estimado: float | None
    Mx_resistente: float | None
    My_resistente: float | None
    numero_intersecoes: int
    confiavel_para_interpolacao: bool
    observacao: str


def estimar_aproveitamento_radial(resultado, Msdx, Msdy):
    """Estima λ na direção da solicitação a partir do diagrama amostrado.

    Os momentos estão em N.mm. Intersecta a semirreta t*(Msdx,Msdy),
    t>=0, com os segmentos da polilinha angular. Só considera a
    interpolação utilizável quando existe exatamente uma raiz por ângulo,
    nenhuma orientação ausente e uma única interseção positiva.
    Não substitui uma verificação resistente com equilíbrio completo.
    """
    if not all(math.isfinite(v) for v in (Msdx, Msdy)):
        raise ValueError('Momentos solicitantes devem ser finitos.')
    norma = math.hypot(Msdx, Msdy)
    if norma == 0:
        return ResultadoAproveitamento(None, None, None, 0, False,
                                       'Solicitação de momentos nula: direção radial indefinida.')
    pts = resultado.pontos
    alfas = [round(p.alfa, 10) for p in pts]
    malha_completa = (len(pts) == resultado.n_angulos and
                      len(set(alfas)) == resultado.n_angulos and
                      not resultado.angulos_sem_solucao)
    if not malha_completa or len(pts) < 4:
        return ResultadoAproveitamento(None, None, None, 0, False,
                                       'Amostragem incompleta ou múltiplos ramos: interpolação radial suspensa.')
    ordenados = sorted(pts, key=lambda p: p.alfa)
    escala = max(norma, max(math.hypot(p.Mx, p.My) for p in pts), 1.)
    # Trabalha com valores adimensionais para estabilidade numérica.
    dx, dy = Msdx/escala, Msdy/escala
    cruzamentos = []
    for a, b in zip(ordenados, ordenados[1:] + ordenados[:1]):
        ax, ay = a.Mx/escala, a.My/escala
        vx, vy = (b.Mx-a.Mx)/escala, (b.My-a.My)/escala
        det = dx*(-vy) - (-vx)*dy
        if abs(det) < 1e-13:
            continue
        # t*d = a + u*v; determinante [d,-v] [t,u] = a
        t = (-ax*vy + vx*ay)/det
        u = (dx*ay - dy*ax)/det
        if t >= 0 and -1e-10 <= u <= 1+1e-10:
            cruzamentos.append(t)
    cruzamentos.sort()
    distintos = []
    for t in cruzamentos:
        if not distintos or abs(t-distintos[-1]) > 1e-7*max(1,abs(t)):
            distintos.append(t)
    if len(distintos) != 1:
        return ResultadoAproveitamento(None, None, None, len(distintos), False,
                'A semirreta interceptou a polilinha zero ou várias vezes; λ indeterminado.')
    t = distintos[0]
    return ResultadoAproveitamento(t, t*Msdx, t*Msdy, 1, True,
                'λ interpolado na polilinha amostrada; não é verificação estrutural certificada.')


def calcular_diagrama_interacao(secao, concreto, aco, As, Nsd,
                               n_angulos=72, n_profundidades=100,
                               tolerancia_normal=1e-5, angulos=None):
    """Resolve Nr(x, alfa) = Nsd para diferentes orientações.

    Os estados de deformação e a transição dos domínios 2-3 utilizam
    epsilon_cu do concreto, conforme a formulação de 2014.

    Varre x desde tração quase uniforme até compressão quase uniforme,
    buscando TODAS as mudanças de sinal detectáveis da equação normal.
    Não conecta automaticamente ramos diferentes nem classifica segurança.

    Parameters
    ----------
    As : float
        Área total de aço em mm².
    Nsd : float
        Normal solicitante em N (compressão negativa).
    n_angulos : int
        Orientações igualmente espaçadas em [0, 2*pi).
    n_profundidades : int
        Número de intervalos de busca por orientação.
    tolerancia_normal : float
        Erro relativo máximo, normalizado pela escala de forças.
    """
    if not math.isfinite(As) or As <= 0:
        raise ValueError('As deve ser positiva e finita (mm²).')
    if not math.isfinite(Nsd):
        raise ValueError('Nsd deve ser finito (N).')
    if angulos is not None:
        angulos = sorted(set(float(a) % (2 * math.pi) for a in angulos))
        n_angulos = len(angulos)
    if n_angulos < (1 if angulos is not None else 4) or n_profundidades < 20:
        raise ValueError('Use n_angulos >= 4 e n_profundidades >= 20.')
    if tolerancia_normal <= 0:
        raise ValueError('tolerancia_normal deve ser positiva.')

    escala = max(abs(Nsd), concreto.sigma_cd * secao.area, 1.0)
    pontos = []
    sem_solucao = []
    for alfa in (angulos if angulos is not None else np.linspace(0.0, 2 * math.pi, n_angulos, endpoint=False)):
        h = secao.altura(float(alfa))
        d = secao.altura_util(float(alfa))
        if h <= 0 or d <= 0:
            sem_solucao.append(float(alfa))
            continue
        # x negativo: tração em toda a seção; x grande: compressão quase uniforme.
        # Inclui explicitamente transições entre domínios.
        x_min = -max(3.0 * h, 3.0 * d)
        x_max = 1000.0 * h
        transicoes = [0.0, (concreto.epsilon_cu / (0.010 + concreto.epsilon_cu)) * d, d, h]
        positivos = np.geomspace(max(1e-8 * h, 1e-8), x_max, n_profundidades + 1)
        negativos = -np.geomspace(max(1e-8 * h, 1e-8), -x_min, n_profundidades + 1)
        malha = np.unique(np.r_[negativos, 0.0, positivos, transicoes])
        malha.sort()
        cache = {}

        def calcular(x):
            x = float(x)
            if x not in cache:
                estado = EstadoDeformacao(secao, x, float(alfa), concreto=concreto)
                nr, mx, my = esforcos_resistentes(secao, estado, concreto, aco, area_total=As)
                cache[x] = (float(nr), float(mx), float(my), estado.dominio)
            return cache[x]

        def f(x):
            return calcular(x)[0] - Nsd

        amostras = []
        for x in malha:
            try:
                y = f(x)
                amostras.append(y if math.isfinite(y) else float('nan'))
            except (ValueError, ZeroDivisionError, FloatingPointError):
                amostras.append(float('nan'))

        raizes = []
        for i in range(len(malha) - 1):
            xa, xb = float(malha[i]), float(malha[i + 1])
            fa, fb = amostras[i], amostras[i + 1]
            if math.isfinite(fa) and abs(fa) / escala <= tolerancia_normal:
                raizes.append(xa)
            if math.isfinite(fa) and math.isfinite(fb) and fa * fb < 0:
                try:
                    raizes.append(float(brentq(f, xa, xb, xtol=1e-9, rtol=1e-12)))
                except (ValueError, ZeroDivisionError, FloatingPointError):
                    continue
        if math.isfinite(amostras[-1]) and abs(amostras[-1]) / escala <= tolerancia_normal:
            raizes.append(float(malha[-1]))

        aceitos = 0
        for x in sorted(raizes):
            if any(abs(x - p.x) < max(1e-6, h * 1e-8) and abs(float(alfa) - p.alfa) < 1e-10
                   for p in pontos[-len(raizes):]):
                continue
            nr, mx, my, dominio = calcular(x)
            residuo = abs(nr - Nsd) / escala
            if residuo <= tolerancia_normal:
                pontos.append(PontoInteracao(float(alfa), x, nr, mx, my, dominio, residuo))
                aceitos += 1
        if not aceitos:
            sem_solucao.append(float(alfa))
    return ResultadoInteracao(Nsd, As, pontos, sem_solucao, n_angulos)




def plotar_diagrama_interacao(resultado, mostrar=True, salvar_em=None):
    """Plota pontos resistentes Mx-My (kN.m) sem presumir uma envoltória.

    Quando existe exatamente um ponto por orientação, liga-os na ordem
    angular apenas para facilitar a inspeção visual. A polilinha não é
    uma certificação da fronteira resistente.
    """
    import matplotlib.pyplot as plt

    pontos = resultado.momentos_kNm
    if not len(pontos):
        raise ValueError('Nenhum ponto resistente disponível para plotagem.')
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(pontos[:, 0], pontos[:, 1], s=30, label='Estados resistentes')
    angulos = [p.alfa for p in resultado.pontos]
    unicos = len(set(round(a, 10) for a in angulos)) == len(angulos)
    if unicos and len(pontos) >= 3:
        ordem = np.argsort(angulos)
        ordenados = pontos[ordem]
        fechados = np.vstack([ordenados, ordenados[0]])
        ax.plot(fechados[:, 0], fechados[:, 1], '--', linewidth=1,
                label='Ligação visual (não validada)')
    ax.axhline(0, linewidth=0.8, color='gray')
    ax.axvline(0, linewidth=0.8, color='gray')
    ax.set(xlabel='Mx (kN·m)', ylabel='My (kN·m)',
           title=f'Diagrama Mx–My | N = {resultado.Nsd/1000:g} kN | '
                 f'As = {resultado.As/100:g} cm²')
    ax.set_aspect('equal', adjustable='datalim')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    fig.tight_layout()
    if salvar_em is not None:
        fig.savefig(salvar_em, dpi=180)
    if mostrar:
        plt.show()
    return fig, ax


def _teste_basico():
    """Teste integrado do diagrama para seção retangular com armadura simétrica."""
    from secao.secao import Secao
    from secao.barra import Barra
    from materiais.concreto import Concreto
    from materiais.aco import Aco

    secao = Secao(
        contorno=[(0, 0), (400, 0), (400, 600), (0, 600)],
        barras=[Barra(x, y, proporcao=0.25) for x, y in
                [(40, 40), (360, 40), (360, 560), (40, 560)]],
    )
    resultado = calcular_diagrama_interacao(
        secao, Concreto(30), Aco(500), As=2000.0, Nsd=-1e6,
        n_angulos=24, n_profundidades=60,
    )
    assert len(resultado.pontos) >= 20, 'Poucos pontos de equilíbrio encontrados.'
    assert all(p.residuo_normal <= 1e-5 for p in resultado.pontos)
    assert all(math.isfinite(p.Mx) and math.isfinite(p.My) for p in resultado.pontos)
    print(f'OK: {len(resultado.pontos)} pontos; '
          f'{len(resultado.angulos_sem_solucao)} orientações sem solução.')
    print('Primeiros pares (Mx, My), kN.m:')
    for mx, my in resultado.momentos_kNm[:5]:
        print(f'  {mx:12.4f} {my:12.4f}')
    plotar_diagrama_interacao(resultado)


if __name__ == '__main__':
    _teste_basico()
