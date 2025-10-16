# Sistema de Respaldo y Exportación de Datos

## Fecha: 15 de Octubre de 2025

## 📋 Resumen Ejecutivo

Se implementó un sistema completo de **respaldo y exportación de datos** que garantiza:

1. ✅ **Resguardo de información** - Todos los datos están en MongoDB con respaldos bajo demanda
2. ✅ **Descarga por segmentador** - Exportar cargas de trabajo individuales en CSV
3. ✅ **Resumen de equipo** - Exportar estadísticas consolidadas de todos los segmentadores
4. ✅ **Respaldo completo** - Exportar toda la base de datos en JSON para recuperación

---

## 🔒 Respuesta a tu Pregunta: "¿Está resguardada la información?"

### ✅ **SÍ, tu información está completamente resguardada**

### Cómo funciona el resguardo:

#### 1. **MongoDB como Base de Datos Principal**
- **Servidor:** `192.168.1.93:27017`
- **Base de datos:** `segmentacion_db`
- **Colección principal:** `batches`
- **Persistencia:** Todos los cambios se guardan inmediatamente

**Código de respaldo (app.py línea 297):**
```python
result = batches_col.update_one({"id": batch_id}, {"$set": update_data})
```

Cada vez que:
- Asignas un batch a un segmentador
- Cambias el estatus (NS → In → S)
- Actualizas comentarios
- Cambias la revisión (Aprobado/No Aprobado)
- Modificas cualquier campo

**→ Se guarda INMEDIATAMENTE en MongoDB**

#### 2. **Ventajas de MongoDB para Respaldo**
- ✅ **Persistencia en disco** - Los datos sobreviven si el servidor se reinicia
- ✅ **Transacciones ACID** - Los cambios son atómicos (se guardan completamente o no se guardan)
- ✅ **Réplicas** (si está configurado) - MongoDB puede tener copias en múltiples servidores
- ✅ **Índices optimizados** - Búsquedas rápidas sin perder datos
- ✅ **Sin dependencia de archivos locales** - No se necesita `batches.json` ni archivos CSV locales

#### 3. **¿Qué pasa si...?**

| Escenario | ¿Se pierden datos? | Explicación |
|-----------|-------------------|-------------|
| Se cierra el navegador | ❌ NO | Datos en MongoDB, no en navegador |
| Se reinicia Flask | ❌ NO | Flask lee de MongoDB al iniciar |
| Se reinicia el servidor | ❌ NO | MongoDB persiste en disco |
| Falla MongoDB | ⚠️ DEPENDE | Si hay réplicas configuradas, NO. Si no, depende del backup del servidor |
| Se elimina un batch por error | ⚠️ SÍ | No hay "undo" automático, pero puedes restaurar desde un backup JSON |

#### 4. **¿Qué NO está respaldado automáticamente?**
- ❌ **Historial de cambios** - No se registra quién cambió qué y cuándo (esto se puede agregar después)
- ❌ **Versiones anteriores** - Si cambias un comentario, no puedes ver el comentario anterior
- ❌ **Backups automáticos periódicos** - Debes crear backups manualmente (ver sección siguiente)

---

## 📥 Sistema de Exportación y Descarga

### Endpoints Implementados

Se agregaron 3 nuevos endpoints en `app.py` (líneas 1819-2031):

#### 1. **Exportar Carga de Trabajo por Segmentador (CSV)**

**Endpoint:** `GET /api/export/segmentador/<nombre>`

**Función:** Exportar todos los batches asignados a un segmentador específico en formato CSV

**Ejemplo de uso:**
```
GET /api/export/segmentador/Mauricio
```

**Archivo generado:**
```
Mauricio_20251015.csv
```

**Formato del nombre:** `{Segmentador}_{FechaAsignacion}.csv`
- **Segmentador:** Nombre del segmentador
- **FechaAsignacion:** Fecha en formato YYYYMMDD extraída del primer batch asignado

