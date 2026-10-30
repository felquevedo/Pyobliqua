"""Resolução numérica do equilíbrio resistente de seções de concreto armado.

O dimensionamento procura a profundidade da linha neutra ``x``, o ângulo
``alfa`` e a área total de armadura ``As`` que equilibram as solicitações.
O problema é resolvido por mínimos quadrados não lineares com limites,
utilizando ``scipy.optimize.least_squares``.

Convenções:
    - ``x`` em mm, ``alfa`` em radianos e ``As`` em mm².
    - Forças normais em N e momentos em N·mm.
    - Resíduos são adimensionais após normalização pelas escalas.
    - A convergência do otimizador não garante, por si só, o equilíbrio.

Os limites numéricos de busca não substituem verificações normativas.
"""

import numpy as np

from scipy.optimize import least_squares
from math import pi

from pyobliqua.analise.estado_deformacao import EstadoDeformacao
from pyobliqua.analise.esforcos import esforcos_resistentes


def residuos_equilibrio(
    variaveis,
    secao,
    concreto,
    aco,
    Nsd,
    Msdx,
    Msdy,
    escala_N,
    escala_M
):
    """Calcula os resíduos adimensionais de equilíbrio da seção.

    Args:
        variaveis (array_like): Sequência ``(x, alfa, As)``, em mm,
            radianos e mm², respectivamente.
        secao: Geometria e armaduras da seção.
        concreto: Modelo constitutivo do concreto.
        aco: Modelo constitutivo do aço.
        Nsd (float): Força normal solicitante, em N.
        Msdx (float): Momento solicitante em torno de x, em N·mm.
        Msdy (float): Momento solicitante em torno de y, em N·mm.
        escala_N (float): Escala de normalização da força, em N.
        escala_M (float): Escala de normalização dos momentos, em N·mm.

    Returns:
        numpy.ndarray: Três resíduos ``[(Nr-Nsd)/escala_N,
        (Mrx-Msdx)/escala_M, (Mry-Msdy)/escala_M]``. Para ``x <= 0``
        ou ``As < 0``, retorna a penalidade ``[1e6, 1e6, 1e6]``.

    Notes:
        A função avalia o estado de deformação e os esforços resistentes
        correspondentes à estimativa atual das incógnitas.
    """

    x, alfa, As = variaveis

    # Evita avaliar estados fora do domínio adotado.
    if x <= 0 or As < 0:
        return np.array([1e6, 1e6, 1e6])

    estado = EstadoDeformacao(
        secao=secao,
        x=x,
        alfa=alfa,
        concreto=concreto
    )

    Nr, Mrx, Mry = esforcos_resistentes(
        secao=secao,
        estado=estado,
        concreto=concreto,
        aco=aco,
        area_total=As
    )

    return np.array([
        (Nr - Nsd) / escala_N,
        (Mrx - Msdx) / escala_M,
        (Mry - Msdy) / escala_M
    ])


