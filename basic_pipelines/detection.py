from pathlib import Path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import numpy as np
import cv2
import hailo
import json

from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp

# -----------------------------------------------------------------------------------------------
# Custom RTSP Detection App - Contador de Personas
# -----------------------------------------------------------------------------------------------
class RTSPGStreamerDetectionApp(GStreamerDetectionApp):
    def __init__(self, app_callback, user_data, rtsp_url):
        # IMPORTANTE: Asignar rtsp_url ANTES de llamar al constructor padre
        # porque el padre llama a get_pipeline_string() durante la inicialización
        self.rtsp_url = rtsp_url
        print(f"🎯 Configurando pipeline RTSP personalizado para: {rtsp_url}")
        super().__init__(app_callback, user_data)
    
    def get_pipeline_string(self):
        """
        Custom pipeline que usa rtspsrc en lugar de filesrc para RTSP streams
        """
        # Construcción del pipeline personalizado para RTSP
        rtsp_source = f"rtspsrc location=\"{self.rtsp_url}\" protocols=tcp ! decodebin"
        
        # Usar los mismos pipelines de la clase padre para el resto del procesamiento
        parent_pipeline = super().get_pipeline_string()
        
        # Reemplazar la parte de filesrc con nuestro rtspsrc
        # Encontrar donde termina la fuente original
        source_end = parent_pipeline.find('caps="video/x-raw, framerate=30/1"')
        if source_end != -1:
            # Tomar solo la parte después de la fuente original
            rest_of_pipeline = parent_pipeline[source_end + len('caps="video/x-raw, framerate=30/1"'):]
            
            # Construir el pipeline completo con RTSP
            custom_pipeline = (
                f'{rtsp_source} ! '
                f'queue name=source_queue_decode leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! '
                f'videoscale name=source_videoscale n-threads=2 ! '
                f'queue name=source_convert_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 ! '
                f'videoconvert n-threads=3 name=source_convert qos=false ! '
                f'video/x-raw, pixel-aspect-ratio=1/1, format=RGB, width=1280, height=720 ! '
                f'videorate name=source_videorate ! '
                f'capsfilter name=source_fps_caps caps="video/x-raw, framerate=30/1" '
                f'{rest_of_pipeline}'
            )
            
            print("🔧 Pipeline RTSP configurado correctamente")
            return custom_pipeline
        else:
            print("⚠️  Fallback al pipeline original")
            return parent_pipeline

# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.new_variable = 42  # New variable example
        
        # ROI Optimization - Cargar polígono de detección
        self.detection_polygon = []
        self.polygon_mask = None
        self.roi_bbox = None
        self.load_detection_areas()

    def new_function(self):  # New function example
        return "The meaning of life is: "
    
    def load_detection_areas(self):
        """Carga el polígono de detección desde counter_areas.json"""
        try:
            # Buscar el archivo desde la raíz del proyecto
            project_root = Path(__file__).resolve().parent.parent
            areas_file = project_root / "counter_areas.json"
            
            if areas_file.exists():
                with open(areas_file, 'r') as f:
                    areas_data = json.load(f)
                
                self.detection_polygon = np.array(areas_data["detection_polygon"], dtype=np.int32)
                
                # Calcular bounding rectangle para crop inicial eficiente
                x, y, w, h = cv2.boundingRect(self.detection_polygon)
                self.roi_bbox = (x, y, w, h)
                
                print(f"🎯 ROI optimizado cargado: {len(self.detection_polygon)} puntos")
                print(f"📐 Bounding rect: x={x}, y={y}, w={w}, h={h}")
                print(f"🔍 Primeros 3 puntos del polígono: {self.detection_polygon[:3]}")
                print(f"🔍 Últimos 3 puntos del polígono: {self.detection_polygon[-3:]}")
                
            else:
                print("⚠️  Archivo counter_areas.json no encontrado, usando frame completo")
                
        except Exception as e:
            print(f"❌ Error cargando áreas de detección: {e}")
            print("⚠️  Continuando con frame completo")
    
    def create_polygon_mask(self, frame_shape):
        """Crear máscara del polígono para filtering preciso"""
        if len(self.detection_polygon) == 0:
            return None
            
        height, width = frame_shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Llenar el polígono con 255 (blanco = área válida)
        cv2.fillPoly(mask, [self.detection_polygon], 255)
        
        return mask
    
    def is_detection_in_roi(self, bbox):
        """Verificar si el centro de una detección está dentro del polígono"""
        if len(self.detection_polygon) == 0:
            return True  # Si no hay polígono, todo es válido
            
        # Calcular centro del bbox
        center_x = int(bbox.xmin() + (bbox.width() / 2))
        center_y = int(bbox.ymin() + (bbox.height() / 2))
        
        # Usar pointPolygonTest de OpenCV
        result = cv2.pointPolygonTest(self.detection_polygon, (center_x, center_y), False)
        return result >= 0  # >= 0 significa dentro o en el borde

# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------

