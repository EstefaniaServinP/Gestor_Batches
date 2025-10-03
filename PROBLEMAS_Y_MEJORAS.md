# ⚠️ Análisis de Problemas y Posibles Errores

> **Documento:** Análisis de Código - Problemas Potenciales y Mejoras
> **Fecha:** Julio 2025
> **Propósito:** Identificar bugs, code smells, vulnerabilidades y áreas de mejora

---

## 🔴 PROBLEMAS CRÍTICOS

### 1. **Falta de Autenticación/Autorización** ⭐⭐⭐⭐⭐
**Ubicación:** Todo el sistema
**Severidad:** CRÍTICA

**Problema:**
```python
# app.py - NO HAY autenticación en ninguna ruta
@app.route("/api/batches", methods=["DELETE"])
def delete_batch(batch_id):
    # ¡Cualquiera puede eliminar batches!
    batches_col.delete_one({"id": batch_id})
```

**Impacto:**
- Cualquiera puede crear/modificar/eliminar batches
- Acceso sin restricción a métricas sensibles
- Sin auditoría de quién hizo qué cambio

**Solución:**
```python
from flask_login import LoginManager, login_required

@app.route("/api/batches/<batch_id>", methods=["DELETE"])
@login_required  # Requiere autenticación
def delete_batch(batch_id):
    # Verificar permisos
    if current_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403
    ...
```

**Recomendación:**
- Implementar Flask-Login o JWT
- Roles: admin, segmentador, viewer
- Auditoría de cambios en MongoDB

---

### 2. **Variable Global Mutable (CREW_MEMBERS)** ⭐⭐⭐⭐
**Ubicación:** `app.py:48`
**Severidad:** ALTA

**Problema:**
```python
# app.py
CREW_MEMBERS = ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"]

@app.route("/api/add-segmentador", methods=["POST"])
def add_segmentador():
    CREW_MEMBERS.append(name)  # ¡Se pierde al reiniciar servidor!
```

**Impacto:**
- Los segmentadores agregados se pierden al reiniciar Flask
- No hay persistencia de cambios
- Inconsistencia entre sesiones

**Solución:**
```python
# Crear colección 'segmentadores' en MongoDB
def get_crew_members():
    return list(db.segmentadores.find({}, {"name": 1, "_id": 0}))

@app.route("/api/add-segmentador", methods=["POST"])
def add_segmentador():
    db.segmentadores.insert_one({"name": name, "role": role, "email": email})
```

---

### 3. **Conexión MongoDB Global Sin Manejo de Reconexión** ⭐⭐⭐⭐
**Ubicación:** `db.py:7-14`, `app.py:28-42`
**Severidad:** ALTA

**Problema:**
```python
# db.py
_client = None

def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client  # ¿Qué pasa si la conexión se cae después?
```

**Impacto:**
- Si MongoDB se desconecta, el cliente no se reconecta automáticamente
- Errores `ServerSelectionTimeoutError` no manejados
- Pérdida de conexión → servidor inoperable

**Solución:**
```python
from pymongo.errors import ServerSelectionTimeoutError, AutoReconnect

def get_client():
    global _client
    try:
        if _client is None:
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                retryWrites=True,
                retryReads=True
            )
        # Verificar que la conexión esté viva
        _client.admin.command('ping')
        return _client
    except (ServerSelectionTimeoutError, AutoReconnect) as e:
        print(f"❌ Error de conexión MongoDB: {e}")
        _client = None  # Resetear para reintentar
        raise
```

---

### 4. **Inyección NoSQL en Búsquedas Regex** ⭐⭐⭐
**Ubicación:** `app.py:552-556`
**Severidad:** MEDIA-ALTA

**Problema:**
```python
# app.py:552
files = list(masks_col.find(
    {"filename": {"$regex": search_pattern, "$options": "i"}},
    # ¡search_pattern viene de construcción de string sin sanitizar!
))
```

**Impacto:**
- Un input malicioso podría inyectar operadores MongoDB
- Ejemplo: `{"filename": {"$ne": null}}` devolvería TODO

