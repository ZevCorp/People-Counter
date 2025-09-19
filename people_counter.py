#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Conteo de Personas en Tiempo Real
Basado en Hailo AI y soporte RTSP

REQUISITOS:
- Debe ejecutarse desde el entorno virtual venv_hailo_rpi_examples
- Ejecutar: source setup_env.sh antes de usar este script
- Compatible con ejemplos oficiales de Hailo RPi5
"""

from pathlib import Path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import numpy as np
import cv2
import hailo
import json
import time
import threading
from datetime import datetime
import argparse

from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from hailo_apps.hailo_app_python.apps.detection.detection_pipeline import GStreamerDetectionApp

# -----------------------------------------------------------------------------------------------
# Configuración del Sistema de Conteo
# -----------------------------------------------------------------------------------------------

class PersonCounterConfig:
    """Configuración del contador de personas"""
    def __init__(self):
        # Zonas de conteo (formato: x1, y1, x2, y2 - líneas horizontales)
        self.entry_line = {"y": 200, "x1": 100, "x2": 500}  # Línea de entrada
        self.exit_line = {"y": 400, "x1": 100, "x2": 500}   # Línea de salida
        
        # Parámetros de detección
        self.confidence_threshold = 0.7
        self.tracking_timeout = 30  # frames sin detección antes de limpiar track
        
        # Archivos de datos
        self.stats_file = "counter_stats.json"
        self.log_file = "counter_log.json"

# -----------------------------------------------------------------------------------------------
# Clase Principal del Contador
# -----------------------------------------------------------------------------------------------

class PersonCounter:
    """Lógica principal del contador de personas"""
    
    def __init__(self, config):
        self.config = config
        self.tracked_persons = {}  # {track_id: {"last_y": y, "direction": None, "frames_missing": 0}}
        self.total_entries = 0
        self.total_exits = 0
        self.current_people = 0
        self.session_start = datetime.now()
        
        # Cargar estadísticas previas si existen
        self.load_stats()
        
    def load_stats(self):
        """Cargar estadísticas guardadas"""
        try:
            if os.path.exists(self.config.stats_file):
                with open(self.config.stats_file, 'r') as f:
                    data = json.load(f)
                    self.total_entries = data.get('total_entries', 0)
                    self.total_exits = data.get('total_exits', 0)
                    self.current_people = data.get('current_people', 0)
                    print(f"📊 Estadísticas cargadas: {self.total_entries} entradas, {self.total_exits} salidas, {self.current_people} personas actuales")
        except Exception as e:
            print(f"⚠️  Error cargando estadísticas: {e}")
    
    def save_stats(self):
        """Guardar estadísticas actuales"""
        try:
            stats = {
                'total_entries': self.total_entries,
                'total_exits': self.total_exits,
                'current_people': self.current_people,
                'last_update': datetime.now().isoformat(),
                'session_start': self.session_start.isoformat()
            }
            with open(self.config.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error guardando estadísticas: {e}")
    
    def log_event(self, event_type, track_id, position):
        """Registrar evento de entrada/salida"""
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'track_id': track_id,
                'position': position,
                'total_entries': self.total_entries,
                'total_exits': self.total_exits,
                'current_people': self.current_people
            }
            
            # Leer log existente o crear nuevo
            log_data = []
            if os.path.exists(self.config.log_file):
                with open(self.config.log_file, 'r') as f:
                    log_data = json.load(f)
            
            log_data.append(event)
            
            # Mantener solo los últimos 1000 eventos
            if len(log_data) > 1000:
                log_data = log_data[-1000:]
                
            with open(self.config.log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Error guardando log: {e}")
    
    def update_person_tracking(self, track_id, bbox, confidence):
        """Actualizar seguimiento de persona"""
        if confidence < self.config.confidence_threshold:
            return
            
        # Obtener centro Y del bounding box
        center_y = bbox.ymin() + (bbox.ymax() - bbox.ymin()) / 2
        center_x = bbox.xmin() + (bbox.xmax() - bbox.xmin()) / 2
        
        # Verificar si la persona está en la zona de conteo (entre líneas)
        entry_y = self.config.entry_line["y"]
        exit_y = self.config.exit_line["y"]
        
        if track_id in self.tracked_persons:
            # Persona ya siendo rastreada
            person = self.tracked_persons[track_id]
            last_y = person["last_y"]
            person["frames_missing"] = 0  # Resetear contador de frames perdidos
            
            # Detectar cruce de líneas
            if person["direction"] is None:
                # Determinar dirección inicial
                if abs(center_y - entry_y) < abs(center_y - exit_y):
                    person["direction"] = "towards_exit"
                else:
                    person["direction"] = "towards_entry"
            
            # Detectar cruce de entrada (de arriba hacia abajo)
            if (last_y < entry_y and center_y >= entry_y and 
                person["direction"] == "towards_exit" and
                self.config.entry_line["x1"] <= center_x <= self.config.entry_line["x2"]):
                
                self.total_entries += 1
                self.current_people += 1
                print(f"🚪➡️  ENTRADA: Persona {track_id} | Total: {self.total_entries} entradas, {self.current_people} personas")
                self.log_event("entry", track_id, {"x": center_x, "y": center_y})
                self.save_stats()
                
            # Detectar cruce de salida (de abajo hacia arriba) 
            elif (last_y > exit_y and center_y <= exit_y and 
                  person["direction"] == "towards_entry" and
                  self.config.exit_line["x1"] <= center_x <= self.config.exit_line["x2"]):
                
                self.total_exits += 1
                self.current_people = max(0, self.current_people - 1)  # No permitir negativos
                print(f"🚪⬅️  SALIDA: Persona {track_id} | Total: {self.total_exits} salidas, {self.current_people} personas")
                self.log_event("exit", track_id, {"x": center_x, "y": center_y})
                self.save_stats()
            
            person["last_y"] = center_y
            
        else:
            # Nueva persona detectada
            self.tracked_persons[track_id] = {
                "last_y": center_y,
                "direction": None,
                "frames_missing": 0
            }
    
    def cleanup_lost_tracks(self):
        """Limpiar tracks de personas que ya no se detectan"""
        to_remove = []
        for track_id, person in self.tracked_persons.items():
            person["frames_missing"] += 1
            if person["frames_missing"] > self.config.tracking_timeout:
                to_remove.append(track_id)
        
        for track_id in to_remove:
            del self.tracked_persons[track_id]

    def get_stats(self):
        """Obtener estadísticas actuales"""
        return {
            'entries': self.total_entries,
            'exits': self.total_exits,
            'current': self.current_people,
            'tracking': len(self.tracked_persons),
            'session_start': self.session_start.isoformat(),
            'last_update': datetime.now().isoformat()
        }

# -----------------------------------------------------------------------------------------------
# Clase de Callback Personalizada
# -----------------------------------------------------------------------------------------------

class PersonCounterCallback(app_callback_class):
    """Callback personalizado para el contador de personas"""
    
    def __init__(self, rtsp_url=None):
        super().__init__()
        self.config = PersonCounterConfig()
        self.counter = PersonCounter(self.config)
        self.rtsp_url = rtsp_url
        
        # Configurar RTSP si se proporciona
        if rtsp_url:
            self.setup_rtsp_input(rtsp_url)
    
    def setup_rtsp_input(self, rtsp_url):
        """Configurar entrada RTSP"""
        print(f"🔗 Configurando entrada RTSP: {rtsp_url}")
        # La configuración RTSP se maneja en el pipeline de GStreamer
        # Esta función puede expandirse para validaciones adicionales
        
    def draw_zones_and_info(self, frame):
        """Dibujar zonas de conteo y información en el frame"""
        if frame is None:
            return frame
            
        height, width = frame.shape[:2]
        
        # Dibujar línea de entrada (verde)
        entry_y = int(self.config.entry_line["y"])
        entry_x1 = int(self.config.entry_line["x1"]) 
        entry_x2 = int(self.config.entry_line["x2"])
        cv2.line(frame, (entry_x1, entry_y), (entry_x2, entry_y), (0, 255, 0), 3)
        cv2.putText(frame, "ENTRADA", (entry_x1, entry_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Dibujar línea de salida (rojo)
        exit_y = int(self.config.exit_line["y"])
        exit_x1 = int(self.config.exit_line["x1"])
        exit_x2 = int(self.config.exit_line["x2"]) 
        cv2.line(frame, (exit_x1, exit_y), (exit_x2, exit_y), (0, 0, 255), 3)
        cv2.putText(frame, "SALIDA", (exit_x1, exit_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Mostrar estadísticas
        stats = self.counter.get_stats()
        info_text = [
            f"Entradas: {stats['entries']}",
            f"Salidas: {stats['exits']}",  
            f"Personas: {stats['current']}",
            f"Tracking: {stats['tracking']}"
        ]
        
        for i, text in enumerate(info_text):
            cv2.putText(frame, text, (10, 30 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, text, (10, 30 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
        
        return frame

# -----------------------------------------------------------------------------------------------
# Función de Callback Principal  
# -----------------------------------------------------------------------------------------------

def app_callback(pad, info, user_data):
    """Callback principal del sistema de conteo"""
    # Obtener buffer de GStreamer
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Incrementar contador de frames
    user_data.increment()
    
    # Obtener información del frame
    format, width, height = get_caps_from_pad(pad)
    
    # Obtener frame de video si está habilitado
    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        frame = get_numpy_from_buffer(buffer, format, width, height)

    # Obtener detecciones de personas
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # Procesar cada detección
    person_count = 0
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        
        if label == "person":
            # Obtener track ID
            track_id = 0
            track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            if len(track) == 1:
                track_id = track[0].get_id()
                
            # Actualizar seguimiento de la persona
            user_data.counter.update_person_tracking(track_id, bbox, confidence)
            person_count += 1

    # Limpiar tracks perdidos cada 30 frames
    if user_data.get_count() % 30 == 0:
        user_data.counter.cleanup_lost_tracks()

    # Procesar frame visual si está habilitado
    if user_data.use_frame and frame is not None:
        # Dibujar zonas e información
        frame = user_data.draw_zones_and_info(frame)
        
        # Convertir a BGR para visualización
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        user_data.set_frame(frame)

    # Imprimir estadísticas cada 60 frames (aprox. cada 2 segundos a 30fps)
    if user_data.get_count() % 60 == 0:
        stats = user_data.counter.get_stats()
        print(f"📊 Frame {user_data.get_count()} | Entradas: {stats['entries']} | Salidas: {stats['exits']} | Actuales: {stats['current']} | Detectadas: {person_count}")

    return Gst.PadProbeReturn.OK

# -----------------------------------------------------------------------------------------------
# Función Principal
# -----------------------------------------------------------------------------------------------

def main():
    """Función principal del sistema de conteo"""
    parser = argparse.ArgumentParser(description="Sistema de Conteo de Personas con Hailo AI")
    parser.add_argument("--input", type=str, default="rpi", 
                       help="Fuente de entrada: 'rpi', 'usb', archivo de video, o URL RTSP")
    parser.add_argument("--use-frame", action="store_true", 
                       help="Mostrar video con visualización en tiempo real")
    parser.add_argument("--rtsp-url", type=str,
                       help="URL RTSP completa (ej: rtsp://user:pass@ip:port/stream)")
    
    args = parser.parse_args()
    
    print("🤖 Iniciando Sistema de Conteo de Personas con Hailo AI")
    print("=" * 60)
    
    # Configurar entrada
    input_source = args.rtsp_url if args.rtsp_url else args.input
    print(f"📹 Entrada de video: {input_source}")
    
    # Configurar variables de entorno
    project_root = Path(__file__).resolve().parent
    env_file = project_root / ".env"
    env_path_str = str(env_file)
    os.environ["HAILO_ENV_FILE"] = env_path_str
    
    # Crear instancia del callback personalizado
    user_data = PersonCounterCallback(args.rtsp_url)
    user_data.use_frame = args.use_frame
    
    print("🚀 Iniciando detección...")
    print("📊 Estadísticas iniciales:", user_data.counter.get_stats())
    print("💡 Presiona Ctrl+C para detener")
    print("=" * 60)
    
    try:
        # Crear y ejecutar aplicación de detección
        app = GStreamerDetectionApp(app_callback, user_data)
        
        # Configurar entrada si es RTSP
        if args.rtsp_url:
            # La URL RTSP se puede pasar como argumento de entrada
            import sys
            sys.argv = [sys.argv[0], "--input", args.rtsp_url]
            if args.use_frame:
                sys.argv.append("--use-frame")
        
        app.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        user_data.counter.save_stats()
        final_stats = user_data.counter.get_stats()
        print("📊 Estadísticas finales:")
        print(f"   - Entradas: {final_stats['entries']}")
        print(f"   - Salidas: {final_stats['exits']}")  
        print(f"   - Personas actuales: {final_stats['current']}")
        print("✅ Sistema detenido correctamente")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        user_data.counter.save_stats()

if __name__ == "__main__":
    main()
