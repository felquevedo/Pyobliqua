"""Integração geométrica de regiões do concreto em eixos rotacionados.

O módulo classifica regiões do diagrama parábola-retângulo do concreto,
subdivide segmentos nos limites de deformação, recorta polígonos e calcula
integrais monomiais por meio do teorema de Green.

Convenções:
    - Coordenadas ``xi`` e ``eta`` em mm.
    - Deformações ``epsilon`` adimensionais; compressão negativa.
    - Transições do concreto em epsilon = 0 e epsilon = -0.002.
    - Integrais orientadas: inverter os vértices inverte o sinal.
    - A integral de xi**p * eta**q tem unidade mm**(p + q + 2).

As funções geométricas não calculam diretamente as tensões do concreto.
"""

from enum import Enum


class RegiaoConcreto(Enum):
    """Identifica o trecho do diagrama constitutivo do concreto.

    Attributes:
        ZERO: Região sem tensão de concreto (epsilon >= 0).
        PARABOLICA: Região comprimida com -0.002 <= epsilon < 0.
        CONSTANTE: Região comprimida com epsilon < -0.002.
    """
    ZERO = 0
    PARABOLICA = 1
    CONSTANTE = 2
    
def identificar_regiao(epsilon: float) -> RegiaoConcreto:

    """Classifica uma deformação no diagrama do concreto.

    Args:
        epsilon (float): Deformação específica adimensional.

    Returns:
        RegiaoConcreto: Região correspondente à deformação.

    Notes:
        Não verifica o limite último de compressão de -0.0035;
        apenas identifica o trecho constitutivo.
    """
    if epsilon >= 0.0:
        return RegiaoConcreto.ZERO

    if epsilon >= -0.002:
        return RegiaoConcreto.PARABOLICA

    return RegiaoConcreto.CONSTANTE

def interpolar_ponto(
    p1,
    p2,
    epsilon1,
    epsilon2,
    epsilon_limite
):

    """Interpola um ponto interno do segmento em uma deformação dada.

    Args:
        p1 (tuple[float, float]): Ponto inicial (xi, eta), em mm.
        p2 (tuple[float, float]): Ponto final (xi, eta), em mm.
        epsilon1 (float): Deformação em p1.
        epsilon2 (float): Deformação em p2.
        epsilon_limite (float): Deformação da linha de interseção.

    Returns:
        tuple[float, float] | None: Ponto interno interpolado, em mm,
        ou None quando as deformações são iguais ou a interseção
        não está estritamente no interior do segmento.
    """
    if epsilon1 == epsilon2:
        return None

    t = (
        (epsilon_limite - epsilon1)
        /
        (epsilon2 - epsilon1)
    )

    if not 0.0 < t < 1.0:
        return None

    xi = p1[0] + t * (p2[0] - p1[0])
    eta = p1[1] + t * (p2[1] - p1[1])

    return xi, eta

def subdividir_segmento(
    p1,
    p2,
    estado
):

    """Divide um segmento nos limites do diagrama do concreto.

    Args:
        p1 (tuple[float, float]): Ponto inicial (xi, eta), em mm.
        p2 (tuple[float, float]): Ponto final (xi, eta), em mm.
        estado: Estado de deformação com método ``deformacao(eta)``.

    Returns:
        list[tuple]: Segmentos (ponto_inicial, ponto_final, regiao),
        ordenados ao longo do segmento original.

    Notes:
        Os cortes ocorrem em epsilon = 0 e epsilon = -0.002.
        A região é determinada pela deformação no ponto médio.
    """
    epsilon1 = estado.deformacao(p1[1])
    epsilon2 = estado.deformacao(p2[1])

    pontos = [
        (0.0, p1),
        (1.0, p2)
    ]

    limites = [
        0.0,
        -0.002
    ]

    for epsilon_limite in limites:

        if epsilon1 == epsilon2:
            continue

        t = (
            (epsilon_limite - epsilon1)
            /
            (epsilon2 - epsilon1)
        )

        if 0.0 < t < 1.0:

            xi = (
                p1[0]
                + t * (p2[0] - p1[0])
            )

            eta = (
                p1[1]
                + t * (p2[1] - p1[1])
            )

            pontos.append(
                (t, (xi, eta))
            )

    pontos.sort(key=lambda item: item[0])

    segmentos = []

    for i in range(len(pontos) - 1):

        pa = pontos[i][1]
        pb = pontos[i + 1][1]

        eta_medio = (
            pa[1] + pb[1]
        ) / 2.0

        epsilon_medio = (
            estado.deformacao(eta_medio)
        )

        regiao = identificar_regiao(
            epsilon_medio
        )

        segmentos.append(
            (pa, pb, regiao)
        )

    return segmentos

