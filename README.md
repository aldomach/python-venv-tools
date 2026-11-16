# Python Venv Manager 1.2

Administrador centralizado de entornos virtuales Python para Windows y Linux. Interfaz gráfica Tkinter y comandos de consola. No requiere paquetes de terceros para funcionar.

## Instalación en Windows

La distribución compilada incorpora el runtime del gestor. Para crear entornos se necesita Python instalado (3.8+; recomendado 3.11+). El equipo de compilación necesita Python con Tkinter, NSIS y acceso a PyPI.

1. Descomprimir el código fuente en una carpeta de Windows.
2. Ejecutar `build_all.bat` (compila PyInstaller y NSIS).
3. Se generan `release\PythonVenvManager-1.2-Setup.exe` y `release\PythonVenvManager-1.2-Portable.zip`.
4. Instalar el EXE; por defecto usa `C:\Programs\venv-tools`, PATH del sistema y menú Inicio. Requiere UAC.
5. Abrir una consola nueva y ejecutar `venv_gui`.

Para usar el código sin compilar: ejecutar `venv_gui.bat` o `python venv_gui.py`. Ver `docs/BUILD_WINDOWS.md`. No se incluyen binarios precompilados.

La ruta predeterminada de entornos es `C:\venvs`, que en algunas PCs requiere que un administrador cree la carpeta y conceda permisos de escritura al usuario. Alternativamente usar `--path "%LOCALAPPDATA%\venvs"`. El gestor nunca eleva permisos automáticamente. La caché por defecto sigue siendo `C:\venvs\pycache`; seleccionar `--cache-path "%LOCALAPPDATA%\venvs\pycache"` si no hay permiso.

**Estado del instalador:** se entregan los fuentes, configuración de PyInstaller y archivos BAT; el EXE debe compilarse en Windows. La compilación y ejecución nativa de Windows deben verificarse en Windows. El instalador no está firmado.

## Instalación en Linux

Instalar Python 3, el módulo venv y Tkinter (en Debian/Ubuntu: `sudo apt install python3 python3-venv python3-tk`). Desde la carpeta descomprimida:

```bash
bash install.sh
```

Instala en `~/.local/share/python-venv-tools` (o XDG_DATA_HOME), con comandos en `~/.local/bin`. Verificar que esta última carpeta esté en PATH. No requiere sudo para instalar el gestor.

## Uso centralizado

Ejecutar los comandos **desde la raíz del proyecto**, no desde la carpeta del gestor.

```cmd
cd /d "C:\Users\usuario\Dropbox\mi_proyecto"
setup_venv --python 3.11
venv_run
venv_launcher
```

En Linux se usan los mismos nombres sin extensión. Los scripts `run.bat` y `run.sh` se incluyen para uso manual, pero no se instalan en PATH: se prefiere `venv_run` para evitar colisiones con otros comandos o un run.bat antiguo.

`setup_venv` crea el entorno si falta, comprueba su aislamiento, actualiza pip por defecto, instala dependencias si existe `requirements.txt` y ejecuta pip check. Si no existe el archivo, informa mediante una advertencia y continúa. Para crear un entorno sin instalar dependencias ni actualizar pip (sin descargas por parte del gestor), usar `setup_venv --no-requirements --no-upgrade-pip`. Estas opciones afectan solamente a esa operación; no eliminan paquetes de un entorno existente. No actualiza automáticamente todas las dependencias existentes: pip conserva las versiones compatibles con requirements.txt.

`venv_run` localiza la configuración del proyecto, prepara la caché y ejecuta main.py. No instala paquetes ni accede a Internet por sí mismo. `--check` agrega validaciones.

### Opciones

| Opción | Uso |
|---|---|
| `--name NOMBRE` | Nombre del proyecto, por defecto la carpeta actual. |
| `--path RUTA` | Base externa de entornos. |
| `--local` / `--external` | Entorno local (venv en Windows, .venv en Linux) o externo. |
| `--python 3.11` | Versión o ruta del intérprete. En run verifica la versión si se especifica. |
| `--cache-path RUTA` | Base de caché externa. |
| `--no-cache` / `--cache` | Desactiva o reactiva escritura de bytecode. |
| `--no-requirements` | Omite requirements.txt aunque exista (setup). |
| `--no-upgrade-pip` | Omite la actualización de pip (setup). |
| `--verbose` | Muestra rutas y configuración. |
| `--entry archivo.py` | Entrada alternativa (run/launcher). |
| `--check` | Verifica aislamiento y paquetes antes de ejecutar (run). |
| `--help` | Ayuda. |
| `-- argumentos` | Argumentos para la aplicación (run). |

Ejemplos:

```cmd
setup_venv
setup_venv --no-requirements --no-upgrade-pip
setup_venv --local --python 3.11
setup_venv --external --name facturas --path D:\venvs
venv_run --entry main.py -- --debug
venv_launcher --entry main.py
```

La configuración exitosa de setup queda guardada por ruta absoluta del proyecto y por equipo, fuera de Dropbox. Si se mueve el proyecto, se debe reconfigurar o usar un nombre externo diferente. Las opciones de run son temporales. No comparte entornos entre proyectos con rutas diferentes; los entornos externos previos sin marca de propietario se rechazan para evitar su modificación accidental. No se borran entornos automáticamente.

## Lanzador autónomo

