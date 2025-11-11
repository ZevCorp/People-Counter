# Resumen de Implementación - Contador de Visitantes con RTSP

## ✅ Tarea Completada

Se ha adaptado exitosamente `visitor-counter.py` para usar la captura RTSP que ya funciona en `detection.py`.

## 📋 Cambios Realizados

### 1. Modificación Principal: `basic_pipelines/visitor-counter.py`

#### Importaciones Agregadas
```python
from pathlib import Path  # Línea 13
```

#### Nueva Clase: `RTSPGStreamerDetectionApp` (Líneas 91-196)
- Hereda de `GStreamerApp`
- Recibe `rtsp_url` en el constructor
- Implementa `get_pipeline_string()` con pipeline RTSP completo
- Pipeline incluye:
  - `rtspsrc` para captura RTSP
  - `rtph264depay`, `h264parse`, `avdec_h264` para decodificación
  - `videoscale`, `videoconvert` para procesamiento
  - `hailomuxer`, `hailonet`, `hailofilter`, `hailotracker` para IA
  - `hailooverlay`, `textoverlay` para visualización
  - `fpsdisplaysink` para salida

#### Nuevo Parámetro: `--rtsp-url` (Líneas 335-339)
```python
parser.add_argument(
  "--rtsp-url",
  default=None,
  help="RTSP URL for camera stream",
)
```

#### Lógica de Selección (Líneas 341-348)
```python
if args.rtsp_url:
  print(f"🎥 Usando RTSP: {args.rtsp_url}")
  app = RTSPGStreamerDetectionApp(args, user_data, args.rtsp_url)
else:
  print("📹 Usando fuente estándar (rpi/usb/archivo)")
  app = GStreamerDetectionApp(args, user_data)
```

## 🚀 Cómo Usar

### Comando Básico
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json
```

### Con Opciones Completas
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json \
  --network yolov6n \
  --use-frame \
  --show-fps
```

### Usando Scripts
**Linux/Raspberry Pi:**
```bash
chmod +x run_visitor_counter_rtsp.sh
./run_visitor_counter_rtsp.sh "rtsp://192.168.1.77:554/..."
```

**Windows (PowerShell):**
```powershell
.\run_visitor_counter_rtsp.ps1 -RtspUrl "rtsp://192.168.1.77:554/..."
```

## 📁 Archivos Creados/Modificados

### Modificados
- ✅ `basic_pipelines/visitor-counter.py`
  - Agregada clase `RTSPGStreamerDetectionApp`
  - Agregado parámetro `--rtsp-url`
  - Agregada lógica de selección de clase

### Nuevos
- ✅ `RTSP_VISITOR_COUNTER_SETUP.md` - Documentación completa
- ✅ `QUICK_START_RTSP.md` - Guía de inicio rápido
- ✅ `run_visitor_counter_rtsp.sh` - Script para Linux/RPi
- ✅ `run_visitor_counter_rtsp.ps1` - Script para Windows
- ✅ `IMPLEMENTATION_SUMMARY.md` - Este archivo

## 🔄 Comparación: detection.py vs visitor-counter.py

| Aspecto | detection.py | visitor-counter.py |
|--------|--------------|-------------------|
| Captura RTSP | ✅ Sí | ✅ Sí (NUEVO) |
| Detección de personas | ✅ Sí | ✅ Sí |
| Tracking de personas | ✅ Sí | ✅ Sí |
| Conteo IN/OUT | ❌ No | ✅ Sí |
| Polígono personalizado | ✅ Sí | ❌ Línea fija |
| Visualización | Bounding boxes | Contadores de texto |
| Fuentes locales (rpi/usb) | ❌ No | ✅ Sí |

## 🎯 Características Principales

- ✅ **Captura RTSP**: Usa la misma URL que funciona en `detection.py`
- ✅ **Conteo de Personas**: Cuenta IN/OUT en tiempo real
- ✅ **Tracking**: Rastrea personas con ID único
- ✅ **Visualización**: Muestra contadores en pantalla
- ✅ **Modelos Flexibles**: Soporta YOLOv6n, YOLOv8s, YOLOx
- ✅ **Retrocompatibilidad**: Mantiene soporte para rpi/usb/file
- ✅ **Etiquetas Personalizadas**: Usa `visitor-counter.json`

