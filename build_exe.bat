@echo off
setlocal DisableDelayedExpansion
set "PYTHONPATH="
set "PYTHONHOME="
cd /d "%~dp0"
set "BUILDENV=%LOCALAPPDATA%\python-venv-tools-build\venv"
if exist "%BUILDENV%\Scripts\python.exe" goto install
py -3 -m venv "%BUILDENV%"
if errorlevel 1 exit /b 1
:install
"%BUILDENV%\Scripts\python.exe" -m pip --require-virtualenv install -r requirements-build.txt
if errorlevel 1 exit /b 1
"%BUILDENV%\Scripts\python.exe" -m PyInstaller --noconfirm --clean venv_manager.spec
if errorlevel 1 exit /b 1
for %%F in (setup_venv.bat venv_run.bat venv_launcher.bat venv_requirements.bat venv_gui.bat README.md README.es.md LICENSE THIRD_PARTY_NOTICES.md path_helper.ps1) do copy /y "%%F" "dist\VenvTool\%%F" >nul
if not exist release mkdir release
powershell -NoProfile -Command "Compress-Archive -Path 'dist\VenvTool\*' -DestinationPath 'release\VenvTool-1.3.0-Portable.zip' -Force"
exit /b %errorlevel%
