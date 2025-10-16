# Diagnóstico Frontend: Batches No Aparecen

## 🐛 Problema

Batches existen en MongoDB pero **NO aparecen** en el dashboard después de:
1. Crear con "Carga Rápida"
2. Recargar la página

---

## 🔍 Diagnóstico Paso a Paso

### Paso 1: Verificar URL de Acceso

**¿Desde qué URL estás accediendo?**

Mira la barra de direcciones del navegador:

❌ **INCORRECTO:**
```
http://192.168.1.93:5000/assign
http://192.168.1.XX:5000/assign
```

✅ **CORRECTO:**
```
http://localhost:5000/assign
http://127.0.0.1:5000/assign
```

**Si estás usando la IP incorrecta:**
1. Cierra esa pestaña
2. Abre nueva pestaña
3. Ve a: `http://localhost:5000/assign`

---

### Paso 2: Limpiar Caché del Navegador

**Opción A: Recarga forzada**
```
Ctrl + Shift + R
```

**Opción B: Limpiar todo**
1. Presiona `F12` (abrir DevTools)
2. Click derecho en el botón de recargar
3. Selecciona "Vaciar caché y recargar de forma forzada"

**Opción C: Desde DevTools**
1. `F12` → Pestaña "Application"
2. Lateral izquierdo → "Storage"
3. Click derecho → "Clear site data"
4. Recargar la página

---

### Paso 3: Verificar Consola del Navegador

1. Presiona `F12`
2. Ve a la pestaña "Console"
3. **¿Ves algún error en ROJO?**

**Errores comunes:**

#### Error A: "Failed to fetch" o "net::ERR_CONNECTION_REFUSED"
```
❌ Error en carga rápida:
  - Status: 0
  - Error: Failed to fetch
```

**Causa:** Estás accediendo desde la IP incorrecta

**Solución:** Ve a `http://localhost:5000/assign`

---

#### Error B: "Requested unknown parameter '4'"
```
❌ DataTables warning: table id=batchesTable - Requested unknown parameter '4'
```

**Causa:** Error de DataTables (ya debería estar arreglado)

**Solución:** Recarga con `Ctrl + Shift + R`

---

#### Error C: No hay errores pero no aparecen batches

**Causa:** La función `loadBatches()` no se está ejecutando

**Solución:** Ejecuta manualmente en la consola

---

### Paso 4: Ejecutar Diagnóstico Manual

**Pega este código en la consola del navegador** (F12 → Console):

```javascript
// ==========================================
// DIAGNÓSTICO MANUAL DE CARGA DE BATCHES
// ==========================================

console.log("🔍 Iniciando diagnóstico...");
console.log("");

// 1. Verificar URL actual
console.log("📍 URL actual:", window.location.href);
if (!window.location.href.includes("localhost") && !window.location.href.includes("127.0.0.1")) {
  console.error("❌ URL INCORRECTA");
  console.error("   Debes acceder desde: http://localhost:5000/assign");
  console.error("   Actual: " + window.location.href);
} else {
  console.log("✅ URL correcta");
}
console.log("");

// 2. Verificar variable global 'batches'
console.log("📦 Variable 'batches':", typeof batches);
if (typeof batches !== 'undefined') {
  console.log("   Total en memoria:", batches.length);
  console.log("   Primeros 3:", batches.slice(0, 3).map(b => b.id));
} else {
  console.error("❌ Variable 'batches' no definida");
}
console.log("");

// 3. Verificar función loadBatches
console.log("🔄 Función 'loadBatches':", typeof loadBatches);
if (typeof loadBatches === 'undefined') {
  console.error("❌ Función loadBatches no existe");
}
console.log("");

// 4. Probar API directamente
console.log("🌐 Probando API...");
fetch('/api/batches?per_page=1000', { cache: 'no-store' })
  .then(res => res.json())
  .then(data => {
    console.log("✅ API respondió correctamente");
    console.log("   Total batches en API:", data.batches.length);
    console.log("   Primeros 5 IDs:", data.batches.slice(0, 5).map(b => b.id));

    // Ver batches sin asignar
    const unassigned = data.batches.filter(b => !b.assignee || b.assignee === null || b.assignee === '');
    console.log("   Sin asignar:", unassigned.length);
    console.log("   Primeros 5 sin asignar:", unassigned.slice(0, 5).map(b => b.id));

    console.log("");
    console.log("🎯 SOLUCIÓN:");
    console.log("   Si ves batches aquí pero NO en el dashboard, ejecuta:");
    console.log("   loadBatches()");
  })
  .catch(err => {
    console.error("❌ Error al llamar API:", err);
    console.error("   Causa probable: Flask no está corriendo o URL incorrecta");
  });

console.log("");
console.log("⏳ Esperando respuesta de la API...");
```

---

### Paso 5: Forzar Recarga Manual

**Si el diagnóstico muestra que la API funciona pero el dashboard no:**

Pega este código en la consola:

```javascript
// FORZAR RECARGA DE BATCHES
console.log("🔄 Forzando recarga de batches...");

async function forceReload() {
  try {
    // Limpiar caché de variables
    window.batches = [];

    // Llamar a loadBatches
    await loadBatches();

    console.log("✅ Recarga completada");
    console.log("📊 Total batches cargados:", batches.length);

    // Ver sin asignar
    const unassigned = batches.filter(b => !b.assignee || b.assignee === null || b.assignee === '');
    console.log("📦 Batches sin asignar:", unassigned.length);

  } catch (error) {
    console.error("❌ Error al forzar recarga:", error);
  }
}

forceReload();
```

---

### Paso 6: Verificar Contenedor DOM