def resolver_equilibrio(
    secao, concreto, aco, Nsd, Msdx, Msdy, x0, alfa0, As0,
    taxa_max=0.08, fator_x_max=5.0, multiplas_tentativas=True,
    tolerancia_equilibrio=1e-6
):
    """Dimensiona a armadura buscando o equilíbrio por mínimos quadrados.

    Args:
        secao: Seção com área positiva e barras definidas por proporções
            positivas que somam 1, sem áreas fixas.
        concreto: Modelo constitutivo do concreto.
        aco: Modelo constitutivo do aço.
        Nsd (float): Força normal solicitante, em N.
        Msdx (float): Momento solicitante em x, em N·mm.
        Msdy (float): Momento solicitante em y, em N·mm.
        x0 (float): Estimativa inicial da linha neutra, em mm.
        alfa0 (float): Estimativa inicial do ângulo, em radianos.
        As0 (float): Estimativa inicial da área de aço, em mm².
        taxa_max (float): Limite numérico ``As <= taxa_max*secao.area``;
            padrão 0.08. Não constitui verificação normativa.
        fator_x_max (float): Limite numérico ``x <= fator_x_max*h``;
            padrão 5.0, com ``h = secao.altura(0.0)``.
        multiplas_tentativas (bool): Se True, testa outras estimativas
            iniciais para reduzir a dependência da partida.
        tolerancia_equilibrio (float): Limite da norma euclidiana dos
            resíduos normalizados; padrão 1e-6.

    Returns:
        scipy.optimize.OptimizeResult: Melhor resultado segundo a norma
        dos resíduos, com atributos adicionais:

        - ``x``: vetor ``[x, alfa, As]`` otimizado.
        - ``norma_residuos``: norma euclidiana dos resíduos.
        - ``equilibrio_atendido``: indica se a norma satisfaz a tolerância.
        - ``otimizador_success``: sucesso da parada do SciPy.
        - ``success``: True somente se o SciPy teve sucesso e o
          equilíbrio atende à tolerância.
        - ``tentativas``: quantidade de estimativas efetivamente avaliadas.

    Raises:
        ValueError: Se a área da seção ou os limites forem inválidos,
            não houver barras, existirem áreas fixas ou as proporções
            das barras não forem positivas e somarem 1.

    Notes:
        Os limites de ``x``, ``alfa`` e ``As`` são impostos ao otimizador.
        Os ângulos iniciais são reduzidos ao intervalo de -pi a pi.
        As escalas usadas nos resíduos são ``max(abs(Nsd), 1e5)`` e
        ``max(abs(Msdx), abs(Msdy), 1e7)``. O menor resíduo pode ainda
        representar um estado sem equilíbrio; confira ``success`` e
        ``equilibrio_atendido`` antes de utilizar a solução.
    """
    if secao.area <= 0 or taxa_max <= 0 or fator_x_max <= 0:
        raise ValueError("Área da seção e limites devem ser positivos.")
    if not secao.barras:
        raise ValueError("É necessário informar barras de armadura.")
    if any(barra.area is not None for barra in secao.barras):
        raise ValueError(
            "Para dimensionar As, utilize proporcao em todas as barras, "
            "não area fixa."
        )
    if any(barra.proporcao is None or barra.proporcao <= 0
           for barra in secao.barras):
        raise ValueError("Cada barra deve ter proporcao positiva.")
    if not np.isclose(sum(barra.proporcao for barra in secao.barras), 1.0):
        raise ValueError("As proporções das barras devem somar 1.")

    h = secao.altura(0.0)
    x_max = fator_x_max * h
    As_max = taxa_max * secao.area
    if x_max <= 1e-6 or As_max <= 0:
        raise ValueError("Limites inválidos para x ou As.")

    limites_inf = np.array([1e-6, -pi, 0.0])
    limites_sup = np.array([x_max, pi, As_max])
    escala_N = max(abs(Nsd), 1e5)
    escala_M = max(abs(Msdx), abs(Msdy), 1e7)
    argumentos = (secao, concreto, aco, Nsd, Msdx, Msdy,
                  escala_N, escala_M)

    def preparar(x, alfa, As):
        # Ângulos equivalentes diferem por 2*pi.
        alfa = (alfa + pi) % (2 * pi) - pi
        valores = np.array([x, alfa, As], dtype=float)
        return np.clip(valores, limites_inf + [1e-9, 1e-9, 0],
                       limites_sup - [1e-9, 1e-9, 0])

    iniciais = [preparar(x0, alfa0, As0)]
    if multiplas_tentativas:
        for angulo in (0.0, pi / 4, -pi / 4, pi / 2, -pi / 2):
            iniciais.append(preparar(0.5 * h, angulo, 0.02 * secao.area))
        iniciais.append(preparar(1.5 * h, alfa0, 0.04 * secao.area))

    resultados = []
    for inicial in iniciais:
        resultado = least_squares(
            residuos_equilibrio, inicial, args=argumentos,
            bounds=(limites_inf, limites_sup),
            x_scale=[h, 1.0, max(As_max, 1.0)],
            max_nfev=1500, ftol=1e-11, xtol=1e-11, gtol=1e-11
        )
        resultados.append(resultado)
        if resultado.success and np.linalg.norm(resultado.fun) <= tolerancia_equilibrio:
            break

    melhor = min(resultados, key=lambda r: np.linalg.norm(r.fun))
    melhor.otimizador_success = bool(melhor.success)
    melhor.norma_residuos = float(np.linalg.norm(melhor.fun))
    melhor.equilibrio_atendido = melhor.norma_residuos <= tolerancia_equilibrio
    melhor.success = bool(melhor.otimizador_success and melhor.equilibrio_atendido)
    melhor.tentativas = len(resultados)
    if not melhor.equilibrio_atendido:
        melhor.message = (
            f"Equilíbrio não atendido (norma dos resíduos = "
            f"{melhor.norma_residuos:.3e}). " + str(melhor.message)
        )
    return melhor


