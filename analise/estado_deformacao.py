class EstadoDeformacao:
    """Estado de deformação último da seção.

    epsilon_i mantém significado histórico dependente do domínio.
    Prefira epsilon_concreto_inferior e epsilon_aco_inferior.
    """

    def __init__(self, secao, x, alfa):

        self.secao = secao
        self.x = float(x)
        self.alfa = float(alfa)

        self.h = secao.altura(alfa)
        self.d = secao.altura_util(alfa)

        _, self.eta_s = (
            secao.limites_eta_concreto(alfa)
        )

        self.eta_i_aco, _ = (
            secao.limites_eta_armadura(alfa)
        )

        self.epsilon_s, self.epsilon_i = (
            self._deformacoes_extremas()
        )

        self.b, self.c = self._calcular_bc()

    @property
    def dominio(self):

        if self.x <= (0.0035 / 0.0135) * self.d:
            return "1-2"

        if self.x <= self.d:
            return "3-4"

        if self.x <= self.h:
            return "4a"

        return "5"

    def _deformacoes_extremas(self):

        x = self.x
        d = self.d
        h = self.h

        if self.dominio == "1-2":

            epsilon_s = (
                -0.010 * x / (d - x)
            )

            epsilon_i = 0.010

        elif self.dominio == "3-4":

            epsilon_s = -0.0035

            epsilon_i = (
                0.0035 * (d - x) / x
            )

        elif self.dominio == "4a":

            epsilon_s = -0.0035
            epsilon_i = -0.0035 * (x - h) / x

        else:

            denominador = (
                x - (3.0 / 7.0) * h
            )

            epsilon_s = (
                -0.002 * x / denominador
            )

            epsilon_i = (
                -0.002
                * (x - h)
                / denominador
            )

        return epsilon_s, epsilon_i

    def _calcular_bc(self): 

        if abs(self.x) < 1e-12:
            b = -0.010 / self.d
        else:
            b = self.epsilon_s / self.x 

        eta_ln = self.eta_s - self.x    

        c = -b * eta_ln 

        return b, c

    def deformacao(self, eta):
        return self.b * eta + self.c

    @property
    def epsilon_concreto_inferior(self):
        """Deformação na borda inferior do concreto (sinal: compressão negativa)."""
        return self.deformacao(self.eta_s - self.h)

    @property
    def epsilon_aco_inferior(self):
        """Deformação da barra com menor coordenada eta."""
        return self.deformacao(self.eta_i_aco)

    def deformacao_barra(self, barra):

        _, eta = (
            self.secao.coordenadas_rotacionadas(
                barra.posicao,
                self.alfa
            )
        )

        return self.deformacao(eta)

if __name__ == "__main__":
    from math import isclose, pi
    from secao.secao import Secao

    def conferir(obtido, esperado, nome):
        assert isclose(obtido, esperado, rel_tol=1e-9, abs_tol=1e-12), (
            f"{nome}: esperado {esperado}, obtido {obtido}"
        )

    secao = Secao(
        [(0, 0), (200, 0), (200, 600), (0, 600)],
        barras=[(30, 50, 100), (170, 50, 100),
                (30, 550, 100), (170, 550, 100)],
    )
    print("\nTESTES: EstadoDeformacao")
    estado = EstadoDeformacao(secao, 100, 0)
    conferir(estado.h, 600, "altura")
    conferir(estado.d, 550, "altura util")
    conferir(estado.eta_s, 300, "eta superior")
    conferir(estado.eta_i_aco, -250, "eta da armadura inferior")
    print("Geometria de referência: OK")

    casos = [
        (0, "1-2"),
        (100, "1-2"),
        (200, "3-4"),
        (550, "3-4"),
        (575, "4a"),
        (600, "4a"),
        (700, "5"),
        (2000, "5"),
    ]
    for x, dominio in casos:
        estado = EstadoDeformacao(secao, x, 0)
        assert estado.dominio == dominio, (x, estado.dominio, dominio)
        conferir(estado.deformacao(estado.eta_s - x), 0,
                 f"linha neutra x={x}")
        conferir(estado.deformacao(estado.eta_s), estado.epsilon_s,
                 f"borda superior x={x}")
        if dominio in ("1-2", "3-4"):
            conferir(estado.deformacao(estado.eta_i_aco), estado.epsilon_i,
                     f"armadura inferior x={x}")
        else:
            conferir(estado.deformacao(estado.eta_s - estado.h),
                     estado.epsilon_i, f"borda inferior x={x}")
    print("Dominios, linha neutra e deformacoes extremas: OK")

    estado = EstadoDeformacao(secao, 575, 0)
    conferir(estado.epsilon_i, -0.0035 * (575 - 600) / 575,
             "dominio 4a: deformacao inferior")
    print("Dominio 4a: OK")

    estado = EstadoDeformacao(secao, 200, 0)
    valores = []
    for barra in secao.barras:
        _, eta = secao.coordenadas_rotacionadas(barra.posicao, 0)
        conferir(estado.deformacao_barra(barra), estado.b * eta + estado.c,
                 "deformacao da barra")
        valores.append(estado.deformacao_barra(barra))
    assert valores[0] == valores[1] and valores[2] == valores[3]
    assert valores[0] != valores[2]
    print("Deformacoes nas barras: OK")

    estado = EstadoDeformacao(secao, 200, pi / 2)
    for barra in secao.barras:
        _, eta = secao.coordenadas_rotacionadas(barra.posicao, pi / 2)
        conferir(estado.deformacao_barra(barra), estado.deformacao(eta),
                 "deformacao da barra com rotacao")
    print("Deformacoes com eixos rotacionados: OK")
    # Transições entre os domínios: sem salto no campo de deformações.
    for limite in ((0.0035 / 0.0135) * secao.altura_util(0),
                   secao.altura_util(0), secao.altura(0)):
        antes = EstadoDeformacao(secao, limite - 1e-6, 0)
        depois = EstadoDeformacao(secao, limite + 1e-6, 0)
        assert isclose(antes.epsilon_s, depois.epsilon_s, abs_tol=1e-7), limite
        assert isclose(antes.epsilon_aco_inferior,
                       depois.epsilon_aco_inferior, abs_tol=1e-7), limite
    estado = EstadoDeformacao(secao, 575, 0)
    conferir(estado.epsilon_concreto_inferior,
             estado.deformacao(estado.eta_s - estado.h), "borda inferior")
    conferir(estado.epsilon_aco_inferior,
             estado.deformacao(estado.eta_i_aco), "aço inferior")
    print("Propriedades e continuidade entre domínios: OK")
    print("Todos os testes passaram!")