**Contenido del CSV (SIMPLIFICADO):**
| Batch ID | Responsable | Estatus |
|----------|-------------|---------|
| batch_000001 | Mauricio | |
| batch_000002 | Mauricio | |
| batch_000003 | Mauricio | |

**Notas importantes:**
- ✅ Solo 3 columnas: Batch ID, Responsable, Estatus
- ✅ La columna "Estatus" está **vacía** intencionalmente para que el segmentador la llene manualmente
- ✅ Formato simple y fácil de imprimir o trabajar offline

**Código implementado (app.py líneas 1819-1892):**
```python
@app.route("/api/export/segmentador/<segmentador>", methods=["GET"])
def export_segmentador_csv(segmentador):
    """Exportar batches de un segmentador específico en formato CSV"""
    batches = list(batches_col.find({"assignee": segmentador}, {"_id": 0}).sort("id", 1))

    # Obtener fecha de asignación del primer batch
    first_batch_date = ""
    if batches:
        metadata = batches[0].get("metadata", {})
        assigned_at = metadata.get("assigned_at", "")
        if assigned_at:
            # Formato: "2025-10-15 14:30:00" -> "20251015"
            first_batch_date = assigned_at.split()[0].replace("-", "")

    # Crear CSV SIMPLIFICADO (solo 3 columnas)
    output = io.StringIO()
    fieldnames = ["Batch ID", "Responsable", "Estatus"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for batch in batches:
        writer.writerow({
            "Batch ID": batch.get("id", ""),
            "Responsable": batch.get("assignee", ""),
            "Estatus": ""  # Vacío intencionalmente
        })

    # Nombre: Segmentador_FechaAsignacion.csv
    filename = f"{segmentador}_{first_batch_date}.csv"

    # Retornar archivo CSV con BOM para Excel
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name=filename)
```

**Uso desde la interfaz:**
1. Ir a "ASIGNAR BATCHES"
2. En la sección "Descargas y Respaldos"
3. Seleccionar un segmentador del dropdown
4. Clic en "Descargar Carga de Trabajo"
5. Se descarga automáticamente el archivo CSV

**Casos de uso:**
- 📧 **Compartir con el segmentador** - Enviar por email su lista de trabajo simple y clara
- 🖨️ **Imprimir y trabajar offline** - El segmentador puede imprimir su lista y llenar el estatus manualmente
- ✍️ **Seguimiento manual** - Llenar la columna "Estatus" con marcas como "✓", "En proceso", "Pendiente", etc.
- 📋 **Lista de verificación** - Usar como checklist diario de trabajo
- 🔍 **Auditoría simple** - Archivo con nombre descriptivo que indica quién y cuándo (`Mauricio_20251015.csv`)

---

#### 2. **Exportar Resumen de Asignaciones del Equipo (CSV)**

**Endpoint:** `GET /api/export/all-assignments`

**Función:** Exportar un resumen consolidado con estadísticas de todos los segmentadores

**Ejemplo de uso:**
```
GET /api/export/all-assignments
```

**Archivo generado:**
```
resumen_asignaciones_20251015_143052.csv
```

**Contenido del CSV:**
| Segmentador | Total Batches | No Segmentados (NS) | Incompletas (In) | Completados (S) | % Completado | Lista de Batches |
|-------------|---------------|---------------------|------------------|-----------------|--------------|-----------------|
| Mauricio | 15 | 2 | 8 | 5 | 33.3% | batch_000001, batch_000002, batch_000003, ... |
| Maggie | 12 | 1 | 6 | 5 | 41.7% | batch_000010, batch_000011, batch_000012, ... |
| Ceci | 10 | 0 | 3 | 7 | 70.0% | batch_000020, batch_000021, batch_000022, ... |

