"""
Dashboard Segmentación Presencia
Sistema de Gestión de Máscaras con Roles y Permisos
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import os
from datetime import datetime
from dotenv import load_dotenv
from bson import ObjectId

# Importar módulo de base de datos
from db import (
    init_db,
    get_usuarios_collection,
    get_mascaras_collection,
    get_estadisticas_collection,
    get_gridfs,
    verificar_usuario,
    close_connection
)

# Cargar variables de entorno
load_dotenv()

# ============================================
# CONFIGURACIÓN FLASK
# ============================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'segmentacion-presencia-secret-key')
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max para archivos

# Habilitar CORS
CORS(app)

# Inicializar MongoDB al arrancar
init_db()


# ============================================
# DECORADORES DE AUTENTICACIÓN
# ============================================
def login_required(f):
    """Requiere que el usuario esté autenticado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """Requiere que el usuario tenga uno de los roles especificados"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario' not in session:
                return jsonify({"error": "No autenticado"}), 401

            usuario_rol = session['usuario'].get('rol')
            if usuario_rol not in roles:
                return jsonify({"error": f"Permisos insuficientes. Se requiere rol: {', '.join(roles)}"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================
# RUTAS - AUTENTICACIÓN
# ============================================

@app.route('/api/login', methods=['POST'])
def login():
    """Login de usuario"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username y password requeridos"}), 400

        # Verificar credenciales
        usuario = verificar_usuario(username, password)

        if usuario:
            # Guardar en sesión (sin el _id de MongoDB)
            usuario['_id'] = str(usuario['_id'])
            session['usuario'] = usuario

            return jsonify({
                "success": True,
                "message": "Login exitoso",
                "usuario": {
                    "username": usuario['username'],
                    "nombre_completo": usuario['nombre_completo'],
                    "rol": usuario['rol'],
                    "email": usuario.get('email')
                }
            })
        else:
            return jsonify({"error": "Credenciales inválidas"}), 401

    except Exception as e:
        print(f"❌ Error en login: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout de usuario"""
    session.pop('usuario', None)
    return jsonify({"success": True, "message": "Logout exitoso"})


@app.route('/api/session', methods=['GET'])
def get_session():
    """Obtiene la sesión actual del usuario"""
    if 'usuario' in session:
        return jsonify({
            "autenticado": True,
            "usuario": session['usuario']
        })
    else:
        return jsonify({"autenticado": False})


# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route('/')
def index():
    """Página principal del dashboard"""
    return render_template('dashboard.html')


# ============================================
# API - MÁSCARAS
# ============================================

@app.route('/api/mascaras', methods=['GET'])
@login_required
def get_mascaras():
    """
    Obtiene la lista de máscaras con paginación y filtros
    Query params:
        - page: número de página (default: 1)
        - per_page: items por página (default: 25)
        - review_status: filtrar por estado de revisión
        - operador: filtrar por operador asignado
        - entrenado: filtrar por estado de entrenamiento (true/false)
    """
    try:
        mascaras_col = get_mascaras_collection()
        if not mascaras_col:
            return jsonify({"error": "Colección de máscaras no disponible"}), 503

        # Paginación
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        skip = (page - 1) * per_page

        # Filtros
        filtro = {}

        review_status = request.args.get('review_status')
        if review_status:
            filtro['review_status'] = review_status

        operador = request.args.get('operador')
        if operador:
            filtro['operador'] = operador

        entrenado = request.args.get('entrenado')
        if entrenado is not None:
            filtro['entrenado'] = entrenado.lower() == 'true'

        # Total de máscaras
        total = mascaras_col.count_documents(filtro)

        # Obtener máscaras paginadas
        mascaras = list(mascaras_col.find(filtro)
                       .sort("fecha_creacion", -1)
                       .skip(skip)
                       .limit(per_page))

        # Convertir ObjectId a string
        for mascara in mascaras:
            mascara['_id'] = str(mascara['_id'])
            if 'gridfs_id' in mascara:
                mascara['gridfs_id'] = str(mascara['gridfs_id'])

        return jsonify({
            "mascaras": mascaras,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        })

    except Exception as e:
        print(f"❌ Error obteniendo máscaras: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/mascaras/<mascara_id>', methods=['GET'])
@login_required
def get_mascara(mascara_id):
    """Obtiene una máscara específica por ID"""
    try:
        mascaras_col = get_mascaras_collection()
        if not mascaras_col:
            return jsonify({"error": "Colección de máscaras no disponible"}), 503

        mascara = mascaras_col.find_one({"mascara_id": mascara_id})
        if not mascara:
            return jsonify({"error": f"Máscara {mascara_id} no encontrada"}), 404

        mascara['_id'] = str(mascara['_id'])
        if 'gridfs_id' in mascara:
            mascara['gridfs_id'] = str(mascara['gridfs_id'])

        return jsonify(mascara)

    except Exception as e:
        print(f"❌ Error obteniendo máscara {mascara_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/mascaras', methods=['POST'])
@login_required
@role_required('admin', 'supervisor', 'operador')
def create_mascara():
    """
    Crea una nueva máscara
    Body: JSON con los datos de la máscara
    """
    try:
        mascaras_col = get_mascaras_collection()
        if not mascaras_col:
            return jsonify({"error": "Colección de máscaras no disponible"}), 503

        data = request.get_json()

        # Validar campos requeridos
        if 'mascara_id' not in data:
            return jsonify({"error": "Falta el campo 'mascara_id'"}), 400

        # Verificar si ya existe
        existing = mascaras_col.find_one({"mascara_id": data['mascara_id']})
        if existing:
            return jsonify({"error": "La máscara ya existe"}), 400

        # Datos de la nueva máscara
        nueva_mascara = {
            "mascara_id": data['mascara_id'],
            "archivo": data.get('archivo', ''),
            "operador": data.get('operador', session['usuario']['username']),
            "fecha_creacion": datetime.now().isoformat(),
            "estado": data.get('estado', 'pendiente'),
            "review_status": data.get('review_status', 'pendiente'),
            "entrenado": False,
            "fecha_entrenamiento": None,
            "notas": data.get('notas', ''),
            "gridfs_id": data.get('gridfs_id', None),
            "created_by": session['usuario']['username'],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # Insertar
        result = mascaras_col.insert_one(nueva_mascara)

        return jsonify({
            "success": True,
            "message": "Máscara creada correctamente",
            "id": str(result.inserted_id),
            "mascara_id": nueva_mascara['mascara_id']
        }), 201

    except Exception as e:
        print(f"❌ Error creando máscara: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/mascaras/<mascara_id>', methods=['PUT'])
@login_required
@role_required('admin', 'supervisor', 'operador')
def update_mascara(mascara_id):
    """
    Actualiza una máscara específica
    Body: JSON con los campos a actualizar
    """
    try:
        mascaras_col = get_mascaras_collection()
        if not mascaras_col:
            return jsonify({"error": "Colección de máscaras no disponible"}), 503

        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400

        # Actualizar fecha de modificación
        data['updated_at'] = datetime.now().isoformat()
        data['updated_by'] = session['usuario']['username']

        # Actualizar máscara
        result = mascaras_col.update_one(
            {"mascara_id": mascara_id},
            {"$set": data}
        )

        if result.matched_count == 0:
            return jsonify({"error": f"Máscara {mascara_id} no encontrada"}), 404

        return jsonify({
            "success": True,
            "message": f"Máscara {mascara_id} actualizada correctamente",
            "modified": result.modified_count > 0
        })

    except Exception as e:
        print(f"❌ Error actualizando máscara {mascara_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/mascaras/<mascara_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'supervisor')
def delete_mascara(mascara_id):
    """Elimina una máscara (solo admin y supervisor)"""
    try:
        mascaras_col = get_mascaras_collection()
        if not mascaras_col:
            return jsonify({"error": "Colección de máscaras no disponible"}), 503

        result = mascaras_col.delete_one({"mascara_id": mascara_id})

        if result.deleted_count == 0:
            return jsonify({"error": f"Máscara {mascara_id} no encontrada"}), 404

        return jsonify({
            "success": True,
            "message": f"Máscara {mascara_id} eliminada correctamente"
        })

    except Exception as e:
        print(f"❌ Error eliminando máscara {mascara_id}: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================
# API - REVISIÓN DE MÁSCARAS
# ============================================

@app.route('/api/mascaras/<mascara_id>/revisar', methods=['POST'])
@login_required
@role_required('admin', 'supervisor')
def revisar_mascara(mascara_id):
    """
    Revisa una máscara (aprobar/rechazar)
    Body: { "review_status": "aprobado" | "rechazado", "notas": "..." }
    """
    try:
        mascaras_col = get_mascaras_collection()
        if not mascaras_col:
            return jsonify({"error": "Colección de máscaras no disponible"}), 503

        data = request.get_json()
        review_status = data.get('review_status')

        if review_status not in ['aprobado', 'rechazado']:
            return jsonify({"error": "review_status debe ser 'aprobado' o 'rechazado'"}), 400

        # Actualizar máscara
        update_data = {
            "review_status": review_status,
            "reviewed_by": session['usuario']['username'],
            "reviewed_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        if 'notas' in data:
            update_data['notas_revision'] = data['notas']

        result = mascaras_col.update_one(
            {"mascara_id": mascara_id},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"error": f"Máscara {mascara_id} no encontrada"}), 404

        return jsonify({
            "success": True,
            "message": f"Máscara {mascara_id} marcada como {review_status}",
            "review_status": review_status
        })

    except Exception as e:
        print(f"❌ Error revisando máscara {mascara_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/mascaras/<mascara_id>/marcar-entrenado', methods=['POST'])
def marcar_entrenado(mascara_id):
    """
    Marca una máscara como entrenada (para uso de la IA)
    No requiere autenticación - usado por el sistema de IA
    """
    try:
        mascaras_col = get_mascaras_collection()
        if not mascaras_col:
            return jsonify({"error": "Colección de máscaras no disponible"}), 503

        result = mascaras_col.update_one(
            {"mascara_id": mascara_id},
            {"$set": {
                "entrenado": True,
                "fecha_entrenamiento": datetime.now().isoformat()
            }}
        )

        if result.matched_count == 0:
            return jsonify({"error": f"Máscara {mascara_id} no encontrada"}), 404

        return jsonify({
            "success": True,
            "message": f"Máscara {mascara_id} marcada como entrenada"
        })

    except Exception as e:
        print(f"❌ Error marcando máscara como entrenada: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/mascaras-aprobadas', methods=['GET'])
def get_mascaras_aprobadas():
    """
    Obtiene máscaras aprobadas y no entrenadas (para uso de la IA)
    No requiere autenticación - usado por el sistema de IA
    """
    try:
        mascaras_col = get_mascaras_collection()
        if not mascaras_col:
            return jsonify({"error": "Colección de máscaras no disponible"}), 503

        mascaras = list(mascaras_col.find({
            "review_status": "aprobado",
            "entrenado": False
        }).sort("fecha_creacion", 1))

        # Convertir ObjectId a string
        for mascara in mascaras:
            mascara['_id'] = str(mascara['_id'])
            if 'gridfs_id' in mascara:
                mascara['gridfs_id'] = str(mascara['gridfs_id'])

        return jsonify({
            "success": True,
            "total": len(mascaras),
            "mascaras": mascaras
        })

    except Exception as e:
        print(f"❌ Error obteniendo máscaras aprobadas: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================
# API - USUARIOS
# ============================================

@app.route('/api/usuarios', methods=['GET'])
@login_required
@role_required('admin', 'supervisor')
def get_usuarios():
    """Obtiene la lista de usuarios"""
    try:
        usuarios_col = get_usuarios_collection()
        if not usuarios_col:
            return jsonify({"error": "Colección de usuarios no disponible"}), 503

        usuarios = list(usuarios_col.find().sort("username", 1))

        # Convertir ObjectId y eliminar passwords
        for usuario in usuarios:
            usuario['_id'] = str(usuario['_id'])
            usuario.pop('password_hash', None)

        return jsonify(usuarios)

    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================
# API - ESTADÍSTICAS
# ============================================

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Obtiene estadísticas generales del sistema"""
    try:
        usuarios_col = get_usuarios_collection()
        mascaras_col = get_mascaras_collection()

        if not usuarios_col or not mascaras_col:
            return jsonify({"error": "Colecciones no disponibles"}), 503

        # Estadísticas básicas
        total_usuarios = usuarios_col.count_documents({"activo": True})
        total_mascaras = mascaras_col.count_documents({})

        # Máscaras por estado de revisión
        mascaras_aprobadas = mascaras_col.count_documents({"review_status": "aprobado"})
        mascaras_rechazadas = mascaras_col.count_documents({"review_status": "rechazado"})
        mascaras_pendientes = mascaras_col.count_documents({"review_status": "pendiente"})

        # Máscaras entrenadas
        mascaras_entrenadas = mascaras_col.count_documents({"entrenado": True})
        mascaras_sin_entrenar = mascaras_col.count_documents({"entrenado": False})

        # Máscaras listas para entrenar (aprobadas y no entrenadas)
        mascaras_listas_entrenar = mascaras_col.count_documents({
            "review_status": "aprobado",
            "entrenado": False
        })

        return jsonify({
            "total_usuarios": total_usuarios,
            "total_mascaras": total_mascaras,
            "mascaras_aprobadas": mascaras_aprobadas,
            "mascaras_rechazadas": mascaras_rechazadas,
            "mascaras_pendientes": mascaras_pendientes,
            "mascaras_entrenadas": mascaras_entrenadas,
            "mascaras_sin_entrenar": mascaras_sin_entrenar,
            "mascaras_listas_entrenar": mascaras_listas_entrenar
        })

    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================
# MANEJO DE ERRORES
# ============================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Recurso no encontrado"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Error interno del servidor"}), 500


# ============================================
# LIMPIEZA AL CERRAR
# ============================================

@app.teardown_appcontext
def teardown_db(exception=None):
    """Cierra las conexiones MongoDB al finalizar"""
    pass


# ============================================
# PUNTO DE ENTRADA
# ============================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Dashboard Segmentación Presencia - Modo Desarrollo")
    print("="*60)
    print(f"📍 URL: http://0.0.0.0:5001")
    print(f"🔧 Hot-reload: Activado")
    print(f"⚡ Modo: Desarrollo")
    print(f"🗄️  Base de datos: segmentacion_presencia")
    print(f"👥 Usuarios iniciales:")
    print(f"   - Estegania / estegania2025 (Admin Principal)")
    print(f"   - admin / admin123")
    print(f"   - supervisor / super123")
    print(f"   - operador1 / oper123")
    print("🛑 Detener: Ctrl+C")
    print("="*60 + "\n")

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True,
        threaded=True
    )
