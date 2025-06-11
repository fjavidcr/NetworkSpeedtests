#!/bin/bash
# Script para preparar el entorno del proyecto NetworkSpeedtests
set -e

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual Python..."
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
if [ -f requirements.txt ]; then
    echo "Instalando dependencias de Python..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "No se encontró requirements.txt"
fi

echo "Entorno preparado. Ya puedes ejecutar ./NetworkSpeedtest.sh"
