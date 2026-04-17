/**
 * Dashboard Segmentación Presencia - JavaScript
 * Vista de Equipo de Segmentación con tarjetas de miembros
 */

// ============================================
// VARIABLES GLOBALES
// ============================================
let currentUser = null;
let teamMembers = [];
let selectedMember = null;

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', function() {
  console.log('Dashboard Segmentación Presencia inicializado');
  loadTheme();
  checkSession();
  setupEventListeners();
});

// ============================================
// TEMA CLARO / OSCURO
// ============================================
function loadTheme() {
  const saved = localStorage.getItem('theme');
  if (saved === 'light') {
    document.body.classList.add('light-mode');
    updateThemeUI(true);
  }
}

function toggleTheme() {
  const isLight = document.body.classList.toggle('light-mode');
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
  updateThemeUI(isLight);
}

function updateThemeUI(isLight) {
  const icon = document.getElementById('themeIcon');
  const label = document.getElementById('themeLabel');
  if (isLight) {
    icon.className = 'fas fa-moon';
    label.textContent = 'Modo Oscuro';
  } else {
    icon.className = 'fas fa-sun';
    label.textContent = 'Modo Claro';
  }
}

// ============================================
// AUTENTICACIÓN
// ============================================
async function checkSession() {
  try {
    const response = await fetch('/api/session');
    const data = await response.json();

    if (data.autenticado) {
      currentUser = data.usuario;
      showDashboard();
    } else {
      showLogin();
    }
  } catch (error) {
    console.error('Error verificando sesión:', error);
    showLogin();
  }
}

function setupEventListeners() {
  const loginForm = document.getElementById('loginForm');
  if (loginForm) loginForm.addEventListener('submit', handleLogin);

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);

  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) themeToggle.addEventListener('click', toggleTheme);

  const closePanelBtn = document.getElementById('closePanelBtn');
  if (closePanelBtn) closePanelBtn.addEventListener('click', closeBatchesPanel);

  const saveMemberBtn = document.getElementById('saveMemberBtn');
  if (saveMemberBtn) saveMemberBtn.addEventListener('click', saveNewMember);

  const createBatchBtn = document.getElementById('createBatchBtn');
  if (createBatchBtn) createBatchBtn.addEventListener('click', () => {
    loadOperadoresSelect();
    new bootstrap.Modal(document.getElementById('createBatchModal')).show();
  });

  const generateBatchBtn = document.getElementById('generateBatchBtn');
  if (generateBatchBtn) generateBatchBtn.addEventListener('click', generateBatch);

  const importBatchFile = document.getElementById('importBatchFile');
  if (importBatchFile) importBatchFile.addEventListener('change', importBatch);
}

async function handleLogin(e) {
  e.preventDefault();

  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const errorDiv = document.getElementById('loginError');

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (response.ok) {
      currentUser = data.usuario;
      errorDiv.classList.add('hidden');
      showDashboard();
    } else {
      errorDiv.textContent = data.error || 'Error en login';
      errorDiv.classList.remove('hidden');
    }
  } catch (error) {
    console.error('Error en login:', error);
    errorDiv.textContent = 'Error de conexión';
    errorDiv.classList.remove('hidden');
  }
}

async function handleLogout() {
  try {
    await fetch('/api/logout', { method: 'POST' });
    currentUser = null;
    selectedMember = null;
    showLogin();
  } catch (error) {
    console.error('Error en logout:', error);
  }
}

function showLogin() {
  document.getElementById('loginScreen').classList.remove('hidden');
  document.getElementById('dashboardScreen').classList.add('hidden');
}

function showDashboard() {
  document.getElementById('loginScreen').classList.add('hidden');
  document.getElementById('dashboardScreen').classList.remove('hidden');

  document.getElementById('userDisplay').textContent = currentUser.nombre_completo;
  document.getElementById('roleDisplay').textContent = currentUser.rol.toUpperCase();

  // Mostrar herramientas de batch para admin/supervisor
  const rol = currentUser.rol;
  if (rol === 'admin' || rol === 'supervisor') {
    document.getElementById('batchTools').classList.remove('hidden');
  }

  loadTeamMembers();
}

// ============================================
// CARGAR MIEMBROS DEL EQUIPO
// ============================================
async function loadTeamMembers() {
  try {
    const res = await fetch('/api/usuarios');
    if (!res.ok) {
      // Si no tiene permisos (operador), mostrar solo su propia tarjeta
      teamMembers = [{
        username: currentUser.username,
        nombre_completo: currentUser.nombre_completo,
        rol: currentUser.rol,
        email: currentUser.email || '',
        activo: true
      }];
      renderTeamGrid();
      return;
    }

    const users = await res.json();
    teamMembers = users.filter(u => u.activo);
    renderTeamGrid();
  } catch (e) {
    console.error('Error cargando equipo:', e);
  }
}

