#!/usr/bin/env python3
"""
🎯 Script súper simple para configurar áreas de detección y línea de conteo
Instrucciones:
1. Click IZQUIERDO: Agregar puntos al polígono de detección
2. Click DERECHO: Finalizar polígono y empezar línea de conteo
3. Después: 2 clicks para marcar línea de entrada/salida
4. ESC: Guardar y salir
"""
import cv2
import json
import numpy as np
import os

# Configuración RTSP
RTSP_URL = "rtsp://192.168.1.77:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif"
CONFIG_FILE = "counter_areas.json"

# Variables globales
polygon_points = []
counting_line = []
mode = "polygon"  # "polygon" -> "line" -> "done"
frame_template = None

def mouse_callback(event, x, y, flags, param):
    global polygon_points, counting_line, mode, frame_template
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if mode == "polygon":
            polygon_points.append([x, y])
            print(f"📍 Punto polígono: ({x}, {y}) - Total: {len(polygon_points)}")
        elif mode == "line":
            counting_line.append([x, y])
            print(f"📏 Punto línea: ({x}, {y}) - Total: {len(counting_line)}")
            if len(counting_line) == 2:
                mode = "done"
                print("✅ Configuración completada! Presiona ESC para guardar")
    
    elif event == cv2.EVENT_RBUTTONDOWN and mode == "polygon":
        if len(polygon_points) >= 3:
            mode = "line"
            print(f"✅ Polígono terminado con {len(polygon_points)} puntos")
            print("📏 Ahora marca la LÍNEA DE CONTEO (2 clicks)")
        else:
            print("❌ Necesitas al menos 3 puntos para el polígono")

def draw_areas(frame):
    """Dibuja las áreas configuradas en el frame"""
    overlay = frame.copy()
    
    # Dibujar polígono
    if len(polygon_points) >= 3:
        pts = np.array(polygon_points, np.int32)
        cv2.fillPoly(overlay, [pts], (0, 255, 0, 100))  # Verde semitransparente
        cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
    elif len(polygon_points) > 0:
        for i, point in enumerate(polygon_points):
            cv2.circle(frame, tuple(point), 5, (0, 255, 0), -1)
            cv2.putText(frame, str(i+1), (point[0]+10, point[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Dibujar línea de conteo
    if len(counting_line) == 2:
        cv2.line(frame, tuple(counting_line[0]), tuple(counting_line[1]), (0, 0, 255), 3)
        cv2.putText(frame, "LINEA CONTEO", (counting_line[0][0], counting_line[0][1]-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    elif len(counting_line) == 1:
        cv2.circle(frame, tuple(counting_line[0]), 5, (0, 0, 255), -1)
    
    # Blend overlay
    if len(polygon_points) >= 3:
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
    
    return frame

def save_config():
    """Guarda la configuración en archivo JSON"""
    config = {
        "detection_polygon": polygon_points,
        "counting_line": counting_line,
        "rtsp_url": RTSP_URL
    }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"💾 Configuración guardada en {CONFIG_FILE}")
    print(f"📐 Polígono: {len(polygon_points)} puntos")
    print(f"📏 Línea: {len(counting_line)} puntos")

def main():
    global frame_template, mode
    
    # Configurar OpenCV para evitar problemas de display en Raspberry Pi
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    
    print("🚀 Configurador de Áreas - Sistema Contador de Personas")
    print("=" * 60)
    print("📝 INSTRUCCIONES:")
    print("   • Click IZQUIERDO: Agregar punto al polígono")
    print("   • Click DERECHO: Finalizar polígono")
    print("   • Después: 2 clicks para línea de conteo")
    print("   • ESC: Guardar y salir")
    print("=" * 60)
    
    # Conectar a RTSP
    cap = cv2.VideoCapture(RTSP_URL)
    
    if not cap.isOpened():
        print("❌ Error: No se puede conectar al stream RTSP")
        return
    
    print("✅ Conectado al stream RTSP")
    
    cv2.namedWindow('Configurar Areas', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('Configurar Areas', mouse_callback)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error leyendo frame")
            break
        
        # Redimensionar para mejor visualización
        frame = cv2.resize(frame, (1280, 720))
        frame_template = frame.copy()
        
        # Dibujar áreas
        frame_with_areas = draw_areas(frame)
        
        # Mostrar estado actual
        if mode == "polygon":
            status = f"POLIGONO - Puntos: {len(polygon_points)}"
        elif mode == "line":
            status = f"LINEA DE CONTEO - Puntos: {len(counting_line)}/2"
        else:
            status = "TERMINADO - Presiona ESC para guardar"
        
        cv2.putText(frame_with_areas, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.imshow('Configurar Areas', frame_with_areas)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            if mode == "done":
                save_config()
                break
            else:
                print("⚠️  Completa la configuración antes de salir")
        elif key == ord('c'):  # Clear
            polygon_points.clear()
            counting_line.clear()
            mode = "polygon"
            print("🧹 Configuración limpiada")
    
    cap.release()
    cv2.destroyAllWindows()
    print("🏁 Configuración terminada")

if __name__ == "__main__":
    main()