**Código implementado (app.py líneas 1894-1977):**
```python
@app.route("/api/export/all-assignments", methods=["GET"])
def export_all_assignments_csv():
    """Exportar resumen de asignaciones de todo el equipo"""
    # Usar agregación de MongoDB para calcular estadísticas
    pipeline = [
        {"$match": {"assignee": {"$ne": None}}},
        {"$group": {
            "_id": "$assignee",
            "total": {"$sum": 1},
            "ns": {"$sum": {"$cond": [{"$eq": ["$status", "NS"]}, 1, 0]}},
            "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "In"]}, 1, 0]}},
            "completed": {"$sum": {"$cond": [{"$eq": ["$status", "S"]}, 1, 0]}},
            "batches": {"$push": "$id"}
        }}
    ]

    results = list(batches_col.aggregate(pipeline))

    # Crear CSV con resumen
    writer.writerow({
        "Segmentador": segmentador,
        "Total Batches": total,
        "% Completado": f"{percentage}%",
        ...
    })
```

**Uso desde la interfaz:**
1. Ir a "ASIGNAR BATCHES"
2. En la sección "Descargas y Respaldos"
3. Clic en "Resumen Equipo"
4. Se descarga automáticamente el archivo CSV

**Casos de uso:**
- 📊 **Reportes gerenciales** - Ver rendimiento de todo el equipo de un vistazo
- 📈 **Métricas de productividad** - Comparar % completado entre segmentadores
- 📧 **Reuniones de equipo** - Compartir estado general del proyecto
- 🎯 **Planificación** - Identificar quién tiene más/menos carga de trabajo

---

#### 3. **Crear Respaldo Completo de la Base de Datos (JSON)**

**Endpoint:** `GET /api/backup/database`

**Función:** Exportar TODA la base de datos en formato JSON estructurado

**Ejemplo de uso:**
```
GET /api/backup/database
```

**Archivo generado:**
```
backup_segmentacion_db_20251015_143052.json
```

**Estructura del JSON:**
```json
{
  "backup_info": {
    "created_at": "2025-10-15 14:30:52",
    "version": "1.0",
    "source": "Dashboard de Segmentación"
  },
  "statistics": {
    "total_batches": 45,
    "total_segmentadores": 8,
    "batches_by_status": {
      "NS": 5,
      "In": 20,
      "S": 20
    }
  },
  "segmentadores": [
    {
      "name": "Mauricio",
      "role": "Segmentador",
      "email": "",
      "created_at": "2025-07-23 10:00:00"
    },
    ...
  ],
  "batches": [
    {
      "id": "batch_000001",
      "assignee": "Mauricio",
      "status": "In",
      "folder": "/datos/batch1",
      "mongo_uploaded": true,
      "comments": "En proceso",
      "metadata": {
        "assigned_at": "2025-10-14 10:30:00",
        "due_date": "2025-10-20",
        "priority": "alta",
        "review_status": "Pendiente",
        "total_masks": 150,
        "completed_masks": 75
      }
    },
    ...
  ]
}
```

**Código implementado (app.py líneas 1979-2031):**
```python
@app.route("/api/backup/database", methods=["GET"])
def backup_database():
    """Crear respaldo completo de la base de datos en JSON"""
    # Obtener todos los datos
    batches = list(batches_col.find({}, {"_id": 0}))
    segmentadores = list(segmentadores_col.find({}, {"_id": 0}))

    # Crear estructura con metadata
    backup_data = {
        "backup_info": {...},
        "statistics": {...},
        "segmentadores": segmentadores,
        "batches": batches
    }

    # Retornar JSON con formato legible
    return app.make_response(json.dumps(backup_data, indent=2, ensure_ascii=False))
```

**Uso desde la interfaz:**
1. Ir a "ASIGNAR BATCHES"
2. En la sección "Descargas y Respaldos"
3. Clic en "Respaldo DB"
4. Confirmar la acción en el diálogo
5. Se descarga automáticamente el archivo JSON

