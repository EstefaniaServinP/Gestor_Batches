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

## 5. Problema de Sincronización de Máscaras (masks_batch vs batch)

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

## 6. Dashboard General Mostrando Batches Sin Asignar

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

### Backend (`app.py` y `db.py`):
1. ✅ Conexión correcta a QUALITY_IEMSA para máscaras
2. ✅ Conexión correcta a Quality_dashboard para segmentadores
3. ✅ API paginada funcionando correctamente
4. ✅ Sincronización de máscaras con identificadores completos

### Frontend:
1. ✅ Interfaz completa para gestión de segmentadores (agregar, editar, eliminar)
2. ✅ Sincronización entre todos los dashboards
3. ✅ Vista de equipo con estadísticas actualizadas
4. ✅ Dashboard general filtra solo batches asignados

### Todas las tareas completadas ✅

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