**Solución:**
```python
import re

def sanitize_regex(pattern):
    # Escapar caracteres especiales de regex
    return re.escape(pattern)

# En el endpoint:
search_pattern = sanitize_regex(f"masks_batch_{batch_number}")
files = list(masks_col.find({"filename": {"$regex": search_pattern, "$options": "i"}}))
```

---

## 🟠 PROBLEMAS IMPORTANTES

### 5. **Hardcoded List de Batches en `/api/missing-batches`** ⭐⭐⭐
**Ubicación:** `app.py:775-865`
**Severidad:** MEDIA

**Problema:**
```python
@app.route("/api/missing-batches", methods=["GET"])
def get_missing_batches():
    all_possible_batches = [
        'batch_20251002T105618', 'batch_20251002T105716', ...  # ¡90 líneas de IDs!
    ]
```

**Impacto:**
- Lista estática → requiere modificar código para agregar batches
- Dificulta mantenimiento
- Propenso a errores manuales

**Solución:**
```python
# Guardar en archivo JSON o colección MongoDB
def get_expected_batches():
    with open("expected_batches.json") as f:
        return json.load(f)["batches"]

# O generar dinámicamente desde rangos
def generate_batch_range(start, end):
    return [f"batch_{i}" for i in range(start, end + 1)]
```

---

### 6. **Falta de Validación de Entrada en POST/PUT** ⭐⭐⭐
**Ubicación:** `app.py:151-203`, `app.py:205-244`
**Severidad:** MEDIA

**Problema:**
```python
@app.route("/api/batches", methods=["POST"])
def create_batch():
    data = request.json  # ¡Sin validar!
    batch = {
        "id": batch_id,
        "assignee": data.get("assignee", ""),  # Acepta cualquier valor
        "status": data.get("status", "NS"),    # Sin validar estados
        ...
    }
```

**Impacto:**
- Datos incorrectos en BD
- Estados inválidos (typos, valores no esperados)
- Campos faltantes no detectados

**Solución:**
```python
from flask import request, jsonify
from jsonschema import validate, ValidationError

BATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "pattern": "^batch_[0-9]+$"},
        "assignee": {"type": "string", "enum": CREW_MEMBERS},
        "status": {"type": "string", "enum": ["NS", "FS", "S"]},
        "folder": {"type": "string"},
        ...
    },
    "required": ["id", "assignee"]
}

@app.route("/api/batches", methods=["POST"])
def create_batch():
    try:
        validate(instance=request.json, schema=BATCH_SCHEMA)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    ...
```

---

### 7. **Manejo de Errores Inconsistente** ⭐⭐⭐
**Ubicación:** Múltiples endpoints
**Severidad:** MEDIA

**Problema:**
```python
# app.py:148-149
except Exception as e:
    print("❌ Error en get_batches:", e)  # Solo print, sin registrar
    return jsonify({"error": str(e)}), 500  # Expone stacktrace al cliente
```

**Impacto:**
- Información sensible expuesta en errores
- Logs difíciles de rastrear (solo prints)
- Sin monitoreo centralizado

**Solución:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500

try:
    ...
except ValueError as e:
    logger.warning(f"Invalid input: {e}")
    return jsonify({"error": "Invalid input"}), 400
except Exception as e:
    logger.error(f"Error in get_batches: {e}", exc_info=True)
    return jsonify({"error": "Failed to retrieve batches"}), 500
```

---

### 8. **Índice Único en `batches.id` No se Verifica Antes de Insert** ⭐⭐⭐
**Ubicación:** `app.py:185`, `db.py:43`
**Severidad:** MEDIA

**Problema:**
```python
# db.py:43
db["batches"].create_index([("id", ASCENDING)], unique=True, background=True)

# app.py:185
result = batches_col.insert_one(batch)  # ¡Puede fallar con DuplicateKeyError!
```

**Impacto:**
- Si se intenta insertar batch con ID duplicado → error 500
- Cliente no recibe mensaje claro

**Solución:**
```python
from pymongo.errors import DuplicateKeyError

