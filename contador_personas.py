import os
from pathlib import Path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import hailo
import cv2
import numpy as np
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer

# Clase personalizada para el conteo de personas
class ContadorPersonasCallback(app_callback_class):
    def __init__(self):
        super().__init__()
        # Activar el uso de frames para visualización
        self.use_frame = True
        # Línea de conteo (posición vertical en la imagen normalizada 0-1)
        self.linea_conteo = 0.5
        # Contadores de personas
        self.entradas = 0
        self.salidas = 0
        # Diccionario para seguimiento de IDs
        self.tracking_dict = {}
        # Umbral de confianza para detecciones
        self.umbral_confianza = 0.5
        # Procesamiento de frames (procesar 1 de cada N frames)
        self.frame_skip = 2
        # Historial de posiciones para suavizado
        self.historial_posiciones = {}
        # Tamaño máximo del historial
        self.max_historial = 3

# Función de callback para procesar cada frame
def app_callback(pad, info, user_data):
    # Obtener el buffer del frame
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Incrementar contador de frames
    user_data.increment()
    
    # Saltar frames para optimizar rendimiento
    if user_data.get_count() % user_data.frame_skip != 0:
        return Gst.PadProbeReturn.OK
    
    # Obtener información del formato de video
    format, width, height = get_caps_from_pad(pad)
    
    # Obtener el frame como array de numpy
    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        frame = get_numpy_from_buffer(buffer, format, width, height)
    
    # Obtener las detecciones del buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    
    # Posición de la línea de conteo en píxeles
    linea_y = int(height * user_data.linea_conteo)
    
    # Dibujar línea de conteo si tenemos frame
    if frame is not None:
        cv2.line(frame, (0, linea_y), (width, linea_y), (0, 255, 255), 2)
    
    # Procesar cada detección
    for detection in detections:
        label = detection.get_label()
        confidence = detection.get_confidence()
        
        # Solo procesar personas con confianza superior al umbral
        if label == "person" and confidence > user_data.umbral_confianza:
            # Obtener bounding box
            bbox = detection.get_bbox()
            x_min = int(bbox.xmin() * width)
            y_min = int(bbox.ymin() * height)
            x_max = int(bbox.xmax() * width)
            y_max = int(bbox.ymax() * height)
            
            # Obtener ID de tracking
            track_id = 0
            track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            if len(track) == 1:
                track_id = track[0].get_id()
            
            # Calcular centro de la persona
            centro_y = (y_min + y_max) / 2
            
            # Lógica de conteo con suavizado
            if track_id > 0:
                # Actualizar historial de posiciones
                if track_id not in user_data.historial_posiciones:
                    user_data.historial_posiciones[track_id] = []
                
                # Agregar posición actual al historial
                user_data.historial_posiciones[track_id].append(centro_y)
                
                # Mantener tamaño máximo del historial
                if len(user_data.historial_posiciones[track_id]) > user_data.max_historial:
                    user_data.historial_posiciones[track_id].pop(0)
                
                # Calcular posición promedio para suavizar movimiento
                posicion_suavizada = sum(user_data.historial_posiciones[track_id]) / len(user_data.historial_posiciones[track_id])
                
                # Verificar si hay suficiente historial para determinar dirección
                if track_id in user_data.tracking_dict and len(user_data.historial_posiciones[track_id]) >= 2:
                    # Posición anterior
                    prev_y = user_data.tracking_dict[track_id]
                    
                    # Verificar si cruzó la línea (usando posición suavizada)
                    if prev_y < linea_y and posicion_suavizada >= linea_y:
                        user_data.salidas += 1
                    elif prev_y >= linea_y and posicion_suavizada < linea_y:
                        user_data.entradas += 1
                
                # Actualizar posición de seguimiento
                user_data.tracking_dict[track_id] = posicion_suavizada
            
            # Dibujar bounding box y ID si tenemos frame
            if frame is not None:
                # Dibujar rectángulo
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                # Mostrar ID y confianza
                texto = f"ID:{track_id} ({confidence:.2f})"
                cv2.putText(frame, texto, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Mostrar contadores en el frame
    if frame is not None:
        cv2.putText(frame, f"Entradas: {user_data.entradas}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Salidas: {user_data.salidas}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Convertir frame a BGR para visualización
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)
    
    # Imprimir estadísticas
    print(f"Frame: {user_data.get_count()} | Entradas: {user_data.entradas} | Salidas: {user_data.salidas}")
    
    return Gst.PadProbeReturn.OK

# Clase para la aplicación de detección con RTSP
class GStreamerRTSPDetectionApp:
    def __init__(self, callback, user_data, rtsp_url):
        self.callback = callback
        self.user_data = user_data
        self.rtsp_url = rtsp_url
        self.pipeline = None
        self.loop = None
        
    def build_pipeline(self):
        # Inicializar GStreamer
        Gst.init(None)
        
        # Crear pipeline
        pipeline_str = (
            f"rtspsrc location={self.rtsp_url} latency=100 ! "
            "rtph264depay ! h264parse ! avdec_h264 ! "
            "videoconvert ! videoscale ! "
            "video/x-raw,format=RGB ! "
            "hailonet hef-path=/usr/lib/hailo-post-processes/yolov5m.hef ! "
            "hailofilter function-name=yolov5 ! "
            "hailotracker name=hailo_tracker tracking-type=1 ! "
            "queue ! videoconvert ! appsink name=hailo_sink"
        )
        
        self.pipeline = Gst.parse_launch(pipeline_str)
        
        # Obtener el sink y añadir el callback
        sink = self.pipeline.get_by_name("hailo_sink")
        sink.set_property("emit-signals", True)
        sink.set_property("sync", False)
        sink.set_property("drop", True)
        sink.set_property("max-buffers", 1)
        
        # Añadir probe para el callback
        sinkpad = sink.get_static_pad("sink")
        sinkpad.add_probe(Gst.PadProbeType.BUFFER, self.callback, self.user_data)
        
        return self.pipeline
        
    def run(self):
        # Construir pipeline
        self.pipeline = self.build_pipeline()
        
        # Crear loop
        self.loop = GLib.MainLoop()
        
        # Conectar señales de bus
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self.on_error)
        bus.connect("message::eos", self.on_eos)
        
        # Iniciar pipeline
        self.pipeline.set_state(Gst.State.PLAYING)
        
        try:
            # Ejecutar loop
            self.loop.run()
        except KeyboardInterrupt:
            pass
        finally:
            # Limpiar recursos
            self.pipeline.set_state(Gst.State.NULL)
    
    def on_error(self, bus, message):
        err, debug = message.parse_error()
        print(f"Error: {err}, {debug}")
        if self.loop:
            self.loop.quit()
    
    def on_eos(self, bus, message):
        print("End of stream")
        if self.loop:
            self.loop.quit()

