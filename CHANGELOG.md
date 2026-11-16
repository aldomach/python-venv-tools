# Changelog

## 1.2.2

- Separate requirements editing, source scanning and environment operations into tabs.
- Never save requirements implicitly during install/update; require an explicit save or reload.
- Preserve the previous file in a machine-local backup before atomic replacement; confirm empty writes and reject external changes.
- Show scan and comparison results as tables; preserve existing specifications and avoid duplicate package suggestions.
- Add read-only environment verification and prevent lock exports from overwriting existing files.

## 1.2.1
- Rename to Python Venv Tools; add English README and repository metadata.
- Preserve project settings and environment locations.
- Reconstruct release history from original archives.

## 1.2
- Editor de requirements con creación, guardado, apertura externa y recarga.
- Escaneo AST con candidatos revisables, comparación, instalación/actualización y freeze.
- Motor uv opcional para requirements.
- Configuración de PyInstaller, icono, información de versión y build NSIS/portable.
- Documentación permanente y plan de evolución.
- Mantiene registros y entornos de 1.1.

## 1.1
- requirements opcional, flags de creación limpia, nueva ruta de instalación y firma.
