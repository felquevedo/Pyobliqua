"""API didática com conversão automática de unidades nas fronteiras do cálculo.

As classes de analise/secao/materiais continuam em unidades internas.
"""
from dataclasses import dataclass
from math import radians

from .unidades import Unidades
from .secao.secao import Secao
from .secao.barra import Barra
from .materiais.concreto import Concreto
from .materiais.aco import Aco
from .analise.equilibrio import resolver_equilibrio
from .analise.verificacao import resolver_verificacao
from .analise.estado_deformacao import EstadoDeformacao
from .visualizacao.desenho_secao import desenhar_secao
from .visualizacao.diagramas import desenhar_diagramas_deformacoes_tensoes


@dataclass
class Resultado:
    """Resultado público: x em cm, alfa em radianos, As em cm², lambda sem unidade."""
    bruto: object
    tipo: str
    unidades: Unidades
    secao: Secao
    concreto: Concreto

    @property
    def success(self):
        return bool(self.bruto.success)

    @property
    def x(self):
        x, alfa, ultimo = self.bruto.x
        return (self.unidades.de_interno(x, 'comprimento'), alfa,
                self.unidades.de_interno(ultimo, 'area') if self.tipo == 'dimensionamento' else ultimo)

    @property
    def x_interno(self):
        """Solução em unidades internas (uso técnico e depuração)."""
        return self.bruto.x

    def __getattr__(self, nome):
        return getattr(self.bruto, nome)


class Modelo:
    """Fachada para exemplos: todos os argumentos usam as unidades escolhidas.

    Comprimentos em cm, áreas em cm², ângulos em radianos; sem conversões manuais.
    """
    def __init__(self, unidades=None):
        self.unidades = unidades if unidades is not None else Unidades()

    def barra(self, x, y, area=None, proporcao=None):
        u = self.unidades
        return Barra(u.para_interno(x, 'comprimento'), u.para_interno(y, 'comprimento'),
                     area=None if area is None else u.para_interno(area, 'area'),
                     proporcao=proporcao)

    def secao(self, contorno, furos=None, barras=None):
        u = self.unidades
        def vertices(pontos):
            return [(u.para_interno(x, 'comprimento'), u.para_interno(y, 'comprimento')) for x, y in pontos]
        return Secao(vertices(contorno), [vertices(f) for f in (furos or [])], barras or [])

    def concreto(self, fck, gamma_c=1.4):
        return Concreto(self.unidades.para_interno(fck, 'tensao'), gamma_c=gamma_c)

    def aco(self, fyk, gamma_s=1.15, es=None):
        u = self.unidades
        # O valor padrão de Es é 210000 MPa, independentemente da unidade escolhida.
        es_interno = 210000.0 if es is None else u.para_interno(es, 'tensao')
        return Aco(u.para_interno(fyk, 'tensao'), gamma_s=gamma_s, es=es_interno)

    def dimensionar(self, secao, concreto, aco, Nsd, Msdx, Msdy, *, x0=None, alfa0=0.0, As0=None, **opcoes):
        u = self.unidades
        bruto = resolver_equilibrio(
            secao, concreto, aco, u.para_interno(Nsd, 'forca'),
            u.para_interno(Msdx, 'momento'), u.para_interno(Msdy, 'momento'),
            x0=None if x0 is None else u.para_interno(x0, 'comprimento'), alfa0=alfa0,
            As0=None if As0 is None else u.para_interno(As0, 'area'), **opcoes)
        return Resultado(bruto, 'dimensionamento', u, secao, concreto)

    def verificar(self, secao, concreto, aco, As, Nsd, Msdx, Msdy, *, x0=None, alfa0=0., lambda0=1., **opcoes):
        u = self.unidades
        bruto = resolver_verificacao(
            secao, concreto, aco, As=u.para_interno(As, 'area'),
            Nsd=u.para_interno(Nsd, 'forca'), Msdx=u.para_interno(Msdx, 'momento'),
            Msdy=u.para_interno(Msdy, 'momento'),
            x0=None if x0 is None else u.para_interno(x0, 'comprimento'),
            alfa0=alfa0, lambda0=lambda0, **opcoes)
        return Resultado(bruto, 'verificacao', u, secao, concreto)

    def grafico(self, resultado, *, As=None, esforcos=None, titulo=None, ax=None, mostrar=False):
        """Desenha seção e diagramas usando dados de entrada nas unidades selecionadas."""
        import matplotlib.pyplot as plt
        u = self.unidades
        secao = resultado.secao
        concreto = resultado.concreto
        x, alfa, ultimo = resultado.x_interno
        area_total = ultimo if resultado.tipo == 'dimensionamento' else u.para_interno(As, 'area')
        estado = EstadoDeformacao(secao, x, alfa, concreto)
        if ax is None:
            _, ax = plt.subplots(figsize=(12, 7))
        esforcos_internos = None
        if esforcos is not None:
            n, mx, my = esforcos
            fator = ultimo if resultado.tipo == 'verificacao' else 1.0
            esforcos_internos = (fator * u.para_interno(n, 'forca'),
                                 fator * u.para_interno(mx, 'momento'),
                                 fator * u.para_interno(my, 'momento'))
        desenhar_secao(secao, area_total=area_total, estado=estado, ax=ax,
                      mostrar=False, esforcos=esforcos_internos,
                      tipo_esforcos='resistentes' if resultado.tipo == 'verificacao' else 'solicitantes',
                      titulo=titulo)
        desenhar_diagramas_deformacoes_tensoes(ax, secao, estado, concreto)
        if mostrar:
            plt.show()
        return ax
