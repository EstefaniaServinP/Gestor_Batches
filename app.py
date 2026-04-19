#!/usr/bin/env python3
"""
Dashboard de Segmentación de Imágenes Médicas
============================================

Sistema web para gestionar la asignación y seguimiento de batches de segmentación.

Funcionalidades principales:
- Vista de equipo con tarjetas interactivas  
- Dashboard con edición inline de estados y fechas
- Filtrado automático por responsable
- API RESTful completa
- Integración con MongoDB

Versión: 1.0.0 - Sistema completamente funcional
Fecha: Julio 23, 2025
Equipo: Mauricio, Maggie, Ceci, Flor, Ignacio
"""

from flask import Flask, render_template, request, jsonify, redirect, send_file
from db import get_db, create_indexes
import json
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)

# Configuración del directorio de datos
DATA_DIRECTORY = os.environ.get("DATA_DIRECTORY", "/home/faservin/american_project")

# Seguridad
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "DeepEye2025")
PROJECT_NAME = os.environ.get("PROJECT_NAME", "Quality Hope")

# No crear la conexión en import time
db = None

batches_col = None
masks_col = None
segmentadores_col = None

# Conexiones a Quality_Hope (base de datos unificada)
quality_db = None
quality_segmentadores_col = None
training_db = None
training_masks_col = None
external_masks_col = None  # DB externa del segmentador

def get_user_role(username):
    """Obtener el rol de un usuario desde la base de datos. Devuelve 'admin' o 'segmentador'."""
    global quality_segmentadores_col
    if quality_segmentadores_col is None:
        return "segmentador"
    try:
        user = quality_segmentadores_col.find_one({"name": username})
        if user and "role" in user:
            return user.get("role", "segmentador")
        return "segmentador"
    except Exception as e:
        print(f"[WARN] Error obteniendo rol de {username}: {e}")
        return "segmentador"

def is_admin(username):
    """Verificar si un usuario tiene rol de administrador."""
    return get_user_role(username) == "admin"

