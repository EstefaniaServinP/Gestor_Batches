/**
 * Segmentador - JavaScript
 * Herramienta de segmentación por batches para operadores
 */

// ============================================
// VARIABLES GLOBALES
// ============================================
let currentUser = null;
let currentBatch = null;

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', function() {
  console.log('Segmentador inicializado');
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
      showSegmentador();
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
  if (loginForm) {
    loginForm.addEventListener('submit', handleLogin);
  }

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
  }

  const loadBatchBtn = document.getElementById('loadBatchBtn');
  if (loadBatchBtn) {
    loadBatchBtn.addEventListener('click', () => {
      const batchId = document.getElementById('batchSelect').value;
      if (batchId) {
        loadBatch(batchId);
      } else {
        alert('Selecciona un batch primero');
      }
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (response.ok) {
      currentUser = data.usuario;
      errorDiv.classList.add('hidden');
      showSegmentador();
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
    currentBatch = null;
    showLogin();
  } catch (error) {
    console.error('Error en logout:', error);
  }
}

function showLogin() {
  document.getElementById('loginScreen').classList.remove('hidden');
  document.getElementById('segmentadorScreen').classList.add('hidden');
}

function showSegmentador() {
  document.getElementById('loginScreen').classList.add('hidden');
  document.getElementById('segmentadorScreen').classList.remove('hidden');

  document.getElementById('userDisplay').textContent = currentUser.nombre_completo;
  document.getElementById('roleDisplay').textContent = currentUser.rol.toUpperCase();

  loadMisBatches();
}

// ============================================
// CARGAR BATCHES DEL USUARIO
// ============================================
async function loadMisBatches() {
  try {
    const res = await fetch('/api/batches/mis-batches');
    const data = await res.json();

    const select = document.getElementById('batchSelect');
    select.innerHTML = '<option value="">-- Selecciona un batch --</option>';

    if (data.success && data.batches.length > 0) {
      data.batches.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.batch_id;
        const statusLabel = getStatusLabel(b.status);
        opt.textContent = `${b.batch_id} [${statusLabel}] - ${b.completed_items}/${b.total_items} máscaras`;
        select.appendChild(opt);
      });
    } else {
      select.innerHTML = '<option value="">-- No tienes batches asignados --</option>';
    }
  } catch (e) {
    console.error('Error cargando batches:', e);
  }
}

function getStatusLabel(status) {
  const map = {
    assigned: 'Asignado',
    in_progress: 'En Progreso',
    completed: 'Completado'
  };
  return map[status] || status;
}

// ============================================
// CARGAR UN BATCH ESPECÍFICO
// ============================================
async function loadBatch(batchId) {
  try {
    const res = await fetch(`/api/batches/${batchId}`);
    if (!res.ok) {
      const err = await res.json();
      alert(err.error || 'Error al cargar el batch');
      return;
    }

    currentBatch = await res.json();
    renderBatchInfo();
    renderMascarasList();

    document.getElementById('batchProgressCard').classList.remove('hidden');
    document.getElementById('mascarasSegCard').classList.remove('hidden');
  } catch (e) {
    console.error('Error cargando batch:', e);
    alert('Error de conexión al cargar el batch');
  }
}

// ============================================
// RENDERIZAR INFO DEL BATCH
// ============================================
function renderBatchInfo() {
  document.getElementById('batchIdDisplay').textContent = currentBatch.batch_id;
  document.getElementById('batchAssigneeDisplay').textContent = currentBatch.assignee.nombre;

  const statusBadge = getBatchStatusBadge(currentBatch.status);
  document.getElementById('batchStatusDisplay').innerHTML = statusBadge;

  updateProgressBar(currentBatch.completed_items, currentBatch.total_items);
}

function getBatchStatusBadge(status) {
  const map = {
    assigned: '<span class="badge bg-warning">Asignado</span>',
    in_progress: '<span class="badge bg-info">En Progreso</span>',
    completed: '<span class="badge bg-success">Completado</span>'
  };
  return map[status] || `<span class="badge bg-secondary">${status}</span>`;
}

function updateProgressBar(completed, total) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  const bar = document.getElementById('batchProgressBar');
  bar.style.width = pct + '%';
  bar.textContent = pct + '%';
  bar.setAttribute('aria-valuenow', pct);
  document.getElementById('batchCompletedCount').textContent = `${completed} / ${total}`;
}