if __name__ == "__main__":
    # Configurar variables de entorno
    project_root = Path(__file__).resolve().parent
    env_file = project_root / ".env"
    env_path_str = str(env_file)
    os.environ["HAILO_ENV_FILE"] = env_path_str
    
    import argparse
    
    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Contador de personas usando Hailo AI Kit y RTSP')
    parser.add_argument('--rtsp', type=str, 
                        default="rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif",
                        help='URL del stream RTSP')
    parser.add_argument('--linea', type=float, default=0.5,
                        help='Posición de la línea de conteo (0-1, normalizada)')
    parser.add_argument('--umbral', type=float, default=0.5,
                        help='Umbral de confianza para detecciones (0-1)')
    parser.add_argument('--skip', type=int, default=2,
                        help='Procesar 1 de cada N frames')
    args = parser.parse_args()
    
    # Crear instancia de la clase de callback
    user_data = ContadorPersonasCallback()
    user_data.linea_conteo = args.linea
    user_data.umbral_confianza = args.umbral
    user_data.frame_skip = args.skip
    
    print(f"Iniciando contador de personas con:")
    print(f"  - URL RTSP: {args.rtsp}")
    print(f"  - Línea de conteo: {args.linea}")
    print(f"  - Umbral de confianza: {args.umbral}")
    print(f"  - Procesando 1 de cada {args.skip} frames")
    
    # Crear aplicación y ejecutar
    app = GStreamerRTSPDetectionApp(app_callback, user_data, args.rtsp)
    app.run()
