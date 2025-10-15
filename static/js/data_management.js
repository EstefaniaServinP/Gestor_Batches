/* ===============================================
   JAVASCRIPT PARA DATA_MANAGEMENT.HTML
   Gestión de Datos - Cargar, Exportar y Eliminar Batches
   =============================================== */

// Variables globales
let selectedFile = null;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
  initializeDataManagement();
});

// Función principal de inicialización
function initializeDataManagement() {
  setupEventListeners();
  loadStatistics();
}

// Configurar event listeners
function setupEventListeners() {
  // File drop zone
  const dropZone = document.getElementById('fileDropZone');
  const fileInput = document.getElementById('fileInput');

  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', handleDragOver);
  dropZone.addEventListener('dragleave', handleDragLeave);
  dropZone.addEventListener('drop', handleDrop);

  fileInput.addEventListener('change', handleFileSelect);

  // Botones
  document.getElementById('btnUpload').addEventListener('click', handleUpload);
  document.getElementById('btnExport').addEventListener('click', handleExport);
  document.getElementById('btnDeleteModal').addEventListener('click', openDeleteModal);
  document.getElementById('btnCloseModal').addEventListener('click', closeDeleteModal);
  document.getElementById('btnCancelDelete').addEventListener('click', closeDeleteModal);
  document.getElementById('btnConfirmDelete').addEventListener('click', handleDelete);

  // Checkbox de "solo sin asignar"
  document.getElementById('deleteUnassignedOnly').addEventListener('change', function() {
    const assigneeSelect = document.getElementById('deleteAssignee');
    assigneeSelect.disabled = this.checked;
    if (this.checked) {
      assigneeSelect.value = '';
    }
  });
}

// Drag and drop handlers
function handleDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  e.currentTarget.classList.remove('dragover');

  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
}

function handleFileSelect(e) {
  const files = e.target.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
}

function handleFile(file) {
  if (!file.name.endsWith('.json')) {
    showNotification('Por favor selecciona un archivo JSON', 'error');
    return;
  }

  selectedFile = file;

  // Mostrar información del archivo
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent = `Tamaño: ${formatFileSize(file.size)}`;
  document.getElementById('fileInfo').style.display = 'block';
  document.getElementById('btnUpload').disabled = false;
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Cargar estadísticas
async function loadStatistics() {
  try {
    const response = await fetch('/api/data/batches/stats');
    const data = await response.json();

    if (data.success) {
      const stats = data.stats;
      document.getElementById('totalBatches').textContent = stats.total;
      document.getElementById('unassignedBatches').textContent = stats.unassigned;
      document.getElementById('assignedBatches').textContent = stats.total - stats.unassigned;
    }
  } catch (error) {
    console.error('Error cargando estadísticas:', error);
  }
}

// Cargar batches desde JSON
async function handleUpload() {
  if (!selectedFile) {
    showNotification('No has seleccionado ningún archivo', 'error');
    return;
  }

  const mode = document.getElementById('uploadMode').value;

  // Confirmar si es modo reemplazar
  if (mode === 'replace') {
    const confirm = window.confirm(
      '⚠️ ADVERTENCIA: Esto eliminará TODOS los batches existentes y los reemplazará con los del archivo.\n\n' +
      'Se creará un backup automático.\n\n' +
      '¿Estás seguro de continuar?'
    );
    if (!confirm) return;
  }

  showLoading(true);

  try {
    // Leer el archivo
    const fileContent = await readFileAsText(selectedFile);
    const jsonData = JSON.parse(fileContent);

    // Validar estructura
    if (!jsonData.batches || !Array.isArray(jsonData.batches)) {
      showNotification('El archivo JSON debe contener un array "batches"', 'error');
      showLoading(false);
      return;
    }

    // Enviar al servidor
    const response = await fetch('/api/data/batches/upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        batches: jsonData.batches,
        mode: mode
      })
    });

    const result = await response.json();

    if (result.success) {
      showNotification(
        `✅ ${result.inserted_count} batches cargados exitosamente`,
        'success'
      );

      // Limpiar selección
      selectedFile = null;
      document.getElementById('fileInput').value = '';
      document.getElementById('fileInfo').style.display = 'none';
      document.getElementById('btnUpload').disabled = true;

      // Recargar estadísticas
      setTimeout(() => {
        loadStatistics();
      }, 1000);

      // Notificar sincronización con otros módulos
      notifyBatchesChanged();
    } else {
      showNotification(`Error: ${result.error}`, 'error');
    }
  } catch (error) {
    console.error('Error cargando batches:', error);
    showNotification(`Error al cargar: ${error.message}`, 'error');
  } finally {
    showLoading(false);
  }
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(e);
    reader.readAsText(file);
  });
}

