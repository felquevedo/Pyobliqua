from .poligono import Poligono
from .barra import Barra
from math import cos, sin

class Secao:
    """Seção poligonal de concreto armado."""

    def __init__(
        self,
        contorno,
        furos=None,
        barras=None
    ):
        self.contorno = Poligono(contorno)

        self.furos = [
            Poligono(furo)
            for furo in (furos or [])
        ]

        self.barras = [
            barra if isinstance(barra, Barra)
            else Barra(*barra)
            for barra in (barras or [])
        ]

        if self.contorno.area < 0:
            self.contorno.inverter()

        for furo in self.furos:
            if furo.area > 0:
                furo.inverter()

        self._calcular_propriedades()

    def _calcular_propriedades(self):   

        poligonos = [
            self.contorno,
            *self.furos
        ]   

        self.area = sum(
            p.area for p in poligonos
        )   

        if self.area <= 0:
            raise ValueError(
                "A área líquida da seção deve ser positiva."
            )   

        self.xc = (
            sum(p.area * p.xc for p in poligonos)
            / self.area
        )   

        self.yc = (
            sum(p.area * p.yc for p in poligonos)
            / self.area
        )   

        IX = sum(p.IX for p in poligonos)
        IY = sum(p.IY for p in poligonos)
        IXY = sum(p.IXY for p in poligonos) 

        self.Ix = (
            IX
            - self.area * self.yc**2
        )   

        self.Iy = (
            IY
            - self.area * self.xc**2
        )   

        self.Ixy = (
            IXY
            - self.area * self.xc * self.yc
        )

    def coordenadas_locais(self, ponto):
    
        x = ponto.x - self.xc
        y = ponto.y - self.yc
    
        return x, y

    def coordenadas_rotacionadas(self, ponto, alfa):    

        x, y = self.coordenadas_locais(ponto)   

        xi = (
            x * cos(alfa)
            + y * sin(alfa)
        )   

        eta = (
            -x * sin(alfa)
            + y * cos(alfa)
        )   

        return xi, eta

    def limites_eta_concreto(self, alfa):   

        pontos = self.contorno.vertices 

        etas = [
            self.coordenadas_rotacionadas(
                ponto,
                alfa
            )[1]
            for ponto in pontos
        ]   

        return min(etas), max(etas) 


    def limites_eta_armadura(self, alfa):   

        if not self.barras:
            return None, None   

        etas = [
            self.coordenadas_rotacionadas(
                barra.posicao,
                alfa
            )[1]
            for barra in self.barras
        ]   

        return min(etas), max(etas)

    def altura(self, alfa):
        eta_i, eta_s = self.limites_eta_concreto(alfa)
    
        return eta_s - eta_i
    
    
    def altura_util(self, alfa):
        eta_i_aco, _ = self.limites_eta_armadura(alfa)
        _, eta_s = self.limites_eta_concreto(alfa)
    
        if eta_i_aco is None:
            raise ValueError(
                "A seção não possui barras de armadura."
            )
    
        return eta_s - eta_i_aco

if __name__ == "__main__":
    from math import isclose, pi
    from .ponto import Ponto

    def conferir(obtido, esperado):
        assert isclose(obtido, esperado, rel_tol=1e-10, abs_tol=1e-8), (
            f"Esperado {esperado}, obtido {obtido}"
        )

    print("\nTESTES: Secao")

    contorno = [(0, 0), (200, 0), (200, 100), (0, 100)]
    barras = [(20, 20, 100), (180, 80, 100)]
    secao = Secao(contorno, barras=barras)
    conferir(secao.area, 20000)
    conferir(secao.xc, 100)
    conferir(secao.yc, 50)
    conferir(secao.Ix, 200 * 100**3 / 12)
    conferir(secao.Iy, 100 * 200**3 / 12)
    conferir(secao.Ixy, 0)
    print("Retângulo: área, centroide e inércias: OK")

    conferir(secao.coordenadas_locais(Ponto(120, 70))[0], 20)
    conferir(secao.coordenadas_locais(Ponto(120, 70))[1], 20)
    xi, eta = secao.coordenadas_rotacionadas(Ponto(120, 70), pi / 2)
    conferir(xi, 20)
    conferir(eta, -20)
    print("Coordenadas locais e rotacionadas: OK")

    conferir(secao.altura(0), 100)
    conferir(secao.altura(pi / 2), 200)
    conferir(secao.altura_util(0), 80)
    conferir(secao.altura_util(pi / 2), 180)
    assert secao.limites_eta_armadura(0) == (-30, 30)
    print("Limites de eta e alturas: OK")

    furo = [(50, 25), (150, 25), (150, 75), (50, 75)]
    vazada = Secao(contorno, furos=[furo])
    conferir(vazada.area, 15000)
    conferir(vazada.xc, 100)
    conferir(vazada.yc, 50)
    conferir(vazada.Ix, 200 * 100**3 / 12 - 100 * 50**3 / 12)
    conferir(vazada.Iy, 100 * 200**3 / 12 - 50 * 100**3 / 12)
    conferir(vazada.Ixy, 0)
    assert vazada.contorno.area > 0
    assert vazada.furos[0].area < 0
    print("Seção vazada e orientação dos contornos: OK")

    invertida = Secao(list(reversed(contorno)), furos=[list(reversed(furo))])
    for atributo in ("area", "xc", "yc", "Ix", "Iy", "Ixy"):
        conferir(getattr(invertida, atributo), getattr(vazada, atributo))
    print("Independência da orientação de entrada: OK")

    sem_barras = Secao(contorno)
    assert sem_barras.limites_eta_armadura(0) == (None, None)
    try:
        sem_barras.altura_util(0)
    except ValueError:
        pass
    else:
        raise AssertionError("Deveria rejeitar altura útil sem armaduras")
    print("Ausência de barras: OK")

    try:
        Secao([(0, 0), (10, 0), (10, 10), (0, 10)],
              furos=[[(0, 0), (20, 0), (20, 20), (0, 20)]])
    except ValueError:
        pass
    else:
        raise AssertionError("Deveria rejeitar área líquida não positiva")
    print("Área líquida não positiva: OK")
    print("Todos os testes passaram!")
