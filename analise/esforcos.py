from analise.integracao import (
    separar_regioes,
    integrar_poligono,
)
from math import cos, sin


def esforcos_concreto(secao, estado, concreto):
    """
    Calcula os esforços resistentes do concreto.

    Retorna
    -------
    Nc : float
        Força normal (N).
    Mc_xi : float
        Momento em torno de xi (N.mm).
    Mc_eta : float
        Momento em torno de eta (N.mm).

    Observação
    ----------
    Esta versão utiliza o recorte poligonal simples,
    devendo ser aplicada inicialmente a contornos convexos.
    """

    sigma_cd = concreto.sigma_cd

    b = estado.b
    c = estado.c

    eps_c2 = 0.002

    D0 = sigma_cd * (
        2 * c / eps_c2
        + c**2 / eps_c2**2
    )

    D1 = sigma_cd * (
        2 * b / eps_c2
        + 2 * b * c / eps_c2**2
    )

    D2 = sigma_cd * b**2 / eps_c2**2

    Nc = 0.0
    Mc_xi = 0.0
    Mc_eta = 0.0

    # Contorno externo e furos, com orientações
    # previamente ajustadas na classe Secao.
    poligonos = [secao.contorno] + list(secao.furos)

    for poligono in poligonos:

        vertices = [
            secao.coordenadas_rotacionadas(
                ponto, estado.alfa
            )
            for ponto in poligono.vertices
        ]

        regiao_I, regiao_II = separar_regioes(
            vertices, estado
        )

        def GI(p, q):
            return integrar_poligono(
                regiao_I, p, q
            )

        def GII(p, q):
            return integrar_poligono(
                regiao_II, p, q
            )

        # Região I: tensão parabólica
        Nc += (
            D0 * GI(0, 0)
            + D1 * GI(0, 1)
            + D2 * GI(0, 2)
        )

        Mc_xi += (
            D0 * GI(0, 1)
            + D1 * GI(0, 2)
            + D2 * GI(0, 3)
        )

        Mc_eta -= (
            D0 * GI(1, 0)
            + D1 * GI(1, 1)
            + D2 * GI(1, 2)
        )

        # Região II: tensão constante
        Nc -= sigma_cd * GII(0, 0)

        Mc_xi -= sigma_cd * GII(0, 1)

        Mc_eta += sigma_cd * GII(1, 0)

    return Nc, Mc_xi, Mc_eta


def esforcos_aco(
    secao,
    estado,
    aco,
    area_total=None
):

    Ns = 0.0
    Ms_xi = 0.0
    Ms_eta = 0.0

    for barra in secao.barras:

        xi, eta = (
            secao.coordenadas_rotacionadas(
                barra.posicao,
                estado.alfa
            )
        )

        epsilon = estado.deformacao(eta)

        sigma = aco.tensao(epsilon)

        area = barra.obter_area(area_total)

        forca = sigma * area

        Ns += forca
        Ms_xi += forca * eta
        Ms_eta -= forca * xi

    return Ns, Ms_xi, Ms_eta

def esforcos_resistentes(
    secao,
    estado,
    concreto,
    aco,
    area_total=None
):
    """
    Calcula os esforços resistentes totais da seção.

    Parameters
    ----------
    secao : Secao
        Geometria da seção e disposição das barras.
    estado : EstadoDeformacao
        Estado de deformação definido por x e alfa.
    concreto : Concreto
        Modelo constitutivo do concreto.
    aco : Aco
        Modelo constitutivo do aço.
    area_total : float, optional
        Área total de armadura, necessária quando
        as barras utilizam proporções de área.

    Returns
    -------
    tuple[float, float, float]
        (Nr, Mrx, Mry), em N e N.mm.
    """

    # Contribuição do concreto
    Nc, Mc_xi, Mc_eta = esforcos_concreto(
        secao,
        estado,
        concreto
    )

    # Contribuição da armadura
    Ns, Ms_xi, Ms_eta = esforcos_aco(
        secao,
        estado,
        aco,
        area_total
    )

    # Esforços totais nos eixos rotacionados
    Nr = Nc + Ns
    Mr_xi = Mc_xi + Ms_xi
    Mr_eta = Mc_eta + Ms_eta

    # Transformação para os eixos originais
    alfa = estado.alfa

    Mrx = (
        Mr_xi * cos(alfa)
        - Mr_eta * sin(alfa)
    )

    Mry = (
        Mr_xi * sin(alfa)
        + Mr_eta * cos(alfa)
    )

    return Nr, Mrx, Mry

