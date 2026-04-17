"""
Script para inicializar la base de datos Quality_Hope con todas sus colecciones e índices.
Ejecutar una vez antes de arrancar la aplicación por primera vez.

Uso:
    python init_quality_hope.py
"""

from pymongo import MongoClient, ASCENDING
from datetime import datetime
import os

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "Quality_Hope"

def init():
    print(f"Conectando a {MONGO_URI} ...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print(f"✅ Conexión OK")

    db = client[DB_NAME]
    print(f"📂 Base de datos: {DB_NAME}")

    # ------------------------------------------------------------------ batches
    batches = db["batches"]
    batches.create_index([("id", ASCENDING)], unique=True, background=True)
    batches.create_index([("assignee", ASCENDING)], background=True)
    batches.create_index([("status", ASCENDING)], background=True)
    batches.create_index([("metadata.assigned_at", ASCENDING)], background=True)
    batches.create_index([("assignee", ASCENDING), ("status", ASCENDING)], background=True)
    batches.create_index([("status", ASCENDING), ("metadata.assigned_at", ASCENDING)], background=True)
    print("  ✅ batches — 6 índices creados")

    # ---------------------------------------------------------------- masks.files
    masks = db["masks.files"]
    masks.create_index([("filename", ASCENDING)], background=True)
    masks.create_index([("uploadDate", ASCENDING)], background=True)
    masks.create_index([("metadata.uploaded_by", ASCENDING)], background=True)
    print("  ✅ masks.files — 3 índices creados")

    # ------------------------------------------------------------ segmentadores
    segmentadores = db["segmentadores"]
    segmentadores.create_index([("name", ASCENDING)], unique=True, background=True)

    if segmentadores.count_documents({}) == 0:
        default_team = ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        segmentadores.insert_many([
            {"name": n, "role": "Segmentador", "email": "", "created_at": now}
            for n in default_team
        ])
        print(f"  ✅ segmentadores — equipo inicial insertado: {default_team}")
    else:
        print(f"  ✅ segmentadores — {segmentadores.count_documents({})} registros existentes")

    # --------------------------------------------------- Reporte_avances_masks
    reporte = db["Reporte_avances_masks"]
    reporte.create_index([("batch_id", ASCENDING)], background=True)
    reporte.create_index([("segmentador", ASCENDING)], background=True)
    reporte.create_index([("fecha", ASCENDING)], background=True)
    reporte.create_index([("segmentador", ASCENDING), ("fecha", ASCENDING)], background=True)
    print("  ✅ Reporte_avances_masks — 4 índices creados")

    # -------------------------------------------------------- resumen final
    colecciones = db.list_collection_names()
    print(f"\n✅ Quality_Hope inicializada correctamente")
    print(f"   Colecciones: {sorted(colecciones)}")
    client.close()

if __name__ == "__main__":
    init()
