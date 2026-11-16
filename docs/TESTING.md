# Pruebas 1.2

Realizadas en Linux con directorios XDG temporales y un proyecto con espacios:
- Creación limpia con pip sin actualización ni requirements; pip check correcto.
- Escaneo JSON: PIL → Pillow, yaml → PyYAML, exclusión de os y local.py.
- Comparación: pip compatible y un paquete ficticio faltante.
- Exportación freeze a nuevo archivo.
- Instalación de requirements vacío mediante pip y uv, sin descarga; pip check correcto.
- Generación y ejecución del lanzador SH y run normal.
- Apertura de ventana principal y diálogo de dependencias con Xvfb.

No comprobados: descarga real de paquetes, actualizaciones de red, instalación de uv, UI interactiva completa, compilación PyInstaller/NSIS, PATH y ejecución nativa de Windows. El escaneo es heurístico; los requisitos complejos no se resuelven mediante compare. No se verifican versiones mínimas de dependencias detectadas automáticamente.
