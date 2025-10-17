#!/usr/bin/env python3
"""
Script para detectar y restaurar batches que fueron quitados a Ignacio
"""
import requests
from datetime import datetime

# Obtener todos los batches
response = requests.get("http://localhost:5000/api/batches?per_page=1000")
batches = response.json()["batches"]

# Batches actuales de Ignacio
ignacio_current = [b for b in batches if b.get('assignee') == 'Ignacio']
print(f"📊 Batches ACTUALES de Ignacio: {len(ignacio_current)}")
print(f"   IDs: {[b['id'] for b in ignacio_current]}")
print()

# Buscar batches que podrían haber sido de Ignacio
# Criterios:
# 1. Batches sin asignar (assignee=null o '')
# 2. Batches asignados recientemente HOY a otra persona
# 3. Batches con patrón similar a los de Ignacio (T000xxx)

print("🔍 Batches sin asignar con patrón T000xxx (posibles de Ignacio):")
unassigned_T = [b for b in batches if (not b.get('assignee') or b.get('assignee').strip() == '') and b['id'].startswith('batch_T000')]
for b in unassigned_T[:20]:  # Mostrar primeros 20
    print(f"   {b['id']}")
print(f"   Total: {len(unassigned_T)}")
print()

print("🔍 Batches asignados a otros HOY con patrón T000xxx:")
today = datetime.now().strftime("%Y-%m-%d")
others_today_T = [b for b in batches
                   if b.get('assignee') and b.get('assignee') != 'Ignacio'
                   and b['id'].startswith('batch_T000')
                   and b.get('metadata', {}).get('assigned_at', '') == today]
for b in others_today_T[:20]:
    print(f"   {b['id']} -> {b.get('assignee')}")
print(f"   Total: {len(others_today_T)}")
print()

# Sugerencias de restauración
print("=" * 60)
print("💡 SUGERENCIAS PARA RESTAURAR:")
print("=" * 60)

if unassigned_T:
    print(f"\n1. Tienes {len(unassigned_T)} batches T000xxx SIN ASIGNAR")
    print("   Posiblemente eran de Ignacio y los desasignaste.")
    print("   ¿Quieres reasignarlos a Ignacio?")
    print()
    print("   Comando:")
    print(f"   python restore_ignacio.py --restore-unassigned")

if others_today_T:
    print(f"\n2. Tienes {len(others_today_T)} batches T000xxx asignados HOY a otros")
    print("   Podrían haber sido de Ignacio originalmente.")
    print()
    print("   Lista:")
    for b in others_today_T:
        print(f"      {b['id']} -> {b.get('assignee')}")

print("\n" + "=" * 60)
print("¿Cuántos batches DEBERÍA tener Ignacio en total?")
print("Actualmente tiene:", len(ignacio_current))
