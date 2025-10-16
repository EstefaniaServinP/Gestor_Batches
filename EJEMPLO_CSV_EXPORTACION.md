# Ejemplo de CSV Exportado

## 📄 Formato del Archivo

### Nombre del archivo
```
{Segmentador}_{FechaAsignacion}.csv
```

**Ejemplos reales:**
- `Mauricio_20251015.csv` - Batches asignados a Mauricio el 15 de octubre de 2025
- `Maggie_20251014.csv` - Batches asignados a Maggie el 14 de octubre de 2025
- `Ceci_20251016.csv` - Batches asignados a Ceci el 16 de octubre de 2025

---

## 📊 Contenido del CSV

### Formato Simplificado (3 columnas)

```csv
Batch ID,Responsable,Estatus
batch_000001,Mauricio,
batch_000002,Mauricio,
batch_000003,Mauricio,
batch_000004,Mauricio,
batch_000005,Mauricio,
```

### Cómo se ve en Excel

| Batch ID | Responsable | Estatus |
|----------|-------------|---------|
| batch_000001 | Mauricio | |
| batch_000002 | Mauricio | |
| batch_000003 | Mauricio | |
| batch_000004 | Mauricio | |
| batch_000005 | Mauricio | |

---

## ✍️ Uso del CSV

### Opción 1: Trabajo Digital
El segmentador abre el archivo en Excel y va llenando la columna "Estatus":

| Batch ID | Responsable | Estatus |
|----------|-------------|---------|
| batch_000001 | Mauricio | ✓ Completado |
| batch_000002 | Mauricio | En proceso |
| batch_000003 | Mauricio | Pendiente |
| batch_000004 | Mauricio | ✓ Completado |
| batch_000005 | Mauricio | Bloqueado |

### Opción 2: Trabajo Impreso (Checklist)
El segmentador puede imprimir el CSV y usarlo como lista física:

```
☐ batch_000001 - Mauricio
☑ batch_000002 - Mauricio  [Completado]
☐ batch_000003 - Mauricio
☑ batch_000004 - Mauricio  [Completado]
☐ batch_000005 - Mauricio
```

### Opción 3: Estados Personalizados
Cada segmentador puede usar sus propios marcadores:

| Batch ID | Responsable | Estatus |
|----------|-------------|---------|
| batch_000001 | Mauricio | 🟢 OK |
| batch_000002 | Mauricio | 🟡 50% |
| batch_000003 | Mauricio | 🔴 Bloqueado |
| batch_000004 | Mauricio | 🟢 OK |
| batch_000005 | Mauricio | ⚪ Pendiente |

---

## 📥 Proceso Completo

### Paso 1: Administrador descarga el CSV
1. Ir a `/assign` (ASIGNAR BATCHES)
2. Seleccionar "Mauricio" del dropdown
3. Clic en "Descargar Carga de Trabajo"
4. Se descarga `Mauricio_20251015.csv`

### Paso 2: Compartir con el segmentador
```
Para: mauricio@empresa.com
Asunto: Tu carga de trabajo - 15 de Octubre

Hola Mauricio,

Adjunto encontrarás tu lista de batches asignados para esta semana.

Por favor revisa y llena la columna "Estatus" para llevar control de tu progreso.

Cualquier duda, estamos en contacto.

Saludos!
```

### Paso 3: Segmentador trabaja con el CSV
- Abre `Mauricio_20251015.csv` en Excel
- Va marcando cada batch según avanza
- Guarda el archivo actualizado
- (Opcional) Envía el archivo actualizado de vuelta al administrador

---

## 🎯 Ventajas de este Formato

### ✅ Simple
- Solo 3 columnas
- Fácil de entender
- No abruma con información innecesaria

### ✅ Flexible
- El segmentador puede usar cualquier notación en "Estatus"
- Se puede imprimir y trabajar en papel
- Compatible con Excel, Google Sheets, LibreOffice

### ✅ Identificable
- El nombre del archivo dice quién y cuándo
- No hay confusión entre diferentes segmentadores
- Fácil de archivar y organizar

### ✅ Offline
- No requiere acceso al dashboard
- Puede trabajarse sin internet
- Se puede compartir por email, WhatsApp, etc.

---

## 📝 Ejemplo Real de Uso Diario

### Lunes - Recepción
```
Mauricio recibe: Mauricio_20251015.csv
Contenido: 12 batches asignados
Estado inicial: Columna "Estatus" vacía
```

### Durante la semana - Trabajo
**Martes:**
```csv
Batch ID,Responsable,Estatus
batch_000001,Mauricio,✓ OK
batch_000002,Mauricio,En proceso
batch_000003,Mauricio,
...
```

**Miércoles:**
```csv
Batch ID,Responsable,Estatus
batch_000001,Mauricio,✓ OK
batch_000002,Mauricio,✓ OK
batch_000003,Mauricio,50%
batch_000004,Mauricio,Pendiente
...
```

### Viernes - Reporte
```
Mauricio envía de vuelta: Mauricio_20251015_COMPLETO.csv
Resultado: 10 de 12 batches completados
Pendientes: 2 batches para la siguiente semana
```

---

## 🔄 Integración con el Dashboard

**Importante:** Este CSV es solo para referencia offline del segmentador.

Los cambios de estatus **deben actualizarse en el dashboard** para que se reflejen en el sistema principal.

**Flujo recomendado:**
1. Segmentador recibe CSV y trabaja offline
2. Al final del día o semana, entra al dashboard
3. Actualiza los estados en el sistema (NS → In → S)
4. El dashboard es la fuente de verdad

**El CSV es complementario, no reemplaza al dashboard.**

---

## 💡 Casos de Uso Específicos

### Caso 1: Segmentador sin acceso constante a internet
```
1. Descarga su CSV el lunes
2. Trabaja toda la semana offline
3. El viernes sincroniza sus cambios en el dashboard
```

### Caso 2: Presentación en reunión
```
1. Administrador descarga CSV de cada segmentador
2. Abre todos en Excel para comparar
3. Presenta avances en reunión de equipo
```

### Caso 3: Archivo de evidencia
```
1. Al terminar un proyecto, descargar todos los CSVs
2. Guardar como evidencia de asignaciones
3. Archivar por fecha para futuras auditorías
```

### Caso 4: Trabajo remoto
```
1. Enviar CSV por WhatsApp/Telegram
2. Segmentador trabaja desde casa
3. Actualiza el CSV y lo comparte por mensaje
4. Administrador actualiza el dashboard con esa info
```

---

## ✅ Resumen

**Formato:** 3 columnas (Batch ID, Responsable, Estatus)
**Nombre:** `Segmentador_FechaAsignacion.csv`
**Propósito:** Lista simple para trabajo offline y seguimiento manual
**Ventaja principal:** Flexibilidad total para cada segmentador

**El segmentador puede usar el estatus como quiera:**
- ✓ / ✗
- Completado / Pendiente / En proceso
- 🟢 🟡 🔴
- Números (1-10)
- Porcentajes (0%, 50%, 100%)
- Cualquier sistema que funcione para él/ella

---

**Documento de ejemplo**
Proyecto: Dashboard de Segmentación
Fecha: 15 de Octubre de 2025
