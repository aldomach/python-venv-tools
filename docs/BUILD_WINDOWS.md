# Compilación Windows

En Windows, instalar Python con launcher py, pip y Tcl/Tk, y NSIS. Abrir CMD en la raíz de los fuentes y ejecutar `build_all.bat`. El build usa un entorno exclusivo en `%LOCALAPPDATA%\python-venv-tools-build\venv`. Instala PyInstaller allí. `build_exe.bat` genera `dist\VenvManager` y el ZIP portable; `build_installer.bat` requiere ese resultado y busca makensis en PATH o Program Files. El instalador se escribe en release. Se recomienda compilar con Python x64 para equipos Windows x64. No es una compilación cruzada, no está firmada, y requiere comprobar el resultado en Windows.

Prueba de aceptación: abrir la GUI del portable sin Python en PATH; comprobar que informa si no encuentra intérprete; instalar Python; instalar el gestor con NSIS; abrir una nueva CMD; crear entorno limpio; comprobar que usa C:\venvs; probar scan, compare y launcher. Desinstalar y confirmar que el proyecto, el entorno y los registros permanecen. En C:\venvs puede ser necesario otorgar permisos al usuario.

El gestor compilado incorpora Python/Tcl/Tk y dependencias de PyInstaller. Antes de redistribuir públicamente los binarios, incluir y revisar las licencias correspondientes.
