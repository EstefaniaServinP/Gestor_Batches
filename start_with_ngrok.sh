#!/bin/bash
# Script para iniciar el Dashboard con ngrok

echo "🚀 Iniciando Dashboard de Segmentación con ngrok"
echo "=================================================="
echo ""

# Verificar que ngrok esté instalado
if [ ! -f "./ngrok" ]; then
    echo "❌ Error: ngrok no encontrado en el directorio actual"
    echo "   Ejecuta primero: wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz && tar -xzf ngrok-v3-stable-linux-amd64.tgz"
    exit 1
fi

# Verificar que ngrok esté configurado con authtoken
if ! ./ngrok config check > /dev/null 2>&1; then
    echo "⚠️  ngrok no está configurado con authtoken"
    echo ""
    echo "Para configurar ngrok:"
    echo "  1. Crea una cuenta en: https://dashboard.ngrok.com/signup"
    echo "  2. Obtén tu token en: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "  3. Ejecuta: ./ngrok config add-authtoken TU_TOKEN"
    echo ""
    read -p "¿Ya tienes tu authtoken? (s/n): " respuesta
    if [ "$respuesta" = "s" ]; then
        read -p "Ingresa tu authtoken: " token
        ./ngrok config add-authtoken $token
    else
        exit 1
    fi
fi

# Verificar si Gunicorn ya está corriendo
if pgrep -f "gunicorn.*app:app" > /dev/null; then
    echo "✅ Gunicorn ya está corriendo"
else
    echo "🔄 Iniciando Gunicorn..."
    source venv/bin/activate
    gunicorn -c gunicorn_config.py app:app > /dev/null 2>&1 &

    # Esperar que Gunicorn inicie
    sleep 3

    if pgrep -f "gunicorn.*app:app" > /dev/null; then
        echo "✅ Gunicorn iniciado correctamente"
    else
        echo "❌ Error al iniciar Gunicorn"
        exit 1
    fi
fi

echo ""
echo "🌐 Iniciando túnel ngrok..."
echo ""
echo "=================================================="
echo "  Para detener ngrok: Presiona Ctrl+C"
echo "  Para detener Gunicorn: pkill -f gunicorn"
echo "=================================================="
echo ""

# Iniciar ngrok
./ngrok http 5000
