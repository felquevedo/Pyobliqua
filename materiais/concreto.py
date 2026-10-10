class Concreto:
    """Modelo constitutivo do concreto conforme a apostila."""

    def __init__(
        self,
        fck: float,
        gamma_c: float = 1.4
    ):
        if fck <= 0:
            raise ValueError("fck deve ser positivo.")

        if gamma_c <= 0:
            raise ValueError("gamma_c deve ser positivo.")

        self.fck = float(fck)
        self.gamma_c = float(gamma_c)

    @property
    def fcd(self):
        return self.fck / self.gamma_c

    @property
    def sigma_cd(self):
        return 0.85 * self.fcd


    def tensao(self, epsilon: float) -> float:
        """Retorna a tensão do concreto em MPa."""  

        # concreto tracionado
        if epsilon >= 0.0:
            return 0.0  

        # trecho parabólico
        if epsilon >= -0.002:
            return -self.sigma_cd * (
                1.0
                - (1.0 + epsilon / 0.002) ** 2
            )   

        # trecho constante
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