# 🤖 Sistema de Conteo de Personas con Hailo AI

## 📋 Descripción
Sistema inteligente de conteo de personas en tiempo real utilizando el procesador AI Hailo-8/8L en Raspberry Pi 5. Soporta múltiples fuentes de video incluyendo **RTSP streams**, cámaras USB, y archivos de video.

### ✨ Características Principales
- **🎯 Conteo Preciso:** Detección de personas con tracking único usando Hailo AI
- **📹 Soporte RTSP:** Streaming en tiempo real desde cámaras IP
- **🚪 Zonas Inteligentes:** Líneas configurables de entrada y salida
- **📊 Dashboard Web:** Interface simple para monitoreo en tiempo real
- **💾 Persistencia:** Guardado automático de estadísticas y eventos
- **🔄 Anti-duplicación:** Sistema robusto contra conteos erróneos

## 🚀 Instalación Rápida

### 1. Preparar Entorno Virtual Hailo
```bash
# ⚠️ IMPORTANTE: Configurar entorno virtual venv_hailo_rpi_examples
source setup_env.sh

# Verificar que el entorno esté activo
echo $VIRTUAL_ENV  # Debería mostrar: .../venv_hailo_rpi_examples

# Instalar dependencias adicionales en el venv
pip install -r requirements_counter.txt
```

**📋 Nota Importante**: Este sistema usa el mismo entorno virtual que los ejemplos oficiales de Hailo (`venv_hailo_rpi_examples`) para mantener consistencia y evitar conflictos de dependencias.

### 0. Verificar Entorno (Recomendado)
```bash
# Script de verificación completa
./check_env.sh

# Verificación manual rápida
source setup_env.sh
echo $VIRTUAL_ENV  # Debe mostrar: .../venv_hailo_rpi_examples
```

### 2. Iniciar Sistema
```bash
# Opción 1: Script interactivo (recomendado) - Maneja el venv automáticamente
./start_counter.sh

# Opción 2: Manual - Asegúrate de activar el entorno primero
source setup_env.sh
python3 people_counter.py --input rpi --use-frame
```

## 📖 Guía de Uso

### Tipos de Entrada Soportados

**⚠️ Todos los comandos deben ejecutarse con el entorno virtual activado:**
```bash
source setup_env.sh  # Activa venv_hailo_rpi_examples
```

#### 🔹 Cámara Raspberry Pi
```bash
python3 people_counter.py --input rpi --use-frame
```

#### 🔹 Cámara USB/Webcam  
```bash
python3 people_counter.py --input usb --use-frame
```

#### 🔹 RTSP Stream (Para cámaras IP)
```bash
python3 people_counter.py --rtsp-url "rtsp://usuario:password@192.168.1.100:554/stream" --use-frame
```

#### 🔹 Archivo de Video
```bash
python3 people_counter.py --input "/ruta/al/video.mp4" --use-frame
```

#### 🔹 Solo Dashboard Web
```bash
python3 dashboard.py
# Visita: http://localhost:5000
```

### 🎛️ Parámetros del Sistema

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--input` | Fuente de entrada | `rpi`, `usb`, `/path/video.mp4` |
| `--rtsp-url` | URL completa RTSP | `rtsp://user:pass@ip:port/stream` |
| `--use-frame` | Mostrar video con overlay | Flag opcional |

## ⚙️ Configuración

### Zonas de Conteo
Edita las zonas en `people_counter.py`:

```python
class PersonCounterConfig:
    def __init__(self):
        # Línea de entrada (verde)
        self.entry_line = {"y": 200, "x1": 100, "x2": 500}
        
        # Línea de salida (roja) 
        self.exit_line = {"y": 400, "x1": 100, "x2": 500}
        
        # Umbral de confianza (0.0 - 1.0)
        self.confidence_threshold = 0.7
```

### Parámetros Avanzados
- **`confidence_threshold`**: Confianza mínima para detecciones (0.7 por defecto)
- **`tracking_timeout`**: Frames antes de limpiar track perdido (30 frames)

## 📊 Dashboard Web

### Acceso
- **URL**: http://localhost:5000
- **Puerto**: 5000 (configurable en `dashboard.py`)

