import os
from pymongo import MongoClient, ASCENDING

# Base de datos unificada Quality_Hope
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB", "Quality_Hope")

_client = None

def get_client():
    """Crear/retornar el cliente de MongoDB con pool de conexiones optimizado."""
    global _client
    if _client is None:
        _client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            maxPoolSize=20,
            minPoolSize=5,
            maxIdleTimeMS=30000,
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
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
    """Retorna la base de datos Quality_Hope."""
    ok, err = ping_client()
    if ok:
        return get_client()[DB_NAME]
    msg = f"No se pudo conectar a MongoDB ({MONGO_URI}): {err}"
    if raise_on_fail:
        raise ConnectionError(msg)
    else:
        print("⚠️", msg)
        return None

def get_quality_db():
    """Alias de get_db() — Quality_Hope contiene segmentadores."""
    return get_db(raise_on_fail=False)

def get_training_db():
    """Alias de get_db() — Quality_Hope contiene masks.files."""
    return get_db(raise_on_fail=False)

def create_indexes():
    """Crear índices optimizados — idempotente."""
    try:
        db = get_db(raise_on_fail=False)
        if db is None:
            return

        batches = db["batches"]
        masks = db["masks.files"]

        # Índices básicos
        batches.create_index([("id", ASCENDING)], unique=True, background=True)

        # Índices para métricas y filtros
        batches.create_index([("assignee", ASCENDING)], background=True)
        batches.create_index([("status", ASCENDING)], background=True)
        batches.create_index([("metadata.assigned_at", ASCENDING)], background=True)

        # Índices compuestos
        batches.create_index([("assignee", ASCENDING), ("status", ASCENDING)], background=True)
        batches.create_index([("status", ASCENDING), ("metadata.assigned_at", ASCENDING)], background=True)

        # Índices para búsqueda de masks
        masks.create_index([("filename", ASCENDING)], background=True)
        masks.create_index([("uploadDate", ASCENDING)], background=True)

        # Índices para reportes de avances
        reporte = db["Reporte_avances_masks"]
        reporte.create_index([("batch_id", ASCENDING)], background=True)
        reporte.create_index([("fecha", ASCENDING)], background=True)
        reporte.create_index([("segmentador", ASCENDING)], background=True)

        print("✅ Índices creados en Quality_Hope (11 índices)")
    except Exception as e:
        print("⚠️ No se pudieron crear índices:", e)

def close_client():
    global _client
    if _client:
        _client.close()
        _client = None
