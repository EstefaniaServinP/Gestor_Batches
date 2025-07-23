#!/usr/bin/env python3
"""
Script de prueba para verificar que los datos se están cargando correctamente
"""
import requests
import json

def test_api():
    base_url = "http://localhost:5001"
    
    print("🧪 Probando API del Dashboard de Segmentación")
    print("=" * 50)
    
    # Test 1: Reset de datos
    print("\n1. Reseteando datos...")
    try:
        response = requests.post(f"{base_url}/api/reset-batches")
        result = response.json()
        print(f"   ✅ Reset exitoso: {result['message']}")
    except Exception as e:
        print(f"   ❌ Error en reset: {e}")
        return
    
    # Test 2: Obtener batches
    print("\n2. Obteniendo batches...")
    try:
        response = requests.get(f"{base_url}/api/batches")
        batches = response.json()
        print(f"   ✅ Total batches: {len(batches)}")
        
        # Contar por asignado
        assignees = {}
        for batch in batches:
            assignee = batch['assignee']
            if assignee not in assignees:
                assignees[assignee] = []
            assignees[assignee].append(batch['id'])
        
        print("\n   📊 Distribución por responsable:")
        for assignee, batch_ids in assignees.items():
            print(f"   - {assignee}: {len(batch_ids)} batches")
            print(f"     {', '.join(batch_ids[:5])}{'...' if len(batch_ids) > 5 else ''}")
        
    except Exception as e:
        print(f"   ❌ Error obteniendo batches: {e}")
        return
    
    # Test 3: Verificar estructura de datos
    print("\n3. Verificando estructura de datos...")
    if batches:
        sample_batch = batches[0]
        required_fields = ['id', 'assignee', 'folder', 'metadata', 'status', 'comments']
        
        for field in required_fields:
            if field in sample_batch:
                print(f"   ✅ Campo '{field}': OK")
            else:
                print(f"   ❌ Campo '{field}': FALTANTE")
        
        # Verificar metadata
        if 'metadata' in sample_batch:
            metadata_fields = ['assigned_at', 'due_date', 'priority']
            for field in metadata_fields:
                if field in sample_batch['metadata']:
                    print(f"   ✅ Metadata '{field}': OK")
                else:
                    print(f"   ❌ Metadata '{field}': FALTANTE")
    
    print("\n🎉 Prueba completada!")

if __name__ == "__main__":
    test_api()
