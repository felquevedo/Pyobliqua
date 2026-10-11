"""Compatibilidade de deformações no estado limite último.

Determina os domínios de deformação e o campo linear de deformações
longitudinais de uma seção de concreto armado a partir da posição
da linha neutra e da orientação dos eixos locais.

Convenções:
    - Coordenadas e comprimentos: mm.
    - Ângulos: radianos.
    - Deformações: adimensionais (por exemplo, -0.0035 = -3,5‰).
    - Compressão negativa; tração positiva.
    - A profundidade ``x`` é medida desde a fibra superior.

A formulação e os limites são os adotados pelo projeto original.
"""

class EstadoDeformacao:
    """Representa o estado último de deformação de uma seção transversal.

    Attributes:
        secao: Seção transversal analisada.
        x (float): Profundidade da linha neutra, em mm.
        alfa (float): Ângulo dos eixos locais, em radianos.
        h (float): Altura total do concreto na direção eta, em mm.
        d (float): Altura útil na direção eta, em mm.
        eta_s (float): Coordenada da fibra superior do concreto, em mm.
        eta_i_aco (float): Menor coordenada eta das barras, em mm.
        epsilon_s (float): Deformação da fibra superior, adimensional.
        epsilon_i (float): Deformação inferior de referência, adimensional;
            seu significado depende do domínio de deformação.
        b (float): Gradiente do campo de deformações, em mm⁻¹.
        c (float): Termo constante do campo de deformações, adimensional.

    Notes:
        As deformações são adimensionais: 0.0035 corresponde a 3,5‰.
        Compressão é negativa e tração positiva. Para obter deformações
        inferiores sem ambiguidade, use ``epsilon_concreto_inferior``
        e ``epsilon_aco_inferior``.
    """

    def __init__(self, secao, x, alfa):

        """Inicializa o estado último de deformação da seção.

        Args:
            secao: Seção transversal com métodos geométricos de altura,
                altura útil e transformação de coordenadas.
            x (float): Profundidade da linha neutra medida a partir da
                fibra superior do concreto, em mm.
            alfa (float): Ângulo de rotação dos eixos locais, em radianos.

        Raises:
            ValueError: Se a seção não possuir barras, conforme a
                implementação de ``secao.altura_util``.

        Notes:
            Calcula as deformações extremas e os coeficientes ``b`` e ``c``
            do campo linear de deformações ``epsilon(eta) = b*eta + c``.
        """
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

        """Classifica o domínio de deformação pela posição da linha neutra.

        Returns:
            str: Identificador ``"1-2"``, ``"3-4"``, ``"4a"`` ou ``"5"``.

        Notes:
            Os limites são ``(0.0035/0.0135)*d``, ``d`` e ``h``.
            O rótulo ``"1-2"`` é usado também quando ``x <= 0``.
        """
        if self.x <= (0.0035 / 0.0135) * self.d:
            return "1-2"

        if self.x <= self.d:
            return "3-4"

        if self.x <= self.h:
            return "4a"

        return "5"

    def _deformacoes_extremas(self):

        """Determina as deformações de referência para o domínio atual.

        Returns:
            tuple[float, float]: ``(epsilon_s, epsilon_i)``, adimensionais.

        Notes:
            ``epsilon_s`` corresponde à fibra superior do concreto.
            Por convenção histórica, ``epsilon_i`` corresponde à barra
            inferior nos domínios 1-2 e 3-4, mas à fibra inferior do
            concreto nos domínios 4a e 5. Prefira as propriedades explícitas
            ``epsilon_aco_inferior`` e ``epsilon_concreto_inferior``.
            Compressão é negativa e tração é positiva.
        """
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

        """Calcula os coeficientes do campo linear de deformações.

        Returns:
            tuple[float, float]: Coeficientes ``(b, c)``, em mm⁻¹ e
            adimensional, respectivamente.

        Notes:
            A linha neutra tem coordenada ``eta_s - x``. Para ``x``
            aproximadamente nulo, utiliza-se ``b = -0.010/d`` para evitar
            divisão por zero, preservando a implementação original.
        """
        if abs(self.x) < 1e-12:
            b = -0.010 / self.d
        else:
            b = self.epsilon_s / self.x 

        eta_ln = self.eta_s - self.x    

        c = -b * eta_ln 

        return b, c

    def deformacao(self, eta):
        """Calcula a deformação longitudinal em uma coordenada local.

        Args:
            eta (float): Coordenada no eixo local eta, em mm.

        Returns:
            float: Deformação longitudinal adimensional, com compressão
            negativa e tração positiva.
        """
        return self.b * eta + self.c

    @property
    def epsilon_concreto_inferior(self):
        """Obtém a deformação na fibra inferior do concreto.

        Returns:
            float: Deformação longitudinal adimensional; compressão negativa.
        """
        return self.deformacao(self.eta_s - self.h)

    @property
    def epsilon_aco_inferior(self):
        """Obtém a deformação na barra com menor coordenada eta.

        Returns:
            float: Deformação longitudinal adimensional, positiva em tração.
        """
        return self.deformacao(self.eta_i_aco)

    def deformacao_barra(self, barra):

        """Calcula a deformação longitudinal de uma barra de armadura.

        Args:
            barra: Objeto de armadura cuja posição é dada por ``barra.posicao``.

        Returns:
            float: Deformação longitudinal adimensional na posição da barra.
        """
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