`venv_launcher` genera `run_project.bat` o `run_project.sh` en el proyecto. No requiere gestor, PATH global ni activación manual; llama directamente al intérprete y redirige la caché. Si existe un lanzador del mismo nombre, lo conserva y avisa. Renombrarlo antes de regenerar. Las rutas absolutas son específicas del equipo; no sincronizar el mismo lanzador entre equipos con configuraciones diferentes. El archivo recibe argumentos de la aplicación directamente.

## Interfaz gráfica

Ejecutar `venv_gui` o `python venv_gui.py`. Seleccionar la raíz del proyecto, completar las opciones y usar Crear / instalar. Las casillas «Instalar requirements.txt si existe» y «Actualizar pip» están marcadas inicialmente; se pueden desmarcar para una creación limpia sin descargas. La lista incluye los proyectos registrados por setup. Permite configurar ubicación, nombre, intérprete, caché y entrada; crear entorno, ejecutar, verificar y ejecutar, generar lanzador, consultar Python, gestionar paquetes (listar, instalar, actualizar uno, desinstalar con confirmación), comprobar dependencias, exportar pip freeze y abrir la carpeta del entorno. Las operaciones que pueden tardar muestran salida en un registro y se realizan en un hilo de trabajo. En Linux el botón detectar Python muestra la versión del intérprete del gestor; no enumera todas las instalaciones. En Windows usa `py -0p`.

Limitaciones actuales: no incluye borrado de entornos, limpieza de caché, terminal activada, medición de espacio, importación/exportación de configuración ni registro automático de entornos ajenos. Se priorizó evitar cambios destructivos. El escáner propone dependencias directas, sujetas a revisión; pip freeze exporta las versiones instaladas.

## Ubicaciones

| Recurso | Windows | Linux |
|---|---|---|
| Gestor | C:\Programs\venv-tools | ~/.local/share/python-venv-tools |
| Base entornos | C:\venvs | ~/.local/share/venvs |
| Entorno externo | base/nombre/venv | base/nombre/venv |
| Entorno local | venv | .venv |
| Base caché | C:\venvs\pycache | ~/.cache/python |
| Configuración | %LOCALAPPDATA%\python-venv-tools | ~/.config/python-venv-tools |

Linux respeta XDG_DATA_HOME, XDG_CONFIG_HOME y XDG_CACHE_HOME si son rutas absolutas. La caché incluye nombre, identificador del proyecto y versión seleccionada (o default). Python agrega su propia etiqueta de versión a los archivos pyc. Se desactiva la compilación de paquetes durante pip install y se usa PYTHONPYCACHEPREFIX en ejecución. Esto evita nuevos __pycache__ en el código, no elimina los existentes ni garantiza que bibliotecas externas no escriban otros archivos. Si se elige entorno local, Dropbox podría sincronizar sus miles de archivos; se recomienda entorno externo.

## Desinstalación

Windows: desde Aplicaciones instaladas o el menú Inicio. Requiere permisos de administrador. Elimina el gestor y su entrada PATH del sistema, pero conserva entornos, proyectos y configuración. Los lanzadores autónomos siguen funcionando si el entorno existe. Linux: quitar los enlaces de los cinco comandos de ~/.local/bin y la carpeta instalada del gestor, después de comprobar que pertenecen a esta herramienta; conservar los entornos y configuración.

## Seguridad y verificación

Las operaciones de paquetes del gestor se dirigen al entorno virtual validado. Se omite configuración global de pip y variables Python/PIP heredadas para evitar contaminación; esto puede requerir configuración adicional en redes con repositorios privados. Los entornos no son una zona de seguridad: ejecutar solo código y paquetes confiables. No ejecutar simultáneamente varias operaciones de instalación sobre el mismo entorno. El gestor no valida el código de la aplicación.

Pruebas y limitaciones: ver `docs/TESTING.md`.

## Dependencias (nuevo en 1.2)

En la UI, abrir **Dependencias / requirements.txt**. Se puede crear, editar, guardar, recargar y abrir el archivo en el editor externo. Instalar conserva versiones compatibles; Actualizar solicita nuevas versiones dentro de las restricciones. No elimina paquetes adicionales. Comparar analiza el archivo guardado; extras, URLs, includes y opciones complejas requieren revisión. Exportar lock escribe un archivo nuevo. El escáner analiza AST sin ejecutar el proyecto, descarta módulos estándar y locales, y sugiere nombres según metadatos del intérprete y una tabla de alias. Seleccionar las filas deseadas antes de agregarlas al editor; revisar y guardar antes de instalar. No detecta de forma fiable importaciones dinámicas, dependencias opcionales, módulos nativos o nombres ambiguos. No instala automáticamente las sugerencias.

```cmd
venv_requirements --scan
venv_requirements --compare
venv_requirements --install
venv_requirements --upgrade
venv_requirements --freeze --output requirements-lock.txt
```

`--json` está disponible para scan y compare. `--freeze` sin output imprime resultados. Para resolver requirements con uv (debe estar instalado y en PATH):

```cmd
setup_venv --engine uv
venv_requirements --upgrade
```

El motor queda guardado al completar setup. `--engine pip` permite volver al motor clásico. Por diseño, venv y pip siguen siendo responsables de la creación, validación y operaciones individuales de paquetes de la UI; uv se usa para instalar/actualizar requirements. No se descarga uv automáticamente. Las opciones de requirements no guardan cambios de configuración. No usar motores simultáneamente sobre el mismo entorno.

Documentación: [proyecto maestro](docs/PROJECT_MASTER.md), [arquitectura](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md), [funciones](docs/FEATURES.md), [compilación](docs/BUILD_WINDOWS.md), [pruebas](docs/TESTING.md).

---

Autor: Aldo Machado.
