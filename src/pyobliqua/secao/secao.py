"""Representação geométrica de uma seção poligonal de concreto armado.

O módulo reúne um contorno externo, eventuais furos e barras de
armadura, calculando área líquida, centroide e inércias centroidais.

Convenções:
    - Coordenadas e comprimentos: mm.
    - Áreas: mm²; momentos e produto de inércia: mm⁴.
    - Contorno externo anti-horário: contribuição positiva.
    - Furos horários: contribuições negativas.
    - Ângulos de transformação: radianos.

O módulo descreve a geometria; não realiza o dimensionamento estrutural.
"""

from .poligono import Poligono
from .barra import Barra
from math import cos, sin

class Secao:
    """Representa uma seção poligonal de concreto armado.

    Attributes:
        contorno (Poligono): Contorno externo da seção.
        furos (list[Poligono]): Polígonos que representam vazios.
        barras (list[Barra]): Barras de armadura da seção.
        area (float): Área líquida orientada, em mm².
        xc (float): Abscissa do centroide, em mm.
        yc (float): Ordenada do centroide, em mm.
        Ix (float): Momento de inércia centroidal em torno de x, mm⁴.
        Iy (float): Momento de inércia centroidal em torno de y, mm⁴.
        Ixy (float): Produto de inércia centroidal, mm⁴.
    """

    def __init__(
        self,
        contorno,
        furos=None,
        barras=None
    ):
        """Inicializa a seção, seus vazios e as barras de armadura.

        Args:
            contorno: Sequência de vértices (x, y) do contorno externo, em mm.
            furos: Sequência opcional de polígonos que representam vazios.
                Cada furo é uma sequência de vértices (x, y), em mm.
            barras: Sequência opcional de objetos Barra ou de argumentos
                posicionais aceitos por ``Barra(*barra)``.

        Raises:
            ValueError: Se algum polígono tiver menos de três vértices
                ou se a área líquida calculada não for positiva.

        Notes:
            O contorno externo é orientado no sentido anti-horário
            (área positiva) e os furos, no horário (área negativa).
            A orientação é corrigida automaticamente.
        """
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

        """Calcula as propriedades geométricas líquidas da seção.

        A área e os momentos estáticos são obtidos por soma algébrica
        das propriedades dos polígonos. As inércias em relação à origem
        são transportadas para os eixos centroidais pelo teorema
        dos eixos paralelos.

        Raises:
            ValueError: Se a área líquida for nula ou negativa.

        Notes:
            Atualiza ``area`` (mm²), ``xc`` e ``yc`` (mm), além de
            ``Ix``, ``Iy`` e ``Ixy`` (mm⁴).
        """
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
    
        """Obtém as coordenadas de um ponto relativas ao centroide.

        Args:
            ponto (Ponto): Ponto expresso no sistema global, em mm.

        Returns:
            tuple[float, float]: Coordenadas (x, y) em relação ao
            centroide da seção, em mm.
        """
        x = ponto.x - self.xc
        y = ponto.y - self.yc
    
        return x, y

    def coordenadas_rotacionadas(self, ponto, alfa):    

        """Transforma as coordenadas para eixos centroidais rotacionados.

        Args:
            ponto (Ponto): Ponto no sistema global, em mm.
            alfa (float): Ângulo de rotação dos eixos, em radianos.

        Returns:
            tuple[float, float]: Coordenadas (xi, eta), em mm.

        Notes:
            xi = x*cos(alfa) + y*sin(alfa)
            eta = -x*sin(alfa) + y*cos(alfa)

            Trata-se da rotação dos eixos de referência, e não
            da rotação física do ponto.
        """
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

        """Obtém as coordenadas extremas do concreto no eixo eta.

        Args:
            alfa (float): Ângulo dos eixos locais, em radianos.

        Returns:
            tuple[float, float]: (eta_inferior, eta_superior), em mm.

        Notes:
            Os extremos são calculados a partir dos vértices do
            contorno externo. Os furos não alteram esses limites.
        """
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

        """Obtém as coordenadas extremas das barras no eixo eta.

        Args:
            alfa (float): Ângulo dos eixos locais, em radianos.

        Returns:
            tuple[float | None, float | None]: Menor e maior coordenada
            eta das barras, em mm; (None, None) se não houver barras.
        """
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
        """Calcula a altura total da seção na direção eta.

        Args:
            alfa (float): Ângulo dos eixos locais, em radianos.

        Returns:
            float: Distância entre as fibras extremas de concreto, em mm.
        """
        eta_i, eta_s = self.limites_eta_concreto(alfa)
    
        return eta_s - eta_i
    
    
    def altura_util(self, alfa):
        """Calcula a distância da fibra superior à barra mais inferior.

        Args:
            alfa (float): Ângulo dos eixos locais, em radianos.

        Returns:
            float: Altura útil na direção eta, em mm.

        Raises:
            ValueError: Se a seção não possuir barras de armadura.
        """
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
