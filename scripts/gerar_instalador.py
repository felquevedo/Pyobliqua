"""Compila Pyobliqua.exe e seu instalador Inno Setup no Windows.

Execute da raiz do repositório: python scripts/gerar_instalador.py
Requisitos: PyInstaller no mesmo Python e Inno Setup 6/7 instalado.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = RAIZ / "scripts"
VERSAO_PY = RAIZ / "src" / "pyobliqua" / "_version.py"
ISS = SCRIPTS / "instalador.iss"


def versao() -> str:
    texto = VERSAO_PY.read_text(encoding="utf-8")
    encontrado = re.search(r'^__version__\s*=\s*[\'\"](\d+(?:\.\d+){1,3})[\'\"]', texto, re.M)
    if not encontrado:
        raise SystemExit("Não foi possível ler __version__ de src/pyobliqua/_version.py")
    return encontrado.group(1)


def localizar_iscc() -> Path:
    candidatos = []
    if os.environ.get("INNO_SETUP_COMPILER"):
        candidatos.append(Path(os.environ["INNO_SETUP_COMPILER"]))
    for nome in ("ISCC.exe", "iscc.exe"):
        encontrado = shutil.which(nome)
        if encontrado:
            candidatos.append(Path(encontrado))
    for variavel in ("ProgramFiles(x86)", "ProgramFiles"):
        base = os.environ.get(variavel)
        if base:
            for pasta in ("Inno Setup 7", "Inno Setup 6"):
                candidatos.append(Path(base) / pasta / "ISCC.exe")
    for candidato in candidatos:
        if candidato.is_file():
            return candidato
    raise SystemExit(
        "ISCC.exe não encontrado. Instale Inno Setup 6/7 ou configure "
        "INNO_SETUP_COMPILER com o caminho completo do ISCC.exe."
    )


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("A compilação do instalador deve ser feita no Windows.")
    if not ISS.is_file():
        raise SystemExit(f"Arquivo Inno Setup não encontrado: {ISS}")
    v = versao()
    print(f"Gerando Pyobliqua {v} com Python: {sys.executable}", flush=True)
    subprocess.run([sys.executable, str(SCRIPTS / "gerar_executavel.py")], cwd=RAIZ, check=True)
    exe = RAIZ / "dist" / "Pyobliqua.exe"
    if not exe.is_file():
        raise SystemExit(f"Executável não encontrado: {exe}")
    compilador = localizar_iscc()
    print(f"Compilando instalador com {compilador}", flush=True)
    subprocess.run([str(compilador), f"/DAppVersion={v}", str(ISS)], cwd=RAIZ, check=True)
    instalador = RAIZ / "dist" / "installer" / f"Pyobliqua_Setup_{v}.exe"
    if not instalador.is_file():
        raise SystemExit(f"Instalador não encontrado: {instalador}")
    print(f"Instalador pronto: {instalador}")


if __name__ == "__main__":
    main()
