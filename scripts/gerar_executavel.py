"""Gera Pyobliqua.exe no Windows, com a mesma versão exibida em Sobre.

Na raiz do projeto: python scripts/gerar_executavel.py
Requer: python -m pip install pyinstaller
"""
from pathlib import Path
import re
import os
import subprocess
import sys

RAIZ = Path(__file__).resolve().parents[1]
SRC = RAIZ / 'src'
VERSAO_ARQUIVO = SRC / 'pyobliqua' / '_version.py'
conteudo = VERSAO_ARQUIVO.read_text(encoding='utf-8')
correspondencia = re.search(r'^__version__\s*=\s*[\'\"]([0-9]+(?:\.[0-9]+){1,3})[\'\"]', conteudo, re.M)
if not correspondencia:
    raise SystemExit('Defina __version__ como uma versão numérica em _version.py.')
versao = correspondencia.group(1)
partes = [int(p) for p in versao.split('.')]
partes += [0] * (4 - len(partes))
versao_windows = ', '.join(map(str, partes))
versao_texto = '.'.join(map(str, partes))

pasta_build = RAIZ / 'build' / 'pyobliqua'
# Arquivos temporários fora do OneDrive para evitar bloqueios durante --clean.
pasta_trabalho = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))) / 'Pyobliqua' / 'build'
icone = SRC / 'pyobliqua' / 'assets' / 'pyobliqua.ico'
if not icone.is_file():
    raise SystemExit(f'Ícone não encontrado: {icone}. Salve pyobliqua.ico em src/pyobliqua/assets/.')
pasta_build.mkdir(parents=True, exist_ok=True)
recurso = pasta_build / 'version_info.txt'
recurso.write_text(f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers=({versao_windows}), prodvers=({versao_windows}),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('CompanyName', 'UFRGS'),
    StringStruct('FileDescription', 'Pyobliqua - Dimensionamento e verificação de seções de concreto armado'),
    StringStruct('FileVersion', '{versao_texto}'),
    StringStruct('InternalName', 'Pyobliqua'),
    StringStruct('OriginalFilename', 'Pyobliqua.exe'),
    StringStruct('ProductName', 'Pyobliqua'),
    StringStruct('ProductVersion', '{versao_texto}')
  ])]), VarFileInfo([VarStruct('Translation', [1033, 1200])])]
)
''', encoding='utf-8')
launcher = pasta_build / 'iniciar_pyobliqua.py'
launcher.write_text('from pyobliqua.__main__ import main\n\nif __name__ == "__main__":\n    main()\n', encoding='utf-8')
comando = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
           '--windowed', '--name', 'Pyobliqua', '--icon', str(icone), '--paths', str(SRC),
           '--collect-data', 'pyobliqua',
           '--version-file', str(recurso), '--distpath', str(RAIZ / 'dist'),
           '--workpath', str(pasta_trabalho), '--specpath', str(pasta_build),
           str(launcher)]
print(f'Compilando Pyobliqua versão {versao}...')
subprocess.run(comando, check=True, cwd=RAIZ)
print('Executável:', RAIZ / 'dist' / 'Pyobliqua.exe')
