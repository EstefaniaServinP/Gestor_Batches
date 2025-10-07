# 📋 Análisis y Plan de Solución - Dashboard de Segmentación

> **Fecha:** 7 de Octubre, 2025
> **Proyecto:** Dashboard de Segmentación de Imágenes Médicas
> **Ubicación:** León → Irapuato (Trabajo Remoto)

---

## 🎯 RESUMEN EJECUTIVO

### Situación Actual
Tienes un dashboard funcional de Flask para gestionar la asignación de folders a segmentadores. Los folders provienen de un archivo JSON y cuando los segmentadores trabajan con las imágenes, las suben a MongoDB en la colección `training_metrics.masks.files`.

### Problemas Identificados

1. **Los segmentadores se pierden al reiniciar el servidor** ⚠️ CRÍTICO
   - Se guardan solo en memoria (`CREW_MEMBERS`)
   - No persisten en MongoDB
   - Se pierden al reiniciar el servidor Flask

2. **Falta sincronización con MongoDB para verificar folders trabajados** 🔄
   - Necesitas verificar qué folders ya están en MongoDB (colección `training_metrics.masks.files`)
   - Comparar con el archivo JSON local
   - Marcar visualmente cuáles ya fueron segmentados

3. **Acceso remoto León ↔ Irapuato** 🌐
   - Necesitas gestionar desde León mientras la oficina está en Irapuato
   - Requiere conexión remota segura a MongoDB

---

## 📊 ARQUITECTURA ACTUAL

### Componentes Identificados

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTE (Browser)                         │
│  - dashboard.html (gestión de batches)                      │
│  - batch_management.html (asignar folders)                  │
│  - team.html (vista del equipo)                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ HTTP/REST API
                   │
┌──────────────────▼──────────────────────────────────────────┐
│               FLASK APP (app.py)                             │
│  - Rutas de API (/api/batches, /api/segmentadores)         │
│  - Lógica de negocio                                        │
│  - Variable global: CREW_MEMBERS (❌ se pierde)             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ MongoDB Driver (pymongo)
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    MONGODB                                   │
│  ┌────────────────────────────────────────────────┐         │
│  │ Base de datos: segmentacion_db                 │         │
│  │                                                 │         │
│  │ Colecciones:                                    │         │
│  │  • batches (asignaciones)          ✅          │         │
│  │  • masks (GridFS - máscaras)       ✅          │         │
│  │  • segmentadores                   ❌ FALTA    │         │
│  └────────────────────────────────────────────────┘         │
│  ┌────────────────────────────────────────────────┐         │
│  │ Base de datos: training_metrics                │         │
│  │                                                 │         │
│  │ Colecciones:                                    │         │
│  │  • masks.files (archivos subidos)  ✅          │         │
│  │  • masks.chunks (bloques GridFS)   ✅          │         │
│  └────────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                   │
                   │ Lectura de folders reales
                   │
┌──────────────────▼──────────────────────────────────────────┐
│         FILESYSTEM (/home/faservin/american_project)        │
│  - batch_1/                                                  │
│  - batch_2/                                                  │
│  - batch_XXX/                                                │
│  - batches.json (lista de folders) ✅                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 ANÁLISIS DETALLADO DE PROBLEMAS

### 1. Problema: Segmentadores se pierden al reiniciar

#### Código Actual (app.py)

```python
# Línea 82 - Variable global
CREW_MEMBERS = []

# Línea 52-79 - Carga inicial desde MongoDB
def load_segmentadores_from_db():
    global CREW_MEMBERS, segmentadores_col
    try:
        if segmentadores_col is not None:
            count = segmentadores_col.count_documents({})
            if count > 0:
                # Carga desde DB ✅
                segmentadores = list(segmentadores_col.find({}, {"_id": 0, "name": 1}).sort("name", 1))
                CREW_MEMBERS = [seg["name"] for seg in segmentadores]
            else:
                # Primera vez: guarda iniciales ✅
                initial_segmentadores = ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"]
                for name in initial_segmentadores:
                    segmentadores_col.insert_one({
                        "name": name,
                        "role": "Segmentador",
                        "email": "",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                CREW_MEMBERS = initial_segmentadores
```

**¿Qué está bien?**
- Ya existe la colección `segmentadores` en MongoDB ✅
- Ya carga automáticamente en `init_db()` ✅
- Ya guarda los iniciales si está vacía ✅

