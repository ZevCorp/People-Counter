#!/bin/bash

# Script para ejecutar el contador de visitantes con RTSP
# Uso: ./run_visitor_counter_rtsp.sh [URL_RTSP]

# URL RTSP por defecto (reemplazar con tu cámara)
RTSP_URL="${1:-rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif}"

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Contador de Visitantes con RTSP - Hailo RPi5        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}🎥 URL RTSP:${NC} $RTSP_URL"
echo -e "${GREEN}📊 Modelo:${NC} yolov6n (por defecto)"
echo -e "${GREEN}📝 Etiquetas:${NC} ../visitor-counter.json (automático)"
echo ""
echo -e "${YELLOW}Iniciando pipeline...${NC}"
echo ""

# Ejecutar el contador de visitantes con RTSP
# Nota: --labels-json se carga automáticamente desde ../visitor-counter.json
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "$RTSP_URL" \
  --use-frame \
  --show-fps

echo ""
echo -e "${YELLOW}Pipeline finalizado${NC}"
