/* ===============================================
   JAVASCRIPT ESPECÍFICO PARA TEAM.HTML
   =============================================== */

// Variables globales para team
let teamMembers = [];

// Cargar miembros del equipo
async function loadTeamMembers() {
  showLoading();
  
  try {
    const response = await fetch('/api/segmentadores');
    const data = await response.json();
    
    if (data.success) {
      teamMembers = data.segmentadores;
      renderTeamGrid();
    } else {
      showNotification('Error cargando miembros del equipo', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error de conexión', 'error');
  } finally {
    hideLoading();
  }
}

// Renderizar grid de miembros
function renderTeamGrid() {
  const memberGrid = document.getElementById('memberGrid');
  if (!memberGrid) return;
  
  memberGrid.innerHTML = '';
  
  // Card para agregar nuevo miembro
  const addCard = document.createElement('div');
  addCard.className = 'add-member-card';
  addCard.onclick = () => showAddSegmentadorModal();
  addCard.innerHTML = `
    <div class="add-member-icon">
      <i class="fas fa-user-plus"></i>
    </div>
    <div class="add-member-text">
      Agregar Segmentador
    </div>
  `;
  memberGrid.appendChild(addCard);
  
  // Cards de miembros existentes
  teamMembers.forEach(member => {
    const memberCard = createMemberCard(member);
    memberGrid.appendChild(memberCard);
  });
}

// Crear card individual de miembro
function createMemberCard(memberName) {
  const card = document.createElement('div');
  card.className = 'member-card';
  card.ondblclick = () => window.location.href = `/dashboard/${memberName}`;
  
  card.innerHTML = `
    <button class="delete-member-btn" onclick="event.stopPropagation(); showDeleteConfirmation('${memberName}')">
      <i class="fas fa-trash"></i>
    </button>
    
    <div class="member-avatar">
      ${memberName.charAt(0).toUpperCase()}
    </div>
    
    <div class="member-name">${memberName}</div>
    <div class="member-role">Segmentador</div>
    
    <div class="member-stats">
      <div class="stat-item">
        <span class="stat-number" id="batches-${memberName}">-</span>
        <span class="stat-label">Batches</span>
      </div>
      <div class="stat-item">
        <span class="stat-number" id="completed-${memberName}">-</span>
        <span class="stat-label">Completados</span>
      </div>
    </div>
  `;
  
  return card;
}

// Cargar estadísticas de batches
async function loadMemberStats() {
  try {
    const response = await fetch('/api/batches');
    const batches = await response.json();
    
    // Contar batches por miembro
    const stats = {};
    teamMembers.forEach(member => {
      stats[member] = { total: 0, completed: 0 };
    });
    
    batches.forEach(batch => {
      if (stats[batch.assignee]) {
        stats[batch.assignee].total++;
        if (batch.status === 'S' || batch.status === 'completado') {
          stats[batch.assignee].completed++;
        }
      }
    });
    
    // Actualizar UI
    Object.entries(stats).forEach(([member, stat]) => {
      const totalElement = document.getElementById(`batches-${member}`);
      const completedElement = document.getElementById(`completed-${member}`);
      
      if (totalElement) totalElement.textContent = stat.total;
      if (completedElement) completedElement.textContent = stat.completed;
    });
    
  } catch (error) {
    console.error('Error cargando estadísticas:', error);
  }
}

// Mostrar modal para agregar segmentador
function showAddSegmentadorModal() {
  const modal = new bootstrap.Modal(document.getElementById('addSegmentadorModal'));
  modal.show();
}

// Agregar nuevo segmentador
async function addSegmentador() {
  const form = document.getElementById('addSegmentadorForm');
  const formData = new FormData(form);
  
  const segmentadorData = {
    name: formData.get('name'),
    role: formData.get('role') || 'Segmentador',
    email: formData.get('email') || ''
  };
  
  if (!segmentadorData.name.trim()) {
    showNotification('El nombre es requerido', 'warning');
    return;
  }
  
  showLoading();
  
  try {
    const response = await fetch('/api/add-segmentador', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(segmentadorData)
    });
    
    const result = await response.json();
    
    if (result.success) {
      showNotification(result.message, 'success');
      bootstrap.Modal.getInstance(document.getElementById('addSegmentadorModal')).hide();
      form.reset();
      await loadTeamMembers();
      await loadMemberStats();
    } else {
      showNotification(result.error, 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error agregando segmentador', 'error');
  } finally {
    hideLoading();
  }
}

// Mostrar confirmación de eliminación
function showDeleteConfirmation(memberName) {
  const modal = document.getElementById('deleteSegmentadorModal');
  const memberNameSpan = modal.querySelector('#memberToDelete');
  
  if (memberNameSpan) {
    memberNameSpan.textContent = memberName;
  }
  
  // Configurar botón de confirmación
  const confirmBtn = modal.querySelector('#confirmDeleteBtn');
  if (confirmBtn) {
    confirmBtn.onclick = () => confirmDeleteSegmentador(memberName);
  }
  
  new bootstrap.Modal(modal).show();
}

// Confirmar eliminación de segmentador
async function confirmDeleteSegmentador(memberName) {
  showLoading();
  
  try {
    const response = await fetch('/api/delete-segmentador', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: memberName })
    });
    
    const result = await response.json();
    
    if (result.success) {
      showNotification(result.message, 'success');
      bootstrap.Modal.getInstance(document.getElementById('deleteSegmentadorModal')).hide();
      await loadTeamMembers();
      await loadMemberStats();
    } else {
      showNotification(result.error, 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showNotification('Error eliminando segmentador', 'error');
  } finally {
    hideLoading();
  }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', async function() {
  await loadTeamMembers();
  await loadMemberStats();
});

// Funciones de utilidad específicas para team
function getRandomColor() {
  const colors = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
    'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',
    'linear-gradient(135deg, #ff8a80 0%, #ea6100 100%)'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}
