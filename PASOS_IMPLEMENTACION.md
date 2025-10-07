# 🚀 PASOS DE IMPLEMENTACIÓN - Dashboard Segmentación

## ✅ CAMBIOS REALIZADOS

Ya modifiqué los archivos necesarios:

1. **db.py** - Agregadas funciones `get_quality_db()` y `get_training_db()`
2. **app.py** - Conexiones a `Quality_dashboard` y `training_metrics`
3. **app.py** - Endpoint `/api/add-segmentador` ahora guarda en `Quality_dashboard`
4. **app.py** - Endpoint `/api/check-mongo-files` ahora usa `training_metrics.masks.files`

---

## 📋 PASO A PASO PARA PROBAR

### PASO 1: Verificar que MongoDB está corriendo

```bash
# Verificar estado de MongoDB
sudo systemctl status mongod

# Si no está corriendo, iniciarlo
sudo systemctl start mongod
```

### PASO 2: Verificar las bases de datos en MongoDB

```bash
# Conectar a MongoDB
mongosh

# Listar bases de datos
show dbs

# Deberías ver:
# - segmentacion_db
# - Quality_dashboard (se creará automáticamente)
# - training_metrics

# Verificar colecciones en training_metrics
use training_metrics
show collections

# Deberías ver:
# - masks.files
# - masks.chunks

# Salir
exit
```

### PASO 3: Reiniciar el servidor Flask

```bash
# Ir al directorio del proyecto
cd /home/faservin/proyectos/segmentacion-dashboard

# Activar entorno virtual
source venv/bin/activate

# Detener el servidor si está corriendo (Ctrl+C)

# Iniciar servidor
python app.py
```

**Deberías ver en la salida:**

```
✅ Conectado a segmentacion_db
✅ Conectado a Quality_dashboard.segmentadores
✅ {X} segmentadores cargados desde Quality_dashboard: ['Mauricio', 'Maggie', ...]
✅ Conectado a training_metrics.masks.files
 * Running on http://0.0.0.0:5000
```

### PASO 4: Probar endpoint de segmentadores

```bash
# En otra terminal, verificar lista actual
curl http://localhost:5000/api/segmentadores

# Deberías ver:
# {
#   "success": true,
#   "segmentadores": ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"],
#   "total": 5
# }
```

### PASO 5: Agregar un nuevo segmentador (PRUEBA CRÍTICA)

```bash
# Agregar segmentador de prueba
curl -X POST http://localhost:5000/api/add-segmentador \
  -H "Content-Type: application/json" \
  -d '{"name": "TestUsuario", "role": "Segmentador", "email": "test@test.com"}'

# Deberías ver:
# {
#   "success": true,
#   "message": "Segmentador 'TestUsuario' agregado y guardado en Quality_dashboard",
#   "segmentador": {
#     "name": "TestUsuario",
#     "role": "Segmentador",
#     "email": "test@test.com"
#   },
#   "team_size": 6
# }
```

### PASO 6: Verificar en MongoDB que se guardó

```bash
mongosh

use Quality_dashboard
db.segmentadores.find().pretty()

# Deberías ver todos los segmentadores incluyendo "TestUsuario"

exit
```

### PASO 7: Reiniciar servidor y verificar persistencia (PRUEBA CRÍTICA)

```bash
# Detener Flask (Ctrl+C en la terminal del servidor)

# Reiniciar
python app.py

# Deberías ver en la salida:
# ✅ 6 segmentadores cargados desde Quality_dashboard: ['Mauricio', 'Maggie', 'Ceci', 'Flor', 'Ignacio', 'TestUsuario']
```

```bash
# Verificar API
curl http://localhost:5000/api/segmentadores

# Deberías ver "TestUsuario" en la lista
```

### PASO 8: Verificar archivos en training_metrics (IMPORTANTE)

```bash
# Verificar archivos de máscaras
curl http://localhost:5000/api/check-mongo-files

# Deberías ver:
# {
#   "success": true,
#   "total_files": X,
#   "recent_files": [...],
#   "batch_patterns": {
#     "batch_XXX": ["archivo1.tar.xz", ...],
#     ...
#   },
#   "database": "training_metrics",
#   "collection": "masks.files",
#   "message": "Se encontraron X archivos en training_metrics.masks.files"
# }
```

### PASO 9: Limpiar segmentador de prueba (Opcional)

```bash
mongosh

use Quality_dashboard
db.segmentadores.deleteOne({"name": "TestUsuario"})

exit
```

---

## ✅ VERIFICACIÓN DE ÉXITO

| Prueba | Esperado | Estado |
|--------|----------|--------|
| Servidor inicia sin errores | ✅ Logs de conexión exitosa | ⬜ |
| Segmentadores se cargan de Quality_dashboard | ✅ Lista de segmentadores en consola | ⬜ |
| Agregar segmentador guarda en DB | ✅ Documento en Quality_dashboard | ⬜ |
| Segmentador persiste después de reinicio | ✅ Aparece en lista tras reiniciar | ⬜ |
| Archivos de training_metrics se listan | ✅ JSON con archivos y patrones | ⬜ |

---

## 🔧 ESTRUCTURA DE MONGODB FINAL

