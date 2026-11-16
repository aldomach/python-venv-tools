@echo off
setlocal DisableDelayedExpansion
where py.exe >nul 2>&1
if errorlevel 1 goto fallback
py -3 -B "%~dp0venv_gui.py"
if errorlevel 1 pause
exit /b
:fallback
python -B "%~dp0venv_gui.py"
if errorlevel 1 pause
