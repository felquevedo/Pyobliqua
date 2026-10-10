from .ponto import Ponto


class Poligono:
    """Representa um polígono plano definido pelos seus vértices."""

    def __init__(self, vertices):
        self.vertices = [
            p if isinstance(p, Ponto) else Ponto(*p)
            for p in vertices
        ]

        if len(self.vertices) < 3:
            raise ValueError(
                "Um polígono deve possuir pelo menos três vértices."
            )

        self.area = self._calcular_area()
        self.xc, self.yc = self._calcular_centroide()
        self.IX, self.IY, self.IXY = (
            self._calcular_inercias_origem()
        )

        self.Ix = self.IX - self.area * self.yc**2
        self.Iy = self.IY - self.area * self.xc**2
        self.Ixy = (
            self.IXY
            - self.area * self.xc * self.yc
        )

    def _pares_vertices(self):
        """Percorre cada lado do polígono."""
        n = len(self.vertices)

        for i in range(n):
            p1 = self.vertices[i]
            p2 = self.vertices[(i + 1) % n]

            yield p1, p2

    def _calcular_area(self):
        soma = 0.0

        for p1, p2 in self._pares_vertices():
            soma += p1.x * p2.y - p2.x * p1.y

        return soma / 2.0

    def _calcular_centroide(self):
        soma_x = 0.0
        soma_y = 0.0

        for p1, p2 in self._pares_vertices():

            delta = (
                p1.x * p2.y
                - p2.x * p1.y
            )

            soma_x += (p1.x + p2.x) * delta
            soma_y += (p1.y + p2.y) * delta

        xc = soma_x / (6.0 * self.area)
        yc = soma_y / (6.0 * self.area)

        return xc, yc

    def _calcular_inercias_origem(self):
        ix = 0.0
        iy = 0.0
        ixy = 0.0   

        for p1, p2 in self._pares_vertices():   

            delta = (
                p1.x * p2.y
                - p2.x * p1.y
            )   

            ix += (
                p1.y**2
                + p1.y * p2.y
                + p2.y**2
            ) * delta   

            iy += (
                p1.x**2
                + p1.x * p2.x
                + p2.x**2
            ) * delta   

            ixy += (
                2 * p1.x * p1.y
                + p1.x * p2.y
                + p2.x * p1.y
                + 2 * p2.x * p2.y
            ) * delta   

        ix /= 12.0
        iy /= 12.0
        ixy /= 24.0 

        return ix, iy, ixy

    @property
    def sentido(self):
        if self.area > 0:
            return "anti-horario"   

        return "horario"    
    

    def inverter(self):
        self.vertices.reverse() 

        self.area = self._calcular_area()
        self.xc, self.yc = self._calcular_centroide()   

        self.IX, self.IY, self.IXY = (
            self._calcular_inercias_origem()
        )   

        self.Ix = self.IX - self.area * self.yc**2
        self.Iy = self.IY - self.area * self.xc**2
        self.Ixy = (
            self.IXY
            - self.area * self.xc * self.yc
        )

if __name__ == "__main__":
    from math import isclose

    def conferir(valor, esperado, nome):
        assert isclose(valor, esperado, rel_tol=1e-10, abs_tol=1e-9), (
            f"{nome}: obtido {valor}, esperado {esperado}"
        )

    print("\nTESTES: Poligono")

    # Retângulo de base 20 e altura 10, com origem no canto inferior esquerdo.
    ret = Poligono([(0, 0), (20, 0), (20, 10), (0, 10)])
    conferir(ret.area, 200, "Área do retângulo")
    conferir(ret.xc, 10, "xc do retângulo")
    conferir(ret.yc, 5, "yc do retângulo")
    conferir(ret.Ix, 20 * 10**3 / 12, "Ix centroidal")
    conferir(ret.Iy, 10 * 20**3 / 12, "Iy centroidal")
    conferir(ret.Ixy, 0, "Ixy centroidal")
    conferir(ret.IX, 20 * 10**3 / 3, "IX na origem")
    conferir(ret.IY, 10 * 20**3 / 3, "IY na origem")
    conferir(ret.IXY, 20**2 * 10**2 / 4, "IXY na origem")
    assert ret.sentido == "anti-horario"
    print("Retângulo e momentos de inércia: OK")

    # Triângulo retângulo com vértices (0,0), (12,0), (0,6).
    tri = Poligono([(0, 0), (12, 0), (0, 6)])
    conferir(tri.area, 36, "Área do triângulo")
    conferir(tri.xc, 4, "xc do triângulo")
    conferir(tri.yc, 2, "yc do triângulo")
    conferir(tri.Ix, 12 * 6**3 / 36, "Ix do triângulo")
    conferir(tri.Iy, 6 * 12**3 / 36, "Iy do triângulo")
    conferir(tri.Ixy, -(12**2 * 6**2) / 72, "Ixy do triângulo")
    print("Triângulo e produto de inércia: OK")

    # A translação altera o centroide e as inércias na origem,
    # mas não as inércias centroidais.
    trans = Poligono([(30, -7), (50, -7), (50, 3), (30, 3)])
    conferir(trans.area, ret.area, "Área transladada")
    conferir(trans.xc, 40, "xc transladado")
    conferir(trans.yc, -2, "yc transladado")
    conferir(trans.Ix, ret.Ix, "Ix transladado")
    conferir(trans.Iy, ret.Iy, "Iy transladado")
    conferir(trans.Ixy, ret.Ixy, "Ixy transladado")
    print("Invariância à translação: OK")

    # A inversão troca o sinal das grandezas orientadas,
    # mantendo as coordenadas do centroide.
    anteriores = {
        nome: getattr(ret, nome)
        for nome in ("area", "xc", "yc", "IX", "IY", "IXY", "Ix", "Iy", "Ixy")
    }
    ret.inverter()
    assert ret.sentido == "horario"
    conferir(ret.xc, anteriores["xc"], "xc após inversão")
    conferir(ret.yc, anteriores["yc"], "yc após inversão")
    for nome in ("area", "IX", "IY", "IXY", "Ix", "Iy", "Ixy"):
        conferir(getattr(ret, nome), -anteriores[nome], nome + " após inversão")
    ret.inverter()
    assert ret.sentido == "anti-horario"
    conferir(ret.area, anteriores["area"], "Área após dupla inversão")
    print("Inversão da orientação: OK")

    # Aceita tanto tuplas quanto objetos Ponto.
    misto = Poligono([Ponto(0, 0), (2, 0), Ponto(0, 2)])
    conferir(misto.area, 2, "Vértices mistos")
    print("Vértices Ponto e tuplas: OK")

    try:
        Poligono([(0, 0), (1, 0)])
    except ValueError:
        pass
    else:
        raise AssertionError("Deveria rejeitar menos de três vértices")
    print("Validação da quantidade de vértices: OK")

    print("Todos os testes passaram!")
