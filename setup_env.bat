@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   Configurando entorno virtual
echo ============================================

REM Cambia al directorio donde esta este .bat
cd /d "%~dp0"

REM Verifica que exista requirements.txt
if not exist "requirements.txt" (
    echo [ERROR] No se encontro requirements.txt en esta carpeta.
    pause
    exit /b 1
)

REM Crea el entorno virtual si no existe
if not exist "venv\Scripts\activate.bat" (
    echo Creando entorno virtual "venv"...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual. Verifica que Python este instalado y en el PATH.
        pause
        exit /b 1
    )
) else (
    echo El entorno virtual "venv" ya existe, se omite la creacion.
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Actualizando pip...
python -m pip install --upgrade pip

echo Instalando dependencias desde requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Fallo la instalacion de dependencias.
    pause
    exit /b 1
)

echo ============================================
echo   Entorno configurado correctamente
echo ============================================
pause
