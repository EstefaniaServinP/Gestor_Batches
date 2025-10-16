# Changelog - Implementación de Filtros en Dashboard General

## Fecha: 15 de Octubre de 2025

## Resumen
Se implementaron filtros individuales para todas las columnas del Dashboard General, permitiendo búsquedas y filtrados específicos en tiempo real.

---

## 1. Cambios Realizados en `/templates/dashboard.html`

### 1.1 Estructura HTML - Fila de Filtros

**Ubicación:** Líneas 368-405

Se agregó una segunda fila `<tr class="filter-row">` dentro del `<thead>` de la tabla `#batchesTable` con los siguientes elementos de filtro:

| Columna | Tipo de Filtro | Valores |
|---------|----------------|---------|
| **Batch ID** | Input de texto | Búsqueda libre |
| **Responsable** | Select dropdown | Lista de segmentadores del equipo |
| **Cargado a Mongo** | Select dropdown | Sí / No / Todos |
| **Estatus Segmentación** | Select dropdown | NS - No Segmentado / In - Incompleta / S - Segmentado / Todos |
| **Fecha Asignación** | Input de texto | Búsqueda libre (formato fecha) |
| **Revisión** | Select dropdown | Pendiente / Aprobado / No Aprobado / Todos |
| **Comentarios** | Input de texto | Búsqueda libre |
| **Acciones** | - | Sin filtro |

**Código agregado:**
```html
<!-- Fila de filtros -->
<tr class="filter-row">
  <th><input type="text" class="form-control form-control-sm filter-input" placeholder="Filtrar Batch ID..." data-column="0"></th>
  <th>
    <select class="form-select form-select-sm filter-select" data-column="1">
      <option value="">Todos</option>
      {% for member in crew %}
      <option value="{{ member }}">{{ member }}</option>
      {% endfor %}
    </select>
  </th>
  <th>
    <select class="form-select form-select-sm filter-select" data-column="2">
      <option value="">Todos</option>
      <option value="Sí">Sí</option>
      <option value="No">No</option>
    </select>
  </th>
  <th>
    <select class="form-select form-select-sm filter-select" data-column="3">
      <option value="">Todos</option>
      <option value="NS - No Segmentado">NS - No Segmentado</option>
      <option value="In - Incompleta">In - Incompleta</option>
      <option value="S - Segmentado">S - Segmentado</option>
    </select>
  </th>
  <th><input type="text" class="form-control form-control-sm filter-input" placeholder="Filtrar fecha..." data-column="4"></th>
  <th>
    <select class="form-select form-select-sm filter-select" data-column="5">
      <option value="">Todos</option>
      <option value="Pendiente">Pendiente</option>
      <option value="Aprobado">Aprobado</option>
      <option value="No Aprobado">No Aprobado</option>
    </select>
  </th>
  <th><input type="text" class="form-control form-control-sm filter-input" placeholder="Filtrar comentarios..." data-column="6"></th>
  <th></th>
</tr>
```

**Características:**
- Cada input/select tiene un atributo `data-column` que identifica el índice de la columna a filtrar (0-7)
- Inputs de texto tienen placeholders descriptivos
- Selects tienen opción "Todos" para limpiar el filtro
- Clases CSS: `filter-input` para inputs de texto, `filter-select` para dropdowns

---

### 1.2 Estilos CSS

**Ubicación:** Líneas 343-366

Se agregaron estilos CSS personalizados para la fila de filtros:

```css
/* Estilos para la fila de filtros */
.filter-row th {
  background: linear-gradient(135deg, #F3E8FF 0%, #FCE7F3 100%);
  padding: 0.5rem;
  vertical-align: middle;
}

.filter-input, .filter-select {
  font-size: 0.85rem;
  height: 32px;
  border-radius: 6px;
  border: 1px solid rgba(107, 70, 193, 0.3);
  background: white;
}

.filter-input:focus, .filter-select:focus {
  border-color: #B794F6;
  box-shadow: 0 0 0 0.2rem rgba(183, 148, 246, 0.25);
}

.filter-input::placeholder {
  color: rgba(107, 70, 193, 0.5);
  font-size: 0.8rem;
}
```

**Características:**
- **Fondo de fila:** Gradiente violeta claro (`#F3E8FF` → `#FCE7F3`) que distingue visualmente la fila de filtros
- **Inputs/Selects:**
  - Altura fija de 32px
  - Bordes redondeados (6px)
  - Border color morado suave
- **Estados focus:**
  - Border color morado más intenso (`#B794F6`)
  - Box-shadow morado translúcido