@app.route("/api/batches", methods=["POST"])
def create_batch():
    try:
        result = batches_col.insert_one(batch)
    except DuplicateKeyError:
        return jsonify({"error": f"Batch con ID '{batch_id}' ya existe"}), 409
    except Exception as e:
        logger.error(f"Error creating batch: {e}")
        return jsonify({"error": "Failed to create batch"}), 500
```

---

## 🟡 PROBLEMAS MENORES / CODE SMELLS

### 9. **Funciones Muy Largas** ⭐⭐
**Ubicación:** `app.py:512-621` (110 líneas), `app.py:770-890` (120 líneas)
**Severidad:** BAJA

**Problema:**
- `sync_batch_files()` tiene 110 líneas
- `get_missing_batches()` tiene 120 líneas (90 de datos)
- Dificulta lectura y testing

**Solución:**
```python
# Refactorizar en funciones más pequeñas
def extract_batch_number(batch_id):
    return batch_id.replace("batch_", "").replace("Batch_", "")

def search_files_for_batch(batch_number, masks_col):
    patterns = generate_search_patterns(batch_number)
    return find_files_by_patterns(patterns, masks_col)

def sync_batch_files():
    batches = get_all_batches()
    for batch in batches:
        files = search_files_for_batch(batch["id"], masks_col)
        update_batch_file_info(batch["id"], files)
```

---

### 10. **Logging con Emojis (No Estándar)** ⭐
**Ubicación:** Todo el código
**Severidad:** BAJA

**Problema:**
```python
print("✅ Batch batch_400 actualizado")
print("🔄 Sincronización completa: 50 batches")
```

**Impacto:**
- Emojis pueden no renderizarse en todos los sistemas
- Dificulta parsing de logs
- No es formato estándar

**Solución:**
```python
logger.info("Batch batch_400 actualizado successfully")
logger.info("Synchronization complete: 50 batches updated")

# Usar niveles de log adecuados:
logger.debug(...)   # Debugging
logger.info(...)    # Operaciones normales
logger.warning(...) # Advertencias
logger.error(...)   # Errores recuperables
logger.critical(...) # Errores críticos
```

---

### 11. **Comentarios Redundantes** ⭐
**Ubicación:** Múltiples archivos
**Severidad:** BAJA

**Problema:**
```python
# Verificar que el batch existe antes de eliminarlo
existing_batch = batches_col.find_one({"id": batch_id})
if not existing_batch:
    return jsonify(...)
```

**Solución:**
- Eliminar comentarios que repiten el código
- Mantener solo comentarios que expliquen **por qué**, no **qué**

---

### 12. **Variables No Utilizadas** ⭐
**Ubicación:** Varios archivos
**Severidad:** BAJA

**Problema:**
```python
# app.py:188-190
batch_response = batch.copy()
if '_id' in batch_response:
    del batch_response['_id']
# batch_response no se usa después del insert_one
```

**Solución:**
- Eliminar código muerto
- Usar linters (pylint, flake8)

---

## 🔵 PROBLEMAS DE FRONTEND

### 13. **jQuery Mezclado con Vanilla JS** ⭐⭐
**Ubicación:** `dashboard.js`, `batch_management.js`
**Severidad:** BAJA

**Problema:**
```javascript
// dashboard.js - Mezcla de estilos
document.addEventListener('DOMContentLoaded', function() {  // Vanilla
  $('#batchesTable').DataTable({ ... });  // jQuery
});

