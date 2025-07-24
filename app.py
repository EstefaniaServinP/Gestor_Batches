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

from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import json
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)

# Cadena de conexión MongoDB
MONGO_URI = "mongodb://admin:hxsCiKTUt0GNpqtaeRJL@192.168.100.26:27017/?authSource=admin"
client = MongoClient(MONGO_URI)

# Base de datos y colecciones
db = client["QA"]
masks_col = db["QA.masks.files"]
batches_col = db["batches"]

# Lista de miembros del equipo
CREW_MEMBERS = ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"]

@app.route("/")
def index():
    return render_template("team.html", crew=CREW_MEMBERS)

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", crew=CREW_MEMBERS)

@app.route("/dashboard/<assignee>")
def dashboard_filtered(assignee):
    return render_template("dashboard.html", crew=CREW_MEMBERS, filter_assignee=assignee)

@app.route("/masks")
def masks():
    # Trae todos los documentos de máscaras
    docs = list(masks_col.find({}, {"_id": 0, "filename": 1, "uploadDate": 1}))
    return render_template("masks.html", files=docs)

@app.route("/api/batches", methods=["GET"])
def get_batches():
    # Obtiene todos los batches de MongoDB
    batches = list(batches_col.find({}, {"_id": 0}))
    
    # Enriquecer con información de archivos
    for batch in batches:
        batch_number = batch["id"].replace("batch_", "")
        pattern = f"masks_batch_{batch_number}"
        
        # Contar archivos para este batch
        files = list(masks_col.find(
            {"filename": {"$regex": pattern}},
            {"filename": 1, "uploadDate": 1, "metadata": 1, "length": 1}
        ).sort("uploadDate", -1))
        
        # Agregar información de archivos al batch
        batch["file_info"] = {
            "count": len(files),
            "latest_upload": files[0]["uploadDate"] if files else None,
            "uploaded_by": files[0].get("metadata", {}).get("uploaded_by", "unknown") if files else None,
            "file_size": files[0].get("length", 0) if files else 0,
            "has_files": len(files) > 0
        }
    
    return jsonify(batches)

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
        update_data["assignee"] = data["assignee"]
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
    
    if result.modified_count > 0:
        return jsonify({"success": True})
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

@app.route("/api/check-mongo-files", methods=["GET"])
def check_mongo_files():
    """Verificar qué archivos están actualmente en MongoDB"""
    try:
        # Obtener lista de todos los archivos en la colección masks
        files = list(masks_col.find(
            {},
            {"filename": 1, "uploadDate": 1, "metadata": 1, "length": 1}
        ).sort("uploadDate", -1).limit(50))  # Últimos 50 archivos
        
        files_info = []
        for file in files:
            files_info.append({
                "filename": file["filename"],
                "uploadDate": file["uploadDate"].isoformat() if file.get("uploadDate") else None,
                "size_mb": round(file.get("length", 0) / (1024*1024), 2),
                "uploaded_by": file.get("metadata", {}).get("uploaded_by", "unknown")
            })
        
        # Contar archivos por patrón de batch
        batch_patterns = {}
        for file in files:
            filename = file["filename"]
            # Buscar patrones como batch_XX, Batch_XX, masks_batch_XX
            import re
            batch_match = re.search(r'[Bb]atch[_\-]?(\d+)', filename)
            if batch_match:
                batch_num = batch_match.group(1)
                batch_key = f"batch_{batch_num}"
                if batch_key not in batch_patterns:
                    batch_patterns[batch_key] = []
                batch_patterns[batch_key].append(filename)
        
        return jsonify({
            "success": True,
            "total_files": len(files_info),
            "recent_files": files_info,
            "batch_patterns": batch_patterns,
            "message": f"Se encontraron {len(files_info)} archivos en MongoDB"
        })
        
    except Exception as e:
        print(f"❌ Error verificando archivos en MongoDB: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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
        
        with open("batches,json", "r", encoding="utf-8") as f:
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
        with open("batches,json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("batches"):
                batches_col.insert_many(data["batches"])
        return jsonify({"success": True, "message": f"Base de datos limpiada y {len(data['batches'])} batches cargados"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
