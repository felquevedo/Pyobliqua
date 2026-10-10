from math import cos, sin


class Ponto:
    """Representa um ponto no plano cartesiano."""

    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)

    def transladar(self, dx: float, dy: float):
        """Retorna um novo ponto transladado."""
        return Ponto(
            self.x + dx,
            self.y + dy
        )

    def rotacionar(self, alfa: float):
        """
        Retorna as coordenadas ξ, η do ponto.

        Parameters
        ----------
        alfa : float
            Ângulo de rotação em radianos.
        """
        xi = (
            self.x * cos(alfa)
            + self.y * sin(alfa)
        )

        eta = (
            -self.x * sin(alfa)
            + self.y * cos(alfa)
        )

        return Ponto(xi, eta)

    def __repr__(self):
        return f"Ponto(x={self.x:.3f}, y={self.y:.3f})"
    
    
if __name__ == "__main__":
    from math import isclose, pi

    def verificar_ponto(obtido, x, y):
        assert isclose(obtido.x, x, rel_tol=1e-12, abs_tol=1e-12), (
            f"Coordenada x: esperado {x}, obtido {obtido.x}"
        )
        assert isclose(obtido.y, y, rel_tol=1e-12, abs_tol=1e-12), (
            f"Coordenada y: esperado {y}, obtido {obtido.y}"
        )

    print("\nTESTES: Ponto")

    ponto = Ponto(3, 4)
    verificar_ponto(ponto, 3.0, 4.0)
    assert isinstance(ponto.x, float)
    assert isinstance(ponto.y, float)
    print("Criação e conversão para float: OK")

    transladado = ponto.transladar(2, -6)
    verificar_ponto(transladado, 5.0, -2.0)
    verificar_ponto(ponto, 3.0, 4.0)
    assert transladado is not ponto
    print("Translação sem alterar o original: OK")

    verificar_ponto(ponto.rotacionar(0), 3.0, 4.0)
    verificar_ponto(ponto.rotacionar(pi / 2), 4.0, -3.0)
    verificar_ponto(ponto.rotacionar(pi), -3.0, -4.0)
    verificar_ponto(ponto.rotacionar(2 * pi), 3.0, 4.0)
    print("Rotações de 0°, 90°, 180° e 360°: OK")

    # Para 30°, cos(30°) = sqrt(3)/2 e sin(30°) = 1/2.
    from math import sqrt
    verificar_ponto(
        ponto.rotacionar(pi / 6),
        3 * sqrt(3) / 2 + 2,
        -3 / 2 + 2 * sqrt(3),
    )
    print("Rotação de 30°: OK")

    # Rotacionar os eixos e desfazer a rotação deve recuperar o ponto.
    recuperado = ponto.rotacionar(pi / 6).rotacionar(-pi / 6)
    verificar_ponto(recuperado, 3.0, 4.0)
    verificar_ponto(ponto, 3.0, 4.0)
    print("Rotação inversa e preservação do original: OK")

    assert repr(ponto) == "Ponto(x=3.000, y=4.000)"
    print("Representação textual: OK")

    print("Todos os testes passaram!\n")
