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
        print(f"🔧 Construyendo pipeline RTSP personalizado...")
        
        # Obtener el pipeline padre completo
        parent_pipeline = super().get_pipeline_string()
        print(f"🔍 Pipeline padre obtenido: {parent_pipeline[:100]}...")
        
        # Construir pipeline RTSP desde cero, manteniendo la estructura del padre
        # pero reemplazando la fuente
        rtsp_pipeline = (
            f'rtspsrc location="{self.rtsp_url}" protocols=tcp latency=300 '
            f'! rtph264depay '
            f'! h264parse '
            f'! avdec_h264 '
            f'! queue name=source_queue_decode leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 '
            f'! videoscale name=source_videoscale n-threads=2 '
            f'! queue name=source_convert_q leaky=no max-size-buffers=3 max-size-bytes=0 max-size-time=0 '
            f'! videoconvert n-threads=3 name=source_convert qos=false '
            f'! video/x-raw, pixel-aspect-ratio=1/1, format=RGB, width=1280, height=720 '
            f'! videorate name=source_videorate '
            f'! capsfilter name=source_fps_caps caps="video/x-raw, framerate=30/1" '
        )
        
        # Encontrar donde empieza la parte de inferencia en el pipeline padre
        inference_start = parent_pipeline.find('! queue name=inference_wrapper_input_q')
        
        if inference_start != -1:
            # Tomar la parte de inferencia del pipeline padre
            inference_pipeline = parent_pipeline[inference_start:]
            
            # Combinar RTSP + inferencia
            complete_pipeline = rtsp_pipeline + inference_pipeline
            
            print("✅ Pipeline RTSP configurado exitosamente")
            print(f"🎯 Pipeline completo: {complete_pipeline[:150]}...")
            return complete_pipeline
        else:
            print("⚠️  No se pudo encontrar punto de inferencia, usando fallback")
            print("🔧 Intentando método alternativo...")
            
            # Método alternativo: reemplazar directamente la fuente
            if 'filesrc' in parent_pipeline:
                # Encontrar el final de la sección de fuente
                decode_end = parent_pipeline.find('! queue name=source_scale_q')
                if decode_end != -1:
                    rest_pipeline = parent_pipeline[decode_end:]
                    alternative_pipeline = rtsp_pipeline + rest_pipeline
                    print("✅ Pipeline alternativo RTSP configurado")
                    return alternative_pipeline
            
            print("❌ Fallback al pipeline original")
            return parent_pipeline

# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.new_variable = 42  # New variable example
        self.detection_polygon = []  # Polígono de delimitación
        self.load_detection_areas()
        
        # 🔧 FORZAR use_frame para que funcione el polígono
        self.use_frame = True
        print(f"🖼️ Forzando use_frame = {self.use_frame}")

    def load_detection_areas(self):
        """Cargar el polígono de detección desde counter_areas.json"""
        try:
            # Buscar el archivo counter_areas.json en el directorio del proyecto
            project_root = Path(__file__).resolve().parent.parent
            areas_file = project_root / "counter_areas.json"
            
            print(f"🔍 Buscando archivo de áreas: {areas_file}")
            
            if areas_file.exists():
                with open(areas_file, 'r') as f:
                    areas_data = json.load(f)
                
                # Cargar el polígono de detección
                self.detection_polygon = np.array(areas_data.get('detection_polygon', []), dtype=np.int32)
                print(f"✅ Polígono de detección cargado: {len(self.detection_polygon)} puntos")
                print(f"📐 Puntos del polígono: {self.detection_polygon[:3]}... (mostrando primeros 3)")
            else:
                print("⚠️  Archivo counter_areas.json no encontrado")
                
        except Exception as e:
            print(f"❌ Error cargando áreas de detección: {e}")
            self.detection_polygon = []

    def draw_polygon(self, frame):
        """Dibujar el polígono de delimitación en el frame"""
        if len(self.detection_polygon) > 0:
            # Debug: Imprimir información del polígono
            if hasattr(self, '_debug_count'):
                self._debug_count += 1
            else:
                self._debug_count = 1
                
            if self._debug_count <= 2:  # Solo los primeros 2 intentos
                print(f"🎨 Dibujando polígono: frame shape {frame.shape}, polígono: {len(self.detection_polygon)} puntos")
                print(f"📍 Primeros puntos: {self.detection_polygon[:3].tolist()}")
            
            # Dibujar polígono con línea verde gruesa y visible
            cv2.polylines(frame, [self.detection_polygon], True, (0, 255, 0), 3)
            
            # Agregar texto informativo más visible
            cv2.putText(frame, f"AREA DELIMITADA ({len(self.detection_polygon)} puntos)", 
                       (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 3)
                       
            # Dibujar un punto en la primera coordenada para verificar visibilidad
            if len(self.detection_polygon) > 0:
                first_point = tuple(self.detection_polygon[0])
                cv2.circle(frame, first_point, 8, (0, 255, 255), -1)  # Círculo amarillo

    def new_function(self):  # New function example
        return "The meaning of life is: "

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
        # Debug: Verificar que el frame se obtiene correctamente
        if user_data.get_count() <= 3:  # Solo los primeros 3 frames
            print(f"🖼️  Frame obtenido: {frame.shape if frame is not None else 'None'}, use_frame: {user_data.use_frame}")
            print(f"📐 Polígono tiene {len(user_data.detection_polygon)} puntos")

    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # Parse the detections
    detection_count = 0
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        if label == "person":
            # Get track ID
            track_id = 0
            track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            if len(track) == 1:
                track_id = track[0].get_id()
            string_to_print += (f"Detection: ID: {track_id} Label: {label} Confidence: {confidence:.2f}\n")
            detection_count += 1
    if user_data.use_frame:
        # Debug: Confirmar que estamos procesando el frame
        if user_data.get_count() <= 3:
            print(f"✅ Procesando frame {user_data.get_count()} para dibujar polígono")
            
        # Note: using imshow will not work here, as the callback function is not running in the main thread
        # Let's print the detection count to the frame
        cv2.putText(frame, f"Detections: {detection_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        # Example of how to use the new_variable and new_function from the user_data
        # Let's print the new_variable and the result of the new_function to the frame
        cv2.putText(frame, f"{user_data.new_function()} {user_data.new_variable}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 🎯 DIBUJAR POLÍGONO DE DELIMITACIÓN
        user_data.draw_polygon(frame)
        
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
