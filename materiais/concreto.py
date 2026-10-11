"""Modelo constitutivo uniaxial do concreto para o Pyobliqua.

Implementa o diagrama tensão-deformação parábola-retângulo adotado
na apostila utilizada como referência pelo projeto.

Convenções:
    - Resistências e tensões são expressas em MPa (N/mm²).
    - Deformações específicas são adimensionais (mm/mm).
    - Compressão possui deformação e tensão negativas.
    - A resistência à tração do concreto é desprezada.
    - O trecho parabólico termina em -0,002 (-2 ‰).
    - O patamar constante termina em -0,0035 (-3,5 ‰).

O módulo reproduz as equações do arquivo original; não implementa
outros diagramas constitutivos nem verifica a adequação normativa
para situações distintas daquelas previstas no projeto.
"""


class Concreto:
    """Representa o concreto pelo diagrama parábola-retângulo.

    Attributes:
        fck (float): Resistência característica à compressão, em MPa.
        gamma_c (float): Coeficiente parcial de segurança do concreto.
    """

    def __init__(
        self,
        fck: float,
        gamma_c: float = 1.4
    ):
        """Inicializa as propriedades resistentes do concreto.

        Args:
            fck (float): Resistência característica à compressão, em MPa.
            gamma_c (float): Coeficiente parcial de segurança, positivo.
                O valor padrão é 1,4.

        Raises:
            ValueError: Se ``fck`` ou ``gamma_c`` não forem positivos.
        """
        if fck <= 0:
            raise ValueError("fck deve ser positivo.")

        if gamma_c <= 0:
            raise ValueError("gamma_c deve ser positivo.")

        self.fck = float(fck)
        self.gamma_c = float(gamma_c)

    @property
    def fcd(self) -> float:
        """Calcula a resistência de cálculo à compressão do concreto.

        Returns:
            float: ``fck / gamma_c``, em MPa.
        """
        return self.fck / self.gamma_c

    @property
    def sigma_cd(self) -> float:
        """Calcula o módulo da tensão do patamar de compressão.

        Returns:
            float: ``0.85 * fcd``, em MPa (valor positivo).

        Notes:
            O método ``tensao`` aplica sinal negativo ao resultado
            quando o concreto está comprimido.
        """
        return 0.85 * self.fcd

    def tensao(self, epsilon: float) -> float:
        """Calcula a tensão normal do concreto para uma deformação.

        Args:
            epsilon (float): Deformação específica adimensional.
                Valores negativos indicam compressão.

        Returns:
            float: Tensão normal em MPa, conforme o diagrama:

                - ``epsilon >= 0``: tensão nula (tração desprezada).
                - ``-0.002 <= epsilon < 0``: trecho parabólico.
                - ``-0.0035 <= epsilon < -0.002``: patamar constante.

        Raises:
            ValueError: Se ``epsilon < -0.0035``, fora do domínio
                de compressão admitido pela implementação.

        Notes:
            No trecho parabólico, a tensão é calculada por
            ``-sigma_cd * [1 - (1 + epsilon / 0.002)**2]``.
            No patamar, a tensão é ``-sigma_cd``.
        """
        # Despreza a resistência à tração do concreto.
        if epsilon >= 0.0:
            return 0.0

        # Compressão: ramo parabólico entre 0 e -2 ‰.
        if epsilon >= -0.002:
            return -self.sigma_cd * (
                1.0
                - (1.0 + epsilon / 0.002) ** 2
            )

        # Compressão: patamar constante entre -2 ‰ e -3,5 ‰.
        if epsilon >= -0.0035:
            return -self.sigma_cd

        raise ValueError(
            f"Deformação do concreto fora do domínio: {epsilon}"
        )


if __name__ == "__main__":
    from math import isclose

    print("\nTESTE: Concreto")

    concreto = Concreto(
        fck=30.0,
        gamma_c=1.4
    )

    sigma_cd = 0.85 * 30.0 / 1.4

    assert isclose(
        concreto.sigma_cd,
        sigma_cd
    )

    assert isclose(
        concreto.tensao(0.001),
        0.0
    )

    assert isclose(
        concreto.tensao(0.0),
        0.0
    )

    assert isclose(
        concreto.tensao(-0.001),
        -0.75 * sigma_cd
    )

    assert isclose(
        concreto.tensao(-0.002),
        -sigma_cd
    )

    assert isclose(
        concreto.tensao(-0.0035),
        -sigma_cd
    )

    print("Todos os testes passaram!")
