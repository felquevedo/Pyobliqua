"""Representação de pontos e transformações de coordenadas no plano.

Este módulo fornece a classe :class:`Ponto`, utilizada para armazenar
coordenadas cartesianas e realizar translações e rotações de eixos.

Convenções:
    - As coordenadas e os deslocamentos devem usar a mesma unidade de
      comprimento (mm no projeto Pyobliqua).
    - Os ângulos são informados em radianos.
    - A rotação implementada é uma transformação *passiva* de coordenadas:
      os eixos locais giram de ``alfa`` no sentido anti-horário em relação
      aos globais, enquanto o ponto físico permanece na mesma posição.
"""

from math import cos, sin


class Ponto:
    """Representa um ponto bidimensional em coordenadas cartesianas.

    Attributes:
        x (float): Coordenada horizontal do ponto.
        y (float): Coordenada vertical do ponto.

    Note:
        A classe não impõe uma unidade; no Pyobliqua, utiliza-se mm.
    """

    def __init__(self, x: float, y: float):
        """Inicializa o ponto a partir de suas coordenadas.

        Args:
            x (float): Coordenada horizontal.
            y (float): Coordenada vertical.
        """
        self.x = float(x)
        self.y = float(y)

    def transladar(self, dx: float, dy: float) -> "Ponto":
        """Obtém um novo ponto após uma translação no plano.

        Args:
            dx (float): Deslocamento na direção x.
            dy (float): Deslocamento na direção y.

        Returns:
            Ponto: Novo ponto com coordenadas ``(x + dx, y + dy)``.

        Note:
            O ponto original não é modificado.
        """
        return Ponto(self.x + dx, self.y + dy)

    def rotacionar(self, alfa: float) -> "Ponto":
        """Expressa o ponto em um sistema de eixos girado de ``alfa``.

        A transformação de coordenadas é dada por:

        ``xi = x*cos(alfa) + y*sin(alfa)``
        ``eta = -x*sin(alfa) + y*cos(alfa)``

        Args:
            alfa (float): Ângulo dos eixos locais em relação aos globais,
                em radianos, positivo no sentido anti-horário.

        Returns:
            Ponto: Novo ponto cujos atributos ``x`` e ``y`` armazenam,
            respectivamente, as coordenadas locais ``xi`` e ``eta``.

        Note:
            Trata-se de uma rotação dos eixos (passiva), não de uma
            rotação física do ponto em torno da origem.
        """
        xi = self.x * cos(alfa) + self.y * sin(alfa)
        eta = -self.x * sin(alfa) + self.y * cos(alfa)
        return Ponto(xi, eta)

    def __repr__(self) -> str:
        """Retorna uma representação textual resumida do ponto.

        Returns:
            str: Texto com as coordenadas arredondadas a três casas
            decimais, no formato ``Ponto(x=..., y=...)``.
        """
        return f"Ponto(x={self.x:.3f}, y={self.y:.3f})"


if __name__ == "__main__":
    from math import isclose, pi

    print("\nTESTE: Ponto")
    ponto = Ponto(3.0, 4.0)
    assert isclose(ponto.x, 3.0)
    assert isclose(ponto.y, 4.0)
    print("Coordenadas: OK")

    # A translação deve criar um novo objeto sem modificar o original.
    transladado = ponto.transladar(2.0, -1.0)
    assert isclose(transladado.x, 5.0)
    assert isclose(transladado.y, 3.0)
    assert isclose(ponto.x, 3.0) and isclose(ponto.y, 4.0)
    print("Translação: OK")

    # Eixos locais girados 90°: xi = y e eta = -x.
    rotacionado = ponto.rotacionar(pi / 2)
    assert isclose(rotacionado.x, 4.0, abs_tol=1e-12)
    assert isclose(rotacionado.y, -3.0, abs_tol=1e-12)
    print("Rotação: OK")

    print("Testes concluídos!")