// ============================================
// RENDERIZAR GRID DE EQUIPO
// ============================================
function renderTeamGrid() {
  const grid = document.getElementById('teamGrid');
  grid.innerHTML = '';

  teamMembers.forEach(member => {
    const card = createTeamCard(member);
    grid.appendChild(card);
  });

  // Tarjeta "Agregar Nuevo Segmentador" (solo admin/supervisor)
  if (currentUser.rol === 'admin' || currentUser.rol === 'supervisor') {
    const addCard = document.createElement('div');
    addCard.className = 'team-card add-card';
    addCard.innerHTML = `
      <div class="add-icon"><i class="fas fa-plus"></i></div>
      <div class="add-label">Agregar Nuevo Segmentador</div>
    `;
    addCard.addEventListener('click', () => {
      new bootstrap.Modal(document.getElementById('addMemberModal')).show();
    });
    grid.appendChild(addCard);
  }
}

function createTeamCard(member) {
  const card = document.createElement('div');
  card.className = 'team-card';

  const initials = getInitials(member.nombre_completo);
  const rolLabel = getRolLabel(member.rol);

  card.innerHTML = `
    <div class="avatar">${initials}</div>
    <div class="member-name">${member.nombre_completo}</div>
    <div class="member-role">${rolLabel}</div>
    <div class="member-stats">
      <i class="fas fa-at"></i> ${member.username}
    </div>
  `;

  // Doble clic para ver batches
  card.addEventListener('dblclick', () => {
    openBatchesPanel(member);
  });

  return card;
}

function getInitials(name) {
  if (!name) return '?';
  const parts = name.split(' ').filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return parts[0].substring(0, 2).toUpperCase();
}

function getRolLabel(rol) {
  const map = {
    admin: 'Administrador',
    supervisor: 'Supervisor',
    operador: 'Operador'
  };
  return map[rol] || rol;
}

