# 🚀 Instrucciones para Ejecutar el Contador de Visitantes

## ✅ Configuración Completada

Tu sistema está **completamente configurado** para funcionar con cámaras RTSP.

---

## 📍 Ubicación de Archivos

```
hailo-rpi5-examples/
├── visitor-counter.json          ← Archivo de configuración (RAÍZ)
├── basic_pipelines/
│   └── visitor-counter.py        ← Script principal
└── run_visitor_counter_rtsp.sh   ← Script de ejecución
```

---

## 🎯 Comando para Ejecutar

### Opción 1: Usar el Script (Recomendado)

**En Raspberry Pi / Linux:**
```bash
cd ~/Desktop/hailo-rpi5-examples
chmod +x run_visitor_counter_rtsp.sh
./run_visitor_counter_rtsp.sh "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
```

**En Windows (PowerShell):**
```powershell
cd "C:\Users\Chriz\Desktop\hailo count\hailo-rpi5-examples"
.\run_visitor_counter_rtsp.ps1 -RtspUrl "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
```

### Opción 2: Ejecutar Directamente

**En Raspberry Pi / Linux:**
```bash
cd ~/Desktop/hailo-rpi5-examples/basic_pipelines
python3 visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --use-frame \
  --show-fps
```

**En Windows (PowerShell):**
```powershell
cd "C:\Users\Chriz\Desktop\hailo count\hailo-rpi5-examples\basic_pipelines"
python3 visitor-counter.py `
  --input rtsp `
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" `
  --use-frame `
  --show-fps
```

---

## 🔧 Parámetros Disponibles

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--input rtsp` | Fuente RTSP | (requerido) |
| `--rtsp-url` | URL de cámara | `rtsp://192.168.1.77:554/...` |
| `--network` | Modelo (yolov6n/yolov8s/yolox_s_leaky) | `yolov6n` |
| `--use-frame` | Mostrar frames | (flag) |
| `--show-fps` | Mostrar FPS | (flag) |
| `--labels-json` | Ruta a etiquetas (opcional) | `../visitor-counter.json` |

---

## 📊 Qué Esperar

Cuando ejecutes el comando, deberías ver:

```
╔════════════════════════════════════════════════════════╗
║   Contador de Visitantes con RTSP - Hailo RPi5        ║
╚════════════════════════════════════════════════════════╝

🎥 URL RTSP: rtsp://192.168.1.77:554/...
📊 Modelo: yolov6n (por defecto)
📝 Etiquetas: ../visitor-counter.json (automático)

Iniciando pipeline...

🎯 Configurando pipeline RTSP personalizado para: rtsp://...
🔧 Construyendo pipeline RTSP personalizado...
✅ Pipeline RTSP COMPLETO configurado desde cero
🎯 Pipeline: rtspsrc location='rtsp://...'
🚫 NO hay referencias a filesrc/MP4
```

Luego verás:
- ✅ Video en vivo de la cámara
- ✅ Personas detectadas con bounding boxes
- ✅ Línea vertical en el centro (x=340)
- ✅ Contadores IN/OUT en la parte superior e inferior
- ✅ FPS en tiempo real

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'hailo_rpi_common'"

**Causa:** Ambiente virtual no activado

**Solución:**
```bash
# Activar ambiente virtual
source venv_hailo_rpi_examples/bin/activate

# Luego ejecutar el comando
./run_visitor_counter_rtsp.sh "rtsp://..."
```

### Error: "Failed to connect to RTSP"

**Causa:** URL RTSP incorrecta o cámara no disponible

**Solución:**
1. Verifica que la URL RTSP es correcta
2. Verifica que la cámara está encendida
3. Verifica conectividad de red: `ping 192.168.1.77`
4. Prueba primero con `detection.py`

### Error: "No such file or directory: '../visitor-counter.json'"

**Causa:** Ejecutas desde directorio incorrecto

**Solución:**
```bash
# Correcto
cd hailo-rpi5-examples/basic_pipelines
python3 visitor-counter.py ...

# Incorrecto
cd hailo-rpi5-examples
python3 visitor-counter.py ...
```

### Bajo rendimiento / FPS bajo

**Soluciones:**
```bash
# Usar modelo más rápido
python3 visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://..." \
  --network yolov6n

# O aumentar latencia RTSP (modificar código)
```

---

## 📝 Archivos Importantes

- `visitor-counter.json` - Configuración de etiquetas y umbrales
- `basic_pipelines/visitor-counter.py` - Script principal
- `run_visitor_counter_rtsp.sh` - Script de ejecución (Linux/RPi)
- `run_visitor_counter_rtsp.ps1` - Script de ejecución (Windows)

---

## 🎯 Configuración de Línea de Detección

**Línea vertical (arriba → abajo):**
- START: (340, 0) - punto superior
- END: (340, 640) - punto inferior
- Personas entran desde arriba
- Personas salen hacia abajo

**Para cambiar la posición:**
Edita `basic_pipelines/visitor-counter.py` líneas 316-317:
```python
START = sv.Point(340, 0)    # Cambia 340 para mover horizontalmente
END = sv.Point(340, 640)
```

---

## ✨ Resumen

| Aspecto | Estado |
|--------|--------|
| Captura RTSP | ✅ Configurada |
| Archivo de configuración | ✅ Automático (raíz) |
| Línea de detección | ✅ Vertical (arriba → abajo) |
| Conteo IN/OUT | ✅ Funcional |
| Scripts de ejecución | ✅ Listos |
| Documentación | ✅ Completa |

---

## 🚀 Próximos Pasos

1. **Ejecuta el comando:**
   ```bash
   ./run_visitor_counter_rtsp.sh "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
   ```

2. **Verifica que funciona:**
   - ✅ Video en vivo
   - ✅ Personas detectadas
   - ✅ Contadores actualizándose

3. **Personaliza si es necesario:**
   - Cambia modelo: `--network yolov8s`
   - Cambia línea: Edita START/END en código
   - Cambia umbrales: Edita `visitor-counter.json`

---

## 📞 Soporte

Si encuentras problemas:
1. Verifica que `detection.py` funciona con RTSP
2. Revisa los logs de GStreamer
3. Comprueba conectividad de red
4. Consulta la documentación en `VISITOR_COUNTER_CONFIG.md`

---

**¡Listo para usar! 🎉**