#### Código con Problema (app.py:340-396)

```python
@app.route("/api/add-segmentador", methods=["POST"])
def add_segmentador():
    global CREW_MEMBERS

    name = data.get("name", "").strip()

    # Solo agrega a memoria ❌
    CREW_MEMBERS.append(name)

    print(f"👤 Nuevo segmentador agregado: {name}")

    # ❌❌❌ NO GUARDA EN MONGODB ❌❌❌

    return jsonify({
        "success": True,
        "message": f"Segmentador '{name}' agregado exitosamente",
        ...
    })
```

**Problema identificado:**
- ✅ Agrega a `CREW_MEMBERS` (memoria)
- ❌ **NO guarda en MongoDB** → se pierde al reiniciar

**Solución:**
```python
@app.route("/api/add-segmentador", methods=["POST"])
def add_segmentador():
    global CREW_MEMBERS

    name = data.get("name", "").strip()
    role = data.get("role", "Segmentador General")
    email = data.get("email", "")

    # Verificar duplicados
    if name in CREW_MEMBERS:
        return jsonify({"success": False, "error": "Ya existe"}), 400

    # ✅ GUARDAR EN MONGODB
    segmentadores_col.insert_one({
        "name": name,
        "role": role,
        "email": email,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Actualizar memoria
    CREW_MEMBERS.append(name)

    return jsonify({"success": True, "message": "Guardado correctamente"})
```

---

### 2. Problema: Sincronización con MongoDB (training_metrics.masks.files)

#### Situación Actual

```python
# app.py:31-36 - Conexiones
db = None  # Base: segmentacion_db
batches_col = None
masks_col = None  # ✅ Esta es para la colección "masks" en segmentacion_db
segmentadores_col = None
```

**Problema:**
- La variable `masks_col` apunta a `segmentacion_db.masks` ✅
- Pero las máscaras reales están en `training_metrics.masks.files` ❌
- **Hay dos bases de datos diferentes:**
  - `segmentacion_db` → gestión del dashboard
  - `training_metrics` → datos de trabajo real (máscaras subidas)

#### Código Actual de Verificación (app.py:413-497)

```python
@app.route("/api/check-mongo-files", methods=["GET"])
def check_mongo_files():
    # Usa masks_col que apunta a segmentacion_db.masks ❌
    files = list(masks_col.find({}, {"filename": 1, "uploadDate": 1}))

    # Busca patrones de batches
    batch_patterns = {}
    for file in files:
        batch_matches = re.findall(r'[Bb]atch[_\-]?(\d+)', filename)
        ...
```

**Problema:**
- Busca en la base equivocada
- Necesita conectar a `training_metrics.masks.files`

#### Solución

```python
# db.py - Agregar función para conectar a training_metrics
def get_training_db():
    """Retorna la base de datos training_metrics"""
    ok, err = ping_client()
    if ok:
        return get_client()["training_metrics"]
    return None

# app.py - Agregar conexión global
training_db = None
training_masks_col = None  # training_metrics.masks.files

def init_db():
    global db, batches_col, masks_col, segmentadores_col
    global training_db, training_masks_col  # ✅ Nueva conexión

    # Base principal (segmentacion_db)
    db = get_db(raise_on_fail=False)
    if db is not None:
        batches_col = db["batches"]
        masks_col = db["masks"]
        segmentadores_col = db["segmentadores"]
        create_indexes()
        load_segmentadores_from_db()

    # Base de métricas (training_metrics)  ✅ NUEVO
    training_db = get_training_db()
    if training_db is not None:
        training_masks_col = training_db["masks.files"]
        print("✅ Conectado a training_metrics.masks.files")
```

**Ahora puedes verificar los archivos correctamente:**

```python
@app.route("/api/check-mongo-files", methods=["GET"])
def check_mongo_files():
    try:
        # ✅ Usar la colección correcta
        files = list(training_masks_col.find(
            {},
            {"filename": 1, "uploadDate": 1, "metadata": 1, "length": 1}
        ).sort("uploadDate", -1).limit(100))

        # Extraer patrones de batches
        batch_patterns = {}
        for file in files:
            filename = file.get("filename", "")
            batch_matches = re.findall(r'[Bb]atch[_\-]?(\d+)', filename)
            for match in batch_matches:
                batch_key = f"batch_{match}"
                if batch_key not in batch_patterns:
                    batch_patterns[batch_key] = []
                batch_patterns[batch_key].append(filename)

        return jsonify({
            "success": True,
            "total_files": len(files),
            "batch_patterns": batch_patterns,
            "message": f"Se encontraron {len(files)} archivos en training_metrics"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
```

