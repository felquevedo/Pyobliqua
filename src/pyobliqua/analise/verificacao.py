"""Verificação da seção no estado-limite último por fator de reserva.

O procedimento mantém fixa a área total de armadura ``As`` e procura
``x``, ``alfa`` e ``lambda`` tais que os esforços resistentes sejam
proporcionais às solicitações de cálculo:

    (Nr, Mrx, Mry) = lambda * (Nsd, Msdx, Msdy)

Convenções:
    - Comprimentos e profundidade da linha neutra: mm.
    - Áreas: mm²; tensões: MPa; forças: N; momentos: N·mm.
    - Ângulos: radianos; deformações: adimensionais.
    - ``lambda`` é adimensional; valores inferiores a 1 indicam
      resistência insuficiente ao longo do raio de carregamento,
      desde que a solução de equilíbrio seja válida.

O método usa ``scipy.optimize.least_squares`` e múltiplas estimativas
iniciais opcionais. Os limites de busca são numéricos, não verificações
normativas independentes.
"""
from math import pi
import numpy as np
from scipy.optimize import least_squares
from pyobliqua.analise.estado_deformacao import EstadoDeformacao
from pyobliqua.analise.esforcos import esforcos_resistentes


def resolver_verificacao(secao, concreto, aco, As, Nsd, Msdx, Msdy,
                         x0=None, alfa0=0.0, lambda0=1.0,
                         fator_x_max=20.0, tolerancia_equilibrio=1e-6,
                         multiplas_tentativas=True):
    """Determina o fator de reserva da seção com armadura total fixa.

    Resolve o equilíbrio proporcional das três componentes de esforços,
    minimizando os resíduos normalizados pelo método dos mínimos quadrados.

    Args:
        secao: Seção com ``area``, ``barras`` e método ``altura(alfa)``.
            Cada barra deve ter área definida por ``proporcao``.
        concreto: Modelo constitutivo do concreto.
        aco: Modelo constitutivo do aço.
        As (float): Área total de armadura, em mm².
        Nsd (float): Força normal solicitante, em N.
        Msdx (float): Momento solicitante em torno do eixo x, em N·mm.
        Msdy (float): Momento solicitante em torno do eixo y, em N·mm.
        x0 (float | None): Estimativa inicial da profundidade da linha
            neutra, em mm. Se None, utiliza ``0.4 * secao.altura(0)``.
        alfa0 (float): Estimativa inicial da orientação, em radianos.
        lambda0 (float): Estimativa inicial do fator de reserva.
        fator_x_max (float): Fator multiplicador da altura de referência
            para estabelecer o limite superior de ``x``.
        tolerancia_equilibrio (float): Limite da norma euclidiana dos
            resíduos normalizados para aceitar o equilíbrio.
        multiplas_tentativas (bool): Se True, testa também uma grade de
            ângulos e profundidades iniciais.

    Returns:
        scipy.optimize.OptimizeResult: Resultado com atributos usuais
        ``x`` (vetor ``[x, alfa, lambda]``), ``fun`` e ``message``, além de:

            - ``otimizador_success``: critério de parada do SciPy.
            - ``norma_residuos``: norma euclidiana dos resíduos escalados.
            - ``success``: True se o otimizador convergir e a norma satisfizer a tolerância.
             - ``equilibrio_atendido``: True se a norma satisfizer a tolerância.
            - ``tentativas``: número de otimizações concluídas.

    Raises:
        ValueError: Se ``As`` não for positiva, não houver barras,
            todas as solicitações forem nulas, houver áreas de barras
            fixas ou as proporções não somarem 1.
        RuntimeError: Se nenhuma tentativa de otimização produzir
            resultado utilizável.

    Notes:
        Os resíduos são ``(R - lambda*S) / escala``. As escalas são
        ``max(abs(Nsd), 1e5)`` para força e
        ``max(abs(Msdx), abs(Msdy), 1e7)`` para cada momento.

        Os limites numéricos são ``1e-6 <= x <= fator_x_max*h``,
        ``-pi <= alfa <= pi`` e ``0 <= lambda <= 100``. As estimativas
        iniciais são ajustadas para permanecer dentro desses limites.

        A rotina redefine ``success`` combinando o sucesso original
        do SciPy e o atendimento à tolerância de equilíbrio. Consulte
        ``otimizador_success`` para o critério de parada do SciPy.
        Uma solução com resíduos pequenos não substitui verificações
        normativas ou análise de unicidade do estado resistente.
    """
    if As <= 0 or not secao.barras:
        raise ValueError('As deve ser positiva e deve haver barras.')
    if not any(abs(v) > 0 for v in (Nsd, Msdx, Msdy)):
        raise ValueError('Pelo menos uma solicitacao deve ser nao nula.')
    if any(b.area is not None for b in secao.barras):
        raise ValueError('Defina barras por proporcao para usar As total.')
    if not np.isclose(sum(b.proporcao for b in secao.barras), 1.0):
        raise ValueError('As proporcoes das barras devem somar 1.')
    h = secao.altura(0.0)
    if x0 is None:
        x0 = 0.4*h
    escalas = np.array([max(abs(Nsd), 1e5),
                        max(abs(Msdx), abs(Msdy), 1e7),
                        max(abs(Msdx), abs(Msdy), 1e7)])
    cargas = np.array([Nsd, Msdx, Msdy])
    lb = np.array([1e-6, -pi, 0.0])
    ub = np.array([fator_x_max*h, pi, 100.0])

    def residuos(v):
        x, alfa, lam = v
        estado = EstadoDeformacao(secao, x, alfa, concreto)
        resistente = np.asarray(esforcos_resistentes(
            secao, estado, concreto, aco, area_total=As), dtype=float)
        return (resistente - lam*cargas)/escalas

    def preparar(x, alfa, lam):
        alfa = (alfa + pi) % (2*pi) - pi
        return np.clip([x, alfa, lam], lb+1e-8, ub-1e-8)

    iniciais = [preparar(x0, alfa0, lambda0)]
    if multiplas_tentativas:
        for ang in np.linspace(-pi, pi, 13)[:-1]:
            for frac in (0.08, 0.3, 0.8, 2.0):
                iniciais.append(preparar(frac*h, ang, 1.0))
    melhores = []
    for ini in iniciais:
        try:
            r = least_squares(residuos, ini, bounds=(lb,ub),
                              x_scale=[h,1.0,1.0], max_nfev=1200,
                              ftol=1e-11, xtol=1e-11, gtol=1e-11)
            melhores.append(r)
            if r.success and np.linalg.norm(r.fun) <= tolerancia_equilibrio:
                break
        except (ValueError, FloatingPointError, ZeroDivisionError):
            continue
    if not melhores:
        raise RuntimeError('Nenhum estado inicial foi avaliado.')
    melhor = min(melhores, key=lambda r: np.linalg.norm(r.fun))
    melhor.otimizador_success = bool(melhor.success)
    melhor.norma_residuos = float(np.linalg.norm(melhor.fun))
    melhor.equilibrio_atendido = melhor.norma_residuos <= tolerancia_equilibrio
    melhor.success = bool(melhor.otimizador_success and melhor.equilibrio_atendido)
    melhor.tentativas = len(melhores)
    return melhor
