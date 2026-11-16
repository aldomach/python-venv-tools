; Autor: Aldo Machado
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
Name "Python Venv Manager"
OutFile "PythonVenvManager-Setup.exe"
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
 File "venv_manager.py"
 File "venv_gui.py"
 File "setup_venv.bat"
 File "venv_run.bat"
 File "venv_launcher.bat"
 File "venv_gui.bat"
 File "README.md"
 File "path_helper.ps1"
 WriteRegStr HKLM "Software\PythonVenvManager" "InstallDir" "$INSTDIR"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PythonVenvManager" "DisplayName" "Python Venv Manager"
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PythonVenvManager" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PythonVenvManager" "DisplayVersion" "1.1.0"
 CreateDirectory "$SMPROGRAMS\Python Venv Manager"
 CreateShortcut "$SMPROGRAMS\Python Venv Manager\Python Venv Manager.lnk" "$INSTDIR\venv_gui.bat"
 CreateShortcut "$SMPROGRAMS\Python Venv Manager\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
 ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\path_helper.ps1" -Action Add -Directory "$INSTDIR"' $0
 ${If} $0 != 0
 MessageBox MB_ICONEXCLAMATION "No se pudo actualizar PATH. Agregue manualmente $INSTDIR al PATH del sistema."
 ${EndIf}
 MessageBox MB_OK "Se requiere Python 3.8 o posterior instalado (con Tkinter para la interfaz). Abra una terminal nueva para usar los comandos."
SectionEnd
Section "Uninstall"
 SetShellVarContext all
 ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\path_helper.ps1" -Action Remove -Directory "$INSTDIR"' $0
 ${If} $0 != 0
 MessageBox MB_ICONEXCLAMATION "No se pudo quitar la entrada de PATH. Puede quitarla manualmente."
 ${EndIf}
 Delete "$INSTDIR\venv_manager.py"
 Delete "$INSTDIR\venv_gui.py"
 Delete "$INSTDIR\setup_venv.bat"
 Delete "$INSTDIR\venv_run.bat"
 Delete "$INSTDIR\venv_launcher.bat"
 Delete "$INSTDIR\venv_gui.bat"
 Delete "$INSTDIR\README.md"
 Delete "$INSTDIR\path_helper.ps1"
 Delete "$INSTDIR\Uninstall.exe"
 Delete "$SMPROGRAMS\Python Venv Manager\Python Venv Manager.lnk"
 Delete "$SMPROGRAMS\Python Venv Manager\Desinstalar.lnk"
 RMDir "$SMPROGRAMS\Python Venv Manager"
 RMDir "$INSTDIR"
 DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PythonVenvManager"
 DeleteRegKey HKLM "Software\PythonVenvManager"
SectionEnd
