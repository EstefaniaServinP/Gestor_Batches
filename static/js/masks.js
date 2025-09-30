/* ===============================================
   FUNCIONALIDAD ESPECÍFICA PARA MASKS.HTML
   =============================================== */

// Variables globales
let masksTable;

// Inicialización cuando el DOM está listo
$(document).ready(function() {
  initializeMasksTable();
  setupFilters();
  setupVisualEffects();
  updateResultsInfo();
});

// Inicializar DataTable con configuración específica para máscaras
function initializeMasksTable() {
  masksTable = $('#masksTable').DataTable({
    responsive: true,
    pageLength: 25,
    language: {
      url: 'https://cdn.datatables.net/plug-ins/1.13.4/i18n/es-ES.json'
    },
    order: [[1, 'desc']], // Ordenar por fecha descendente
    dom: '<"row"<"col-sm-6"l><"col-sm-6">>' +  // Ocultar búsqueda default
         '<"row"<"col-sm-12"tr>>' +
         '<"row"<"col-sm-5"i><"col-sm-7"p>>',
    drawCallback: function() {
      // Aplicar efectos después de cada redibujado
      $('.table tbody tr').hover(
        function() { 
          $(this).addClass('pulse');
        },
        function() { 
          $(this).removeClass('pulse');
        }
      );
    },
    initComplete: function() {
      console.log('Tabla de máscaras inicializada correctamente');
      showNotification('Tabla de máscaras cargada', 'success');
    }
  });
}

// Configurar filtros personalizados
function setupFilters() {
  // Filtro por nombre (columna 0)
  $('#nameFilter').on('keyup', function() {
    const value = this.value;
    masksTable.column(0).search(value).draw();
    updateResultsInfo();
    
    // Mostrar indicador visual de filtro activo
    if (value) {
      $(this).addClass('filter-active');
    } else {
      $(this).removeClass('filter-active');
    }
  });
  
  // Filtro por fecha (columna 1)
  $('#dateFilter').on('keyup', function() {
    const value = this.value;
    masksTable.column(1).search(value).draw();
    updateResultsInfo();
    
    // Mostrar indicador visual de filtro activo
    if (value) {
      $(this).addClass('filter-active');
    } else {
      $(this).removeClass('filter-active');
    }
  });
  
  // Limpiar filtros con Escape
  $('.filter-input').on('keydown', function(e) {
    if (e.key === 'Escape') {
      $(this).val('').trigger('keyup');
    }
  });
}

// Configurar efectos visuales
function setupVisualEffects() {
  // Efectos para los filtros
  $('.filter-input').on('focus', function() {
    $(this).closest('.filter-group').addClass('pulse');
  }).on('blur', function() {
    $(this).closest('.filter-group').removeClass('pulse');
  });
  
  // Efectos para las filas de la tabla
  $('.table tbody tr').on('mouseenter', function() {
    $(this).addClass('table-row-hover');
  }).on('mouseleave', function() {
    $(this).removeClass('table-row-hover');
  });
}

// Función para toggle de filtros
function toggleFilters() {
  const filtersContent = document.getElementById('filtersContent');
  const toggleBtn = document.querySelector('.filter-toggle-btn');
  
  if (filtersContent.classList.contains('show')) {
    // Cerrar filtros
    filtersContent.classList.remove('show');
    toggleBtn.classList.remove('active');
  } else {
    // Abrir filtros
    filtersContent.classList.add('show');
    toggleBtn.classList.add('active');
    
    // Enfocar el primer campo después de un pequeño delay
    setTimeout(() => {
      document.getElementById('nameFilter').focus();
    }, 200);
  }
}

// Función para actualizar información de resultados
function updateResultsInfo() {
  if (!masksTable) return;
  
  const info = masksTable.page.info();
  const totalRecords = info.recordsTotal;
  const filteredRecords = info.recordsDisplay;
  
  if (filteredRecords !== totalRecords) {
    // Crear notificación de filtro activo
    showFilterNotification(`Mostrando ${filteredRecords} de ${totalRecords} máscaras`);
  } else {
    // Remover notificación si no hay filtros
    $('.filter-notification').fadeOut(300, function() {
      $(this).remove();
    });
  }
  
  // Actualizar título con conteo
  updatePageTitle(filteredRecords, totalRecords);
}

// Actualizar título de página con información de conteo
function updatePageTitle(filtered, total) {
  const titleElement = document.querySelector('.title-section h1');
  const originalTitle = '<i class="fas fa-image"></i> Dashboard de Máscaras MongoDB';
  
  if (filtered !== total) {
    titleElement.innerHTML = `${originalTitle} (${filtered}/${total})`;
  } else {
    titleElement.innerHTML = `${originalTitle} (${total})`;
  }
}

// Función para mostrar notificaciones de filtro
function showFilterNotification(message) {
  // Remover notificación anterior si existe
  $('.filter-notification').remove();
  
  const notification = $(`
    <div class="filter-notification">
      <i class="fas fa-filter"></i> ${message}
    </div>
  `);
  
  $('body').append(notification);
  
  // Auto-remover después de 3 segundos
  setTimeout(() => {
    notification.fadeOut(300, function() {
      $(this).remove();
    });
  }, 3000);
}

