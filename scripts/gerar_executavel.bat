@echo off
setlocal
cd /d "%~dp0.."
python -m pip install -e ".[build]"
if errorlevel 1 exit /b 1
python -m PyInstaller --noconfirm --clean --onefile --windowed --name Pyobliqua --paths src --add-data "src\pyobliqua\logo_ufrgs.png;pyobliqua" scripts\entrypoint.py
if errorlevel 1 exit /b 1
echo Executavel criado em dist\Pyobliqua.exe