// ============================================
// RENDERIZAR LISTA DE MÁSCARAS
// ============================================
function renderMascarasList() {
  const container = document.getElementById('mascarasSegList');
  container.innerHTML = '';

  currentBatch.mascaras.forEach((m, index) => {
    const row = buildMascaraRow(m, index);
    container.appendChild(row);
  });
}

function buildMascaraRow(mascara, index) {
  const row = document.createElement('div');
  row.className = `mascara-row status-${mascara.status}`;
  row.id = `mascara-row-${index}`;

  const statusOptions = ['pending', 'in_progress', 'completed', 'skipped'].map(s => {
    const labels = { pending: 'Pendiente', in_progress: 'En Progreso', completed: 'Completado', skipped: 'Omitido' };
    const selected = s === mascara.status ? 'selected' : '';
    return `<option value="${s}" ${selected}>${labels[s]}</option>`;
  }).join('');

  row.innerHTML = `
    <div class="row align-items-center">
      <div class="col-md-2">
        <strong class="d-block mb-1" style="color:var(--accent)">${mascara.mascara_id}</strong>
        <small class="text-secondary">#${index + 1} de ${currentBatch.total_items}</small>
      </div>
      <div class="col-md-2">
        <label class="form-label" style="font-size:0.75rem">Estado</label>
        <select class="form-select form-select-sm" id="status-${index}">
          ${statusOptions}
        </select>
      </div>
      <div class="col-md-3">
        <label class="form-label" style="font-size:0.75rem">
          Progreso: <span class="range-value" id="progress-val-${index}">${mascara.progress}%</span>
        </label>
        <input type="range" class="form-range" min="0" max="100" step="5"
               value="${mascara.progress}" id="progress-${index}"
               oninput="document.getElementById('progress-val-${index}').textContent = this.value + '%'">
      </div>
      <div class="col-md-3">
        <label class="form-label" style="font-size:0.75rem">Notas</label>
        <input type="text" class="form-control form-control-sm" id="notes-${index}"
               value="${mascara.segmentation_notes || ''}" placeholder="Notas...">
      </div>
      <div class="col-md-2 text-end">
        <button class="btn btn-sm btn-success mt-3" id="save-btn-${index}"
                onclick="saveMascara(${index}, '${mascara.mascara_id}')">
          <i class="fas fa-save"></i> Guardar
        </button>
      </div>
    </div>
  `;

  return row;
}

// ============================================
// GUARDAR PROGRESO DE MÁSCARA
// ============================================
async function saveMascara(index, mascaraId) {
  const btn = document.getElementById(`save-btn-${index}`);
  const status = document.getElementById(`status-${index}`).value;
  const progress = parseInt(document.getElementById(`progress-${index}`).value);
  const notes = document.getElementById(`notes-${index}`).value;

  // Deshabilitar botón mientras se guarda
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

  try {
    const res = await fetch(
      `/api/batches/${currentBatch.batch_id}/mascaras/${mascaraId}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: status,
          progress: progress,
          segmentation_notes: notes
        })
      }
    );

    const data = await res.json();

    if (res.ok) {
      // Actualizar estado local
      currentBatch.mascaras[index].status = status;
      currentBatch.mascaras[index].progress = progress;
      currentBatch.mascaras[index].segmentation_notes = notes;
      currentBatch.completed_items = data.completed_items;
      currentBatch.status = data.batch_status;

      // Actualizar UI
      updateProgressBar(data.completed_items, currentBatch.total_items);
      document.getElementById('batchStatusDisplay').innerHTML = getBatchStatusBadge(data.batch_status);

      // Actualizar color del borde de la fila
      const row = document.getElementById(`mascara-row-${index}`);
      row.className = `mascara-row status-${status}`;

      // Feedback visual
      btn.innerHTML = '<i class="fas fa-check"></i>';
      btn.classList.remove('btn-success');
      btn.classList.add('btn-outline-light');
      setTimeout(() => {
        btn.innerHTML = '<i class="fas fa-save"></i> Guardar';
        btn.classList.remove('btn-outline-light');
        btn.classList.add('btn-success');
      }, 1500);
    } else {
      alert(data.error || 'Error al guardar');
      btn.innerHTML = '<i class="fas fa-save"></i> Guardar';
    }
  } catch (e) {
    console.error('Error guardando máscara:', e);
    alert('Error de conexión');
    btn.innerHTML = '<i class="fas fa-save"></i> Guardar';
  }

  btn.disabled = false;
}

// ============================================
// EXPORTAR FUNCIONES GLOBALES
// ============================================
window.saveMascara = saveMascara;
