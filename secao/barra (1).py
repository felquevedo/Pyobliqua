from .ponto import Ponto

class Barra:
    """Representa uma barra de armadura."""

    def __init__(
        self,
        x: float,
        y: float,
        area: float | None = None,
        proporcao: float | None = None
    ):
        self.posicao = Ponto(x, y)
        self.area = area
        self.proporcao = proporcao

    @property
    def x(self):
        return self.posicao.x

    @property
    def y(self):
        return self.posicao.y

    def __repr__(self):
        return (
            f"Barra(x={self.x:.3f}, y={self.y:.3f}, "
            f"area={self.area}, proporcao={self.proporcao})"
        )

    def obter_area(self, area_total=None):

        if self.area is not None:
            return self.area

        if self.proporcao is not None:

            if area_total is None:
                raise ValueError(
                    "É necessário informar a área "
                    "total de armadura."
                )

            return (
                self.proporcao
                * area_total
            )

        raise ValueError(
            "A barra não possui área ou proporção."
        )

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