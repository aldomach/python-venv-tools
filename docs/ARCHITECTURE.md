# Arquitectura

GUI y wrappers CLI llaman venv_manager.py (o venv_cli.exe). dependencies.py implementa análisis AST y código de consulta para el intérprete destino. El núcleo conserva los registros JSON y marcas de propietario de 1.1; agrega la propiedad engine (por defecto pip). El entorno validado se usa por ruta absoluta, sin activar una shell. La caché se redirige mediante PYTHONPYCACHEPREFIX. Los lanzadores autónomos no dependen del gestor.

Motores: Python venv y pip para crear y validar; pip o uv para instalar requirements. El gestor congelado no utiliza sys.executable como intérprete del proyecto: usa py -3 o python en PATH, o el intérprete explícito. La GUI congelada llama al CLI hermano. PyInstaller empaqueta ambos ejecutables en una carpeta; NSIS copia esta distribución.

Evolución: separar registro, motores, paquetes, escaneo y tareas en módulos si aumenta el alcance. No migrar automáticamente los entornos a otro motor ni alterar proyectos existentes.
