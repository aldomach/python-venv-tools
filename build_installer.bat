@echo off
setlocal
cd /d "%~dp0"
if not exist "dist\VenvTool\VenvTool.exe" (
 echo Ejecuta build_exe.bat primero.
 exit /b 1
)
if not exist release mkdir release
where makensis.exe >nul 2>&1
if not errorlevel 1 goto pathbuild
if exist "%ProgramFiles(x86)%\NSIS\makensis.exe" goto x86
if exist "%ProgramFiles%\NSIS\makensis.exe" goto x64
echo NSIS no encontrado. Instala NSIS o agrega makensis al PATH.
exit /b 1
:pathbuild
makensis.exe installer.nsi
exit /b %errorlevel%
:x86
"%ProgramFiles(x86)%\NSIS\makensis.exe" installer.nsi
exit /b %errorlevel%
:x64
"%ProgramFiles%\NSIS\makensis.exe" installer.nsi
exit /b %errorlevel%
