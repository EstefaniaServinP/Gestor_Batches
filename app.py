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
    result = batches_col.delete_one({"id": batch_id})
    
    if result.deleted_count > 0:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Batch no encontrado"}), 404

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
    """Sincronizar todos los batches con archivos subidos"""
    try:
        batches = list(batches_col.find({}, {"id": 1}))
        sync_results = []
        
        for batch in batches:
            batch_id = batch["id"]
            batch_number = batch_id.replace("batch_", "")
            
            # Buscar archivos para este batch
            pattern = f"masks_batch_{batch_number}"
            files = list(masks_col.find(
                {"filename": {"$regex": pattern}},
                {"filename": 1, "uploadDate": 1, "metadata": 1}
            ).sort("uploadDate", -1))
            
            # Actualizar información del batch
            update_data = {
                "file_count": len(files),
                "last_file_upload": files[0]["uploadDate"] if files else None,
                "has_files": len(files) > 0
            }
            
            batches_col.update_one(
                {"id": batch_id},
                {"$set": {"file_info": update_data}}
            )
            
            sync_results.append({
                "batch_id": batch_id,
                "files_found": len(files),
                "latest_upload": files[0]["uploadDate"] if files else None
            })
        
        return jsonify({
            "success": True,
            "synced_batches": len(sync_results),
            "results": sync_results
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/init-batches", methods=["POST"])
def init_batches():
    # Limpia la colección existente y carga datos desde batches.json
    try:
        # Limpiar colección existente
        batches_col.delete_many({})
        
        with open("batches,json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("batches"):
                batches_col.insert_many(data["batches"])
        return jsonify({"success": True, "message": f"Batches reinicializados: {len(data['batches'])} batches cargados"})
    except Exception as e:
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
    app.run(debug=True, host="0.0.0.0", port=5002)
