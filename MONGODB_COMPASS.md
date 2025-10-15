# 🧭 Guía de MongoDB Compass

## 📊 Conexiones Disponibles

### 1️⃣ MongoDB Local (Batches y Segmentadores)

**Connection String:**
```
mongodb://127.0.0.1:27017
```

**Bases de datos:**
- `segmentacion_db` → batches, team
- `Quality_dashboard` → segmentadores

---

### 2️⃣ MongoDB Remoto (Máscaras) - Requiere Túnel SSH

**⚠️ IMPORTANTE:** Primero abre el túnel SSH:
```bash
ssh -f -N -L 27019:127.0.0.1:27017 carlos@192.168.1.93
```

**Connection String:**
```
mongodb://127.0.0.1:27019/QUALITY_IEMSA?directConnection=true
```

**Base de datos:**
- `QUALITY_IEMSA` → training_metrics.masks.files

---

## 🔌 Cómo Conectarse en Compass

### Opción A: Pegar Connection String

1. Abre MongoDB Compass
2. Click en **"New Connection"**
3. Pega el connection string completo
4. Click en **"Connect"**

### Opción B: Formulario Manual

**Para MongoDB Local (27017):**
- **Host:** localhost
- **Port:** 27017
- **Authentication:** None
- Click **"Connect"**

**Para MongoDB Remoto (27019):**
- **Host:** localhost
- **Port:** 27019
- **Authentication:** None
- **Advanced Options:**
  - **Direct Connection:** ✅ Activado
- Click **"Connect"**

---

## 🔍 Queries Útiles en Compass

### Ver Máscaras
1. Conectar a `mongodb://127.0.0.1:27019`
2. Seleccionar base de datos: **QUALITY_IEMSA**
3. Seleccionar colección: **training_metrics.masks.files**
4. En la pestaña "Documents", ejecutar:

```javascript
// Ver todas las máscaras
{}

// Buscar máscara específica
{ "filename": /batch_20250909T0034/ }

// Contar máscaras
// (En la pestaña Aggregations)
[
  { $count: "total" }
]
```

### Ver Batches
1. Conectar a `mongodb://127.0.0.1:27017`
2. Seleccionar base de datos: **segmentacion_db**
3. Seleccionar colección: **batches**
4. Filtros útiles:

```javascript
// Batches asignados
{ "assignee": { $ne: null, $ne: "" } }

// Batches de un segmentador específico
{ "assignee": "Mauricio" }

// Batches pendientes
{ "status": "NS" }

// Batches con máscaras subidas
{ "mongo_uploaded": true }
```

### Cruzar Batches con Máscaras

**Pipeline de Agregación** (En pestaña Aggregations de `batches`):

```javascript
[
  // 1. Proyectar campos necesarios
  {
    $project: {
      id: 1,
      assignee: 1,
      status: 1,
      mongo_uploaded: 1,
      // Extraer identificador del batch
      batch_identifier: {
        $regexFind: {
          input: "$id",
          regex: /batch_(.+)/
        }
      }
    }
  },
  // 2. Crear campo limpio
  {
    $addFields: {
      batch_id_clean: {
        $arrayElemAt: ["$batch_identifier.captures", 0]
      }
    }
  },
  // 3. Lookup a máscaras (requiere conexión a ambos MongoDB)
  // Nota: Este paso no funciona cross-database en Compass
  // Usar el script Python en su lugar
]
```

---

## ⚠️ Troubleshooting

### Error: "Connection refused" en puerto 27019
```bash
# Verificar que el túnel está activo
ss -ltnp | grep 27019

# Si no está, abrirlo:
ssh -f -N -L 27019:127.0.0.1:27017 carlos@192.168.1.93
```

### Error: "Server selection timed out"
```bash
# Verificar que MongoDB está corriendo
# Local:
sudo systemctl status mongod

# Remoto (desde túnel):
mongosh "mongodb://127.0.0.1:27019" --eval "db.adminCommand('ping')"
```

### No veo las colecciones
- Verifica que seleccionaste la **base de datos correcta**
- En el panel izquierdo, haz click en el nombre de la base de datos
- Las colecciones aparecerán debajo

---

## 📝 Cheat Sheet - Strings de Conexión

```bash
# Local - Batches
mongodb://127.0.0.1:27017

# Local - Segmentadores
mongodb://127.0.0.1:27017/Quality_dashboard

# Remoto - Máscaras (requiere túnel SSH)
mongodb://127.0.0.1:27019/QUALITY_IEMSA?directConnection=true

# Con autenticación (si aplica):
mongodb://usuario:password@127.0.0.1:27019/QUALITY_IEMSA?authSource=admin&directConnection=true
```

---

## 🚀 Workflow Recomendado

```bash
# 1. Abrir túnel SSH
ssh -f -N -L 27019:127.0.0.1:27017 carlos@192.168.1.93

# 2. Verificar health check
./health_check.sh

# 3. Abrir Compass y conectar a ambos MongoDB

# 4. Al terminar, cerrar túnel
pkill -f "L 27019"
```