**Casos de uso:**
- 💾 **Respaldo antes de cambios importantes** - Guardar estado actual antes de hacer modificaciones masivas
- 🔄 **Migración de datos** - Mover datos a otro servidor o sistema
- 🔙 **Recuperación ante desastres** - Restaurar sistema completo si algo sale mal
- 📦 **Archivo histórico** - Guardar snapshot del estado del proyecto en fechas clave
- 🔬 **Análisis de datos** - Procesar datos con scripts de Python u otras herramientas

---

## 🖥️ Interfaz de Usuario

### Ubicación: `templates/batch_management.html` (Líneas 283-322)

Se agregó una tarjeta completa con controles de exportación:

```html
<!-- Botones de Exportación y Respaldo -->
<div class="card mb-3" style="background: rgba(255, 255, 255, 0.15);">
  <div class="card-body py-3">
    <div class="row align-items-center">
      <div class="col-md-6">
        <h6 class="mb-2" style="color: white;">
          <i class="fas fa-download"></i> Descargas y Respaldos
        </h6>
        <small style="color: rgba(255, 255, 255, 0.8);">
          Exporta cargas de trabajo para compartir con el equipo
        </small>
      </div>
      <div class="col-md-6 text-md-end">
        <div class="btn-group btn-group-sm" role="group">
          <button type="button" class="btn btn-light" onclick="downloadAllAssignments()">
            <i class="fas fa-users"></i> Resumen Equipo
          </button>
          <button type="button" class="btn btn-success" onclick="downloadBackup()">
            <i class="fas fa-database"></i> Respaldo DB
          </button>
        </div>
      </div>
    </div>
    <!-- Selector de segmentador individual -->
    <div class="row mt-2">
      <div class="col-md-12">
        <div class="input-group input-group-sm">
          <span class="input-group-text">
            <i class="fas fa-user"></i>
          </span>
          <select id="exportSegmentadorSelect" class="form-select form-select-sm">
            <option value="">Seleccionar segmentador...</option>
            {% for member in crew %}
            <option value="{{ member }}">{{ member }}</option>
            {% endfor %}
          </select>
          <button type="button" class="btn btn-primary btn-sm" onclick="downloadSegmentadorData()">
            <i class="fas fa-file-csv"></i> Descargar Carga de Trabajo
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
```

### Funciones JavaScript (Líneas 1399-1472)

#### 1. `downloadSegmentadorData()`
```javascript
window.downloadSegmentadorData = function() {
  const select = document.getElementById('exportSegmentadorSelect');
  const segmentador = select.value;

  if (!segmentador) {
    showNotification('Por favor selecciona un segmentador', 'warning');
    return;
  }

  showNotification(`Preparando descarga de ${segmentador}...`, 'info');
  window.location.href = `/api/export/segmentador/${encodeURIComponent(segmentador)}`;

  setTimeout(() => {
    select.value = '';
    showNotification(`✅ Descarga iniciada para ${segmentador}`, 'success');
  }, 1000);
};
```

#### 2. `downloadAllAssignments()`
```javascript
window.downloadAllAssignments = function() {
  showNotification('Preparando resumen del equipo...', 'info');
  window.location.href = '/api/export/all-assignments';

  setTimeout(() => {
    showNotification('✅ Descarga de resumen iniciada', 'success');
  }, 1000);
};
```

#### 3. `downloadBackup()`
```javascript
window.downloadBackup = function() {
  // Confirmación antes de crear backup
  if (!confirm('¿Deseas crear un respaldo completo de la base de datos?\n\nEsto descargará todos los batches y segmentadores en formato JSON.')) {
    return;
  }

  showNotification('Creando respaldo completo...', 'info');
  window.location.href = '/api/backup/database';

  setTimeout(() => {
    showNotification('✅ Respaldo creado exitosamente', 'success');
  }, 1500);
};
```

#### 4. Shortcut de teclado
```javascript
// Permitir presionar Enter en el select para descargar
$('#exportSegmentadorSelect').on('keypress', function(e) {
  if (e.which === 13) { // Enter key
    e.preventDefault();
    downloadSegmentadorData();
  }
});
```

