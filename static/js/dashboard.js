/**
 * Dashboard Segmentación Presencia - JavaScript
 * Sistema con autenticación y gestión de máscaras
 */

// ============================================
// VARIABLES GLOBALES
// ============================================
let currentUser = null;
let mascarasData = [];
let currentPage = 1;
let totalPages = 1;
const itemsPerPage = 25;

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', function() {
  console.log('🚀 Dashboard Segmentación Presencia inicializado');
  checkSession();
  setupEventListeners();
});

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
  // Login
  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }

  // Logout
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }

  // Botón agregar máscara
  const addBtn = document.getElementById('addMascaraBtn');
  if (addBtn) {
    addBtn.addEventListener('click', () => {
      alert('Funcionalidad de agregar máscara por implementar');
    });
  }
}

async function handleLogin(e) {
  e.preventDefault();

  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  const errorDiv = document.getElementById('loginError');

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
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

  // Actualizar UI con datos de usuario
  document.getElementById('userDisplay').textContent = currentUser.nombre_completo;
  document.getElementById('roleDisplay').textContent = currentUser.rol.toUpperCase();

  // Cargar datos
  loadStats();
  loadMascaras();
}

// ============================================
// CARGAR ESTADÍSTICAS
// ============================================
async function loadStats() {
  try {
    const response = await fetch('/api/stats');
    const stats = await response.json();

    if (response.ok) {
      document.getElementById('totalMascaras').textContent = stats.total_mascaras || 0;
      document.getElementById('mascarasAprobadas').textContent = stats.mascaras_aprobadas || 0;
      document.getElementById('mascarasPendientes').textContent = stats.mascaras_pendientes || 0;
      document.getElementById('mascarasListasIA').textContent = stats.mascaras_listas_entrenar || 0;
    } else {
      console.error('Error cargando estadísticas:', stats.error);
    }
  } catch (error) {
    console.error('❌ Error cargando estadísticas:', error);
  }
}

// ============================================
// CARGAR MÁSCARAS
// ============================================
async function loadMascaras(page = 1) {
  try {
    showLoading();

    const response = await fetch(`/api/mascaras?page=${page}&per_page=${itemsPerPage}`);
    const data = await response.json();

    if (response.ok) {
      mascarasData = data.mascaras || [];
      currentPage = data.page || 1;
      totalPages = data.total_pages || 1;

      console.log(`📊 Máscaras cargadas: ${mascarasData.length} de ${data.total}`);

      if (mascarasData.length === 0) {
        showEmptyState();
      } else {
        renderMascarasTable();
      }
    } else {
      console.error('Error cargando máscaras:', data.error);
      showEmptyState();
    }
  } catch (error) {
    console.error('❌ Error cargando máscaras:', error);
    showEmptyState();
  }
}

// ============================================
// RENDERIZAR TARJETAS DE MÁSCARAS
// ============================================
function renderMascarasTable() {
  const grid = document.getElementById('mascarasGrid');
  grid.innerHTML = '';

  mascarasData.forEach(mascara => {
    const card = createMascaraCard(mascara);
    grid.appendChild(card);
  });

  // Mostrar grid y ocultar estados de carga
  document.getElementById('loadingSpinner').style.display = 'none';
  document.getElementById('emptyState').classList.add('hidden');
  document.getElementById('cardsContainer').classList.remove('hidden');
}

