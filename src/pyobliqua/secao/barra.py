"""Representação de barras de armadura em seções de concreto armado.

Uma barra é identificada por suas coordenadas cartesianas, em milímetros,
e por sua área de aço (mm²) ou por uma fração da área total de armadura.

Convenções de unidades:
    - Coordenadas e distâncias: mm.
    - Áreas de aço: mm².
    - Tensões: MPa (N/mm²).
    - Forças resultantes: N.
    - Momentos resultantes: N·mm.

A distribuição das deformações e a lei constitutiva do aço são fornecidas
pelos objetos de estado de deformação e de material, respectivamente.
"""

from .ponto import Ponto


class Barra:
    """Representa uma barra longitudinal de armadura da seção.

    Args:
        x (float): Coordenada horizontal do centro da barra, em mm.
        y (float): Coordenada vertical do centro da barra, em mm.
        area (float | None): Área conhecida da barra, em mm². Se informada,
            tem prioridade sobre ``proporcao`` no cálculo de área.
        proporcao (float | None): Fração adimensional da área total de aço
            atribuída à barra. Usada quando ``area`` não é informada.

    Attributes:
        posicao (Ponto): Centro geométrico da barra.
        area (float | None): Área de aço fornecida diretamente, em mm².
        proporcao (float | None): Fração da área total de armadura.

    Notes:
        Esta classe não verifica a positividade das áreas nem exige que a
        soma das proporções de todas as barras seja igual a um. Essas
        verificações devem ser realizadas na validação dos dados da seção.
    """

    def __init__(
        self,
        x: float,
        y: float,
        area: float | None = None,
        proporcao: float | None = None,
    ) -> None:
        """Inicializa a barra e armazena sua posição e dados de armadura."""
        self.posicao = Ponto(x, y)
        self.area = area
        self.proporcao = proporcao

    @property
    def x(self) -> float:
        """float: Coordenada horizontal do centro da barra, em mm."""
        return self.posicao.x

    @property
    def y(self) -> float:
        """float: Coordenada vertical do centro da barra, em mm."""
        return self.posicao.y

    def __repr__(self) -> str:
        """Retorna uma representação textual dos dados da barra."""
        return (
            f"Barra(x={self.x:.3f}, y={self.y:.3f}, "
            f"area={self.area}, proporcao={self.proporcao})"
        )

    def obter_area(self, area_total: float | None = None) -> float:
        """Obtém a área de aço da barra.

        Args:
            area_total (float | None): Área total de armadura da seção,
                em mm², necessária apenas quando a barra é definida por
                ``proporcao``.

        Returns:
            float: Área da barra, em mm².

        Raises:
            ValueError: Se a barra não possuir área nem proporção, ou se
                a proporção for utilizada sem informar ``area_total``.

        Notes:
            Se ``area`` e ``proporcao`` forem fornecidas simultaneamente,
            prevalece a área explícita, conforme a implementação original.
        """
        if self.area is not None:
            return self.area

        if self.proporcao is not None:
            if area_total is None:
                raise ValueError("É necessário informar a área total de armadura.")
            return self.proporcao * area_total

        raise ValueError("A barra não possui área ou proporção.")

    @staticmethod
    def esforcos_aco(secao, estado, aco, area_total: float | None = None) -> tuple[float, float, float]:
        """Calcula as resultantes de todas as barras de aço da seção.

        Args:
            secao: Seção contendo a coleção ``barras`` e o método
                ``coordenadas_rotacionadas``.
            estado: Estado de deformação com ângulo ``alfa`` (rad) e método
                ``deformacao(eta)`` para obter a deformação longitudinal.
            aco: Modelo constitutivo com método ``tensao(epsilon)`` que
                retorna a tensão do aço em MPa.
            area_total (float | None): Área total de armadura, em mm²,
                usada para barras definidas por proporção.

        Returns:
            tuple[float, float, float]: Resultantes ``(Ns, Ms_xi, Ms_eta)``,
            com força normal em N e momentos em N·mm, no sistema de eixos
            rotacionados da seção.

        Raises:
            ValueError: Se uma barra não tiver área determinável por
                ``obter_area``.

        Notes:
            As resultantes são somadas para todas as barras, e não apenas
            para uma instância de ``Barra``. As convenções de sinal são
            preservadas da formulação original:

            ``Ns = Σ(Fs)``, ``Ms_xi = Σ(Fs·eta)`` e
            ``Ms_eta = -Σ(Fs·xi)``.
        """
        Ns = 0.0
        Ms_xi = 0.0
        Ms_eta = 0.0

        for barra in secao.barras:
            # Expressa a posição da barra no referencial rotacionado.
            xi, eta = secao.coordenadas_rotacionadas(barra.posicao, estado.alfa)

            # Compatibilidade de deformações e relação constitutiva do aço.
            epsilon = estado.deformacao(eta)
            sigma = aco.tensao(epsilon)
            area = barra.obter_area(area_total)
            forca = sigma * area

            # Acumula as resultantes com os sinais da formulação existente.
            Ns += forca
            Ms_xi += forca * eta
            Ms_eta -= forca * xi

        return Ns, Ms_xi, Ms_eta