**Verifica que el contenedor de batches existe:**

```javascript
// VERIFICAR CONTENEDOR DOM
console.log("🎯 Verificando contenedores DOM...");

const unassignedContainer = document.getElementById('unassignedBatches');
console.log("Contenedor 'unassignedBatches':", unassignedContainer ? "✅ Existe" : "❌ NO existe");

if (unassignedContainer) {
  console.log("  - Hijos:", unassignedContainer.children.length);
  console.log("  - Visible:", unassignedContainer.offsetParent !== null);
}

const noResultsMsg = document.getElementById('noResultsMessage');
console.log("Mensaje 'noResultsMessage':", noResultsMsg ? "✅ Existe" : "❌ NO existe");

if (noResultsMsg) {
  console.log("  - Display:", window.getComputedStyle(noResultsMsg).display);
}
```

---

## 🎯 Soluciones Según Diagnóstico

### Solución 1: URL Incorrecta

**Síntoma:** Error "Failed to fetch" o "Connection refused"

**Acción:**
1. Cierra la pestaña actual
2. Abre: `http://localhost:5000/assign`
3. Recarga con `Ctrl + Shift + R`

---

### Solución 2: Caché del Navegador

**Síntoma:** API funciona pero batches no aparecen

**Acción:**
1. `F12` → Application → Clear site data
2. O usa modo incógnito: `Ctrl + Shift + N`
3. Ve a `http://localhost:5000/assign`

---

### Solución 3: JavaScript No Se Ejecuta

**Síntoma:** La función `loadBatches` no está definida

**Acción:**
1. Verifica errores en consola
2. Recarga la página
3. Si persiste, reinicia Flask:
   ```bash
   # Terminal donde corre Flask: Ctrl + C
   python app.py
   ```

---

### Solución 4: Batches Están Asignados

**Síntoma:** API devuelve batches pero están asignados

**Acción:**

**Los 3 batches que pediste YA ESTÁN ASIGNADOS a Maggie:**
- `batch_000001F` → Asignado a Maggie
- `batch_000045F` → Asignado a Maggie
- `batch_000046F` → Asignado a Maggie

**Por eso NO aparecen en "Batches No Asignados".**

**Opciones:**

A) **Ver en la tarjeta de Maggie:**
   1. Click en "Maggie" para expandir su tarjeta
   2. Deberías ver esos 3 batches ahí

B) **Desasignarlos para reasignar:**
   ```bash
   python reassign_batch.py batch_000001F null
   python reassign_batch.py batch_000045F null
   python reassign_batch.py batch_000046F null
   ```

C) **Verificar en vista detallada:**
   1. Toggle "Vista Detallada"
   2. Busca en la tabla por "Maggie"
   3. Deberías verlos ahí

---

## 📋 Checklist de Verificación

Marca lo que ya verificaste:

- [ ] Accediendo desde `http://localhost:5000/assign` (NO desde 192.168.1.93)
- [ ] Recargado con `Ctrl + Shift + R`
- [ ] Limpiado caché del navegador
- [ ] Sin errores en consola (F12)
- [ ] API devuelve 435 batches (verificado con diagnóstico)
- [ ] Función `loadBatches()` existe
- [ ] Variable `batches` tiene datos
- [ ] Contenedor DOM `#unassignedBatches` existe

---

## 🔄 Flujo Completo Correcto

```
1. Acceder desde localhost:5000/assign
          ↓
2. Página carga → loadBatches() se ejecuta
          ↓
3. GET /api/batches?per_page=1000
          ↓
4. API devuelve 435 batches
          ↓
5. updateDragDropInterface() filtra por assignee
          ↓
6. Sin asignar: 365 batches
   Asignados: 70 batches
          ↓
7. renderUnassignedBatches(365 batches)
          ↓
8. Aparecen en "Batches No Asignados"
```

---

## 💡 Solución Rápida (Si Todo Lo Demás Falla)

**Ejecuta este comando completo en la consola del navegador:**

```javascript
// SOLUCIÓN RÁPIDA COMPLETA
(async function() {
  console.log("🚀 Iniciando solución rápida...");

  // 1. Limpiar
  console.log("🧹 Limpiando variables...");
  window.batches = [];

  // 2. Recargar desde API
  console.log("🔄 Recargando desde API...");
  try {
    const response = await fetch('/api/batches?per_page=1000&_=' + Date.now(), {
      cache: 'no-store',
      headers: { 'Cache-Control': 'no-cache' }
    });

    const data = await response.json();
    window.batches = data.batches || data;

    console.log("✅ Batches cargados:", batches.length);

    // 3. Actualizar interfaz
    console.log("🎨 Actualizando interfaz...");
    if (typeof updateDragDropInterface === 'function') {
      updateDragDropInterface();
      console.log("✅ Interfaz actualizada");
    }

    if (typeof updateStats === 'function') {
      await updateStats();
      console.log("✅ Estadísticas actualizadas");
    }

    // 4. Verificar sin asignar
    const unassigned = batches.filter(b => !b.assignee || b.assignee === null || b.assignee === '');
    console.log("📦 Batches sin asignar:", unassigned.length);

    console.log("");
    console.log("🎉 COMPLETADO");
    console.log("   Si aún no aparecen, verifica que estés en la vista correcta");
    console.log("   (Vista Drag & Drop, no Vista Detallada)");

  } catch (error) {
    console.error("❌ Error:", error);
    console.error("   Verifica que estés en http://localhost:5000");
  }
})();
```

---

**Documento creado:** 15 de Octubre de 2025
**Última actualización:** 15 de Octubre de 2025
