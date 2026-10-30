"""Testes de regressão dos exemplos; não substituem validação independente."""
import subprocess
import sys


def test_exemplos_conhecidos():
    resultado = subprocess.run(
        [sys.executable, "-m", "pyobliqua.main"],
        capture_output=True, text=True, check=True, timeout=90,
    )
    assert resultado.stdout.count("Convergencia: True") == 2
    assert "As = 37.28896 cm²" in resultado.stdout
    assert "lambda = 0.93460410" in resultado.stdout