$(document).on('click', '.editable', function() { ... });  // jQuery
```

**Impacto:**
- Código inconsistente
- Dependencia de jQuery innecesaria (DataTables la requiere)

**Solución:**
- Elegir un enfoque y mantenerlo
- O migrar a framework moderno (React, Vue)

---

### 14. **Manejo de Estado Global Sin Patrón** ⭐⭐
**Ubicación:** `dashboard.js:6-8`, `batch_management.js:6`
**Severidad:** BAJA

**Problema:**
```javascript
// dashboard.js
let batchesData = [];
let dataTable = null;
let currentFilter = '';
```

**Impacto:**
- Estado global mutable
- Dificulta testing
- No hay single source of truth

**Solución:**
```javascript
// Usar patrón módulo o clase
const DashboardState = {
  batches: [],
  dataTable: null,
  currentFilter: '',

  setBatches(batches) {
    this.batches = batches;
    this.render();
  }
};
```

---

### 15. **Hardcoded URLs en JavaScript** ⭐⭐
**Ubicación:** Múltiples archivos JS
**Severidad:** BAJA

**Problema:**
```javascript
// dashboard.js:35
const response = await fetch(`/api/batches?page=${page}&per_page=${perPage}`);
```

**Impacto:**
- Si cambia la ruta de API → hay que buscar en todos los JS

**Solución:**
```javascript
// config.js
const API_BASE = '/api';
const ENDPOINTS = {
  batches: `${API_BASE}/batches`,
  segmentadores: `${API_BASE}/segmentadores`,
  ...
};

// dashboard.js
const response = await fetch(`${ENDPOINTS.batches}?page=${page}`);
```

---

### 16. **Falta de Manejo de Errores en Fetch** ⭐⭐⭐
**Ubicación:** Todos los archivos JS
**Severidad:** MEDIA

**Problema:**
```javascript
// dashboard.js:35-49
async function loadBatches(page = 1, perPage = 50) {
  try {
    const response = await fetch(`/api/batches?...`);
    const data = await response.json();
    // ¡No verifica response.ok!
  } catch (error) {
    console.error('Error cargando batches:', error);
    throw error;  // Solo re-throw
  }
}
```

**Impacto:**
- Si API devuelve 404/500 → `data` puede no ser JSON
- Usuario no recibe feedback claro

**Solución:**
```javascript
async function loadBatches(page = 1, perPage = 50) {
  try {
    const response = await fetch(`/api/batches?page=${page}&per_page=${perPage}`);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error cargando batches:', error);
    showNotification(`Error: ${error.message}`, 'error');
    throw error;
  }
}
```

---

### 17. **Edición Inline Sin Confirmación en Cambios Críticos** ⭐⭐
**Ubicación:** `dashboard.js:296-340`
**Severidad:** BAJA

**Problema:**
```javascript
// dashboard.js:296
async function saveInlineEdit(element, field, batchId, newValue, oldValue) {
  // Guarda inmediatamente sin confirmar
  const response = await fetch(`/api/batches/${batchId}`, {...});
}
```

**Impacto:**
- Cambios accidentales se guardan sin advertencia
- Especialmente peligroso en campos críticos (status, assignee)

**Solución:**
```javascript
async function saveInlineEdit(element, field, batchId, newValue, oldValue) {
  // Confirmar cambios críticos
  if (['status', 'assignee'].includes(field)) {
    if (!confirm(`¿Cambiar ${field} de "${oldValue}" a "${newValue}"?`)) {
      cancelInlineEdit(element, oldValue);
      return;
    }
  }

  const response = await fetch(`/api/batches/${batchId}`, {...});
  ...
}
```

---

## 🔧 MEJORAS DE RENDIMIENTO

### 18. **Carga de Todos los Batches en Frontend** ⭐⭐⭐
**Ubicación:** `dashboard.js:33-55`
**Severidad:** MEDIA

**Problema:**
```javascript
// dashboard.js
async function loadBatches(page = 1, perPage = 50) {
  const response = await fetch(`/api/batches?page=${page}&per_page=${perPage}`);
  batchesData = data.batches;  // Solo carga primera página
  // DataTable muestra solo estos 50, pero no hay paginación server-side
}
```

**Impacto:**
- Si hay 10,000 batches → solo ve los primeros 50
- DataTable paginación es client-side

**Solución:**
```javascript
// Implementar server-side processing en DataTable
$('#batchesTable').DataTable({
  processing: true,
  serverSide: true,
  ajax: {
    url: '/api/batches',
    data: function(d) {
      return {
        page: Math.floor(d.start / d.length) + 1,
        per_page: d.length,
        search: d.search.value
      };
    }
  },
  ...
});
```

---

### 19. **Múltiples Queries en Loop (N+1 Problem)** ⭐⭐⭐
**Ubicación:** `app.py:521-607`
**Severidad:** MEDIA

**Problema:**
```python
# app.py:521-607 - sync_batch_files()
for batch in batches:
    for pattern in patterns:
        files = list(masks_col.find({...}))  # ¡1 query por patrón!
