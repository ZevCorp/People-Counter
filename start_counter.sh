#!/bin/bash

# Script de inicio para el Sistema de Conteo de Personas
# Usar con diferentes tipos de entrada (Consistente con entorno Hailo)

echo "🤖 Sistema de Conteo de Personas - Hailo AI"
echo "=========================================="

# Verificar que el entorno esté configurado
if [ ! -f "setup_env.sh" ]; then
    echo "❌ Error: setup_env.sh no encontrado"
    echo "Asegúrate de estar en el directorio correcto del proyecto Hailo"
    exit 1
fi

echo "⚙️  Configurando entorno virtual Hailo (venv_hailo_rpi_examples)..."
source setup_env.sh

# Verificar que el entorno virtual esté activo
if [[ "$VIRTUAL_ENV" != *"venv_hailo_rpi_examples"* ]]; then
    echo "❌ Error: El entorno virtual venv_hailo_rpi_examples no está activo"
    echo "Por favor ejecuta: source setup_env.sh"
    exit 1
fi

echo "✅ Entorno virtual Hailo activado: $VIRTUAL_ENV"

echo "📦 Instalando dependencias adicionales en venv_hailo_rpi_examples..."
pip install -r requirements_counter.txt

echo ""
echo "Opciones disponibles:"
echo "1) Cámara Raspberry Pi"  
echo "2) Cámara USB"
echo "3) RTSP Stream"
echo "4) Archivo de video"
echo "5) Solo dashboard web"

read -p "Selecciona una opción (1-5): " choice

case $choice in
    1)
        echo "🔄 Iniciando con cámara Raspberry Pi..."
        python3 people_counter.py --input rpi --use-frame
        ;;
    2)
        echo "🔄 Iniciando con cámara USB..."
        python3 people_counter.py --input usb --use-frame
        ;;
    3)
        read -p "Ingresa la URL RTSP (ej: rtsp://user:pass@ip:port/stream): " rtsp_url
        echo "🔄 Iniciando con RTSP: $rtsp_url"
        python3 people_counter.py --rtsp-url "$rtsp_url" --use-frame
        ;;
    4)
        read -p "Ingresa la ruta del archivo de video: " video_file
        echo "🔄 Iniciando con archivo: $video_file"
        python3 people_counter.py --input "$video_file" --use-frame
        ;;
    5)
        echo "🌐 Iniciando solo dashboard web en http://localhost:5000"
        python3 dashboard.py
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac
