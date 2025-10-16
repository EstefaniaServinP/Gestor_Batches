#!/usr/bin/env python3
"""
Script para reasignar un batch a otro responsable
"""

from pymongo import MongoClient
import sys

MONGO_URI = "mongodb://192.168.1.93:27017"
DB_NAME = "segmentacion_db"

def reassign_batch(batch_id, new_assignee):
    """Reasignar un batch a un nuevo responsable"""

    print(f"🔄 Reasignando batch: {batch_id}")
    print(f"👤 Nuevo responsable: {new_assignee}")
    print()

    try:
        # Conectar a MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        batches_col = db["batches"]

        # Buscar el batch
        batch = batches_col.find_one({"id": batch_id})

        if not batch:
            print(f"❌ Batch '{batch_id}' no encontrado")
            return

        old_assignee = batch.get('assignee')
        print(f"📊 Estado actual:")
        print(f"  - Responsable actual: {old_assignee}")
        print(f"  - Status: {batch.get('status')}")
        print()

        # Actualizar
        result = batches_col.update_one(
            {"id": batch_id},
            {"$set": {
                "assignee": new_assignee if new_assignee != "null" else None
            }}
        )

        if result.modified_count > 0:
            print(f"✅ Batch reasignado exitosamente")
            print(f"  {old_assignee} → {new_assignee}")
        else:
            print(f"⚠️ No se realizaron cambios (quizás ya tenía ese responsable)")

        client.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python reassign_batch.py <batch_id> <nuevo_responsable>")
        print()
        print("Ejemplos:")
        print("  python reassign_batch.py batch_T000054 Mauricio")
        print("  python reassign_batch.py batch_T000054 null    # Para sin asignar")
        sys.exit(1)

    batch_id = sys.argv[1]
    new_assignee = sys.argv[2]

    reassign_batch(batch_id, new_assignee)