def segmentos_rotacionados(
    secao,
    poligono,
    estado
):

    """Converte e subdivide os lados de um polígono da seção.

    Args:
        secao: Seção com método ``coordenadas_rotacionadas``.
        poligono: Polígono cujos vértices são objetos Ponto.
        estado: Estado de deformação contendo ``alfa`` e ``deformacao``.

    Returns:
        list[tuple]: Segmentos em (xi, eta) classificados por região,
        respeitando a ordem dos lados do polígono.
    """
    vertices = poligono.vertices

    segmentos = []

    for i in range(len(vertices)):

        p1 = vertices[i]
        p2 = vertices[(i + 1) % len(vertices)]

        xi1, eta1 = (
            secao.coordenadas_rotacionadas(
                p1,
                estado.alfa
            )
        )

        xi2, eta2 = (
            secao.coordenadas_rotacionadas(
                p2,
                estado.alfa
            )
        )

        novos_segmentos = subdividir_segmento(
            (xi1, eta1),
            (xi2, eta2),
            estado
        )

        segmentos.extend(novos_segmentos)

    return segmentos

from math import comb


def G(p: int, q: int, p1: tuple, p2: tuple) -> float:
    """Calcula a contribuição orientada de um segmento à integral monomial.

    Usa o teorema de Green para integrar xi**p * eta**q sobre a área
    delimitada por um contorno fechado.

    Args:
        p (int): Expoente não negativo de xi.
        q (int): Expoente não negativo de eta.
        p1 (tuple[float, float]): Ponto inicial (xi, eta), em mm.
        p2 (tuple[float, float]): Ponto final (xi, eta), em mm.

    Returns:
        float: Contribuição orientada, em mm**(p + q + 2).

    Raises:
        ValueError: Se p ou q forem negativos.

    Notes:
        A expressão corresponde à integral de linha
        (xi**(p+1) * eta**q / (p+1)) d(eta).
        O resultado sobre um polígono é a soma das contribuições
        dos segmentos de seu contorno.
    """

    if p < 0 or q < 0:
        raise ValueError("p e q devem ser não negativos.")

    xi1, eta1 = p1
    xi2, eta2 = p2

    dxi = xi2 - xi1
    deta = eta2 - eta1

    soma = 0.0

    for i in range(p + 2):
        for j in range(q + 1):

            termo = (
                comb(p + 1, i)
                * comb(q, j)
                * xi1 ** (p + 1 - i)
                * dxi ** i
                * eta1 ** (q - j)
                * deta ** j
                / (i + j + 1)
            )

            soma += termo

    return deta * soma / (p + 1)

#**************************************

def recortar_poligono(vertices, estado, limite, manter_menor=True):
    """Recorta um polígono por uma linha de deformação constante.

    Args:
        vertices (list[tuple[float, float]]): Vértices (xi, eta), em mm.
        estado: Estado de deformação com método ``deformacao(eta)``.
        limite (float): Deformação que define a linha de corte.
        manter_menor (bool): Se True, conserva epsilon <= limite;
            caso contrário, conserva epsilon >= limite.

    Returns:
        list[tuple[float, float]]: Vértices do polígono recortado,
        preservando a orientação do contorno.

    Notes:
        Usa uma tolerância de 1e-12 na classificação dos vértices.
        Pressupõe um campo de deformações linear e um contorno
        adequado ao recorte por semiplano.
    """

    if not vertices:
        return []

    def dentro(ponto):
        epsilon = estado.deformacao(ponto[1])

        if manter_menor:
            return epsilon <= limite + 1e-12

        return epsilon >= limite - 1e-12

    def intersecao(p1, p2):
        e1 = estado.deformacao(p1[1])
        e2 = estado.deformacao(p2[1])

        t = (limite - e1) / (e2 - e1)

        xi = p1[0] + t * (p2[0] - p1[0])
        eta = p1[1] + t * (p2[1] - p1[1])

        return (xi, eta)

    resultado = []

    anterior = vertices[-1]

    for atual in vertices:

        anterior_dentro = dentro(anterior)
        atual_dentro = dentro(atual)

        if anterior_dentro and atual_dentro:
            resultado.append(atual)

        elif anterior_dentro and not atual_dentro:
            resultado.append(intersecao(anterior, atual))

        elif not anterior_dentro and atual_dentro:
            resultado.append(intersecao(anterior, atual))
            resultado.append(atual)

        anterior = atual

    return resultado

