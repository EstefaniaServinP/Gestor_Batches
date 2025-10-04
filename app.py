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

from flask import Flask, render_template, request, jsonify, redirect
from db import get_db, create_indexes
import json
import os
from datetime import datetime

app = Flask(__name__)

# Configuración del directorio de datos
DATA_DIRECTORY = os.environ.get("DATA_DIRECTORY", "/home/faservin/american_project")

# No crear la conexión en import time
db = None

batches_col = None
masks_col = None

def init_db():
    global db, batches_col, masks_col
    db = get_db(raise_on_fail=False)
    if db is not None:
        batches_col = db["batches"]
        masks_col = db["masks"]
        # crear índices en background (no bloqueante)
        create_indexes()
    else:
        print("⚠️ DB no disponible en init_db — seguirá intentando al recibir peticiones")

# ejemplo: contar documentos
# print("Batches en DB:", batches_col.count_documents({}))

# Lista de miembros del equipo
CREW_MEMBERS = ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"]

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

@app.route("/masks")
def masks():
    global masks_col
    if masks_col is None:
        # Intentar reconectar a demanda
        db_local = get_db(raise_on_fail=False)
        if db_local is not None:
            masks_col = db_local["masks"]
        else:
            return jsonify({"error": "No DB connection"}), 503

    # Trae todos los documentos de máscaras
    docs = list(masks_col.find({}, {"_id": 0, "filename": 1, "uploadDate": 1}))
    return render_template("masks.html", files=docs)

@app.route("/metrics")
def metrics():
    """Página principal de métricas del sistema"""
    return render_template("metrics.html", crew=CREW_MEMBERS)

@app.route("/metrics/overview")
def metrics_overview():
    """Página de vista general de métricas"""
    return render_template("metrics_overview.html", crew=CREW_MEMBERS)

@app.route("/metrics/team")
def metrics_team():
    """Página de métricas del equipo"""
    return render_template("metrics_team.html", crew=CREW_MEMBERS)

@app.route("/metrics/progress")
def metrics_progress():
    """Página de reportes de progreso"""
    return render_template("metrics_progress.html", crew=CREW_MEMBERS)

@app.route("/metrics/people")
def metrics_people():
    """Página de avances por persona (redirige a team)"""
    return render_template("metrics_team.html", crew=CREW_MEMBERS)

@app.route("/metrics/global")
def metrics_global():
    """Página de estadísticas globales (redirige a overview)"""
    return render_template("metrics_overview.html", crew=CREW_MEMBERS)

@app.route("/metrics/mongo")
def metrics_mongo():
    """Página de verificación MongoDB"""
    return render_template("metrics_mongo.html", crew=CREW_MEMBERS)

