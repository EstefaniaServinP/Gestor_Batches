#!/usr/bin/env python3
"""
Script para verificar el estatus de los batches de Flor e Ignacio
"""

from pymongo import MongoClient
import sys

try:
    # Conectar a MongoDB
    MONGO_URI = "mongodb://admin:hxsCiKTUt0GNpqtaeRJL@192.168.100.26:27017/?authSource=admin"
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["QA"]
    batches_col = db["batches"]
    
    # Test connection
    count = batches_col.count_documents({})
    print(f"✅ Conexión exitosa. Total batches en DB: {count}")
    
    # Batches de Flor
    flor_batches = [
        'batch_9', 'batch_11', 'batch_13', 'batch_14', 'batch_23', 'batch_24', 'batch_25',
        'batch_28', 'batch_34', 'batch_36', 'batch_38', 'batch_39', 'batch_41', 'batch_42',
        'batch_43', 'batch_44', 'batch_45'
    ]
    
    # Batches de Ignacio
    ignacio_batches = [
        'batch_15', 'batch_16', 'batch_17', 'batch_21', 'batch_46', 'batch_47', 'batch_48',
        'batch_49', 'batch_50', 'batch_51', 'batch_52', 'batch_53', 'batch_54', 'batch_55'
    ]
    
    print("\n" + "="*60)
    print("🌸 BATCHES DE FLOR")
    print("="*60)
    
    flor_found = 0
    flor_status_count = {"S": 0, "In": 0, "NS": 0}
    
    for batch_id in flor_batches:
        batch = batches_col.find_one({"id": batch_id})
        if batch:
            flor_found += 1
            status = batch.get("status", "?")
            assignee = batch.get("assignee", "?")
            mongo = "✅" if batch.get("mongo_uploaded", False) else "❌"
            review = batch.get("metadata", {}).get("review_status", "pendiente")
            
            if status in flor_status_count:
                flor_status_count[status] += 1
            
            status_emoji = {"S": "✅", "In": "⏳", "NS": "⭕"}.get(status, "❓")
            
            print(f"{batch_id}: {status_emoji} {status} | {assignee} | MongoDB:{mongo} | Review:{review}")
        else:
            print(f"{batch_id}: ❌ NO ENCONTRADO EN DB")
    
    print(f"\n📊 Flor - Encontrados: {flor_found}/{len(flor_batches)}")
    print(f"   • Segmentados (S): {flor_status_count['S']}")
    print(f"   • Incompletos (In): {flor_status_count['In']}")
    print(f"   • No Segmentados (NS): {flor_status_count['NS']}")
    
    print("\n" + "="*60)
    print("🔥 BATCHES DE IGNACIO")
    print("="*60)
    
    ignacio_found = 0
    ignacio_status_count = {"S": 0, "In": 0, "NS": 0}
    
    for batch_id in ignacio_batches:
        batch = batches_col.find_one({"id": batch_id})
        if batch:
            ignacio_found += 1
            status = batch.get("status", "?")
            assignee = batch.get("assignee", "?")
            mongo = "✅" if batch.get("mongo_uploaded", False) else "❌"
            review = batch.get("metadata", {}).get("review_status", "pendiente")
            
            if status in ignacio_status_count:
                ignacio_status_count[status] += 1
            
            status_emoji = {"S": "✅", "In": "⏳", "NS": "⭕"}.get(status, "❓")
            
            print(f"{batch_id}: {status_emoji} {status} | {assignee} | MongoDB:{mongo} | Review:{review}")
        else:
            print(f"{batch_id}: ❌ NO ENCONTRADO EN DB")
    
    print(f"\n📊 Ignacio - Encontrados: {ignacio_found}/{len(ignacio_batches)}")
    print(f"   • Segmentados (S): {ignacio_status_count['S']}")
    print(f"   • Incompletos (In): {ignacio_status_count['In']}")
    print(f"   • No Segmentados (NS): {ignacio_status_count['NS']}")
    
    # Resumen general
    print("\n" + "="*60)
    print("📈 RESUMEN GENERAL")
    print("="*60)
    
    total_found = flor_found + ignacio_found
    total_expected = len(flor_batches) + len(ignacio_batches)
    total_s = flor_status_count["S"] + ignacio_status_count["S"]
    total_in = flor_status_count["In"] + ignacio_status_count["In"]
    total_ns = flor_status_count["NS"] + ignacio_status_count["NS"]
    
    print(f"Total batches esperados: {total_expected}")
    print(f"Total batches encontrados: {total_found}")
    print(f"")
    print(f"✅ Segmentados (S): {total_s}")
    print(f"⏳ Incompletos (In): {total_in}")
    print(f"⭕ No Segmentados (NS): {total_ns}")
    
    # Calcular porcentajes
    if total_found > 0:
        pct_s = (total_s / total_found) * 100
        pct_in = (total_in / total_found) * 100
        pct_ns = (total_ns / total_found) * 100
        
        print(f"")
        print(f"Progreso de segmentación:")
        print(f"  • {pct_s:.1f}% Completados")
        print(f"  • {pct_in:.1f}% En progreso")
        print(f"  • {pct_ns:.1f}% Pendientes")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
