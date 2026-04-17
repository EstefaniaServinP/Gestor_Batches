"""
Módulo de conexión a MongoDB para Dashboard Segmentación Presencia
Base de datos: segmentacion_presencia
Servidor: localhost:27017
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import gridfs
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Cargar variables de entorno
load_dotenv()

# ============================================
# CONFIGURACIÓN MONGODB
# ============================================
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB = os.getenv("MONGO_DB", "segmentacion_presencia")

# Construir URI
MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

# Colecciones
USUARIOS_COLLECTION = os.getenv("USUARIOS_COLLECTION", "usuarios")
MASCARAS_COLLECTION = os.getenv("MASCARAS_COLLECTION", "mascaras")
ESTADISTICAS_COLLECTION = os.getenv("ESTADISTICAS_COLLECTION", "estadisticas")
BATCHES_COLLECTION = os.getenv("BATCHES_COLLECTION", "batches")

# ============================================
# CLIENTE MONGODB (SINGLETON)
# ============================================
_client = None
_db = None
_usuarios_col = None
_mascaras_col = None
_estadisticas_col = None
_batches_col = None
_gridfs = None


def get_client():
    """Obtiene el cliente MongoDB (singleton)"""
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=10,
                minPoolSize=2,
                maxIdleTimeMS=30000,
                connectTimeoutMS=5000,
                socketTimeoutMS=30000,
            )
            # Verificar conexión
            _client.admin.command('ping')
            print(f"✅ Conectado a MongoDB: {MONGO_HOST}:{MONGO_PORT}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ Error conectando a MongoDB: {e}")
            _client = None
    return _client


def get_db():
    """Obtiene la base de datos segmentacion_presencia"""
    global _db
    if _db is None:
        client = get_client()
        if client:
            _db = client[MONGO_DB]
            print(f"✅ Base de datos seleccionada: {MONGO_DB}")
    return _db


def get_usuarios_collection():
    """Obtiene la colección de usuarios"""
    global _usuarios_col
    if _usuarios_col is None:
        db = get_db()
        if db is not None:
            _usuarios_col = db[USUARIOS_COLLECTION]
            print(f"✅ Colección usuarios lista: {USUARIOS_COLLECTION}")
    return _usuarios_col


def get_mascaras_collection():
    """Obtiene la colección de máscaras"""
    global _mascaras_col
    if _mascaras_col is None:
        db = get_db()
        if db is not None:
            _mascaras_col = db[MASCARAS_COLLECTION]
            print(f"✅ Colección máscaras lista: {MASCARAS_COLLECTION}")
    return _mascaras_col


def get_estadisticas_collection():
    """Obtiene la colección de estadísticas"""
    global _estadisticas_col
    if _estadisticas_col is None:
        db = get_db()
        if db is not None:
            _estadisticas_col = db[ESTADISTICAS_COLLECTION]
            print(f"✅ Colección estadísticas lista: {ESTADISTICAS_COLLECTION}")
    return _estadisticas_col


def get_batches_collection():
    """Obtiene la colección de batches"""
    global _batches_col
    if _batches_col is None:
        db = get_db()
        if db is not None:
            _batches_col = db[BATCHES_COLLECTION]
            print(f"✅ Colección batches lista: {BATCHES_COLLECTION}")
    return _batches_col


def get_gridfs():
    """Obtiene el cliente GridFS para archivos de máscaras"""
    global _gridfs
    if _gridfs is None:
        db = get_db()
        if db is not None:
            _gridfs = gridfs.GridFS(db, collection="mascaras")
            print(f"✅ GridFS configurado para almacenar archivos")
    return _gridfs


def close_connection():
    """Cierra la conexión a MongoDB"""
    global _client, _db, _usuarios_col, _mascaras_col, _estadisticas_col, _batches_col, _gridfs
    if _client:
        _client.close()
        _client = None
        _db = None
        _usuarios_col = None
        _mascaras_col = None
        _estadisticas_col = None
        _batches_col = None
        _gridfs = None
        print("✅ Conexión MongoDB cerrada")


# ============================================
# INICIALIZACIÓN Y DATOS DE EJEMPLO
# ============================================
def init_db():
    """Inicializa las conexiones y crea datos iniciales"""
    print("\n🔧 Inicializando base de datos Segmentación Presencia...")

    # Conectar
    client = get_client()
    if not client:
        print("❌ No se pudo conectar a MongoDB")
        return False

    db = get_db()
    if db is None:
        print("❌ No se pudo seleccionar la base de datos")
        return False

    # Obtener colecciones existentes
    existing_collections = db.list_collection_names()
    print(f"📋 Colecciones existentes: {existing_collections}")

    # Crear colecciones si no existen
    if USUARIOS_COLLECTION not in existing_collections:
        db.create_collection(USUARIOS_COLLECTION)
        print(f"✅ Colección '{USUARIOS_COLLECTION}' creada")

    if MASCARAS_COLLECTION not in existing_collections:
        db.create_collection(MASCARAS_COLLECTION)
        print(f"✅ Colección '{MASCARAS_COLLECTION}' creada")

    if ESTADISTICAS_COLLECTION not in existing_collections:
        db.create_collection(ESTADISTICAS_COLLECTION)
        print(f"✅ Colección '{ESTADISTICAS_COLLECTION}' creada")

    if BATCHES_COLLECTION not in existing_collections:
        db.create_collection(BATCHES_COLLECTION)
        print(f"✅ Colección '{BATCHES_COLLECTION}' creada")

    # Obtener referencias a colecciones
    usuarios_col = get_usuarios_collection()
    mascaras_col = get_mascaras_collection()
    estadisticas_col = get_estadisticas_collection()
    gridfs_client = get_gridfs()

    # Crear índices
    _create_indexes(usuarios_col, mascaras_col)

    # Crear usuarios iniciales si no existen
    _create_initial_users(usuarios_col)

    print("✅ Inicialización completada\n")
    return True


def _create_indexes(usuarios_col, mascaras_col):
    """Crea índices para mejorar performance"""
    print("🔍 Creando índices...")

    try:
        # Índice único en username
        usuarios_col.create_index("username", unique=True)

        # Índice en mascara_id
        mascaras_col.create_index("mascara_id", unique=True)

        # Índice compuesto para consultas frecuentes
        mascaras_col.create_index([("review_status", 1), ("entrenado", 1)])

        # Índices para batches
        batches_col = get_batches_collection()
        batches_col.create_index("batch_id", unique=True)
        batches_col.create_index("assignee.user_id")
        batches_col.create_index([("assignee.user_id", 1), ("status", 1)])

        print("✅ Índices creados")
    except Exception as e:
        print(f"⚠️  Advertencia al crear índices: {e}")


def _create_initial_users(usuarios_col):
    """Crea usuarios iniciales si no existen"""
    print("👥 Verificando usuarios iniciales...")

    # Verificar si ya hay usuarios
    if usuarios_col.count_documents({}) > 0:
        print("ℹ️  Ya existen usuarios en la base de datos")
        return

    # Usuarios iniciales
    usuarios_iniciales = [
        {
            "username": "Estegania",
            "password_hash": generate_password_hash("estegania2025"),
            "nombre_completo": "Estegania - Administrador Principal",
            "email": "estegania@segmentacion.com",
            "rol": "admin",
            "activo": True
        },
        {
            "username": "admin",
            "password_hash": generate_password_hash("admin123"),
            "nombre_completo": "Administrador",
            "email": "admin@segmentacion.com",
            "rol": "admin",
            "activo": True
        },
        {
            "username": "supervisor",
            "password_hash": generate_password_hash("super123"),
            "nombre_completo": "Supervisor",
            "email": "supervisor@segmentacion.com",
            "rol": "supervisor",
            "activo": True
        },
        {
            "username": "operador1",
            "password_hash": generate_password_hash("oper123"),
            "nombre_completo": "Operador 1",
            "email": "operador1@segmentacion.com",
            "rol": "operador",
            "activo": True
        }
    ]

    # Insertar usuarios
    result = usuarios_col.insert_many(usuarios_iniciales)
    print(f"✅ {len(result.inserted_ids)} usuarios iniciales creados:")
    print("   - Estegania / estegania2025 (Administrador Principal)")
    print("   - admin / admin123 (Administrador)")
    print("   - supervisor / super123 (Supervisor)")
    print("   - operador1 / oper123 (Operador)")


# ============================================
# FUNCIONES DE UTILIDAD
# ============================================
def verificar_usuario(username, password):
    """Verifica credenciales de usuario"""
    from werkzeug.security import check_password_hash

    usuarios_col = get_usuarios_collection()
    if usuarios_col is None:
        return None

    usuario = usuarios_col.find_one({"username": username, "activo": True})
    if usuario and check_password_hash(usuario['password_hash'], password):
        # No devolver el hash de password
        usuario.pop('password_hash', None)
        return usuario

    return None


def get_usuario_by_username(username):
    """Obtiene un usuario por username"""
    usuarios_col = get_usuarios_collection()
    if usuarios_col is None:
        return None

    usuario = usuarios_col.find_one({"username": username})
    if usuario:
        usuario.pop('password_hash', None)
    return usuario


# ============================================
# TEST DE CONEXIÓN
# ============================================
if __name__ == "__main__":
    print("🧪 Probando conexión a MongoDB...\n")

    if init_db():
        print("\n✅ CONEXIÓN EXITOSA!")
        print(f"   Base de datos: {MONGO_DB}")
        print(f"   Host: {MONGO_HOST}:{MONGO_PORT}")

        db = get_db()
        print(f"\n📋 Colecciones disponibles:")
        for col in db.list_collection_names():
            count = db[col].count_documents({})
            print(f"   - {col}: {count} documentos")

        close_connection()
    else:
        print("\n❌ ERROR EN LA CONEXIÓN")
