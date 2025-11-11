# Script para ejecutar el contador de visitantes con RTSP en Windows
# Uso: .\run_visitor_counter_rtsp.ps1 -RtspUrl "rtsp://..."

param(
    [string]$RtspUrl = "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
    [string]$Network = "yolov6n"
)

Write-Host "╔════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Contador de Visitantes con RTSP - Hailo RPi5        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎥 URL RTSP: $RtspUrl" -ForegroundColor Green
Write-Host "📊 Modelo: $Network" -ForegroundColor Green
Write-Host "📝 Etiquetas: ../visitor-counter.json (automático)" -ForegroundColor Green
Write-Host ""
Write-Host "Iniciando pipeline..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar el contador de visitantes con RTSP
# Nota: --labels-json se carga automáticamente desde ../visitor-counter.json
python3 ./basic_pipelines/visitor-counter.py `
  --input rtsp `
  --rtsp-url $RtspUrl `
  --network $Network `
  --use-frame `
  --show-fps

Write-Host ""
Write-Host "Pipeline finalizado" -ForegroundColor Yellow
