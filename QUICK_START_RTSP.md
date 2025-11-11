# Inicio Rápido - Contador de Visitantes con RTSP

## Paso 1: Verificar la URL RTSP
Asegúrate de que la URL RTSP funciona (como en `detection.py`):
```bash
python3 ./basic_pipelines/detection.py --input rtsp --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" --labels-json ../resources/visitor-counter.json
```

## Paso 2: Ejecutar el Contador de Visitantes con RTSP

### En Linux/Raspberry Pi:
```bash
cd /ruta/al/hailo-rpi5-examples
python3 ./basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --labels-json ../resources/visitor-counter.json \
  --use-frame \
  --show-fps
```

O usar el script:
```bash
chmod +x run_visitor_counter_rtsp.sh
./run_visitor_counter_rtsp.sh "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
```

### En Windows (PowerShell):
```powershell
cd "C:\Users\Chriz\Desktop\hailo count\hailo-rpi5-examples"
python3 ./basic_pipelines/visitor-counter.py `
  --input rtsp `
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" `
  --labels-json ../resources/visitor-counter.json `
  --use-frame `
  --show-fps
```

O usar el script:
```powershell
.\run_visitor_counter_rtsp.ps1 -RtspUrl "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
```

## Paso 3: Verificar la Salida

Deberías ver:
- ✅ "Configurando pipeline RTSP personalizado para: rtsp://..."
- ✅ "Construyendo pipeline RTSP personalizado..."
- ✅ "Pipeline RTSP COMPLETO configurado desde cero"
- ✅ Contador de personas en pantalla (IN/OUT)
- ✅ FPS mostrado en tiempo real

## Cambios Realizados en visitor-counter.py

1. **Agregada clase `RTSPGStreamerDetectionApp`**
   - Hereda de `GStreamerApp`
   - Implementa `get_pipeline_string()` para RTSP
   - Usa la misma URL RTSP que `detection.py`

2. **Agregado parámetro `--rtsp-url`**
   - Permite especificar la URL de la cámara RTSP
   - Opcional (mantiene compatibilidad con `--input rpi/usb/file`)

3. **Lógica de selección de clase**
   - Si se proporciona `--rtsp-url`, usa `RTSPGStreamerDetectionApp`
   - Si no, usa `GStreamerDetectionApp` (comportamiento original)

## Comparación: detection.py vs visitor-counter.py

| Característica | detection.py | visitor-counter.py |
|---|---|---|
| Fuente RTSP | ✅ Soportada | ✅ Soportada (NUEVO) |
| Detección de personas | ✅ Sí | ✅ Sí |
| Tracking de personas | ✅ Sí | ✅ Sí |
| Conteo IN/OUT | ❌ No | ✅ Sí (NUEVO) |
| Polígono personalizado | ✅ Sí | ❌ No (línea fija) |
| Visualización | Bounding boxes | Contadores de texto |

## Solución de Problemas

### Error: "rtspsrc not found"
- Instala GStreamer con soporte RTSP:
  ```bash
  sudo apt-get install gstreamer1.0-plugins-good gstreamer1.0-plugins-bad
  ```

### Error: "Failed to connect to RTSP"
- Verifica la URL RTSP
- Comprueba conectividad de red
- Prueba primero con `detection.py`

### Bajo rendimiento
- Reduce resolución: Modifica `self.network_width` y `self.network_height`
- Usa modelo más rápido: `--network yolov6n`
- Aumenta latencia RTSP: Modifica `latency=300` a `latency=500`

## Archivos Creados/Modificados

- ✅ `basic_pipelines/visitor-counter.py` - Modificado con soporte RTSP
- ✅ `RTSP_VISITOR_COUNTER_SETUP.md` - Documentación completa
- ✅ `run_visitor_counter_rtsp.sh` - Script para Linux/Raspberry Pi
- ✅ `run_visitor_counter_rtsp.ps1` - Script para Windows
- ✅ `QUICK_START_RTSP.md` - Este archivo

## Próximos Pasos

1. Prueba con tu cámara RTSP
2. Ajusta la línea de detección si es necesario (modificar `START` y `END` en el código)
3. Personaliza los modelos y parámetros según tus necesidades
4. Considera agregar persistencia de contadores (guardar en archivo)

## Soporte

Si encuentras problemas:
1. Verifica que `detection.py` funciona con RTSP
2. Revisa los logs de GStreamer
3. Comprueba que la cámara está accesible
4. Consulta la documentación de Hailo TAPPAS
