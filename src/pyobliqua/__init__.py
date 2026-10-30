"""API pública do Pyobliqua para exemplos e scripts didáticos."""

__version__ = "0.1.0"

from .secao.secao import Secao
from .secao.barra import Barra
from .materiais.concreto import Concreto
from .materiais.aco import Aco
from .analise.equilibrio import resolver_equilibrio
from .analise.verificacao import resolver_verificacao
from .analise.estado_deformacao import EstadoDeformacao
from .visualizacao.desenho_secao import desenhar_secao
from .visualizacao.diagramas import desenhar_diagramas_deformacoes_tensoes

__all__ = [
    "Secao", "Barra", "Concreto", "Aco", "resolver_equilibrio",
    "resolver_verificacao", "EstadoDeformacao", "desenhar_secao",
    "desenhar_diagramas_deformacoes_tensoes",
]

from .unidades import Unidades
from .api import Modelo, Resultado
__all__ += ["Unidades", "Modelo", "Resultado"]
