#!/usr/bin/env python3
"""
Cargar batches nuevos T000169-T000268 a MongoDB
"""
import requests
import json

API_BASE = "http://localhost:5000/api"

# Leer el archivo JSON
with open('nuevos_batches_T169-268.json', 'r') as f:
    data = json.load(f)

# Agregar modo "add" para no reemplazar
data['mode'] = 'add'

print("🚀 Cargando 100 batches nuevos (T000169 - T000268)...")

response = requests.post(
    f"{API_BASE}/data/batches/upload",
    json=data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ {result['inserted_count']} batches cargados exitosamente a MongoDB")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