def admin_required(f):
    """Decorator para proteger rutas que solo admins pueden acceder."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user = kwargs.get('assignee') or request.args.get('user')
        if not current_user and request.is_json:
            current_user = request.json.get('current_user')
        if not current_user:
            return redirect('/team')
        if not is_admin(current_user):
            return render_template(
                'error.html',
                error_title="Acceso Denegado",
                error_message="Solo administradores pueden acceder a esta sección.",
                current_user=current_user
            ), 403
        return f(*args, **kwargs)

    return decorated_function

def init_db():
    global db, batches_col, masks_col, segmentadores_col, CREW_MEMBERS
    global quality_db, quality_segmentadores_col, training_db, training_masks_col
    global external_masks_col

    # Conexión a Quality_Hope (batches, segmentadores, masks, reportes)
    db = get_db(raise_on_fail=False)
    if db is not None:
        batches_col = db["batches"]
        masks_col = db["masks.files"]
        segmentadores_col = db["segmentadores"]
        create_indexes()
        print("✅ Conectado a Quality_Hope")
    else:
        print("⚠️ Quality_Hope no disponible")

    # segmentadores — misma BD Quality_Hope
    from db import get_quality_db
    quality_db = get_quality_db()
    if quality_db is not None:
        quality_segmentadores_col = quality_db["segmentadores"]
        load_segmentadores_from_db()
        print("✅ Quality_Hope.segmentadores listo")
    else:
        print("⚠️ Quality_Hope.segmentadores no disponible")

    # masks.files — misma BD Quality_Hope
    from db import get_training_db
    training_db = get_training_db()
    if training_db is not None:
        training_masks_col = training_db["masks.files"]
        print("✅ Quality_Hope.masks.files listo")
    else:
        print("⚠️ Quality_Hope.masks.files no disponible")

    # Conexión a DB externa del segmentador (sincronización de máscaras)
    MASKS_DB_NAME = os.environ.get("MASKS_DB", "segmentor_dev")
    MASKS_COLLECTION = os.environ.get("MASKS_COLLECTION", "segmentation_masks.mask.files")
    try:
        from pymongo import MongoClient
        ext_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        ext_client.admin.command("ping")
        external_masks_col = ext_client[MASKS_DB_NAME][MASKS_COLLECTION]
        print(f"✅ DB externa de máscaras: {MASKS_DB_NAME}.{MASKS_COLLECTION}")
    except Exception as e:
        external_masks_col = None
        print(f"⚠️ DB externa de máscaras no disponible: {e}")

def load_segmentadores_from_db():
    """Cargar lista de segmentadores desde Quality_Hope.segmentadores"""
    global CREW_MEMBERS, quality_segmentadores_col
    try:
        if quality_segmentadores_col is not None:
            # Verificar si hay segmentadores en Quality_Hope.segmentadores
            count = quality_segmentadores_col.count_documents({})
            if count > 0:
                # Cargar desde Quality_Hope.segmentadores
                segmentadores = list(quality_segmentadores_col.find({}, {"_id": 0, "name": 1}).sort("name", 1))
                CREW_MEMBERS = [seg["name"] for seg in segmentadores]
                print(f"✅ {len(CREW_MEMBERS)} segmentadores cargados desde Quality_Hope.segmentadores: {CREW_MEMBERS}")
            else:
                CREW_MEMBERS = []
                print("[INFO] Sin segmentadores en BD, iniciando limpio")
        else:
            CREW_MEMBERS = []
            print("[WARN] Quality_Hope.segmentadores no disponible")
    except Exception as e:
        CREW_MEMBERS = []
        print(f"[WARN] Error cargando segmentadores: {e}")

# Lista de miembros del equipo (será cargada desde MongoDB en init_db)
CREW_MEMBERS = []

@app.route("/")
def index():
    return render_template("team.html", crew=CREW_MEMBERS)

@app.route("/team")
def team():
    return render_template("team.html", crew=CREW_MEMBERS)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", crew=CREW_MEMBERS)

@app.route("/dashboard/<assignee>")
def dashboard_filtered(assignee):
    return render_template("dashboard.html", crew=CREW_MEMBERS, filter_assignee=assignee)

@app.route("/assign")
def assign_batches():
    """Página para asignar batches"""
    return render_template("batch_management.html", crew=CREW_MEMBERS)

@app.route("/batch-management")
def batch_management():
    """Redirigir a la nueva ruta /assign"""
    return redirect("/assign")

@app.route("/batch-assignment-v2")
def batch_assignment_v2():
    """Nueva interfaz de asignación de batches - Diseño moderno"""
    global CREW_MEMBERS
    return render_template("batch_assignment_v2.html", crew=CREW_MEMBERS)

@app.route("/masks")
def masks():
    global training_masks_col
    if training_masks_col is None:
        # Intentar reconectar a demanda
        from db import get_training_db
        training_db_local = get_training_db()
        if training_db_local is not None:
            training_masks_col = training_db_local["masks.files"]
        else:
            return jsonify({"error": "No DB connection to Quality_Hope"}), 503

    # Trae todos los documentos de máscaras desde Quality_Hope.masks.files
    docs = list(training_masks_col.find({}, {"_id": 0, "filename": 1, "uploadDate": 1}))
    return render_template("masks.html", files=docs)

@app.route("/metrics")
def metrics():
    """Página de estadísticas globales"""
    return render_template("metrics_overview.html", crew=CREW_MEMBERS)

@app.route("/logout")
def logout():
    """Cerrar sesión (placeholder)"""
    # Por ahora solo redirige al inicio
    # Implementar autenticación en el futuro
    return redirect("/")

@app.route("/api/batches", methods=["GET"])
def get_batches():
    """Endpoint paginado: ?page=1&per_page=50"""
    global batches_col
    if batches_col is None:
        # intentar reconectar a demanda
        db_local = get_db(raise_on_fail=False)
        if db_local is not None:
            batches_col = db_local["batches"]
            print("✅ Conexión a MongoDB restablecida en get_batches")
        else:
            print("❌ No se pudo conectar a MongoDB en get_batches")
            return jsonify({"error":"No DB connection"}), 503

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = int(request.args.get("per_page", 50))
        per_page = min(max(5, per_page), 1000)  # límites razonables aumentados

        skip = (page - 1) * per_page

        # Proyección para evitar traer campos pesados
        projection = {"_id": 0}

        cursor = batches_col.find({}, projection).sort("id", 1).skip(skip).limit(per_page)
        items = list(cursor)

        total = batches_col.count_documents({})

        return jsonify({
            "batches": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        print("❌ Error en get_batches:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/batches", methods=["POST"])
def create_batch():
    try:
        data = request.json
        print(f"📝 Datos recibidos para crear batch: {data}")
        
        # Generar nuevo ID si no se proporciona
        if "id" not in data or not data["id"]:
            existing_batches = list(batches_col.find({}, {"id": 1}))
            existing_ids = [int(b["id"].replace("batch_", "")) for b in existing_batches if "batch_" in b["id"]]
            new_id = max(existing_ids) + 1 if existing_ids else 1
            batch_id = f"batch_{new_id}"
        else:
            batch_id = data["id"]
        
        # Crear el batch con la nueva estructura
        batch = {
            "id": batch_id,
            "assignee": data.get("assignee", ""),
            "folder": data.get("folder", f"{DATA_DIRECTORY}/{batch_id}"),
            "tasks": data.get("tasks", ["segmentar", "subir_mascaras", "revisar"]),
            "metadata": {
                "assigned_at": data.get("metadata", {}).get("assigned_at", datetime.now().strftime("%Y-%m-%d")),
                "due_date": data.get("metadata", {}).get("due_date", ""),
                "priority": data.get("metadata", {}).get("priority", "media"),
                "reviewed_at": data.get("metadata", {}).get("reviewed_at", None)
            },
            "status": data.get("status", "NS"),  # NS = No Segmentado por defecto
            "mongo_uploaded": data.get("mongo_uploaded", False),
            "comments": data.get("comments", "")
        }
        
        print(f"✅ Batch creado: {batch}")

        batches_col.insert_one(batch)

        # Remover el ObjectId para la respuesta JSON
        batch_response = batch.copy()
        if '_id' in batch_response:
            del batch_response['_id']
        
        return jsonify({
            "success": True,
            "message": f"Batch {batch_id} creado exitosamente",
            "batch": batch_response
        })
        
    except Exception as e:
        print(f"❌ Error creando batch: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/batches/<batch_id>", methods=["PUT"])
def update_batch(batch_id):
    data = request.json

    update_data = {}

    # Campos directos
    if "assignee" in data:
        # Permitir explícitamente None/null para desasignar
        update_data["assignee"] = data["assignee"] if data["assignee"] else None
        print(f"🔄 Actualizando assignee de {batch_id} a: {update_data['assignee']}")

    if "status" in data:
        update_data["status"] = data["status"]
    if "comments" in data:
        update_data["comments"] = data["comments"]
    if "folder" in data:
        update_data["folder"] = data["folder"]

    # Campos de metadata - nueva forma estructurada
    if "metadata" in data:
        metadata = data["metadata"]
        for key, value in metadata.items():
            update_data[f"metadata.{key}"] = value

    # Campos individuales de metadata (retrocompatibilidad)
    if "due_date" in data:
        update_data["metadata.due_date"] = data["due_date"]
    if "priority" in data:
        update_data["metadata.priority"] = data["priority"]
    if "reviewed_at" in data:
        update_data["metadata.reviewed_at"] = data["reviewed_at"]

    result = batches_col.update_one({"id": batch_id}, {"$set": update_data})

    if result.modified_count > 0 or batches_col.find_one({"id": batch_id}):
        print(f"✅ Batch {batch_id} actualizado correctamente")
        return jsonify({"success": True, "message": f"Batch {batch_id} actualizado"})
    else:
        return jsonify({"success": False, "error": "Batch no encontrado"}), 404

@app.route("/api/batches/<batch_id>/change-id", methods=["PUT"])
def change_batch_id(batch_id):
    """Cambiar el ID de un batch"""
    data = request.json
    new_id = data.get("new_id", "").strip()
    
    if not new_id:
        return jsonify({"success": False, "error": "Nuevo ID requerido"}), 400
    
    # Verificar que el nuevo ID no exista ya
    existing = batches_col.find_one({"id": new_id})
    if existing:
        return jsonify({"success": False, "error": f"El ID '{new_id}' ya existe"}), 400
    
    # Actualizar el ID
    result = batches_col.update_one(
        {"id": batch_id}, 
        {"$set": {"id": new_id}}
    )
    
    if result.modified_count > 0:
        return jsonify({"success": True, "message": f"ID actualizado de {batch_id} a {new_id}"})
    else:
        return jsonify({"success": False, "error": "Batch no encontrado"}), 404

@app.route("/api/batches/<batch_id>", methods=["DELETE"])
def delete_batch(batch_id):
    try:
        print(f"🗑️ Eliminando batch: {batch_id}")
        
        # Verificar que el batch existe antes de eliminarlo
        existing_batch = batches_col.find_one({"id": batch_id})
        if not existing_batch:
            return jsonify({
                "success": False, 
                "error": f"Batch '{batch_id}' no encontrado"
            }), 404
        
        # Eliminar el batch
        result = batches_col.delete_one({"id": batch_id})
        
        if result.deleted_count > 0:
            print(f"✅ Batch {batch_id} eliminado exitosamente")
            return jsonify({
                "success": True, 
                "message": f"Batch {batch_id} eliminado exitosamente",
                "deleted_batch": {
                    "id": batch_id,
                    "assignee": existing_batch.get("assignee", ""),
                    "status": existing_batch.get("status", "")
                }
            })
        else:
            print(f"❌ Error eliminando batch {batch_id}")
            return jsonify({
                "success": False, 
                "error": "Error al eliminar el batch"
            }), 500
            
    except Exception as e:
        print(f"❌ Error en delete_batch: {e}")
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500

@app.route("/api/add-segmentador", methods=["POST"])
def add_segmentador():
    """Agregar un nuevo segmentador al equipo y guardarlo en Quality_Hope.segmentadores"""
    global CREW_MEMBERS, quality_segmentadores_col

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No se enviaron datos"
            }), 400

        name = data.get("name", "").strip()
        role = data.get("role", "segmentador")
        email = data.get("email", "")
        admin_password = data.get("admin_password", "")

        # Validar que se proporcione un nombre
        if not name:
            return jsonify({
                "success": False,
                "error": "El nombre del segmentador es requerido"
            }), 400

        # Validar contraseña si es admin
        if role == "admin":
            if not admin_password:
                return jsonify({"success": False, "error": "Se requiere contraseña de administrador"}), 403
            if admin_password != ADMIN_PASSWORD:
                return jsonify({"success": False, "error": "Contraseña de administrador incorrecta"}), 403

        # Verificar que no exista ya
        if name in CREW_MEMBERS:
            return jsonify({
                "success": False,
                "error": f"El segmentador '{name}' ya existe en el equipo"
            }), 400

        # GUARDAR EN QUALITY_DASHBOARD
        if quality_segmentadores_col is None:
            return jsonify({
                "success": False,
                "error": "Quality_Hope.segmentadores no disponible"
            }), 503

        quality_segmentadores_col.insert_one({
            "name": name,
            "role": role,
            "email": email,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Agregar a memoria
        CREW_MEMBERS.append(name)

        print(f"✅ Segmentador '{name}' guardado en Quality_Hope.segmentadores y memoria")
        print(f"📋 Equipo actualizado: {CREW_MEMBERS}")

        return jsonify({
            "success": True,
            "message": f"Segmentador '{name}' agregado y guardado en Quality_Hope.segmentadores",
            "segmentador": {
                "name": name,
                "role": role,
                "email": email
            },
            "team_size": len(CREW_MEMBERS)
        })

    except Exception as e:
        print(f"❌ Error agregando segmentador: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/segmentadores", methods=["GET"])
def get_segmentadores():
    """Obtener la lista actual de segmentadores con sus roles"""
    try:
        roles = {member: get_user_role(member) for member in CREW_MEMBERS}
        docs = []
        if quality_segmentadores_col is not None:
            docs = list(quality_segmentadores_col.find(
                {}, {"_id": 0, "name": 1, "role": 1, "email": 1}
            ).sort("name", 1))
        else:
            docs = [{"name": m, "role": roles.get(m, "segmentador"), "email": ""} for m in CREW_MEMBERS]
        return jsonify({
            "success": True,
            "segmentadores": CREW_MEMBERS,
            "roles": roles,
            "members": docs,
            "total": len(CREW_MEMBERS)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/remove-segmentador", methods=["DELETE"])
def remove_segmentador():
    """Eliminar un segmentador del equipo y de Quality_Hope.segmentadores"""
    global CREW_MEMBERS, quality_segmentadores_col

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No se enviaron datos"
            }), 400

        name = data.get("name", "").strip()

        if not name:
            return jsonify({
                "success": False,
                "error": "El nombre es requerido"
            }), 400

        if name not in CREW_MEMBERS:
            return jsonify({
                "success": False,
                "error": f"El segmentador '{name}' no existe"
            }), 404

        # ELIMINAR DE QUALITY_DASHBOARD
        if quality_segmentadores_col is None:
            return jsonify({
                "success": False,
                "error": "Quality_Hope.segmentadores no disponible"
            }), 503

        result = quality_segmentadores_col.delete_one({"name": name})

        if result.deleted_count > 0:
            # Eliminar de memoria
            CREW_MEMBERS.remove(name)
            print(f"✅ Segmentador '{name}' eliminado de Quality_Hope.segmentadores y memoria")

            return jsonify({
                "success": True,
                "message": f"Segmentador '{name}' eliminado exitosamente",
                "team_size": len(CREW_MEMBERS)
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo eliminar de la base de datos"
            }), 500

    except Exception as e:
        print(f"❌ Error eliminando segmentador: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/update-segmentador", methods=["PUT"])
def update_segmentador():
    """Actualizar datos de un segmentador en Quality_Hope.segmentadores"""
    global CREW_MEMBERS, quality_segmentadores_col

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No se enviaron datos"
            }), 400

        old_name = data.get("old_name", "").strip()
        new_name = data.get("name", "").strip()
        role = data.get("role", "")
        email = data.get("email", "")

        if not old_name:
            return jsonify({
                "success": False,
                "error": "El nombre anterior es requerido"
            }), 400

        if not new_name:
            return jsonify({
                "success": False,
                "error": "El nuevo nombre es requerido"
            }), 400

        if old_name not in CREW_MEMBERS:
            return jsonify({
                "success": False,
                "error": f"El segmentador '{old_name}' no existe"
            }), 404

        # Si cambió el nombre, verificar que el nuevo no exista
        if old_name != new_name and new_name in CREW_MEMBERS:
            return jsonify({
                "success": False,
                "error": f"Ya existe un segmentador con el nombre '{new_name}'"
            }), 400

        # ACTUALIZAR EN QUALITY_DASHBOARD
        if quality_segmentadores_col is None:
            return jsonify({
                "success": False,
                "error": "Quality_Hope.segmentadores no disponible"
            }), 503

        update_data = {
            "name": new_name,
            "role": role,
            "email": email,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        result = quality_segmentadores_col.update_one(
            {"name": old_name},
            {"$set": update_data}
        )

        if result.modified_count > 0 or quality_segmentadores_col.find_one({"name": new_name}):
            # Actualizar memoria
            if old_name != new_name:
                index = CREW_MEMBERS.index(old_name)
                CREW_MEMBERS[index] = new_name

            print(f"✅ Segmentador actualizado: '{old_name}' -> '{new_name}'")

            return jsonify({
                "success": True,
                "message": f"Segmentador '{new_name}' actualizado exitosamente",
                "segmentador": update_data,
                "team_size": len(CREW_MEMBERS)
            })
        else:
            return jsonify({
                "success": False,
                "error": "No se pudo actualizar en la base de datos"
            }), 500

    except Exception as e:
        print(f"❌ Error actualizando segmentador: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/check-mongo-files", methods=["GET"])
def check_mongo_files():
    """Verificar qué archivos están actualmente en Quality_Hope.masks.files (OPTIMIZADO)"""
    global training_masks_col

    try:
        print("🔍 Iniciando verificación de archivos en Quality_Hope.masks.files...")

        # Verificar que la colección esté disponible
        if training_masks_col is None:
            return jsonify({
                "success": False,
                "error": "Quality_Hope.masks.files no disponible"
            }), 503

        # Verificar conexión primero
        try:
            # Test de conexión
            training_masks_col.find_one({}, {"_id": 1})
            print("✅ Conexión a Quality_Hope.masks.files establecida")
        except Exception as conn_error:
            print(f"❌ Error de conexión a Quality_Hope.masks.files: {conn_error}")
            return jsonify({
                "success": False,
                "error": f"Error de conexión a Quality_Hope.masks.files: {str(conn_error)}"
            }), 500

        # OPTIMIZACIÓN: Solo proyectar campos necesarios y limitar resultados
        try:
            # Límite REDUCIDO: máximo 300 para no sobrecargar (antes 500)
            limit = min(int(request.args.get("limit", 100)), 300)

            files = list(training_masks_col.find(
                {},
                {"filename": 1, "uploadDate": 1, "metadata.uploaded_by": 1, "length": 1, "_id": 0}
            ).sort("uploadDate", -1).limit(limit))
            print(f"📊 Se encontraron {len(files)} archivos en Quality_Hope.masks.files (límite: {limit})")
        except Exception as query_error:
            print(f"❌ Error consultando archivos: {query_error}")
            return jsonify({
                "success": False,
                "error": f"Error consultando archivos: {str(query_error)}"
            }), 500
        
        files_info = []
        for file in files:
            try:
                file_data = {
                    "filename": file.get("filename", "Sin nombre"),
                    "uploadDate": file.get("uploadDate").isoformat() if file.get("uploadDate") else None,
                    "size_mb": round(file.get("length", 0) / (1024*1024), 2) if file.get("length") else 0,
                    "uploaded_by": file.get("metadata", {}).get("uploaded_by", "unknown") if file.get("metadata") else "unknown"
                }
                files_info.append(file_data)
            except Exception as file_error:
                print(f"⚠️ Error procesando archivo {file.get('_id', 'unknown')}: {file_error}")
                continue
        
        # Contar archivos por patrón de batch
        batch_patterns = {}
        try:
            import re
            for file in files:
                filename = file.get("filename", "")
                if not filename:
                    continue
                    
                # Buscar patrones como batch_XX, Batch_XX, masks_batch_XX
                batch_matches = re.findall(r'[Bb]atch[_\-]?(\d+)', filename)
                for match in batch_matches:
                    batch_key = f"batch_{match}"
                    if batch_key not in batch_patterns:
                        batch_patterns[batch_key] = []
                    batch_patterns[batch_key].append(filename)
        except Exception as pattern_error:
            print(f"⚠️ Error procesando patrones: {pattern_error}")
            batch_patterns = {}
        
        print(f"📊 Patrones encontrados: {len(batch_patterns)} batches diferentes")

        return jsonify({
            "success": True,
            "total_files": len(files_info),
            "recent_files": files_info,
            "batch_patterns": batch_patterns,
            "database": "Quality_Hope",
            "collection": "masks.files",
            "message": f"Se encontraron {len(files_info)} archivos en Quality_Hope.masks.files"
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error general en check_mongo_files: {error_msg}")
        print(f"❌ Tipo de error: {type(e).__name__}")
        return jsonify({
            "success": False, 
            "error": f"Error verificando MongoDB: {error_msg}",
            "error_type": type(e).__name__
        }), 500

@app.route("/api/batch-files/<batch_id>", methods=["GET"])
def get_batch_files(batch_id):
    """Obtener información de archivos subidos para un batch específico"""
    global training_masks_col

    try:
        # Verificar que training_masks_col esté disponible
        if training_masks_col is None:
            return jsonify({
                "success": False,
                "error": "Quality_Hope.masks.files no disponible"
            }), 503

        # Buscar archivos que coincidan con el patrón batch_XX
        pattern = f"masks_batch_{batch_id.replace('batch_', '')}"
        files = list(training_masks_col.find(
            {"filename": {"$regex": pattern}},
            {"filename": 1, "uploadDate": 1, "metadata": 1, "length": 1}
        ).sort("uploadDate", -1))
        
        # Procesar información
        file_info = {
            "batch_id": batch_id,
            "total_files": len(files),
            "latest_upload": None,
            "uploaded_by": None,
            "file_size": 0,
            "all_uploads": []
        }
        
        if files:
            latest = files[0]
            file_info["latest_upload"] = latest["uploadDate"]
            file_info["uploaded_by"] = latest.get("metadata", {}).get("uploaded_by", "unknown")
            file_info["file_size"] = latest.get("length", 0)
            
            # Lista de todas las subidas
            for file in files:
                file_info["all_uploads"].append({
                    "filename": file["filename"],
                    "uploadDate": file["uploadDate"],
                    "uploaded_by": file.get("metadata", {}).get("uploaded_by", "unknown"),
                    "size": file.get("length", 0)
                })
        
        return jsonify(file_info)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sync-batch-files", methods=["POST"])
def sync_batch_files():
    """Sincronizar batches con archivos — revisa Quality_Hope y DB externa del segmentador"""
    global training_masks_col, external_masks_col

    try:
        print("🔄 Iniciando sincronización de archivos con batches...")

        if training_masks_col is None and external_masks_col is None:
            return jsonify({
                "success": False,
                "error": "Ninguna colección de máscaras disponible"
            }), 503

        # Traer solo campos necesarios de batches
        batches = list(batches_col.find({}, {"id": 1, "mongo_uploaded": 1, "_id": 0}))

        import re

        # Construir identificadores por batch — soporta batch_XXX y pN_cam1_cam2_NNNNNN
        batch_identifiers = {}
        for batch in batches:
            batch_id = batch["id"]
            # Formato pN_cam1_cam2_NNNNNN → usar el ID completo
            if re.match(r'^p\d+_', batch_id):
                batch_identifiers[batch_id] = batch_id
            else:
                # Formato batch_XXX → extraer sufijo
                match = re.search(r'batch_(.+)', batch_id, re.IGNORECASE)
                if match:
                    batch_identifiers[batch_id] = match.group(1)
                else:
                    batch_identifiers[batch_id] = batch_id

        if not batch_identifiers:
            return jsonify({
                "success": True,
                "batches_updated": 0,
                "total_batches": 0,
                "message": "No hay batches para sincronizar"
            })

        # Construir patrón regex para una sola query
        escaped = [re.escape(v) for v in batch_identifiers.values()]
        numbers_pattern = "|".join(escaped)
        mega_pattern = f"(masks_)?(batch_|Batch_)?({numbers_pattern})"

        print(f"📊 Buscando en Quality_Hope y DB externa para {len(batch_identifiers)} batches...")

        # Query a Quality_Hope.masks.files
        all_files = []
        if training_masks_col is not None:
            qh_files = list(training_masks_col.find(
                {"filename": {"$regex": mega_pattern, "$options": "i"}},
                {"filename": 1, "uploadDate": 1, "_id": 0}
            ).sort("uploadDate", -1))
            all_files.extend(qh_files)
            print(f"  Quality_Hope: {len(qh_files)} archivos")

        # Query a DB externa del segmentador
        if external_masks_col is not None:
            ext_files = list(external_masks_col.find(
                {"filename": {"$regex": mega_pattern, "$options": "i"}},
                {"filename": 1, "uploadDate": 1, "_id": 0}
            ).sort("uploadDate", -1))
            all_files.extend(ext_files)
            print(f"  DB externa: {len(ext_files)} archivos")

        print(f"✅ Total archivos encontrados: {len(all_files)}")

        # Mapear archivos a batches en memoria
        batch_file_map = {}
        for batch_id, identifier in batch_identifiers.items():
            batch_file_map[batch_id] = [
                f for f in all_files if identifier in f.get("filename", "")
            ]

        # OPTIMIZACIÓN 5: Actualizar batches en bulk
        updated_batches = 0
        sync_results = []
        bulk_operations = []

        for batch in batches:
            batch_id = batch["id"]
            current_mongo_status = batch.get("mongo_uploaded", False)
            files_for_batch = batch_file_map.get(batch_id, [])
            has_files = len(files_for_batch) > 0

            # Solo actualizar si hay cambios
            if current_mongo_status != has_files:
                bulk_operations.append({
                    "filter": {"id": batch_id},
                    "update": {
                        "$set": {
                            "mongo_uploaded": has_files,
                            "file_info": {
                                "file_count": len(files_for_batch),
                                "last_file_upload": files_for_batch[0]["uploadDate"] if files_for_batch else None,
                                "has_files": has_files
                            }
                        }
                    }
                })
                updated_batches += 1

            sync_results.append({
                "batch_id": batch_id,
                "files_found": len(files_for_batch),
                "mongo_uploaded": has_files,
                "updated": current_mongo_status != has_files
            })

        # Ejecutar todas las actualizaciones de una vez (bulk write)
        if bulk_operations:
            from pymongo import UpdateOne
            batches_col.bulk_write([UpdateOne(op["filter"], op["update"]) for op in bulk_operations])

        print(f"🔄 Sincronización completa: {updated_batches} batches actualizados (OPTIMIZADO)")

        return jsonify({
            "success": True,
            "batches_updated": updated_batches,
            "total_batches": len(sync_results),
            "total_files_found": len(all_files),
            "message": f"Sincronización optimizada: {updated_batches} batches actualizados",
            "results": sync_results[:50]  # Limitar resultado para no sobrecargar respuesta
        })

    except Exception as e:
        print(f"❌ Error en sincronización: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/auto-create-batches", methods=["POST"])
def auto_create_batches():
    """Crear batches automáticamente (OPTIMIZADO: solo filename, sin metadata pesada)"""
    global training_masks_col

    try:
        print("🤖 Iniciando creación automática de batches...")

        # Verificar que training_masks_col esté disponible
        if training_masks_col is None:
            return jsonify({
                "success": False,
                "error": "Quality_Hope.masks.files no disponible"
            }), 503

        # OPTIMIZACIÓN: Solo traer filename, no metadata ni length desde Quality_Hope.masks.files
        # LÍMITE REDUCIDO: 5000 archivos (reducir carga de memoria)
        files = list(training_masks_col.find(
            {},
            {"filename": 1, "_id": 0}  # Solo filename necesario
        ).limit(5000))  # Límite de seguridad reducido

        # Extraer números de batch de los nombres de archivos
        import re
        batch_numbers = set()
        for file in files:
            filename = file.get("filename", "")
            # Buscar patrones como batch_XXXX, Batch_XXXX
            batch_matches = re.findall(r'[Bb]atch[_\-]?(\d+)', filename)
            for match in batch_matches:
                batch_numbers.add(match)

        print(f"📊 Números de batch encontrados: {len(batch_numbers)}")

        # OPTIMIZACIÓN: Solo IDs de batches existentes (proyección mínima)
        # Usar set comprehension directamente para ahorrar memoria
        existing_ids = {b["id"] for b in batches_col.find({}, {"id": 1, "_id": 0})}

        created_batches = 0
        results = []

        # OPTIMIZACIÓN: Preparar bulk insert
        batches_to_insert = []

        for batch_num in sorted(batch_numbers):
            batch_id = f"batch_{batch_num}"

            if batch_id not in existing_ids:
                # Preparar batch para inserción bulk
                batch = {
                    "id": batch_id,
                    "assignee": "Maggie",
                    "folder": f"{DATA_DIRECTORY}/{batch_id}",
                    "tasks": ["segmentar", "subir_mascaras", "revisar"],
                    "metadata": {
                        "assigned_at": datetime.now().strftime("%Y-%m-%d"),
                        "due_date": "",
                        "priority": "media",
                        "reviewed_at": None
                    },
                    "status": "NS",
                    "mongo_uploaded": True,
                    "comments": "Batch creado automáticamente"
                }

                batches_to_insert.append(batch)
                results.append({
                    "batch_id": batch_id,
                    "created": True,
                    "assignee": "Maggie"
                })
            else:
                results.append({
                    "batch_id": batch_id,
                    "created": False,
                    "reason": "Ya existe"
                })

        # OPTIMIZACIÓN: Insertar todos de una vez (bulk insert)
        if batches_to_insert:
            batches_col.insert_many(batches_to_insert)
            created_batches = len(batches_to_insert)
            print(f"✅ {created_batches} batches creados en bulk")

        return jsonify({
            "success": True,
            "created_batches": created_batches,
            "total_found": len(batch_numbers),
            "message": f"Se crearon {created_batches} nuevos batches (optimizado)",
            "results": results[:100]  # Limitar respuesta
        })

    except Exception as e:
        print(f"❌ Error en auto_create_batches: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/init-batches", methods=["POST"])
def init_batches():
    """Inicializar batches SOLO si la colección está vacía o si se especifica forzar"""
    try:
        # Manejar tanto requests con JSON como sin JSON
        if request.is_json:
            force_reload = request.json.get("force", False)
        else:
            # Si no hay JSON, verificar parámetro en URL o asumir False
            force_reload = request.args.get("force", "false").lower() == "true"
        
        # Verificar si ya hay batches en la colección
        existing_count = batches_col.count_documents({})
        
        if existing_count > 0 and not force_reload:
            print(f"📊 Ya existen {existing_count} batches en la colección, omitiendo inicialización")
            return jsonify({
                "success": True, 
                "message": f"Batches ya inicializados: {existing_count} batches existentes",
                "existing_count": existing_count,
                "loaded": False
            })
        
        # Solo cargar desde JSON si no hay datos o si se fuerza
        if force_reload:
            print("🔄 Forzando reinicialización - limpiando datos existentes")
            batches_col.delete_many({})
        
        with open("batches.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("batches"):
                # Verificar duplicados antes de insertar
                loaded_count = 0
                for batch in data["batches"]:
                    existing = batches_col.find_one({"id": batch["id"]})
                    if not existing:
                        batches_col.insert_one(batch)
                        loaded_count += 1
                        print(f"➕ Batch {batch['id']} cargado")
                    else:
                        print(f"⚠️ Batch {batch['id']} ya existe, omitiendo")
                
                return jsonify({
                    "success": True, 
                    "message": f"Inicialización completa: {loaded_count} nuevos batches cargados",
                    "loaded_count": loaded_count,
                    "total_in_file": len(data["batches"]),
                    "loaded": True
                })
            else:
                return jsonify({
                    "success": False, 
                    "error": "No se encontraron batches en el archivo JSON"
                })
                
    except Exception as e:
        print(f"❌ Error en init_batches: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/reset-batches", methods=["POST"])
def reset_batches():
    # Endpoint para limpiar y recargar completamente los batches
    try:
        batches_col.delete_many({})
        with open("batches.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("batches"):
                batches_col.insert_many(data["batches"])
        return jsonify({"success": True, "message": f"Base de datos limpiada y {len(data['batches'])} batches cargados"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/missing-batches", methods=["GET"])
def get_missing_batches():
    """Obtener batches que FALTAN por segmentar (desde batches.json)"""
    try:
        # Leer batches desde batches.json
        with open("batches.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            all_possible_batches = [batch["id"] for batch in data.get("batches", [])]

        print(f"📁 Leídos {len(all_possible_batches)} batches desde batches.json")

        # Obtener batches que YA están en la base de datos
        existing_batch_ids = set()
        for batch in batches_col.find({}, {"id": 1, "_id": 0}):
            existing_batch_ids.add(batch["id"])

        # Filtrar para obtener solo los que FALTAN (no están en la DB)
        missing_batches = [batch_id for batch_id in all_possible_batches
                          if batch_id not in existing_batch_ids]

        print(f"📊 Total batches en batches.json: {len(all_possible_batches)}")
        print(f"📊 Batches en DB: {len(existing_batch_ids)}")
        print(f"📊 Batches faltantes: {len(missing_batches)}")

        return jsonify({
            "success": True,
            "missing_batches": missing_batches,
            "total_missing": len(missing_batches),
            "total_existing": len(existing_batch_ids),
            "source": "batches.json",
            "message": f"Se encontraron {len(missing_batches)} batches pendientes de asignar"
        })

    except Exception as e:
        print(f"❌ Error obteniendo batches faltantes: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/metrics/overview", methods=["GET"])
def get_metrics_overview():
    """Obtener estadísticas globales del sistema"""
    try:
        global batches_col
        if batches_col is None:
            db_local = get_db(raise_on_fail=False)
            if db_local is not None:
                batches_col = db_local["batches"]
            else:
                return jsonify({"error": "No DB connection"}), 503

        # Agregación para estadísticas globales
        pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }
            }
        ]

        results = list(batches_col.aggregate(pipeline)) or []

        # Inicializar contadores (valores seguros por defecto)
        stats = {
            "total_batches": 0,
            "completed_batches": 0,  # S
            "in_progress_batches": 0,  # FS
            "pending_batches": 0,     # NS
            "unassigned_batches": 0   # assignee null/empty
        }

        # Procesar resultados de agregación
        for result in results:
            status = result.get("_id")
            count = result.get("count", 0)
            stats["total_batches"] += count

            if status == "S":
                stats["completed_batches"] = count
            elif status == "FS":
                stats["in_progress_batches"] = count
            elif status == "NS":
                stats["pending_batches"] = count

        # Contar batches sin asignar (con manejo de error)
        try:
            unassigned_count = batches_col.count_documents({
                "$or": [
                    {"assignee": {"$exists": False}},
                    {"assignee": None},
                    {"assignee": ""},
                    {"assignee": {"$regex": "^\\s*$"}}
                ]
            })
            stats["unassigned_batches"] = unassigned_count
        except Exception as count_error:
            print(f"⚠️ Error contando sin asignar: {count_error}")
            stats["unassigned_batches"] = 0

        # Calcular porcentaje de completado (división segura)
        completion_rate = (stats["completed_batches"] / stats["total_batches"] * 100) if stats["total_batches"] > 0 else 0

        return jsonify({
            "success": True,
            "data": stats,
            "completion_rate": round(completion_rate, 1),
            "message": f"Estadísticas calculadas para {stats['total_batches']} batches"
        })

    except Exception as e:
        print(f"❌ Error en metrics overview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/metrics/team", methods=["GET"])
def get_metrics_team():
    """Obtener métricas por miembro del equipo con paridad de datos (OPTIMIZADO)"""
    try:
        global batches_col
        if batches_col is None:
            db_local = get_db(raise_on_fail=False)
            if db_local is not None:
                batches_col = db_local["batches"]
            else:
                return jsonify({"error": "No DB connection"}), 503

        # OPTIMIZACIÓN: Agregación con proyección mínima y límite de batches
        pipeline = [
            {
                "$project": {  # Proyectar solo campos necesarios PRIMERO
                    "id": 1,
                    "assignee": 1,
                    "status": 1,
                    "metadata.assigned_at": 1
                }
            },
            {
                "$addFields": {
                    "assignee_normalized": {
                        "$cond": {
                            "if": {"$or": [
                                {"$eq": ["$assignee", None]},
                                {"$eq": ["$assignee", ""]},
                                {"$not": ["$assignee"]}
                            ]},
                            "then": "Sin asignar",
                            "else": "$assignee"
                        }
                    },
                    # Usar metadata.assigned_at si existe, sino usar fecha por defecto
                    "sort_date": {
                        "$ifNull": ["$metadata.assigned_at", "1970-01-01"]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$assignee_normalized",
                    "total": {"$sum": 1},
                    "completed": {"$sum": {"$cond": [{"$eq": ["$status", "S"]}, 1, 0]}},
                    "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "FS"]}, 1, 0]}},
                    "pending": {"$sum": {"$cond": [{"$eq": ["$status", "NS"]}, 1, 0]}},
                    "batches": {"$push": {
                        "id": "$id",
                        "status": "$status",
                        "sort_date": "$sort_date"
                    }}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ]

        results = list(batches_col.aggregate(pipeline))

        # Procesar resultados y agregar recent_batches
        team_metrics = []
        for result in results:
            assignee = result["_id"]

            # OPTIMIZACIÓN: Ordenar y tomar solo 3 más recientes en una sola pasada
            batches = result["batches"]
            # Usar sorted con slice para evitar ordenar todos si hay muchos
            recent_batches_full = sorted(batches, key=lambda x: x.get("sort_date", "1970-01-01"), reverse=True)[:3]
            recent_batches = [batch["id"] for batch in recent_batches_full]

            # Calcular eficiencia: S / (S + FS)
            active_work = result["completed"] + result["in_progress"]
            efficiency = round((result["completed"] / active_work * 100), 1) if active_work > 0 else 0

            team_metrics.append({
                "assignee": assignee,
                "total": result["total"],
                "completed": result["completed"],
                "in_progress": result["in_progress"],
                "pending": result["pending"],
                "completion_rate": round((result["completed"] / result["total"] * 100), 1) if result["total"] > 0 else 0,
                "efficiency": efficiency,
                "recent_batches": recent_batches
            })

        # Asegurar que todos los miembros del equipo aparezcan (incluso con 0 batches)
        existing_assignees = {metric["assignee"] for metric in team_metrics}
        for member in CREW_MEMBERS:
            if member not in existing_assignees:
                team_metrics.append({
                    "assignee": member,
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "pending": 0,
                    "completion_rate": 0,
                    "efficiency": 0,
                    "recent_batches": []
                })

        # Ordenar por nombre de assignee
        team_metrics.sort(key=lambda x: x["assignee"])

        return jsonify({
            "success": True,
            "data": team_metrics,
            "total_members": len(CREW_MEMBERS),
            "message": f"Métricas calculadas para {len(team_metrics)} miembros"
        })

    except Exception as e:
        print(f"❌ Error en metrics team: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/metrics/progress", methods=["GET"])
def get_metrics_progress():
    """Obtener serie temporal de progreso con filtros opcionales"""
    try:
        global batches_col
        if batches_col is None:
            db_local = get_db(raise_on_fail=False)
            if db_local is not None:
                batches_col = db_local["batches"]
            else:
                return jsonify({"error": "No DB connection"}), 503

        # Obtener parámetros de filtro
        from_date = request.args.get("from")  # YYYY-MM-DD
        to_date = request.args.get("to")      # YYYY-MM-DD
        assignees_param = request.args.get("assignees")  # "Flor,Mauricio"

        # Construir filtro de match
        match_filter = {
            "metadata.assigned_at": {"$exists": True, "$ne": None, "$ne": ""}
        }

        # Filtro por rango de fechas
        if from_date or to_date:
            date_filter = {}
            if from_date:
                date_filter["$gte"] = from_date
            if to_date:
                date_filter["$lte"] = to_date
            match_filter["metadata.assigned_at"] = {**match_filter["metadata.assigned_at"], **date_filter}

        # Filtro por assignees
        if assignees_param:
            assignees_list = [a.strip() for a in assignees_param.split(",") if a.strip()]
            if assignees_list:
                match_filter["assignee"] = {"$in": assignees_list}

        # Agregación por fecha de asignación
        pipeline = [
            {"$match": match_filter},
            {
                "$group": {
                    "_id": "$metadata.assigned_at",
                    "total": {"$sum": 1},
                    "completed": {"$sum": {"$cond": [{"$eq": ["$status", "S"]}, 1, 0]}},
                    "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "FS"]}, 1, 0]}},
                    "pending": {"$sum": {"$cond": [{"$eq": ["$status", "NS"]}, 1, 0]}}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        results = list(batches_col.aggregate(pipeline))

        # Procesar resultados
        progress_data = []
        for result in results:
            date = result["_id"]
            progress_data.append({
                "date": date,
                "total": result["total"],
                "completed": result["completed"],
                "in_progress": result["in_progress"],
                "pending": result["pending"],
                "completion_rate": round((result["completed"] / result["total"] * 100), 1) if result["total"] > 0 else 0
            })

        return jsonify({
            "success": True,
            "data": progress_data,
            "total_dates": len(progress_data),
            "filters": {
                "from": from_date,
                "to": to_date,
                "assignees": assignees_param
            },
            "message": f"Serie temporal calculada para {len(progress_data)} fechas"
        })

    except Exception as e:
        print(f"❌ Error en metrics progress: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/metrics/export", methods=["GET"])
def export_metrics():
    """Exportar métricas a CSV con filtros opcionales"""
    try:
        global batches_col
        if batches_col is None:
            db_local = get_db(raise_on_fail=False)
            if db_local is not None:
                batches_col = db_local["batches"]
            else:
                return "Error: No DB connection", 503

        # Obtener parámetros de filtro (sanitizados)
        from_date = request.args.get("from", "").strip()
        to_date = request.args.get("to", "").strip()
        assignees_param = request.args.get("assignees", "").strip()

        # Construir pipeline de agregación con assignee expandido
        match_filter = {}

        # Filtro por rango de fechas
        if from_date or to_date:
            date_filter = {}
            if from_date:
                date_filter["$gte"] = from_date
            if to_date:
                date_filter["$lte"] = to_date
            match_filter["metadata.assigned_at"] = date_filter

        # Filtro por assignees
        if assignees_param:
            assignees_list = [a.strip() for a in assignees_param.split(",") if a.strip()]
            if assignees_list:
                match_filter["assignee"] = {"$in": assignees_list}

        # Agregación por fecha y assignee
        pipeline = [
            {
                "$addFields": {
                    "assignee_display": {
                        "$cond": {
                            "if": {"$or": [
                                {"$eq": ["$assignee", None]},
                                {"$eq": ["$assignee", ""]},
                                {"$not": ["$assignee"]}
                            ]},
                            "then": "Sin asignar",
                            "else": "$assignee"
                        }
                    }
                }
            }
        ]

        if match_filter:
            pipeline.insert(0, {"$match": match_filter})

        pipeline.extend([
            {
                "$group": {
                    "_id": {
                        "date": "$metadata.assigned_at",
                        "assignee": "$assignee_display"
                    },
                    "total": {"$sum": 1},
                    "S": {"$sum": {"$cond": [{"$eq": ["$status", "S"]}, 1, 0]}},
                    "FS": {"$sum": {"$cond": [{"$eq": ["$status", "FS"]}, 1, 0]}},
                    "NS": {"$sum": {"$cond": [{"$eq": ["$status", "NS"]}, 1, 0]}}
                }
            },
            {
                "$sort": {"_id.date": 1, "_id.assignee": 1}
            }
        ])

        results = list(batches_col.aggregate(pipeline))

        # Generar CSV
        from io import StringIO
        import csv

        output = StringIO()
        writer = csv.writer(output)

        # Headers
        writer.writerow(['date', 'assignee', 'total', 'S', 'FS', 'NS', 'completionRate', 'efficiency'])

        # Datos
        for result in results:
            date = result["_id"]["date"] or "Sin fecha"
            assignee = result["_id"]["assignee"]
            total = result["total"]
            completed = result["S"]
            in_progress = result["FS"]
            pending = result["NS"]

            completion_rate = round((completed / total * 100), 1) if total > 0 else 0
            active_work = completed + in_progress
            efficiency = round((completed / active_work * 100), 1) if active_work > 0 else 0

            writer.writerow([
                date,
                assignee,
                total,
                completed,
                in_progress,
                pending,
                completion_rate,
                efficiency
            ])

        # Si no hay datos, solo headers
        csv_content = output.getvalue()
        output.close()

        # Generar nombre de archivo con timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"progress_{timestamp}.csv"

        # Crear respuesta
        response = app.make_response(csv_content)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"

        return response

    except Exception as e:
        print(f"❌ Error en metrics export: {e}")
        return f"Error: {str(e)}", 500

# ============================================
# MÓDULO DE GESTIÓN DE DATOS
# ============================================

@app.route("/data-management")
def data_management():
    """Página de gestión de datos (cargar/borrar batches)"""
    return render_template("data_management.html", crew=CREW_MEMBERS)

@app.route("/api/data/batches/upload", methods=["POST"])
def upload_batches_json():
    """Cargar batches desde un archivo JSON"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        data = request.json
        batches = data.get("batches", [])

        if not batches:
            return jsonify({"success": False, "error": "No se encontraron batches en el JSON"}), 400

        # Validar estructura de batches
        required_fields = ["id"]
        invalid_batches = []

        for idx, batch in enumerate(batches):
            if not all(field in batch for field in required_fields):
                invalid_batches.append(idx)

        if invalid_batches:
            return jsonify({
                "success": False,
                "error": f"Batches inválidos en índices: {invalid_batches}"
            }), 400

        # Opción: reemplazar todos o solo agregar nuevos
        mode = data.get("mode", "add")  # "add" o "replace"

        if mode == "replace":
            # Crear backup antes de borrar
            backup_batches = list(batches_col.find({}, {"_id": 0}))
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Guardar backup en archivo temporal
            import tempfile
            backup_file = os.path.join(tempfile.gettempdir(), f"batches_backup_{backup_timestamp}.json")
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump({"batches": backup_batches}, f, indent=2, default=str)

            print(f"💾 Backup guardado en: {backup_file}")

            # Borrar todos los batches existentes
            deleted = batches_col.delete_many({})
            print(f"🗑️ {deleted.deleted_count} batches eliminados")

        # Insertar nuevos batches con campos por defecto
        batches_to_insert = []
        for batch in batches:
            # Asegurar que tenga todos los campos necesarios
            batch_doc = {
                "id": batch.get("id"),
                "assignee": batch.get("assignee", None),
                "folder": batch.get("folder", f"{DATA_DIRECTORY}/{batch.get('id')}"),
                "tasks": batch.get("tasks", ["segmentar", "subir_mascaras", "revisar"]),
                "metadata": {
                    "assigned_at": batch.get("metadata", {}).get("assigned_at", None),
                    "due_date": batch.get("metadata", {}).get("due_date", ""),
                    "priority": batch.get("metadata", {}).get("priority", "media"),
                    "reviewed_at": batch.get("metadata", {}).get("reviewed_at", None)
                },
                "status": batch.get("status", "NS"),
                "mongo_uploaded": batch.get("mongo_uploaded", True),
                "comments": batch.get("comments", ""),
                "created_at": batch.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            }
            batches_to_insert.append(batch_doc)

        # Insertar batches
        result = batches_col.insert_many(batches_to_insert)

        return jsonify({
            "success": True,
            "message": f"{len(result.inserted_ids)} batches cargados exitosamente",
            "inserted_count": len(result.inserted_ids),
            "mode": mode,
            "backup_file": backup_file if mode == "replace" else None
        })

    except Exception as e:
        print(f"❌ Error cargando batches: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/data/batches/delete-by-filter", methods=["POST"])