@app.route("/metrics/report")
def metrics_report():
    """Página de reporte de progreso (redirige a progress)"""
    return render_template("metrics_progress.html", crew=CREW_MEMBERS)

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
        
        result = batches_col.insert_one(batch)
        
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
    """Agregar un nuevo segmentador al equipo"""
    global CREW_MEMBERS
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No se enviaron datos"
            }), 400
        
        name = data.get("name", "").strip()
        role = data.get("role", "Segmentador General")
        email = data.get("email", "")
        
        # Validar que se proporcione un nombre
        if not name:
            return jsonify({
                "success": False,
                "error": "El nombre del segmentador es requerido"
            }), 400
        
        # Verificar que no exista ya
        if name in CREW_MEMBERS:
            return jsonify({
                "success": False,
                "error": f"El segmentador '{name}' ya existe en el equipo"
            }), 400
        
        # Agregar al equipo
        CREW_MEMBERS.append(name)
        
        print(f"👤 Nuevo segmentador agregado: {name} ({role})")
        
        # Log para debugging
        print(f"📋 Equipo actualizado: {CREW_MEMBERS}")
        
        return jsonify({
            "success": True,
            "message": f"Segmentador '{name}' agregado exitosamente",
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
    """Obtener la lista actual de segmentadores"""
    try:
        return jsonify({
            "success": True,
            "segmentadores": CREW_MEMBERS,
            "total": len(CREW_MEMBERS)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/check-mongo-files", methods=["GET"])
def check_mongo_files():
    """Verificar qué archivos están actualmente en MongoDB"""
    try:
        print("🔍 Iniciando verificación de archivos en MongoDB...")
        
        # Verificar conexión primero
        try:
            # Test de conexión
            masks_col.find_one({}, {"_id": 1})
            print("✅ Conexión a MongoDB establecida")
        except Exception as conn_error:
            print(f"❌ Error de conexión a MongoDB: {conn_error}")
            return jsonify({
                "success": False, 
                "error": f"Error de conexión a MongoDB: {str(conn_error)}"
            }), 500
        
        # Obtener lista de todos los archivos en la colección masks
        try:
            files = list(masks_col.find(
                {},
                {"filename": 1, "uploadDate": 1, "metadata": 1, "length": 1}
            ).sort("uploadDate", -1).limit(100))  # Aumentar a 100 archivos
            print(f"📊 Se encontraron {len(files)} archivos en total")
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
            "message": f"Se encontraron {len(files_info)} archivos en MongoDB"
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
    try:
        # Buscar archivos que coincidan con el patrón batch_XX
        pattern = f"masks_batch_{batch_id.replace('batch_', '')}"
        files = list(masks_col.find(
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
    """Sincronizar todos los batches con archivos subidos y actualizar mongo_uploaded"""
    try:
        print("🔄 Iniciando sincronización de archivos con batches...")
        batches = list(batches_col.find({}, {"id": 1, "mongo_uploaded": 1}))
        updated_batches = 0
        sync_results = []
        
        for batch in batches:
            batch_id = batch["id"]
            current_mongo_status = batch.get("mongo_uploaded", False)
            batch_number = batch_id.replace("batch_", "").replace("Batch_", "")
            
            # Buscar archivos para este batch con múltiples patrones más específicos
            # Basado en los nombres reales encontrados en MongoDB
            patterns = [
                f"masks_batch_{batch_number}",          # masks_batch_400
                f"masks_Batch_{batch_number}",          # masks_Batch_400  
                f"batch_{batch_number}",                # batch_400
                f"Batch_{batch_number}",                # Batch_400
                f"batch_{batch_number} \\(",            # batch_400 (100) - patrón con paréntesis
                f"Batch_{batch_number} \\(",            # Batch_400 (100)
                f"^batch_{batch_number}$",              # batch_400 exacto
                f"^{batch_number}$",                    # solo el número 400
                batch_id,                               # batch_400 exacto
            ]
            
            files_found = []
            for pattern in patterns:
                # Buscar con diferentes extensiones comunes
                search_patterns = [
                    pattern,
                    f"{pattern}.tar.xz",
                    f"{pattern}.tar.gz", 
                    f"{pattern}.zip",
                    f"{pattern}.tar"
                ]
                
                for search_pattern in search_patterns:
                    files = list(masks_col.find(
                        {"filename": {"$regex": search_pattern, "$options": "i"}},  # Case insensitive
                        {"filename": 1, "uploadDate": 1, "metadata": 1, "length": 1}
                    ).sort("uploadDate", -1))
                    files_found.extend(files)
                    
                    # Log para debug de batches específicos
                    if files and (batch_id == "batch_400" or batch_number in ["4250", "4251", "4252"]):
                        print(f"🔍 ENCONTRADO para {batch_id} con patrón '{search_pattern}': {[f['filename'] for f in files]}")
            
            # Remover duplicados
            seen_filenames = set()
            unique_files = []
            for file in files_found:
                if file["filename"] not in seen_filenames:
                    unique_files.append(file)
                    seen_filenames.add(file["filename"])
            
            has_files = len(unique_files) > 0
            
            # Log específico para batches de debug
            if batch_id == "batch_400" or batch_number in ["4250", "4251", "4252"]:
                print(f"📊 DEBUG {batch_id}:")
                print(f"   - Número extraído: {batch_number}")
                print(f"   - Archivos encontrados: {len(unique_files)}")
                print(f"   - Nombres: {[f['filename'] for f in unique_files]}")
                print(f"   - Estado actual mongo_uploaded: {current_mongo_status}")
                print(f"   - Nuevo estado: {has_files}")
            
            # Actualizar información del batch
            update_data = {
                "mongo_uploaded": has_files,  # Actualizar el estado principal
                "file_info": {
                    "file_count": len(unique_files),
                    "last_file_upload": unique_files[0]["uploadDate"] if unique_files else None,
                    "has_files": has_files,
                    "files": [f["filename"] for f in unique_files[:5]]  # Primeros 5 archivos
                }
            }
            
            # Solo actualizar si hay cambios
            if current_mongo_status != has_files or not batch.get("file_info"):
                batches_col.update_one(
                    {"id": batch_id},
                    {"$set": update_data}
                )
                updated_batches += 1
                print(f"✅ Batch {batch_id}: mongo_uploaded actualizado de {current_mongo_status} a {has_files}")
            
            sync_results.append({
                "batch_id": batch_id,
                "files_found": len(unique_files),
                "mongo_uploaded": has_files,
                "latest_upload": unique_files[0]["uploadDate"] if unique_files else None,
                "updated": current_mongo_status != has_files
            })
        
        print(f"🔄 Sincronización completa: {updated_batches} batches actualizados")
        
        return jsonify({
            "success": True,
            "batches_updated": updated_batches,
            "total_batches": len(sync_results),
            "message": f"Sincronización completa: {updated_batches} batches actualizados",
            "results": sync_results
        })
        
    except Exception as e:
        print(f"❌ Error en sincronización: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/auto-create-batches", methods=["POST"])
def auto_create_batches():
    """Crear batches automáticamente basándose en archivos encontrados en MongoDB"""
    try:
        print("🤖 Iniciando creación automática de batches...")
        
        # Obtener todos los archivos de MongoDB
        files = list(masks_col.find(
            {},
            {"filename": 1, "uploadDate": 1, "metadata": 1, "length": 1}
        ).sort("uploadDate", -1))
        
        # Extraer números de batch de los nombres de archivos
        import re
        batch_numbers = set()
        for file in files:
            filename = file["filename"]
            # Buscar patrones como batch_XXXX, Batch_XXXX
            batch_matches = re.findall(r'[Bb]atch[_\-]?(\d+)', filename)
            for match in batch_matches:
                batch_numbers.add(match)
        
        print(f"📊 Números de batch encontrados en archivos: {sorted(list(batch_numbers))}")
        
        # Verificar qué batches ya existen
        existing_batches = list(batches_col.find({}, {"id": 1}))
        existing_ids = {b["id"] for b in existing_batches}
        
        created_batches = 0
        results = []
        
        for batch_num in sorted(batch_numbers):
            batch_id = f"batch_{batch_num}"
            
            if batch_id not in existing_ids:
                # Crear el batch
                batch = {
                    "id": batch_id,
                    "assignee": "Maggie",  # Asignar por defecto, se puede cambiar después
                    "folder": f"{DATA_DIRECTORY}/{batch_id}",
                    "tasks": ["segmentar", "subir_mascaras", "revisar"],
                    "metadata": {
                        "assigned_at": datetime.now().strftime("%Y-%m-%d"),
                        "due_date": "",
                        "priority": "media",
                        "reviewed_at": None
                    },
                    "status": "NS",  # No segmentado por defecto
                    "mongo_uploaded": True,  # Ya que el archivo existe
                    "comments": f"Batch creado automáticamente - archivo detectado en MongoDB"
                }
                
                batches_col.insert_one(batch)
                created_batches += 1
                results.append({
                    "batch_id": batch_id,
                    "created": True,
                    "assignee": "Maggie"
                })
                print(f"✅ Batch {batch_id} creado automáticamente")
            else:
                results.append({
                    "batch_id": batch_id,
                    "created": False,
                    "reason": "Ya existe"
                })
                print(f"⚠️ Batch {batch_id} ya existe")
        
        return jsonify({
            "success": True,
            "created_batches": created_batches,
            "total_found": len(batch_numbers),
            "message": f"Se crearon {created_batches} nuevos batches automáticamente",
            "results": results
        })
        
    except Exception as e:
        print(f"❌ Error en auto_create_batches: {e}")
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
    """Obtener batches que FALTAN por segmentar (leyendo carpetas del filesystem)"""
    try:
        # Leer carpetas reales del directorio de datos
        if os.path.exists(DATA_DIRECTORY):
            all_possible_batches = []
            for item in os.listdir(DATA_DIRECTORY):
                item_path = os.path.join(DATA_DIRECTORY, item)
                # Excluir archivos y directorios que no son batches
                exclude_items = ['subfolder_names.txt', 'assets_task_01jxjr14ykeghb7nvakp9ey2d9_1749754687_img_1.webp',
                                'imagenes ilustrativas', 'logo.png', 'logo.zip', 'Presentación_Cap_OPERADOR', 'PRESENT_LECTURA']
                if os.path.isdir(item_path) and item not in exclude_items and not item.startswith('.'):
                    all_possible_batches.append(item)

            print(f"📁 Leídas {len(all_possible_batches)} carpetas desde {DATA_DIRECTORY}")
            print(f"📂 Carpetas encontradas: {all_possible_batches[:10]}..." if len(all_possible_batches) > 10 else f"📂 Carpetas encontradas: {all_possible_batches}")
        else:
            print(f"⚠️ Directorio {DATA_DIRECTORY} no existe")
            return jsonify({"error": f"Directorio de datos {DATA_DIRECTORY} no existe"}), 500

        # Obtener batches que YA están en la base de datos
        existing_batch_ids = set()
        for batch in batches_col.find({}, {"id": 1, "_id": 0}):
            existing_batch_ids.add(batch["id"])

        # Filtrar para obtener solo los que FALTAN (no están en la DB)
        missing_batches = [batch_id for batch_id in all_possible_batches
                          if batch_id not in existing_batch_ids]

        print(f"📊 Total batches en filesystem: {len(all_possible_batches)}")
        print(f"📊 Batches en DB: {len(existing_batch_ids)}")
        print(f"📊 Batches faltantes: {len(missing_batches)}")

        return jsonify({
            "success": True,
            "missing_batches": missing_batches,
            "total_missing": len(missing_batches),
            "total_existing": len(existing_batch_ids),
            "data_directory": DATA_DIRECTORY,
            "message": f"Se encontraron {len(missing_batches)} batches pendientes de segmentación"
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

        results = list(batches_col.aggregate(pipeline))

        # Inicializar contadores
        stats = {
            "total_batches": 0,
            "completed_batches": 0,  # S
            "in_progress_batches": 0,  # FS
            "pending_batches": 0,     # NS
            "unassigned_batches": 0   # assignee null/empty
        }

        # Procesar resultados de agregación
        for result in results:
            status = result["_id"]
            count = result["count"]
            stats["total_batches"] += count

            if status == "S":
                stats["completed_batches"] = count
            elif status == "FS":
                stats["in_progress_batches"] = count
            elif status == "NS":
                stats["pending_batches"] = count

        # Contar batches sin asignar
        unassigned_count = batches_col.count_documents({
            "$or": [
                {"assignee": {"$exists": False}},
                {"assignee": None},
                {"assignee": ""},
                {"assignee": {"$regex": "^\\s*$"}}
            ]
        })
        stats["unassigned_batches"] = unassigned_count

        # Calcular porcentaje de completado
        completion_rate = (stats["completed_batches"] / stats["total_batches"] * 100) if stats["total_batches"] > 0 else 0

        return jsonify({
            "success": True,
            "data": stats,
            "completion_rate": round(completion_rate, 1),
            "message": f"Estadísticas calculadas para {stats['total_batches']} batches"
        })

    except Exception as e:
        print(f"❌ Error en metrics overview: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/metrics/team", methods=["GET"])
def get_metrics_team():
    """Obtener métricas por miembro del equipo"""
    try:
        global batches_col
        if batches_col is None:
            db_local = get_db(raise_on_fail=False)
            if db_local is not None:
                batches_col = db_local["batches"]
            else:
                return jsonify({"error": "No DB connection"}), 503

        # Obtener lista de miembros del equipo
        team_members = []
        try:
            # Intentar usar colección team de MongoDB
            team_col = db_local["team"]
            team_members = [member["name"] for member in team_col.find({}, {"name": 1, "_id": 0})]
        except:
            # Fallback a lista hardcodeada
            team_members = CREW_MEMBERS

        # Agregación para métricas por assignee
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "$cond": {
                            "if": {"$or": [
                                {"$eq": ["$assignee", None]},
                                {"$eq": ["$assignee", ""]},
                                {"$regexMatch": {"input": "$assignee", "regex": "^\\s*$"}}
                            ]},
                            "then": "Sin asignar",
                            "else": "$assignee"
                        }
                    },
                    "total": {"$sum": 1},
                    "completed": {"$sum": {"$cond": [{"$eq": ["$status", "S"]}, 1, 0]}},
                    "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "FS"]}, 1, 0]}},
                    "pending": {"$sum": {"$cond": [{"$eq": ["$status", "NS"]}, 1, 0]}},
                    "batches": {"$push": {
                        "id": "$id",
                        "status": "$status",
                        "assigned_at": "$metadata.assigned_at"
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

            # Ordenar batches por fecha de asignación (si existe) o por ID
            batches = result["batches"]
            batches.sort(key=lambda x: (x.get("assigned_at") or "9999-99-99", x["id"]), reverse=True)

            # Tomar los 3 más recientes
            recent_batches = [batch["id"] for batch in batches[:3]]

            team_metrics.append({
                "assignee": assignee,
                "total": result["total"],
                "completed": result["completed"],
                "in_progress": result["in_progress"],
                "pending": result["pending"],
                "completion_rate": round((result["completed"] / result["total"] * 100), 1) if result["total"] > 0 else 0,
                "recent_batches": recent_batches
            })

        # Asegurar que todos los miembros del equipo aparezcan (incluso con 0 batches)
        existing_assignees = {metric["assignee"] for metric in team_metrics}
        for member in team_members:
            if member not in existing_assignees:
                team_metrics.append({
                    "assignee": member,
                    "total": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "pending": 0,
                    "completion_rate": 0,
                    "recent_batches": []
                })

        # Ordenar por nombre de assignee
        team_metrics.sort(key=lambda x: x["assignee"])

        return jsonify({
            "success": True,
            "data": team_metrics,
            "total_members": len(team_members),
            "message": f"Métricas calculadas para {len(team_metrics)} miembros"
        })

    except Exception as e:
        print(f"❌ Error en metrics team: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/metrics/progress", methods=["GET"])
def get_metrics_progress():
    """Obtener serie temporal de progreso por fechas de asignación"""
    try:
        global batches_col
        if batches_col is None:
            db_local = get_db(raise_on_fail=False)
            if db_local is not None:
                batches_col = db_local["batches"]
            else:
                return jsonify({"error": "No DB connection"}), 503

        # Agregación por fecha de asignación
        pipeline = [
            {
                "$match": {
                    "metadata.assigned_at": {"$exists": True, "$ne": None, "$ne": ""}
                }
            },
            {
                "$group": {
                    "_id": "$metadata.assigned_at",
                    "total": {"$sum": 1},
                    "completed": {"$sum": {"$cond": [{"$eq": ["$status", "S"]}, 1, 0]}},
                    "in_progress": {"$sum": {"$cond": [{"$eq": ["$status", "FS"]}, 1, 0]}},
                    "pending": {"$sum": {"$cond": [{"$eq": ["$status", "NS"]}, 1, 0]}}
                }
            },
            {
                "$sort": {"_id": 1}
            }
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
            "message": f"Serie temporal calculada para {len(progress_data)} fechas"
        })

    except Exception as e:
        print(f"❌ Error en metrics progress: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Inicializar DB de forma segura al iniciar localmente
    try:
        init_db()
    except Exception as e:
        print("⚠️ Error inicializando DB en startup:", e)
    app.run(debug=True, host="0.0.0.0", port=5000)