if __name__ == "__main__":
    from math import isclose, pi
    from types import SimpleNamespace

    def conferir(obtido, esperado, descricao):
        assert isclose(obtido, esperado, rel_tol=1e-9, abs_tol=1e-7), (
            f"{descricao}: esperado {esperado}, obtido {obtido}"
        )

    class PontoTeste:
        def __init__(self, x, y):
            self.x, self.y = x, y

    class SecaoTeste:
        def __init__(self, barras=(), furo=False):
            # Retângulo centrado na origem: largura 4, altura 2
            self.contorno = SimpleNamespace(vertices=[
                PontoTeste(-2, -1), PontoTeste(2, -1),
                PontoTeste(2, 1), PontoTeste(-2, 1)
            ])
            self.furos = []
            if furo:
                # Furo central: largura 2, altura 1; sentido horário
                self.furos.append(SimpleNamespace(vertices=[
                    PontoTeste(-1, -.5), PontoTeste(-1, .5),
                    PontoTeste(1, .5), PontoTeste(1, -.5)
                ]))
            self.barras = list(barras)

        def coordenadas_rotacionadas(self, ponto, alfa):
            return (
                ponto.x * cos(alfa) + ponto.y * sin(alfa),
                -ponto.x * sin(alfa) + ponto.y * cos(alfa)
            )

    class BarraTeste:
        def __init__(self, x, y, area=None, proporcao=None):
            self.posicao = PontoTeste(x, y)
            self.area, self.proporcao = area, proporcao

        def obter_area(self, area_total=None):
            if self.area is not None:
                return self.area
            if self.proporcao is not None and area_total is not None:
                return self.proporcao * area_total
            raise ValueError("Área da barra não definida")

    class ConcretoTeste:
        sigma_cd = 20.0

    class AcoTeste:
        def tensao(self, epsilon):
            return 200000 * epsilon

    print("\\nTESTES: esforcos")
    concreto, aco = ConcretoTeste(), AcoTeste()
    secao = SecaoTeste()

    # Compressão constante: sigma = -20 MPa em toda a seção
    uniforme = SimpleNamespace(b=0.0, c=-.003, alfa=0.0,
                               deformacao=lambda eta: -.003)
    Nc, Mx, My = esforcos_concreto(secao, uniforme, concreto)
    conferir(Nc, -160, "Força do concreto em compressão uniforme")
    conferir(Mx, 0, "Momento x simétrico")
    conferir(My, 0, "Momento y simétrico")
    print("Concreto em compressão uniforme: OK")

    # Ramo parabólico uniforme: eps=-0.001 => sigma=-0.75*sigma_cd
    parabolico = SimpleNamespace(b=0.0, c=-.001, alfa=0.0,
                                deformacao=lambda eta: -.001)
    Nc, Mx, My = esforcos_concreto(secao, parabolico, concreto)
    conferir(Nc, -120, "Força no ramo parabólico")
    conferir(Mx, 0, "Momento x parabólico")
    conferir(My, 0, "Momento y parabólico")
    print("Concreto no ramo parabólico: OK")

    vazada = SecaoTeste(furo=True)
    Nc, Mx, My = esforcos_concreto(vazada, uniforme, concreto)
    conferir(Nc, -120, "Força com furo")
    conferir(Mx, 0, "Momento x com furo")
    conferir(My, 0, "Momento y com furo")
    print("Subtração da contribuição dos furos: OK")

    barras = [BarraTeste(-1, -0.5, area=2),
              BarraTeste(1, 0.5, area=3)]
    secao_armada = SecaoTeste(barras=barras)
    # eps(eta) = 0.001*eta: tensões -100 e +100 MPa
    estado_aco = SimpleNamespace(b=.001, c=0.0, alfa=0.0,
                                deformacao=lambda eta: .001 * eta)
    Ns, Msx, Msy = esforcos_aco(secao_armada, estado_aco, aco)
    conferir(Ns, 100, "Normal do aço")
    conferir(Msx, 250, "Momento xi do aço")
    conferir(Msy, -500, "Momento eta do aço")
    print("Força e momentos do aço: OK")

    proporcionais = SecaoTeste(barras=[
        BarraTeste(-1, -.5, proporcao=.4),
        BarraTeste(1, .5, proporcao=.6)
    ])
    Ns2, Mx2, My2 = esforcos_aco(proporcionais, estado_aco, aco,
                                area_total=5)
    for obtido, esperado in zip((Ns2, Mx2, My2), (Ns, Msx, Msy)):
        conferir(obtido, esperado, "Áreas proporcionais")
    print("Áreas proporcionais: OK")

    # Verifica transformação de momentos a 90 graus.
    rotacionado = SimpleNamespace(b=0.0, c=-.003, alfa=pi/2,
                                  deformacao=lambda eta: -.003)
    nr, mrx, mry = esforcos_resistentes(
        SecaoTeste(barras=[BarraTeste(1, 0, area=2)]),
        rotacionado, concreto, aco
    )
    conferir(nr, -1360, "Força total rotacionada")
    conferir(mrx, 0, "Momento x global")
    conferir(mry, 1200, "Momento y global")
    print("Soma e transformação dos esforços: OK")
    # Teste independente: uma força concentrada em coordenadas globais.
    # Para F=-1200 N aplicada em (x,y)=(1,2) mm:
    # Mx=F*y=-2400 N.mm; My=-F*x=+1200 N.mm.
    for angulo in (0.0, pi / 6, pi / 2, -pi / 3):
        estado_forca = SimpleNamespace(
            b=0.0, c=-.003, alfa=angulo,
            deformacao=lambda eta: -.003
        )
        secao_forca = SecaoTeste(barras=[BarraTeste(1, 2, area=2)])
        # Descontamos a contribuicao do concreto por diferenca,
        # isolando o efeito da barra e sua transformacao de momentos.
        nr_total, mx_total, my_total = esforcos_resistentes(
            secao_forca, estado_forca, concreto, aco
        )
        nr_conc, mxi_conc, meta_conc = esforcos_concreto(
            secao_forca, estado_forca, concreto
        )
        mx_conc = mxi_conc * cos(angulo) - meta_conc * sin(angulo)
        my_conc = mxi_conc * sin(angulo) + meta_conc * cos(angulo)
        conferir(nr_total - nr_conc, -1200, "Forca isolada da barra")
        conferir(mx_total - mx_conc, -2400, "Momento x invariante")
        conferir(my_total - my_conc, 1200, "Momento y invariante")
    print("Invariancia dos momentos globais: OK")
    print("Todos os testes passaram!")
