# Configuración del Contador de Visitantes con RTSP

## Descripción
Este documento explica cómo usar el `visitor-counter.py` con una cámara RTSP en lugar de la cámara local de la Raspberry Pi.

## Cambios Realizados
Se ha modificado `basic_pipelines/visitor-counter.py` para soportar:
- Captura de video desde cámaras RTSP (como en `detection.py`)
- Mantener toda la funcionalidad de conteo de personas
- Usar la misma URL RTSP que funciona en `detection.py`

## Uso

### Opción 1: Con Cámara RTSP (Recomendado)
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json
```

### Opción 2: Con Cámara Local de Raspberry Pi (Original)
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rpi \
  --labels-json ../resources/visitor-counter.json
```

### Opción 3: Con Cámara USB
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input usb \
  --video-source /dev/video0 \
  --labels-json ../resources/visitor-counter.json
```

### Opción 4: Con Archivo de Video
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input file \
  --video-source /ruta/al/video.mp4 \
  --labels-json ../resources/visitor-counter.json
```

## Parámetros Disponibles

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--input` | Tipo de fuente (rpi, usb, file, rtsp) | `rpi` |
| `--rtsp-url` | URL de la cámara RTSP | `rtsp://192.168.1.77:554/...` |
| `--labels-json` | Ruta al archivo JSON de etiquetas | `../resources/visitor-counter.json` |
| `--network` | Red neuronal a usar (yolov6n, yolov8s, yolox_s_leaky) | `yolov6n` |
| `--hef-path` | Ruta personalizada al archivo HEF | `/ruta/al/modelo.hef` |
| `--use-frame` | Mostrar frames procesados | (flag) |
| `--show-fps` | Mostrar FPS en pantalla | (flag) |

## Cómo Funciona

### Flujo de Procesamiento RTSP
1. **Captura RTSP**: Se conecta a la cámara usando `rtspsrc`
2. **Decodificación**: Decodifica el stream H.264
3. **Procesamiento**: Redimensiona y convierte el video al formato RGB
4. **Inferencia**: Ejecuta la red neuronal YOLOv6n/v8s/YOLOx
5. **Tracking**: Rastrea personas usando el tracker de Hailo
6. **Conteo**: Cuenta personas que cruzan la línea de detección
7. **Visualización**: Muestra IN/OUT en pantalla

### Línea de Detección
- **Posición**: Vertical en x=340 (ajustable en el código)
- **Anclajes**: CENTER, TOP_CENTER, BOTTOM_CENTER
- **Salida**: Muestra contadores IN (←) y OUT (→)

## Comparación con detection.py

| Aspecto | detection.py | visitor-counter.py |
|--------|--------------|-------------------|
| Propósito | Detección de personas | Conteo de personas |
| Salida | Bounding boxes + tracking | Contadores IN/OUT |
| Línea de detección | Polígono personalizado | Línea vertical |
| Visualización | Overlay de detecciones | Contadores de texto |

## Solución de Problemas

### Error: "Failed to connect to RTSP stream"
- Verifica que la URL RTSP sea correcta
- Comprueba la conectividad de red
- Asegúrate de que la cámara está encendida

### Error: "Pipeline creation failed"
- Verifica que todos los parámetros sean válidos
- Comprueba que el archivo HEF existe
- Revisa los logs para más detalles

### Bajo rendimiento / FPS bajo
- Reduce la resolución de entrada
- Usa un modelo más pequeño (yolov6n)
- Aumenta la latencia RTSP si es necesario

## Notas Importantes

1. **URL RTSP**: Reemplaza `192.168.1.77` con la IP de tu cámara
2. **Protocolo**: Usa `protocols=tcp` para mejor estabilidad
3. **Latencia**: Ajusta `latency=300` si hay problemas de sincronización
4. **Modelo**: YOLOv6n es más rápido, YOLOv8s es más preciso

## Archivos Modificados

- `basic_pipelines/visitor-counter.py`: Agregada clase `RTSPGStreamerDetectionApp` y soporte RTSP
- Este archivo: Documentación de uso

## Referencias

- Tutorial original: https://www.cytron.io/tutorial/raspberry-pi-ai-kit-booth-visitor-counter
- Hailo TAPPAS: https://github.com/hailo-ai/tappas
- GStreamer: https://gstreamer.freedesktop.org/