// Función para mostrar notificaciones generales
function showNotification(message, type = 'info') {
  const icons = {
    success: 'fas fa-check-circle',
    error: 'fas fa-exclamation-circle',
    warning: 'fas fa-exclamation-triangle',
    info: 'fas fa-info-circle'
  };
  
  const colors = {
    success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    error: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    warning: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
    info: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
  };
  
  const notification = $(`
    <div class="general-notification">
      <i class="${icons[type]}"></i> ${message}
    </div>
  `);
  
  notification.css({
    position: 'fixed',
    top: '20px',
    right: '20px',
    background: colors[type],
    color: 'white',
    padding: '1rem 1.5rem',
    borderRadius: '10px',
    fontSize: '0.9rem',
    fontWeight: '600',
    zIndex: '1002',
    backdropFilter: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
    animation: 'slideInDown 0.3s ease'
  });
  
  $('body').append(notification);
  
  // Auto-remover después de 4 segundos
  setTimeout(() => {
    notification.fadeOut(400, function() {
      $(this).remove();
    });
  }, 4000);
}

// Búsqueda rápida con atajo de teclado
function setupKeyboardShortcuts() {
  $(document).keydown(function(e) {
    // Ctrl+F para enfocar filtro de nombre
    if (e.ctrlKey && e.key === 'f') {
      e.preventDefault();
      $('#nameFilter').focus();
      
      // Abrir filtros si están cerrados
      const filtersContent = document.getElementById('filtersContent');
      if (!filtersContent.classList.contains('show')) {
        toggleFilters();
      }
    }
    
    // Ctrl+D para enfocar filtro de fecha
    if (e.ctrlKey && e.key === 'd') {
      e.preventDefault();
      $('#dateFilter').focus();
      
      // Abrir filtros si están cerrados
      const filtersContent = document.getElementById('filtersContent');
      if (!filtersContent.classList.contains('show')) {
        toggleFilters();
      }
    }
    
    // Escape para limpiar todos los filtros
    if (e.key === 'Escape') {
      clearAllFilters();
    }
  });
}

// Limpiar todos los filtros
function clearAllFilters() {
  $('#nameFilter').val('').removeClass('filter-active');
  $('#dateFilter').val('').removeClass('filter-active');
  
  if (masksTable) {
    masksTable.search('').columns().search('').draw();
    updateResultsInfo();
  }
  
  showNotification('Filtros limpiados', 'info');
}

// Exportar datos de máscaras
function exportMasksData() {
  if (!masksTable) return;
  
  const data = masksTable.rows({ search: 'applied' }).data().toArray();
  const csvContent = convertToCSV(data);
  
  // Crear enlace de descarga
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `mascaras_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('Datos exportados correctamente', 'success');
  }
}

// Convertir datos a formato CSV
function convertToCSV(data) {
  const headers = ['Nombre de Archivo', 'Fecha de Subida', 'Estado'];
  const csvRows = [headers.join(',')];
  
  data.forEach(row => {
    // Limpiar datos HTML para CSV
    const cleanRow = Array.from(row).map(cell => {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = cell;
      return tempDiv.textContent || tempDiv.innerText || '';
    });
    csvRows.push(cleanRow.join(','));
  });
  
  return csvRows.join('\n');
}

// Estadísticas de máscaras
function generateMasksStats() {
  if (!masksTable) return;
  
  const info = masksTable.page.info();
  const totalMasks = info.recordsTotal;
  const visibleMasks = info.recordsDisplay;
  
  // Contar estados
  let activeCount = 0;
  let warningCount = 0;
  
  masksTable.rows({ search: 'applied' }).every(function() {
    const data = this.data();
    const statusCell = data[2]; // Columna de estado
    
    if (statusCell.includes('bg-success')) {
      activeCount++;
    } else if (statusCell.includes('bg-warning')) {
      warningCount++;
    }
  });
  
  // Mostrar estadísticas
  const stats = {
    total: totalMasks,
    visible: visibleMasks,
    active: activeCount,
    warning: warningCount
  };
  
  console.log('Estadísticas de máscaras:', stats);
  return stats;
}

// Inicializar funcionalidades adicionales cuando la página está completamente cargada
window.addEventListener('load', function() {
  setupKeyboardShortcuts();
  
  // Mostrar consejos de uso
  setTimeout(() => {
    showNotification('Tip: Usa Ctrl+F para buscar por nombre, Ctrl+D para fecha', 'info');
  }, 2000);
  
  // Animación de entrada
  setTimeout(() => {
    const masksCard = document.querySelector('.masks-card');
    if (masksCard) {
      masksCard.style.opacity = '1';
      masksCard.style.transform = 'translateY(0)';
    }
  }, 100);
});

// Agregar CSS dinámico para animaciones
const dynamicStyles = `
  .filter-active {
    border-color: #B794F6 !important;
    box-shadow: 0 0 0 2px rgba(183, 148, 246, 0.3) !important;
    background: rgba(183, 148, 246, 0.1) !important;
  }
  
  .table-row-hover {
    background: linear-gradient(135deg, rgba(183, 148, 246, 0.15) 0%, rgba(246, 135, 179, 0.15) 100%) !important;
    transform: scale(1.01) !important;
  }
  
  @keyframes slideInDown {
    from {
      opacity: 0;
      transform: translateY(-30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

// Inyectar estilos dinámicos
const styleSheet = document.createElement('style');
styleSheet.textContent = dynamicStyles;
document.head.appendChild(styleSheet);
