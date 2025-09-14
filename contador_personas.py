from pathlib import Path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import numpy as np
import cv2
import hailo
import argparse

from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp

# Clase para el conteo de personas
class PersonCounterCallback(app_callback_class):
    def __init__(self):
        super().__init__()
        # Contadores
        self.total_count = 0
        self.entrada_count = 0
        self.salida_count = 0
        
        # Línea virtual (porcentaje de la altura de la imagen)
        self.line_position = 0.5  # Mitad de la imagen
        
        # Seguimiento de personas
        self.tracked_people = {}  # {track_id: {"last_y": y_position, "counted": False}}
        
        # Para visualización
        self.line_color = (0, 255, 255)  # Amarillo
        self.line_thickness = 2

# Función de callback para procesar cada frame
def app_callback(pad, info, user_data):
    # Obtener el buffer del frame
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Incrementar contador de frames
    user_data.increment()
    
    # Obtener información del frame
    format, width, height = get_caps_from_pad(pad)
    
    # Posición de la línea virtual
    line_y = int(height * user_data.line_position)
    
    # Obtener frame si está habilitado
    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        frame = get_numpy_from_buffer(buffer, format, width, height)
        # Dibujar línea virtual
        cv2.line(frame, (0, line_y), (width, line_y), user_data.line_color, user_data.line_thickness)
    
    # Obtener detecciones
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    
    # Contar personas detectadas en este frame
    current_count = 0
    
    # Procesar cada detección
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        
        # Solo procesar personas
        if label == "person" and confidence > 0.5:
            current_count += 1
            
            # Obtener ID de seguimiento
            track_id = 0
            track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            if len(track) == 1:
                track_id = track[0].get_id()
                
                # Calcular centro del bounding box
                y_center = (bbox.ymin() + bbox.ymax()) * height / 2
                
                # Verificar si ya estamos siguiendo a esta persona
                if track_id in user_data.tracked_people:
                    last_y = user_data.tracked_people[track_id]["last_y"]
                    counted = user_data.tracked_people[track_id]["counted"]
                    
                    # Si no ha sido contada y cruza la línea
                    if not counted:
                        if last_y < line_y and y_center >= line_y:
                            # Cruce de arriba hacia abajo (entrada)
                            user_data.entrada_count += 1
                            user_data.tracked_people[track_id]["counted"] = True
                        elif last_y > line_y and y_center <= line_y:
                            # Cruce de abajo hacia arriba (salida)
                            user_data.salida_count += 1
                            user_data.tracked_people[track_id]["counted"] = True
                
                # Actualizar posición
                user_data.tracked_people[track_id] = {
                    "last_y": y_center,
                    "counted": user_data.tracked_people.get(track_id, {}).get("counted", False)
                }
                
                # Dibujar bounding box y ID si el frame está disponible
                if user_data.use_frame:
                    x1, y1 = int(bbox.xmin() * width), int(bbox.ymin() * height)
                    x2, y2 = int(bbox.xmax() * width), int(bbox.ymax() * height)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Actualizar contador total
    user_data.total_count = max(user_data.total_count, current_count)
    
    # Mostrar contadores en el frame
    if user_data.use_frame:
        cv2.putText(frame, f"Total: {user_data.total_count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Entradas: {user_data.entrada_count}", (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Salidas: {user_data.salida_count}", (10, 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Convertir frame a BGR y guardarlo
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)
    
    # Imprimir estadísticas
    print(f"Frame: {user_data.get_count()} | Total: {user_data.total_count} | Entradas: {user_data.entrada_count} | Salidas: {user_data.salida_count}")
    
    return Gst.PadProbeReturn.OK

if __name__ == "__main__":
    # Parsear argumentos
    parser = argparse.ArgumentParser(description='Contador de personas con RTSP')
    parser.add_argument('--rtsp', type=str, help='URL del stream RTSP (ej: rtsp://usuario:contraseña@ip:puerto/stream)')
    parser.add_argument('--line-position', type=float, default=0.5, help='Posición de la línea virtual (0-1, porcentaje de la altura)')
    args = parser.parse_args()
    
    # Configurar variables de entorno
    project_root = Path(__file__).resolve().parent
    env_file = project_root / ".env"
    env_path_str = str(env_file)
    os.environ["HAILO_ENV_FILE"] = env_path_str
    
    # Si se proporciona una URL RTSP, configurarla
    if args.rtsp:
        os.environ["HAILO_SOURCE"] = args.rtsp
    
    # Crear instancia del contador
    user_data = PersonCounterCallback()
    user_data.line_position = args.line_position
    
    # Iniciar aplicación
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()
