class Aco:
    """Modelo elastoplástico perfeito do aço classe A."""

    def __init__(
        self,
        fyk: float,
        gamma_s: float = 1.15,
        es: float = 210_000.0
    ):
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
    def fyd(self):
        return self.fyk / self.gamma_s

    @property
    def epsilon_yd(self):
        return self.fyd / self.es

    def tensao(self, epsilon: float) -> float:
        """Retorna a tensão no aço em MPa."""   

        sigma_elastica = self.es * epsilon  

        if sigma_elastica > self.fyd:
            return self.fyd 

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