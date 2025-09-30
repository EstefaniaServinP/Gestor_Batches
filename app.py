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
from datetime import datetime

app = Flask(__name__)

# No crear la conexión en import time
db = None
batches_col = None
masks_col = None

def init_db():
    global db, batches_col, masks_col
    db = get_db(raise_on_fail=False)
    if db:
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
        if db_local:
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

@app.route("/api/batches", methods=["GET"])
def get_batches():
    """Endpoint paginado: ?page=1&per_page=50"""
    global batches_col
    if batches_col is None:
        # intentar reconectar a demanda
        db_local = get_db(raise_on_fail=False)
        if db_local:
            batches_col = db_local["batches"]
        else:
            return jsonify({"error":"No DB connection"}), 503

    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = int(request.args.get("per_page", 50))
        per_page = min(max(5, per_page), 200)  # límites razonables

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
            "folder": data.get("folder", f"/data/{batch_id}"),
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
                    "folder": f"/data/{batch_id}",
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
        force_reload = request.json.get("force", False) if request.json else False
        
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
    """Obtener batches que FALTAN por segmentar (no están en MongoDB)"""
    try:
        # Lista completa de todos los batches que deberían existir
        all_possible_batches = [
            'batch_9', 'batch_10', 'batch_11', 'batch_12', 'batch_13', 'batch_14', 'batch_15',
            'batch_16', 'batch_17', 'batch_18', 'batch_19', 'batch_20', 'batch_21', 'batch_22',
            'batch_23', 'batch_24', 'batch_25', 'batch_26', 'batch_27', 'batch_28', 'batch_29',
            'batch_30', 'batch_31', 'batch_32', 'batch_33', 'batch_34', 'batch_35', 'batch_36',
            'batch_37', 'batch_38', 'batch_39', 'batch_40', 'batch_41', 'batch_42', 'batch_43',
            'batch_44', 'batch_45', 'batch_46', 'batch_47', 'batch_48', 'batch_49', 'batch_50',
            'batch_51', 'batch_52', 'batch_53', 'batch_54', 'batch_55', 'batch_56', 'batch_57',
            'batch_58', 'batch_59', 'batch_60', 'batch_61', 'batch_62', 'batch_63', 'batch_64', 'batch_65',
            'batch_66', 'batch_67', 'batch_68', 'batch_69', 'batch_70', 'batch_71', 'batch_72', 'batch_73',
            'batch_74', 'batch_75', 'batch_76', 'batch_77', 'batch_78', 'batch_79', 'batch_80', 'batch_81',
            'batch_82', 'batch_83', 'batch_84', 'batch_85', 'batch_86', 'batch_87', 'batch_88', 'batch_89',
            'batch_90', 'batch_91', 'batch_92', 'batch_93', 'batch_94', 'batch_95', 'batch_96', 'batch_97',
            'batch_98', 'batch_99', 'batch_100', 'batch_101', 'batch_102', 'batch_103', 'batch_104', 'batch_105',
            'batch_106', 'batch_107', 'batch_108', 'batch_109', 'batch_110', 'batch_111', 'batch_112', 'batch_113',
            'batch_114', 'batch_115', 'batch_116', 'batch_117', 'batch_118', 'batch_119', 'batch_120', 'batch_121',
            'batch_122', 'batch_123', 'batch_124', 'batch_125', 'batch_126', 'batch_127', 'batch_128', 'batch_129',
            'batch_130', 'batch_131', 'batch_132', 'batch_133', 'batch_134', 'batch_135', 'batch_136', 'batch_137',
            'batch_138', 'batch_139', 'batch_140', 'batch_141', 'batch_142', 'batch_143', 'batch_144', 'batch_145',
            'batch_146', 'batch_147', 'batch_148', 'batch_149', 'batch_150', 'batch_151', 'batch_152', 'batch_153',
            'batch_154', 'batch_155', 'batch_156', 'batch_157', 'batch_158', 'batch_159', 'batch_160', 'batch_161',
            'batch_162', 'batch_163', 'batch_164', 'batch_165', 'batch_166', 'batch_167', 'batch_168', 'batch_169',
            'batch_170', 'batch_171', 'batch_172', 'batch_173', 'batch_174', 'batch_175', 'batch_176', 'batch_177',
            'batch_178', 'batch_179', 'batch_180', 'batch_181', 'batch_182', 'batch_183', 'batch_184', 'batch_185',
            'batch_186', 'batch_187', 'batch_188', 'batch_189', 'batch_190', 'batch_191', 'batch_192', 'batch_193',
            'batch_194', 'batch_195', 'batch_196', 'batch_197', 'batch_198', 'batch_199', 'batch_200', 'batch_361',
            'batch_362', 'batch_363', 'batch_364', 'batch_365', 'batch_366', 'batch_367', 'batch_368', 'batch_369',
            'batch_370', 'batch_371', 'batch_372', 'batch_373', 'batch_374', 'batch_375', 'batch_376', 'batch_377',
            'batch_378', 'batch_379', 'batch_380', 'batch_381', 'batch_382', 'batch_383', 'batch_384', 'batch_385',
            'batch_386', 'batch_387', 'batch_388', 'batch_389', 'batch_390', 'batch_391', 'batch_393', 'batch_394',
            'batch_395', 'batch_396', 'batch_397', 'batch_398', 'batch_399', 'batch_400', 'batch_401', 'batch_402',
            'batch_403', 'batch_404', 'batch_405', 'batch_406', 'batch_407', 'batch_408', 'batch_409', 'batch_410',
            'batch_411', 'batch_412', 'batch_413', 'batch_414', 'batch_415', 'batch_416', 'batch_417', 'batch_418',
            'batch_419', 'batch_420', 'batch_421', 'batch_422', 'batch_423', 'batch_424', 'batch_425', 'batch_426',
            'batch_427', 'batch_428', 'batch_429', 'batch_430', 'batch_431', 'batch_432', 'batch_433', 'batch_434',
            'batch_435', 'batch_436', 'batch_437', 'batch_438', 'batch_439', 'batch_440', 'batch_441', 'batch_442',
            'batch_443', 'batch_444', 'batch_445', 'batch_446', 'batch_447', 'batch_448', 'batch_449', 'batch_450',
            'batch_451', 'batch_452', 'batch_453', 'batch_454', 'batch_455', 'batch_456', 'batch_457', 'batch_458',
            'batch_459', 'batch_460', 'batch_461', 'batch_462', 'batch_463', 'batch_464', 'batch_465', 'batch_466',
            'batch_467', 'batch_468', 'batch_469', 'batch_470', 'batch_471', 'batch_472', 'batch_473', 'batch_474',
            'batch_475', 'batch_476', 'batch_477', 'batch_478', 'batch_479', 'batch_480', 'batch_481', 'batch_482',
            'batch_483', 'batch_484', 'batch_485', 'batch_486', 'batch_487', 'batch_488', 'batch_2402', 'batch_2403',
            'batch_2409', 'batch_2410', 'batch_2411', 'batch_2412', 'batch_2413', 'batch_2414', 'batch_2416', 'batch_2417',
            'batch_2421', 'batch_2422', 'batch_2423', 'batch_2424', 'batch_2426', 'batch_2427', 'batch_2430', 'batch_2432',
            'batch_2433', 'batch_2434', 'batch_2435', 'batch_2436', 'batch_2437', 'batch_2438', 'batch_2439', 'batch_2440',
            'batch_2441', 'batch_2442', 'batch_2443', 'batch_2444', 'batch_2445', 'batch_2446', 'batch_2447', 'batch_2448',
            'batch_2449', 'batch_2450', 'batch_2451', 'batch_2452', 'batch_2453', 'batch_2454', 'batch_2455', 'batch_2456',
            'batch_2457', 'batch_2458', 'batch_2459', 'batch_2460', 'batch_2461', 'batch_2462', 'batch_2463', 'batch_2464',
            'batch_2465', 'batch_2466', 'batch_2467', 'batch_2468', 'batch_2469', 'batch_2470', 'batch_2471', 'batch_2472',
            'batch_2473', 'batch_2474', 'batch_2475', 'batch_2477', 'batch_2478', 'batch_2479', 'batch_2480', 'batch_2481',
            'batch_2482', 'batch_2484', 'batch_2485', 'batch_2486', 'batch_2487', 'batch_2488', 'batch_2490', 'batch_2491',
            'batch_2493', 'batch_2494', 'batch_2496', 'batch_2497', 'batch_2498', 'batch_2520', 'batch_2521', 'batch_2522',
            'batch_2523', 'batch_2524', 'batch_2525', 'batch_2526', 'batch_2527', 'batch_2528', 'batch_2529', 'batch_2530',
            'batch_2531', 'batch_2532', 'batch_2533', 'batch_2534', 'batch_2535', 'batch_2536', 'batch_2537', 'batch_2538',
            'batch_2539', 'batch_2540', 'batch_2541', 'batch_2542', 'batch_2543', 'batch_2544', 'batch_2545', 'batch_2546',
            'batch_2547', 'batch_2548', 'batch_2549', 'batch_2550', 'batch_2551', 'batch_2552', 'batch_2553', 'batch_2554',
            'batch_2555', 'batch_2556', 'batch_2557', 'batch_2558', 'batch_2559', 'batch_2560', 'batch_2561', 'batch_2562',
            'batch_2563', 'batch_2564'
        ]
        
        # Obtener batches que YA están en la base de datos
        existing_batch_ids = set()
        for batch in batches_col.find({}, {"id": 1, "_id": 0}):
            existing_batch_ids.add(batch["id"])
        
        # Filtrar para obtener solo los que FALTAN (no están en la DB)
        missing_batches = [batch_id for batch_id in all_possible_batches 
                          if batch_id not in existing_batch_ids]
        
        print(f"📊 Total batches posibles: {len(all_possible_batches)}")
        print(f"📊 Batches en DB: {len(existing_batch_ids)}")
        print(f"📊 Batches faltantes: {len(missing_batches)}")
        
        return jsonify({
            "success": True,
            "missing_batches": missing_batches,
            "total_missing": len(missing_batches),
            "total_existing": len(existing_batch_ids),
            "message": f"Se encontraron {len(missing_batches)} batches pendientes de segmentación"
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo batches faltantes: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Inicializar DB de forma segura al iniciar localmente
    try:
        init_db()
    except Exception as e:
        print("⚠️ Error inicializando DB en startup:", e)
    app.run(debug=True, host="0.0.0.0", port=5000)


