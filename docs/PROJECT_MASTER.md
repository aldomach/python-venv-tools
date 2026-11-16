# Documento maestro — Python Venv Tools

## Objetivo
Administrar proyectos Python en Windows y Linux sin sincronizar entornos, caché ni configuración particular por Dropbox. Mantener comandos globales, GUI y lanzadores independientes.

## Decisiones permanentes
- Windows: gestor C:\Programs\venv-tools, entornos C:\venvs, caché C:\venvs\pycache. Linux: XDG. Entorno local opcional (venv/.venv).
- Registro por ruta de proyecto y equipo; no compartir entornos accidentalmente.
- requirements.txt opcional, actualizaciones explícitas, sin borrados automáticos.
- Tkinter, núcleo Python y CLI común; uv opcional para resolución de requirements.
- PyInstaller onedir y NSIS; prioridad velocidad y facilidad de instalación.
- Mantener implementaciones propias y revisar las licencias de cualquier código reutilizado.

## Estado
1.2 incorpora gestión de requirements, escáner estático, uv parcial y compilación preparada. Las siguientes versiones están en ROADMAP.md. La validación Windows sigue pendiente. Los detalles de operación están en README.md.