```
MongoDB
├── segmentacion_db
│   ├── batches (asignaciones de folders)
│   └── masks (GridFS - no usado actualmente)
│
├── Quality_dashboard
│   └── segmentadores (NUEVO - aquí se guardan segmentadores)
│        ├── {name: "Mauricio", role: "Segmentador", email: "", created_at: "..."}
│        ├── {name: "Maggie", ...}
│        └── ...
│
└── training_metrics
    ├── masks.files (archivos de máscaras subidas)
    └── masks.chunks (bloques GridFS)
```

---

## 🌐 ACCESO REMOTO (LEÓN ↔ IRAPUATO)

### Opción 1: SSH Tunnel (Recomendada)

**En León - Terminal 1:**

```bash
# Crear túnel SSH a Irapuato
ssh -L 27017:localhost:27017 faservin@IP_SERVIDOR_IRAPUATO

# Dejar corriendo este comando
```

**En León - Terminal 2:**

```bash
# Ahora MongoDB de Irapuato está disponible en localhost:27017
cd /home/faservin/proyectos/segmentacion-dashboard
source venv/bin/activate

# Verificar conexión
mongosh mongodb://localhost:27017 --eval "db.stats()"

# Ejecutar app
python app.py
```

### Opción 2: Conexión Directa con Autenticación

**En Irapuato (servidor):**

```bash
# Editar configuración de MongoDB
sudo nano /etc/mongod.conf

# Cambiar:
net:
  bindIp: 0.0.0.0  # Permitir conexiones externas
  port: 27017

# Guardar y reiniciar
sudo systemctl restart mongod

# Crear usuario
mongosh
use admin
db.createUser({
  user: "admin_dashboard",
  pwd: "TU_PASSWORD_SEGURO",
  roles: [
    { role: "readWrite", db: "segmentacion_db" },
    { role: "readWrite", db: "Quality_dashboard" },
    { role: "readWrite", db: "training_metrics" }
  ]
})
exit
```

**En León:**

```bash
# Configurar URI con autenticación
export MONGO_URI="mongodb://admin_dashboard:TU_PASSWORD_SEGURO@IP_IRAPUATO:27017"

# Ejecutar app
python app.py
```

### Opción 3: Montar Carpeta Remota (Para DATA_DIRECTORY)

```bash
# En León - instalar sshfs
sudo apt install sshfs

# Crear punto de montaje
mkdir -p /mnt/irapuato

# Montar carpeta remota
sshfs faservin@IP_IRAPUATO:/home/faservin/american_project /mnt/irapuato

# Configurar Flask
export DATA_DIRECTORY="/mnt/irapuato"
python app.py

# Para desmontar
fusermount -u /mnt/irapuato
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Error: "Quality_dashboard no disponible"

```bash
# Verificar que MongoDB está corriendo
sudo systemctl status mongod

# Verificar que puedes conectar
mongosh mongodb://localhost:27017

# Verificar URI en app
echo $MONGO_URI
```

### Error: "training_metrics.masks.files no disponible"

```bash
# Verificar que la base existe
mongosh
show dbs
use training_metrics
show collections

# Debería aparecer masks.files
```

### Los segmentadores no se guardan

```bash
# Ver logs del servidor Flask
# Buscar:
# ✅ Segmentador 'XXX' guardado en Quality_dashboard y memoria

# Verificar en MongoDB
mongosh
use Quality_dashboard
db.segmentadores.find()
```

### No se listan archivos de training_metrics

```bash
# Verificar que hay archivos
mongosh
use training_metrics
db.getCollection("masks.files").countDocuments()

# Si es 0, no hay archivos subidos aún
# Si es > 0, verificar endpoint
curl http://localhost:5000/api/check-mongo-files
```

---

## 📞 SIGUIENTE PASO: SINCRONIZACIÓN AUTOMÁTICA

Una vez que funcione todo, podemos implementar un endpoint que:

1. Lee `training_metrics.masks.files`
2. Identifica qué batches tienen máscaras
3. Actualiza automáticamente el campo `mongo_uploaded` en `segmentacion_db.batches`

Esto se puede hacer con:

```bash
curl -X POST http://localhost:5000/api/sync-batch-files
```

(Este endpoint ya existe en tu código, solo hay que actualizarlo para usar `training_masks_col`)

---

## ✅ CHECKLIST FINAL

- [ ] MongoDB corriendo
- [ ] Bases de datos existen (segmentacion_db, Quality_dashboard, training_metrics)
- [ ] Servidor Flask inicia sin errores
- [ ] Logs muestran "✅ Conectado a Quality_dashboard.segmentadores"
- [ ] Logs muestran "✅ Conectado a training_metrics.masks.files"
- [ ] Segmentadores se cargan automáticamente
- [ ] Agregar segmentador funciona (POST /api/add-segmentador)
- [ ] Segmentador persiste después de reiniciar
- [ ] Archivos de training_metrics se listan (GET /api/check-mongo-files)
- [ ] Conexión remota funciona (si aplica)

---

**¿TODO FUNCIONANDO?** ✅

Si todos los checks están OK, el sistema está listo para:

1. Agregar/remover segmentadores persistentemente
2. Verificar qué batches tienen máscaras en training_metrics
3. Gestionar remotamente desde León

---

**Última actualización:** 2025-10-07
**Versión:** 1.0
