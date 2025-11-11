# Configuración del Contador de Visitantes - visitor-counter.json

## 📍 Ubicación del Archivo

El archivo `visitor-counter.json` se encuentra en la **carpeta raíz** del proyecto:
```
hailo-rpi5-examples/
├── visitor-counter.json          ← AQUÍ (raíz)
├── basic_pipelines/
│   ├── visitor-counter.py
│   ├── detection.py
│   └── ...
├── resources/
│   └── ...
└── ...
```

## 🔍 Cómo el Código Rastrea el Archivo

### Ruta por Defecto (Automática)

El código ahora tiene una ruta por defecto configurada:

```python
parser.add_argument(
  "--labels-json",
  default="../visitor-counter.json",  # ← Ruta por defecto
  help="Path to costume labels JSON file",
)
```

**Explicación:**
- Cuando ejecutas desde `basic_pipelines/visitor-counter.py`
- `../` sube un nivel al directorio raíz
- Busca `visitor-counter.json` en la raíz
- **Resultado:** `hailo-rpi5-examples/visitor-counter.json` ✅

### Cómo Funciona la Ruta Relativa

```
Ubicación actual: hailo-rpi5-examples/basic_pipelines/visitor-counter.py
Ruta relativa: ../visitor-counter.json

Resolución:
  basic_pipelines/  ← estamos aquí
  ../              ← sube a la carpeta padre
  visitor-counter.json ← busca este archivo

Resultado final: hailo-rpi5-examples/visitor-counter.json ✅
```

## 🚀 Comandos de Ejecución

### Opción 1: Usar Ruta por Defecto (Recomendado)
```bash
cd hailo-rpi5-examples/basic_pipelines
python3 visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
```

**Resultado:**
- ✅ Busca automáticamente `../visitor-counter.json`
- ✅ Encuentra el archivo en la raíz
- ✅ Carga las etiquetas correctamente

### Opción 2: Especificar Ruta Explícitamente
```bash
cd hailo-rpi5-examples/basic_pipelines
python3 visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/..." \
  --labels-json ../visitor-counter.json
```

### Opción 3: Ejecutar desde la Raíz
```bash
cd hailo-rpi5-examples
python3 basic_pipelines/visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/..." \
  --labels-json visitor-counter.json
```

## 📋 Contenido de visitor-counter.json

```json
{
  "iou_threshold": 0.45,
  "detection_threshold": 0.7,
  "output_activation": "none",
  "label_offset": 1,
  "max_boxes": 200,
  "anchors": [
    [116, 90, 156, 198, 373, 326],
    [30, 61, 62, 45, 59, 119],
    [10, 13, 16, 30, 33, 23]
  ],
  "labels": [
    "unlabeled",
    "Person"
  ]
}
```

**Parámetros:**
- `iou_threshold`: 0.45 - Umbral de IoU para NMS
- `detection_threshold`: 0.7 - Confianza mínima de detección
- `label_offset`: 1 - Offset de etiquetas
- `max_boxes`: 200 - Máximo de cajas de detección
- `anchors`: Anchors de YOLO
- `labels`: Etiquetas disponibles (Person)

## 🎯 Configuración de Línea de Detección

### Línea Vertical (Arriba → Abajo)

```python
# Configuración actual en visitor-counter.py
START = sv.Point(340, 0)      # Punto superior (x=340, y=0)
END = sv.Point(340, 640)      # Punto inferior (x=340, y=640)

# Visualización:
# y=0    ← START (arriba)
# |
# | (línea vertical en x=340)
# |
# y=640  ← END (abajo)
```

**Características:**
- ✅ Línea vertical en el centro de la pantalla
- ✅ Personas entran desde arriba
- ✅ Personas salen hacia abajo
- ✅ Contadores IN/OUT funcionan correctamente

### Anclajes de Detección

```python
triggering_anchors=(
  sv.Position.CENTER,        # Centro del bounding box
  sv.Position.TOP_CENTER,    # Arriba-centro
  sv.Position.BOTTOM_CENTER  # Abajo-centro
)
```