### Funciones del Dashboard
- 📈 **Estadísticas en Tiempo Real**: Entradas, salidas, personas actuales
- ⏰ **Actividad por Hora**: Gráfico de barras del día actual  
- 📋 **Eventos Recientes**: Últimas 10 detecciones con timestamp
- 🔄 **Reset de Contadores**: Función para reiniciar estadísticas
- 🟢 **Indicador de Estado**: Monitoreo de conexión en tiempo real

## 📁 Archivos Generados

### `counter_stats.json`
Estadísticas actuales del sistema:
```json
{
  "total_entries": 45,
  "total_exits": 42,
  "current_people": 3,
  "last_update": "2025-01-XX...",
  "session_start": "2025-01-XX..."
}
```

### `counter_log.json`
Log detallado de eventos (últimos 1000):
```json
[
  {
    "timestamp": "2025-01-XX...",
    "type": "entry",
    "track_id": 123,
    "position": {"x": 350, "y": 200},
    "total_entries": 45,
    "total_exits": 42,
    "current_people": 3
  }
]
```

## 🔧 Troubleshooting

### Entorno Virtual

#### Error: "Entorno virtual no está activo"
```bash
# Solución: Activar el entorno virtual correcto
source setup_env.sh

# Verificar que esté activo
echo $VIRTUAL_ENV  # Debe mostrar venv_hailo_rpi_examples
```

#### Error: "ModuleNotFoundError"
```bash
# Instalar dependencias en el venv correcto
source setup_env.sh
pip install -r requirements_counter.txt
```

### Problemas Comunes

#### No se detectan personas
- ✅ Verificar que `--use-frame` esté activo para ver detecciones
- ✅ Ajustar `confidence_threshold` si hay muchas detecciones falsas
- ✅ Comprobar que la cámara tenga buena iluminación

#### RTSP no conecta
- ✅ Verificar URL, usuario y contraseña
- ✅ Comprobar que la cámara soporte RTSP
- ✅ Testear URL en VLC Media Player primero

#### Dashboard sin datos
- ✅ Verificar que `people_counter.py` esté ejecutándose
- ✅ Comprobar que los archivos JSON se estén generando
- ✅ Revisar permisos de escritura en el directorio

#### Video muy lento/choppy
- ✅ Reducir resolución de entrada
- ✅ Quitar `--use-frame` para modo solo conteo
- ✅ Verificar carga CPU con `htop`

### Logs y Debugging
```bash
# Ver estadísticas en tiempo real
tail -f counter_log.json

# Monitorear rendimiento Hailo
hailortcli monitor

# Verificar carga del sistema
htop
```

## 🎯 Casos de Uso

### 🏢 Oficinas y Edificios
- Control de aforo por COVID-19
- Estadísticas de ocupación
- Optimización de espacios

### 🛒 Tiendas y Retail  
- Análisis de flujo de clientes
- Horarios pico de actividad
- Conversión entrada-compra

### 🎓 Centros Educativos
- Control de acceso a aulas
- Estadísticas de asistencia
- Seguridad estudiantil

### 🏥 Centros de Salud
- Gestión de salas de espera
- Control de visitantes
- Cumplimiento de normativas

## 📋 Arquitectura del Sistema

```
RTSP/Camera → Hailo AI Detection → Person Tracking → Zone Analysis → Counter Logic → Dashboard/API
```

### Componentes Principales
1. **`people_counter.py`**: Motor principal de detección y conteo
2. **`dashboard.py`**: Interface web para monitoreo
3. **`PersonCounter`**: Lógica de conteo y persistencia
4. **`PersonCounterCallback`**: Callback de GStreamer optimizado

## 🤝 Soporte

### Comunidad Hailo
- [Foro Oficial](https://community.hailo.ai/)
- [Documentación](https://hailo.ai/developer-zone/documentation/)
- [GitHub](https://github.com/hailo-ai/hailo-rpi5-examples)

### Desarrollo Local
```bash
# Debugger en código Python
import ipdb; ipdb.set_trace()

# Monitoreo Hailo
export HAILO_MONITOR=1
hailortcli monitor
```

---

**🎉 ¡Sistema completamente funcional y listo para producción!**

El contador utiliza la máxima precisión del procesador Hailo AI con tracking único de personas, garantizando conteos exactos sin duplicaciones. Dashboard web incluido para monitoreo profesional en tiempo real.
