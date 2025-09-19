#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Web Básico para el Sistema de Conteo de Personas
Interface simple con Flask

REQUISITOS:
- Instalar Flask en venv_hailo_rpi_examples: pip install flask
- Ejecutar: source setup_env.sh antes de usar
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

class DashboardData:
    """Clase para manejar datos del dashboard"""
    
    def __init__(self):
        self.stats_file = "counter_stats.json"
        self.log_file = "counter_log.json"
        self.last_stats = {}
        self.recent_events = []
        
    def get_stats(self):
        """Obtener estadísticas actuales"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    self.last_stats = json.load(f)
                    return self.last_stats
        except Exception as e:
            print(f"Error leyendo estadísticas: {e}")
        
        return {
            'total_entries': 0,
            'total_exits': 0,
            'current_people': 0,
            'last_update': datetime.now().isoformat(),
            'session_start': datetime.now().isoformat()
        }
    
    def get_recent_events(self, limit=10):
        """Obtener eventos recientes"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    events = json.load(f)
                    # Devolver los últimos eventos
                    self.recent_events = events[-limit:] if len(events) > limit else events
                    return self.recent_events
        except Exception as e:
            print(f"Error leyendo eventos: {e}")
        
        return []
    
    def get_hourly_stats(self):
        """Obtener estadísticas por hora del día actual"""
        try:
            if not os.path.exists(self.log_file):
                return {}
                
            with open(self.log_file, 'r') as f:
                events = json.load(f)
            
            # Filtrar eventos del día actual
            today = datetime.now().date()
            hourly_data = {}
            
            for event in events:
                event_time = datetime.fromisoformat(event['timestamp'])
                if event_time.date() == today:
                    hour = event_time.hour
                    if hour not in hourly_data:
                        hourly_data[hour] = {'entries': 0, 'exits': 0}
                    
                    if event['type'] == 'entry':
                        hourly_data[hour]['entries'] += 1
                    elif event['type'] == 'exit':
                        hourly_data[hour]['exits'] += 1
            
            return hourly_data
            
        except Exception as e:
            print(f"Error generando estadísticas por hora: {e}")
            return {}

# Instancia global para datos del dashboard
dashboard_data = DashboardData()

