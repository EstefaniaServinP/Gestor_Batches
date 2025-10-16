# Buscador de Batches No Asignados

## 🔍 ¿Qué es?

Un **buscador en tiempo real** en la zona de "Batches No Asignados" para encontrar rápidamente los batches que necesitas asignar.

---

## 📍 Ubicación

```
Página: /assign (ASIGNAR BATCHES)
        ↓
Card: "Batches No Asignados"
        ↓
Header: Input de búsqueda con ícono de lupa
```

---

## 🎨 Interfaz

### Vista del Buscador

```
┌─────────────────────────────────────────────────────────┐
│ 📦 Batches No Asignados                                 │
│ 5 batches disponibles                                   │
│                                                          │
│ [🔍] [Buscar batch por ID...]              [✕]         │
└─────────────────────────────────────────────────────────┘
```

### Componentes

1. **Contador:** Muestra cuántos batches hay disponibles
2. **Input de búsqueda:** Campo de texto para escribir
3. **Ícono de lupa:** Indicador visual
4. **Botón X:** Limpiar búsqueda rápidamente

---

## 🚀 Cómo Usar

### Opción 1: Búsqueda Simple
```
1. Escribe en el input: "batch_000001"
2. Automáticamente filtra mientras escribes
3. Solo muestra batches que coincidan
```

### Opción 2: Búsqueda Parcial
```
1. Escribe: "0001"
2. Encuentra todos los batches que contengan "0001"
   Ejemplo:
   - batch_000001F ✅
   - batch_000012F ✅
   - batch_000100F ✅
```

### Opción 3: Búsqueda Case-Insensitive
```
1. Escribe: "BATCH" o "batch" o "BaTcH"
2. Todas funcionan igual
3. No distingue mayúsculas/minúsculas
```

### Opción 4: Limpiar Búsqueda
```
1. Clic en el botón [✕]
2. Vuelven a aparecer todos los batches
```

---

## 💡 Ejemplos de Uso

### Ejemplo 1: Buscar batch específico
```
Tienes: 100 batches en la lista
Buscas: "batch_000050F"
Resultado: Solo 1 batch aparece
```

### Ejemplo 2: Buscar por patrón
```
Tienes: batch_000001F, batch_000002F, ..., batch_000010F
Buscas: "00000"
Resultado: 9 batches (batch_000001F a batch_000009F)
```

### Ejemplo 3: Buscar por sufijo
```
Tienes: batch_000001F, batch_000002F, batch_000003G
Buscas: "F"
Resultado: Solo los que terminan en F
```

---

## 🎯 Características

### ✅ Búsqueda en Tiempo Real
- Filtra mientras escribes
- No necesitas presionar Enter (aunque también funciona)
- Respuesta instantánea

### ✅ Búsqueda Inteligente
- **Case-insensitive:** No importa mayúsculas/minúsculas
- **Búsqueda parcial:** Encuentra coincidencias en cualquier parte del ID
- **Sin espacios:** Ignora espacios extra

### ✅ Visual Claro
- **Contador actualizado:** Muestra cuántos resultados hay
- **Mensaje de "No resultados":** Si no encuentra nada
- **Mantiene arrastre:** Los batches filtrados siguen siendo arrastrables

---

## 🔧 Implementación Técnica

### HTML (líneas 375-420)

**Estructura:**
```html
<div class="card-header">
  <div class="row">
    <div class="col-md-6">
      <h5>Batches No Asignados</h5>
      <small><span id="unassignedCount">0</span> batches disponibles</small>
    </div>
    <div class="col-md-6">
      <!-- BUSCADOR -->
      <div class="input-group">
        <span class="input-group-text"><i class="fas fa-search"></i></span>
        <input id="searchUnassignedBatches" placeholder="Buscar batch por ID...">
        <button onclick="clearSearchUnassigned()"><i class="fas fa-times"></i></button>
      </div>
    </div>
  </div>
</div>

<!-- Mensaje cuando no hay resultados -->
<div id="noResultsMessage" style="display: none;">
  <i class="fas fa-search fa-2x"></i>
  <p>No se encontraron batches con ese criterio</p>
</div>
```

### JavaScript (líneas 744-1722)

**Variables Globales:**
```javascript
let allUnassignedBatches = []; // Almacena todos los batches para búsqueda
```

**Función de Búsqueda:**
```javascript
function searchUnassignedBatches() {
  const searchTerm = $('#searchUnassignedBatches').val().trim().toLowerCase();

  if (!searchTerm) {
    // Mostrar todos si no hay término
    renderUnassignedBatches(allUnassignedBatches);
    return;
  }

  // Filtrar batches que coincidan
  const filteredBatches = allUnassignedBatches.filter(batch =>
    batch.id.toLowerCase().includes(searchTerm)
  );

  // Renderizar resultados
  renderUnassignedBatches(filteredBatches);
}
```

**Función de Limpiar:**
```javascript
window.clearSearchUnassigned = function() {
  $('#searchUnassignedBatches').val('');
  renderUnassignedBatches(allUnassignedBatches);
};
```

**Eventos:**
```javascript
$(document).ready(function() {
  // Búsqueda en tiempo real (mientras escribes)
  $('#searchUnassignedBatches').on('input', searchUnassignedBatches);

  // También funciona con Enter
  $('#searchUnassignedBatches').on('keypress', function(e) {
    if (e.which === 13) {
      e.preventDefault();
      searchUnassignedBatches();
    }
  });
});
```

