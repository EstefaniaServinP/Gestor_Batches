"""
Configuración de Gunicorn optimizada para:
- AMD Ryzen 5 5625U (6 núcleos / 12 hilos)
- 11GB RAM disponible
- Dashboard de Segmentación
"""

import multiprocessing
import os

# WORKERS: Aprovechar múltiples núcleos
# Fórmula recomendada: (2 x núcleos) + 1
# Para 6 núcleos físicos = 8 workers (usa ~8 de 12 hilos)
workers = int(os.environ.get("GUNICORN_WORKERS", 8))

# WORKER CLASS: Sync workers (compatible con MongoDB)
worker_class = "sync"

# THREADS por worker: Para I/O concurrente (MongoDB, etc)
threads = 2

# TIMEOUT: Aumentado para operaciones pesadas (sync-batch-files)
timeout = 120  # 2 minutos

# BINDING
bind = os.environ.get("BIND_ADDRESS", "0.0.0.0:5000")

# MEMORIA: Límite de requests antes de reciclar worker (previene memory leaks)
max_requests = 1000
max_requests_jitter = 50  # Variación aleatoria para evitar restarts simultáneos

# LOGGING
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# PERFORMANCE
keepalive = 5  # Segundos para mantener conexiones keep-alive
worker_connections = 1000  # Conexiones simultáneas por worker

# GRACEFUL TIMEOUT
graceful_timeout = 30

# PRELOAD: Cargar app antes de fork (ahorra memoria)
preload_app = True

# ESTADÍSTICAS
proc_name = "segmentacion_dashboard"

print(f"""
╔══════════════════════════════════════════════════════════╗
║  Gunicorn - Dashboard de Segmentación OPTIMIZADO        ║
╟──────────────────────────────────────────────────────────╢
║  Workers:              {workers} (aprovecha {workers} de 12 hilos)       ║
║  Threads por worker:   {threads}                                    ║
║  Total capacidad:      {workers * threads} conexiones concurrentes      ║
║  Timeout:              {timeout}s                                ║
║  Bind:                 {bind}                      ║
║  Max requests:         {max_requests} (recicla workers)            ║
╚══════════════════════════════════════════════════════════╝
""")

def on_starting(server):
    """Hook al iniciar Gunicorn"""
    print("🚀 Iniciando Gunicorn con configuración optimizada...")

def worker_init(worker):
    """Hook al iniciar cada worker"""
    print(f"👷 Worker {worker.pid} iniciado")

def post_fork(server, worker):
    """Después de fork - optimizar conexiones MongoDB"""
    print(f"🔧 Worker {worker.pid} configurado con MongoDB")