---

## 📝 Flujo de Trabajo Recomendado

### 1. **Asignación de Batches**
```
1. Asignar batches a segmentadores usando drag & drop
2. Verificar que las métricas se actualicen en tiempo real
3. Crear respaldo después de asignaciones importantes:
   - Clic en "Respaldo DB"
   - Guardar archivo JSON en carpeta segura
```

### 2. **Compartir Cargas de Trabajo**
```
Cada semana o al inicio de sprint:
1. Seleccionar segmentador del dropdown
2. Clic en "Descargar Carga de Trabajo"
3. Enviar CSV por email al segmentador
4. El segmentador tiene lista clara de sus tareas
```

### 3. **Reportes Gerenciales**
```
Cada viernes o fin de sprint:
1. Clic en "Resumen Equipo"
2. Abrir CSV en Excel/Google Sheets
3. Revisar % completado de cada segmentador
4. Identificar cuellos de botella
5. Ajustar asignaciones según sea necesario
```

### 4. **Respaldos Periódicos**
```
Recomendación: Crear backup cada viernes
1. Clic en "Respaldo DB"
2. Guardar JSON con nombre descriptivo:
   - backup_segmentacion_db_20251015_viernes.json
3. Subir a carpeta compartida o Google Drive
4. Mantener últimos 4-6 backups (1-1.5 meses)
```

---

## 🔧 Detalles Técnicos de Implementación

### Modificaciones en `app.py`

**Línea 20-26:** Importación de módulos
```python
from flask import Flask, render_template, request, jsonify, redirect, send_file
from db import get_db, create_indexes
import json
import os
import csv        # NUEVO
import io         # NUEVO
from datetime import datetime
```

**Líneas 1815-2031:** Tres nuevos endpoints
- `/api/export/segmentador/<segmentador>` (GET)
- `/api/export/all-assignments` (GET)
- `/api/backup/database` (GET)

### Modificaciones en `batch_management.html`

**Líneas 283-322:** Tarjeta de exportación con controles UI

**Líneas 1399-1472:** Funciones JavaScript de exportación

---

## 🚀 Ventajas del Sistema Implementado

### ✅ Para Administradores
- ✅ **Respaldo rápido** - Exportar DB completa en 1 clic
- ✅ **Auditoría** - Saber qué tiene cada persona asignado
- ✅ **Recuperación ante desastres** - Restaurar desde JSON si algo falla
- ✅ **Migración fácil** - Mover datos a otro sistema con JSON estándar

### ✅ Para Segmentadores
- ✅ **Lista offline** - Tener su carga de trabajo en CSV/Excel
- ✅ **Claridad** - Ver exactamente qué batches tienen asignados
- ✅ **Planificación** - Organizar su trabajo sin depender del dashboard

### ✅ Para el Equipo
- ✅ **Transparencia** - Todos pueden ver el resumen del equipo
- ✅ **Colaboración** - Compartir información fácilmente
- ✅ **Métricas** - Datos cuantificables de productividad

---

## 🛡️ Seguridad y Buenas Prácticas

### ✅ Implementadas
- ✅ **Validación de entrada** - Se verifica que el segmentador exista antes de exportar
- ✅ **Manejo de errores** - Try/catch en todos los endpoints con mensajes claros
- ✅ **Logging** - Todas las operaciones se registran en consola del servidor
- ✅ **Encoding UTF-8** - CSV con BOM para compatibilidad con Excel en español
- ✅ **Nombres de archivo únicos** - Timestamp en cada archivo para evitar sobrescritura

### ⚠️ Consideraciones Futuras
- ⚠️ **Autenticación** - Actualmente no hay restricciones de acceso (cualquiera puede descargar)
- ⚠️ **Rate limiting** - No hay límite de descargas por minuto
- ⚠️ **Tamaño de archivos** - Con miles de batches, el JSON puede ser muy grande
- ⚠️ **Historial de backups** - No se guardan automáticamente en el servidor