**Resultado:**
- Detecta personas que cruzan la línea en cualquier punto vertical
- Más preciso para personas que se solapan
- Evita contar dos veces la misma persona

## 📊 Flujo de Detección

```
Persona entra desde arriba
    ↓
Cámara captura video RTSP
    ↓
Red neuronal detecta persona
    ↓
Bounding box cruza línea vertical (x=340)
    ↓
Sistema verifica anclajes (CENTER, TOP_CENTER, BOTTOM_CENTER)
    ↓
Persona cuenta como IN (↓)
    ↓
Persona continúa hacia abajo
    ↓
Persona sale de pantalla
    ↓
Persona cuenta como OUT (↓)
```

## 🔧 Personalización

### Cambiar Posición de Línea

Para mover la línea a otra posición:

```python
# Línea más a la izquierda
START = sv.Point(200, 0)
END = sv.Point(200, 640)

# Línea más a la derecha
START = sv.Point(480, 0)
END = sv.Point(480, 640)

# Línea horizontal (izquierda → derecha)
START = sv.Point(0, 320)
END = sv.Point(640, 320)
```

### Cambiar Anclajes

```python
# Solo detectar en el centro
triggering_anchors=(sv.Position.CENTER,)

# Detectar en todas las posiciones
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
```

## ✅ Verificación

### Verificar que el Archivo se Carga Correctamente

```bash
# Ejecutar con mensajes de debug
python3 visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/..." \
  --use-frame \
  --show-fps
```

**Señales de éxito:**
- ✅ No hay errores de "archivo no encontrado"
- ✅ Las etiquetas se cargan correctamente
- ✅ El conteo funciona (IN/OUT)
- ✅ Los contadores se actualizan en pantalla

### Verificar Ruta del Archivo

```bash
# Ver la ruta absoluta del archivo
python3 -c "import os; print(os.path.abspath('../visitor-counter.json'))"
```

## 🐛 Troubleshooting

### Error: "No such file or directory: ../visitor-counter.json"

**Causa:** Ejecutas desde un directorio incorrecto

**Solución:**
```bash
# Correcto
cd hailo-rpi5-examples/basic_pipelines
python3 visitor-counter.py ...

# Incorrecto
cd hailo-rpi5-examples
python3 visitor-counter.py ...  # Buscaría ../../visitor-counter.json
```

### Error: "Failed to load labels from JSON"

**Causa:** El archivo JSON está corrupto o mal formado

**Solución:**
```bash
# Verificar que el JSON es válido
python3 -m json.tool visitor-counter.json

# Verificar contenido
cat visitor-counter.json
```

### El Conteo No Funciona

**Causa:** Línea de detección mal configurada

**Solución:**
1. Verifica que `START` y `END` están correctos
2. Verifica que los anclajes incluyen `CENTER`
3. Prueba con `--use-frame` para ver la línea

## 📝 Resumen

| Aspecto | Configuración |
|--------|---|
| Ubicación del archivo | `hailo-rpi5-examples/visitor-counter.json` |
| Ruta por defecto | `../visitor-counter.json` |
| Línea de detección | Vertical (x=340, y=0 a y=640) |
| Dirección | Arriba → Abajo |
| Anclajes | CENTER, TOP_CENTER, BOTTOM_CENTER |
| Etiqueta detectada | Person |
| Umbral de confianza | 0.7 |

## 🎯 Comando Recomendado

```bash
cd hailo-rpi5-examples/basic_pipelines
python3 visitor-counter.py \
  --input rtsp \
  --rtsp-url "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif" \
  --use-frame \
  --show-fps
```

**Resultado esperado:**
- ✅ Carga `../visitor-counter.json` automáticamente
- ✅ Conecta a cámara RTSP
- ✅ Detecta personas
- ✅ Cuenta IN/OUT en línea vertical
- ✅ Muestra contadores en pantalla