```

**Impacto:**
- Si hay 500 batches × 9 patrones = 4,500 queries
- Lentitud extrema

**Solución:**
```python
# Optimizar con aggregation pipeline
pipeline = [
    {
        "$group": {
            "_id": {"$regexFind": {"input": "$filename", "regex": r"batch_(\d+)"}},
            "files": {"$push": "$$ROOT"}
        }
    }
]
files_by_batch = {doc["_id"]["match"]: doc["files"] for doc in masks_col.aggregate(pipeline)}
```

---

### 20. **Índices Faltantes en Queries Frecuentes** ⭐⭐
**Ubicación:** `db.py:36-49`
**Severidad:** MEDIA

**Problema:**
```python
# db.py - Solo 3 índices creados
db["batches"].create_index([("id", ASCENDING)], unique=True)
db["batches"].create_index([("assignee", ASCENDING)])
db["masks.files"].create_index([("filename", ASCENDING)])
```

**Impacto:**
- Query `find({"status": "NS"})` → full collection scan
- Query `find({"mongo_uploaded": true})` → full scan

**Solución:**
```python
# Agregar índices compuestos
db["batches"].create_index([("status", ASCENDING), ("assignee", ASCENDING)])
db["batches"].create_index([("mongo_uploaded", ASCENDING)])
db["batches"].create_index([("metadata.due_date", ASCENDING)])
```

---

## 🛡️ MEJORAS DE SEGURIDAD

### 21. **CORS No Configurado** ⭐⭐
**Ubicación:** `app.py`
**Severidad:** BAJA (si solo se usa en mismo origen)

**Problema:**
```python
# No hay configuración de CORS
# Si se intenta acceder desde otro dominio → bloqueado
```

**Solución:**
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://tudominio.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

---

### 22. **Secrets en Variables de Entorno Sin Validar** ⭐⭐
**Ubicación:** `db.py:4-5`
**Severidad:** BAJA

**Problema:**
```python
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
# Si MONGO_URI no está definido → usa localhost (puede no ser deseado)
```

**Solución:**
```python
MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is required")

# O usar dotenv
from dotenv import load_dotenv
load_dotenv()
```

---

## 📊 MEJORAS DE ARQUITECTURA

### 23. **Lógica de Negocio en Rutas** ⭐⭐⭐
**Ubicación:** `app.py` (todo el archivo)
**Severidad:** MEDIA

**Problema:**
- Rutas de Flask contienen lógica de negocio directamente
- Dificulta testing unitario
- Viola separación de responsabilidades

**Solución:**
```python
# services/batch_service.py
class BatchService:
    def __init__(self, batches_col):
        self.batches_col = batches_col

    def get_batches_paginated(self, page=1, per_page=50):
        skip = (page - 1) * per_page
        batches = list(self.batches_col.find({}).skip(skip).limit(per_page))
        total = self.batches_col.count_documents({})
        return batches, total

    def create_batch(self, batch_data):
        # Validación + lógica de creación
        ...

# app.py
batch_service = BatchService(batches_col)

@app.route("/api/batches", methods=["GET"])
def get_batches():
    batches, total = batch_service.get_batches_paginated(page, per_page)
    return jsonify({"batches": batches, "total": total})
```

---

### 24. **Sin Tests Automatizados** ⭐⭐⭐⭐
**Ubicación:** Proyecto completo
**Severidad:** ALTA

**Problema:**
- No hay carpeta `tests/`
- Sin cobertura de tests
- Refactoring riesgoso

**Solución:**
```python
# tests/test_batch_service.py
import pytest
from services.batch_service import BatchService

