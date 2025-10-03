# 📊 Arquitectura del Sistema - Dashboard de Segmentación

> **Proyecto:** Dashboard de Segmentación de Imágenes Médicas
> **Versión:** 1.0.0
> **Fecha:** Julio 2025
> **Equipo:** Mauricio, Maggie, Ceci, Flor, Ignacio

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Cliente)                      │
├─────────────────────────────────────────────────────────────┤
│  Templates (Jinja2)  │  JavaScript  │  CSS (Bootstrap 5)    │
│  ─────────────────── │ ──────────── │ ───────────────────   │
│  • team.html         │ • menu.js    │ • menu.css            │
│  • dashboard.html    │ • team.js    │ • common.css          │
│  • metrics.html      │ • dashboard.js                       │
│  • masks.html        │ • batch_management.js                │
│  • batch_mgmt.html   │ • masks.js                           │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (Flask Server)                    │
├─────────────────────────────────────────────────────────────┤
│  app.py (Rutas y API REST)                                  │
│  ─────────────────────────────────────────────────────────  │
│  • Rutas de vistas (render_template)                        │
│  • Endpoints API (/api/*)                                   │
│  • Lógica de negocio                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓ PyMongo
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE DATOS (db.py)                      │
├─────────────────────────────────────────────────────────────┤
│  • Conexión MongoDB                                         │
│  • Gestión de cliente                                       │
│  • Creación de índices                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓ MongoDB Protocol
┌─────────────────────────────────────────────────────────────┐
│                   BASE DE DATOS (MongoDB)                    │
├─────────────────────────────────────────────────────────────┤
│  Database: segmentacion_db                                  │
│  ─────────────────────────                                  │
│  • Colección: batches (documentos de batches)               │
│  • Colección: masks.files (GridFS para máscaras)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 BACKEND - Componentes Principales

### 1. **db.py** - Capa de Acceso a Datos

#### Funciones:
- **`get_client()`**: Singleton de conexión MongoDB
- **`ping_client(timeout_ms=2000)`**: Verificar conectividad
- **`get_db(raise_on_fail=True)`**: Obtener instancia de BD
- **`create_indexes()`**: Crear índices optimizados
- **`close_client()`**: Cerrar conexión

#### Configuración:
```python
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB", "segmentacion_db")
```

#### Índices Creados:
- `batches.id` (único, ascendente)
- `batches.assignee` (ascendente)
- `masks.files.filename` (ascendente)

---

### 2. **app.py** - Servidor Flask & API REST

#### Variables Globales:
```python
CREW_MEMBERS = ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"]
db = None
batches_col = None
masks_col = None
```

#### Inicialización:
```python
def init_db():
    # Conexión diferida a MongoDB
    # Creación de índices en background
```

---

## 🌐 RUTAS DEL SISTEMA

### **Rutas de Vistas** (Templates HTML)

| Ruta | Template | Descripción |
|------|----------|-------------|
| `/` | `team.html` | Página principal - Vista de equipo |
| `/team` | `team.html` | Vista de tarjetas de equipo |
| `/dashboard` | `dashboard.html` | Dashboard con tabla editable |
| `/dashboard/<assignee>` | `dashboard.html` | Dashboard filtrado por responsable |
| `/assign` | `batch_management.html` | Asignación de batches |
| `/batch-management` | → Redirect a `/assign` | Compatibilidad |
| `/masks` | `masks.html` | Visualización de máscaras MongoDB |
| `/metrics` | `metrics.html` | Métricas principales |
| `/metrics/overview` | `metrics_overview.html` | Vista general de métricas |
| `/metrics/team` | `metrics_team.html` | Métricas por equipo |
| `/metrics/progress` | `metrics_progress.html` | Reportes de progreso |

---

### **API REST Endpoints**

#### **CRUD de Batches**

##### `GET /api/batches`
**Descripción:** Obtener batches paginados
**Parámetros:**
- `page` (int, default=1): Número de página
- `per_page` (int, default=50, max=200): Batches por página

**Respuesta:**
```json
{
  "batches": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 500,
    "total_pages": 10
  }
}
```

##### `POST /api/batches`
**Descripción:** Crear nuevo batch
**Body:**
```json
{
  "id": "batch_123",
  "assignee": "Mauricio",
  "folder": "/data/batch_123",
  "status": "NS",
  "metadata": {
    "assigned_at": "2025-07-23",
    "due_date": "2025-07-30",
    "priority": "media"
  },
  "comments": "Batch inicial"
}
```

##### `PUT /api/batches/<batch_id>`
**Descripción:** Actualizar batch existente
**Body:** (campos opcionales)
```json
{
  "assignee": "Maggie",
  "status": "S",
  "metadata": {
    "due_date": "2025-08-01"
  }
}
```

##### `DELETE /api/batches/<batch_id>`
**Descripción:** Eliminar batch
**Respuesta:**
```json
{
  "success": true,
  "message": "Batch batch_123 eliminado",
  "deleted_batch": {...}
}
```

##### `PUT /api/batches/<batch_id>/change-id`
**Descripción:** Cambiar ID de un batch
**Body:**
```json
{
  "new_id": "batch_456"
}
```

---

#### **Gestión de Segmentadores**

##### `POST /api/add-segmentador`
**Descripción:** Agregar nuevo segmentador
**Body:**
```json
{
  "name": "Nuevo Segmentador",
  "role": "Segmentador General",
  "email": "email@ejemplo.com"
}
```

##### `GET /api/segmentadores`
**Descripción:** Obtener lista de segmentadores
**Respuesta:**
```json
{
  "success": true,
  "segmentadores": ["Mauricio", "Maggie", ...],
  "total": 5
}
```

---

#### **Operaciones MongoDB**

##### `GET /api/check-mongo-files`
**Descripción:** Verificar archivos en GridFS
**Respuesta:**
```json
{
  "success": true,
  "total_files": 150,
  "recent_files": [...],
  "batch_patterns": {
    "batch_400": ["masks_batch_400.tar.xz", ...]
  }
}
```

##### `GET /api/batch-files/<batch_id>`
**Descripción:** Obtener archivos de un batch
**Respuesta:**
```json
{
  "batch_id": "batch_400",
  "total_files": 3,
  "latest_upload": "2025-07-23T10:30:00",
  "uploaded_by": "Mauricio",
  "file_size": 1048576,
  "all_uploads": [...]
}
```

##### `POST /api/sync-batch-files`
**Descripción:** Sincronizar estado `mongo_uploaded` con archivos reales
**Lógica:**
```python
# Busca archivos con patrones:
patterns = [
    f"masks_batch_{batch_number}",
    f"batch_{batch_number}",
    f"Batch_{batch_number}",
    ...
]
# Actualiza mongo_uploaded: true/false
```

##### `POST /api/auto-create-batches`
**Descripción:** Crear batches automáticamente desde archivos en MongoDB
**Lógica:**
```python
# 1. Extrae números de batch de nombres de archivo
# 2. Crea batches faltantes
# 3. Asigna por defecto a "Maggie"
```

##### `POST /api/init-batches`
**Descripción:** Inicializar batches desde `batches.json`
**Body:**
```json
{
  "force": false  // true = limpiar y recargar
}
```

##### `POST /api/reset-batches`
**Descripción:** Limpiar y recargar todos los batches desde JSON

##### `GET /api/missing-batches`
**Descripción:** Obtener lista de batches pendientes (no en DB)
**Respuesta:**
```json
{
  "success": true,
  "missing_batches": ["batch_9", "batch_10", ...],
  "total_missing": 50,
  "total_existing": 450
}
```

---

## 🎨 FRONTEND - Estructura

### **1. Templates HTML (Jinja2)**

#### Estructura Común:
```html
<!DOCTYPE html>
<html>
<head>
  <!-- Bootstrap 5 -->
  <!-- Font Awesome 6 -->
  <!-- DataTables (opcional) -->
  <link href="/static/css/menu.css">
  <style>/* Estilos inline */</style>
</head>
<body>
  <!-- Menú se inyecta via menu.js -->

  <div class="main-content">
    <!-- Contenido específico de la página -->
  </div>

  <script src="/static/js/menu.js"></script>
  <script src="/static/js/[page-specific].js"></script>
</body>
</html>
```

---

### **2. JavaScript Modular**

#### **menu.js** - Menú Global
**Responsabilidades:**
- Generar HTML del menú lateral
- Toggle del menú (hamburguesa)
- Submenú colapsable de Métricas
- Estado en localStorage
- Accesibilidad (ARIA, teclado)

**Funciones principales:**
```javascript
function generateMenuHTML()
function toggleMenu()
function openMenu() / closeMenu()
function toggleMetricsSubmenu(event)
function handleMetricsTriggerKeydown(event)
```

---

#### **dashboard.js** - Dashboard Principal
**Responsabilidades:**
- Cargar batches paginados
- Inicializar DataTable
- Edición inline (assignee, status, folder, due_date, comments)
- Filtrado por responsable
- Métricas en tiempo real

**Funciones principales:**
```javascript
async function loadBatches(page, perPage)
function initializeDataTable()
function enableInlineEdit(element, field, batchId, value)
async function saveInlineEdit(...)
function filterByAssignee()
function calculateMetrics(batches)
```

---

#### **batch_management.js** - Asignación de Batches
**Responsabilidades:**
- Verificar conexión MongoDB
- Sincronizar archivos
- Crear batches automáticamente
- Inicializar/resetear datos

**Funciones principales:**
```javascript
async function checkMongoFiles()
async function syncBatchFiles()
async function autoCreateBatches()
async function initializeBatches()
```

---

#### **team.js** - Vista de Equipo
**Responsabilidades:**
- Cargar batches por responsable
- Renderizar tarjetas de miembros
- Gestionar modal de agregar segmentador
- Estadísticas por persona

---

#### **masks.js** - Visualización de Máscaras
**Responsabilidades:**
- Listar archivos en GridFS
- Filtrado por nombre/fecha
- DataTable responsive

---

### **3. CSS Modular**

#### **menu.css** - Estilos del Menú
**Componentes:**
- `.menu-toggle`: Botón hamburguesa
- `.side-menu`: Menú lateral
- `.menu-item`: Items de nivel 1
- `.menu-item-trigger`: Trigger del submenú
- `.submenu-container`: Contenedor colapsable
- `.submenu-item`: Items del submenú
- `.menu-overlay`: Overlay de cierre

**Features:**
- Glassmorphism (backdrop-filter: blur)
- Transiciones suaves
- ARIA/accesibilidad
- Responsive

---

## 📊 MODELO DE DATOS (MongoDB)

### **Colección: batches**

```javascript
{
  "_id": ObjectId("..."),
  "id": "batch_400",              // ID único del batch
  "assignee": "Mauricio",          // Responsable
  "folder": "/data/batch_400",     // Ruta del batch
  "tasks": [                       // Tareas pendientes
    "segmentar",
    "subir_mascaras",
    "revisar"
  ],
  "metadata": {
    "assigned_at": "2025-07-23",   // Fecha de asignación
    "due_date": "2025-07-30",      // Fecha límite
    "priority": "media",           // Prioridad: baja/media/alta
    "reviewed_at": null            // Fecha de revisión
  },
  "status": "NS",                  // NS/FS/S (No/Parcial/Segmentado)
  "mongo_uploaded": true,          // Si tiene archivos en MongoDB
  "comments": "Comentarios...",    // Observaciones
  "file_info": {                   // Metadatos de archivos (opcional)
    "file_count": 3,
    "last_file_upload": "2025-07-23T10:30:00Z",
    "has_files": true,
    "files": ["masks_batch_400.tar.xz"]
  }
}
```

#### **Estados Posibles:**
- `NS` (No Segmentado): Pendiente
- `FS` (Fragmento Segmentado): Parcial
- `S` (Segmentado): Completado
- `In` (En progreso): Legacy (algunos archivos)

---

### **Colección: masks.files** (GridFS)

```javascript
{
  "_id": ObjectId("..."),
  "filename": "masks_batch_400.tar.xz",
  "uploadDate": ISODate("2025-07-23T10:30:00Z"),
  "length": 1048576,               // Tamaño en bytes
  "chunkSize": 261120,
  "metadata": {
    "uploaded_by": "Mauricio",
    "content_type": "application/x-xz"
  }
}
```

---

## 🔄 FLUJO DE TRABAJO TÍPICO

### **Caso 1: Asignar Batch a Segmentador**

```mermaid
sequenceDiagram
    Usuario->>Frontend: Selecciona batch en dashboard
    Frontend->>Usuario: Habilita edición inline
    Usuario->>Frontend: Cambia assignee a "Maggie"
    Frontend->>API: PUT /api/batches/batch_400
    API->>MongoDB: update_one({id: "batch_400"}, {assignee: "Maggie"})
    MongoDB-->>API: {modified_count: 1}
    API-->>Frontend: {success: true}
    Frontend-->>Usuario: Muestra notificación éxito
```

---

### **Caso 2: Sincronizar Archivos MongoDB**

```mermaid
sequenceDiagram
    Usuario->>Frontend: Click "Sincronizar Archivos"
    Frontend->>API: POST /api/sync-batch-files
    API->>MongoDB: find({}) en batches
    API->>MongoDB: find({filename: {$regex: ...}}) en masks.files
    loop Para cada batch
        API->>API: Buscar archivos con patrones
        API->>MongoDB: update_one({id: batch_id}, {mongo_uploaded: true/false})
    end
    API-->>Frontend: {batches_updated: 50}
    Frontend-->>Usuario: Muestra resultados
```

---

### **Caso 3: Visualizar Métricas**

```mermaid
sequenceDiagram
    Usuario->>Frontend: Abre /metrics
    Frontend->>API: GET /api/batches
    API->>MongoDB: find({}).skip(0).limit(50)
    MongoDB-->>API: [batch_1, batch_2, ...]
    API-->>Frontend: {batches: [...], pagination: {...}}
    Frontend->>Frontend: calculateMetrics(batches)
    Frontend->>Usuario: Renderiza gráficos/tablas
```

---

## 🎯 CARACTERÍSTICAS PRINCIPALES

### **1. Paginación**
- Implementada en `/api/batches`
- Límite: 5-200 batches/página
- Optimiza rendimiento con grandes datasets

### **2. Edición Inline**
- Click en campo → input editable
- Save: blur o Enter
- Cancel: Escape
- Actualización inmediata en DB

### **3. Filtrado Dinámico**
- Por responsable (dropdown)
- DataTable search global
- Métricas se actualizan en tiempo real

### **4. Sincronización MongoDB**
- Detecta archivos por patrones regex
- Actualiza campo `mongo_uploaded`
- Soporta múltiples formatos (.tar.xz, .tar.gz, .zip)

### **5. Gestión de Equipo**
- Agregar segmentadores dinámicamente
- Lista en memoria (CREW_MEMBERS)
- Disponible en todos los selectores

### **6. Accesibilidad**
- ARIA labels en menú
- Soporte teclado (Tab, Enter, Escape)
- Focus visible
- Semantic HTML

---

## 🔐 SEGURIDAD Y BUENAS PRÁCTICAS

### **Implementadas:**
✅ Validación de entrada en endpoints
✅ Manejo de errores con try/except
✅ Logging de operaciones críticas
✅ Índices únicos en MongoDB
✅ Conexión MongoDB con timeout
✅ CORS implícito (mismo origen)

### **Pendientes (Recomendadas):**
⚠️ Autenticación/Autorización
⚠️ Rate limiting en API
⚠️ Sanitización de inputs HTML
⚠️ HTTPS en producción
⚠️ Backup automático MongoDB
⚠️ Variables de entorno para secretos

---

## 🚀 DESPLIEGUE

### **Desarrollo:**
```bash
python app.py
# Servidor en http://localhost:5000
```

### **Producción (Recomendado):**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### **Variables de Entorno:**
```bash
export MONGO_URI="mongodb://usuario:contraseña@host:27017"
export MONGO_DB="segmentacion_db"
```

---

## 📈 MÉTRICAS Y MONITOREO

### **Endpoints de Monitoreo:**
- `/api/batches` → Total de batches
- `/api/check-mongo-files` → Archivos en GridFS
- `/api/segmentadores` → Tamaño del equipo

### **Logs:**
```python
print("✅ Batch batch_400 actualizado")
print("❌ Error en get_batches:", e)
print("🔄 Sincronización completa: 50 batches actualizados")
```

---

## 🎓 TECNOLOGÍAS UTILIZADAS

### **Backend:**
- **Flask** 2.x - Framework web
- **PyMongo** 4.x - Driver MongoDB
- **Python** 3.10+

### **Frontend:**
- **Bootstrap** 5.3 - UI framework
- **jQuery** 3.7 - Manipulación DOM
- **DataTables** 1.13 - Tablas interactivas
- **Font Awesome** 6.4 - Iconografía

### **Base de Datos:**
- **MongoDB** 6.x+ - NoSQL database
- **GridFS** - Almacenamiento de archivos

---

## 📝 CONVENCIONES DE CÓDIGO

### **Python:**
- **PEP 8** - Estilo de código
- **snake_case** para funciones/variables
- **UPPER_CASE** para constantes
- Docstrings en endpoints

### **JavaScript:**
- **camelCase** para funciones/variables
- **async/await** para operaciones asíncronas
- **const/let** (no var)
- Comentarios descriptivos

### **MongoDB:**
- **snake_case** para campos
- **id** sin guion bajo (no _id para documentos propios)
- Metadatos en objetos anidados

---

## 🔄 VERSIONAMIENTO

**Sistema:** Git
**Branches:**
- `main` - Producción
- `develop` - Desarrollo
- `feature/*` - Features

**Commits:**
- ✨ Feature nueva
- 🐛 Bug fix
- 📝 Documentación
- ♻️ Refactoring
- 🎨 Estilos/UI

---

## 📚 RECURSOS ADICIONALES

- **Flask Docs:** https://flask.palletsprojects.com/
- **PyMongo Docs:** https://pymongo.readthedocs.io/
- **Bootstrap 5:** https://getbootstrap.com/docs/5.3/
- **DataTables:** https://datatables.net/
- **MongoDB Docs:** https://www.mongodb.com/docs/

---

**Última actualización:** Julio 2025
**Mantenido por:** Equipo de Segmentación
