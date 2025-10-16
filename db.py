import os
from pymongo import MongoClient, ASCENDING

# Conexión principal (puerto 27017) - Para segmentacion_db y Quality_dashboard
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://192.168.1.93:27017")
DB_NAME = os.environ.get("MONGO_DB", "segmentacion_db")
QUALITY_DB_NAME = "Quality_dashboard"  # Base para segmentadores

# Conexión secundaria - Para QUALITY_IEMSA (máscaras en training_metrics.masks.files)
# Ahora en el mismo servidor que la conexión principal
TRAINING_MONGO_URI = os.environ.get(
    "TRAINING_MONGO_URI",
    "mongodb://192.168.1.93:27017/QUALITY_IEMSA"
)
TRAINING_DB_NAME = "QUALITY_IEMSA"  # Base para máscaras (training_metrics.masks.files)

_client = None
_training_client = None

def get_client():
    """Crear/retornar el cliente de MongoDB con pool de conexiones optimizado."""
    global _client
    if _client is None:
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=20,  # Máximo 20 conexiones en el pool (4 workers x 3 threads = 12, +8 buffer)
            minPoolSize=5,   # Mínimo 5 conexiones siempre abiertas
            maxIdleTimeMS=30000,  # Cerrar conexiones inactivas después de 30s
            connectTimeoutMS=5000,  # Timeout de conexión
            socketTimeoutMS=30000,  # Timeout de operaciones
        )
    return _client

def ping_client(timeout_ms=2000):
    """Intentar un ping rápido; devuelve (True, None) o (False, Exception)."""
    try:
        get_client().admin.command("ping")
        return True, None
    except Exception as e:
        return False, e

def get_db(raise_on_fail=True):
    """Retorna la base de datos configurada. No fuerza la creación del cliente en import."""
    ok, err = ping_client()
    if ok:
        return get_client()[DB_NAME]
    msg = f"No se pudo conectar a MongoDB ({MONGO_URI}): {err}"
    if raise_on_fail:
        raise ConnectionError(msg)
    else:
        print("⚠️", msg)
        return None

def create_indexes():
    """Crear índices optimizados para reducir tiempo de consulta — idempotente."""
    try:
        db = get_db(raise_on_fail=False)
        if db is None:
            return

        batches = db["batches"]
        masks = db["masks.files"]

        # ÍNDICES BÁSICOS
        batches.create_index([("id", ASCENDING)], unique=True, background=True)

        # ÍNDICES PARA MÉTRICAS Y FILTROS (mejora agregaciones 10x)
        batches.create_index([("assignee", ASCENDING)], background=True)
        batches.create_index([("status", ASCENDING)], background=True)
        batches.create_index([("metadata.assigned_at", ASCENDING)], background=True)

        # ÍNDICES COMPUESTOS (queries 5-10x más rápidas)
        batches.create_index([("assignee", ASCENDING), ("status", ASCENDING)], background=True)
        batches.create_index([("status", ASCENDING), ("metadata.assigned_at", ASCENDING)], background=True)

        # ÍNDICES PARA BÚSQUEDA DE METADATA DE ARCHIVOS
        masks.create_index([("filename", ASCENDING)], background=True)
        masks.create_index([("uploadDate", ASCENDING)], background=True)

        print("✅ Índices optimizados creados (8 índices)")
    except Exception as e:
        print("⚠️ No se pudieron crear índices:", e)

def get_quality_db():
    """Retorna la base de datos Quality_dashboard para segmentadores"""
    ok, err = ping_client()
    if ok:
        return get_client()[QUALITY_DB_NAME]
    msg = f"No se pudo conectar a Quality_dashboard: {err}"
    print("⚠️", msg)
    return None

def get_training_client():
    """Crear/retornar el cliente de MongoDB para máscaras con pool optimizado"""
    global _training_client
    if _training_client is None:
        _training_client = MongoClient(
            TRAINING_MONGO_URI,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=15,  # Pool más pequeño para base secundaria
            minPoolSize=3,   # Mínimo 3 conexiones
            maxIdleTimeMS=30000,
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
        )
    return _training_client

def ping_training_client():
    """Intentar un ping rápido al servidor de training; devuelve (True, None) o (False, Exception)."""
    try:
        get_training_client().admin.command("ping")
        return True, None
    except Exception as e:
        return False, e

def get_training_db():
    """Retorna la base de datos QUALITY_IEMSA para máscaras (puerto 27018)"""
    ok, err = ping_training_client()
    if ok:
        return get_training_client()[TRAINING_DB_NAME]
    msg = f"No se pudo conectar a QUALITY_IEMSA ({TRAINING_MONGO_URI}): {err}"
    print("⚠️", msg)
    return None

def close_client():
    global _client, _training_client
    if _client:
        _client.close()
        _client = None
    if _training_client:
        _training_client.close()
        _training_client = None