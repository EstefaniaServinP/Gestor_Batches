"""
Configuración de Gunicorn para Quality Ktech Dashboard

Para producción, ejecutar con:
    gunicorn -c gunicorn_config.py app:app

Para desarrollo, es más fácil usar:
    python app.py
"""

import multiprocessing
import os

# WORKERS: Configuración conservadora para desarrollo/producción
workers = int(os.environ.get("GUNICORN_WORKERS", 2))

# WORKER CLASS: Sync workers (compatible con MongoDB)
worker_class = "sync"

# THREADS por worker: Balance entre concurrencia y memoria
threads = 4

# TIMEOUT: Para operaciones pesadas
timeout = 120  # 2 minutos

# BINDING
bind = os.environ.get("BIND_ADDRESS", "0.0.0.0:5000")

# MEMORIA: Reciclaje de workers para liberar memoria
max_requests = 300
max_requests_jitter = 50

# LOGGING
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# RELOAD: Útil para desarrollo (desactivar en producción)
reload = False  # Cambiar a True si quieres hot-reload con gunicorn

# PRELOAD: Cargar la app antes de forkear workers
preload_app = True

# WORKER CONNECTIONS
worker_connections = 1000

print(f"""
╔═══════════════════════════════════════════════════════════╗
║        Quality Ktech Dashboard - Gunicorn Config          ║
╠═══════════════════════════════════════════════════════════╣
║  Workers:          {workers} workers x {threads} threads = {workers * threads} conexiones    ║
║  Timeout:          {timeout}s                                       ║
║  Max requests:     {max_requests} (recicla workers)                   ║
║  Bind:             {bind}                            ║
║  Preload:          {preload_app}                                      ║
╚═══════════════════════════════════════════════════════════╝
""")
