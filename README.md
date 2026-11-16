# Python Venv Manager 1.0

Administrador centralizado de entornos virtuales Python para Windows y Linux. Interfaz gráfica Tkinter y comandos de consola. No requiere paquetes de terceros para funcionar.

## Instalación en Windows

Requisitos: Windows 10/11, Python 3.8 o posterior instalado (se recomienda 3.11+), con el launcher `py` o `python` disponible y Tcl/Tk para la interfaz gráfica. El instalador no instala Python ni necesita NSIS en las computadoras de destino.

1. En la PC que tiene NSIS instalado, descomprimir el paquete completo.
2. Ejecutar `build_installer.bat`. También se puede abrir `installer.nsi` con MakeNSISW y compilar.
3. El resultado esperado es `PythonVenvManager-Setup.exe`, junto a los fuentes.
4. Ejecutar ese EXE en la PC de destino. Por defecto se instala en `%LOCALAPPDATA%\Programs\PythonVenvManager`, agrega esa carpeta al PATH del usuario y crea accesos en el menú Inicio. No requiere permisos de administrador para instalar el gestor.
5. Abrir una consola nueva. Ejecutar `venv_gui` o abrir Python Venv Manager desde Inicio.

La ruta predeterminada de entornos es `C:\venvs`, que en algunas PCs requiere que un administrador cree la carpeta y conceda permisos de escritura al usuario. Alternativamente usar `--path "%LOCALAPPDATA%\venvs"`. El gestor nunca eleva permisos automáticamente. La caché por defecto sigue siendo `C:\venvs\pycache`; seleccionar `--cache-path "%LOCALAPPDATA%\venvs\pycache"` si no hay permiso.

**Estado del instalador:** se entregan el fuente NSIS y el compilador BAT; el EXE no está incluido porque NSIS no está disponible en el entorno de desarrollo. La compilación y ejecución nativa de Windows deben verificarse en Windows. El instalador no está firmado.

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

`setup_venv` requiere requirements.txt, crea el entorno si falta, comprueba su aislamiento, actualiza pip, instala dependencias y ejecuta pip check. No actualiza automáticamente todas las dependencias existentes: pip conserva las versiones compatibles con requirements.txt.

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
| `--verbose` | Muestra rutas y configuración. |
| `--entry archivo.py` | Entrada alternativa (run/launcher). |
| `--check` | Verifica aislamiento y paquetes antes de ejecutar (run). |
| `--help` | Ayuda. |
| `-- argumentos` | Argumentos para la aplicación (run). |

Ejemplos:

```cmd
setup_venv --local --python 3.11
setup_venv --external --name facturas --path D:\venvs
venv_run --entry main.py -- --debug
venv_launcher --entry main.py
```

La configuración exitosa de setup queda guardada por ruta absoluta del proyecto y por equipo, fuera de Dropbox. Si se mueve el proyecto, se debe reconfigurar o usar un nombre externo diferente. Las opciones de run son temporales. No comparte entornos entre proyectos con rutas diferentes; los entornos externos previos sin marca de propietario se rechazan para evitar su modificación accidental. No se borran entornos automáticamente.

## Lanzador autónomo

`venv_launcher` genera `run_project.bat` o `run_project.sh` en el proyecto. No requiere gestor, PATH global ni activación manual; llama directamente al intérprete y redirige la caché. Si existe un lanzador del mismo nombre, lo conserva y avisa. Renombrarlo antes de regenerar. Las rutas absolutas son específicas del equipo; no sincronizar el mismo lanzador entre equipos con configuraciones diferentes. El archivo recibe argumentos de la aplicación directamente.

## Interfaz gráfica

Ejecutar `venv_gui` o `python venv_gui.py`. Seleccionar la raíz del proyecto, completar las opciones y usar Crear / instalar. La lista incluye los proyectos registrados por setup. Permite configurar ubicación, nombre, intérprete, caché y entrada; crear entorno, ejecutar, verificar y ejecutar, generar lanzador, consultar Python, gestionar paquetes (listar, instalar, actualizar uno, desinstalar con confirmación), comprobar dependencias, exportar pip freeze y abrir la carpeta del entorno. Las operaciones que pueden tardar muestran salida en un registro y se realizan en un hilo de trabajo. En Linux el botón detectar Python muestra la versión del intérprete del gestor; no enumera todas las instalaciones. En Windows usa `py -0p`.

Primera versión: no incluye borrado de entornos, limpieza de caché, terminal activada, medición de espacio, importación/exportación de configuración ni registro automático de entornos ajenos. Se priorizó evitar cambios destructivos. El gestor no genera automáticamente requirements.txt de dependencias directas: pip freeze exporta todas las versiones a un archivo elegido por el usuario.

## Ubicaciones

| Recurso | Windows | Linux |
|---|---|---|
| Base entornos | C:\venvs | ~/.local/share/venvs |
| Entorno externo | base/nombre/venv | base/nombre/venv |
| Entorno local | venv | .venv |
| Base caché | C:\venvs\pycache | ~/.cache/python |
| Configuración | %LOCALAPPDATA%\python-venv-tools | ~/.config/python-venv-tools |

Linux respeta XDG_DATA_HOME, XDG_CONFIG_HOME y XDG_CACHE_HOME si son rutas absolutas. La caché incluye nombre, identificador del proyecto y versión seleccionada (o default). Python agrega su propia etiqueta de versión a los archivos pyc. Se desactiva la compilación de paquetes durante pip install y se usa PYTHONPYCACHEPREFIX en ejecución. Esto evita nuevos __pycache__ en el código, no elimina los existentes ni garantiza que bibliotecas externas no escriban otros archivos. Si se elige entorno local, Dropbox podría sincronizar sus miles de archivos; se recomienda entorno externo.

## Desinstalación

Windows: desde Aplicaciones instaladas o el menú Inicio. Elimina el gestor y su entrada PATH, pero conserva entornos, proyectos y configuración. Los lanzadores autónomos siguen funcionando si el entorno existe. Linux: quitar los enlaces de los cuatro comandos de ~/.local/bin y la carpeta instalada del gestor, después de comprobar que pertenecen a esta herramienta; conservar los entornos y configuración.

## Seguridad y verificación

No se instala nada fuera del entorno virtual mediante pip. Se omite configuración global de pip y variables Python/PIP heredadas para evitar contaminación; esto puede requerir configuración adicional en redes con repositorios privados. Los entornos no son una zona de seguridad: ejecutar solo código y paquetes confiables. No ejecutar simultáneamente varias operaciones de instalación sobre el mismo entorno. El gestor no valida el código de la aplicación.

Pruebas en Linux: sintaxis Python y Bash, generación de lanzador, configuración persistente y ejecución con un entorno aislado de prueba. Interfaz gráfica y Windows requieren validación nativa. El instalador NSIS no se pudo compilar aquí.
