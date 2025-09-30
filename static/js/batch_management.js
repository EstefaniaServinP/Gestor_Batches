/* ===============================================
   JAVASCRIPT ESPECÍFICO PARA BATCH_MANAGEMENT.HTML
   =============================================== */

// Variables globales para batch management
let operationInProgress = false;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
  initializeBatchManagement();
});

// Función principal de inicialización
function initializeBatchManagement() {
  setupEventListeners();
  checkMongoConnection();
  loadInitialStats();
}

// Configurar event listeners
function setupEventListeners() {
  // Botones de herramientas
  const buttons = document.querySelectorAll('.tool-button');
  buttons.forEach(button => {
    button.addEventListener('click', handleToolAction);
  });
  
  // Formularios
  const forms = document.querySelectorAll('.management-form form');
  forms.forEach(form => {
    form.addEventListener('submit', handleFormSubmit);
  });
}

// Manejar acciones de herramientas
async function handleToolAction(event) {
  if (operationInProgress) {
    showNotification('Hay una operación en progreso. Espera a que termine.', 'warning');
    return;
  }
  
  const action = event.target.dataset.action;
  const confirmation = event.target.dataset.confirm;
  
  if (confirmation && !confirm(confirmation)) {
    return;
  }
  
  switch(action) {
    case 'check-mongo':
      await checkMongoFiles();
      break;
    case 'sync-batches':
      await syncBatchFiles();
      break;
    case 'auto-create':
      await autoCreateBatches();
      break;
    case 'init-batches':
      await initializeBatches();
      break;
    case 'reset-batches':
      await resetBatches();
      break;
    case 'missing-batches':
      await findMissingBatches();
      break;
    default:
      showNotification('Acción no reconocida', 'error');
  }
}

// Verificar conexión a MongoDB
async function checkMongoConnection() {
  try {
    const response = await fetch('/api/check-mongo-files');
    const data = await response.json();
    
    if (data.success) {
      updateConnectionStatus('success', 'Conexión a MongoDB exitosa');
    } else {
      updateConnectionStatus('error', 'Error de conexión a MongoDB');
    }
  } catch (error) {
    updateConnectionStatus('error', 'No se pudo conectar a MongoDB');
  }
}

// Actualizar estado de conexión
function updateConnectionStatus(type, message) {
  const statusElement = document.getElementById('connectionStatus');
  if (statusElement) {
    statusElement.className = `operation-status status-${type}`;
    statusElement.textContent = message;
  }
}

// Verificar archivos en MongoDB
async function checkMongoFiles() {
  operationInProgress = true;
  showLoading();
  clearLogs();
  
  try {
    addLog('info', 'Verificando archivos en MongoDB...');
    
    const response = await fetch('/api/check-mongo-files');
    const data = await response.json();
    
    if (data.success) {
      addLog('success', `Encontrados ${data.total_files} archivos en MongoDB`);
      updateFileStats(data.stats);
      showNotification('Verificación completada exitosamente', 'success');
    } else {
      addLog('error', `Error: ${data.error}`);
      showNotification('Error verificando archivos', 'error');
    }
  } catch (error) {
    addLog('error', `Error de conexión: ${error.message}`);
    showNotification('Error de conexión', 'error');
  } finally {
    operationInProgress = false;
    hideLoading();
  }
}