// ============================================
// PANEL DE BATCHES (al hacer doble clic)
// ============================================
async function openBatchesPanel(member) {
  selectedMember = member;
  document.getElementById('panelMemberName').textContent = member.nombre_completo;

  const panel = document.getElementById('batchesPanel');
  const emptyDiv = document.getElementById('panelBatchesEmpty');
  const tableDiv = document.getElementById('panelBatchesTable');

  panel.classList.remove('hidden');
  emptyDiv.classList.add('hidden');
  tableDiv.classList.add('hidden');

  try {
    const res = await fetch(`/api/batches?assignee_id=${encodeURIComponent(member.username)}`);
    const data = await res.json();

    if (!data.success || data.batches.length === 0) {
      emptyDiv.classList.remove('hidden');
      return;
    }

    renderPanelBatches(data.batches);
    tableDiv.classList.remove('hidden');
  } catch (e) {
    console.error('Error cargando batches del miembro:', e);
    emptyDiv.classList.remove('hidden');
  }

  // Scroll al panel
  panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeBatchesPanel() {
  document.getElementById('batchesPanel').classList.add('hidden');
  selectedMember = null;
}

function renderPanelBatches(batches) {
  const tbody = document.getElementById('panelBatchesBody');
  tbody.innerHTML = '';

  batches.forEach(b => {
    const pct = b.total_items > 0 ? Math.round((b.completed_items / b.total_items) * 100) : 0;
    const statusBadge = getBatchStatusBadge(b.status);

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><code style="color:var(--accent)">${b.batch_id}</code></td>
      <td>${b.total_items}</td>
      <td>${b.completed_items}</td>
      <td>
        <div class="d-flex align-items-center gap-2">
          <div class="progress flex-grow-1">
            <div class="progress-bar bg-success" style="width:${pct}%"></div>
          </div>
          <small>${pct}%</small>
        </div>
      </td>
      <td>${statusBadge}</td>
      <td>${formatDate(b.created_at)}</td>
      <td>
        <button class="btn btn-sm btn-outline-light" onclick="downloadBatchJson('${b.batch_id}')" title="Descargar JSON">
          <i class="fas fa-download"></i>
        </button>
      </td>`;
    tbody.appendChild(tr);
  });
}

function getBatchStatusBadge(status) {
  const map = {
    assigned: '<span class="badge bg-warning">Asignado</span>',
    in_progress: '<span class="badge bg-info">En Progreso</span>',
    completed: '<span class="badge bg-success">Completado</span>'
  };
  return map[status] || `<span class="badge bg-secondary">${status}</span>`;
}

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    });
  } catch (e) {
    return dateString;
  }
}

// ============================================
// AGREGAR NUEVO SEGMENTADOR
// ============================================
async function saveNewMember() {
  const nombre = document.getElementById('newMemberNombre').value.trim();
  const username = document.getElementById('newMemberUsername').value.trim();
  const password = document.getElementById('newMemberPassword').value;
  const email = document.getElementById('newMemberEmail').value.trim();
  const rol = document.getElementById('newMemberRol').value;
  const errorDiv = document.getElementById('addMemberError');

  if (!nombre || !username || !password) {
    errorDiv.textContent = 'Nombre, username y contraseña son requeridos';
    errorDiv.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/usuarios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nombre_completo: nombre,
        username: username,
        password: password,
        email: email,
        rol: rol
      })
    });

    const data = await res.json();

    if (res.ok) {
      errorDiv.classList.add('hidden');
      bootstrap.Modal.getInstance(document.getElementById('addMemberModal')).hide();

      // Limpiar formulario
      document.getElementById('newMemberNombre').value = '';
      document.getElementById('newMemberUsername').value = '';
      document.getElementById('newMemberPassword').value = '';
      document.getElementById('newMemberEmail').value = '';
      document.getElementById('newMemberRol').value = 'operador';

      // Recargar equipo
      loadTeamMembers();
    } else {
      errorDiv.textContent = data.error || 'Error al crear usuario';
      errorDiv.classList.remove('hidden');
    }
  } catch (e) {
    console.error('Error creando miembro:', e);
    errorDiv.textContent = 'Error de conexión';
    errorDiv.classList.remove('hidden');
  }
}

// ============================================
// BATCHES - CREAR / IMPORTAR / DESCARGAR
// ============================================

async function loadOperadoresSelect() {
  try {
    const res = await fetch('/api/usuarios');
    const users = await res.json();
    const select = document.getElementById('batchAssigneeSelect');
    if (!select) return;
    select.innerHTML = '';
    users.filter(u => u.activo).forEach(u => {
      const opt = document.createElement('option');
      opt.value = u.username;
      opt.textContent = `${u.nombre_completo} (${u.rol})`;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error('Error cargando operadores:', e);
  }
}

async function generateBatch() {
  const assignee = document.getElementById('batchAssigneeSelect').value;
  const rawIds = document.getElementById('batchMascaraIds').value;
  const mascara_ids = rawIds.split(/[\s,]+/).map(s => s.trim()).filter(Boolean);
  const errorDiv = document.getElementById('createBatchError');

  if (!assignee || mascara_ids.length === 0) {
    errorDiv.textContent = 'Selecciona un operador e ingresa al menos un ID de máscara';
    errorDiv.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch('/api/batches/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ assignee_user_id: assignee, mascara_ids })
    });

    const data = await res.json();

    if (res.ok) {
      // Descargar JSON
      const blob = new Blob([JSON.stringify(data.batch, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${data.batch.batch_id}.json`;
      a.click();
      URL.revokeObjectURL(url);

      // Cerrar modal y limpiar
      errorDiv.classList.add('hidden');
      document.getElementById('batchMascaraIds').value = '';
      bootstrap.Modal.getInstance(document.getElementById('createBatchModal')).hide();

      // Refrescar panel si está abierto
      if (selectedMember && selectedMember.username === assignee) {
        openBatchesPanel(selectedMember);
      }
    } else {
      errorDiv.textContent = data.error || 'Error al generar batch';
      errorDiv.classList.remove('hidden');
    }
  } catch (e) {
    console.error('Error generando batch:', e);
    errorDiv.textContent = 'Error de conexión';
    errorDiv.classList.remove('hidden');
  }
}

async function importBatch(e) {
  const file = e.target.files[0];
  if (!file) return;

  try {
    const text = await file.text();
    const jsonData = JSON.parse(text);

    const res = await fetch('/api/batches/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(jsonData)
    });

    const data = await res.json();
    alert(data.message || (data.success ? 'Importado correctamente' : 'Error al importar'));

    if (data.success && selectedMember) {
      openBatchesPanel(selectedMember);
    }
  } catch (e) {
    console.error('Error importando batch:', e);
    alert('Error al leer o parsear el archivo JSON');
  }

  // Reset input
  document.getElementById('importBatchFile').value = '';
}

async function downloadBatchJson(batchId) {
  try {
    const res = await fetch(`/api/batches/${batchId}`);
    const batch = await res.json();
    delete batch._id;
    const blob = new Blob([JSON.stringify(batch, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${batchId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) {
    console.error('Error descargando batch:', e);
  }
}

// ============================================
// EXPORTAR FUNCIONES GLOBALES
// ============================================
window.downloadBatchJson = downloadBatchJson;
