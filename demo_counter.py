#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo del Sistema de Conteo de Personas
Simulación con datos de prueba para testing
"""

import json
import time
import random
from datetime import datetime, timedelta

def generate_demo_data():
    """Generar datos de prueba para el demo"""
    
    # Generar estadísticas base
    base_stats = {
        'total_entries': random.randint(20, 100),
        'total_exits': 0,
        'current_people': 0,
        'last_update': datetime.now().isoformat(),
        'session_start': (datetime.now() - timedelta(hours=2)).isoformat()
    }
    
    # Calcular salidas (entre 70-90% de entradas para ser realista)
    base_stats['total_exits'] = int(base_stats['total_entries'] * random.uniform(0.7, 0.9))
    base_stats['current_people'] = max(0, base_stats['total_entries'] - base_stats['total_exits'])
    
    # Guardar estadísticas
    with open('counter_stats.json', 'w') as f:
        json.dump(base_stats, f, indent=2)
    
    # Generar eventos de ejemplo
    events = []
    current_time = datetime.now() - timedelta(hours=2)
    
    for i in range(base_stats['total_entries'] + base_stats['total_exits']):
        event_type = 'entry' if len([e for e in events if e['type'] == 'entry']) < base_stats['total_entries'] else 'exit'
        
        if event_type == 'exit' and len([e for e in events if e['type'] == 'entry']) <= len([e for e in events if e['type'] == 'exit']):
            event_type = 'entry'
        
        current_people = len([e for e in events if e['type'] == 'entry']) - len([e for e in events if e['type'] == 'exit'])
        if event_type == 'entry':
            current_people += 1
        else:
            current_people = max(0, current_people - 1)
        
        event = {
            'timestamp': (current_time + timedelta(minutes=random.randint(0, 120))).isoformat(),
            'type': event_type,
            'track_id': random.randint(100, 999),
            'position': {
                'x': random.randint(200, 400),
                'y': 200 if event_type == 'entry' else 400
            },
            'total_entries': len([e for e in events if e['type'] == 'entry']) + (1 if event_type == 'entry' else 0),
            'total_exits': len([e for e in events if e['type'] == 'exit']) + (1 if event_type == 'exit' else 0),
            'current_people': current_people
        }
        events.append(event)
    
    # Ordenar eventos por tiempo
    events.sort(key=lambda x: x['timestamp'])
    
    # Guardar eventos
    with open('counter_log.json', 'w') as f:
        json.dump(events, f, indent=2)
    
    print("✅ Datos demo generados exitosamente:")
    print(f"   - Entradas: {base_stats['total_entries']}")
    print(f"   - Salidas: {base_stats['total_exits']}")
    print(f"   - Personas actuales: {base_stats['current_people']}")
    print(f"   - Eventos totales: {len(events)}")
    print(f"   - Archivos: counter_stats.json, counter_log.json")
    print("\n🌐 Ahora puedes ejecutar: python3 dashboard.py")
    print("   Y visitar: http://localhost:5000")

def update_demo_data():
    """Actualizar datos demo cada pocos segundos"""
    try:
        with open('counter_stats.json', 'r') as f:
            stats = json.load(f)
        
        with open('counter_log.json', 'r') as f:
            events = json.load(f)
    except FileNotFoundError:
        generate_demo_data()
        return
    
    # Simular nueva actividad
    if random.random() < 0.3:  # 30% probabilidad de nuevo evento
        event_type = random.choice(['entry', 'exit'])
        
        # No permitir salidas si no hay personas
        if event_type == 'exit' and stats['current_people'] <= 0:
            event_type = 'entry'
        
        # Crear nuevo evento
        new_event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'track_id': random.randint(1000, 9999),
            'position': {
                'x': random.randint(200, 400),
                'y': 200 if event_type == 'entry' else 400
            },
            'total_entries': stats['total_entries'] + (1 if event_type == 'entry' else 0),
            'total_exits': stats['total_exits'] + (1 if event_type == 'exit' else 0),
            'current_people': stats['current_people'] + (1 if event_type == 'entry' else -1)
        }
        
        # Actualizar estadísticas
        if event_type == 'entry':
            stats['total_entries'] += 1
            stats['current_people'] += 1
        else:
            stats['total_exits'] += 1
            stats['current_people'] = max(0, stats['current_people'] - 1)
        
        stats['last_update'] = datetime.now().isoformat()
        
        # Agregar evento
        events.append(new_event)
        
        # Mantener solo últimos 100 eventos
        if len(events) > 100:
            events = events[-100:]
        
        # Guardar datos actualizados
        with open('counter_stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        with open('counter_log.json', 'w') as f:
            json.dump(events, f, indent=2)
        
        action = "Entrada" if event_type == 'entry' else "Salida"
        icon = "➡️" if event_type == 'entry' else "⬅️"
        print(f"{icon} {action} simulada - Personas actuales: {stats['current_people']}")

def run_demo():
    """Ejecutar demo en bucle"""
    print("🎬 Iniciando Demo del Sistema de Conteo")
    print("=====================================")
    print("Este demo simula actividad en tiempo real")
    print("Presiona Ctrl+C para detener")
    print("")
    
    generate_demo_data()
    print("")
    
    try:
        while True:
            time.sleep(random.uniform(3, 8))  # Esperar entre 3-8 segundos
            update_demo_data()
    except KeyboardInterrupt:
        print("\n🛑 Demo detenido")

if __name__ == "__main__":
    run_demo()
