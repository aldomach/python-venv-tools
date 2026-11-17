@echo off
if exist "%~dp0VenvTool.exe" (
 start "" "%~dp0VenvTool.exe"
 exit /b
)
where py.exe >nul 2>&1
if errorlevel 1 goto fallback
py -3 -B "%~dp0venv_gui.py"
exit /b %errorlevel%
:fallback
python -B "%~dp0venv_gui.py"
exit /b %errorlevel%
