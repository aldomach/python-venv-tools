# Python Venv Tools

Scripts reutilizables para crear entornos virtuales y ejecutar proyectos Python sin sincronizar dependencias ni archivos de caché con Dropbox.

## Archivos

| Archivo | Función |
|---|---|
| `setup_venv.bat` / `setup_venv.sh` | Crea el entorno, actualiza pip, instala `requirements.txt` y verifica dependencias. |
| `run.bat` / `run.sh` | Ejecuta el proyecto sin instalar ni actualizar paquetes. |
| `venv_manager.py` | Motor común de los cuatro scripts. Debe permanecer junto a ellos. |
| `README.md` | Documentación. |

Copiar los cinco archivos ejecutables/de código a la raíz de cada proyecto, junto a `requirements.txt` y `main.py`. Los scripts trabajan desde su propia carpeta, independientemente del directorio desde el que se invocan. No necesitan dependencias externas al Python base (3.8 o posterior). Para aplicaciones modernas se recomienda Python 3.11 o superior según sus requisitos.

## Ubicaciones predeterminadas

| Recurso | Windows | Linux |
|---|---|---|
| Entorno externo | `C:\venvs\<proyecto>\venv` | `~/.local/share/venvs/<proyecto>/venv` |
| Entorno local | `venv/` | `.venv/` |
| Caché externa | `C:\venvs\pycache\<proyecto>\<id>\<version>` | `~/.cache/python/<proyecto>/<id>/<version>` |
| Configuración | `%LOCALAPPDATA%\python-venv-tools` | `~/.config/python-venv-tools` |

En Linux se respetan `XDG_DATA_HOME`, `XDG_CACHE_HOME` y `XDG_CONFIG_HOME` cuando son rutas absolutas. `<id>` identifica la ruta absoluta del proyecto y evita mezclar cachés de proyectos homónimos. `<version>` es `default` o la selección numérica de Python. En Windows, si no hay permiso de escritura en `C:\venvs`, usar `--path` y `--cache-path` con rutas propias. No es necesario ejecutar como administrador.

## Inicio rápido

### Windows (CMD)

```cmd
setup_venv.bat
run.bat
```

### Linux

Instalar previamente Python y su módulo venv (en Debian/Ubuntu, `sudo apt install python3 python3-venv`).

```bash
chmod +x setup_venv.sh run.sh
./setup_venv.sh
./run.sh
```

En Windows se utiliza `py -3` si está disponible, o `python` como alternativa. En Linux se usa `python3` del PATH. Los scripts requieren que ese intérprete de arranque siga disponible, incluso si el entorno fue creado con otra versión.

## Parámetros

| Opción | Setup | Run | Descripción |
|---|:---:|:---:|---|
| `--name NOMBRE` | Sí | Sí | Nombre del proyecto; inicialmente el de la carpeta de los scripts. |
| `--path RUTA` | Sí | Sí | Base externa; se agrega `NOMBRE/venv`. No afecta al entorno local. |
| `--local` | Sí | Sí | Selecciona el entorno local. |
| `--external` | Sí | Sí | Selecciona el entorno externo. Predeterminado inicial. |
| `--python VERSION_O_RUTA` | Sí | Sí | Setup selecciona el intérprete; run verifica la versión si se solicita explícitamente. |
| `--cache-path RUTA` | Sí | Sí | Cambia la base de la caché externa. |
| `--no-cache` | Sí | Sí | Evita que Python escriba archivos `.pyc` durante la ejecución normal. |
| `--cache` | Sí | Sí | Restablece la escritura de caché externa. |
| `--verbose` | Sí | Sí | Muestra rutas y configuración. |
| `--help` | Sí | Sí | Ayuda de argumentos. |
| `--entry ARCHIVO` | No | Sí | Ejecuta otro archivo en lugar de `main.py`. |
| `--check` | No | Sí | Verifica aislamiento y ejecuta `pip check` antes de iniciar. |
| `-- ARGUMENTOS` | No | Sí | Pasa los argumentos restantes al programa. |

Las opciones de setup se guardan **solo si la instalación y las verificaciones terminan correctamente**. Run reutiliza esa configuración, pero sus cambios de parámetros son temporales. Una nueva ejecución de setup sin parámetros conserva las preferencias guardadas. Para volver a un entorno externo, especificar `--external`. Para restaurar nombre o rutas, especificarlos explícitamente. Las rutas relativas se interpretan desde la raíz del proyecto.