def delete_batches_by_filter():
    """Eliminar batches basándose en filtros"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        data = request.json
        filter_criteria = {}

        # Construir filtro basado en criterios
        if "status" in data and data["status"]:
            filter_criteria["status"] = data["status"]

        if "assignee" in data and data["assignee"]:
            filter_criteria["assignee"] = data["assignee"]

        if "id_pattern" in data and data["id_pattern"]:
            filter_criteria["id"] = {"$regex": data["id_pattern"]}

        if "date_before" in data and data["date_before"]:
            filter_criteria["created_at"] = {"$lt": data["date_before"]}

        if "unassigned_only" in data and data["unassigned_only"]:
            filter_criteria["assignee"] = None

        # Verificar cuántos batches se borrarían
        count = batches_col.count_documents(filter_criteria)

        if count == 0:
            return jsonify({
                "success": False,
                "error": "No se encontraron batches que coincidan con los filtros"
            }), 404

        # Crear backup antes de borrar
        backup_batches = list(batches_col.find(filter_criteria, {"_id": 0}))
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        import tempfile
        backup_file = os.path.join(tempfile.gettempdir(), f"deleted_batches_{backup_timestamp}.json")
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({"batches": backup_batches}, f, indent=2, default=str)

        print(f"💾 Backup de batches a eliminar guardado en: {backup_file}")

        # Eliminar batches
        result = batches_col.delete_many(filter_criteria)

        return jsonify({
            "success": True,
            "message": f"{result.deleted_count} batches eliminados exitosamente",
            "deleted_count": result.deleted_count,
            "backup_file": backup_file
        })

    except Exception as e:
        print(f"❌ Error eliminando batches: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/data/batches/export", methods=["GET"])
def export_batches_json():
    """Exportar todos los batches a JSON"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        # Obtener todos los batches
        batches = list(batches_col.find({}, {"_id": 0}))

        # Crear JSON
        export_data = {
            "program": "Gestor de Batches de Segmentación",
            "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "crew": CREW_MEMBERS,
            "total_batches": len(batches),
            "batches": batches
        }

        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batches_export_{timestamp}.json"

        # Crear respuesta
        response = app.make_response(json.dumps(export_data, indent=2, default=str, ensure_ascii=False))
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "application/json; charset=utf-8"

        return response

    except Exception as e:
        print(f"❌ Error exportando batches: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/data/batches/stats", methods=["GET"])
