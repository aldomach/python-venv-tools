@echo off
setlocal DisableDelayedExpansion
if not exist "%~dp0venv_cli.exe" goto source
"%~dp0venv_cli.exe" requirements %*
exit /b %errorlevel%
:source
where py.exe >nul 2>&1
if errorlevel 1 goto fallback
py -3 -I -B "%~dp0venv_manager.py" requirements %*
exit /b %errorlevel%
:fallback
python -I -B "%~dp0venv_manager.py" requirements %*
exit /b %errorlevel%
