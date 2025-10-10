#!/bin/bash

# Script para iniciar el dashboard OPTIMIZADO con Gunicorn
# Aprovecha los 12 hilos de tu AMD Ryzen 5 5625U

echo "🚀 Iniciando Dashboard de Segmentación OPTIMIZADO"
echo "=================================================="
echo ""

# Verificar que gunicorn esté instalado
if ! command -v gunicorn &> /dev/null; then
    echo "⚠️  Gunicorn no instalado. Instalando..."
    pip install gunicorn==21.2.0
fi

# Variables de entorno
export MONGO_URI="${MONGO_URI:-mongodb://localhost:27017}"
export GUNICORN_WORKERS="${GUNICORN_WORKERS:-8}"

echo "📊 Configuración:"
echo "   - MongoDB: $MONGO_URI"
echo "   - Workers: $GUNICORN_WORKERS (de 12 hilos disponibles)"
echo "   - Puerto: 5000"
echo ""

# Iniciar con Gunicorn
echo "🔥 Iniciando Gunicorn..."
gunicorn -c gunicorn_config.py app:app

# Si falla, mostrar ayuda
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Error al iniciar Gunicorn"
    echo ""
    echo "Alternativas:"
    echo "  1. Modo desarrollo (1 solo núcleo):"
    echo "     python app.py"
    echo ""
    echo "  2. Gunicorn manual:"
    echo "     gunicorn -w 8 -b 0.0.0.0:5000 --timeout 120 app:app"
    echo ""
fi
