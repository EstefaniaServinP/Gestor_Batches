#!/usr/bin/env python3
"""
Script para restaurar batches de Ignacio que fueron desasignados
"""
import requests
import json

API_BASE = "http://localhost:5000/api"

# Los batches actuales de Ignacio (T000093-T000098, T000142)
# Buscaremos batches T000xxx que estén sin asignar y que probablemente eran de Ignacio

# Obtener todos los batches
response = requests.get(f"{API_BASE}/batches?per_page=1000")
batches = response.json()["batches"]

# Batches actuales de Ignacio
ignacio_actual = [b['id'] for b in batches if b.get('assignee') == 'Ignacio']
print(f"📊 Ignacio tiene actualmente: {len(ignacio_actual)} batches")
print(f"   {ignacio_actual}")
print()

# Buscar batches candidatos para restaurar:
# 1. Sin assignee
# 2. Con metadata.assigned_at = "2025-10-15"
# 3. Patrón T000xxx (rango cercano a los que tiene)

candidatos = []
for b in batches:
    assignee = (b.get('assignee') or '').strip()
    assigned_at = b.get('metadata', {}).get('assigned_at', '')
    batch_id = b['id']

    # Criterios:
    if (not assignee and assigned_at == "2025-10-15" and batch_id.startswith('batch_T000')):
        # Extraer número
        try:
            num = int(batch_id.replace('batch_T', ''))
            # Buscar en rango 35-116 (cerca de los que tiene: 93-98)
            if 35 <= num <= 116:
                candidatos.append({
                    'id': batch_id,
                    'num': num,
                    'status': b.get('status', 'NS')
                })
        except:
            pass

# Ordenar por número
candidatos.sort(key=lambda x: x['num'])

print(f"🔍 Encontrados {len(candidatos)} batches candidatos para restaurar:")
for c in candidatos:
    print(f"   {c['id']:20} | Status: {c['status']}")
print()

# Ignacio debería tener 13 batches (tenía 13 antes)
# Actualmente tiene 7
# Necesita: 6 batches más

batches_a_restaurar = candidatos[:6]  # Los primeros 6

print("=" * 60)
print(f"✅ VAMOS A RESTAURAR {len(batches_a_restaurar)} BATCHES A IGNACIO:")
print("=" * 60)
for b in batches_a_restaurar:
    print(f"   {b['id']}")
print()

# Confirmar
confirmar = input("¿Confirmas que quieres reasignar estos batches a Ignacio? (si/no): ")

if confirmar.lower() != 'si':
    print("❌ Operación cancelada")
    exit(0)

# Reasignar batches
print()
print("🔄 Reasignando batches...")
exitos = 0
errores = 0

for batch_info in batches_a_restaurar:
    batch_id = batch_info['id']

    # Datos para actualizar
    update_data = {
        "assignee": "Ignacio",
        "metadata": {
            "assigned_at": "2025-10-16"  # Fecha de hoy (restauración)
        }
    }

    try:
        response = requests.put(
            f"{API_BASE}/batches/{batch_id}",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            print(f"   ✅ {batch_id} reasignado a Ignacio")
            exitos += 1
        else:
            print(f"   ❌ Error en {batch_id}: {response.status_code}")
            errores += 1
    except Exception as e:
        print(f"   ❌ Error en {batch_id}: {e}")
        errores += 1

print()
print("=" * 60)
print(f"✅ Completado: {exitos} exitosos, {errores} errores")
print("=" * 60)
print()
print("🔍 Verificando batches de Ignacio después de restaurar...")
response = requests.get(f"{API_BASE}/batches?per_page=1000")
batches = response.json()["batches"]
ignacio_final = [b['id'] for b in batches if b.get('assignee') == 'Ignacio']
print(f"📊 Ignacio tiene ahora: {len(ignacio_final)} batches")
for bid in sorted(ignacio_final):
    print(f"   {bid}")