- **Placeholders:** Color morado suave semi-transparente

---

### 1.3 Configuración de DataTables

**Ubicación:** Líneas 716-727

Se actualizó la inicialización de DataTables para soportar la fila de filtros:

```javascript
batchesTable = $('#batchesTable').DataTable({
  responsive: true,
  pageLength: 25,
  language: {
    url: 'https://cdn.datatables.net/plug-ins/1.13.4/i18n/es-ES.json'
  },
  columnDefs: [
    { orderable: false, targets: -1 }
  ],
  orderCellsTop: true,    // NUEVO: Permite ordenar por la primera fila de encabezados
  fixedHeader: true       // NUEVO: Fija el encabezado al hacer scroll
});

// Inicializar filtros de columnas
initializeColumnFilters();  // NUEVO: Llamada a función de inicialización de filtros
```

**Propiedades agregadas:**
- `orderCellsTop: true` - Hace que DataTables use la primera fila de `<thead>` para ordenar, ignorando la fila de filtros
- `fixedHeader: true` - Mantiene visible el encabezado (incluyendo filtros) al hacer scroll vertical

---

### 1.4 Función JavaScript de Inicialización de Filtros

**Ubicación:** Líneas 772-795

Se creó la función `initializeColumnFilters()` que vincula los eventos de los filtros con la API de búsqueda de DataTables:

```javascript
// Función para inicializar los filtros de columnas
function initializeColumnFilters() {
  console.log('🔧 Inicializando filtros de columnas...');

  // Filtros de texto (Batch ID, Fecha, Comentarios)
  $('.filter-input').on('keyup change', function() {
    const columnIndex = $(this).data('column');
    const searchValue = $(this).val();

    console.log(`🔍 Filtrando columna ${columnIndex} con valor: "${searchValue}"`);
    batchesTable.column(columnIndex).search(searchValue).draw();
  });

  // Filtros de select (Responsable, Cargado a Mongo, Estatus, Revisión)
  $('.filter-select').on('change', function() {
    const columnIndex = $(this).data('column');
    const searchValue = $(this).val();

    console.log(`🔍 Filtrando columna ${columnIndex} con valor: "${searchValue}"`);
    batchesTable.column(columnIndex).search(searchValue).draw();
  });

  console.log('✅ Filtros de columnas inicializados');
}
```

**Funcionamiento:**

1. **Filtros de texto** (`.filter-input`):
   - Eventos: `keyup` (tiempo real mientras se escribe) y `change` (al perder foco)
   - Acción: Busca el valor en la columna correspondiente y redibuja la tabla

2. **Filtros de select** (`.filter-select`):
   - Evento: `change` (al seleccionar una opción)
   - Acción: Filtra por el valor seleccionado, o muestra todos si se selecciona opción vacía

3. **API utilizada:**
   - `batchesTable.column(columnIndex)` - Selecciona la columna por índice
   - `.search(searchValue)` - Aplica el filtro de búsqueda
   - `.draw()` - Redibuja la tabla con los resultados filtrados

4. **Logging:**
   - Muestra en consola cada operación de filtrado para debugging
   - Formato: `🔍 Filtrando columna [índice] con valor: "[valor]"`

---

## 2. Comportamiento de los Filtros

### 2.1 Filtrado en Tiempo Real
- Los **inputs de texto** filtran mientras el usuario escribe
- Los **dropdowns** filtran inmediatamente al cambiar la selección
- Los filtros son **acumulativos**: se pueden aplicar múltiples filtros simultáneamente

### 2.2 Búsqueda Inteligente de DataTables
DataTables realiza búsquedas "inteligentes" por defecto:
- **Case-insensitive** (no distingue mayúsculas/minúsculas)
- **Búsqueda parcial**: busca coincidencias en cualquier parte del texto
- **Ejemplo:** Filtrar "batch" en Batch ID encontrará "batch_000001", "batch_000002", etc.

### 2.3 Reseteo de Filtros
Para limpiar un filtro:
- **Inputs de texto:** Borrar el contenido del campo
- **Dropdowns:** Seleccionar la opción "Todos"

---

## 3. Compatibilidad y Notas Técnicas

### 3.1 Dependencias
- **DataTables 1.13.4** con Bootstrap 5
- **jQuery** (incluido en el proyecto)
- **Font Awesome** para iconos (ya presente)

### 3.2 Compatibilidad con Funcionalidad Existente
Los filtros **NO interfieren** con:
- Ordenamiento de columnas (click en encabezados)
- Paginación
- Filtro por responsable desde URL (`?assignee=nombre`)
- Edición inline de celdas
- Acciones de guardar/ver/eliminar batches

