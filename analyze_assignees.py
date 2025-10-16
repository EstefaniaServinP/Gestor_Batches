#!/usr/bin/env python3
"""
Script para analizar los responsables (assignees) de todos los batches
y detectar asignaciones a personas que no están en el equipo actual
"""

from pymongo import MongoClient
from collections import Counter

MONGO_URI = "mongodb://192.168.1.93:27017"
DB_NAME = "segmentacion_db"

# Miembros actuales del equipo (según el sistema)
CURRENT_TEAM = ["Mauricio", "Maggie", "Ceci", "Flor", "Ignacio"]

def analyze_assignees():
    """Analizar todos los assignees en la base de datos"""

    print("🔍 ANÁLISIS DE RESPONSABLES EN MONGODB")
    print("=" * 70)
    print()

    try:
        # Conectar a MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        batches_col = db["batches"]

        # Contar total de batches
        total_batches = batches_col.count_documents({})
        print(f"📦 Total de batches en MongoDB: {total_batches}")
        print()

        # Obtener todos los assignees únicos
        pipeline = [
            {"$group": {
                "_id": "$assignee",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]

        assignees_data = list(batches_col.aggregate(pipeline))

        print("📊 DISTRIBUCIÓN POR RESPONSABLE:")
        print("-" * 70)

        assignees_in_team = []
        assignees_not_in_team = []
        unassigned_count = 0

        for item in assignees_data:
            assignee = item["_id"]
            count = item["count"]

            if assignee is None or assignee == "":
                unassigned_count = count
                print(f"  {'SIN ASIGNAR':<20} | {count:>5} batches | ✅ OK (disponibles)")
            elif assignee in CURRENT_TEAM:
                assignees_in_team.append((assignee, count))
                print(f"  {assignee:<20} | {count:>5} batches | ✅ En el equipo")
            else:
                assignees_not_in_team.append((assignee, count))
                print(f"  {assignee:<20} | {count:>5} batches | ❌ NO en el equipo")

        print()
        print("=" * 70)
        print()

        # Resumen
        print("📋 RESUMEN:")
        print("-" * 70)
        print(f"  Total batches:              {total_batches}")
        print(f"  Sin asignar:                {unassigned_count}")
        print(f"  Asignados a equipo actual:  {sum(c for _, c in assignees_in_team)}")
        print(f"  Asignados a NO-miembros:    {sum(c for _, c in assignees_not_in_team)}")
        print()

        if assignees_not_in_team:
            print("⚠️  PROBLEMA DETECTADO:")
            print(f"  Hay {sum(c for _, c in assignees_not_in_team)} batches asignados a personas que NO están en el equipo actual")
            print()
            print("  Personas NO en el equipo:")
            for assignee, count in assignees_not_in_team:
                print(f"    • {assignee}: {count} batches")
            print()
            print("  Equipo actual:")
            for member in CURRENT_TEAM:
                print(f"    • {member}")
            print()
            print("=" * 70)
            print()
            print("💡 SOLUCIONES:")
            print()
            print("  Opción 1: Desasignar TODOS los batches de NO-miembros")
            print("  ---------------------------------------------------------")
            print("  python mass_reassign.py --unassign-all-non-members")
            print()
            print("  Opción 2: Reasignar todos a un miembro específico")
            print("  ---------------------------------------------------------")
            print("  python mass_reassign.py --reassign-non-members Mauricio")
            print()
            print("  Opción 3: Agregar las personas faltantes al equipo")
            print("  ---------------------------------------------------------")
            for assignee, count in assignees_not_in_team:
                print(f"  curl -X POST http://localhost:5000/api/segmentadores \\")
                print(f"    -H 'Content-Type: application/json' \\")
                print(f"    -d '{{\"name\": \"{assignee}\", \"email\": \"{assignee.lower()}@example.com\"}}'")
                print()

        client.close()

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_assignees()
