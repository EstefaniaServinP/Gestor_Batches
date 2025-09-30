/* ===============================================
   JAVASCRIPT ESPECÍFICO PARA DASHBOARD.HTML
   =============================================== */

// Variables globales para dashboard
let batchesData = [];
let dataTable = null;
let currentFilter = '';

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
  initializeDashboard();
});

// Función principal de inicialización
async function initializeDashboard() {
  showLoading();
  
  try {
    await loadBatches();
    initializeDataTable();
    loadMetrics();
    setupEventListeners();
  } catch (error) {
    console.error('Error inicializando dashboard:', error);
    showNotification('Error cargando el dashboard', 'error');
  } finally {
    hideLoading();
  }
}

// Cargar batches desde la API
async function loadBatches(page = 1, perPage = 50) {
  try {
    const response = await fetch(`/api/batches?page=${page}&per_page=${perPage}`);
    const data = await response.json();

    // Handle new paginated response format
    if (data.batches) {
      batchesData = data.batches;
      // Store pagination info for future use
      window.currentPage = data.pagination.page;
      window.totalPages = data.pagination.total_pages;
      window.totalBatches = data.pagination.total;
    } else {
      // Fallback for old format
      batchesData = data;
    }

    // console.log('📊 Batches cargados:', batchesData.length, 'de', window.totalBatches || 'N/A');
  } catch (error) {
    console.error('Error cargando batches:', error);
    throw error;
  }
}

// Inicializar DataTable
function initializeDataTable() {
  if (dataTable) {
    dataTable.destroy();
  }
  
  dataTable = $('#batchesTable').DataTable({
    data: batchesData,
    columns: [
      { 
        data: 'id', 
        title: 'Batch ID',
        render: function(data, type, row) {
          return `<span class="batch-id">${data || 'Sin ID'}</span>`;
        }
      },
      { 
        data: 'assignee', 
        title: 'Responsable',
        render: function(data, type, row) {
          return `<span class="assignee editable" data-field="assignee" data-id="${row.id}">${data || 'Sin asignar'}</span>`;
        }
      },
      { 
        data: 'status', 
        title: 'Estado',
        render: function(data, type, row) {
          const statusClass = getStatusClass(data);
          const statusText = getStatusText(data);
          return `<span class="status-badge ${statusClass} editable" data-field="status" data-id="${row.id}">${statusText}</span>`;
        }
      },
      { 
        data: 'folder', 
        title: 'Carpeta',
        render: function(data, type, row) {
          return `<span class="folder editable" data-field="folder" data-id="${row.id}">${data || 'Sin carpeta'}</span>`;
        }
      },
      { 
        data: 'metadata.due_date', 
        title: 'Fecha Límite',
        render: function(data, type, row) {
          return `<span class="due-date editable" data-field="due_date" data-id="${row.id}">${data || 'Sin fecha'}</span>`;
        }
      },
      { 
        data: 'comments', 
        title: 'Comentarios',
        render: function(data, type, row) {
          const comments = data || 'Sin comentarios';
          const truncated = comments.length > 50 ? comments.substring(0, 50) + '...' : comments;
          return `<span class="comments editable" data-field="comments" data-id="${row.id}" title="${comments}">${truncated}</span>`;
        }
      },
      {
        data: null,
        title: 'Acciones',
        orderable: false,
        render: function(data, type, row) {
          return `
            <div class="action-buttons">
              <button class="btn-action btn-edit" onclick="editBatch('${row.id}')" title="Editar">
                <i class="fas fa-edit"></i>
              </button>
              <button class="btn-action btn-delete" onclick="deleteBatch('${row.id}')" title="Eliminar">
                <i class="fas fa-trash"></i>
              </button>
            </div>
          `;
        }
      }
    ],
    pageLength: 25,
    responsive: true,
    language: {
      url: 'https://cdn.datatables.net/plug-ins/1.13.4/i18n/es-ES.json'
    },
    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip',
    order: [[0, 'asc']]
  });
}

// Obtener clase CSS para estado
function getStatusClass(status) {
  switch(status) {
    case 'S': return 'status-s';
    case 'FS': return 'status-fs';
    case 'NS': return 'status-ns';
    case 'pendiente': return 'status-pending';
    case 'en-progreso': return 'status-in-progress';
    case 'completado': return 'status-completed';
    default: return 'status-pending';
  }
}

// Obtener texto legible para estado
function getStatusText(status) {
  switch(status) {
    case 'S': return 'Segmentado';
    case 'FS': return 'Parcial';
    case 'NS': return 'Pendiente';
    case 'pendiente': return 'Pendiente';
    case 'en-progreso': return 'En Progreso';
    case 'completado': return 'Completado';
    default: return status || 'Sin estado';
  }
}

// Cargar métricas del dashboard
function loadMetrics() {
  const metrics = calculateMetrics(batchesData);
  updateMetricsDisplay(metrics);
}

// Calcular métricas
function calculateMetrics(batches) {
  const total = batches.length;
  let completed = 0;
  let inProgress = 0;
  let pending = 0;
  
  batches.forEach(batch => {
    switch(batch.status) {
      case 'S':
      case 'completado':
        completed++;
        break;
      case 'FS':
      case 'en-progreso':
        inProgress++;
        break;
      case 'NS':
      case 'pendiente':
        pending++;
        break;
    }
  });
  
  return { total, completed, inProgress, pending };
}