def separar_regioes(vertices, estado):
    """Separa o polígono nas regiões comprimidas do concreto.

    Args:
        vertices (list[tuple[float, float]]): Vértices (xi, eta), em mm.
        estado: Estado de deformação com método ``deformacao(eta)``.

    Returns:
        tuple[list[tuple], list[tuple]]: Polígonos das regiões
        parabólica (-0.002 <= epsilon <= 0) e constante
        (epsilon <= -0.002), respectivamente.

    Notes:
        Primeiro elimina a região tracionada (epsilon > 0).
        As fronteiras podem pertencer a ambas as regiões, sem
        produzir sobreposição de área.
    """

    # Região comprimida
    comprimida = recortar_poligono(
        vertices,
        estado,
        limite=0.0,
        manter_menor=True
    )

    # Região I: -0.002 <= epsilon <= 0
    regiao_I = recortar_poligono(
        comprimida,
        estado,
        limite=-0.002,
        manter_menor=False
    )

    # Região II: epsilon <= -0.002
    regiao_II = recortar_poligono(
        comprimida,
        estado,
        limite=-0.002,
        manter_menor=True
    )

    return regiao_I, regiao_II

def integrar_poligono(vertices, p, q):
    """Integra o monômio xi**p * eta**q sobre um polígono fechado.

    Args:
        vertices (list[tuple[float, float]]): Vértices (xi, eta), em mm.
        p (int): Expoente não negativo de xi.
        q (int): Expoente não negativo de eta.

    Returns:
        float: Integral orientada, em mm**(p + q + 2).
        Retorna 0.0 para menos de três vértices.

    Raises:
        ValueError: Se p ou q forem negativos em um polígono
            com pelo menos três vértices.
    """

    if len(vertices) < 3:
        return 0.0

    resultado = 0.0

    for i in range(len(vertices)):

        p1 = vertices[i]
        p2 = vertices[(i + 1) % len(vertices)]

        resultado += G(p, q, p1, p2)

    return resultado

if __name__ == "__main__":
    from math import isclose

    def conferir(valor, esperado, nome):
        assert isclose(valor, esperado, rel_tol=1e-9, abs_tol=1e-9), (
            f"{nome}: esperado {esperado}, obtido {valor}"
        )

    class EstadoTeste:
        alfa = 0.0

        def deformacao(self, eta):
            return -0.001 * eta

    estado = EstadoTeste()
    print("\nTESTES: integracao")

    assert identificar_regiao(0.001) == RegiaoConcreto.ZERO
    assert identificar_regiao(-0.001) == RegiaoConcreto.PARABOLICA
    assert identificar_regiao(-0.003) == RegiaoConcreto.CONSTANTE
    print("Classificação das regiões: OK")

    p = interpolar_ponto((0, -1), (4, 3), 0.001, -0.003, -0.002)
    conferir(p[0], 3, "Interpolação xi")
    conferir(p[1], 2, "Interpolação eta")
    assert interpolar_ponto((0, 0), (1, 1), 0, 0, 0) is None
    print("Interpolação: OK")

    segmentos = subdividir_segmento((0, -1), (4, 3), estado)
    assert len(segmentos) == 3
    assert [s[2] for s in segmentos] == [
        RegiaoConcreto.ZERO,
        RegiaoConcreto.PARABOLICA,
        RegiaoConcreto.CONSTANTE,
    ]
    conferir(segmentos[0][1][1], 0, "Limite epsilon=0")
    conferir(segmentos[1][1][1], 2, "Limite epsilon=-0.002")
    print("Subdivisão de segmentos: OK")

    retangulo = [(0, -1), (2, -1), (2, 3), (0, 3)]
    conferir(integrar_poligono(retangulo, 0, 0), 8, "Área")
    conferir(integrar_poligono(retangulo, 1, 0), 8, "Integral xi")
    conferir(integrar_poligono(retangulo, 0, 1), 8, "Integral eta")
    conferir(integrar_poligono(retangulo, 2, 0), 32 / 3, "Integral xi²")
    conferir(integrar_poligono(retangulo, 0, 2), 56 / 3, "Integral eta²")
    conferir(integrar_poligono(retangulo, 1, 1), 8, "Integral xi*eta")
    conferir(integrar_poligono(list(reversed(retangulo)), 0, 0), -8,
             "Orientação invertida")
    print("Integrais de Green e orientação: OK")

    comprimida = recortar_poligono(retangulo, estado, 0)
    conferir(integrar_poligono(comprimida, 0, 0), 6, "Área comprimida")
    regiao_I, regiao_II = separar_regioes(retangulo, estado)
    conferir(integrar_poligono(regiao_I, 0, 0), 4, "Área parabólica")
    conferir(integrar_poligono(regiao_II, 0, 0), 2, "Área constante")
    conferir(integrar_poligono(regiao_I, 0, 1), 4, "Primeiro momento I")
    conferir(integrar_poligono(regiao_II, 0, 1), 5, "Primeiro momento II")
    print("Recorte e separação das regiões: OK")

    assert recortar_poligono([], estado, 0) == []
    assert integrar_poligono([], 0, 0) == 0
    try:
        G(-1, 0, (0, 0), (1, 1))
    except ValueError:
        pass
    else:
        raise AssertionError("Expoente negativo deveria gerar ValueError")
    print("Casos-limite: OK")
    print("Todos os testes passaram!")
