#!/usr/bin/env python3
"""
Script para cargar batches desde batches.json a MongoDB
"""

import json
from pymongo import MongoClient

MONGO_URI = "mongodb://127.0.0.1:27018"
DB_NAME = "segmentacion_db"

print("="*70)
print("  CARGANDO BATCHES DESDE batches.json A MONGODB")
print("="*70)

# Conectar a MongoDB
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
batches_col = db["batches"]

# Verificar conexión
try:
    client.admin.command('ping')
    print("✅ Conexión exitosa a MongoDB")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")
    exit(1)

# Leer batches.json
try:
    with open("batches.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        batches = data.get("batches", [])

    print(f"✅ Leídos {len(batches)} batches desde batches.json")
except Exception as e:
    print(f"❌ Error leyendo batches.json: {e}")
    exit(1)

# Verificar si ya hay batches en la base de datos
existing_count = batches_col.count_documents({})
if existing_count > 0:
    print(f"\n⚠️  Ya existen {existing_count} batches en MongoDB")
    response = input("¿Deseas eliminarlos y recargar todos? (s/n): ")
    if response.lower() == 's':
        result = batches_col.delete_many({})
        print(f"🗑️  {result.deleted_count} batches eliminados")
    else:
        print("ℹ️  Saltando carga (batches existentes no modificados)")
        exit(0)

# Insertar batches
if batches:
    try:
        result = batches_col.insert_many(batches)
        print(f"✅ {len(result.inserted_ids)} batches insertados exitosamente")

        # Mostrar algunos ejemplos
        samples = list(batches_col.find({}, {"id": 1, "assignee": 1, "status": 1}).limit(5))
        print("\nℹ️  Ejemplos de batches insertados:")
        for i, batch in enumerate(samples, 1):
            batch_id = batch.get("id", "N/A")
            assignee = batch.get("assignee", "Sin asignar")
            status = batch.get("status", "N/A")
            print(f"   {i}. {batch_id} - Asignado a: {assignee} - Estado: {status}")

        print("\n" + "="*70)
        print("✅ CARGA COMPLETADA EXITOSAMENTE")
        print("\nPróximos pasos:")
        print("  1. Reinicia el servidor Flask: python app.py")
        print("  2. Abre http://localhost:5000/dashboard")
        print("  3. Haz clic en 'Sincronizar Archivos'")
        print("  4. Verifica que los batches muestren mongo_uploaded=True")
        print("="*70)

    except Exception as e:
        print(f"❌ Error insertando batches: {e}")
        exit(1)
else:
    print("❌ No se encontraron batches en batches.json")
    exit(1)

client.close()
