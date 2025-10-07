import os
from pymongo import MongoClient, ASCENDING

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB", "segmentacion_db")
QUALITY_DB_NAME = "Quality_dashboard"  # Base para segmentadores
TRAINING_DB_NAME = "training_metrics"  # Base para máscaras

_client = None

def get_client():
    """Crear/retornar el cliente de MongoDB sin hacer ping (no bloqueante en import)."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
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
    """Crear índices recomendados (id único, assignee) — idempotente."""
    try:
        db = get_db(raise_on_fail=False)
        if db is None:
            return
        # batches: id único, assignee para búsquedas
        db["batches"].create_index([("id", ASCENDING)], unique=True, background=True)
        db["batches"].create_index([("assignee", ASCENDING)], background=True)
        # masks: index sobre filename para búsquedas por patrón
        db["masks.files"].create_index([("filename", ASCENDING)], background=True)
        print("✅ Índices verificados/creados")
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

def get_training_db():
    """Retorna la base de datos training_metrics para máscaras"""
    ok, err = ping_client()
    if ok:
        return get_client()[TRAINING_DB_NAME]
    msg = f"No se pudo conectar a training_metrics: {err}"
    print("⚠️", msg)
    return None

def close_client():
    global _client
    if _client:
        _client.close()
        _client = None