; Autor: Aldo Machado
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
Name "Venv Tool"
OutFile "release\VenvTool-1.3.0-Setup.exe"
InstallDir "C:\venv-tool\app"
InstallDirRegKey HKLM "Software\VenvTool" "InstallDir"
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
 File /r "dist\VenvTool\*"
 WriteRegStr HKLM "Software\VenvTool" "InstallDir" "$INSTDIR"
 WriteUninstaller "$INSTDIR\Uninstall.exe"
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VenvTool" "DisplayName" "Venv Tool"
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VenvTool" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
 WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VenvTool" "DisplayVersion" "1.3.0"
 CreateDirectory "$SMPROGRAMS\Venv Tool"
 CreateShortcut "$SMPROGRAMS\Venv Tool\Venv Tool.lnk" "$INSTDIR\VenvTool.exe"
 CreateShortcut "$SMPROGRAMS\Venv Tool\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
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
 Delete "$INSTDIR\VenvTool.exe"
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
 Delete "$SMPROGRAMS\Venv Tool\Venv Tool.lnk"
 Delete "$SMPROGRAMS\Venv Tool\Desinstalar.lnk"
 RMDir "$SMPROGRAMS\Venv Tool"
 RMDir "$INSTDIR"
 DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VenvTool"
 DeleteRegKey HKLM "Software\VenvTool"
SectionEnd
