@echo off
setlocal DisableDelayedExpansion
where py.exe >nul 2>&1
if errorlevel 1 goto fallback
py -3 -I -B "%~dp0venv_manager.py" setup %*
exit /b %errorlevel%
:fallback
python -I -B "%~dp0venv_manager.py" setup %*
exit /b %errorlevel%