@pytest.fixture
def mock_batches_col():
    return MagicMock()

def test_get_batches_paginated(mock_batches_col):
    service = BatchService(mock_batches_col)
    batches, total = service.get_batches_paginated(page=1, per_page=10)
    assert len(batches) <= 10

# Ejecutar: pytest tests/
```

---

### 25. **Sin Containerización (Docker)** ⭐⭐
**Ubicación:** Proyecto
**Severidad:** BAJA

**Problema:**
- Despliegue manual
- Dependencias no documentadas
- Dificulta reproducibilidad

**Solución:**
```dockerfile
# Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]

# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - MONGO_URI=mongodb://mongo:27017
  mongo:
    image: mongo:6
    volumes:
      - mongo-data:/data/db
```

---

## 📋 RESUMEN DE PRIORIDADES

### **Urgente (Hacer YA):**
1. ✅ Implementar autenticación/autorización
2. ✅ Persistir CREW_MEMBERS en MongoDB
3. ✅ Mejorar manejo de reconexión MongoDB
4. ✅ Validar inputs en POST/PUT
5. ✅ Sanitizar regex patterns

### **Importante (Próximas 2 semanas):**
6. ✅ Implementar tests unitarios
7. ✅ Refactorizar lógica a services
8. ✅ Optimizar queries N+1
9. ✅ Agregar índices faltantes
10. ✅ Server-side DataTable

### **Deseable (Próximo mes):**
11. ✅ Containerizar con Docker
12. ✅ Centralizar logging (no prints)
13. ✅ Configurar CORS adecuadamente
14. ✅ Migrar hardcoded lista de batches
15. ✅ Mejorar UX (confirmaciones, feedback)

### **Opcional (Backlog):**
16. ✅ Migrar a framework moderno (React/Vue)
17. ✅ Refactorizar funciones largas
18. ✅ Eliminar comentarios redundantes
19. ✅ Standarizar logging (sin emojis)

---

## 🎯 CHECKLIST DE MEJORAS

### **Seguridad:**
- [ ] Implementar autenticación con Flask-Login
- [ ] Agregar roles (admin, segmentador, viewer)
- [ ] Validar todos los inputs con schemas
- [ ] Sanitizar regex patterns
- [ ] Configurar CORS correctamente
- [ ] Usar variables de entorno con dotenv
- [ ] Ocultar stacktraces en producción

### **Estabilidad:**
- [ ] Manejo robusto de reconexión MongoDB
- [ ] Persistir CREW_MEMBERS en BD
- [ ] Verificar `response.ok` en fetch
- [ ] Agregar manejo de DuplicateKeyError
- [ ] Implementar retry logic

### **Rendimiento:**
- [ ] Server-side processing en DataTables
- [ ] Optimizar queries N+1
- [ ] Agregar índices compuestos
- [ ] Cachear resultados frecuentes
- [ ] Lazy loading de datos

### **Mantenibilidad:**
- [ ] Tests unitarios (>80% coverage)
- [ ] Refactorizar a services
- [ ] Separar lógica de rutas
- [ ] Documentar APIs con OpenAPI/Swagger
- [ ] Configurar linting (pylint, flake8, ESLint)

### **DevOps:**
- [ ] Dockerizar aplicación
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Monitoring (Sentry, New Relic)
- [ ] Backup automático MongoDB
- [ ] Health checks

---

## 📚 RECURSOS RECOMENDADOS

**Seguridad:**
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask-Login: https://flask-login.readthedocs.io/

**Testing:**
- pytest: https://docs.pytest.org/
- Mocking: https://docs.python.org/3/library/unittest.mock.html

**Arquitectura:**
- Clean Architecture: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Repository Pattern: https://martinfowler.com/eaaCatalog/repository.html

**MongoDB:**
- Indexing Strategies: https://www.mongodb.com/docs/manual/indexes/
- Aggregation Pipeline: https://www.mongodb.com/docs/manual/aggregation/

---

**Última actualización:** Julio 2025
**Mantenido por:** Equipo de Desarrollo
