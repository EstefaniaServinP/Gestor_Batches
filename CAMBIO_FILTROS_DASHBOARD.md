# Cambios en Filtros del Dashboard

## 📋 Resumen del Cambio

Se modificó el comportamiento del dashboard para diferenciar entre:
- **Dashboard General** (sin filtro de segmentador)
- **Dashboard Individual** (con filtro de segmentador específico)

---

## 🎯 Comportamiento Anterior

**Antes**, el dashboard general mostraba solo:
- Batches con status "In" (Incompleto) o "NS" (No Segmentado)
- Ocultaba TODOS los batches con status "S" (Segmentado)

**Problema:**
- No se podía ver el historial completo de trabajo de cada segmentador
- Los batches segmentados pero no aprobados se ocultaban

---

## ✅ Comportamiento Nuevo

### Dashboard General (sin filtro de segmentador)

**Muestra:**
- ✅ Batches con status "NS" (No Segmentado)
- ✅ Batches con status "In" (Incompleto)
- ✅ Batches con status "S" (Segmentado) que **NO** están aprobados

**Oculta SOLO:**
- ❌ Batches que tienen:
  - `status = "S"` (Segmentado) **Y**
  - `metadata.review_status = "aprobado"` (Aprobado)

**Ejemplo:**
```
Batch 001: status=NS, review_status=''            → ✅ Se muestra
Batch 002: status=In, review_status=''            → ✅ Se muestra
Batch 003: status=S, review_status=''             → ✅ Se muestra (segmentado pero no revisado)
Batch 004: status=S, review_status='no_aprobado' → ✅ Se muestra (segmentado pero rechazado)
Batch 005: status=S, review_status='aprobado'    → ❌ SE OCULTA (completado y aprobado)
```

---

### Dashboard Individual (con filtro por segmentador)

**Ejemplo:** Al filtrar por "Mauricio"

**Muestra:**
- ✅ **TODOS** los batches asignados a Mauricio
- ✅ Sin importar el `status` (NS, In, S)
- ✅ Sin importar `review_status` (aprobado, no_aprobado, pendiente)

**Propósito:**
- Ver el historial completo de trabajo del segmentador
- Hacer seguimiento a batches completados y aprobados
- Revisar batches rechazados que necesitan corrección

**Ejemplo:**
```
Dashboard de Mauricio (/dashboard?assignee=Mauricio):
Batch 010: status=NS, review_status=''            → ✅ Se muestra
Batch 020: status=In, review_status=''            → ✅ Se muestra
Batch 030: status=S, review_status=''             → ✅ Se muestra
Batch 040: status=S, review_status='aprobado'    → ✅ Se muestra (historial completo)
Batch 050: status=S, review_status='no_aprobado' → ✅ Se muestra (historial completo)
```

---

## 🔧 Implementación Técnica

### Archivo Modificado:
`templates/dashboard.html` (líneas 1072-1094)

### Lógica Implementada:

```javascript
// Detectar si hay filtro de segmentador activo
const isFilteredByAssignee = $('#filter-assignee').val() !== '';

if (isFilteredByAssignee) {
  // DASHBOARD INDIVIDUAL: Mostrar TODOS los batches del segmentador
  const selectedAssignee = $('#filter-assignee').val();
  batchesForReview = batches.filter(batch =>
    batch.assignee === selectedAssignee
  );
} else {
  // DASHBOARD GENERAL: Ocultar solo batches Segmentados Y Aprobados
  batchesForReview = batches.filter(batch => {
    const isSegmented = batch.status === 'S';
    const isApproved = batch.metadata?.review_status === 'aprobado';
    const shouldHide = isSegmented && isApproved;
    return !shouldHide && batch.assignee && batch.assignee.trim() !== '';
  });
}
```

---

## 📊 Campos Involucrados

### 1. `status` (Estatus de Segmentación)
- **Valores:** "NS", "In", "S"
- **Descripción:**
  - `NS` = No Segmentado
  - `In` = Incompleto (en proceso)
  - `S` = Segmentado (completado)

### 2. `metadata.review_status` (Revisión)
- **Valores:** "aprobado", "no_aprobado", o vacío
- **Descripción:**
  - `aprobado` = Revisado y aprobado (✅)
  - `no_aprobado` = Revisado pero rechazado (❌)
  - vacío = Pendiente de revisión

---

## 🎯 Casos de Uso

### Caso 1: Ver cola general de trabajo
```
Usuario: Accede a /dashboard (sin filtro)
Resultado: Ve todos los batches pendientes + segmentados sin aprobar
Batches ocultos: Solo los que están completamente terminados (S + aprobado)
```

### Caso 2: Ver trabajo específico de Mauricio
```
Usuario: Accede a /dashboard y filtra por "Mauricio"
Resultado: Ve TODO el trabajo de Mauricio (historial completo)
Batches ocultos: Ninguno (muestra todo su trabajo)
```

### Caso 3: Ver trabajo específico de Maggie
```
Usuario: Accede a /dashboard/Maggie (URL directa)
Resultado: Ve TODO el trabajo de Maggie automáticamente
Batches ocultos: Ninguno
```

---

## ✅ Verificación

Para verificar que funciona correctamente:

1. **Dashboard General:**
   ```
   Navegar a: http://localhost:5000/dashboard
   Verificar: Solo aparecen batches pendientes (no se ven los S + aprobado)
   ```

2. **Dashboard Individual:**
   ```
   Navegar a: http://localhost:5000/dashboard
   Filtrar por: Seleccionar un segmentador del dropdown
   Verificar: Aparecen TODOS los batches de ese segmentador
   ```

3. **Probar con consola del navegador:**
   ```javascript
   // Ver logs en consola (F12):
   // Debe mostrar: "[DASHBOARD GENERAL]" o "[DASHBOARD INDIVIDUAL]"
   ```

---

## 📝 Notas Importantes

1. ✅ **No se cambió** la API backend
2. ✅ **No se modificó** la estructura de la base de datos
3. ✅ **Solo se cambió** el filtrado en el frontend (JavaScript)
4. ✅ Los cambios son **retrocompatibles** con batches existentes
5. ✅ La funcionalidad de **edición inline** sigue funcionando igual

---

**Fecha de cambio:** 2025-10-16
**Archivo modificado:** `templates/dashboard.html`
**Líneas:** 1072-1094