## Ejemplos

### Windows (CMD)

```cmd
setup_venv.bat --local
setup_venv.bat --external --name facturas --path "D:\Python Envs" --python 3.11
setup_venv.bat --cache-path "%LOCALAPPDATA%\PythonCache"
run.bat
run.bat --verbose --check
run.bat --entry herramienta.py -- --archivo "Mi archivo.pdf"
run.bat --no-cache
```

### Linux

```bash
./setup_venv.sh --local
./setup_venv.sh --external --name facturas --path "$HOME/venvs" --python 3.11
./setup_venv.sh --cache-path "$HOME/.cache/mis-proyectos"
./run.sh
./run.sh --verbose --check
./run.sh --entry herramienta.py -- --archivo "Mi archivo.pdf"
./run.sh --no-cache
```

Para una instalación de Python específica se puede pasar la ruta de su ejecutable mediante `--python`. No se instala Python automáticamente. Si el entorno ya existe con otra versión, se detiene sin sobrescribirlo.

## Caché y Dropbox

Se utiliza `PYTHONPYCACHEPREFIX` (Python 3.8+) para redirigir los archivos de bytecode de los imports fuera del proyecto. La primera ejecución puede generar caché y las siguientes reutilizarla. `--no-cache` añade `PYTHONDONTWRITEBYTECODE=1`; no borra la caché previa. Pip instala con `--no-compile` para evitar precompilación innecesaria. Herramientas que compilen explícitamente o generen su propia caché pueden ignorar estas variables. No se eliminan archivos existentes ni se controlan las cachés de editores o bibliotecas ajenas a Python.

El entorno local también contiene muchos archivos, por lo que no se recomienda dentro de Dropbox. Los entornos virtuales no son portables entre equipos ni entre Windows y Linux. Si se usa Git, conviene ignorar `venv/`, `.venv/`, `__pycache__/` y `*.pyc`; `.gitignore` no impide que Dropbox sincronice archivos.

## Seguridad y mantenimiento

- Se ejecuta el Python del entorno directamente, sin activar el entorno en la consola. Run prepara `PATH` y `VIRTUAL_ENV` únicamente para el proceso hijo.
- Setup comprueba el prefijo de Python, el aislamiento de paquetes de usuario/sistema y la ubicación de pip; instala con `--require-virtualenv` y ejecuta `pip check`.
- Se excluyen variables de entorno `PYTHON*` y `PIP_*` heredadas para evitar contaminación; se usan las variables propias de caché y aislamiento. Setup deshabilita configuraciones habituales de pip; si se requiere un índice privado, certificados o proxy configurados mediante pip, habrá que adaptar la configuración conscientemente. No es un mecanismo de seguridad para ejecutar proyectos no confiables.
- Se utiliza un identificador de propietario dentro de los entornos. Si dos proyectos de carpetas diferentes comparten nombre, usar `--name` o `--path` distintos. No se adoptan automáticamente entornos externos antiguos sin identificador; se recomienda utilizar otro nombre o mover el entorno anterior manualmente tras comprobar que no se usa. Los entornos locales existentes sí se pueden adoptar tras validar su aislamiento.
- Si falla la creación y queda una carpeta incompleta, no se elimina automáticamente. Moverla o elegir otra ubicación antes de reintentar.
- `run` no accede a Internet ni ejecuta pip en condiciones normales. El motor común añade un inicio breve de Python; la aplicación puede realizar sus propias operaciones. No se necesita dejar una consola activada. Los códigos de salida se conservan durante la ejecución normal.
- No se incluye una pausa al cerrar: ejecutar desde CMD/terminal para ver los errores. En Windows, un `.bat` invocado con doble clic puede cerrar su ventana al terminar.
- No ejecutar dos instalaciones simultáneas sobre el mismo entorno.

## Verificaciones

```cmd
run.bat --check --verbose
```

```bash
./run.sh --check --verbose
```

La comprobación verifica dependencias declaradas, no garantiza que todas las funciones de la aplicación o sus DLL funcionen. Si se cambia de equipo o se mueve el proyecto, ejecutar setup de nuevo con una ubicación apropiada.