**Actualización de Contador:**
```javascript
function renderUnassignedBatches(unassignedBatches) {
  // Actualizar contador
  $('#unassignedCount').text(unassignedBatches.length);

  // Renderizar batches filtrados
  // ...
}
```

---

## 📊 Flujo de Búsqueda

```
Usuario escribe "batch_0001"
        ↓
Evento 'input' detectado
        ↓
searchUnassignedBatches()
        ↓
searchTerm = "batch_0001".toLowerCase()
        ↓
Filtrar allUnassignedBatches
        ↓
batch.id.includes("batch_0001")
        ↓
filteredBatches = [batch_000001F, batch_000010F, ...]
        ↓
renderUnassignedBatches(filteredBatches)
        ↓
Actualiza contador: "2 batches disponibles"
        ↓
Muestra solo batches filtrados
```

---

## 🎬 Ejemplo Paso a Paso

### Paso 1: Estado Inicial
```
Input: [vacío]
Contador: "50 batches disponibles"
Visible: Todos los 50 batches
```

### Paso 2: Empiezas a escribir
```
Input: "b"
Contador: "50 batches disponibles" (todos empiezan con "batch")
Visible: Todos los 50 batches
```

### Paso 3: Sigues escribiendo
```
Input: "batch_0000"
Contador: "9 batches disponibles"
Visible: batch_000001F, batch_000002F, ..., batch_000009F
```

### Paso 4: Escribes número específico
```
Input: "batch_000005"
Contador: "1 batch disponible"
Visible: solo batch_000005F
```

### Paso 5: Limpias búsqueda
```
Clic en [✕]
Input: [vacío]
Contador: "50 batches disponibles"
Visible: Todos los 50 batches
```

---

## 🐛 Manejo de Casos Especiales

### Caso 1: No hay batches
```
Input: [cualquier cosa]
Contador: "0 batches disponibles"
Mensaje: "¡Todos los batches están asignados!"
```

### Caso 2: Búsqueda sin resultados
```
Input: "xyz123"
Contador: "0 batches disponibles"
Mensaje: "No se encontraron batches con ese criterio"
        "Intenta con otro término de búsqueda"
```

### Caso 3: Batches filtrados son arrastrables
```
Input: "batch_0001"
Visible: 2 batches
Acción: Arrastrar uno hacia segmentador
Resultado: ✅ Funciona normalmente
          Se puede arrastrar sin problemas
```

---

## 📱 Responsive

El buscador se adapta a diferentes tamaños de pantalla:

**Desktop (>768px):**
```
┌──────────────────────────────────────────────┐
│ Título          |  [🔍] [Buscador...]  [✕] │
└──────────────────────────────────────────────┘
```

**Mobile (<768px):**
```
┌─────────────────────────┐
│ Título                  │
│ [🔍] [Buscador...] [✕] │
└─────────────────────────┘
```

---

## ⌨️ Atajos

| Acción | Método |
|--------|--------|
| **Buscar en tiempo real** | Escribir en el input |
| **Buscar (Enter)** | Escribir + Enter |
| **Limpiar** | Clic en [✕] |
| **Limpiar (teclado)** | Seleccionar todo + Delete |

---

## 🎯 Ventajas

### Para el Usuario
1. ✅ **Rápido:** Encuentra batches en segundos
2. ✅ **Simple:** Solo escribe y filtra
3. ✅ **Visual:** Contador muestra cuántos resultados
4. ✅ **Flexible:** Busca por cualquier parte del ID

### Para el Sistema
1. ✅ **Eficiente:** Filtra en cliente (sin requests)
2. ✅ **Ligero:** Solo JavaScript vanilla + jQuery
3. ✅ **Compatible:** Funciona con drag & drop
4. ✅ **Mantenible:** Código simple y claro

---

## 🔄 Integración con Otras Funciones

### Con Carga Rápida
```
1. Usuario carga batches con copy-paste
2. Batches aparecen en lista
3. Usuario busca uno específico
4. Lo arrastra al segmentador
```

### Con Drag & Drop
```
1. Usuario busca "batch_0001"
2. Aparece 1 resultado
3. Lo arrastra a "Mauricio"
4. Búsqueda sigue activa
5. Puede buscar otro batch
```

---

## 📝 Mejoras Futuras (Opcional)

### Posibles Mejoras
1. **Búsqueda por múltiples campos:**
   - Por status (NS, In, S)
   - Por fecha de creación
   - Por prioridad

2. **Filtros avanzados:**
   - Dropdown con opciones
   - Filtros combinados

3. **Historial de búsqueda:**
   - Recordar búsquedas recientes
   - Sugerencias automáticas

4. **Highlight:**
   - Resaltar el término buscado en los resultados

---

## ✅ Estado Actual

**Implementado:** ✅ Completamente funcional

**Características:**
- ✅ Búsqueda en tiempo real
- ✅ Case-insensitive
- ✅ Búsqueda parcial
- ✅ Contador dinámico
- ✅ Botón limpiar
- ✅ Mensaje "sin resultados"
- ✅ Compatible con drag & drop

**Ubicación:** `/assign` → Header de "Batches No Asignados"

---

**Documento creado:** 15 de Octubre de 2025
**Estado:** ✅ Funcionando
