# Uso Avanzado - Contador de Visitantes con RTSP

## Ejemplos de Uso Avanzado

### 1. Con Diferentes Modelos de Red

#### YOLOv6n (Más rápido, menos preciso)
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json \
  --network yolov6n
```

#### YOLOv8s (Balance)
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json \
  --network yolov8s
```

#### YOLOx_s_leaky (Más preciso, más lento)
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json \
  --network yolox_s_leaky
```

### 2. Con Modelo Personalizado

Si tienes un modelo HEF personalizado:
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json \
  --hef-path /ruta/a/tu/modelo_personalizado.hef
```

### 3. Con Visualización Completa

```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json \
  --use-frame \
  --show-fps \
  --network yolov8s
```

### 4. Múltiples Cámaras RTSP

Ejecutar en terminales separadas:

**Terminal 1 - Cámara 1:**
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json
```

**Terminal 2 - Cámara 2:**
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.78:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json
```

### 5. Combinación de Fuentes

#### RTSP + Archivo de Video
```bash
# Terminal 1 - RTSP
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/..." \
  --labels-json ../resources/visitor-counter.json

# Terminal 2 - Archivo
python3 ./basic_pipelines/visitor-counter.py \
  --input file \
  --video-source /ruta/a/video.mp4 \
  --labels-json ../resources/visitor-counter.json
```

#### RTSP + Cámara Local RPi
```bash
# Terminal 1 - RTSP
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/..." \
  --labels-json ../resources/visitor-counter.json

# Terminal 2 - Cámara RPi
python3 ./basic_pipelines/visitor-counter.py \
  --input rpi \
  --labels-json ../resources/visitor-counter.json
```

## Personalización del Código

### 1. Cambiar Posición de la Línea de Detección

En `visitor-counter.py`, líneas 313-314:
```python
# Línea vertical en x=340 (actual)
START = sv.Point(340, 0)
END = sv.Point(340, 640)

# Cambiar a línea horizontal en y=320
START = sv.Point(0, 320)
END = sv.Point(640, 320)

# Cambiar a línea diagonal
START = sv.Point(100, 100)
END = sv.Point(540, 540)
```

### 2. Cambiar Anclajes de Detección

En `visitor-counter.py`, línea 315:
```python
# Actual - detecta en centro, arriba y abajo
line_zone = sv.LineZone(
  start=START, 
  end=END, 
  triggering_anchors=(
    sv.Position.CENTER,
    sv.Position.TOP_CENTER, 
    sv.Position.BOTTOM_CENTER
  )
)

# Solo detectar en centro
line_zone = sv.LineZone(
  start=START, 
  end=END, 
  triggering_anchors=(sv.Position.CENTER,)
)

# Detectar en todas las posiciones
line_zone = sv.LineZone(
  start=START, 
  end=END, 
  triggering_anchors=(
    sv.Position.TOP_LEFT,
    sv.Position.TOP_CENTER,
    sv.Position.TOP_RIGHT,
    sv.Position.CENTER_LEFT,
    sv.Position.CENTER,
    sv.Position.CENTER_RIGHT,
    sv.Position.BOTTOM_LEFT,
    sv.Position.BOTTOM_CENTER,
    sv.Position.BOTTOM_RIGHT,
  )
)
```

### 3. Cambiar Resolución de Red

En la clase `RTSPGStreamerDetectionApp`, líneas 101-102:
```python
# Actual - 640x640
self.network_width = 640
self.network_height = 640

# Para mejor rendimiento - 416x416
self.network_width = 416
self.network_height = 416

# Para mejor precisión - 832x832
self.network_width = 832
self.network_height = 832
```

### 4. Cambiar Latencia RTSP

En `RTSPGStreamerDetectionApp.get_pipeline_string()`, línea 151:
```python
# Actual - 300ms
f'rtspsrc location="{self.rtsp_url}" protocols=tcp latency=300 '

# Para mejor sincronización - 100ms
f'rtspsrc location="{self.rtsp_url}" protocols=tcp latency=100 '

# Para mejor estabilidad - 500ms
f'rtspsrc location="{self.rtsp_url}" protocols=tcp latency=500 '
```

### 5. Cambiar Umbrales de Confianza

En `RTSPGStreamerDetectionApp.__init__()`, líneas 104-105:
```python
# Actual
nms_score_threshold = 0.3
nms_iou_threshold = 0.45

# Más estricto (menos falsos positivos)
nms_score_threshold = 0.5
nms_iou_threshold = 0.6

# Más permisivo (más detecciones)
nms_score_threshold = 0.1
nms_iou_threshold = 0.3
```

## Integración con Sistemas Externos

### 1. Guardar Contadores en Archivo