def get_batches_stats():
    """Obtener estadísticas de batches"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        total = batches_col.count_documents({})

        # Estadísticas por estado
        status_stats = list(batches_col.aggregate([
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))

        # Estadísticas por asignado
        assignee_stats = list(batches_col.aggregate([
            {"$group": {"_id": "$assignee", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]))

        # Batches sin asignar
        unassigned = batches_col.count_documents({"assignee": None})

        # Batches por formato de ID
        id_patterns = {}
        sample_batches = list(batches_col.find({}, {"id": 1, "_id": 0}).limit(1000))

        for batch in sample_batches:
            batch_id = batch.get("id", "")
            # Detectar patrón
            if batch_id.startswith("batch_T"):
                pattern = "batch_T000XXX"
            elif batch_id.startswith("batch_000"):
                pattern = "batch_000XXX"
            elif batch_id.startswith("batch_2025"):
                pattern = "batch_2025XXXXXXXX"
            else:
                pattern = "otros"

            id_patterns[pattern] = id_patterns.get(pattern, 0) + 1

        return jsonify({
            "success": True,
            "stats": {
                "total": total,
                "unassigned": unassigned,
                "by_status": [{"status": s["_id"], "count": s["count"]} for s in status_stats],
                "by_assignee": [{"assignee": a["_id"], "count": a["count"]} for a in assignee_stats],
                "by_id_pattern": id_patterns
            }
        })

    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/batch-assignment/metrics", methods=["GET"])
def get_batch_assignment_metrics():
    """Obtener métricas detalladas para el módulo de asignación de batches"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        # Métricas globales
        total = batches_col.count_documents({})

        # Por estado
        ns_count = batches_col.count_documents({"status": "NS"})  # No Segmentado
        in_count = batches_col.count_documents({"status": "In"})  # Incompleto
        s_count = batches_col.count_documents({"status": "S"})    # Segmentado

        # Métricas por segmentador
        segmentadores_metrics = {}

        # Obtener lista de segmentadores del sistema
        for member in CREW_MEMBERS:
            # Total asignados al segmentador
            total_assigned = batches_col.count_documents({"assignee": member})

            # Por estado
            ns = batches_col.count_documents({"assignee": member, "status": "NS"})
            in_progress = batches_col.count_documents({"assignee": member, "status": "In"})
            completed = batches_col.count_documents({"assignee": member, "status": "S"})

            segmentadores_metrics[member] = {
                "total": total_assigned,
                "ns": ns,
                "in_progress": in_progress,
                "completed": completed,
                "percentage_completed": round((completed / total_assigned * 100) if total_assigned > 0 else 0, 1)
            }

        # Batches sin asignar
        unassigned = batches_col.count_documents({"assignee": None})

        return jsonify({
            "success": True,
            "metrics": {
                "global": {
                    "total": total,
                    "ns": ns_count,
                    "in_progress": in_count,
                    "completed": s_count,
                    "unassigned": unassigned
                },
                "by_segmentador": segmentadores_metrics
            }
        })

    except Exception as e:
        print(f"❌ Error obteniendo métricas de asignación: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# ENDPOINTS DE DESCARGA Y RESPALDO
# ============================================================================

@app.route("/api/export/segmentador/<segmentador>", methods=["GET"])
def export_segmentador_csv(segmentador):
    """Exportar batches de un segmentador específico en formato CSV"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        print(f"📥 Exportando datos de segmentador: {segmentador}")

        # Obtener batches del segmentador
        batches = list(batches_col.find({"assignee": segmentador}, {"_id": 0}).sort("id", 1))

        if not batches:
            return jsonify({
                "success": False,
                "error": f"No se encontraron batches para {segmentador}"
            }), 404

        # Obtener la fecha de asignación del primer batch (o fecha actual si no hay)
        first_batch_date = ""
        if batches:
            metadata = batches[0].get("metadata", {})
            assigned_at = metadata.get("assigned_at", "")
            if assigned_at:
                # Extraer solo la fecha (YYYY-MM-DD) sin la hora
                try:
                    # Formato esperado: "2025-10-15 14:30:00"
                    first_batch_date = assigned_at.split()[0].replace("-", "")  # 20251015
                except:
                    first_batch_date = datetime.now().strftime("%Y%m%d")
            else:
                first_batch_date = datetime.now().strftime("%Y%m%d")

        # Crear CSV en memoria
        output = io.StringIO()

        # Definir columnas SIMPLIFICADAS (solo ID, Nombre, Estatus vacío)
        fieldnames = ["Batch ID", "Responsable", "Estatus"]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Escribir datos
        for batch in batches:
            writer.writerow({
                "Batch ID": batch.get("id", ""),
                "Responsable": batch.get("assignee", ""),
                "Estatus": ""  # Campo vacío para que lo llene el segmentador
            })

        # Preparar respuesta
        output.seek(0)

        # Nombre del archivo: segmentador_fechaAsignacion.csv
        # Ejemplo: Mauricio_20251015.csv
        filename = f"{segmentador}_{first_batch_date}.csv"

        # Convertir a bytes para send_file
        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))  # BOM para Excel
        mem.seek(0)

        print(f"✅ Exportados {len(batches)} batches de {segmentador}")

        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"❌ Error exportando datos de {segmentador}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/export/all-assignments", methods=["GET"])
def export_all_assignments_csv():
    """Exportar todos los batches asignados en formato CSV (resumen por segmentador)"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        print(f"📥 Exportando resumen de asignaciones de todo el equipo")

        # Obtener estadísticas por segmentador
        pipeline = [
            {"$match": {"assignee": {"$ne": None}}},  # Solo asignados
            {"$group": {
                "_id": "$assignee",
                "total": {"$sum": 1},
                "ns": {"$sum": {"$cond": [{"$eq": ["$status", "NS"]}, 1, 0]}},
                "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "In"]}, 1, 0]}},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "S"]}, 1, 0]}},
                "batches": {"$push": "$id"}
            }},
            {"$sort": {"_id": 1}}
        ]

        results = list(batches_col.aggregate(pipeline))

        if not results:
            return jsonify({
                "success": False,
                "error": "No hay batches asignados"
            }), 404

        # Crear CSV en memoria
        output = io.StringIO()

        fieldnames = [
            "Segmentador", "Total Batches", "No Segmentados (NS)",
            "Incompletas (In)", "Completados (S)", "% Completado",
            "Lista de Batches"
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Escribir datos
        for result in results:
            segmentador = result["_id"]
            total = result["total"]
            completed = result["completed"]
            percentage = round((completed / total * 100) if total > 0 else 0, 1)
            batches_list = ", ".join(result["batches"])

            writer.writerow({
                "Segmentador": segmentador,
                "Total Batches": total,
                "No Segmentados (NS)": result["ns"],
                "Incompletas (In)": result["in_progress"],
                "Completados (S)": completed,
                "% Completado": f"{percentage}%",
                "Lista de Batches": batches_list
            })

        # Preparar respuesta
        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resumen_asignaciones_{timestamp}.csv"

        mem = io.BytesIO()
        mem.write(output.getvalue().encode('utf-8-sig'))
        mem.seek(0)

        print(f"✅ Exportado resumen de {len(results)} segmentadores")

        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"❌ Error exportando resumen de asignaciones: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/backup/database", methods=["GET"])
def backup_database():
    """Crear respaldo completo de la base de datos en JSON"""
    global batches_col, segmentadores_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        print("💾 Creando respaldo completo de la base de datos...")

        # Obtener todos los datos
        batches = list(batches_col.find({}, {"_id": 0}))
        segmentadores = list(segmentadores_col.find({}, {"_id": 0})) if segmentadores_col else []

        # Crear estructura del respaldo
        backup_data = {
            "backup_info": {
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0",
                "source": "Dashboard de Segmentación"
            },
            "statistics": {
                "total_batches": len(batches),
                "total_segmentadores": len(segmentadores),
                "batches_by_status": {
                    "NS": sum(1 for b in batches if b.get("status") == "NS"),
                    "In": sum(1 for b in batches if b.get("status") == "In"),
                    "S": sum(1 for b in batches if b.get("status") == "S")
                }
            },
            "segmentadores": segmentadores,
            "batches": batches
        }

        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_Quality_Hope_{timestamp}.json"

        # Crear respuesta
        response = app.make_response(
            json.dumps(backup_data, indent=2, default=str, ensure_ascii=False)
        )
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-Type"] = "application/json; charset=utf-8"

        print(f"✅ Respaldo creado: {len(batches)} batches, {len(segmentadores)} segmentadores")

        return response

    except Exception as e:
        print(f"❌ Error creando respaldo: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================================
# ENDPOINT DE CARGA RÁPIDA CON COPY-PASTE
# ============================================================================

@app.route("/api/batches/quick-create", methods=["POST"])
def quick_create_batches():
    """Crear múltiples batches desde texto plano (copy-paste de lista)"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        data = request.json
        batch_list_text = data.get("batch_list", "").strip()

        if not batch_list_text:
            return jsonify({"success": False, "error": "Lista de batches vacía"}), 400

        print(f"📝 Procesando lista de batches desde texto...")

        # Parsear la lista: separar por líneas y limpiar
        lines = batch_list_text.split('\n')
        batch_ids = []

        for line in lines:
            line = line.strip()
            if line:  # Ignorar líneas vacías
                # Si la línea contiene comas o espacios, dividir
                parts = line.replace(',', ' ').split()
                batch_ids.extend(parts)

        # Limpiar y filtrar batch IDs válidos
        batch_ids = [bid.strip() for bid in batch_ids if bid.strip()]

        if not batch_ids:
            return jsonify({"success": False, "error": "No se encontraron IDs de batches válidos"}), 400

        print(f"📋 {len(batch_ids)} batch IDs detectados: {batch_ids[:5]}{'...' if len(batch_ids) > 5 else ''}")

        # Verificar cuáles ya existen
        existing_ids = set()
        for bid in batch_ids:
            if batches_col.find_one({"id": bid}):
                existing_ids.add(bid)

        # Crear los que no existen
        created = []
        skipped = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for bid in batch_ids:
            if bid in existing_ids:
                skipped.append(bid)
                print(f"⏭️ Batch {bid} ya existe, omitido")
                continue

            # Crear batch nuevo
            new_batch = {
                "id": bid,
                "assignee": None,
                "status": "NS",  # No Segmentado
                "folder": "",
                "mongo_uploaded": False,
                "comments": "",
                "metadata": {
                    "created_at": current_time,
                    "priority": "media",
                    "total_masks": 0,
                    "completed_masks": 0
                }
            }

            batches_col.insert_one(new_batch)
            created.append(bid)
            print(f"✅ Batch {bid} creado")

        result_message = f"Creados: {len(created)}, Ya existían: {len(skipped)}"
        print(f"✅ {result_message}")

        return jsonify({
            "success": True,
            "message": result_message,
            "created": created,
            "skipped": skipped,
            "total_processed": len(batch_ids)
        })

    except Exception as e:
        print(f"❌ Error en carga rápida: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/export/batches", methods=["POST"])
def export_batches_report():
    """Exportar reporte de batches en Excel o CSV con filtros aplicados"""
    global batches_col

    if batches_col is None:
        return jsonify({"success": False, "error": "No DB connection"}), 503

    try:
        data = request.json or {}
        export_format = data.get("format", "excel")  # "excel" o "csv"
        batch_ids = data.get("batch_ids", [])  # IDs de batches filtrados

        print(f"[STATS] Exportando {len(batch_ids)} batches en formato {export_format}")

        # Si no se proporcionan IDs, exportar TODOS los batches
        if not batch_ids:
            # Traer TODOS los batches (no solo asignados)
            batches = list(batches_col.find({}, {"_id": 0}))
        else:
            # Si se proporcionan IDs específicos, traer solo esos
            batches = list(batches_col.find({
                "id": {"$in": batch_ids}
            }, {"_id": 0}))

        # ===========================================================
        # CALCULAR MÉTRICAS GENERALES
        # ===========================================================
        all_batches = list(batches_col.find({}, {"_id": 0, "status": 1, "assignee": 1, "metadata": 1, "specification": 1, "especificacion": 1}))

        total_batches = len(all_batches)
        completed_batches = sum(1 for b in all_batches if b.get("status") == "S")
        in_progress_batches = sum(1 for b in all_batches if b.get("status") == "FS")
        pending_batches = sum(1 for b in all_batches if b.get("status") == "NS")

        # Batches con revisión
        aprobados = sum(1 for b in all_batches if b.get("metadata", {}).get("review_status") == "aprobado")
        no_aprobados = sum(1 for b in all_batches if b.get("metadata", {}).get("review_status") == "no_aprobado")
        sin_revisar = sum(1 for b in all_batches if not b.get("metadata", {}).get("review_status"))

        unassigned_batches = sum(1 for b in all_batches if not b.get("assignee") or b.get("assignee") == "Sin asignar")

        completion_rate = round((completed_batches / total_batches * 100), 1) if total_batches > 0 else 0
        review_rate = round((aprobados / total_batches * 100), 1) if total_batches > 0 else 0

        # ===========================================================
        # CALCULAR MÉTRICAS POR EQUIPO
        # ===========================================================
        team_stats = {}
        for batch in all_batches:
            assignee = batch.get("assignee", "Sin asignar")
            if not assignee or assignee == "":
                assignee = "Sin asignar"

            if assignee not in team_stats:
                team_stats[assignee] = {
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "pending": 0,
                    "aprobados": 0,
                    "no_aprobados": 0
                }

            team_stats[assignee]["total"] += 1
            status = batch.get("status", "NS")
            if status == "S":
                team_stats[assignee]["completed"] += 1
            elif status == "FS":
                team_stats[assignee]["in_progress"] += 1
            elif status == "NS":
                team_stats[assignee]["pending"] += 1

            review_status = batch.get("metadata", {}).get("review_status", "")
            if review_status == "aprobado":
                team_stats[assignee]["aprobados"] += 1
            elif review_status == "no_aprobado":
                team_stats[assignee]["no_aprobados"] += 1

        # ===========================================================
        # CALCULAR MÉTRICAS POR ESPECIFICACIÓN
        # ===========================================================
        spec_stats = {}
        for batch in all_batches:
            # Usar 'specification' que es el campo correcto en la BD
            especificacion = batch.get("specification", batch.get("especificacion", "Sin especificación"))
            if not especificacion or especificacion == "":
                especificacion = "Sin especificación"

            if especificacion not in spec_stats:
                spec_stats[especificacion] = {
                    "total": 0,
                    "asignados": 0,
                    "aprobados": 0,
                    "no_aprobados": 0,
                    "sin_revisar": 0,
                    "completados": 0
                }

            spec_stats[especificacion]["total"] += 1

            # Contar solo batches que tienen un assignee válido
            assignee = batch.get("assignee", "")
            if assignee and assignee != "Sin asignar":
                spec_stats[especificacion]["asignados"] += 1

            status = batch.get("status", "NS")
            if status == "S":
                spec_stats[especificacion]["completados"] += 1

            review_status = batch.get("metadata", {}).get("review_status", "")
            if review_status == "aprobado":
                spec_stats[especificacion]["aprobados"] += 1
            elif review_status == "no_aprobado":
                spec_stats[especificacion]["no_aprobados"] += 1
            else:
                spec_stats[especificacion]["sin_revisar"] += 1

        # ===========================================================
        # PREPARAR DATOS DETALLADOS DE BATCHES
        # ===========================================================
        batch_rows = []
        for batch in batches:
            # Incluir TODOS los batches, no solo los asignados
            assignee = batch.get("assignee", "Sin asignar")
            if not assignee or assignee == "":
                assignee = "Sin asignar"

            # Obtener el estatus de revisión
            review_status = batch.get("metadata", {}).get("review_status", "")
            # Formatear el estatus de revisión para mejor legibilidad
            review_display = ""
            if review_status == "aprobado":
                review_display = "[OK] Aprobado"
            elif review_status == "no_aprobado":
                review_display = "[ERROR] No Aprobado"
            else:
                review_display = "⏳ Pendiente"

            # Obtener metadatos adicionales
            metadata = batch.get("metadata", {})

            # Usar 'specification' que es el campo correcto
            specification = batch.get("specification", batch.get("especificacion", ""))

            row = {
                "Batch ID": batch.get("id", ""),
                "Responsable": assignee,
                "Estatus Segmentación": batch.get("status", "NS"),
                "Estatus Revisión": review_display,
                "Especificación": specification,
                "Mongo Subido": "Sí" if batch.get("mongo_uploaded", False) else "No",
                "Prioridad": metadata.get("priority", "").capitalize() if metadata.get("priority") else "",
                "Fecha Asignación": metadata.get("assigned_at", ""),
                "Fecha Límite": metadata.get("due_date", ""),
                "Fecha Revisión": metadata.get("reviewed_at", ""),
                "Path": metadata.get("path", ""),
                "Comentarios": batch.get("comments", ""),
                "Carpeta": batch.get("folder", ""),
            }
            batch_rows.append(row)

        # Para retrocompatibilidad con CSV
        rows = batch_rows

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if export_format == "excel":
            # Exportar a Excel con múltiples hojas
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            wb = openpyxl.Workbook()

            # ===============================================================
            # HOJA 1: RESUMEN GENERAL
            # ===============================================================
            ws_resumen = wb.active
            ws_resumen.title = "Resumen General"

            # Estilos
            title_fill = PatternFill(start_color="6B46C1", end_color="6B46C1", fill_type="solid")
            title_font = Font(color="FFFFFF", bold=True, size=14)
            header_fill = PatternFill(start_color="9333EA", end_color="9333EA", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            value_font = Font(size=12)

            # Título principal
            ws_resumen.merge_cells("A1:B1")
            title_cell = ws_resumen["A1"]
            title_cell.value = f"Reporte General - {PROJECT_NAME}"
            title_cell.fill = title_fill
            title_cell.font = title_font
            title_cell.alignment = Alignment(horizontal="center", vertical="center")

            # Fecha de generación
            ws_resumen["A2"] = "Fecha de Generación:"
            ws_resumen["B2"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws_resumen["A2"].font = Font(bold=True)

            # Métricas globales
            current_row = 4
            ws_resumen[f"A{current_row}"] = "Métrica"
            ws_resumen[f"B{current_row}"] = "Valor"
            ws_resumen[f"A{current_row}"].fill = header_fill
            ws_resumen[f"B{current_row}"].fill = header_fill
            ws_resumen[f"A{current_row}"].font = header_font
            ws_resumen[f"B{current_row}"].font = header_font

            metrics_data = [
                ("Total de Batches", total_batches),
                ("Batches Completados (S)", completed_batches),
                ("Batches En Progreso (FS)", in_progress_batches),
                ("Batches Pendientes (NS)", pending_batches),
                ("Batches Sin Asignar", unassigned_batches),
                ("", ""),
                ("Tasa de Completitud (%)", f"{completion_rate}%"),
                ("", ""),
                ("Batches Aprobados", aprobados),
                ("Batches No Aprobados", no_aprobados),
                ("Tasa de Aprobación (%)", f"{review_rate}%"),
            ]

            current_row += 1
            for metric, value in metrics_data:
                ws_resumen[f"A{current_row}"] = metric
                ws_resumen[f"B{current_row}"] = value
                ws_resumen[f"A{current_row}"].font = value_font
                ws_resumen[f"B{current_row}"].font = value_font
                ws_resumen[f"B{current_row}"].alignment = Alignment(horizontal="right")
                current_row += 1

            # Ajustar anchos
            ws_resumen.column_dimensions["A"].width = 35
            ws_resumen.column_dimensions["B"].width = 20

            # ===============================================================
            # HOJA 2: MÉTRICAS POR SEGMENTADOR
            # ===============================================================
            ws_team = wb.create_sheet("Métricas por Segmentador")

            team_headers = ["Responsable", "Número de lotes asignados", "Completados",
                           "Aprobados", "No Aprobados", "Tasa de Completitud (%)"]

            for col_num, header in enumerate(team_headers, 1):
                cell = ws_team.cell(row=1, column=col_num)
                cell.value = header
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Datos del equipo
            row_num = 2
            for assignee, stats in sorted(team_stats.items()):
                completion_pct = round((stats["completed"] / stats["total"] * 100), 1) if stats["total"] > 0 else 0

                ws_team.cell(row=row_num, column=1, value=assignee)  # Responsable
                ws_team.cell(row=row_num, column=2, value=stats["total"])  # Número de lotes asignados
                ws_team.cell(row=row_num, column=3, value=stats["completed"])  # Completados
                ws_team.cell(row=row_num, column=4, value=stats["aprobados"])  # Aprobados
                ws_team.cell(row=row_num, column=5, value=stats["no_aprobados"])  # No Aprobados
                ws_team.cell(row=row_num, column=6, value=f"{completion_pct}%")  # Tasa de Completitud

                # Alinear números a la derecha
                for col_num in range(2, 7):
                    ws_team.cell(row=row_num, column=col_num).alignment = Alignment(horizontal="right")

                row_num += 1

            # Ajustar anchos de columnas
            ws_team.column_dimensions["A"].width = 18  # Responsable
            ws_team.column_dimensions["B"].width = 25  # Número de lotes asignados
            ws_team.column_dimensions["C"].width = 15  # Completados
            ws_team.column_dimensions["D"].width = 15  # Aprobados
            ws_team.column_dimensions["E"].width = 15  # No Aprobados
            ws_team.column_dimensions["F"].width = 22  # Tasa de Completitud

            # Agregar autofiltros
            ws_team.auto_filter.ref = f"A1:{get_column_letter(len(team_headers))}{row_num - 1}"

            # ===============================================================
            # HOJA 3: MÉTRICAS POR ESPECIFICACIÓN
            # ===============================================================
            ws_spec = wb.create_sheet("Métricas por Especificación")

            spec_headers = ["Especificación", "Data Total (folders)", "Asignados", "Completados",
                           "Aprobados", "No Aprobados", "Tasa de Aprobación (%)"]

            for col_num, header in enumerate(spec_headers, 1):
                cell = ws_spec.cell(row=1, column=col_num)
                cell.value = header
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Datos por especificación
            row_num = 2
            for especificacion, stats in sorted(spec_stats.items()):
                # Calcular tasa de aprobación sobre el total de batches completados revisados
                total_revisados = stats["aprobados"] + stats["no_aprobados"]
                aprobacion_pct = round((stats["aprobados"] / total_revisados * 100), 1) if total_revisados > 0 else 0

                ws_spec.cell(row=row_num, column=1, value=especificacion)  # Especificación
                ws_spec.cell(row=row_num, column=2, value=stats["total"])  # Data Total (folders)
                ws_spec.cell(row=row_num, column=3, value=stats["asignados"])  # Asignados
                ws_spec.cell(row=row_num, column=4, value=stats["completados"])  # Completados
                ws_spec.cell(row=row_num, column=5, value=stats["aprobados"])  # Aprobados
                ws_spec.cell(row=row_num, column=6, value=stats["no_aprobados"])  # No Aprobados
                ws_spec.cell(row=row_num, column=7, value=f"{aprobacion_pct}%")  # Tasa de Aprobación

                # Alinear números a la derecha (excepto especificación que va en columna 1)
                for col_num in range(2, 8):
                    ws_spec.cell(row=row_num, column=col_num).alignment = Alignment(horizontal="right")

                row_num += 1

            # Ajustar anchos de columnas
            ws_spec.column_dimensions["A"].width = 50  # Especificación (más ancho)
            ws_spec.column_dimensions["B"].width = 20  # Data Total
            ws_spec.column_dimensions["C"].width = 15  # Asignados
            ws_spec.column_dimensions["D"].width = 15  # Completados
            ws_spec.column_dimensions["E"].width = 15  # Aprobados
            ws_spec.column_dimensions["F"].width = 15  # No Aprobados
            ws_spec.column_dimensions["G"].width = 22  # Tasa de Aprobación

            # Agregar autofiltros
            ws_spec.auto_filter.ref = f"A1:{get_column_letter(len(spec_headers))}{row_num - 1}"

            # ===============================================================
            # HOJA 4: DETALLE DE BATCHES
            # ===============================================================
            ws_batches = wb.create_sheet("Batches Detallados")

            # Encabezados con estilo
            batch_headers = list(batch_rows[0].keys()) if batch_rows else []

            for col_num, header in enumerate(batch_headers, 1):
                cell = ws_batches.cell(row=1, column=col_num)
                cell.value = header
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            # Datos de batches
            for row_num, row_data in enumerate(batch_rows, 2):
                for col_num, header in enumerate(batch_headers, 1):
                    cell = ws_batches.cell(row=row_num, column=col_num)
                    cell.value = row_data[header]
                    cell.alignment = Alignment(vertical="top", wrap_text=True)

            # Ajustar ancho de columnas
            column_widths = {
                "Batch ID": 15,
                "Responsable": 15,
                "Estatus Segmentación": 18,
                "Estatus Revisión": 18,
                "Especificación": 50,  # Más ancho para especificaciones largas
                "Mongo Subido": 12,
                "Prioridad": 12,
                "Fecha Asignación": 16,
                "Fecha Límite": 16,
                "Fecha Revisión": 16,
                "Path": 50,  # Más ancho para rutas
                "Comentarios": 30,
                "Carpeta": 40
            }

            for col_num, header in enumerate(batch_headers, 1):
                width = column_widths.get(header, 20)
                ws_batches.column_dimensions[get_column_letter(col_num)].width = width

            # Agregar autofiltros a la tabla
            if batch_rows:
                ws_batches.auto_filter.ref = f"A1:{get_column_letter(len(batch_headers))}{len(batch_rows) + 1}"

            # Guardar en memoria
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            filename = f"reporte_completo_{timestamp}.xlsx"
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        else:
            # Exportar a CSV
            import csv
            output = io.StringIO()

            if rows:
                writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

            # Convertir a bytes
            mem = io.BytesIO()
            mem.write(output.getvalue().encode('utf-8-sig'))
            mem.seek(0)
            output = mem

            filename = f"reporte_batches_{timestamp}.csv"
            mimetype = 'text/csv'

        if export_format == "excel":
            print(f"[OK] Reporte completo generado: {len(batch_rows)} batches detallados, métricas del equipo y resumen general en {filename}")
        else:
            print(f"[OK] Reporte CSV generado: {len(rows)} batches en {filename}")

        return send_file(
            output,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"[ERROR] Error exportando reporte: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/validate-admin-password", methods=["POST"])
def validate_admin_password():
    """Validar contraseña de administrador"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No se enviaron datos"}), 400
        password = data.get("password", "")
        if not password:
            return jsonify({"success": False, "error": "La contraseña es requerida"}), 400
        if password == ADMIN_PASSWORD:
            return jsonify({"success": True, "message": "Contraseña válida"})
        return jsonify({"success": False, "error": "Contraseña incorrecta"}), 401
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    import socket

    def find_free_port(start_port=5000, max_attempts=10):
        """Encontrar un puerto libre disponible"""
        for port in range(start_port, start_port + max_attempts):
            try:
                # Intentar crear un socket en el puerto
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()

                if result != 0:  # Puerto disponible
                    return port
            except:
                continue

        # Si no encuentra puerto libre, usar uno aleatorio
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    # Inicializar DB de forma segura al iniciar localmente
    try:
        init_db()
    except Exception as e:
        print("⚠️ Error inicializando DB en startup:", e)

    # Encontrar puerto disponible
    port = find_free_port()
    print(f"\n{'='*60}")
    print(f"🚀 Servidor iniciando en puerto {port}")
    print(f"{'='*60}\n")

    app.run(debug=True, host="0.0.0.0", port=port)


