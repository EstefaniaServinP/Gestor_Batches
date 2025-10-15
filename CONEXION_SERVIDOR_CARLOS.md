# 🔐 Conexión al Servidor MongoDB de Carlos

## 📊 Datos de Conexión

- **Servidor:** 189.187.242.54
- **Usuario SSH:** carlos
- **Usuario MongoDB:** carlos
- **Password MongoDB:** EnervDeepEye0930
- **Puerto MongoDB remoto:** 27017
- **Puerto local (túnel):** 27018
- **authSource:** admin

---

## 🚀 Inicio Rápido (3 Pasos)

### 1️⃣ Verificar el servidor y encontrar máscaras
```bash
./verificar_servidor_carlos.sh
```

Este script:
- ✅ Abre el túnel SSH automáticamente
- ✅ Se conecta con autenticación
- ✅ Lista todas las bases de datos
- ✅ Busca las máscaras en QUALITY_IEMSA y seg_lab
- ✅ Muestra cuántas máscaras hay

### 2️⃣ Una vez verificado, iniciar la aplicación
```bash
python app.py
```

### 3️⃣ Acceder a las máscaras
Ir a: http://localhost:5000/masks

---

## 🔧 Método Manual (Si prefieres hacerlo paso a paso)

### 1. Cerrar túneles previos
```bash
pkill -f "L 27018:localhost:27017" 2>/dev/null || true
sleep 2
```

### 2. Abrir túnel SSH
```bash
ssh -f -N -L 27018:localhost:27017 carlos@189.187.242.54
```

**Nota:** Te pedirá la contraseña SSH de carlos (puede ser diferente a la de MongoDB)

### 3. Verificar túnel activo
```bash
ss -ltnp | grep 27018
```

### 4. Probar conexión a MongoDB
```bash
# Listar bases de datos
mongosh "mongodb://carlos:EnervDeepEye0930@localhost:27018/?authSource=admin" \
  --eval "db.getMongo().getDBNames()"

# Ver colecciones en QUALITY_IEMSA
mongosh "mongodb://carlos:EnervDeepEye0930@localhost:27018/QUALITY_IEMSA?authSource=admin" \
  --eval "db.getCollectionNames()"

# Contar máscaras
mongosh "mongodb://carlos:EnervDeepEye0930@localhost:27018/QUALITY_IEMSA?authSource=admin" \
  --eval "db['training_metrics.masks.files'].countDocuments()"
```

### 5. Si las máscaras están en seg_lab (alternativa)
```bash
mongosh "mongodb://carlos:EnervDeepEye0930@localhost:27018/seg_lab?authSource=admin" \
  --eval "db['masks.files'].countDocuments()"
```

---

## 🔍 MongoDB Compass

Si quieres visualizar con Compass:

**Connection String:**
```
mongodb://carlos:EnervDeepEye0930@localhost:27018/?authSource=admin
```

O en el formulario de Compass:
- **Host:** localhost
- **Port:** 27018
- **Authentication:** Username/Password
- **Username:** carlos
- **Password:** EnervDeepEye0930
- **Authentication Database:** admin

---

## ⚙️ Configuración de la App

La app ya está configurada en `db.py`:

```python
# Conexión con autenticación al servidor de Carlos
TRAINING_MONGO_URI = "mongodb://carlos:EnervDeepEye0930@127.0.0.1:27018/QUALITY_IEMSA?authSource=admin"
```

Si las máscaras están en `seg_lab`, edita:
```python
TRAINING_DB_NAME = "seg_lab"  # En lugar de "QUALITY_IEMSA"
```

---

## 🛑 Cerrar Túnel

```bash
# Opción 1: Por proceso
ps aux | grep "ssh.*27018" | awk '{print $2}' | xargs kill -9

# Opción 2: Por patrón
pkill -f "L 27018:localhost:27017"
```

---

## 🔐 Variables de Entorno (Opcional - Mayor Seguridad)

Para no dejar la contraseña en el código:

```bash
# Crear archivo .env
cat > .env << 'EOF'
TRAINING_MONGO_USER=carlos
TRAINING_MONGO_PASS=EnervDeepEye0930
TRAINING_MONGO_URI=mongodb://carlos:EnervDeepEye0930@127.0.0.1:27018/QUALITY_IEMSA?authSource=admin
EOF

# La app las leerá automáticamente
python app.py
```

---

## ❌ Solución de Problemas

### Error: "Authentication failed"
```bash
# Verificar credenciales directamente en el servidor
ssh carlos@189.187.242.54
mongosh -u carlos -p EnervDeepEye0930 --authenticationDatabase admin
show dbs
exit
exit
```

### Error: "Connection refused" al abrir túnel SSH
```bash
# ¿Carlos tiene SSH habilitado?
ssh carlos@189.187.242.54 "echo 'SSH OK'"

# ¿El firewall permite el puerto 22?
# Pide a Carlos que verifique: sudo ufw status
```

### Error: "MongoDB no responde"
```bash
# Verificar que MongoDB está corriendo en el servidor de Carlos
ssh carlos@189.187.242.54 "systemctl status mongod"

# Verificar que escucha en 127.0.0.1:27017
ssh carlos@189.187.242.54 "ss -tulpn | grep 27017"
```

### Las máscaras no aparecen
```bash
# Ejecuta el script de verificación
./verificar_servidor_carlos.sh

# Te dirá en qué base de datos están las máscaras
# Luego actualiza TRAINING_DB_NAME en db.py
```

---

## 📋 Checklist Pre-inicio

Antes de iniciar la app Flask:

- [ ] Túnel SSH activo: `ss -ltnp | grep 27018`
- [ ] MongoDB local corriendo: `mongosh "mongodb://127.0.0.1:27017" --eval "db.version()"`
- [ ] MongoDB remoto accesible: `mongosh "mongodb://carlos:EnervDeepEye0930@localhost:27018/?authSource=admin" --eval "db.version()"`
- [ ] Máscaras localizadas: Ejecutar `./verificar_servidor_carlos.sh`

---

## 🎯 Arquitectura Final

```
┌─────────────────────────────────────────────────────────┐
│  TU LAPTOP                                              │
│                                                         │
│  MongoDB Local (127.0.0.1:27017)                       │
│  ├── segmentacion_db                                   │
│  └── Quality_dashboard                                 │
│                                                         │
│  ┌────────────────────────────────────────────┐       │
│  │  Túnel SSH (puerto 27018)                  │       │
│  │  ssh -L 27018:localhost:27017 carlos@...   │       │
│  └────────────────────────────────────────────┘       │
│                   ▲                                     │
│                   │                                     │
│  Flask App ───────┴─────────────────────────────────  │
└─────────────────────────────────────────────────────────┘
                         │
                         │ SSH Tunnel (autenticado)
                         ▼
┌─────────────────────────────────────────────────────────┐
│  SERVIDOR DE CARLOS (189.187.242.54)                   │
│                                                         │
│  MongoDB (127.0.0.1:27017)                             │
│  Usuario: carlos / Password: EnervDeepEye0930          │
│                                                         │
│  ├── QUALITY_IEMSA                                     │
│  │   └── training_metrics.masks.files                 │
│  └── seg_lab                                           │
│      └── masks.files (?)                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Flujo de Trabajo Diario

```bash
# 1. Abrir túnel y verificar
./verificar_servidor_carlos.sh

# 2. Iniciar app
python app.py

# 3. Acceder
# http://localhost:5000/masks

# 4. Al terminar, cerrar túnel
pkill -f "L 27018"
```

---

**¡Listo!** Con esto deberías poder conectarte al servidor de Carlos y ver las máscaras. 🎉
