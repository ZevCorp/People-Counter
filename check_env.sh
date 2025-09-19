#!/bin/bash

# Script de verificación del entorno para el Sistema de Conteo de Personas
# Verifica que el entorno virtual venv_hailo_rpi_examples esté correctamente configurado

echo "🔍 Verificando Entorno del Sistema de Conteo..."
echo "============================================="

# Verificar si estamos en el directorio correcto
if [ ! -f "setup_env.sh" ]; then
    echo "❌ Error: setup_env.sh no encontrado"
    echo "   Debes ejecutar este script desde el directorio raíz del proyecto hailo-rpi5-examples"
    exit 1
fi

echo "✅ Directorio del proyecto correcto"

# Verificar si existe el entorno virtual
VENV_NAME="venv_hailo_rpi_examples"
if [ ! -d "$VENV_NAME" ]; then
    echo "❌ Error: Entorno virtual $VENV_NAME no encontrado"
    echo "   Ejecuta: ./install.sh para crear el entorno virtual"
    exit 1
fi

echo "✅ Entorno virtual $VENV_NAME encontrado"

# Verificar si el entorno virtual está activo
if [[ "$VIRTUAL_ENV" == *"$VENV_NAME"* ]]; then
    echo "✅ Entorno virtual $VENV_NAME está ACTIVO"
    echo "   Ubicación: $VIRTUAL_ENV"
else
    echo "⚠️  Entorno virtual $VENV_NAME NO está activo"
    echo "   Ejecuta: source setup_env.sh"
    echo ""
    echo "🔄 Activando entorno virtual ahora..."
    source setup_env.sh
    
    if [[ "$VIRTUAL_ENV" == *"$VENV_NAME"* ]]; then
        echo "✅ Entorno virtual activado correctamente"
    else
        echo "❌ Error: No se pudo activar el entorno virtual"
        exit 1
    fi
fi

# Verificar Python y pip
echo ""
echo "🐍 Verificando Python y pip..."
python3 --version
pip --version

# Verificar dependencias básicas de Hailo
echo ""
echo "📦 Verificando dependencias básicas de Hailo..."

MISSING_DEPS=0

if pip list | grep -q "hailo-apps-infra"; then
    echo "✅ hailo-apps-infra instalado"
else
    echo "❌ hailo-apps-infra NO instalado"
    MISSING_DEPS=1
fi

if pip list | grep -q "hailort"; then
    echo "✅ hailort instalado"
else
    echo "❌ hailort NO instalado"
    MISSING_DEPS=1
fi

# Verificar dependencias del contador
echo ""
echo "🤖 Verificando dependencias del contador..."

if pip list | grep -q "flask"; then
    echo "✅ flask instalado"
else
    echo "⚠️  flask no instalado - ejecuta: pip install -r requirements_counter.txt"
fi

if pip list | grep -q "opencv-python"; then
    echo "✅ opencv-python instalado"
else
    echo "⚠️  opencv-python no instalado - ejecuta: pip install -r requirements_counter.txt"
fi

# Verificar archivos del contador
echo ""
echo "📁 Verificando archivos del contador..."

FILES_TO_CHECK=("people_counter.py" "dashboard.py" "start_counter.sh" "requirements_counter.txt")

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file encontrado"
    else
        echo "❌ $file NO encontrado"
        MISSING_DEPS=1
    fi
done

# Resumen final
echo ""
echo "📊 RESUMEN DE VERIFICACIÓN"
echo "========================"

if [ $MISSING_DEPS -eq 0 ]; then
    echo "🎉 ¡TODO CORRECTO! El sistema está listo para usar"
    echo ""
    echo "🚀 Para iniciar el contador:"
    echo "   ./start_counter.sh"
    echo ""
    echo "🌐 Para solo el dashboard:"
    echo "   python3 dashboard.py"
else
    echo "⚠️  Se encontraron problemas. Revisa los errores de arriba"
    echo ""
    echo "🔧 Soluciones comunes:"
    echo "   - Ejecutar: ./install.sh (para instalar Hailo)"
    echo "   - Ejecutar: source setup_env.sh (para activar entorno)"
    echo "   - Ejecutar: pip install -r requirements_counter.txt (para dependencias)"
fi