### 3.3 Responsive Design
- La tabla mantiene su comportamiento responsive de DataTables
- En pantallas pequeñas, los filtros se adaptan automáticamente
- La propiedad `fixedHeader: true` asegura que los filtros permanezcan visibles al hacer scroll

---

## 4. Pruebas Sugeridas

Para verificar el correcto funcionamiento:

1. **Filtro de Batch ID:**
   - Escribir "batch_0000" → Debe mostrar todos los batches que contengan ese texto
   - Escribir "1F" → Debe mostrar solo batches con "1F" en el ID

2. **Filtro de Responsable:**
   - Seleccionar un segmentador → Mostrar solo sus batches asignados
   - Seleccionar "Todos" → Volver a mostrar todos los batches

3. **Filtro de Cargado a Mongo:**
   - Seleccionar "Sí" → Solo batches con ✅
   - Seleccionar "No" → Solo batches con ❌

4. **Filtro de Estatus de Segmentación:**
   - Seleccionar "NS - No Segmentado" → Solo batches con status NS
   - Combinar con filtro de Responsable → Ver batches NS de un segmentador específico

5. **Filtro de Revisión:**
   - Seleccionar "Aprobado" → Solo batches con ✅ Aprobado
   - Seleccionar "No Aprobado" → Solo batches con ❌ No Aprobado
   - Seleccionar "Pendiente" → Solo batches sin revisión asignada

6. **Filtros Múltiples:**
   - Combinar Responsable + Estatus + Revisión
   - Verificar que los resultados cumplen TODOS los criterios simultáneamente

---

## 5. Mantenimiento Futuro

### 5.1 Agregar Nuevas Columnas con Filtros
Para agregar filtros a nuevas columnas:

1. Agregar `<th>` en la fila de filtros con input/select correspondiente
2. Asignar `data-column="N"` con el índice correcto
3. Usar clase `filter-input` o `filter-select` según el tipo
4. La función `initializeColumnFilters()` los detectará automáticamente

### 5.2 Modificar Opciones de Dropdowns
Los valores de los dropdowns están hardcoded en el HTML. Para modificarlos:
- Editar las opciones `<option>` en `templates/dashboard.html` (líneas 372-401)
- Los valores deben coincidir EXACTAMENTE con el texto mostrado en las celdas de la tabla

### 5.3 Personalizar Comportamiento de Búsqueda
Para cambiar el comportamiento de búsqueda (ej: búsqueda exacta en lugar de parcial):

```javascript
// Búsqueda exacta (regex)
batchesTable.column(columnIndex).search('^' + searchValue + '$', true, false).draw();

// Búsqueda case-sensitive
batchesTable.column(columnIndex).search(searchValue, false, true).draw();
```

---

## 6. Referencias

- **DataTables Column Searching:** https://datatables.net/examples/api/multi_filter_select.html
- **DataTables API - column().search():** https://datatables.net/reference/api/column().search()
- **DataTables Fixed Header:** https://datatables.net/extensions/fixedheader/

---

## 7. Problemas Conocidos y Soluciones

### 7.1 Los filtros no funcionan después de recargar datos
**Causa:** Los filtros se inicializan solo una vez en `$(document).ready()`

**Solución:** Si se recargan los datos de la tabla dinámicamente (ej: con AJAX), los filtros seguirán funcionando porque usan la API de DataTables que se mantiene activa.

### 7.2 Los valores de los dropdowns no coinciden con los datos
**Causa:** Los valores hardcoded en las opciones del select no coinciden exactamente con el texto en las celdas

**Solución:** Verificar que los valores en las opciones coincidan EXACTAMENTE con el texto renderizado en las celdas. Ejemplo:
- ❌ Incorrecto: `<option value="Si">` (sin tilde)
- ✅ Correcto: `<option value="Sí">` (con tilde)

### 7.3 El filtro de fecha no encuentra resultados
**Causa:** El formato de fecha en el input no coincide con el formato mostrado en la tabla

**Solución:** DataTables busca coincidencias parciales, así que:
- Para fecha "2025-10-15 14:30", se puede buscar:
  - "2025" → Encuentra todos de ese año
  - "10-15" → Encuentra todos de ese día
  - "14:30" → Encuentra por hora específica

---

## Autor
Claude Code - Anthropic

## Revisado por
Francisco Servin (faservin)

## Estado
✅ Completado y funcionando
