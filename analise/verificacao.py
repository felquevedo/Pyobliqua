"""Verificacao no ELU por fator de reserva lambda.

Unidades: mm, N, MPa, N.mm. Angulos em radianos.
"""
from math import pi
import numpy as np
from scipy.optimize import least_squares
from analise.estado_deformacao import EstadoDeformacao
from analise.esforcos import esforcos_resistentes


def resolver_verificacao(secao, concreto, aco, As, Nsd, Msdx, Msdy,
                         x0=None, alfa0=0.0, lambda0=1.0,
                         fator_x_max=20.0, tolerancia_equilibrio=1e-6,
                         multiplas_tentativas=True):
    """Determina x, alfa, lambda tal que (Nr,Mr) = lambda*(Nsd,Msd).

    Retorna scipy OptimizeResult com success indicando residuos suficientemente
    pequenos. lambda < 1 indica resistencia insuficiente no raio de carga.
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
        estado = EstadoDeformacao(secao, x, alfa)
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
            if np.linalg.norm(r.fun) <= tolerancia_equilibrio:
                break
        except (ValueError, FloatingPointError, ZeroDivisionError):
            continue
    if not melhores:
        raise RuntimeError('Nenhum estado inicial foi avaliado.')
    melhor = min(melhores, key=lambda r: np.linalg.norm(r.fun))
    melhor.otimizador_success = bool(melhor.success)
    melhor.norma_residuos = float(np.linalg.norm(melhor.fun))
    melhor.success = melhor.norma_residuos <= tolerancia_equilibrio
    melhor.tentativas = len(melhores)
    return melhor
