# Problemas Solucionados - Dashboard de Segmentación

## Fecha: 2025-10-11

---

## 1. Error en Conexión a Base de Datos de Máscaras

### Problema:
- La aplicación intentaba conectarse a `training_metrics.masks.files` pero las máscaras están en `QUALITY_IEMSA.training_metrics.masks.files`
- Error: "No DB connection to training_metrics"

### Solución:
- Actualizado `db.py` línea 7: `TRAINING_DB_NAME = "QUALITY_IEMSA"`
- Actualizado `app.py` línea 73: `training_masks_col = training_db["training_metrics.masks.files"]`

### Archivos modificados:
- `db.py` (líneas 4-7)
- `app.py` (líneas 69-76, 142-154, 706-754, 756-875, 877-972)

---

## 2. Conflicto en Base de Datos de Segmentadores

### Problema:
- Al arreglar las máscaras, se cambió accidentalmente la base de datos de segmentadores
- Los segmentadores se buscaban en `QUALITY_IEMSA.segmentadores` en vez de `Quality_dashboard.segmentadores`
- No se podían agregar nuevos segmentadores

### Solución:
- Separar correctamente las dos bases de datos:
  - **Segmentadores**: `Quality_dashboard.segmentadores`
  - **Máscaras**: `QUALITY_IEMSA.training_metrics.masks.files`

### Archivos modificados:
- `db.py` (línea 6): `QUALITY_DB_NAME = "Quality_dashboard"`

---

## 3. Falta de Funcionalidad para Editar y Eliminar Segmentadores

### Problema:
- Los endpoints del backend (`/api/update-segmentador` y `/api/remove-segmentador`) existían pero no había interfaz de usuario
- No se podían editar ni eliminar segmentadores desde el frontend

### Solución:
- Agregados botones de acción (editar/eliminar) en las tarjetas de miembros
- Creado modal de edición
- Implementadas funciones JavaScript:
  - `showEditSegmentadorModal()` - Abre modal de edición
  - `updateSegmentador()` - Actualiza datos del segmentador
  - `confirmDeleteSegmentador()` - Pide confirmación antes de eliminar
  - `deleteSegmentador()` - Elimina el segmentador
- Los botones aparecen al hacer hover sobre las tarjetas

### Archivos modificados:
- `templates/team.html` (líneas 271-317, 614-657, 733-765, 977-1085)

---

## 4. Dashboard General y Dashboard Individual Desincronizados

### Problema:
- Los batches asignados desde `/assign` no aparecían en `/dashboard` o `/dashboard/<assignee>`
- El endpoint `/api/batches` cambió su formato de respuesta a paginado:
  ```json
  {
    "batches": [...],
    "pagination": {"page": 1, "per_page": 50, "total": 100}
  }
  ```
- El dashboard general esperaba recibir directamente un array de batches

### Solución:
- Actualizada la función `loadBatches()` en `dashboard.html` para:
  - Solicitar hasta 1000 batches (`?per_page=1000`)
  - Manejar correctamente la respuesta paginada extrayendo `data.batches`
  - Incluir fallback para formato anterior

### Código actualizado:
```javascript
// ANTES:
$.get('/api/batches')
  .done(function(data) {
    batches = data;  // ❌ Asumía que data es un array

// AHORA:
$.get('/api/batches?per_page=1000')
  .done(function(data) {
    if (data.batches) {
      batches = data.batches;  // ✅ Maneja formato paginado
    } else {
      batches = data;  // Fallback
    }
```

### Archivos modificados:
- `templates/dashboard.html` (líneas 827-848)

---

## 5. MongoDB Remoto - Máscaras en Servidor Externo

### Problema:
- La aplicación intentaba conectarse a `127.0.0.1:27018` pero no había MongoDB escuchando
- Las máscaras NO están en la laptop local, sino en un servidor remoto (de Carlos)
- Se requiere túnel SSH para acceder al MongoDB remoto

### Arquitectura Real:
```
MongoDB LOCAL (127.0.0.1:27017):
├── segmentacion_db (batches, team)
└── Quality_dashboard (segmentadores)

MongoDB REMOTO (servidor Carlos):
└── QUALITY_IEMSA (training_metrics.masks.files)
    └── Acceso vía túnel SSH → localhost:27018
```

### Solución:
1. **Scripts de Túnel SSH creados:**
   - `setup_mongo_tunnel.sh` - Túnel básico con reintentos
   - `setup_mongo_tunnel_autossh.sh` - Túnel persistente con reconexión automática

2. **Configuración en db.py:**
   - Conexión principal (27017): MongoDB local
   - Conexión secundaria (27018): MongoDB remoto vía túnel SSH