---

### 3. Problema: Acceso Remoto (León ↔ Irapuato)

#### Situación
- Estás en León
- MongoDB está en Irapuato
- Necesitas gestionar remotamente

#### Consideraciones de Seguridad

**Opciones de Conexión:**

1. **VPN (Recomendado)** ⭐⭐⭐⭐⭐
   ```bash
   # Conectar VPN primero
   sudo openvpn --config irapuato-vpn.ovpn

   # Luego usar MongoDB como si fuera local
   export MONGO_URI="mongodb://192.168.1.100:27017"
   ```

2. **SSH Tunnel (Alternativa segura)** ⭐⭐⭐⭐
   ```bash
   # Crear túnel SSH
   ssh -L 27017:localhost:27017 usuario@servidor-irapuato.com

   # En otra terminal, conectar a localhost
   export MONGO_URI="mongodb://localhost:27017"
   python app.py
   ```

3. **MongoDB Atlas (Cloud - más fácil pero costo)** ⭐⭐⭐
   ```bash
   # Migrar a MongoDB Atlas
   export MONGO_URI="mongodb+srv://usuario:password@cluster.mongodb.net"
   ```

4. **Exposición directa con autenticación** ⭐⭐ (No recomendado)
   ```bash
   # MongoDB con usuario/contraseña
   export MONGO_URI="mongodb://admin:password@servidor-irapuato.com:27017"
   ```

#### Configuración Recomendada

```python
# .env (en León)
MONGO_URI=mongodb://localhost:27017  # Conectado via VPN o SSH tunnel
MONGO_DB=segmentacion_db
DATA_DIRECTORY=/mnt/shared/american_project  # Carpeta compartida via NFS/SSHFS
```

**Montar carpeta remota con SSHFS:**
```bash
# En León - montar carpeta de Irapuato
sudo apt install sshfs
mkdir -p /mnt/shared
sshfs usuario@servidor-irapuato:/home/faservin/american_project /mnt/shared
```

---

## 🔧 PLAN DE IMPLEMENTACIÓN

### Fase 1: Persistencia de Segmentadores (CRÍTICO) ⚡

**Tiempo estimado:** 15 minutos

#### Cambios Necesarios

**Archivo: `app.py`**

