# Guía de Instalación de ngrok

## Opción 1: Instalación Manual SIN sudo (Recomendada)

```bash
# Ir al directorio del proyecto
cd ~/proyectos/segmentacion-dashboard

# Descargar ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz

# Extraer
tar -xvzf ngrok-v3-stable-linux-amd64.tgz

# Verificar instalación
./ngrok version

# Limpiar archivo descargado
rm ngrok-v3-stable-linux-amd64.tgz
```

## Opción 2: Instalación con sudo (Requiere contraseña)

```bash
# Agregar repositorio de ngrok
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list

# Actualizar e instalar
sudo apt update
sudo apt install ngrok -y
```

---

## Configuración de ngrok

### 1. Crear cuenta en ngrok (si no tienes)
Visita: https://dashboard.ngrok.com/signup

### 2. Obtener tu authtoken
Después de crear cuenta, visita: https://dashboard.ngrok.com/get-started/your-authtoken

### 3. Configurar authtoken
```bash
# Si instalaste con Opción 1 (sin sudo):
./ngrok config add-authtoken TU_TOKEN_AQUI

# Si instalaste con Opción 2 (con sudo):
ngrok config add-authtoken TU_TOKEN_AQUI
```

---

## Uso de ngrok con tu Dashboard

### Exponer el dashboard (puerto 5000)

```bash
# Si instalaste sin sudo (Opción 1):
./ngrok http 5000

# Si instalaste con sudo (Opción 2):
ngrok http 5000
```

### Con opciones adicionales:

```bash
# Con dominio personalizado y región
./ngrok http 5000 --region us --host-header="localhost:5000"

# En segundo plano (background)
./ngrok http 5000 > /dev/null &
```

---

## Verificar que el Dashboard está corriendo

Antes de iniciar ngrok, asegúrate que Gunicorn esté corriendo:

```bash
# Verificar que Gunicorn está corriendo
ps aux | grep gunicorn

# Si no está corriendo, iniciarlo:
source venv/bin/activate
gunicorn -c gunicorn_config.py app:app
```

---

## Ejemplo de salida de ngrok

```
ngrok

Session Status                online
Account                       tu_usuario (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xx-xx-xx-xx.ngrok-free.app -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**URL pública**: `https://xxxx-xx-xx-xx-xx.ngrok-free.app`

---

## Script de inicio completo

Puedes crear un script para iniciar todo:

```bash
#!/bin/bash
# start_with_ngrok.sh

echo "🚀 Iniciando Dashboard con ngrok..."

# Activar entorno virtual e iniciar Gunicorn en background
source venv/bin/activate
gunicorn -c gunicorn_config.py app:app &

# Esperar que Gunicorn inicie
sleep 3

# Iniciar ngrok
./ngrok http 5000
```

Hacerlo ejecutable:
```bash
chmod +x start_with_ngrok.sh
```

Ejecutar:
```bash
./start_with_ngrok.sh
```

---

## Detener ngrok y Gunicorn

```bash
# Detener ngrok
pkill ngrok

# Detener Gunicorn
pkill -f gunicorn
```

---

## Consideraciones de Seguridad

⚠️ **IMPORTANTE**:
- ngrok expondrá tu dashboard a internet
- Cualquiera con la URL puede acceder
- El plan gratuito cambia la URL cada vez que reinicias ngrok
- Considera agregar autenticación básica si vas a compartir la URL

### Agregar autenticación básica con ngrok:

```bash
./ngrok http 5000 --basic-auth="usuario:contraseña"
```

---

## Límites del plan gratuito de ngrok

- ✅ 1 túnel online simultáneo
- ✅ 40 conexiones por minuto
- ⚠️ La URL cambia cada vez que reinicias
- ⚠️ Requiere confirmar en navegador (pantalla de advertencia de ngrok)

### Para dominio permanente necesitas plan de pago
