#!/usr/bin/env python3
"""
Script para verificar el estado de un batch en MongoDB
"""

from pymongo import MongoClient
import sys
import json

MONGO_URI = "mongodb://192.168.1.93:27017"
DB_NAME = "segmentacion_db"

def check_batch(batch_id):
    """Verificar estado de un batch"""

    print(f"🔍 Buscando batch: {batch_id}")
    print(f"📍 Conexión: {MONGO_URI}")
    print(f"📂 Base de datos: {DB_NAME}")
    print()

    try:
        # Conectar a MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        batches_col = db["batches"]

        # Buscar el batch
        batch = batches_col.find_one({"id": batch_id})

        if batch:
            print("✅ BATCH ENCONTRADO")
            print("=" * 60)

            # Función para convertir tipos no serializables
            def convert_for_json(obj):
                from datetime import datetime
                from bson import ObjectId

                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, ObjectId):
                    return str(obj)
                elif isinstance(obj, dict):
                    return {k: convert_for_json(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_for_json(item) for item in obj]
                else:
                    return obj

            batch_clean = convert_for_json(batch)
            print(json.dumps(batch_clean, indent=2, ensure_ascii=False))
            print("=" * 60)
            print()

            # Análisis del estado
            print("📊 ANÁLISIS:")
            print(f"  - ID: {batch.get('id')}")
            print(f"  - Responsable: {batch.get('assignee') or '❌ SIN ASIGNAR'}")
            print(f"  - Status: {batch.get('status')}")
            print(f"  - Mongo Uploaded: {batch.get('mongo_uploaded')}")
            print(f"  - Comentarios: {batch.get('comments') or '(vacío)'}")

            if batch.get('metadata'):
                print(f"  - Metadata:")
                for key, value in batch.get('metadata', {}).items():
                    print(f"    • {key}: {value}")

            print()

            # Determinar por qué no aparece
            print("🔍 DIAGNÓSTICO:")
            assignee = batch.get('assignee')

            if assignee and assignee != '' and assignee != None:
                print(f"  ⚠️ El batch YA está asignado a: {assignee}")
                print(f"  📍 Por eso NO aparece en 'Batches No Asignados'")
                print(f"  📍 Debería aparecer en la tarjeta de '{assignee}'")
            else:
                print(f"  ✅ El batch NO está asignado")
                print(f"  ✅ DEBERÍA aparecer en 'Batches No Asignados'")
                print(f"  ⚠️ Si no aparece, hay un problema en el frontend")

        else:
            print("❌ BATCH NO ENCONTRADO")
            print(f"  El batch '{batch_id}' no existe en la base de datos")
            print()

            # Buscar batches similares
            print("🔍 Buscando batches similares...")
            similar = list(batches_col.find(
                {"id": {"$regex": batch_id[:10]}},
                limit=5
            ))

            if similar:
                print(f"  Encontrados {len(similar)} batches similares:")
                for b in similar:
                    print(f"    - {b.get('id')} (Asignado a: {b.get('assignee') or 'Sin asignar'})")
            else:
                print("  No se encontraron batches similares")

        client.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        batch_id = sys.argv[1]
    else:
        batch_id = "batch_T000054"  # Default

    check_batch(batch_id)