// Exportar batches a JSON
async function handleExport() {
  showLoading(true);

  try {
    const response = await fetch('/api/data/batches/export');

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // Obtener nombre de archivo del header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'batches_export.json';
      if (contentDisposition) {
        const matches = /filename="(.+)"/.exec(contentDisposition);
        if (matches && matches[1]) {
          filename = matches[1];
        }
      }

      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showNotification('✅ Batches exportados exitosamente', 'success');
    } else {
      const error = await response.json();
      showNotification(`Error: ${error.error}`, 'error');
    }
  } catch (error) {
    console.error('Error exportando batches:', error);
    showNotification(`Error al exportar: ${error.message}`, 'error');
  } finally {
    showLoading(false);
  }
}

// Modal de eliminación
function openDeleteModal() {
  document.getElementById('deleteModal').style.display = 'flex';
}

function closeDeleteModal() {
  document.getElementById('deleteModal').style.display = 'none';
  // Limpiar campos
  document.getElementById('deleteIdPattern').value = '';
  document.getElementById('deleteStatus').value = '';
  document.getElementById('deleteAssignee').value = '';
  document.getElementById('deleteUnassignedOnly').checked = false;
  document.getElementById('deleteAssignee').disabled = false;
}

// Eliminar batches por filtro
async function handleDelete() {
  const idPattern = document.getElementById('deleteIdPattern').value.trim();
  const status = document.getElementById('deleteStatus').value;
  const assignee = document.getElementById('deleteAssignee').value;
  const unassignedOnly = document.getElementById('deleteUnassignedOnly').checked;

  // Validar que al menos un filtro esté seleccionado
  if (!idPattern && !status && !assignee && !unassignedOnly) {
    showNotification('Debes seleccionar al menos un filtro', 'warning');
    return;
  }

  // Confirmación
  const confirm = window.confirm(
    '⚠️ ADVERTENCIA: Esta acción eliminará batches según los filtros especificados.\n\n' +
    'Se creará un backup automático de los batches eliminados.\n\n' +
    '¿Estás seguro de continuar?'
  );
  if (!confirm) return;

  showLoading(true);
  closeDeleteModal();

  try {
    const response = await fetch('/api/data/batches/delete-by-filter', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        id_pattern: idPattern,
        status: status,
        assignee: assignee,
        unassigned_only: unassignedOnly
      })
    });

    const result = await response.json();

    if (result.success) {
      showNotification(
        `✅ ${result.deleted_count} batches eliminados exitosamente`,
        'success'
      );

      // Recargar estadísticas
      setTimeout(() => {
        loadStatistics();
      }, 1000);

      // Notificar sincronización con otros módulos
      notifyBatchesChanged();
    } else {
      showNotification(`Error: ${result.error}`, 'error');
    }
  } catch (error) {
    console.error('Error eliminando batches:', error);
    showNotification(`Error al eliminar: ${error.message}`, 'error');
  } finally {
    showLoading(false);
  }
}

// Notificar cambios a otros módulos (sincronización)
function notifyBatchesChanged() {
  // Disparar evento personalizado para que otros módulos puedan escuchar
  const event = new CustomEvent('batchesChanged', {
    detail: { timestamp: new Date().toISOString() }
  });
  window.dispatchEvent(event);

  // Si hay una tabla de DataTables activa en otra página, recargarla
  if (window.batchTable && typeof window.batchTable.ajax === 'object') {
    window.batchTable.ajax.reload(null, false);
  }

  console.log('✅ Notificación de cambios en batches enviada');
}

// Mostrar notificación
function showNotification(message, type = 'success') {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.className = `notification ${type}`;
  notification.style.display = 'block';

  setTimeout(() => {
    notification.style.display = 'none';
  }, 5000);
}

// Mostrar/ocultar loading
function showLoading(show) {
  document.getElementById('loading').style.display = show ? 'block' : 'none';
}

// Escuchar eventos de cambios en batches desde otros módulos
window.addEventListener('batchesChanged', function(e) {
  console.log('📡 Cambios en batches detectados desde otro módulo:', e.detail);
  loadStatistics();
});
