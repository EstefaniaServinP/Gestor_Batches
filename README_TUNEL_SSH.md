# 🔐 Guía de Túnel SSH para MongoDB Remoto

## 📋 Resumen

Este proyecto requiere acceso a **DOS instancias de MongoDB**:
1. **Local (127.0.0.1:27017)**: `segmentacion_db`, `Quality_dashboard`
2. **Remoto (vía túnel SSH → 127.0.0.1:27018)**: `QUALITY_IEMSA` con máscaras

## 🚀 Inicio Rápido

### Opción 1: Túnel Básico (Recomendado para desarrollo)
```bash
./setup_mongo_tunnel.sh
```

### Opción 2: Túnel Persistente (Recomendado para producción)
```bash
./setup_mongo_tunnel_autossh.sh
```

## 📦 Requisitos Previos

### 1. Instalar mongosh (si no lo tienes)
```bash
# Ubuntu/Debian
wget -qO- https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install mongodb-mongosh
```

### 2. Instalar autossh (solo para opción 2)
```bash
sudo apt install autossh
```

### 3. Configurar acceso SSH sin contraseña (opcional pero recomendado)
```bash
# Generar llave SSH (si no tienes)
ssh-keygen -t ed25519 -C "tu_email@example.com"

# Copiar llave al servidor remoto
ssh-copy-id -p 22 faservin@192.168.1.93
```

## ⚙️ Configuración

### Variables de Entorno (opcional)
```bash
export REMOTE_USER="faservin"              # Usuario SSH
export REMOTE_HOST="192.168.1.93"          # IP del servidor
export REMOTE_PORT="22"                     # Puerto SSH
export LOCAL_PORT="27018"                   # Puerto local para túnel
```

### Cambiar IP del Servidor
Si la IP de Carlos cambia, edita los scripts o usa variables de entorno:

```bash
# Opción 1: Variable de entorno
export REMOTE_HOST="192.168.0.246"
./setup_mongo_tunnel.sh

# Opción 2: Editar el script
nano setup_mongo_tunnel.sh
# Busca: REMOTE_HOST="${REMOTE_HOST:-192.168.1.93}"
# Cambia a: REMOTE_HOST="${REMOTE_HOST:-192.168.0.246}"
```

## 🔍 Verificación y Diagnóstico

### Ver si el túnel está activo
```bash
# Para túnel básico
ps aux | grep ssh | grep 27018

# Para autossh
ps aux | grep autossh | grep 27018
```

### Probar conexión a MongoDB remoto
```bash
mongosh "mongodb://127.0.0.1:27018/QUALITY_IEMSA" --eval "db.adminCommand('ping')"
```

### Ver máscaras disponibles
```bash
mongosh "mongodb://127.0.0.1:27018/QUALITY_IEMSA" --eval "db['training_metrics.masks.files'].countDocuments()"
```

### Ver logs de autossh
```bash
tail -f /tmp/autossh_mongo_27018.log
```

### Verificar puerto en uso
```bash
ss -tulpn | grep 27018
```

## 🛠️ Solución de Problemas

### Problema: "Connection refused"
```bash
# Verificar que puedes conectarte por SSH
ssh -p 22 faservin@192.168.1.93

# Si falla, verifica:
# 1. ¿El servidor está encendido?
# 2. ¿La IP es correcta?
# 3. ¿Tienes acceso a la red?
```

### Problema: "Port already in use"
```bash
# Ver qué proceso usa el puerto
sudo lsof -i :27018

# Cerrar proceso específico
kill -9 <PID>

# Cerrar todos los túneles SSH
pkill -f "ssh.*27018"
```

### Problema: "MongoDB no responde"
```bash
# 1. Verificar que MongoDB está corriendo en el servidor remoto
ssh faservin@192.168.1.93 "systemctl status mongod"

# 2. Verificar que escucha en 127.0.0.1:27017
ssh faservin@192.168.1.93 "ss -tulpn | grep 27017"

# 3. Verificar que QUALITY_IEMSA existe
ssh faservin@192.168.1.93 "mongosh --eval 'db.getMongo().getDBNames()'"
```

### Problema: "AutoSSH se desconecta constantemente"
```bash
# Aumentar intervalo de keep-alive
export AUTOSSH_POLL=120  # 2 minutos
./setup_mongo_tunnel_autossh.sh
```

## 🔐 Uso en MongoDB Compass

1. Asegúrate de que el túnel está activo
2. Abre MongoDB Compass
3. **Connection String:**
   ```
   mongodb://127.0.0.1:27018
   ```
4. Click en "Connect"
5. Deberías ver la base de datos `QUALITY_IEMSA`

## 🐍 Uso en Aplicación Flask

La aplicación ya está configurada automáticamente:

```python
# db.py
MONGO_URI = "mongodb://127.0.0.1:27017"          # MongoDB local
TRAINING_MONGO_URI = "mongodb://127.0.0.1:27018"  # MongoDB remoto vía túnel

# La app usa:
# - get_client() → Puerto 27017 (local)
# - get_training_client() → Puerto 27018 (remoto vía túnel)
```

## 🛑 Detener Túneles

### Túnel básico
```bash
ps aux | grep ssh | grep 27018 | awk '{print $2}' | xargs kill
```

### AutoSSH
```bash
pkill -f "autossh.*27018"
```

## 📊 Checklist de Inicio

Antes de ejecutar la aplicación Flask:

- [ ] MongoDB local está corriendo (puerto 27017)
- [ ] Túnel SSH está activo (puerto 27018)
- [ ] Puedes acceder a `mongodb://127.0.0.1:27018`
- [ ] QUALITY_IEMSA existe y tiene máscaras

```bash
# Verificación rápida
mongosh "mongodb://127.0.0.1:27017" --eval "db.getMongo().getDBNames()"  # Local
mongosh "mongodb://127.0.0.1:27018" --eval "db.getMongo().getDBNames()"  # Remoto
```

## 🔄 Script de Inicio Completo

Crea este archivo para automatizar todo:

```bash
#!/bin/bash
# start_dashboard.sh

echo "🚀 Iniciando Dashboard de Segmentación..."

# 1. Verificar MongoDB local
if ! mongosh "mongodb://127.0.0.1:27017" --eval "db.adminCommand('ping')" &>/dev/null; then
    echo "❌ MongoDB local no está corriendo. Iniciando..."
    sudo systemctl start mongod
    sleep 3
fi

# 2. Iniciar túnel SSH
echo "🔐 Configurando túnel SSH..."
./setup_mongo_tunnel_autossh.sh

# 3. Esperar a que el túnel esté listo
sleep 5

# 4. Iniciar aplicación Flask
echo "🌐 Iniciando aplicación Flask..."
source venv/bin/activate
python app.py
```

## 📝 Notas Adicionales

- **Seguridad**: El túnel SSH usa compresión y keep-alive para estabilidad
- **Rendimiento**: AutoSSH agrega overhead mínimo (~1-2% CPU)
- **Red**: Funciona en LAN (192.168.x.x) - no requiere internet
- **Firewall**: Si hay firewall, asegura que el puerto 22 (SSH) esté abierto

## 🆘 Soporte

Si los scripts fallan, revisa:
1. Variables de entorno
2. Permisos SSH
3. Estado del servidor remoto
4. Logs: `/tmp/autossh_mongo_27018.log`
