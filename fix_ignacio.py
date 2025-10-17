#!/usr/bin/env python3
"""
Corregir asignación de Ignacio:
1. Quitar los 6 incorrectos (T000035-046)
2. Asignar los correctos (T000136-141)
"""
import requests

API_BASE = "http://localhost:5000/api"

# Paso 1: DESASIGNAR los incorrectos
batches_incorrectos = [
    'batch_T000035',
    'batch_T000036',
    'batch_T000037',
    'batch_T000038',
    'batch_T000039',
    'batch_T000046'
]

print("=" * 60)
print("PASO 1: Desasignando batches incorrectos...")
print("=" * 60)

for batch_id in batches_incorrectos:
    update_data = {
        "assignee": None,  # Desasignar
        "metadata": {
            "assigned_at": None
        }
    }

    try:
        response = requests.put(
            f"{API_BASE}/batches/{batch_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print(f"   ✅ {batch_id} desasignado")
        else:
            print(f"   ❌ Error {batch_id}: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error {batch_id}: {e}")

print()

# Paso 2: ASIGNAR los correctos
batches_correctos = [
    'batch_T000136',
    'batch_T000137',
    'batch_T000138',
    'batch_T000139',
    'batch_T000140',
    'batch_T000141'
]

print("=" * 60)
print("PASO 2: Asignando batches correctos a Ignacio...")
print("=" * 60)

for batch_id in batches_correctos:
    update_data = {
        "assignee": "Ignacio",
        "metadata": {
            "assigned_at": "2025-10-15"
        }
    }

    try:
        response = requests.put(
            f"{API_BASE}/batches/{batch_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print(f"   ✅ {batch_id} asignado a Ignacio")
        else:
            print(f"   ❌ Error {batch_id}: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error {batch_id}: {e}")

print()
print("=" * 60)
print("Verificando batches finales de Ignacio...")
print("=" * 60)

response = requests.get(f"{API_BASE}/batches?per_page=1000")
batches = response.json()["batches"]
ignacio_final = sorted([b['id'] for b in batches if b.get('assignee') == 'Ignacio'])

print(f"📊 Ignacio tiene ahora: {len(ignacio_final)} batches")
for bid in ignacio_final:
    print(f"   {bid}")
