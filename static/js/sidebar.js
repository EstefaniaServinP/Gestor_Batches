/* ================================================
   SIDEBAR UNIFICADO - Lógica JavaScript
   ================================================ */

// Variables globales
let sidebarOpen = false;
let metricsSubmenuOpen = false;

// Toggle del sidebar principal
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggle = document.getElementById('sidebarToggle');

  sidebarOpen = !sidebarOpen;

  if (sidebarOpen) {
    openSidebar();
  } else {
    closeSidebar();
  }
}

// Abrir sidebar
function openSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggle = document.getElementById('sidebarToggle');

  sidebar.classList.add('open');
  overlay.classList.add('show');
  toggle.classList.add('active');
  toggle.setAttribute('aria-expanded', 'true');
  sidebarOpen = true;

  // Restaurar estado del submenú desde localStorage
  const savedState = localStorage.getItem('metricsSubmenuOpen');
  if (savedState === 'true') {
    openMetricsSubmenu();
  }

  // Event listener para cerrar con ESC
  document.addEventListener('keydown', handleEscapeKey);
}

// Cerrar sidebar
function closeSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggle = document.getElementById('sidebarToggle');

  sidebar.classList.remove('open');
  overlay.classList.remove('show');
  toggle.classList.remove('active');
  toggle.setAttribute('aria-expanded', 'false');
  sidebarOpen = false;

  // Remover event listener
  document.removeEventListener('keydown', handleEscapeKey);
}

// Manejar tecla ESC
function handleEscapeKey(event) {
  if (event.key === 'Escape' && sidebarOpen) {
    closeSidebar();
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
    submenu.classList.add('open');
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
    submenu.classList.remove('open');
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

// Inicialización al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
  // Si estamos en una ruta de /metrics/*, abrir el submenú automáticamente
  const currentPath = window.location.pathname;
  if (currentPath.startsWith('/metrics/')) {
    // Esperar un momento para que el DOM esté completamente listo
    setTimeout(openMetricsSubmenu, 100);
  }
});