3. **Uso:**
```bash
# Opción 1: Túnel básico
./setup_mongo_tunnel.sh

# Opción 2: Túnel persistente (recomendado)
./setup_mongo_tunnel_autossh.sh

# Verificar túnel activo
ps aux | grep autossh | grep 27018

# Probar conexión
mongosh "mongodb://127.0.0.1:27018/QUALITY_IEMSA"
```

### Archivos modificados:
- `setup_mongo_tunnel.sh` (nuevo)
- `setup_mongo_tunnel_autossh.sh` (nuevo)
- `db.py` (líneas 4-14, 82-104)

---

## 6. Problema de Sincronización de Máscaras (masks_batch vs batch)

### Problema:
- Las máscaras en MongoDB se guardan con el nombre `masks_batch_20250909T0034`
- Los batches en la base de datos se llaman `batch_20250909T0034`
- La función de sincronización solo extraía números (`20250909`) en lugar del identificador completo (`20250909T0034`)
- Esto causaba colisiones entre batches con números similares
- El campo `mongo_uploaded` no se actualizaba correctamente

### Solución:
- Modificada la extracción del identificador para capturar el texto completo después de `batch_`
- Mejorado el patrón regex para buscar: `masks_batch_XXXX`, `batch_XXXX`, `Batch_XXXX`, `masks_XXXX`
- Agregados mensajes de debug para verificar coincidencias
- Ahora la sincronización detecta correctamente cuando hay máscaras subidas

### Código actualizado:
```python
# ANTES:
match = re.search(r'(\d+)', batch_id)  # Solo capturaba números
if match:
    batch_numbers[batch_id] = match.group(1)  # Resultado: "20250909"

# AHORA:
match = re.search(r'batch_(.+)', batch_id, re.IGNORECASE)
if match:
    batch_numbers[batch_id] = match.group(1)  # Resultado: "20250909T0034"
```

### Archivos modificados:
- `app.py` (líneas 774-833)

---

## 7. Dashboard General Mostrando Batches Sin Asignar

### Problema:
- El dashboard general (`/dashboard`) mostraba TODOS los batches, incluyendo los que no tienen responsable asignado
- Esto causaba confusión porque aparecían batches pendientes de asignación

### Solución:
- Agregado filtro adicional en la función `updateTable()` para mostrar solo batches que:
  - Tienen estado `In` (Incompleta) o `NS` (No Segmentado)
  - **Y tienen un responsable asignado** (`assignee` no vacío)

### Código actualizado:
```javascript
// ANTES:
const batchesForReview = batches.filter(batch =>
  batch.status === 'In' || batch.status === 'NS'
);

// AHORA:
const batchesForReview = batches.filter(batch =>
  (batch.status === 'In' || batch.status === 'NS') &&
  batch.assignee && batch.assignee.trim() !== ''
);
```

### Archivos modificados:
- `templates/dashboard.html` (líneas 942-948)

---

## Resumen de Mejoras

### Infraestructura:
1. ✅ Túnel SSH configurado para acceder a MongoDB remoto
2. ✅ Scripts automatizados para gestión de túneles (básico + autossh)
3. ✅ Dos conexiones MongoDB: local (27017) y remota (27018 vía túnel)

### Backend (`app.py` y `db.py`):
1. ✅ Conexión correcta a QUALITY_IEMSA para máscaras (vía túnel SSH)
2. ✅ Conexión correcta a Quality_dashboard para segmentadores
3. ✅ API paginada funcionando correctamente
4. ✅ Sincronización de máscaras con identificadores completos

### Frontend:
1. ✅ Interfaz completa para gestión de segmentadores (agregar, editar, eliminar)
2. ✅ Sincronización entre todos los dashboards
3. ✅ Vista de equipo con estadísticas actualizadas
4. ✅ Dashboard general filtra solo batches asignados

### Scripts de Utilidad:
1. ✅ `setup_mongo_tunnel.sh` - Túnel SSH básico
2. ✅ `setup_mongo_tunnel_autossh.sh` - Túnel persistente con reconexión

---

## 8. Actualización de Conexión MongoDB y Sincronización Automática de Máscaras

**Fecha:** 2025-10-14

### Problema:
1. La conexión a QUALITY_IEMSA usaba túnel SSH (`127.0.0.1:27019`) cuando la base de datos estaba en el mismo servidor MongoDB
2. Las máscaras recién subidas no se sincronizaban automáticamente con el dashboard
3. El usuario tenía que ejecutar manualmente scripts de sincronización después de subir máscaras
4. El dashboard mostraba batches antiguos que ya no existían

### Solución Implementada:

#### 1. **Actualización de Conexiones MongoDB**
- Ambas conexiones ahora apuntan directamente a `mongodb://192.168.1.93:27017`
- Eliminada necesidad de túnel SSH
- Conexión más rápida y confiable

