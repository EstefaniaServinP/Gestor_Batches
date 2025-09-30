# 📋 Documentación Completa del Sistema de Gestión de Segmentación

> **Versión:** 1.0.0
> **Fecha:** Septiembre 30, 2025
> **Estado:** En desarrollo activo
> **Equipo:** Mauricio, Maggie, Ceci, Flor, Ignacio

---

## 📑 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Componentes Principales](#componentes-principales)
5. [Flujo de Datos](#flujo-de-datos)
6. [API REST](#api-rest)
7. [Interfaces de Usuario](#interfaces-de-usuario)
8. [Problemáticas y Soluciones](#problemáticas-y-soluciones)
9. [Roadmap de Desarrollo](#roadmap-de-desarrollo)
10. [Guía de Instalación](#guía-de-instalación)
11. [Guía de Uso](#guía-de-uso)

---

## 🎯 Introducción

### Descripción General
Sistema web integral para la gestión, asignación y seguimiento de batches de segmentación de imágenes médicas. Diseñado para facilitar la colaboración entre múltiples segmentadores, proporcionar visibilidad en tiempo real del progreso y mantener un historial completo de todas las operaciones.

### Objetivos del Sistema
- ✅ **Gestión centralizada** de batches de segmentación
- ✅ **Asignación visual** mediante drag & drop
- ✅ **Seguimiento en tiempo real** del progreso de cada miembro
- ✅ **Integración con MongoDB** para almacenamiento de máscaras
- ✅ **Interfaz intuitiva** y responsive
- ✅ **API RESTful** completa para integración con otros sistemas

### Contexto del Proyecto
El sistema gestiona la segmentación de imágenes médicas (tomografías, resonancias, ultrasonidos, rayos X) donde cada "batch" representa una carpeta con múltiples imágenes que deben ser procesadas manualmente por especialistas.

---

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico

#### Backend
- **Framework:** Flask 2.3.3
- **Base de Datos:** MongoDB 4.5.0
- **Lenguaje:** Python 3.10+

#### Frontend
- **Framework CSS:** Bootstrap 5.3.0
- **Librería JS:** jQuery 3.7.0
- **Tablas:** DataTables 1.13.4
- **Iconos:** Font Awesome 6.4.0

#### Infraestructura
- **Servidor:** Ubuntu/Linux
- **MongoDB:** Instancia dedicada con autenticación
- **Puerto:** 5000 (configurable)

### Arquitectura de 3 Capas

```
┌─────────────────────────────────────────┐
│         CAPA DE PRESENTACIÓN            │
│  ┌───────────┐ ┌───────────┐ ┌────────┐│
│  │   Team    │ │ Dashboard │ │ Masks  ││
│  │   View    │ │   View    │ │  View  ││
│  └───────────┘ └───────────┘ └────────┘│
│           Bootstrap 5 + jQuery           │
└─────────────────────────────────────────┘
                    ↕ HTTP/JSON
┌─────────────────────────────────────────┐
│        CAPA DE LÓGICA DE NEGOCIO        │
│          Flask Application (app.py)      │
│  ┌───────────────────────────────────┐  │
│  │  API REST Endpoints               │  │
│  │  - GET/POST/PUT/DELETE batches    │  │
│  │  - Sincronización MongoDB         │  │
│  │  - Gestión de segmentadores       │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    ↕ PyMongo
┌─────────────────────────────────────────┐
│         CAPA DE PERSISTENCIA            │
│            MongoDB Database              │
│  ┌────────────┐      ┌────────────┐    │
│  │  batches   │      │   masks    │    │
│  │ collection │      │ collection │    │
│  └────────────┘      └────────────┘    │
└─────────────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

### Árbol de Directorios

```
segmentacion-dashboard/
│
├── 📄 app.py                          # Aplicación Flask principal (830 líneas)
├── 📄 db.py                           # Gestor de conexión MongoDB (37 líneas)
├── 📄 requirements.txt                # Dependencias Python
├── 📄 README.md                       # Documentación básica
├── 📄 DOCUMENTACION_COMPLETA.md       # Este archivo
│
├── 📁 templates/                      # Plantillas HTML Jinja2
│   ├── team.html                      # Vista principal del equipo (899 líneas)
│   ├── dashboard.html                 # Dashboard de gestión (3335 líneas)
│   ├── batch_management.html          # Asignación drag & drop (1438 líneas)
│   ├── masks.html                     # Visualización de máscaras (724 líneas)
│   ├── metrics.html                   # Métricas generales
│   ├── metrics_overview.html          # Vista general de métricas
│   ├── metrics_team.html              # Métricas por equipo
│   ├── metrics_progress.html          # Reportes de progreso
│   │
│   └── 📁 backups/                    # Versiones anteriores
│       ├── *_backup_original.html
│       ├── *_refactored.html
│       └── *_old.html
│
├── 📁 static/                         # Archivos estáticos (generado)
│   ├── css/
│   ├── js/
│   └── images/
│
├── 📁 data/                           # Datos de batches (JSON)
│   ├── batches,json                   # Configuración activa (typo intencional)
│   ├── batches_backup.json
│   ├── batches_clean.json
│   ├── batches_real.json
│   └── batches_updated.json
│
├── 📁 scripts/                        # Scripts utilitarios
│   ├── check_batches.py               # Verificación de batches
│   ├── test_api.py                    # Pruebas de API
│   ├── test_mongo.py                  # Pruebas de MongoDB
│   ├── fix_maggie_batches.py          # Corrección de batches de Maggie
│   └── gantt_generator.py             # Generador de gráficas Gantt
│
└── 📁 venv/                           # Entorno virtual Python (gitignored)
```

### Archivos Clave

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `app.py` | 830 | Servidor Flask, endpoints API, lógica de negocio |
| `db.py` | 37 | Conexión singleton a MongoDB |
| `dashboard.html` | 3335 | Interfaz principal de gestión con edición inline |
| `batch_management.html` | 1438 | Sistema drag & drop para asignación de batches |
| `team.html` | 899 | Vista de equipo con tarjetas interactivas |
| `masks.html` | 724 | Visualización de archivos en MongoDB |

**Total de líneas de código:** ~7,263 líneas (sin contar librerías)

---

## 🧩 Componentes Principales

### 1. Backend (app.py)

#### Configuración Global
```python
from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from db import get_db

app = Flask(__name__)
db = get_db()
batches_col = db["batches"]
masks_col = db["masks"]

CREW_MEMBERS = ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"]
```

#### Rutas Principales

**Vistas HTML:**
- `/` → Página de equipo
- `/team` → Vista del equipo
- `/dashboard` → Dashboard general
- `/dashboard/<assignee>` → Dashboard filtrado por responsable
- `/assign` → Gestión de asignación drag & drop
- `/masks` → Visualización de máscaras MongoDB
- `/metrics/*` → Diferentes vistas de métricas

**API Endpoints:**
- `GET /api/batches` → Obtener todos los batches
- `POST /api/batches` → Crear nuevo batch
- `PUT /api/batches/<id>` → Actualizar batch existente
- `DELETE /api/batches/<id>` → Eliminar batch
- `PUT /api/batches/<id>/change-id` → Cambiar ID de batch
- `GET /api/missing-batches` → Obtener batches pendientes
- `GET /api/check-mongo-files` → Verificar archivos en MongoDB
- `POST /api/sync-batch-files` → Sincronizar archivos con batches
- `POST /api/auto-create-batches` → Crear batches automáticamente
- `POST /api/add-segmentador` → Agregar nuevo segmentador
- `GET /api/segmentadores` → Listar segmentadores

### 2. Base de Datos (db.py)

#### Gestión de Conexión MongoDB
```python
import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://...")
DB_NAME = os.environ.get("MONGO_DB", "segmentacion_db")

_client = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client

def ping_client():
    try:
        get_client().admin.command("ping")
        return True, None
    except Exception as e:
        return False, e

def get_db(raise_on_fail=True):
    ok, err = ping_client()
    if ok:
        return get_client()[DB_NAME]
    # Manejo de errores...
```

**Características:**
- ✅ Cliente singleton (una sola conexión reutilizable)
- ✅ Ping de salud antes de retornar DB
- ✅ Manejo de errores configurable
- ✅ Timeout de 5 segundos

### 3. Modelo de Datos

#### Estructura de Batch en MongoDB

```json
{
  "id": "batch_400",
  "assignee": "Mauricio",
  "folder": "/data/batch_400",
  "tasks": ["segmentar", "subir_mascaras", "revisar"],
  "metadata": {
    "assigned_at": "2025-09-28",
    "due_date": "2025-10-05",
    "priority": "alta",
    "reviewed_at": null,
    "review_status": "aprobado"
  },
  "status": "In",
  "mongo_uploaded": true,
  "comments": "Batch con prioridad alta",
  "file_info": {
    "file_count": 1,
    "last_file_upload": "2025-09-27T14:30:00Z",
    "has_files": true,
    "files": ["masks_batch_400.tar.xz"]
  }
}
```

#### Estados de Batch (status)

| Estado | Código | Descripción | Icono |
|--------|--------|-------------|-------|
| No Segmentado | `NS` | Batch asignado pero sin iniciar | 🔴 |
| Incompleta | `In` | En proceso de segmentación | 🟡 |
| Segmentado | `S` | Completado y aprobado | 🟢 |

#### Estados de Revisión (review_status)

| Estado | Valor | Descripción | Emoji |
|--------|-------|-------------|-------|
| Pendiente | `null` o `""` | Sin revisar | ⏳ |
| Aprobado | `"aprobado"` | Revisión exitosa | ✅ |
| No Aprobado | `"no_aprobado"` | Requiere correcciones | ❌ |

---

## 🔄 Flujo de Datos

### 1. Ciclo de Vida de un Batch

```mermaid
graph TD
    A[Batch Detectado] --> B{Existe en DB?}
    B -->|No| C[Crear en missing_batches]
    B -->|Sí| D[Cargar datos existentes]
    C --> E[Aparece en 'No Asignados']
    D --> E
    E --> F[Usuario arrastra a segmentador]
    F --> G[POST/PUT /api/batches]
    G --> H[Batch asignado: status=NS]
    H --> I[Segmentador trabaja]
    I --> J{Subió a Mongo?}
    J -->|Sí| K[mongo_uploaded=true]
    J -->|No| L[mongo_uploaded=false]
    K --> M[Revisor verifica]
    L --> M
    M --> N{Aprobado?}
    N -->|Sí| O[status=S, review_status=aprobado]
    N -->|No| P[review_status=no_aprobado]
    P --> I
    O --> Q[Batch completado]
```

### 2. Flujo de Asignación (Drag & Drop)

**Escenario 1: Asignar batch pendiente a segmentador**
```
1. Frontend: Usuario arrastra batch_400 de "No Asignados" → Zona de Mauricio
2. JavaScript: assignBatchToSegmentador('batch_400', 'Mauricio')
3. JavaScript: Detecta que batch_400 NO existe en DB → createBatchFromPending()
4. Frontend → Backend: POST /api/batches
   Body: {
     id: "batch_400",
     assignee: "Mauricio",
     status: "NS",
     ...
   }
5. Backend: Inserta documento en MongoDB
6. Backend → Frontend: {success: true, batch: {...}}
7. Frontend: loadBatches() → Refresca toda la interfaz
8. Resultado: batch_400 aparece en zona de Mauricio
```

**Escenario 2: Reasignar batch existente**
```
1. Frontend: Usuario arrastra batch_400 de Mauricio → Zona de Maggie
2. JavaScript: assignBatchToSegmentador('batch_400', 'Maggie')
3. JavaScript: Detecta que batch_400 SÍ existe en DB → updateExistingBatch()
4. Frontend → Backend: PUT /api/batches/batch_400
   Body: {
     assignee: "Maggie",
     metadata: {...}
   }
5. Backend: Update documento en MongoDB
6. Backend → Frontend: {success: true}
7. Frontend: loadBatches() → Refresca toda la interfaz
8. Resultado: batch_400 aparece en zona de Maggie
```

**Escenario 3: Desasignar batch (regresar a "No Asignados")**
```
1. Frontend: Usuario arrastra batch_400 de Mauricio → "No Asignados"
2. JavaScript: assignBatchToSegmentador('batch_400', undefined)
3. JavaScript: updateExistingBatch('batch_400', null)
4. Frontend → Backend: PUT /api/batches/batch_400
   Body: {
     assignee: null,
     metadata: {...}
   }
5. Backend: Update documento: assignee = null
6. Backend → Frontend: {success: true}
7. Frontend: loadBatches() → Refresca toda la interfaz
8. Resultado: batch_400 reaparece en "No Asignados"
```

### 3. Sincronización con MongoDB

```python
# Flujo de sincronización automática
GET /api/sync-batch-files

1. Obtener todos los batches de la DB
2. Para cada batch:
   - Extraer número: "batch_400" → "400"
   - Buscar archivos con patrones:
     * masks_batch_400*
     * Batch_400*
     * batch_400 (*).tar.xz
   - Contar archivos encontrados
3. Actualizar campo mongo_uploaded:
   - true si hay archivos
   - false si no hay archivos
4. Actualizar file_info con metadatos
5. Retornar resumen de sincronización
```

---

## 🌐 API REST

### Endpoints Completos

#### 1. Gestión de Batches

**GET `/api/batches`**
```http
GET /api/batches HTTP/1.1
Host: localhost:5000
```

**Respuesta:**
```json
[
  {
    "id": "batch_400",
    "assignee": "Mauricio",
    "folder": "/data/batch_400",
    "tasks": ["segmentar", "subir_mascaras", "revisar"],
    "metadata": {
      "assigned_at": "2025-09-28",
      "due_date": "2025-10-05",
      "priority": "alta",
      "reviewed_at": null,
      "review_status": "aprobado"
    },
    "status": "In",
    "mongo_uploaded": true,
    "comments": "Prioridad alta",
    "file_info": {
      "count": 1,
      "latest_upload": "2025-09-27T14:30:00Z",
      "uploaded_by": "Mauricio",
      "file_size": 52428800,
      "has_files": true
    }
  }
]
```

**POST `/api/batches`**
```http
POST /api/batches HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "id": "batch_500",
  "assignee": "Maggie",
  "folder": "/data/batch_500",
  "tasks": ["segmentar", "subir_mascaras", "revisar"],
  "metadata": {
    "assigned_at": "2025-09-30",
    "due_date": "2025-10-07",
    "priority": "media"
  },
  "status": "NS",
  "mongo_uploaded": false,
  "comments": "Nuevo batch creado"
}
```

**PUT `/api/batches/<batch_id>`**
```http
PUT /api/batches/batch_500 HTTP/1.1
Host: localhost:5000
Content-Type: application/json

{
  "assignee": "Ceci",
  "status": "In",
  "metadata": {
    "review_status": "aprobado"
  }
}
```

**DELETE `/api/batches/<batch_id>`**
```http
DELETE /api/batches/batch_500 HTTP/1.1
Host: localhost:5000
```

#### 2. Batches Pendientes

**GET `/api/missing-batches`**
```http
GET /api/missing-batches HTTP/1.1
```

**Respuesta:**
```json
{
  "success": true,
  "missing_batches": [
    "batch_9",
    "batch_10",
    "batch_11",
    "batch_15",
    "batch_2402"
  ],
  "total_missing": 5,
  "total_existing": 195,
  "message": "Se encontraron 5 batches pendientes de segmentación"
}
```

#### 3. Sincronización MongoDB

**POST `/api/sync-batch-files`**
```http
POST /api/sync-batch-files HTTP/1.1
```

**Respuesta:**
```json
{
  "success": true,
  "batches_updated": 12,
  "total_batches": 200,
  "message": "Sincronización completa: 12 batches actualizados",
  "results": [
    {
      "batch_id": "batch_400",
      "files_found": 1,
      "mongo_uploaded": true,
      "latest_upload": "2025-09-27T14:30:00Z",
      "updated": true
    }
  ]
}
```

**GET `/api/check-mongo-files`**
```http
GET /api/check-mongo-files HTTP/1.1
```

**Respuesta:**
```json
{
  "success": true,
  "total_files": 87,
  "recent_files": [
    {
      "filename": "masks_batch_400.tar.xz",
      "uploadDate": "2025-09-27T14:30:00Z",
      "size_mb": 50.5,
      "uploaded_by": "Mauricio"
    }
  ],
  "batch_patterns": {
    "batch_400": ["masks_batch_400.tar.xz"],
    "batch_401": ["Batch_401.zip"]
  },
  "message": "Se encontraron 87 archivos en MongoDB"
}
```

#### 4. Gestión de Segmentadores

**POST `/api/add-segmentador`**
```http
POST /api/add-segmentador HTTP/1.1
Content-Type: application/json

{
  "name": "Ana",
  "role": "Segmentador Senior",
  "email": "ana@example.com"
}
```

**GET `/api/segmentadores`**
```http
GET /api/segmentadores HTTP/1.1
```

**Respuesta:**
```json
{
  "success": true,
  "segmentadores": ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio", "Ana"],
  "total": 6
}
```

---

## 🖥️ Interfaces de Usuario

### 1. Vista de Equipo (team.html)

**URL:** `/` o `/team`

**Características:**
- 🎨 Cards glassmorphism para cada miembro
- 📊 Estadísticas en tiempo real
- 🔄 Ordenamiento alfabético automático
- ➕ Botón para agregar nuevos segmentadores
- 🎯 Doble clic para ver dashboard filtrado

**Funcionalidades JavaScript:**
```javascript
// Estadísticas por miembro
function updateAssigneeStats() {
  // Cuenta batches NS, In, S por responsable
  // Actualiza badges en cada card
  // Muestra gráfico de progreso
}

// Modal para agregar segmentador
function showAddSegmentadorModal() {
  // Formulario con validación
  // POST a /api/add-segmentador
  // Recarga la página automáticamente
}
```

**Diseño:**
```
┌─────────────────────────────────────────────────┐
│         🏥 EQUIPO DE SEGMENTACIÓN               │
│  Sistema de Gestión de Imágenes Médicas        │
└─────────────────────────────────────────────────┘

┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ 👤      │ │ 👤      │ │ 👤      │ │ 👤      │
│ Mauricio│ │ Maggie  │ │  Ceci   │ │  Flor   │
├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤
│ 🔴 NS:5 │ │ 🔴 NS:3 │ │ 🔴 NS:2 │ │ 🔴 NS:4 │
│ 🟡 In:2 │ │ 🟡 In:4 │ │ 🟡 In:1 │ │ 🟡 In:3 │
│ 🟢 S:10 │ │ 🟢 S:15 │ │ 🟢 S:8  │ │ 🟢 S:12 │
└─────────┘ └─────────┘ └─────────┘ └─────────┘

              ┌─────────┐
              │    ➕   │
              │ Agregar │
              │Miembro  │
              └─────────┘
```

### 2. Dashboard Principal (dashboard.html)

**URL:** `/dashboard` o `/dashboard/<assignee>`

**Características:**
- 📝 **Edición Inline:** Cambiar estados, fechas, prioridades directamente
- 🔍 **Búsqueda y Filtros:** DataTables con búsqueda avanzada
- 🎯 **Acciones Rápidas:** Aprobar, rechazar, ver detalles
- 📊 **Estadísticas Dinámicas:** Cards con totales actualizados
- 🔄 **Sincronización:** Botón para verificar archivos en MongoDB

**Tabla Principal:**
```html
<table id="batchesTable">
  <thead>
    <tr>
      <th>Batch ID</th>
      <th>Responsable</th>
      <th>Cargado a Mongo</th>
      <th>Estatus</th>
      <th>Fecha Asignación</th>
      <th>Revisión</th>
      <th>Comentarios</th>
      <th>Acciones</th>
    </tr>
  </thead>
</table>
```

**Funciones Clave:**
```javascript
// Cambio de estado inline
$(document).on('change', '.status-select', function() {
  const batchId = $(this).data('batch-id');
  const newStatus = $(this).val();
  updateBatchStatus(batchId, newStatus);
});

// Cambio de fecha límite inline
$(document).on('change', '.due-date-input', function() {
  const batchId = $(this).data('batch-id');
  const newDate = $(this).val();
  updateBatchDueDate(batchId, newDate);
});

// Revisión rápida
function quickApprove(batchId) {
  updateBatchReview(batchId, 'aprobado');
}

function quickReject(batchId) {
  updateBatchReview(batchId, 'no_aprobado');
}
```

### 3. Gestión de Asignación (batch_management.html)

**URL:** `/assign`

**Características:**
- 🖱️ **Drag & Drop:** Asignación visual intuitiva
- 📋 **Batches Pendientes:** Lista de batches sin asignar
- 👥 **Zonas por Segmentador:** Cards para cada miembro
- 🎨 **Feedback Visual:** Animaciones y colores durante drag
- 📊 **Contadores en Tiempo Real:** Badges con cantidad de batches

**Zonas de la Interfaz:**

```
┌────────────────────┬─────────────────────────────┐
│                    │                             │
│  📥 NO ASIGNADOS   │   👥 SEGMENTADORES         │
│                    │                             │
│  ┌──────────────┐  │  ┌────────┐  ┌────────┐   │
│  │ batch_400    │  │  │Mauricio│  │ Maggie │   │
│  │ NS | Pend.   │  │  │   [3]  │  │   [5]  │   │
│  └──────────────┘  │  ├────────┤  ├────────┤   │
│                    │  │batch_10│  │batch_15│   │
│  ┌──────────────┐  │  │batch_20│  │batch_25│   │
│  │ batch_401    │  │  └────────┘  └────────┘   │
│  │ NS | Pend.   │  │                             │
│  └──────────────┘  │  ┌────────┐  ┌────────┐   │
│                    │  │  Ceci  │  │  Flor  │   │
│  (Arrastrar aquí)  │  │   [2]  │  │   [4]  │   │
│                    │  └────────┘  └────────┘   │
└────────────────────┴─────────────────────────────┘
```

**Funciones Drag & Drop:**
```javascript
// Inicializar drag & drop
function initializeDragAndDrop() {
  // Eventos dragstart, dragover, drop
  $(document).on('dragstart', '.batch-item', handleDragStart);
  $(document).on('drop', '.drop-zone', handleDrop);
}

// Asignar batch
function assignBatchToSegmentador(batchId, newAssignee) {
  if (isPendingBatch(batchId)) {
    createBatchFromPending(batchId, newAssignee);
  } else {
    updateExistingBatch(batchId, newAssignee);
  }
}

// Crear batch desde pendiente
function createBatchFromPending(batchId, assignee) {
  $.ajax({
    url: '/api/batches',
    method: 'POST',
    data: {
      id: batchId,
      assignee: assignee,
      status: 'NS'
    }
  });
}

// Actualizar batch existente
function updateExistingBatch(batchId, newAssignee) {
  $.ajax({
    url: `/api/batches/${batchId}`,
    method: 'PUT',
    data: {
      assignee: newAssignee || null
    }
  });
}
```

### 4. Visualización de Máscaras (masks.html)

**URL:** `/masks`

**Características:**
- 📂 Lista de archivos en MongoDB
- 📊 Información de metadatos
- 🔍 Búsqueda por nombre
- ⬇️ Descarga de archivos

---

## 🐛 Problemáticas y Soluciones

### Problemática #1: Batches desaparecen al regresar a "No Asignados"

**Fecha Detectada:** 2025-09-30
**Estado:** ✅ **SOLUCIONADO**

#### Descripción del Problema
Cuando un usuario arrastraba un batch de vuelta a la zona "No Asignados" (desasignación), el batch desaparecía completamente de la interfaz y no reaparecía en la lista de pendientes. En el dashboard general, el batch aparecía pero sin nombre de responsable asignado.

#### Causa Raíz
1. **Frontend:** La función `updateExistingBatch()` no manejaba correctamente el caso cuando `assignee` era `undefined`, `null` o `''` (string vacío)
2. **Backend:** El endpoint `PUT /api/batches/<id>` no validaba explícitamente el valor `null` para `assignee`
3. **Sincronización:** Después de la actualización, la interfaz no se recargaba completamente, causando inconsistencias visuales

#### Código Problemático

**Frontend (ANTES):**
```javascript
// batch_management.html línea ~1122
function updateExistingBatch(batchId, newAssignee) {
  const batch = batches.find(b => b.id === batchId);

  // ❌ PROBLEMA: No manejaba correctamente undefined
  batch.assignee = newAssignee || null;

  $.ajax({
    url: `/api/batches/${batchId}`,
    method: 'PUT',
    data: JSON.stringify({
      assignee: newAssignee || null,  // ❌ Inconsistente
      metadata: batch.metadata
    }),
    success: function() {
      updateDragDropInterface();  // ❌ No recargaba todo
    }
  });
}
```

**Backend (ANTES):**
```python
# app.py línea ~172
@app.route("/api/batches/<batch_id>", methods=["PUT"])
def update_batch(batch_id):
    data = request.json
    update_data = {}

    # ❌ PROBLEMA: No validaba explícitamente null
    if "assignee" in data:
        update_data["assignee"] = data["assignee"]

    result = batches_col.update_one({"id": batch_id}, {"$set": update_data})

    if result.modified_count > 0:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False}), 404
```

#### Solución Implementada

**Frontend (DESPUÉS):**
```javascript
// batch_management.html línea ~1122
function updateExistingBatch(batchId, newAssignee) {
  const batch = batches.find(b => b.id === batchId);
  if (!batch) {
    showNotification('Batch no encontrado', 'error');
    return;
  }

  const oldAssignee = batch.assignee;

  // ✅ SOLUCIÓN: Validación explícita de valores vacíos
  const updateData = {
    assignee: newAssignee === '' || newAssignee === undefined ? null : newAssignee,
    metadata: batch.metadata
  };

  // ✅ Agregar fecha de asignación solo si se está asignando
  if (newAssignee && !batch.metadata.assigned_at) {
    updateData.metadata.assigned_at = new Date().toISOString().split('T')[0];
  }

  console.log(`🔄 Actualizando batch ${batchId}:`, {
    old: oldAssignee,
    new: newAssignee,
    data: updateData
  });

  $.ajax({
    url: `/api/batches/${batchId}`,
    method: 'PUT',
    contentType: 'application/json',
    data: JSON.stringify(updateData),
    success: function(response) {
      console.log('✅ Batch actualizado correctamente:', response);

      // ✅ Actualizar localmente después de confirmar
      batch.assignee = updateData.assignee;
      batch.metadata = updateData.metadata;

      showNotification(
        newAssignee ?
          `Batch ${batchId} asignado a ${newAssignee}` :
          `Batch ${batchId} regresado a "No Asignados"`,  // ✅ Mensaje claro
        'success'
      );

      // ✅ SOLUCIÓN CLAVE: Recargar interfaz completa
      loadBatches();
    },
    error: function(xhr) {
      console.error('❌ Error actualizando batch:', xhr);
      showNotification('Error asignando batch: ' + (xhr.responseJSON?.error || 'Error desconocido'), 'error');
      updateDragDropInterface();
    }
  });
}
```

**Backend (DESPUÉS):**
```python
# app.py línea ~172
@app.route("/api/batches/<batch_id>", methods=["PUT"])
def update_batch(batch_id):
    data = request.json

    update_data = {}

    # ✅ SOLUCIÓN: Validación explícita de assignee
    if "assignee" in data:
        # Permitir explícitamente None/null para desasignar
        update_data["assignee"] = data["assignee"] if data["assignee"] else None
        print(f"🔄 Actualizando assignee de {batch_id} a: {update_data['assignee']}")

    if "status" in data:
        update_data["status"] = data["status"]
    if "comments" in data:
        update_data["comments"] = data["comments"]
    if "folder" in data:
        update_data["folder"] = data["folder"]

    # Campos de metadata
    if "metadata" in data:
        metadata = data["metadata"]
        for key, value in metadata.items():
            update_data[f"metadata.{key}"] = value

    result = batches_col.update_one({"id": batch_id}, {"$set": update_data})

    # ✅ SOLUCIÓN: Retornar éxito incluso si no se modificó (ya tenía ese valor)
    if result.modified_count > 0 or batches_col.find_one({"id": batch_id}):
        print(f"✅ Batch {batch_id} actualizado correctamente")
        return jsonify({"success": True, "message": f"Batch {batch_id} actualizado"})
    else:
        return jsonify({"success": False, "error": "Batch no encontrado"}), 404
```

#### Cambios Realizados

**Archivo:** `templates/batch_management.html`
**Líneas modificadas:** 1122-1178

1. ✅ Validación explícita: `newAssignee === '' || newAssignee === undefined ? null : newAssignee`
2. ✅ Logs detallados para debugging
3. ✅ Actualización local solo después de confirmar servidor
4. ✅ Mensaje de notificación específico para desasignación
5. ✅ Llamada a `loadBatches()` en lugar de `updateDragDropInterface()` para recarga completa

**Archivo:** `app.py`
**Líneas modificadas:** 172-211

1. ✅ Validación: `data["assignee"] if data["assignee"] else None`
2. ✅ Logs de actualización
3. ✅ Retorno de éxito incluso si `modified_count == 0` pero el batch existe
4. ✅ Mensaje descriptivo en respuesta

#### Pruebas Realizadas

**Test Case 1: Asignar batch pendiente**
```
✅ batch_400 (pendiente) → Arrastrar a Mauricio
✅ Resultado: batch_400 aparece en zona de Mauricio con status "NS"
```

**Test Case 2: Reasignar batch entre segmentadores**
```
✅ batch_400 (Mauricio) → Arrastrar a Maggie
✅ Resultado: batch_400 desaparece de Mauricio y aparece en Maggie
```

**Test Case 3: Desasignar batch (regresar a No Asignados)**
```
✅ batch_400 (Mauricio) → Arrastrar a "No Asignados"
✅ Resultado: batch_400 desaparece de Mauricio y reaparece en "No Asignados"
✅ Dashboard general: batch_400 aparece sin nombre de asignado (assignee = null)
```

#### Referencias de Código

- Frontend: `/templates/batch_management.html:1122-1178`
- Backend: `/app.py:172-211`
- Commit: (pendiente de commit)

---

### Problemática #2: [Pendiente]

**Fecha Detectada:** [A definir]
**Estado:** 🔍 **EN INVESTIGACIÓN**

_Se actualizará cuando el usuario reporte nuevos problemas._

---

## 🗺️ Roadmap de Desarrollo

### Fase 1: Sistema Base (Completado ✅)
- [x] Estructura Flask básica
- [x] Conexión a MongoDB
- [x] CRUD de batches
- [x] Vista de equipo
- [x] Dashboard general

### Fase 2: Mejoras UX (Completado ✅)
- [x] Sistema drag & drop
- [x] Edición inline en dashboard
- [x] Sincronización con archivos MongoDB
- [x] Diseño glassmorphism
- [x] Menú hamburguesa overlay

### Fase 3: Gestión Avanzada (En Progreso 🔄)
- [x] Asignación visual de batches
- [x] Estados y revisión de batches
- [x] Filtros por responsable
- [ ] Sistema de notificaciones
- [ ] Historial de cambios (audit log)

### Fase 4: Métricas y Análisis (Pendiente 📋)
- [ ] Gráficos de progreso por miembro
- [ ] Reportes semanales/mensuales
- [ ] Predicción de tiempos
- [ ] Identificación de cuellos de botella

### Fase 5: Integración y Automatización (Futuro 🚀)
- [ ] API de integración con sistemas externos
- [ ] Webhooks para notificaciones
- [ ] Carga automática de batches desde servidor
- [ ] Exportación de reportes (PDF, Excel)

---

## 🛠️ Guía de Instalación

### Requisitos Previos

- Python 3.10 o superior
- MongoDB 4.5 o superior
- Git (opcional)
- 2GB RAM mínimo
- 1GB espacio en disco

### Instalación Paso a Paso

#### 1. Clonar el Repositorio

```bash
cd ~/proyectos
git clone <repo-url> segmentacion-dashboard
cd segmentacion-dashboard
```

#### 2. Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

#### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Contenido de `requirements.txt`:**
```
Flask==2.3.3
pymongo==4.5.0
python-dateutil==2.8.2
```

#### 4. Configurar MongoDB

**Editar `db.py`:**
```python
MONGO_URI = "mongodb://usuario:password@host:puerto/database?authSource=admin"
DB_NAME = "segmentacion_db"
```

**Probar conexión:**
```bash
python3 test_mongo.py
```

**Salida esperada:**
```
✅ Conectado a MongoDB
📊 Base de datos: segmentacion_db
📚 Colecciones: ['batches', 'masks']
```

#### 5. Inicializar Datos (Opcional)

```bash
# Cargar batches iniciales desde JSON
curl -X POST http://localhost:5000/api/init-batches
```

#### 6. Ejecutar la Aplicación

```bash
python3 app.py
```

**Salida esperada:**
```
 * Serving Flask app 'app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in production.
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

#### 7. Acceder a la Aplicación

Abrir navegador en:
```
http://localhost:5000
```

### Configuración de Producción

**Usar Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Systemd Service (`/etc/systemd/system/segmentacion.service`):**
```ini
[Unit]
Description=Segmentacion Dashboard
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/segmentacion-dashboard
Environment="PATH=/var/www/segmentacion-dashboard/venv/bin"
ExecStart=/var/www/segmentacion-dashboard/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

**Activar servicio:**
```bash
sudo systemctl enable segmentacion
sudo systemctl start segmentacion
```

---

## 📘 Guía de Uso

### Flujo de Trabajo Típico

#### Para Administrador

**1. Agregar Nuevo Segmentador**
```
Inicio → Tarjeta "+" → Formulario → Nombre: "Ana" → Guardar
```

**2. Crear Batch Manualmente**
```
Dashboard → "Nuevo Batch" →
  ID: batch_500
  Responsable: Mauricio
  Fecha Límite: 2025-10-05
  Prioridad: Alta
→ Crear
```

**3. Asignar Batch Pendiente (Drag & Drop)**
```
Asignar Batches →
  Arrastrar "batch_400" desde "No Asignados" →
  Soltar en zona de "Mauricio"
```

**4. Sincronizar Archivos de MongoDB**
```
Dashboard → "Verificar MongoDB" →
  Esperar sincronización →
  Ver reporte de archivos encontrados
```

#### Para Segmentador

**1. Ver Mis Batches Asignados**
```
Inicio → Doble clic en mi tarjeta →
  Dashboard filtrado con mis batches
```

**2. Actualizar Estado de Batch**
```
Dashboard → Localizar batch_400 →
  Cambiar estado de "NS" a "In" →
  Guardar (automático)
```

**3. Subir Máscaras a MongoDB**
```
# Usar script externo o interfaz de carga
# Luego sincronizar en el dashboard
```

**4. Marcar como Completado**
```
Dashboard → batch_400 →
  Estado: "S" (Segmentado) →
  Comentarios: "Completado, 150 imágenes" →
  Guardar
```

#### Para Revisor

**1. Ver Batches para Revisar**
```
Dashboard → Filtrar por estado "In" →
  Ver solo batches en progreso
```

**2. Aprobar Batch**
```
Dashboard → batch_400 →
  Revisión: "✅ Aprobado" →
  Comentarios: "Calidad excelente" →
  Guardar
```

**3. Rechazar Batch**
```
Dashboard → batch_401 →
  Revisión: "❌ No Aprobado" →
  Comentarios: "Revisar imágenes 50-75" →
  Guardar
```

### Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| `Ctrl + F` | Buscar en tabla |
| `Esc` | Cerrar modales |
| `Enter` | Guardar formulario activo |

### Buenas Prácticas

1. ✅ **Sincronizar archivos diariamente** para mantener `mongo_uploaded` actualizado
2. ✅ **Usar comentarios descriptivos** al aprobar/rechazar batches
3. ✅ **Establecer fechas límite realistas** considerando la carga de trabajo
4. ✅ **Revisar batches pendientes** antes de asignar nuevos
5. ✅ **Hacer backups de la base de datos** semanalmente

---

## 📊 Estadísticas del Proyecto

### Métricas de Código

| Métrica | Valor |
|---------|-------|
| Total de líneas de código | ~7,263 |
| Archivos Python | 3 |
| Templates HTML | 8 activos |
| Endpoints API | 15 |
| Funciones JavaScript | ~50 |
| Colecciones MongoDB | 2 |

### Capacidad del Sistema

| Recurso | Capacidad |
|---------|-----------|
| Batches soportados | Ilimitado (MongoDB) |
| Segmentadores | Ilimitado (dinámico) |
| Archivos por batch | Ilimitado |
| Usuarios simultáneos | ~100 (con Gunicorn) |
| Tamaño de archivo máximo | Configurable (GridFS) |

---

## 🤝 Contribuciones

### Cómo Reportar Problemas

Cuando encuentres un problema, por favor proporciona:

1. **Descripción clara** del comportamiento esperado vs. actual
2. **Pasos para reproducir** el problema
3. **Screenshots** o videos si es posible
4. **Logs** del navegador (Consola F12)
5. **Versión del navegador** y sistema operativo

### Formato de Reporte

```markdown
## Descripción
[Describe el problema]

## Pasos para Reproducir
1. Ir a...
2. Hacer clic en...
3. Observar...

## Comportamiento Esperado
[Lo que debería pasar]

## Comportamiento Actual
[Lo que realmente pasa]

## Screenshots
[Adjuntar imágenes]

## Entorno
- Navegador: Chrome 120
- SO: Ubuntu 22.04
- Versión del sistema: 1.0.0
```

---

## 📄 Licencia

Este proyecto es para uso interno del equipo de segmentación de imágenes médicas.

**Restricciones:**
- ❌ No redistribuir sin autorización
- ❌ No usar para propósitos comerciales
- ✅ Modificaciones permitidas para uso interno

---

## 📞 Contacto

**Equipo de Desarrollo:**
- Mauricio
- Maggie
- Ceci
- Flor
- Ignacio

**Soporte Técnico:** [A definir]

---

## 📚 Referencias

- [Flask Documentation](https://flask.palletsprojects.com/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
- [DataTables Documentation](https://datatables.net/)

---

**Última actualización:** 2025-09-30
**Versión del documento:** 1.0.0

---

## 🔄 Historial de Cambios del Documento

| Fecha | Versión | Cambios |
|-------|---------|---------|
| 2025-09-30 | 1.0.0 | Creación inicial del documento completo |
| 2025-09-30 | 1.0.0 | Añadida Problemática #1 y solución |

---

_Este documento se actualizará automáticamente conforme se detecten y resuelvan nuevas problemáticas._
