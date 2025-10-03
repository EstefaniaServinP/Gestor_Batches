/* ===============================================
   JAVASCRIPT COMÚN PARA MENÚ HAMBURGUESA
   =============================================== */

// Variables globales del menú
let menuOpen = false;
let metricsSubmenuOpen = false;

// Función para alternar el menú
function toggleMenu() {
  const menu = document.getElementById('sideMenu');
  const overlay = document.getElementById('menuOverlay');
  const toggle = document.getElementById('menuToggle');

  menuOpen = !menuOpen;

  if (menuOpen) {
    openMenu();
  } else {
    closeMenu();
  }
}

// Función para abrir el menú
function openMenu() {
  const menu = document.getElementById('sideMenu');
  const overlay = document.getElementById('menuOverlay');
  const toggle = document.getElementById('menuToggle');

  menu.classList.add('open');
  overlay.classList.add('show');
  toggle.classList.add('active');
  menuOpen = true;

  // Restaurar estado del submenú desde localStorage
  const savedState = localStorage.getItem('metricsSubmenuOpen');
  if (savedState === 'true') {
    openMetricsSubmenu();
  }

  // Agregar event listener para cerrar con ESC
  document.addEventListener('keydown', handleEscapeKey);
}

// Función para cerrar el menú
function closeMenu() {
  const menu = document.getElementById('sideMenu');
  const overlay = document.getElementById('menuOverlay');
  const toggle = document.getElementById('menuToggle');

  menu.classList.remove('open');
  overlay.classList.remove('show');
  toggle.classList.remove('active');
  menuOpen = false;

  // Remover event listener
  document.removeEventListener('keydown', handleEscapeKey);
}

// Manejar tecla ESC para cerrar menú
function handleEscapeKey(event) {
  if (event.key === 'Escape' && menuOpen) {
    closeMenu();
  }
}

// Toggle del submenú de Métricas
function toggleMetricsSubmenu(event) {
  if (event) {
    event.preventDefault();
    event.stopPropagation();
  }

  metricsSubmenuOpen = !metricsSubmenuOpen;

  if (metricsSubmenuOpen) {
    openMetricsSubmenu();
  } else {
    closeMetricsSubmenu();
  }

  // Guardar estado en localStorage
  localStorage.setItem('metricsSubmenuOpen', metricsSubmenuOpen);
}

// Abrir submenú de Métricas
function openMetricsSubmenu() {
  const trigger = document.getElementById('metricsTrigger');
  const submenu = document.getElementById('metricsSubmenu');

  if (trigger && submenu) {
    trigger.classList.add('expanded');
    trigger.setAttribute('aria-expanded', 'true');
    submenu.classList.add('expanded');
    submenu.setAttribute('aria-hidden', 'false');
    metricsSubmenuOpen = true;
  }
}

// Cerrar submenú de Métricas
function closeMetricsSubmenu() {
  const trigger = document.getElementById('metricsTrigger');
  const submenu = document.getElementById('metricsSubmenu');

  if (trigger && submenu) {
    trigger.classList.remove('expanded');
    trigger.setAttribute('aria-expanded', 'false');
    submenu.classList.remove('expanded');
    submenu.setAttribute('aria-hidden', 'true');
    metricsSubmenuOpen = false;
  }
}

// Soporte de teclado para el trigger del submenú
function handleMetricsTriggerKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    toggleMetricsSubmenu(event);
  }
}

