@echo off
setlocal

REM Cambia al directorio donde esta este .bat
cd /d "%~dp0"

REM Verifica que exista el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] No se encontro el entorno virtual "venv".
    echo Ejecuta primero setup_env.bat para crearlo.
    pause
    exit /b 1
)

REM Verifica que exista main.py
if not exist "main.py" (
    echo [ERROR] No se encontro main.py en esta carpeta.
    pause
    exit /b 1
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Ejecutando main.py...
python main.py

echo.
echo ============================================
echo   Programa finalizado
echo ============================================