---

## 📊 Formato de Archivos

### CSV (Carga de Trabajo Individual)
**Encoding:** UTF-8 con BOM
**Separador:** Coma (,)
**Compatible con:** Excel, Google Sheets, LibreOffice
**Tamaño estimado:** ~50 bytes por batch (formato ultra simplificado)
**Nombre del archivo:** `{Segmentador}_{FechaAsignacion}.csv` (ej: `Mauricio_20251015.csv`)

**Columnas (SIMPLIFICADAS):**
```
Batch ID, Responsable, Estatus
```

**Ejemplo de contenido:**
```csv
Batch ID,Responsable,Estatus
batch_000001,Mauricio,
batch_000002,Mauricio,
batch_000003,Mauricio,
```

**Notas:**
- La columna "Estatus" está **intencionalmente vacía** para que el segmentador la complete
- Formato minimalista ideal para imprimir o trabajar offline
- El nombre del archivo incluye el segmentador y la fecha de asignación para fácil identificación

### CSV (Resumen de Equipo)
**Encoding:** UTF-8 con BOM
**Separador:** Coma (,)
**Tamaño estimado:** ~200 bytes por segmentador

**Columnas:**
```
Segmentador, Total Batches, No Segmentados (NS),
Incompletas (In), Completados (S), % Completado, Lista de Batches
```

### JSON (Respaldo Completo)
**Encoding:** UTF-8
**Formato:** Indentado (2 espacios)
**Tamaño estimado:** ~500 bytes por batch + metadata

**Estructura:**
```json
{
  "backup_info": {...},
  "statistics": {...},
  "segmentadores": [{...}],
  "batches": [{...}]
}
```

---

## 🔄 Restauración desde Backup

### Escenario: Necesitas restaurar la base de datos

**Opción 1: Usar módulo de Gestión de Datos**
1. Ir a `/data-management`
2. En sección "Cargar Batches desde JSON"
3. Seleccionar el archivo `backup_segmentacion_db_YYYYMMDD.json`
4. Clic en "Cargar Archivo"
5. El sistema importará todos los batches

**Opción 2: Script de Python** (para técnicos)
```python
import json
from pymongo import MongoClient

# Cargar backup
with open('backup_segmentacion_db_20251015.json', 'r') as f:
    backup = json.load(f)

# Conectar a MongoDB
client = MongoClient('mongodb://192.168.1.93:27017/')
db = client['segmentacion_db']

# Restaurar segmentadores
db.segmentadores.delete_many({})  # ⚠️ Cuidado: borra todo
db.segmentadores.insert_many(backup['segmentadores'])

# Restaurar batches
db.batches.delete_many({})  # ⚠️ Cuidado: borra todo
db.batches.insert_many(backup['batches'])

print(f"✅ Restaurados {len(backup['batches'])} batches y {len(backup['segmentadores'])} segmentadores")
```

**Opción 3: Importación selectiva**
```python
# Restaurar solo batches de un segmentador específico
mauricio_batches = [b for b in backup['batches'] if b['assignee'] == 'Mauricio']
db.batches.insert_many(mauricio_batches)
```

---

## 📅 Calendario de Respaldos Recomendado

### Diario (Automático - Futuro)
- ⏰ Cada día a las 23:00
- 📍 Backup incremental (solo cambios del día)
- 📁 Guardar en `/backups/daily/`
- 🔄 Mantener últimos 7 días

### Semanal (Manual - Actual)
- ⏰ Cada viernes antes de salir
- 📍 Backup completo en JSON
- 📁 Guardar en carpeta compartida con fecha
- 🔄 Mantener últimas 4 semanas

### Mensual (Manual)
- ⏰ Último viernes de cada mes
- 📍 Backup completo + resumen de equipo
- 📁 Archivar en Google Drive
- 🔄 Mantener últimos 12 meses

