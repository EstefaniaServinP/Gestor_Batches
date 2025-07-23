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
    return jsonify(batches)

@app.route("/api/batches", methods=["POST"])
def create_batch():
    data = request.json
    
    # Genera un nuevo ID de batch
    existing_batches = list(batches_col.find({}, {"id": 1}))
    existing_ids = [int(b["id"].replace("batch_", "")) for b in existing_batches if "batch_" in b["id"]]
    new_id = max(existing_ids) + 1 if existing_ids else 1
    
    batch = {
        "id": f"batch_{new_id}",
        "assignee": data.get("assignee", ""),
        "folder": data.get("folder", ""),
        "tasks": data.get("tasks", ["segmentar", "insertar metadata", "guardar"]),
        "metadata": {
            "assigned_at": datetime.now().strftime("%Y-%m-%d"),
            "due_date": data.get("due_date", ""),
            "priority": data.get("priority", "media")
        },
        "status": "pendiente",
        "comments": data.get("comments", "")
    }
    
    result = batches_col.insert_one(batch)
    # Remover el ObjectId antes de devolver el resultado
    batch_response = batch.copy()
    return jsonify({"success": True, "batch": batch_response})

@app.route("/api/batches/<batch_id>", methods=["PUT"])
def update_batch(batch_id):
    data = request.json
    
    update_data = {}
    if "assignee" in data:
        update_data["assignee"] = data["assignee"]
    if "status" in data:
        update_data["status"] = data["status"]
    if "comments" in data:
        update_data["comments"] = data["comments"]
    if "due_date" in data:
        update_data["metadata.due_date"] = data["due_date"]
    if "priority" in data:
        update_data["metadata.priority"] = data["priority"]
    if "folder" in data:
        update_data["folder"] = data["folder"]
    
    result = batches_col.update_one({"id": batch_id}, {"$set": update_data})
    
    if result.modified_count > 0:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Batch no encontrado"}), 404

@app.route("/api/batches/<batch_id>", methods=["DELETE"])
def delete_batch(batch_id):
    result = batches_col.delete_one({"id": batch_id})
    
    if result.deleted_count > 0:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Batch no encontrado"}), 404

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
    app.run(debug=True, host="0.0.0.0", port=5001)
