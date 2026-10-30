"""Conversões de unidades para a API pública do Pyobliqua.

O núcleo numérico utiliza mm, mm², mm⁴, N, N·mm e MPa.
As unidades geométricas da API pública são fixas: cm, cm² e cm⁴.
"""

from dataclasses import dataclass
from math import isfinite

_G0 = 9.80665  # 1 kgf = 9.80665 N (gravidade convencional)
_FATORES = {
    "comprimento": {"cm": 10.0},
    "area": {"cm²": 100.0, "cm2": 100.0},
    "inercia": {"cm⁴": 10000.0, "cm4": 10000.0},
    "forca": {"kN": 1000.0, "kgf": _G0, "tf": 1000.0 * _G0},
    "momento": {"kN.m": 1e6, "kgf.m": 1000.0 * _G0, "tf.m": 1e6 * _G0},
    "tensao": {"MPa": 1.0, "kN/cm²": 10.0, "kgf/cm²": _G0 / 100.0, "tf/cm²": 10.0 * _G0},
}
_ALIASES = {
    "dimensao": "comprimento", "dimensão": "comprimento",
    "área": "area", "momento_inercia": "inercia", "momento_de_inercia": "inercia",
    "inércia": "inercia", "força": "forca", "tensão": "tensao",
}
_MOMENTOS = {"kN m": "kN.m", "kgf m": "kgf.m", "tf m": "tf.m",
            "kN·m": "kN.m", "kgf·m": "kgf.m", "tf·m": "tf.m"}


@dataclass(frozen=True)
class Unidades:
    """Seleciona unidades de força, momento e tensão; geometria sempre em cm.

    Exemplo::
        un = Unidades(forca="tf", momento="kN.m", tensao="MPa")
        N = un.para_interno(-20, "forca")  # N
        M = un.para_interno(100, "momento")  # N.mm
        As_cm2 = un.de_interno(3000, "area")
    """

    forca: str = "kN"
    momento: str = "kN.m"
    tensao: str = "MPa"

    def __post_init__(self):
        for grandeza in ("forca", "momento", "tensao"):
            unidade = self._unidade(grandeza)
            if unidade not in _FATORES[grandeza]:
                raise ValueError(f"Unidade inválida para {grandeza}: {unidade!r}. "
                                 f"Opções: {', '.join(_FATORES[grandeza])}")

    def _unidade(self, grandeza):
        if grandeza == "comprimento":
            return "cm"
        if grandeza == "area":
            return "cm²"
        if grandeza == "inercia":
            return "cm⁴"
        unidade = getattr(self, grandeza)
        return _MOMENTOS.get(unidade, unidade)

    def unidade(self, grandeza):
        """Retorna o símbolo da unidade selecionada para uma grandeza."""
        grandeza = _ALIASES.get(grandeza, grandeza)
        if grandeza not in _FATORES:
            raise ValueError(f"Grandeza desconhecida: {grandeza!r}")
        return self._unidade(grandeza)

    def _fator(self, grandeza):
        grandeza = _ALIASES.get(grandeza, grandeza)
        return _FATORES[grandeza][self.unidade(grandeza)]

    def para_interno(self, valor, grandeza):
        """Converte da unidade selecionada para a unidade interna do núcleo."""
        valor = float(valor)
        if not isfinite(valor):
            raise ValueError("O valor deve ser finito")
        return valor * self._fator(grandeza)

    def de_interno(self, valor, grandeza):
        """Converte da unidade interna do núcleo para a unidade selecionada."""
        valor = float(valor)
        if not isfinite(valor):
            raise ValueError("O valor deve ser finito")
        return valor / self._fator(grandeza)
