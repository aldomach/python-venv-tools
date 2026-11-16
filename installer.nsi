; Autor: Aldo Machado
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
Name "Python Venv Tools"
OutFile "release\PythonVenvTools-1.2.1-Setup.exe"
InstallDir "C:\Programs\venv-tools"
InstallDirRegKey HKLM "Software\PythonVenvManager" "InstallDir"
RequestExecutionLevel admin
!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Spanish"
Section "Instalar"
 SetShellVarContext all
 SetOutPath "$INSTDIR"
 File /r "dist\VenvTools\*"
 WriteRegStr HKLM "Software\PythonVenvManager" "InstallDir" "$INSTDIR"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PythonVenvManager" "DisplayName" "Python Venv Tools"
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PythonVenvManager" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PythonVenvManager" "DisplayVersion" "1.2.1"
 CreateDirectory "$SMPROGRAMS\Python Venv Tools"
 CreateShortcut "$SMPROGRAMS\Python Venv Tools\Python Venv Tools.lnk" "$INSTDIR\VenvTools.exe"
 CreateShortcut "$SMPROGRAMS\Python Venv Tools\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
 ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\path_helper.ps1" -Action Add -Directory "$INSTDIR"' $0
 ${If} $0 != 0
 MessageBox MB_ICONEXCLAMATION "No se pudo actualizar PATH. Agregue manualmente $INSTDIR al PATH del sistema."
 ${EndIf}
 MessageBox MB_OK "El gestor incluye su propio runtime. Para crear entornos instala Python. Abra una terminal nueva para usar los comandos."
SectionEnd
Section "Uninstall"
 SetShellVarContext all
 ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\path_helper.ps1" -Action Remove -Directory "$INSTDIR"' $0
 ${If} $0 != 0
 MessageBox MB_ICONEXCLAMATION "No se pudo quitar la entrada de PATH. Puede quitarla manualmente."
 ${EndIf}
 Delete "$INSTDIR\VenvTools.exe"
 Delete "$INSTDIR\venv_cli.exe"
 Delete "$INSTDIR\venv_requirements.bat"
 RMDir /r "$INSTDIR\_internal"
 Delete "$INSTDIR\venv_manager.py"
 Delete "$INSTDIR\venv_gui.py"
 Delete "$INSTDIR\setup_venv.bat"
 Delete "$INSTDIR\venv_run.bat"
 Delete "$INSTDIR\venv_launcher.bat"
 Delete "$INSTDIR\venv_gui.bat"
 Delete "$INSTDIR\README.md"
 Delete "$INSTDIR\README.es.md"
 Delete "$INSTDIR\LICENSE"
 Delete "$INSTDIR\THIRD_PARTY_NOTICES.md"
 Delete "$INSTDIR\path_helper.ps1"
 Delete "$INSTDIR\Uninstall.exe"
 Delete "$SMPROGRAMS\Python Venv Tools\Python Venv Tools.lnk"
 Delete "$SMPROGRAMS\Python Venv Tools\Desinstalar.lnk"
 RMDir "$SMPROGRAMS\Python Venv Tools"
 RMDir "$INSTDIR"
 DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PythonVenvManager"
 DeleteRegKey HKLM "Software\PythonVenvManager"
SectionEnd