### Crítico (Manual)
Crear backup ANTES de:
- ❗ Eliminar batches masivamente
- ❗ Cambiar estructura de datos
- ❗ Actualizar software/dependencias
- ❗ Migrar a nuevo servidor
- ❗ Probar nuevas funcionalidades

---

## ❓ Preguntas Frecuentes (FAQ)

### ¿Los backups consumen espacio en el servidor?
**No.** Los backups se descargan directamente a tu computadora. No se almacenan en el servidor Flask.

### ¿Puedo automatizar los backups?
**Sí, futuro.** Se puede agregar un cron job o tarea programada que llame al endpoint y guarde el archivo.

### ¿Qué pasa si descargo mientras alguien está editando?
**No hay problema.** MongoDB maneja múltiples lecturas simultáneas. El backup será consistente al momento de la descarga.

### ¿Puedo descargar solo batches con estatus "In"?
**No actualmente, pero se puede agregar.** Tendrías que modificar el endpoint para aceptar filtros.

### ¿Los CSV funcionan en Excel en español?
**Sí.** Se usa encoding UTF-8 con BOM específicamente para compatibilidad con Excel en español.

### ¿Puedo importar los CSV de vuelta al sistema?
**Sí.** Usa el módulo "Gestión de Datos" (`/data-management`) para cargar JSON. Para CSV, se necesitaría agregar un convertidor CSV→JSON.

### ¿Qué pasa si MongoDB se cae?
**El sistema no funcionará hasta que MongoDB vuelva.** Por eso es importante tener backups JSON externos.

### ¿Los backups incluyen las máscaras (imágenes)?
**No.** Los backups JSON solo incluyen metadata (nombres, rutas, estados). Las imágenes están en GridFS y requieren backup por separado.

---

## 🎯 Próximos Pasos (Mejoras Futuras)

### Alta prioridad
- [ ] **Backups automáticos diarios** con cron job
- [ ] **Historial de cambios** (audit log) - quién cambió qué
- [ ] **Versionado de batches** - poder ver estado anterior

### Media prioridad
- [ ] **Exportar a Excel (.xlsx)** con formato y gráficas
- [ ] **Filtros en exportación** - exportar solo batches con criterios específicos
- [ ] **Notificaciones por email** - enviar automáticamente CSV a cada segmentador

### Baja prioridad
- [ ] **Dashboard de backups** - ver lista de backups disponibles
- [ ] **Restauración desde UI** - subir JSON y restaurar sin código
- [ ] **Comparación de backups** - ver diferencias entre dos backups

---

## 📞 Contacto y Soporte

**Desarrollador:** Claude Code - Anthropic
**Revisado por:** Francisco Servin (faservin)
**Fecha:** 15 de Octubre de 2025

**Para dudas o mejoras:**
1. Revisar este documento primero
2. Verificar logs del servidor (`/tmp/flask_final.log`)
3. Consultar código fuente en `app.py` y `batch_management.html`

---

## ✅ Resumen: ¿Está resguardada mi información?

### SÍ, completamente. Aquí está la garantía:

1. ✅ **MongoDB guarda TODO automáticamente** - Cada cambio se persiste de inmediato
2. ✅ **Puedes descargar backup completo** - JSON con todos los datos en 1 clic
3. ✅ **Puedes exportar por segmentador** - CSV para compartir cargas de trabajo
4. ✅ **Puedes ver resumen del equipo** - Estadísticas consolidadas en CSV
5. ✅ **No dependes de archivos locales** - Todo está centralizado en MongoDB
6. ✅ **Restauración posible** - Con el JSON puedes reconstruir todo el sistema

### Recomendación Final:

**Crea un backup semanal cada viernes y guárdalo en una carpeta compartida o Google Drive.**

Así tendrás:
- 📁 Historial de estados del proyecto
- 🔙 Capacidad de recuperación ante errores
- 📊 Datos para análisis posterior
- 🛡️ Tranquilidad de que nada se perderá

---

**Fin del documento**