// Generar HTML del menú hamburguesa
function generateMenuHTML() {
  const currentPath = window.location.pathname;

  return `
    <!-- Menú hamburguesa elegante -->
    <div class="menu-toggle" onclick="toggleMenu()" id="menuToggle">
      <i class="fas fa-bars" style="color: white; font-size: 1.5rem;"></i>
    </div>

    <!-- Menú lateral minimalista -->
    <div class="side-menu" id="sideMenu">
      <div class="menu-header">
        <h5><i class="fas fa-microscope"></i> Dashboard</h5>
      </div>
      <div class="menu-items">
        <a href="/" class="menu-item">
          <i class="fas fa-home"></i>
          <span>Inicio</span>
        </a>
        <a href="/dashboard" class="menu-item">
          <i class="fas fa-th-large"></i>
          <span>Dashboard General</span>
        </a>
        <a href="/masks" class="menu-item">
          <i class="fas fa-images"></i>
          <span>Máscaras</span>
        </a>

        <!-- Trigger del submenú de Métricas -->
        <button
          class="menu-item-trigger"
          id="metricsTrigger"
          onclick="toggleMetricsSubmenu(event)"
          onkeydown="handleMetricsTriggerKeydown(event)"
          aria-expanded="false"
          aria-controls="metricsSubmenu"
        >
          <i class="fas fa-chart-bar"></i>
          <span>Métricas</span>
          <i class="fas fa-caret-right caret"></i>
        </button>

        <!-- Submenú colapsable de Métricas -->
        <div
          class="submenu-container"
          id="metricsSubmenu"
          role="group"
          aria-hidden="true"
        >
          <a href="/metrics/team" class="submenu-item ${currentPath === '/metrics/team' ? 'active' : ''}">
            <i class="fas fa-users"></i>
            <span>Avances por Persona</span>
          </a>
          <a href="/metrics/overview" class="submenu-item ${currentPath === '/metrics/overview' ? 'active' : ''}">
            <i class="fas fa-chart-line"></i>
            <span>Estadísticas Globales</span>
          </a>
          <a href="/verify" class="submenu-item ${currentPath === '/verify' ? 'active' : ''}">
            <i class="fas fa-database"></i>
            <span>Verificar MongoDB</span>
          </a>
          <a href="/metrics/progress" class="submenu-item ${currentPath === '/metrics/progress' ? 'active' : ''}">
            <i class="fas fa-chart-pie"></i>
            <span>Reporte de Progreso</span>
          </a>
        </div>

        <a href="#" class="menu-item" onclick="logout(); return false;">
          <i class="fas fa-sign-out-alt"></i>
          <span>Salir</span>
        </a>
      </div>
    </div>

    <!-- Overlay para cerrar menú -->
    <div class="menu-overlay" id="menuOverlay" onclick="closeMenu()"></div>
  `;
}

// Función de logout
function logout() {
  if (confirm('¿Estás seguro de que quieres salir?')) {
    window.location.href = '/logout';
  }
}

// Inicializar menú cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
  // Si no existe el menú, lo creamos
  if (!document.getElementById('menuToggle')) {
    const menuContainer = document.createElement('div');
    menuContainer.innerHTML = generateMenuHTML();
    document.body.insertBefore(menuContainer, document.body.firstChild);
  }
});

// Función utilitaria para mostrar/ocultar loading
function showLoading() {
  const loadingOverlay = document.getElementById('loadingOverlay');
  if (loadingOverlay) {
    loadingOverlay.style.display = 'flex';
  }
}

function hideLoading() {
  const loadingOverlay = document.getElementById('loadingOverlay');
  if (loadingOverlay) {
    loadingOverlay.style.display = 'none';
  }
}

// Función utilitaria para notificaciones
function showNotification(message, type = 'success') {
  // Crear elemento de notificación si no existe
  let notification = document.getElementById('notification');
  if (!notification) {
    notification = document.createElement('div');
    notification.id = 'notification';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      border-radius: 10px;
      color: white;
      font-weight: 500;
      z-index: 10000;
      transform: translateX(400px);
      transition: all 0.3s ease;
      min-width: 250px;
    `;
    document.body.appendChild(notification);
  }
  
  // Configurar estilo según tipo
  const colors = {
    success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    error: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    warning: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    info: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
  };
  
  notification.style.background = colors[type] || colors.success;
  notification.textContent = message;
  notification.style.transform = 'translateX(0)';
  
  // Auto-ocultar después de 3 segundos
  setTimeout(() => {
    notification.style.transform = 'translateX(400px)';
  }, 3000);
}
