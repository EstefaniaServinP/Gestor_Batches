#!/usr/bin/env python3
"""
Script para explorar la estructura completa de MongoDB
y encontrar dónde están las máscaras
"""

from pymongo import MongoClient

MONGO_URI = "mongodb://127.0.0.1:27018"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

print("="*70)
print("  EXPLORANDO MONGODB - Todas las bases de datos y colecciones")
print("="*70)

# Listar todas las bases de datos
databases = client.list_database_names()
print(f"\n📊 Bases de datos encontradas: {len(databases)}")
for db_name in databases:
    print(f"\n{'─'*70}")
    print(f"📁 Base de datos: {db_name}")
    print(f"{'─'*70}")

    db = client[db_name]
    collections = db.list_collection_names()

    if not collections:
        print("   (vacía)")
        continue

    for coll_name in collections:
        coll = db[coll_name]
        count = coll.count_documents({})
        print(f"   📂 {coll_name}: {count} documentos")

        # Si hay documentos, mostrar un ejemplo
        if count > 0:
            sample = coll.find_one()
            if sample:
                # Mostrar las claves del documento
                keys = list(sample.keys())
                print(f"      Campos: {', '.join(keys[:10])}")

                # Si tiene filename, mostrar algunos ejemplos
                if "filename" in keys:
                    examples = list(coll.find({}, {"filename": 1}).limit(3))
                    print(f"      Ejemplos de filename:")
                    for ex in examples:
                        print(f"        - {ex.get('filename', 'N/A')}")

print("\n" + "="*70)
print("✅ Exploración completada")
print("="*70)

client.close()
