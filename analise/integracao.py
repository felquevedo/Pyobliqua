from enum import Enum


class RegiaoConcreto(Enum):
    ZERO = 0
    PARABOLICA = 1
    CONSTANTE = 2
    
def identificar_regiao(epsilon: float) -> RegiaoConcreto:

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
    """
    Calcula a contribuição de um segmento orientado
    para a integral G_pq.

    Parameters
    ----------
    p, q : int
        Expoentes das coordenadas xi e eta.
    p1, p2 : tuple
        Pontos (xi, eta) inicial e final do segmento.

    Returns
    -------
    float
        Contribuição do segmento para G_pq.
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
    """
    Recorta um polígono por uma linha de deformação constante.

    Parameters
    ----------
    vertices : list[tuple]
        Vértices (xi, eta) do polígono.
    estado : EstadoDeformacao
        Estado de deformação da seção.
    limite : float
        Deformação que define a linha de corte.
    manter_menor : bool
        True: mantém epsilon <= limite.
        False: mantém epsilon >= limite.

    Returns
    -------
    list[tuple]
        Vértices do polígono recortado.
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
    """
    Separa o polígono nas regiões parabólica
    e de tensão constante do concreto.
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
    """Calcula G_pq sobre um polígono fechado."""

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