# This is the callback function that will be called when data is available from the pipeline
def app_callback(pad, info, user_data):
    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()
    # Check if the buffer is valid
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Using the user_data to count the number of frames
    user_data.increment()
    string_to_print = f"Frame count: {user_data.get_count()}\n"

    # Get the caps from the pad
    format, width, height = get_caps_from_pad(pad)

    # If the user_data.use_frame is set to True, we can get the video frame from the buffer
    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        # Get video frame
        frame = get_numpy_from_buffer(buffer, format, width, height)
        
        # DEBUG: Info del frame cada 30 frames para no saturar logs
        if user_data.get_count() % 30 == 0:
            print(f"🔍 Frame info: {frame.shape if frame is not None else 'None'}, format: {format}, w: {width}, h: {height}")
            print(f"🔍 Polígono cargado: {len(user_data.detection_polygon)} puntos")

    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # Parse the detections con ROI filtering
    detection_count = 0
    roi_detection_count = 0
    total_persons = 0
    
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        
        if label == "person":
            total_persons += 1
            
            # DEBUG: Info de detecciones cada cierto tiempo
            center_x = int(bbox.xmin() + (bbox.width() / 2))
            center_y = int(bbox.ymin() + (bbox.height() / 2))
            
            if user_data.get_count() % 30 == 0:  # Debug cada 30 frames
                string_to_print += (f"🔍 Persona detectada en: ({center_x}, {center_y}), bbox: {bbox.xmin():.0f},{bbox.ymin():.0f},{bbox.width():.0f},{bbox.height():.0f}\n")
            
            # ROI OPTIMIZATION: Solo procesar si está dentro del polígono
            if user_data.is_detection_in_roi(bbox):
                # Get track ID
                track_id = 0
                track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
                if len(track) == 1:
                    track_id = track[0].get_id()
                
                string_to_print += (f"ROI Detection: ID: {track_id} Label: {label} Confidence: {confidence:.2f}\n")
                roi_detection_count += 1
            else:
                # Persona detectada pero fuera del ROI (filtrada para ahorrar recursos)
                if user_data.get_count() % 30 == 0:  # Debug cada 30 frames
                    string_to_print += (f"🔍 Persona FUERA del ROI en: ({center_x}, {center_y})\n")
    
    detection_count = roi_detection_count
    
    # Estadísticas de optimización
    if total_persons > 0:
        efficiency = (roi_detection_count / total_persons) * 100
        string_to_print += f"📊 Optimización ROI: {roi_detection_count}/{total_persons} personas procesadas ({efficiency:.1f}%)\n"
    if user_data.use_frame:
        # Note: using imshow will not work here, as the callback function is not running in the main thread
        
        # Visualización del ROI - Dibujar polígono de detección
        if len(user_data.detection_polygon) > 0:
            # DEBUG: Verificar dimensiones cada 30 frames
            if user_data.get_count() % 30 == 0:
                print(f"🔍 Dibujando polígono en frame shape: {frame.shape}")
                print(f"🔍 Rango polígono X: {user_data.detection_polygon[:, 0].min()}-{user_data.detection_polygon[:, 0].max()}")
                print(f"🔍 Rango polígono Y: {user_data.detection_polygon[:, 1].min()}-{user_data.detection_polygon[:, 1].max()}")
            
            # Dibujar polígono con líneas semi-transparentes
            overlay = frame.copy()
            cv2.fillPoly(overlay, [user_data.detection_polygon], (0, 255, 255))  # Amarillo
            cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)  # Transparencia 10%
            
            # Contorno del polígono más visible
            cv2.polylines(frame, [user_data.detection_polygon], True, (0, 255, 255), 3)  # Amarillo, línea más gruesa
            
            # Etiqueta del ROI
            cv2.putText(frame, "ROI ACTIVO", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            # DEBUG: Si no hay polígono
            if user_data.get_count() % 30 == 0:
                print(f"🔍 NO HAY POLÍGONO CARGADO para dibujar")
        
        # Mostrar contadores optimizados
        cv2.putText(frame, f"ROI Detections: {roi_detection_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Total Persons: {total_persons}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        
        # Estadística de eficiencia en el frame
        if total_persons > 0:
            efficiency = (roi_detection_count / total_persons) * 100
            cv2.putText(frame, f"Efficiency: {efficiency:.1f}%", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
        
        # Convert the frame to BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)

    print(string_to_print)
    return Gst.PadProbeReturn.OK

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    env_file     = project_root / ".env"
    env_path_str = str(env_file)
    os.environ["HAILO_ENV_FILE"] = env_path_str
    
    # Hardcoded RTSP URL for people counter
    rtsp_url = "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
    
    # Configure sys.argv for our custom RTSP app
    import sys
    sys.argv = [sys.argv[0], "--use-frame", "--show-fps"]
    
    print(f"🎥 Conectando a cámara RTSP: {rtsp_url}")
    print("📊 Sistema de conteo de personas iniciando...")
    print("🚀 Usando pipeline RTSP personalizado...")
    
    # Create an instance of the user app callback class
    user_data = user_app_callback_class()
    
    # Use our custom RTSP Detection App instead of the standard one
    app = RTSPGStreamerDetectionApp(app_callback, user_data, rtsp_url)
    app.run()
