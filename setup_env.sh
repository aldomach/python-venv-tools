#!/usr/bin/env bash

echo "============================================"
echo "  Configurando entorno virtual"
echo "============================================"

# Cambia al directorio donde está este script
cd "$(dirname "$0")" || exit 1

# Verifica que exista requirements.txt
if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] No se encontró requirements.txt en esta carpeta."
    exit 1
fi

# Crea el entorno virtual si no existe
if [ ! -f ".venv/bin/activate" ]; then
    echo "Creando entorno virtual ".venv"..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] No se pudo crear el entorno virtual."
        echo "Verificá que Python 3 y el módulo venv estén instalados y disponibles."
        exit 1
    fi
else
    echo "El entorno virtual ".venv" ya existe, se omite la creación."
fi

echo "Activando entorno virtual..."
source .venv/bin/activate

echo "Actualizando pip..."
python -m pip install --upgrade pip

echo "Instalando dependencias desde requirements.txt..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Falló la instalación de dependencias."
    exit 1
fi

echo "============================================"
echo "  Entorno configurado correctamente"
echo "============================================"
