#!/usr/bin/env bash

# Cambia al directorio donde está este script
cd "$(dirname "$0")" || exit 1

# Verifica que exista el entorno virtual
if [ ! -f ".venv/bin/activate" ]; then
    echo "[ERROR] No se encontró el entorno virtual ".venv"."
    echo "Ejecutá primero setup_env.sh para crearlo."
    exit 1
fi

# Verifica que exista main.py
if [ ! -f "main.py" ]; then
    echo "[ERROR] No se encontró main.py en esta carpeta."
    exit 1
fi

echo "Activando entorno virtual..."
source .venv/bin/activate

echo "Ejecutando main.py..."
python main.py

echo
echo "============================================"
echo "  Programa finalizado"
echo "============================================"
