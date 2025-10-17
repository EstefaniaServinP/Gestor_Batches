#!/usr/bin/env python3
"""
Script para eliminar batches específicos
"""
import requests

API_BASE = "http://localhost:5000/api"

# Batches a eliminar
batches_to_delete = [
    # Serie F (000051F - 000112F)
    'batch_000051F', 'batch_000052F', 'batch_000053F', 'batch_000054F', 'batch_000055F',
    'batch_000056F', 'batch_000057F', 'batch_000058F', 'batch_000059F', 'batch_000060F',
    'batch_000061F', 'batch_000062F', 'batch_000063F', 'batch_000064F', 'batch_000065F',
    'batch_000066F', 'batch_000067F', 'batch_000068F', 'batch_000069F', 'batch_000070F',
    'batch_000071F', 'batch_000072F', 'batch_000073F', 'batch_000074F', 'batch_000075F',
    'batch_000076F', 'batch_000077F', 'batch_000078F', 'batch_000079F', 'batch_000080F',
    'batch_000081F', 'batch_000082F', 'batch_000083F', 'batch_000084F', 'batch_000085F',
    'batch_000086F', 'batch_000087F', 'batch_000088F', 'batch_000089F', 'batch_000090F',
    'batch_000091F', 'batch_000092F', 'batch_000093F', 'batch_000094F', 'batch_000095F',
    'batch_000096F', 'batch_000097F', 'batch_000098F', 'batch_000099F', 'batch_000100F',
    'batch_000101F', 'batch_000102F', 'batch_000103F', 'batch_000104F', 'batch_000105F',
    'batch_000106F', 'batch_000107F', 'batch_000108F', 'batch_000109F', 'batch_000110F',
    'batch_000111F', 'batch_000112F',

    # Serie T (T000002 - T000032, T000061 - T000092)
    'batch_T000002', 'batch_T000003', 'batch_T000004', 'batch_T000005', 'batch_T000006',
    'batch_T000007', 'batch_T000008', 'batch_T000009', 'batch_T000010', 'batch_T000011',
    'batch_T000012', 'batch_T000013', 'batch_T000014', 'batch_T000015', 'batch_T000016',
    'batch_T000017', 'batch_T000018', 'batch_T000019', 'batch_T000020', 'batch_T000021',
    'batch_T000022', 'batch_T000023', 'batch_T000024', 'batch_T000025', 'batch_T000026',
    'batch_T000027', 'batch_T000028', 'batch_T000029', 'batch_T000030', 'batch_T000031',
    'batch_T000032', 'batch_T000061', 'batch_T000062', 'batch_T000063', 'batch_T000064',
    'batch_T000065', 'batch_T000066', 'batch_T000067', 'batch_T000068', 'batch_T000069',
    'batch_T000070', 'batch_T000071', 'batch_T000072', 'batch_T000073', 'batch_T000074',
    'batch_T000075', 'batch_T000076', 'batch_T000077', 'batch_T000078', 'batch_T000079',
    'batch_T000080', 'batch_T000081', 'batch_T000082', 'batch_T000083', 'batch_T000084',
    'batch_T000085', 'batch_T000086', 'batch_T000087', 'batch_T000088', 'batch_T000089',
    'batch_T000090', 'batch_T000091', 'batch_T000092'
]

print("=" * 70)
print(f"🗑️  ELIMINANDO {len(batches_to_delete)} BATCHES")
print("=" * 70)
print()

exitos = 0
errores = 0
no_encontrados = 0

for batch_id in batches_to_delete:
    try:
        response = requests.delete(
            f"{API_BASE}/batches/{batch_id}",
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            print(f"   ✅ {batch_id} eliminado")
            exitos += 1
        elif response.status_code == 404:
            print(f"   ⚠️  {batch_id} no encontrado (ya eliminado o no existe)")
            no_encontrados += 1
        else:
            print(f"   ❌ Error {batch_id}: {response.status_code}")
            errores += 1
    except Exception as e:
        print(f"   ❌ Error {batch_id}: {e}")
        errores += 1

print()
print("=" * 70)
print(f"📊 RESUMEN:")
print(f"   ✅ Eliminados exitosamente: {exitos}")
print(f"   ⚠️  No encontrados: {no_encontrados}")
print(f"   ❌ Errores: {errores}")
print(f"   📝 Total procesados: {len(batches_to_delete)}")
print("=" * 70)
print()

# Verificar batches restantes
print("🔍 Verificando batches restantes...")
response = requests.get(f"{API_BASE}/batches?per_page=1000")
batches = response.json()["batches"]

batches_f = [b['id'] for b in batches if b['id'].endswith('F')]
batches_t = [b['id'] for b in batches if b['id'].startswith('batch_T')]

print(f"   Serie F restantes: {len(batches_f)}")
if batches_f:
    for bid in sorted(batches_f)[:10]:  # Mostrar primeros 10
        print(f"      {bid}")
    if len(batches_f) > 10:
        print(f"      ... y {len(batches_f) - 10} más")

print(f"   Serie T restantes: {len(batches_t)}")
if batches_t:
    for bid in sorted(batches_t)[:10]:  # Mostrar primeros 10
        print(f"      {bid}")
    if len(batches_t) > 10:
        print(f"      ... y {len(batches_t) - 10} más")

print()
print("✅ Proceso completado. Ahora puedes agregar los nuevos batches.")