@app.route('/')
def index():
    """Página principal del dashboard"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def api_stats():
    """API para obtener estadísticas actuales"""
    stats = dashboard_data.get_stats()
    events = dashboard_data.get_recent_events()
    hourly = dashboard_data.get_hourly_stats()
    
    return jsonify({
        'stats': stats,
        'recent_events': events,
        'hourly_stats': hourly
    })

@app.route('/api/reset')
def api_reset():
    """API para resetear contadores (solo en desarrollo)"""
    try:
        reset_data = {
            'total_entries': 0,
            'total_exits': 0,
            'current_people': 0,
            'last_update': datetime.now().isoformat(),
            'session_start': datetime.now().isoformat()
        }
        
        with open(dashboard_data.stats_file, 'w') as f:
            json.dump(reset_data, f, indent=2)
            
        return jsonify({'success': True, 'message': 'Contadores reseteados'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def create_template():
    """Crear template HTML básico"""
    template_dir = "templates"
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    template_content = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Contador de Personas - Hailo AI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #4a5568;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .header p {
            color: #718096;
            font-size: 1.1em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-number {
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #718096;
            font-size: 1.1em;
        }
        
        .entries .stat-number { color: #48bb78; }
        .exits .stat-number { color: #f56565; }
        .current .stat-number { color: #4299e1; }
        .session .stat-number { color: #9f7aea; }
        
        .content-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        
        .panel {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .panel h3 {
            color: #4a5568;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        
        .event {
            padding: 15px;
            border-left: 4px solid #e2e8f0;
            margin-bottom: 15px;
            background: #f7fafc;
            border-radius: 5px;
        }
        
        .event.entry { border-left-color: #48bb78; }
        .event.exit { border-left-color: #f56565; }
        
        .event-time {
            font-size: 0.9em;
            color: #718096;
        }
        
        .event-desc {
            font-weight: 500;
            margin-top: 5px;
        }
        
        .chart-container {
            height: 200px;
            display: flex;
            align-items: end;
            justify-content: space-between;
            padding: 20px 0;
        }
        
        .chart-bar {
            background: linear-gradient(to top, #4299e1, #63b3ed);
            width: 30px;
            margin: 0 2px;
            border-radius: 3px 3px 0 0;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .chart-bar:hover {
            background: linear-gradient(to top, #3182ce, #4299e1);
        }
        
        .chart-label {
            position: absolute;
            bottom: -25px;
            left: 50%;
            transform: translateX(-50%);
            font-size: 0.8em;
            color: #718096;
        }
        
        .status-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #48bb78;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 0.9em;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .status-indicator.offline {
            background: #f56565;
        }
        
        .reset-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #e53e3e;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: background 0.3s ease;
        }
        
        .reset-btn:hover {
            background: #c53030;
        }
        
        @media (max-width: 768px) {
            .content-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🤖 Contador de Personas</h1>
            <p>Sistema de monitoreo con Hailo AI en tiempo real</p>
        </div>
        
        <!-- Status Indicator -->
        <div id="statusIndicator" class="status-indicator">
            🟢 Sistema Activo
        </div>
        
        <!-- Stats Cards -->
        <div class="stats-grid">
            <div class="stat-card entries">
                <div id="entriesCount" class="stat-number">0</div>
                <div class="stat-label">Entradas</div>
            </div>
            <div class="stat-card exits">
                <div id="exitsCount" class="stat-number">0</div>
                <div class="stat-label">Salidas</div>
            </div>
            <div class="stat-card current">
                <div id="currentCount" class="stat-number">0</div>
                <div class="stat-label">Personas Actuales</div>
            </div>
            <div class="stat-card session">
                <div id="sessionTime" class="stat-number">0h</div>
                <div class="stat-label">Tiempo de Sesión</div>
            </div>
        </div>
        
        <!-- Content Panels -->
        <div class="content-grid">
            <!-- Recent Events -->
            <div class="panel">
                <h3>📋 Eventos Recientes</h3>
                <div id="recentEvents">
                    <div class="event">
                        <div class="event-time">Esperando datos...</div>
                        <div class="event-desc">Sistema inicializando</div>
                    </div>
                </div>
            </div>
            
            <!-- Hourly Chart -->
            <div class="panel">
                <h3>📊 Actividad por Hora (Hoy)</h3>
                <div id="hourlyChart" class="chart-container">
                    <!-- Chart will be generated by JavaScript -->
                </div>
            </div>
        </div>
        
        <!-- Reset Button -->
        <button class="reset-btn" onclick="resetCounters()">🔄 Reset Contadores</button>
    </div>
    
    <script>
        let lastUpdate = null;
        
        function updateDashboard() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    // Update main stats
                    document.getElementById('entriesCount').textContent = data.stats.total_entries || 0;
                    document.getElementById('exitsCount').textContent = data.stats.total_exits || 0;
                    document.getElementById('currentCount').textContent = data.stats.current_people || 0;
                    
                    // Update session time
                    if (data.stats.session_start) {
                        const sessionStart = new Date(data.stats.session_start);
                        const now = new Date();
                        const diffHours = Math.floor((now - sessionStart) / (1000 * 60 * 60));
                        document.getElementById('sessionTime').textContent = diffHours + 'h';
                    }
                    
                    // Update recent events
                    updateRecentEvents(data.recent_events);
                    
                    // Update hourly chart
                    updateHourlyChart(data.hourly_stats);
                    
                    // Update status indicator
                    const statusIndicator = document.getElementById('statusIndicator');
                    if (data.stats.last_update) {
                        const lastUpdateTime = new Date(data.stats.last_update);
                        const now = new Date();
                        const timeDiff = (now - lastUpdateTime) / 1000;
                        
                        if (timeDiff < 30) {
                            statusIndicator.textContent = '🟢 Sistema Activo';
                            statusIndicator.classList.remove('offline');
                        } else {
                            statusIndicator.textContent = '🔴 Sin datos recientes';
                            statusIndicator.classList.add('offline');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                    const statusIndicator = document.getElementById('statusIndicator');
                    statusIndicator.textContent = '⚠️ Error de conexión';
                    statusIndicator.classList.add('offline');
                });
        }
        
        function updateRecentEvents(events) {
            const container = document.getElementById('recentEvents');
            if (!events || events.length === 0) {
                container.innerHTML = '<div class="event"><div class="event-time">Sin eventos</div><div class="event-desc">Esperando actividad...</div></div>';
                return;
            }
            
            container.innerHTML = events.slice(-10).reverse().map(event => {
                const time = new Date(event.timestamp).toLocaleTimeString();
                const type = event.type === 'entry' ? 'Entrada' : 'Salida';
                const icon = event.type === 'entry' ? '➡️' : '⬅️';
                
                return `
                    <div class="event ${event.type}">
                        <div class="event-time">${time}</div>
                        <div class="event-desc">${icon} ${type} - ID: ${event.track_id}</div>
                    </div>
                `;
            }).join('');
        }
        
        function updateHourlyChart(hourlyStats) {
            const container = document.getElementById('hourlyChart');
            const currentHour = new Date().getHours();
            
            let chartHTML = '';
            for (let hour = 0; hour < 24; hour++) {
                const data = hourlyStats[hour] || {entries: 0, exits: 0};
                const total = data.entries + data.exits;
                const height = Math.max(5, total * 10); // Minimum height of 5px
                
                chartHTML += `
                    <div class="chart-bar" style="height: ${height}px;" title="Hora ${hour}: ${total} eventos">
                        <div class="chart-label">${hour}h</div>
                    </div>
                `;
            }
            container.innerHTML = chartHTML;
        }
        
        function resetCounters() {
            if (confirm('¿Estás seguro de que quieres resetear todos los contadores?')) {
                fetch('/api/reset')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('✅ Contadores reseteados correctamente');
                            updateDashboard();
                        } else {
                            alert('❌ Error: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('❌ Error de conexión: ' + error);
                    });
            }
        }
        
        // Update dashboard every 2 seconds
        updateDashboard();
        setInterval(updateDashboard, 2000);
    </script>
</body>
</html>'''
    
    template_path = os.path.join(template_dir, "dashboard.html")
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"✅ Template HTML creado: {template_path}")

def main():
    """Función principal del dashboard"""
    print("🌐 Iniciando Dashboard Web...")
    
    # Crear template HTML
    create_template()
    
    print("📊 Dashboard disponible en: http://localhost:5000")
    print("💡 Presiona Ctrl+C para detener")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard detenido")

if __name__ == "__main__":
    main()
