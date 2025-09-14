# Contador de Personas con Hailo AI Kit y Raspberry Pi 5

Este proyecto implementa un sistema de conteo de personas utilizando el Hailo AI Kit en una Raspberry Pi 5, con capacidad para recibir video a través de RTSP y contar entradas y salidas de personas.

## Características

- Detección de personas usando el acelerador de IA Hailo
- Recepción de video mediante RTSP
- Conteo de entradas y salidas de personas
- Visualización en tiempo real
- Optimizaciones de rendimiento:
  - Procesamiento selectivo de frames
  - Suavizado de trayectorias
  - Configuración ajustable

## Requisitos

- Raspberry Pi 5
- Hailo AI Kit (13 TOPs)
- Cámara con soporte RTSP
- Sistema operativo compatible con Hailo

## Instalación

1. Asegúrate de tener instalado el software de Hailo:

```bash
sudo apt update
sudo apt install hailo-all
```

2. Clona este repositorio:

```bash
git clone https://github.com/tu-usuario/contador-personas-hailo.git
cd contador-personas-hailo
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Uso

Ejecuta el script principal con la URL de tu cámara RTSP:

```bash
python contador_personas.py --rtsp rtsp://usuario:contraseña@ip_camara:554/stream
```

### Opciones disponibles

- `--rtsp`: URL del stream RTSP (requerido)
- `--linea`: Posición de la línea de conteo (0-1, normalizada). Por defecto: 0.5
- `--umbral`: Umbral de confianza para detecciones (0-1). Por defecto: 0.5
- `--skip`: Procesar 1 de cada N frames. Por defecto: 2

Ejemplo:

```bash
python contador_personas.py --rtsp rtsp://192.168.1.100:554/stream --linea 0.6 --umbral 0.7 --skip 3
```

## Funcionamiento

El sistema funciona de la siguiente manera:

1. Recibe el video desde la fuente RTSP
2. Procesa los frames con el acelerador Hailo para detectar personas
3. Realiza seguimiento de las personas detectadas
4. Cuenta las personas que cruzan una línea virtual (configurable)
5. Muestra en tiempo real los contadores de entradas y salidas

La línea de conteo se dibuja horizontalmente en la posición especificada. Cuando una persona cruza esta línea de abajo hacia arriba, se cuenta como una entrada. Cuando cruza de arriba hacia abajo, se cuenta como una salida.

## Optimización

El código incluye varias optimizaciones para mejorar el rendimiento:

- **Procesamiento selectivo**: Procesa solo 1 de cada N frames para reducir la carga de CPU
- **Suavizado de trayectorias**: Utiliza un historial de posiciones para evitar falsos conteos por fluctuaciones
- **Umbral de confianza**: Filtra detecciones con baja confianza

## Personalización

Puedes modificar los siguientes parámetros en el código:

- Umbral de confianza para las detecciones
- Posición de la línea de conteo
- Frecuencia de procesamiento de frames
- Tamaño del historial para suavizado

## Solución de problemas

- **No se detectan personas**: Verifica el umbral de confianza, podría ser demasiado alto
- **Conteos incorrectos**: Ajusta la posición de la línea de conteo o aumenta el tamaño del historial
- **Rendimiento lento**: Aumenta el valor de `skip` para procesar menos frames

## Contribuciones

Las contribuciones son bienvenidas. Por favor, envía un pull request o abre un issue para discutir los cambios propuestos.

## Licencia

[MIT](LICENSE)