// Sincronizar archivos de batches
async function syncBatchFiles() {
  operationInProgress = true;
  showLoading();
  clearLogs();
  
  try {
    addLog('info', 'Sincronizando archivos de batches...');
    
    const response = await fetch('/api/sync-batch-files', { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
      addLog('success', `Sincronización completada: ${data.synchronized} batches`);
      if (data.details) {
        data.details.forEach(detail => {
          addLog('info', `  - ${detail}`);
        });
      }
      showNotification('Sincronización completada', 'success');
    } else {
      addLog('error', `Error en sincronización: ${data.error}`);
      showNotification('Error en sincronización', 'error');
    }
  } catch (error) {
    addLog('error', `Error de conexión: ${error.message}`);
    showNotification('Error de conexión', 'error');
  } finally {
    operationInProgress = false;
    hideLoading();
  }
}

// Crear batches automáticamente
async function autoCreateBatches() {
  operationInProgress = true;
  showLoading();
  clearLogs();
  
  try {
    addLog('info', 'Creando batches automáticamente...');
    
    const response = await fetch('/api/auto-create-batches', { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
      addLog('success', `Creados ${data.created} nuevos batches`);
      if (data.batches) {
        data.batches.forEach(batch => {
          addLog('info', `  - ${batch.id}: ${batch.file_count} archivos`);
        });
      }
      showNotification(`${data.created} batches creados exitosamente`, 'success');
    } else {
      addLog('error', `Error creando batches: ${data.error}`);
      showNotification('Error creando batches', 'error');
    }
  } catch (error) {
    addLog('error', `Error de conexión: ${error.message}`);
    showNotification('Error de conexión', 'error');
  } finally {
    operationInProgress = false;
    hideLoading();
  }
}

// Inicializar batches desde archivo
async function initializeBatches() {
  operationInProgress = true;
  showLoading();
  clearLogs();
  
  try {
    addLog('info', 'Inicializando batches desde archivo...');
    
    const response = await fetch('/api/init-batches', { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
      addLog('success', `Inicialización completada: ${data.loaded} batches cargados`);
      showNotification('Batches inicializados correctamente', 'success');
    } else {
      addLog('error', `Error en inicialización: ${data.error}`);
      showNotification('Error inicializando batches', 'error');
    }
  } catch (error) {
    addLog('error', `Error de conexión: ${error.message}`);
    showNotification('Error de conexión', 'error');
  } finally {
    operationInProgress = false;
    hideLoading();
  }
}

// Reset de batches
async function resetBatches() {
  const confirmText = prompt('Esta acción eliminará TODOS los batches. Escribe "CONFIRMAR" para continuar:');
  
  if (confirmText !== 'CONFIRMAR') {
    showNotification('Operación cancelada', 'info');
    return;
  }
  
  operationInProgress = true;
  showLoading();
  clearLogs();
  
  try {
    addLog('warning', 'RESET: Eliminando todos los batches...');
    
    const response = await fetch('/api/reset-batches', { method: 'POST' });
    const data = await response.json();
    
    if (data.success) {
      addLog('success', `Reset completado: ${data.deleted} batches eliminados`);
      showNotification('Reset completado exitosamente', 'success');
    } else {
      addLog('error', `Error en reset: ${data.error}`);
      showNotification('Error en reset', 'error');
    }
  } catch (error) {
    addLog('error', `Error de conexión: ${error.message}`);
    showNotification('Error de conexión', 'error');
  } finally {
    operationInProgress = false;
    hideLoading();
  }
}

// Encontrar batches faltantes
async function findMissingBatches() {
  operationInProgress = true;
  showLoading();
  clearLogs();
  
  try {
    addLog('info', 'Buscando batches faltantes...');
    
    const response = await fetch('/api/missing-batches');
    const data = await response.json();
    
    if (data.success) {
      if (data.missing.length === 0) {
        addLog('success', 'No se encontraron batches faltantes');
      } else {
        addLog('warning', `Encontrados ${data.missing.length} batches faltantes:`);
        data.missing.forEach(batch => {
          addLog('info', `  - ${batch}`);
        });
      }
      showNotification('Búsqueda completada', 'success');
    } else {
      addLog('error', `Error buscando batches: ${data.error}`);
      showNotification('Error en búsqueda', 'error');
    }
  } catch (error) {
    addLog('error', `Error de conexión: ${error.message}`);
    showNotification('Error de conexión', 'error');
  } finally {
    operationInProgress = false;
    hideLoading();
  }
}

// Manejar envío de formularios
function handleFormSubmit(event) {
  event.preventDefault();
  
  if (operationInProgress) {
    showNotification('Hay una operación en progreso. Espera a que termine.', 'warning');
    return;
  }
  
  const form = event.target;
  const action = form.dataset.action;
  
  // Procesar según el tipo de formulario
  switch(action) {
    case 'create-batch':
      createSingleBatch(form);
      break;
    case 'assign-batch':
      assignBatch(form);
      break;
    default:
      showNotification('Acción de formulario no reconocida', 'error');
  }
}

// Crear un batch individual
async function createSingleBatch(form) {
  const formData = new FormData(form);
  const batchData = Object.fromEntries(formData.entries());
  
  operationInProgress = true;
  showLoading();
  
  try {
    const response = await fetch('/api/batches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batchData)
    });
    
    const data = await response.json();
    
    if (data.success || response.ok) {
      showNotification('Batch creado exitosamente', 'success');
      form.reset();
    } else {
      showNotification('Error creando batch: ' + (data.error || 'Error desconocido'), 'error');
    }
  } catch (error) {
    showNotification('Error de conexión: ' + error.message, 'error');
  } finally {
    operationInProgress = false;
    hideLoading();
  }
}

// Funciones de utilidad para logs
function clearLogs() {
  const logsContainer = document.getElementById('logsContainer');
  if (logsContainer) {
    logsContainer.innerHTML = '';
  }
}

function addLog(type, message) {
  const logsContainer = document.getElementById('logsContainer');
  if (!logsContainer) return;
  
  const timestamp = new Date().toLocaleTimeString();
  const logEntry = document.createElement('div');
  logEntry.className = `log-entry log-${type}`;
  logEntry.innerHTML = `
    <span class="log-timestamp">${timestamp}</span>
    <span class="log-message">${message}</span>
  `;
  
  logsContainer.appendChild(logEntry);
  logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Actualizar estadísticas de archivos
function updateFileStats(stats) {
  if (!stats) return;
  
  const statsContainer = document.getElementById('fileStats');
  if (!statsContainer) return;
  
  statsContainer.innerHTML = `
    <div class="stat-box">
      <div class="stat-number">${stats.total || 0}</div>
      <div class="stat-label">Total</div>
    </div>
    <div class="stat-box">
      <div class="stat-number">${stats.batches || 0}</div>
      <div class="stat-label">Batches</div>
    </div>
    <div class="stat-box">
      <div class="stat-number">${stats.assigned || 0}</div>
      <div class="stat-label">Asignados</div>
    </div>
    <div class="stat-box">
      <div class="stat-number">${stats.unassigned || 0}</div>
      <div class="stat-label">Sin Asignar</div>
    </div>
  `;
}

// Cargar estadísticas iniciales
function loadInitialStats() {
  // Placeholder para estadísticas iniciales
  updateFileStats({
    total: 0,
    batches: 0,
    assigned: 0,
    unassigned: 0
  });
}
