"""Modelo constitutivo do concreto — aproximação da apostila de Campos Filho (2014).

Convenções:
    fck e tensões em MPa; deformações adimensionais.
    Compressão negativa; tração do concreto desprezada.

O ramo comprimido é aproximado por um polinômio quadrático:
    sigma = sigma_cd * (a2 * epsilon**2 + a1 * epsilon)
para -epsilon_c2 <= epsilon < 0, e por -sigma_cd no patamar.

A tabela 2.2 da apostila fornece coeficientes para concretos até C50
e para C60, C70, C80 e C90. Não se interpolam coeficientes.
"""


class Concreto:
    """Concreto com diagrama parábola-retângulo aproximado (2014)."""

    _COEFICIENTES = {
        60: (120101.0, 720.64),
        70: (81458.0, 620.29),
        80: (69363.0, 581.26),
        90: (64545.0, 561.34),
    }

    def __init__(self, fck: float, gamma_c: float = 1.4):
        if not math.isfinite(fck) or fck <= 0:
            raise ValueError("fck deve ser positivo e finito.")
        if not math.isfinite(gamma_c) or gamma_c <= 0:
            raise ValueError("gamma_c deve ser positivo e finito.")
        if fck > 90:
            raise ValueError("A formulação está limitada a fck <= 90 MPa.")
        if 50 < fck < 90 and fck not in self._COEFICIENTES:
            raise ValueError(
                "Para fck > 50 MPa, a tabela 2.2 contempla apenas "
                "C60, C70, C80 e C90; interpolação não implementada."
            )
        self.fck = float(fck)
        self.gamma_c = float(gamma_c)

    @property
    def fcd(self) -> float:
        """Resistência de cálculo à compressão (MPa)."""
        return self.fck / self.gamma_c

    @property
    def sigma_cd(self) -> float:
        """Módulo da tensão do patamar comprimido (MPa)."""
        return 0.85 * self.fcd

    @property
    def epsilon_c2(self) -> float:
        """Deformação do início do patamar, positiva (mm/mm)."""
        if self.fck <= 50:
            return 0.002
        return (2.0 + 0.085 * (self.fck - 50.0) ** 0.53) / 1000.0

    @property
    def epsilon_cu(self) -> float:
        """Deformação última do concreto, positiva (mm/mm)."""
        if self.fck <= 50:
            return 0.0035
        return (2.6 + 35.0 * ((90.0 - self.fck) / 100.0) ** 4) / 1000.0

    @property
    def a2(self) -> float:
        """Coeficiente quadrático da tabela 2.2 (deformação adimensional)."""
        if self.fck <= 50:
            return 250000.0
        return self._COEFICIENTES[int(self.fck)][0]

    @property
    def a1(self) -> float:
        """Coeficiente linear da tabela 2.2 (deformação adimensional)."""
        if self.fck <= 50:
            return 1000.0
        return self._COEFICIENTES[int(self.fck)][1]

    def tensao(self, epsilon: float) -> float:
        """Tensão do concreto em MPa; compressão negativa.

        O ramo parabólico usa a aproximação quadrática da apostila de
        2014. O patamar começa em -epsilon_c2 e termina em -epsilon_cu.
        """
        if not math.isfinite(epsilon):
            raise ValueError("epsilon deve ser finito.")
        if epsilon >= 0:
            return 0.0
        if epsilon < -self.epsilon_cu - 1e-12:
            raise ValueError(
                f"Deformação do concreto fora do domínio: {epsilon}"
            )
        if epsilon > -self.epsilon_c2:
            return self.sigma_cd * (
                self.a2 * epsilon**2 + self.a1 * epsilon
            )
        return -self.sigma_cd


import math


if __name__ == "__main__":
    from math import isclose

    print("TESTE: Concreto (apostila 2014)")

    c30 = Concreto(fck=30.0)
    assert isclose(c30.fcd, 30.0 / 1.4)
    assert isclose(c30.sigma_cd, 0.85 * 30.0 / 1.4)
    assert isclose(c30.epsilon_c2, 0.002)
    assert isclose(c30.epsilon_cu, 0.0035)
    assert c30.a1 == 1000.0 and c30.a2 == 250000.0
    assert c30.tensao(0.001) == 0.0
    assert c30.tensao(0.0) == 0.0
    assert isclose(c30.tensao(-0.001), -0.75 * c30.sigma_cd)
    assert isclose(c30.tensao(-0.002), -c30.sigma_cd)
    assert isclose(c30.tensao(-0.0035), -c30.sigma_cd)

    for fck, (a2, a1) in Concreto._COEFICIENTES.items():
        c = Concreto(fck)
        assert c.a2 == a2 and c.a1 == a1
        assert 0.002 < c.epsilon_c2 < 0.003
        assert 0.0025 <= c.epsilon_cu < 0.0035
        assert c.tensao(0.001) == 0
        assert isclose(c.tensao(-c.epsilon_cu), -c.sigma_cd, rel_tol=3e-2)
        assert c.tensao(-c.epsilon_c2 * 0.5) < 0

    for fck in (55, 65, 75, 85, 91):
        try:
            Concreto(fck)
        except ValueError:
            pass
        else:
            raise AssertionError(f"fck={fck} deveria ser rejeitado")

    try:
        c30.tensao(-0.004)
    except ValueError:
        pass
    else:
        raise AssertionError("Deformação além do limite deveria falhar")

    print("Todos os testes passaram!")
