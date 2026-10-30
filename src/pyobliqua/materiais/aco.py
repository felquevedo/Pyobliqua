"""Modelo constitutivo elastoplástico perfeito para o aço classe A.

O diagrama tensão-deformação é linear até a tensão de escoamento de
cálculo e apresenta um patamar plástico, tanto em tração quanto em
compressão. Não são considerados encruamento nem ruptura por deformação.

Convenções:
    - Tensões e resistências: MPa (N/mm²).
    - Módulo de elasticidade: MPa.
    - Deformações: adimensionais (mm/mm).
    - Tração: tensão e deformação positivas.
    - Compressão: tensão e deformação negativas.
"""


class Aco:
    """Representa o comportamento elastoplástico perfeito do aço classe A.

    Attributes:
        fyk (float): Resistência característica ao escoamento, em MPa.
        gamma_s (float): Coeficiente parcial de segurança do aço.
        es (float): Módulo de elasticidade longitudinal, em MPa.
    """

    def __init__(
        self,
        fyk: float,
        gamma_s: float = 1.15,
        es: float = 210_000.0
    ):
        """Inicializa os parâmetros mecânicos do aço.

        Args:
            fyk (float): Resistência característica ao escoamento, em MPa.
            gamma_s (float): Coeficiente parcial de segurança, adimensional.
                O valor padrão é 1,15.
            es (float): Módulo de elasticidade, em MPa.
                O valor padrão é 210.000 MPa.

        Raises:
            ValueError: Se ``fyk``, ``gamma_s`` ou ``es`` não for positivo.
        """
        if fyk <= 0:
            raise ValueError("fyk deve ser positivo.")

        if gamma_s <= 0:
            raise ValueError("gamma_s deve ser positivo.")

        if es <= 0:
            raise ValueError("Es deve ser positivo.")

        self.fyk = float(fyk)
        self.gamma_s = float(gamma_s)
        self.es = float(es)

    @property
    def fyd(self) -> float:
        """Calcula a resistência de cálculo ao escoamento, em MPa.

        Returns:
            float: Razão ``fyk / gamma_s``, em MPa.
        """
        return self.fyk / self.gamma_s

    @property
    def epsilon_yd(self) -> float:
        """Calcula a deformação correspondente ao escoamento de cálculo.

        Returns:
            float: Razão ``fyd / es``, adimensional.
        """
        return self.fyd / self.es

    def tensao(self, epsilon: float) -> float:
        """Calcula a tensão no aço para uma deformação longitudinal.

        Args:
            epsilon (float): Deformação longitudinal, adimensional;
                positiva em tração e negativa em compressão.

        Returns:
            float: Tensão no aço, em MPa, limitada ao intervalo
            ``[-fyd, fyd]``.

        Notes:
            No trecho elástico, ``sigma = es * epsilon``. Após atingir
            o escoamento de cálculo, a tensão permanece constante em
            ``+fyd`` (tração) ou ``-fyd`` (compressão).
        """
        # Resposta elástica inicial, válida até o escoamento de cálculo.
        sigma_elastica = self.es * epsilon

        # Patamar plástico em tração.
        if sigma_elastica > self.fyd:
            return self.fyd

        # Patamar plástico em compressão.
        if sigma_elastica < -self.fyd:
            return -self.fyd

        return sigma_elastica


if __name__ == "__main__":

    from math import isclose

    print("\nTESTE: Aço")

    aco = Aco(
        fyk=500.0,
        gamma_s=1.15,
        es=210000.0
    )

    fyd = 500.0 / 1.15
    epsilon_yd = fyd / 210000.0

    assert isclose(aco.fyd, fyd)
    assert isclose(aco.epsilon_yd, epsilon_yd)

    assert isclose(
        aco.tensao(0.001),
        210.0
    )

    assert isclose(
        aco.tensao(-0.001),
        -210.0
    )

    assert isclose(
        aco.tensao(0.010),
        fyd
    )

    assert isclose(
        aco.tensao(-0.010),
        -fyd
    )

    print("Todos os testes passaram!")