```python
# Línea 340-396 - Modificar endpoint add_segmentador
@app.route("/api/add-segmentador", methods=["POST"])
def add_segmentador():
    global CREW_MEMBERS, segmentadores_col

    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No se enviaron datos"}), 400

        name = data.get("name", "").strip()
        role = data.get("role", "Segmentador General")
        email = data.get("email", "")

        # Validar nombre
        if not name:
            return jsonify({"success": False, "error": "El nombre es requerido"}), 400

        # Verificar duplicados
        if name in CREW_MEMBERS:
            return jsonify({"success": False, "error": f"'{name}' ya existe"}), 400

        # ✅ GUARDAR EN MONGODB (NUEVO)
        if segmentadores_col is None:
            return jsonify({"success": False, "error": "DB no disponible"}), 503

        segmentadores_col.insert_one({
            "name": name,
            "role": role,
            "email": email,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Actualizar memoria
        CREW_MEMBERS.append(name)

        print(f"✅ Segmentador '{name}' guardado en MongoDB y memoria")

        return jsonify({
            "success": True,
            "message": f"Segmentador '{name}' agregado exitosamente",
            "segmentador": {"name": name, "role": role, "email": email},
            "team_size": len(CREW_MEMBERS)
        })

    except Exception as e:
        print(f"❌ Error agregando segmentador: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

**Agregar endpoint para eliminar segmentadores:**

```python
@app.route("/api/remove-segmentador", methods=["DELETE"])
def remove_segmentador():
    """Eliminar un segmentador del equipo"""
    global CREW_MEMBERS, segmentadores_col

    try:
        data = request.get_json()
        name = data.get("name", "").strip()

        if not name:
            return jsonify({"success": False, "error": "Nombre requerido"}), 400

        if name not in CREW_MEMBERS:
            return jsonify({"success": False, "error": f"'{name}' no existe"}), 404

        # Eliminar de MongoDB
        result = segmentadores_col.delete_one({"name": name})

        if result.deleted_count > 0:
            # Eliminar de memoria
            CREW_MEMBERS.remove(name)
            print(f"✅ Segmentador '{name}' eliminado")

            return jsonify({
                "success": True,
                "message": f"Segmentador '{name}' eliminado",
                "team_size": len(CREW_MEMBERS)
            })
        else:
            return jsonify({"success": False, "error": "No se pudo eliminar"}), 500

    except Exception as e:
        print(f"❌ Error eliminando segmentador: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

#### Verificación

```bash
# Después de implementar, probar:
curl -X POST http://localhost:5000/api/add-segmentador \
  -H "Content-Type: application/json" \
  -d '{"name": "TestUser", "role": "Segmentador", "email": "test@test.com"}'

# Reiniciar servidor
# Verificar que sigue apareciendo en /api/segmentadores
```

---

### Fase 2: Conexión a training_metrics.masks.files 🔄

**Tiempo estimado:** 20 minutos

#### Cambios en db.py

```python
# db.py - Agregar función
def get_training_db():
    """Retorna la base de datos training_metrics para consultar máscaras"""
    ok, err = ping_client()
    if ok:
        return get_client()["training_metrics"]
    msg = f"No se pudo conectar a training_metrics: {err}"
    print("⚠️", msg)
    return None
```

#### Cambios en app.py

```python
# app.py - Línea 31-36 - Agregar variables globales
db = None
batches_col = None
masks_col = None
segmentadores_col = None

# ✅ NUEVAS VARIABLES
training_db = None
training_masks_col = None  # Para training_metrics.masks.files

# app.py - Línea 38-50 - Modificar init_db()
def init_db():
    global db, batches_col, masks_col, segmentadores_col
    global training_db, training_masks_col  # ✅ NUEVO

    # Base principal
    db = get_db(raise_on_fail=False)
    if db is not None:
        batches_col = db["batches"]
        masks_col = db["masks"]
        segmentadores_col = db["segmentadores"]
        create_indexes()
        load_segmentadores_from_db()
    else:
        print("⚠️ segmentacion_db no disponible")

    # Base de métricas (training_metrics)  ✅ NUEVO
    from db import get_training_db
    training_db = get_training_db()
    if training_db is not None:
        training_masks_col = training_db["masks.files"]
        print("✅ Conectado a training_metrics.masks.files")
    else:
        print("⚠️ training_metrics no disponible")
```

#### Nuevo Endpoint: Sincronizar con training_metrics

```python
@app.route("/api/sync-with-training-metrics", methods=["POST"])
def sync_with_training_metrics():
    """
    Sincronizar batches con archivos reales en training_metrics.masks.files
    Marca qué batches ya tienen máscaras subidas
    """
    global batches_col, training_masks_col

    try:
        if training_masks_col is None:
            return jsonify({"success": False, "error": "training_metrics no disponible"}), 503

        # Obtener todos los archivos de training_metrics
        print("🔍 Consultando training_metrics.masks.files...")
        files = list(training_masks_col.find(
            {},
            {"filename": 1, "uploadDate": 1, "metadata": 1}
        ))

        print(f"📊 Encontrados {len(files)} archivos en training_metrics")

        # Agrupar por batch
        batches_with_masks = {}
        import re

        for file in files:
            filename = file.get("filename", "")
            # Buscar patrones: batch_XXX, Batch_XXX, masks_batch_XXX
            matches = re.findall(r'[Bb]atch[_\-]?(\d+)', filename)

            for match in matches:
                batch_id = f"batch_{match}"
                if batch_id not in batches_with_masks:
                    batches_with_masks[batch_id] = {
                        "files": [],
                        "latest_upload": None
                    }

                batches_with_masks[batch_id]["files"].append(filename)

                # Actualizar última fecha de subida
                upload_date = file.get("uploadDate")
                if upload_date:
                    if batches_with_masks[batch_id]["latest_upload"] is None:
                        batches_with_masks[batch_id]["latest_upload"] = upload_date
                    elif upload_date > batches_with_masks[batch_id]["latest_upload"]:
                        batches_with_masks[batch_id]["latest_upload"] = upload_date

        # Actualizar batches en segmentacion_db
        updated = 0
        for batch_id, info in batches_with_masks.items():
            result = batches_col.update_one(
                {"id": batch_id},
                {
                    "$set": {
                        "mongo_uploaded": True,
                        "training_metrics_info": {
                            "file_count": len(info["files"]),
                            "latest_upload": info["latest_upload"],
                            "files": info["files"][:5]  # Solo primeros 5
                        }
                    }
                }
            )

            if result.modified_count > 0:
                updated += 1
                print(f"✅ {batch_id}: {len(info['files'])} archivos encontrados")

        # Marcar batches SIN máscaras
        all_batches = list(batches_col.find({}, {"id": 1}))
        batches_without_masks = 0

        for batch in all_batches:
            batch_id = batch["id"]
            if batch_id not in batches_with_masks:
                batches_col.update_one(
                    {"id": batch_id},
                    {"$set": {"mongo_uploaded": False}}
                )
                batches_without_masks += 1

        return jsonify({
            "success": True,
            "total_files": len(files),
            "batches_with_masks": len(batches_with_masks),
            "batches_without_masks": batches_without_masks,
            "batches_updated": updated,
            "message": f"Sincronización completa: {len(batches_with_masks)} batches con máscaras"
        })

    except Exception as e:
        print(f"❌ Error en sincronización: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
```

#### Actualizar endpoint check-mongo-files

```python
@app.route("/api/check-mongo-files", methods=["GET"])
def check_mongo_files():
    """Verificar archivos en training_metrics.masks.files"""
    global training_masks_col

    try:
        if training_masks_col is None:
            return jsonify({"success": False, "error": "training_metrics no disponible"}), 503

        # ✅ Usar training_masks_col en vez de masks_col
        files = list(training_masks_col.find(
            {},
            {"filename": 1, "uploadDate": 1, "metadata": 1, "length": 1}
        ).sort("uploadDate", -1).limit(100))

        files_info = []
        for file in files:
            files_info.append({
                "filename": file.get("filename", "Sin nombre"),
                "uploadDate": file.get("uploadDate").isoformat() if file.get("uploadDate") else None,
                "size_mb": round(file.get("length", 0) / (1024*1024), 2) if file.get("length") else 0,
                "uploaded_by": file.get("metadata", {}).get("uploaded_by", "unknown")
            })

        # Contar archivos por patrón de batch
        batch_patterns = {}
        import re

        for file in files:
            filename = file.get("filename", "")
            batch_matches = re.findall(r'[Bb]atch[_\-]?(\d+)', filename)
            for match in batch_matches:
                batch_key = f"batch_{match}"
                if batch_key not in batch_patterns:
                    batch_patterns[batch_key] = []
                batch_patterns[batch_key].append(filename)

        return jsonify({
            "success": True,
            "total_files": len(files_info),
            "recent_files": files_info,
            "batch_patterns": batch_patterns,
            "database": "training_metrics",
            "collection": "masks.files",
            "message": f"Se encontraron {len(files_info)} archivos en training_metrics"
        })

    except Exception as e:
        print(f"❌ Error en check_mongo_files: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
```

---

### Fase 3: Configuración de Acceso Remoto 🌐

**Tiempo estimado:** 30 minutos

#### Opción 1: SSH Tunnel (Recomendada para empezar)

**En tu máquina (León):**

```bash
# 1. Crear script de conexión
cat > ~/scripts/connect-irapuato-db.sh << 'EOF'
#!/bin/bash
echo "🔒 Conectando a MongoDB en Irapuato via SSH tunnel..."

# Configurar variables
SERVER_USER="faservin"
SERVER_HOST="servidor-irapuato.local"  # O la IP
LOCAL_PORT=27017
REMOTE_PORT=27017

# Crear túnel
ssh -N -L ${LOCAL_PORT}:localhost:${REMOTE_PORT} ${SERVER_USER}@${SERVER_HOST}
EOF

chmod +x ~/scripts/connect-irapuato-db.sh

# 2. En una terminal, ejecutar el túnel
~/scripts/connect-irapuato-db.sh

# 3. En otra terminal, configurar Flask
export MONGO_URI="mongodb://localhost:27017"
export MONGO_DB="segmentacion_db"
export DATA_DIRECTORY="/mnt/shared/american_project"

# 4. Montar carpeta remota (opcional)
mkdir -p /mnt/shared
sshfs faservin@servidor-irapuato:/home/faservin/american_project /mnt/shared

# 5. Ejecutar app
cd ~/proyectos/segmentacion-dashboard
source venv/bin/activate
python app.py
```

#### Opción 2: VPN

**Si ya tienes VPN configurada:**

```bash
# Conectar VPN
sudo openvpn --config /etc/openvpn/irapuato.ovpn

# Configurar Flask con IP interna
export MONGO_URI="mongodb://192.168.1.100:27017"
export DATA_DIRECTORY="/mnt/shared/american_project"

python app.py
```

#### Opción 3: MongoDB con Autenticación Remota

**En el servidor (Irapuato):**

```bash
# Editar mongod.conf
sudo nano /etc/mongod.conf

# Agregar:
net:
  bindIp: 0.0.0.0  # Permitir conexiones externas
  port: 27017

security:
  authorization: enabled

# Crear usuario administrador
mongosh
use admin
db.createUser({
  user: "admin_dashboard",
  pwd: "PASSWORD_SEGURO_AQUI",
  roles: [
    { role: "readWrite", db: "segmentacion_db" },
    { role: "readWrite", db: "training_metrics" }
  ]
})

# Reiniciar MongoDB
sudo systemctl restart mongod
```

**En tu máquina (León):**

```bash
export MONGO_URI="mongodb://admin_dashboard:PASSWORD_SEGURO_AQUI@IP_IRAPUATO:27017"
python app.py
```

---

## 📝 CHECKLIST DE IMPLEMENTACIÓN

### ✅ Fase 1: Persistencia de Segmentadores

- [ ] Modificar `/api/add-segmentador` para guardar en MongoDB
- [ ] Crear endpoint `/api/remove-segmentador`
- [ ] Probar agregar segmentador
- [ ] Reiniciar servidor
- [ ] Verificar que persiste

### ✅ Fase 2: Conexión a training_metrics

- [ ] Agregar `get_training_db()` en `db.py`
- [ ] Agregar variables globales `training_db` y `training_masks_col` en `app.py`
- [ ] Modificar `init_db()` para conectar a `training_metrics`
- [ ] Crear endpoint `/api/sync-with-training-metrics`
- [ ] Actualizar `/api/check-mongo-files` para usar `training_masks_col`
- [ ] Probar sincronización

### ✅ Fase 3: Acceso Remoto

- [ ] Elegir método de conexión (SSH tunnel / VPN / Directo)
- [ ] Configurar conexión remota
- [ ] Probar conexión a MongoDB desde León
- [ ] Montar carpeta compartida (si aplica)
- [ ] Configurar variables de entorno
- [ ] Probar dashboard completo remotamente

---

## 🧪 PRUEBAS DE VERIFICACIÓN

### Prueba 1: Persistencia de Segmentadores

```bash
# Agregar segmentador
curl -X POST http://localhost:5000/api/add-segmentador \
  -H "Content-Type: application/json" \
  -d '{"name": "Roberto", "role": "Segmentador", "email": "roberto@test.com"}'

# Verificar en MongoDB
mongosh segmentacion_db
db.segmentadores.find().pretty()

# Reiniciar Flask
pkill -f "python app.py"
python app.py

# Verificar que sigue en el equipo
curl http://localhost:5000/api/segmentadores
# Debe aparecer "Roberto"
```

### Prueba 2: Sincronización con training_metrics

```bash
# Ejecutar sincronización
curl -X POST http://localhost:5000/api/sync-with-training-metrics

# Verificar batches actualizados
curl http://localhost:5000/api/batches?page=1&per_page=10

# Debe mostrar mongo_uploaded: true/false correctamente
```

### Prueba 3: Acceso Remoto

```bash
# Desde León, verificar conectividad
nc -zv IP_IRAPUATO 27017

# Probar conexión MongoDB
mongosh "mongodb://IP_IRAPUATO:27017/segmentacion_db" --eval "db.stats()"

# Ejecutar app
export MONGO_URI="mongodb://IP_IRAPUATO:27017"
python app.py

# Verificar endpoints
curl http://localhost:5000/api/check-mongo-files
```

---

## 📊 ESTRUCTURA DE DATOS

### Colección: segmentadores

```json
{
  "_id": ObjectId("..."),
  "name": "Mauricio",
  "role": "Segmentador Senior",
  "email": "mauricio@example.com",
  "created_at": "2025-10-07 12:00:00"
}
```

### Colección: batches (actualizada)

```json
{
  "_id": ObjectId("..."),
  "id": "batch_400",
  "assignee": "Flor",
  "folder": "/home/faservin/american_project/batch_400",
  "status": "S",
  "mongo_uploaded": true,
  "training_metrics_info": {
    "file_count": 3,
    "latest_upload": ISODate("2025-10-01T10:30:00Z"),
    "files": [
      "masks_batch_400.tar.xz",
      "batch_400_part1.zip",
      "batch_400_part2.zip"
    ]
  },
  "metadata": {
    "assigned_at": "2025-09-15",
    "due_date": "2025-09-30",
    "priority": "alta"
  }
}
```

### Colección: training_metrics.masks.files (referencia)

```json
{
  "_id": ObjectId("..."),
  "filename": "masks_batch_400.tar.xz",
  "uploadDate": ISODate("2025-10-01T10:30:00Z"),
  "length": 15728640,  // Tamaño en bytes
  "chunkSize": 261120,
  "metadata": {
    "uploaded_by": "flor",
    "batch_id": "batch_400"
  }
}
```

---

## 🔐 CONSIDERACIONES DE SEGURIDAD

### Para Producción

1. **Autenticación MongoDB**
   ```bash
   # Siempre usar usuario/contraseña
   export MONGO_URI="mongodb://user:password@host:27017/db?authSource=admin"
   ```

2. **No exponer MongoDB directamente a Internet**
   - Usar VPN o SSH tunnel
   - Firewall restrictivo (solo IPs conocidas)

3. **HTTPS para Flask**
   ```bash
   # Usar gunicorn con SSL
   gunicorn --certfile=cert.pem --keyfile=key.pem -b 0.0.0.0:443 app:app
   ```

4. **Variables de entorno seguras**
   ```bash
   # Usar .env (no commitear a git)
   cat > .env << EOF
   MONGO_URI=mongodb://user:password@host:27017
   MONGO_DB=segmentacion_db
   DATA_DIRECTORY=/path/to/data
   EOF

   # En app.py
   from dotenv import load_dotenv
   load_dotenv()
   ```

---

## 📞 CONTACTO Y SOPORTE

### Recursos

- Documentación MongoDB: https://www.mongodb.com/docs/
- Flask Documentation: https://flask.palletsprojects.com/
- pymongo Guide: https://pymongo.readthedocs.io/

### Comandos Útiles

```bash
# Ver logs de MongoDB
sudo tail -f /var/log/mongodb/mongod.log

# Verificar estado de MongoDB
sudo systemctl status mongod

# Probar conexión
mongosh "mongodb://localhost:27017/segmentacion_db" --eval "db.stats()"

# Ver procesos Python
ps aux | grep python

# Ver conexiones MongoDB activas
mongosh --eval "db.serverStatus().connections"
```

---

## 📋 RESUMEN DE ARCHIVOS A MODIFICAR

| Archivo | Cambios | Líneas Aprox |
|---------|---------|--------------|
| `db.py` | Agregar `get_training_db()` | +10 |
| `app.py` | Modificar `add_segmentador` | ~20 |
| `app.py` | Agregar `remove_segmentador` | +30 |
| `app.py` | Modificar `init_db()` | +10 |
| `app.py` | Agregar `sync_with_training_metrics` | +80 |
| `app.py` | Actualizar `check_mongo_files` | ~30 |
| `.env` (nuevo) | Variables de entorno | +5 |

**Total:** ~185 líneas de código

---

## ⏱️ TIEMPO ESTIMADO TOTAL

- Fase 1 (Persistencia): 15 minutos
- Fase 2 (Sincronización): 20 minutos
- Fase 3 (Remoto): 30 minutos
- Pruebas: 15 minutos

**Total: ~1.5 horas**

---

## 🎯 PRÓXIMOS PASOS RECOMENDADOS

1. ✅ Implementar Fase 1 (crítica)
2. ✅ Probar y verificar
3. ✅ Implementar Fase 2
4. ✅ Configurar acceso remoto
5. ⚠️ Considerar implementar autenticación (según doc PROBLEMAS_Y_MEJORAS.md)
6. ⚠️ Agregar tests automatizados
7. ⚠️ Dockerizar la aplicación

---

**Documento creado:** 2025-10-07
**Última actualización:** 2025-10-07
**Versión:** 1.0
**Autor:** Análisis del sistema existente