function createMascaraCard(mascara) {
  // Crear columna Bootstrap
  const col = document.createElement('div');
  col.className = 'col-12 col-md-6 col-lg-4 col-xl-3';

  // Crear tarjeta
  const card = document.createElement('div');
  card.className = 'mascara-card';

  // Imagen o placeholder
  const imgContainer = document.createElement('div');
  if (mascara.imagen_url) {
    const img = document.createElement('img');
    img.src = mascara.imagen_url;
    img.className = 'card-img-top';
    img.alt = mascara.mascara_id;
    imgContainer.appendChild(img);
  } else {
    imgContainer.className = 'card-img-placeholder';
    imgContainer.innerHTML = '<i class="fas fa-mask"></i>';
  }
  card.appendChild(imgContainer);

  // Cuerpo de la tarjeta
  const cardBody = document.createElement('div');
  cardBody.className = 'card-body';

  // Título
  const title = document.createElement('h5');
  title.className = 'card-title';
  title.innerHTML = `<i class="fas fa-id-badge"></i> ${mascara.mascara_id || 'N/A'}`;
  cardBody.appendChild(title);

  // Información
  const infoRows = [
    { label: 'Operador', value: mascara.operador || 'Sin asignar', icon: 'fa-user' },
    { label: 'Estado', value: getEstadoBadge(mascara.estado), icon: 'fa-info-circle', isHtml: true },
    { label: 'Revisión', value: getRevisionBadge(mascara.review_status), icon: 'fa-clipboard-check', isHtml: true },
    { label: 'Entrenado', value: getEntrenadoBadge(mascara.entrenado), icon: 'fa-robot', isHtml: true },
    { label: 'Fecha', value: formatDate(mascara.fecha_creacion), icon: 'fa-calendar' }
  ];

  infoRows.forEach(row => {
    const infoRow = document.createElement('div');
    infoRow.className = 'info-row';

    const label = document.createElement('span');
    label.className = 'info-label';
    label.innerHTML = `<i class="fas ${row.icon}"></i> ${row.label}`;

    const value = document.createElement('span');
    value.className = 'info-value';
    if (row.isHtml) {
      value.innerHTML = row.value;
    } else {
      value.textContent = row.value;
    }

    infoRow.appendChild(label);
    infoRow.appendChild(value);
    cardBody.appendChild(infoRow);
  });

  card.appendChild(cardBody);

  // Footer con botones
  const cardFooter = document.createElement('div');
  cardFooter.className = 'card-footer';

  // Botón Ver
  const btnVer = document.createElement('button');
  btnVer.className = 'btn btn-sm btn-primary btn-action';
  btnVer.innerHTML = '<i class="fas fa-eye"></i> Ver';
  btnVer.onclick = () => viewMascaraDetails(mascara.mascara_id);
  cardFooter.appendChild(btnVer);

  // Botones de revisión (solo admin y supervisor)
  if (currentUser && (currentUser.rol === 'admin' || currentUser.rol === 'supervisor')) {
    if (mascara.review_status !== 'aprobado') {
      const btnAprobar = document.createElement('button');
      btnAprobar.className = 'btn btn-sm btn-success btn-action';
      btnAprobar.innerHTML = '<i class="fas fa-check"></i> Aprobar';
      btnAprobar.onclick = () => revisarMascara(mascara.mascara_id, 'aprobado');
      cardFooter.appendChild(btnAprobar);
    }

    if (mascara.review_status !== 'rechazado') {
      const btnRechazar = document.createElement('button');
      btnRechazar.className = 'btn btn-sm btn-danger btn-action';
      btnRechazar.innerHTML = '<i class="fas fa-times"></i> Rechazar';
      btnRechazar.onclick = () => revisarMascara(mascara.mascara_id, 'rechazado');
      cardFooter.appendChild(btnRechazar);
    }
  }

  card.appendChild(cardFooter);
  col.appendChild(card);

  return col;
}

function getEstadoBadge(estado) {
  return `<span class="badge bg-secondary">${estado || 'Pendiente'}</span>`;
}

function getRevisionBadge(reviewStatus) {
  if (reviewStatus === 'aprobado') {
    return '<span class="badge bg-success">Aprobado</span>';
  } else if (reviewStatus === 'rechazado') {
    return '<span class="badge bg-danger">Rechazado</span>';
  } else {
    return '<span class="badge bg-warning">Pendiente</span>';
  }
}

function getEntrenadoBadge(entrenado) {
  if (entrenado) {
    return '<span class="badge bg-success"><i class="fas fa-check"></i> Sí</span>';
  } else {
    return '<span class="badge bg-secondary"><i class="fas fa-times"></i> No</span>';
  }
}

// ============================================
// FUNCIONES DE ACCIÓN
// ============================================
async function revisarMascara(mascaraId, reviewStatus) {
  const accion = reviewStatus === 'aprobado' ? 'aprobar' : 'rechazar';

  if (!confirm(`¿Estás seguro de ${accion} la máscara ${mascaraId}?`)) {
    return;
  }

  try {
    const response = await fetch(`/api/mascaras/${mascaraId}/revisar`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ review_status: reviewStatus })
    });

    const result = await response.json();

    if (response.ok) {
      console.log(`✅ Máscara ${reviewStatus}:`, result);
      // Recargar datos
      await loadMascaras(currentPage);
      await loadStats();
    } else {
      console.error(`Error al ${accion}:`, result.error);
      alert(result.error || `Error al ${accion} la máscara`);
    }
  } catch (error) {
    console.error(`❌ Error al ${accion}:`, error);
    alert(`Error al ${accion} la máscara`);
  }
}

function viewMascaraDetails(mascaraId) {
  console.log('Ver detalles de máscara:', mascaraId);
  alert(`Detalles de máscara ${mascaraId}\n(Funcionalidad por implementar)`);
}

// ============================================
// FUNCIONES DE UTILIDAD
// ============================================
function formatDate(dateString) {
  if (!dateString) return 'N/A';

  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    return dateString;
  }
}

function showLoading() {
  document.getElementById('loadingSpinner').style.display = 'flex';
  document.getElementById('emptyState').classList.add('hidden');
  document.getElementById('cardsContainer').classList.add('hidden');
}

function showEmptyState() {
  document.getElementById('loadingSpinner').style.display = 'none';
  document.getElementById('emptyState').classList.remove('hidden');
  document.getElementById('cardsContainer').classList.add('hidden');
}

// ============================================
// EXPORTAR FUNCIONES GLOBALES
// ============================================
window.loadMascaras = loadMascaras;
window.loadStats = loadStats;
window.revisarMascara = revisarMascara;