// Actualizar display de métricas
function updateMetricsDisplay(metrics) {
  const metricsContainer = document.getElementById('metricsContainer');
  if (!metricsContainer) return;
  
  metricsContainer.innerHTML = `
    <div class="metric-card">
      <div class="metric-number">${metrics.total}</div>
      <div class="metric-label">Total Batches</div>
    </div>
    <div class="metric-card">
      <div class="metric-number" style="color: #22c55e;">${metrics.completed}</div>
      <div class="metric-label">Completados</div>
    </div>
    <div class="metric-card">
      <div class="metric-number" style="color: #f97316;">${metrics.inProgress}</div>
      <div class="metric-label">En Progreso</div>
    </div>
    <div class="metric-card">
      <div class="metric-number" style="color: #ef4444;">${metrics.pending}</div>
      <div class="metric-label">Pendientes</div>
    </div>
  `;
}

// Configurar event listeners
function setupEventListeners() {
  // Filtro por responsable
  const assigneeFilter = document.getElementById('assigneeFilter');
  if (assigneeFilter) {
    assigneeFilter.addEventListener('change', filterByAssignee);
  }
  
  // Edición inline
  $(document).on('click', '.editable', function() {
    const element = $(this);
    const field = element.data('field');
    const batchId = element.data('id');
    const currentValue = element.text().trim();
    
    enableInlineEdit(element, field, batchId, currentValue);
  });
}

// Filtrar por responsable
function filterByAssignee() {
  const filter = document.getElementById('assigneeFilter').value;
  currentFilter = filter;
  
  if (filter === '' || filter === 'all') {
    dataTable.search('').draw();
  } else {
    dataTable.column(1).search(filter).draw();
  }
  
  // Actualizar métricas filtradas
  const filteredData = dataTable.rows({ search: 'applied' }).data().toArray();
  const metrics = calculateMetrics(filteredData);
  updateMetricsDisplay(metrics);
}

// Habilitar edición inline
function enableInlineEdit(element, field, batchId, currentValue) {
  element.addClass('editing');
  
  let input;
  if (field === 'status') {
    input = $(`
      <select class="form-control form-control-sm">
        <option value="NS" ${currentValue.includes('Pendiente') ? 'selected' : ''}>Pendiente</option>
        <option value="FS" ${currentValue.includes('Parcial') ? 'selected' : ''}>Parcial</option>
        <option value="S" ${currentValue.includes('Segmentado') ? 'selected' : ''}>Segmentado</option>
      </select>
    `);
  } else {
    input = $(`<input type="text" class="form-control form-control-sm" value="${currentValue}">`);
  }
  
  element.html(input);
  input.focus();
  
  // Guardar al perder foco o presionar Enter
  input.on('blur keypress', function(e) {
    if (e.type === 'blur' || e.which === 13) {
      const newValue = $(this).val();
      saveInlineEdit(element, field, batchId, newValue, currentValue);
    }
  });
  
  // Cancelar con Escape
  input.on('keypress', function(e) {
    if (e.which === 27) {
      cancelInlineEdit(element, currentValue);
    }
  });
}

// Guardar edición inline
async function saveInlineEdit(element, field, batchId, newValue, oldValue) {
  if (newValue === oldValue) {
    cancelInlineEdit(element, oldValue);
    return;
  }
  
  try {
    const updateData = {};
    updateData[field] = newValue;
    
    const response = await fetch(`/api/batches/${batchId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData)
    });
    
    if (response.ok) {
      // Actualizar display
      if (field === 'status') {
        const statusClass = getStatusClass(newValue);
        const statusText = getStatusText(newValue);
        element.removeClass('editing').removeClass().addClass(`status-badge ${statusClass} editable`).text(statusText);
      } else {
        element.removeClass('editing').text(newValue);
      }
      
      // Actualizar datos locales
      const batchIndex = batchesData.findIndex(b => b.id === batchId);
      if (batchIndex !== -1) {
        if (field === 'due_date') {
          batchesData[batchIndex].metadata = batchesData[batchIndex].metadata || {};
          batchesData[batchIndex].metadata.due_date = newValue;
        } else {
          batchesData[batchIndex][field] = newValue;
        }
      }
      
      showNotification('Batch actualizado correctamente', 'success');
      loadMetrics(); // Actualizar métricas
    } else {
      throw new Error('Error actualizando batch');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error actualizando batch', 'error');
    cancelInlineEdit(element, oldValue);
  }
}

// Cancelar edición inline
function cancelInlineEdit(element, originalValue) {
  element.removeClass('editing').text(originalValue);
}

// Editar batch (modal)
function editBatch(batchId) {
  // Implementar modal de edición completa
  showNotification('Función de edición completa próximamente', 'info');
}

// Eliminar batch
async function deleteBatch(batchId) {
  if (!confirm('¿Estás seguro de que quieres eliminar este batch?')) {
    return;
  }
  
  try {
    const response = await fetch(`/api/batches/${batchId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      showNotification('Batch eliminado correctamente', 'success');
      await loadBatches();
      dataTable.clear().rows.add(batchesData).draw();
      loadMetrics();
    } else {
      throw new Error('Error eliminando batch');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error eliminando batch', 'error');
  }
}

// Crear nuevo batch
function createNewBatch() {
  // Implementar modal de creación
  showNotification('Función de creación próximamente', 'info');
}