Agregar al final de `app_callback()`:
```python
# Guardar contadores en archivo
with open('/tmp/visitor_count.txt', 'w') as f:
  f.write(f"IN: {line_zone.in_count}\n")
  f.write(f"OUT: {line_zone.out_count}\n")
  f.write(f"Total: {line_zone.in_count + line_zone.out_count}\n")
```

### 2. Enviar Contadores a Base de Datos

```python
import sqlite3
from datetime import datetime

# Crear conexión a BD
conn = sqlite3.connect('/tmp/visitor_counter.db')
cursor = conn.cursor()

# Crear tabla
cursor.execute('''
  CREATE TABLE IF NOT EXISTS counts (
    timestamp TEXT,
    in_count INTEGER,
    out_count INTEGER
  )
''')

# Guardar cada 60 segundos
if user_data.get_count() % 1800 == 0:  # ~60 segundos a 30 FPS
  cursor.execute(
    'INSERT INTO counts VALUES (?, ?, ?)',
    (datetime.now().isoformat(), line_zone.in_count, line_zone.out_count)
  )
  conn.commit()
```

### 3. Enviar Contadores a API REST

```python
import requests
import json

# Enviar cada 60 segundos
if user_data.get_count() % 1800 == 0:
  data = {
    'timestamp': datetime.now().isoformat(),
    'in_count': line_zone.in_count,
    'out_count': line_zone.out_count,
    'camera_id': 'cam_001'
  }
  
  try:
    response = requests.post(
      'http://tu-servidor.com/api/counts',
      json=data,
      timeout=5
    )
    print(f"✅ Contadores enviados: {response.status_code}")
  except Exception as e:
    print(f"❌ Error enviando contadores: {e}")
```

### 4. Integración con MQTT

```python
import paho.mqtt.client as mqtt

# Conectar a broker MQTT
client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

# Publicar cada 60 segundos
if user_data.get_count() % 1800 == 0:
  client.publish(
    "visitor_counter/in",
    line_zone.in_count
  )
  client.publish(
    "visitor_counter/out",
    line_zone.out_count
  )
```

## Monitoreo y Debugging

### 1. Habilitar Logs Detallados de GStreamer

```bash
GST_DEBUG=3 python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/..." \
  --labels-json ../resources/visitor-counter.json
```

### 2. Guardar Frames Procesados

En `app_callback()`, línea 82:
```python
# Actual - guarda cada frame
cv2.imwrite('/home/raspberry/output_frame.jpg', frame)

# Guardar cada 30 frames (1 segundo a 30 FPS)
if user_data.get_count() % 30 == 0:
  cv2.imwrite(f'/tmp/frame_{user_data.get_count()}.jpg', frame)
```

### 3. Monitoreo de Rendimiento

```python
import time

# Agregar al inicio de app_callback()
start_time = time.time()

# ... procesamiento ...

# Agregar al final de app_callback()
elapsed = time.time() - start_time
if user_data.get_count() % 30 == 0:
  print(f"⏱️  Tiempo de procesamiento: {elapsed*1000:.2f}ms")
```

## Optimización para Producción

### 1. Usar systemd para Ejecutar Automáticamente

Crear `/etc/systemd/system/visitor-counter.service`:
```ini
[Unit]
Description=Visitor Counter with RTSP
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/hailo-rpi5-examples
ExecStart=/usr/bin/python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Habilitar:
```bash
sudo systemctl enable visitor-counter.service
sudo systemctl start visitor-counter.service
```

### 2. Monitoreo con Systemd

```bash
# Ver estado
sudo systemctl status visitor-counter.service

# Ver logs
sudo journalctl -u visitor-counter.service -f

# Reiniciar
sudo systemctl restart visitor-counter.service
```

## Troubleshooting Avanzado

### Problema: Conexión RTSP inestable
**Solución:**
```bash
# Aumentar timeouts
GST_DEBUG=3 python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/..." \
  --labels-json ../resources/visitor-counter.json
```

### Problema: Bajo FPS
**Solución:**
```bash
# Usar modelo más rápido y resolución menor
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/..." \
  --labels-json ../resources/visitor-counter.json \
  --network yolov6n
```

### Problema: Falsos positivos
**Solución:**
- Aumentar `nms_score_threshold` a 0.5 o 0.6
- Usar modelo más preciso (YOLOv8s o YOLOx)
- Ajustar línea de detección

## Referencias Adicionales

- Supervision Docs: https://supervision.roboflow.com/
- GStreamer Pipeline: https://gstreamer.freedesktop.org/documentation/
- Hailo TAPPAS: https://github.com/hailo-ai/tappas
- MQTT Protocol: https://mqtt.org/
