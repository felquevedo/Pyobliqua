"""Testes de regressão dos resultados conhecidos; não substituem validação independente."""
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "exemplo, esperado",
    [("5.1", "As = 37.28896 cm²"), ("5.2", "lambda = 0.93460410")],
)
def test_exemplos_conhecidos(exemplo, esperado):
    resultado = subprocess.run(
        [sys.executable, "-m", "pyobliqua.main", "--exemplo", exemplo],
        capture_output=True, text=True, check=True, timeout=90,
    )
    assert "Convergencia: True" in resultado.stdout
    assert esperado in resultado.stdout