## 🔧 Parámetros Disponibles

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `--input` | str | Fuente (rpi/usb/file/rtsp) | `rtsp` |
| `--rtsp-url` | str | URL de cámara RTSP | `rtsp://192.168.1.77:554/...` |
| `--labels-json` | str | Ruta a etiquetas JSON | `../resources/visitor-counter.json` |
| `--network` | str | Modelo (yolov6n/yolov8s/yolox_s_leaky) | `yolov6n` |
| `--hef-path` | str | Ruta personalizada a HEF | `/ruta/modelo.hef` |
| `--use-frame` | flag | Mostrar frames procesados | (sin valor) |
| `--show-fps` | flag | Mostrar FPS en pantalla | (sin valor) |

## 📊 Flujo de Procesamiento RTSP

```
RTSP Stream
    ↓
rtspsrc (captura)
    ↓
rtph264depay → h264parse → avdec_h264 (decodificación)
    ↓
videoscale → videoconvert (procesamiento)
    ↓
hailomuxer (multiplexing)
    ├→ hailonet (inferencia YOLOv6n/v8s/YOLOx)
    ├→ hailofilter (post-procesamiento)
    └→ hailotracker (tracking)
    ↓
hailooverlay (visualización detecciones)
    ↓
textoverlay (contadores IN/OUT)
    ↓
fpsdisplaysink (salida a pantalla)
```

## 🧪 Verificación

Para verificar que todo funciona:

1. **Prueba con `detection.py` primero:**
   ```bash
   python3 ./basic_pipelines/detection.py \
     --input rtsp \
     --rtsp-url "rtsp://192.168.1.77:554/..." \
     --labels-json ../resources/visitor-counter.json
   ```

2. **Luego prueba con `visitor-counter.py`:**
   ```bash
   python3 ./basic_pipelines/visitor-counter.py \
     --input rtsp \
     --rtsp-url "rtsp://192.168.1.77:554/..." \
     --labels-json ../resources/visitor-counter.json
   ```

3. **Verifica la salida:**
   - ✅ "Configurando pipeline RTSP personalizado para: rtsp://..."
   - ✅ "Construyendo pipeline RTSP personalizado..."
   - ✅ "Pipeline RTSP COMPLETO configurado desde cero"
   - ✅ Contadores IN/OUT en pantalla
   - ✅ FPS mostrado en tiempo real

## 🐛 Solución de Problemas

### Error: "rtspsrc not found"
```bash
sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad
```

### Error: "Failed to connect to RTSP"
- Verifica URL RTSP
- Comprueba conectividad de red
- Prueba primero con `detection.py`

### Bajo rendimiento / FPS bajo
- Reduce resolución (modifica `network_width`, `network_height`)
- Usa modelo más rápido (`--network yolov6n`)
- Aumenta latencia RTSP (`latency=500`)

## 📝 Notas Importantes

1. **URL RTSP**: Reemplaza `192.168.1.77` con IP de tu cámara
2. **Protocolo TCP**: Usa `protocols=tcp` para estabilidad
3. **Latencia**: Ajusta `latency=300` si hay problemas de sincronización
4. **Modelo**: YOLOv6n es más rápido, YOLOv8s es más preciso
5. **Línea de Detección**: Configurada en x=340 (ajustable en código)

## 📚 Referencias

- Tutorial Original: https://www.cytron.io/tutorial/raspberry-pi-ai-kit-booth-visitor-counter
- Hailo TAPPAS: https://github.com/hailo-ai/tappas
- GStreamer: https://gstreamer.freedesktop.org/
- Supervision: https://github.com/roboflow/supervision

## ✨ Resumen

La integración RTSP en `visitor-counter.py` está **completada y lista para usar**. El sistema:
- Captura video desde cámaras RTSP
- Detecta y rastrea personas
- Cuenta personas que cruzan la línea de detección
- Visualiza contadores IN/OUT en tiempo real
- Mantiene compatibilidad con fuentes locales

**Comando recomendado para comenzar:**
```bash
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json \
  --use-frame \
  --show-fps
```