**Archivos modificados:**
- `db.py` (líneas 5, 9-15)
- `.env.example` (líneas 6, 9-14)

**Antes:**
```python
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017")
TRAINING_MONGO_URI = os.environ.get(
    "TRAINING_MONGO_URI",
    "mongodb://127.0.0.1:27019/QUALITY_IEMSA?directConnection=true"
)
```

**Ahora:**
```python
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://192.168.1.93:27017")
TRAINING_MONGO_URI = os.environ.get(
    "TRAINING_MONGO_URI",
    "mongodb://192.168.1.93:27017/QUALITY_IEMSA"
)
```

#### 2. **Reemplazo Completo de Batches**
- Eliminados 156 batches antiguos
- Creados 429 batches nuevos:
  - 284 batches tipo F (`batch_000001F` - `batch_000284F`)
  - 145 batches tipo T (`batch_T000002` - `batch_T000168`)

**Script creado:** `replace_batches.py`

#### 3. **Script de Sincronización de Máscaras**
- Nuevo script para sincronizar máscaras con batches
- Soporta formatos: `masks_batch_XXXXXF.tar.xz` y `masks_batch_TXXXXXX.tar.xz`
- Actualiza campo `mongo_uploaded` y `file_info` en cada batch

**Script creado:** `sync_masks_with_batches.py`

**Funcionamiento:**
```python
# Extrae IDs de batch de nombres de archivo
# masks_batch_000040F.tar.xz → batch_000040F
# masks_batch_T000044.tar.xz → batch_T000044

# Actualiza batch en DB
batches_col.update_one(
    {"id": batch_id},
    {"$set": {
        "mongo_uploaded": True,
        "file_info": {
            "file_count": len(masks),
            "last_file_upload": latest_upload_date,
            "has_files": True
        }
    }}
)
```

#### 4. **Sincronización Automática en Dashboard**
- Dashboard ahora sincroniza automáticamente al cargar
- No requiere acción manual del usuario
- Fallback en caso de error (carga batches de todas formas)

**Archivo modificado:** `templates/dashboard.html` (líneas 635-647, 834-861)

**Función agregada:**
```javascript
function syncMasksWithBatches() {
  return new Promise((resolve, reject) => {
    $.ajax({
      url: '/api/sync-batch-files',
      method: 'POST',
      timeout: 30000,
      success: function(response) {
        console.log(`✅ Sincronización exitosa: ${response.batches_updated} batches actualizados`);
        resolve(response);
      },
      error: function(xhr, status, error) {
        console.error('❌ Error en sincronización:', error);
        reject(error);
      }
    });
  });
}
```

**Integración en carga:**
```javascript
$(document).ready(function() {
  initBatches();

  // Sincronizar máscaras antes de cargar batches
  syncMasksWithBatches().then(() => {
    loadBatches();
  }).catch(err => {
    console.error('⚠️ Error sincronizando, cargando de todas formas');
    loadBatches();
  });
});
```

### Resultados:
- ✅ 58 batches con máscaras sincronizados
- ✅ 371 batches sin máscaras
- ✅ 125 archivos de máscaras detectados en QUALITY_IEMSA
- ✅ Sincronización automática al recargar dashboard
- ✅ No requiere túnel SSH

### Verificación:
```bash
# Verificar conexión
python3 -c "from db import ping_training_client; print(ping_training_client())"

# Sincronizar manualmente (si es necesario)
python3 sync_masks_with_batches.py

# Verificar batches con máscaras
python3 -c "from db import get_db; db = get_db(); print(db.batches.count_documents({'mongo_uploaded': True}))"
```

### Documentación creada:
- `SOLUCION_SINCRONIZACION_MONGO.md` - Documentación completa de la solución

---

### Pendiente:
- 🔄 Arreglar menú hamburguesa (no mostrar página actual)

---

## Notas Técnicas

### Estructura de Bases de Datos:
```
MongoDB (127.0.0.1:27018)
├── segmentacion_db           # Batches principales
│   ├── batches
│   └── masks.files
├── Quality_dashboard         # Segmentadores persistentes
│   └── segmentadores
└── QUALITY_IEMSA            # Máscaras subidas en GridFS
    └── training_metrics.masks.files
```

### Estados de Batches:
- **NS** - No Segmentado (pendiente)
- **In** - Incompletas (en progreso)
- **S** - Segmentado (completado - se quita de la cola)

### Endpoints Principales:
- `GET /api/batches?per_page=N` - Obtener batches paginados
- `POST /api/add-segmentador` - Agregar segmentador
- `PUT /api/update-segmentador` - Actualizar segmentador
- `DELETE /api/remove-segmentador` - Eliminar segmentador
- `POST /api/sync-batch-files` - Sincronizar máscaras con batches
