#!/bin/bash

# Script para probar conectividad RTSP en Raspberry Pi
# Creado para testing de cámara IP

echo "🚀 Iniciando test de conectividad RTSP..."
echo "📅 $(date)"
echo "=================================="

# Crear el script Python temporal
cat > /tmp/test_rtsp.py << 'EOF'
import cv2
print("🔍 Probando conectividad RTSP con OpenCV...")
rtsp_url = "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
cap = cv2.VideoCapture(rtsp_url)
if not cap.isOpened():
    print("❌ Error: No se pudo abrir el flujo RTSP con OpenCV.")
else:
    print("✅ Conectado exitosamente al stream RTSP")
    ret, frame = cap.read()
    if ret:
        print(f"📐 Resolución del frame: {frame.shape}")
        print("✅ Frame capturado exitosamente")
    else:
        print("❌ No se pudo leer frame del stream")
cap.release()
EOF

# Ejecutar el test
echo "🔄 Ejecutando test..."
python /tmp/test_rtsp.py

# Limpiar archivo temporal
rm /tmp/test_rtsp.py

echo "=================================="
echo "✅ Test completado"