if __name__ == "__main__":
    from unittest.mock import patch
    from types import SimpleNamespace

    print("\nTESTES: equilibrio")

    # Teste isolado: substituímos o modelo estrutural por um sistema
    # linear de solução conhecida: (x, alfa, As) = (2, 0.3, 4).
    def esforcos_ficticios(secao, estado, concreto, aco, area_total):
        return (100000 * estado.x,
                1e7 * estado.alfa,
                1e7 * area_total)

    class EstadoFicticio:
        def __init__(self, secao, x, alfa, concreto=None):
            self.x, self.alfa = x, alfa
            self.concreto = concreto

    barras = [SimpleNamespace(area=None, proporcao=0.5),
              SimpleNamespace(area=None, proporcao=0.5)]
    secao = SimpleNamespace(area=100, barras=barras,
                            altura=lambda alfa: 10)
    concreto = aco = SimpleNamespace()
    parametros = (secao, concreto, aco, 200000, 3e6, 4e7, 100000, 4e7)

    with patch(__name__ + ".EstadoDeformacao", EstadoFicticio), \
         patch(__name__ + ".esforcos_resistentes", esforcos_ficticios):
        residuo = residuos_equilibrio([2, 0.3, 4], *parametros)
        assert np.allclose(residuo, [0, 0, 0], atol=1e-12)
        print("Resíduos nulos na solução conhecida: OK")

        # O estado deve receber o mesmo concreto usado no equilíbrio.
        with patch(__name__ + ".EstadoDeformacao", wraps=EstadoFicticio) as construtor:
            residuos_equilibrio([2, 0.3, 4], *parametros)
            assert construtor.call_args.kwargs["concreto"] is concreto
        print("Propagação do material concreto: OK")

        residuo = residuos_equilibrio([3, 0.4, 5], *parametros)
        assert np.allclose(residuo, [1, .025, .25], atol=1e-12)
        print("Sinais e normalização dos resíduos: OK")

        penalidade = residuos_equilibrio([-1, 0, 4], *parametros)
        assert np.array_equal(penalidade, [1e6, 1e6, 1e6])
        penalidade = residuos_equilibrio([2, 0, -1], *parametros)
        assert np.array_equal(penalidade, [1e6, 1e6, 1e6])
        print("Penalização de valores inadmissíveis: OK")

        resultado = resolver_equilibrio(
            secao, concreto, aco,
            Nsd=200000, Msdx=3e6, Msdy=4e7,
            x0=1.5, alfa0=0.2, As0=3
        )
        assert resultado.success, resultado.message
        assert np.allclose(resultado.x, [2, .3, 4], rtol=1e-8, atol=1e-8)
        assert np.linalg.norm(resultado.fun) < 1e-8
        print("Convergência do scipy.optimize.least_squares: OK")
        assert resultado.equilibrio_atendido
        assert resultado.tentativas >= 1

        # O algoritmo pode parar sem que o equilíbrio esteja atendido.
        inviavel = resolver_equilibrio(
            secao, concreto, aco, Nsd=200000, Msdx=3e6, Msdy=4e7,
            x0=1.5, alfa0=0.2, As0=3, taxa_max=0.02,
            multiplas_tentativas=False
        )
        assert not inviavel.success
        assert not inviavel.equilibrio_atendido
        print("Detecção de equilíbrio não atendido: OK")

        try:
            secao.barras[0].area = 2
            resolver_equilibrio(secao, concreto, aco, 200000, 3e6, 4e7,
                                1.5, 0.2, 3)
        except ValueError:
            print("Rejeição de área fixa na armadura: OK")
        else:
            raise AssertionError("Deveria rejeitar barras com área fixa")

    print("Todos os testes passaram!")
