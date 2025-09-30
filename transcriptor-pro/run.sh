#!/bin/bash
# Script de inicio para Transcriptor Pro (Linux/Mac)
# Activa el entorno virtual y ejecuta la aplicación

echo "========================================"
echo " Transcriptor Pro v1.0"
echo "========================================"
echo

# Verificar si existe el entorno virtual
if [ ! -d ".venv" ]; then
    echo "ERROR: No se encontró el entorno virtual"
    echo
    echo "Por favor ejecuta primero:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo
    exit 1
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source .venv/bin/activate

# Verificar que FFmpeg está instalado
if ! command -v ffmpeg &> /dev/null; then
    echo
    echo "ADVERTENCIA: FFmpeg no está instalado"
    echo "El procesamiento de audio no funcionará correctamente"
    echo
    echo "Instala FFmpeg con:"
    echo "  Mac: brew install ffmpeg"
    echo "  Linux: sudo apt install ffmpeg"
    echo
    read -p "Presiona Enter para continuar de todas formas..."
fi

# Ejecutar la aplicación
echo "Iniciando Transcriptor Pro..."
echo
python -m src.main

# Capturar código de salida
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo
    echo "ERROR: La aplicación terminó con errores (código: $EXIT_CODE)"
    read -p "Presiona Enter para salir..."
fi

exit $EXIT_CODE
