#!/usr/bin/env python3
"""
Script de prueba para verificar el endpoint /api/batches/quick-create
"""

import requests
import json

# Configuración
BASE_URL = "http://192.168.1.93:5000"
ENDPOINT = "/api/batches/quick-create"

def test_quick_create():
    """Probar el endpoint de carga rápida"""

    print("🧪 Probando endpoint de carga rápida...")
    print(f"📍 URL: {BASE_URL}{ENDPOINT}")
    print()

    # Datos de prueba
    test_data = {
        "batch_list": "batch_TEST001\nbatch_TEST002\nbatch_TEST003"
    }

    print("📤 Enviando datos:")
    print(json.dumps(test_data, indent=2))
    print()

    try:
        # Hacer la petición
        response = requests.post(
            f"{BASE_URL}{ENDPOINT}",
            json=test_data,
            timeout=5
        )

        print(f"✅ Respuesta recibida:")
        print(f"  - Status Code: {response.status_code}")
        print(f"  - Headers: {dict(response.headers)}")
        print()

        if response.status_code == 200:
            data = response.json()
            print("📊 Datos de respuesta:")
            print(json.dumps(data, indent=2))
            print()

            if data.get("success"):
                print("✅ ¡Endpoint funcionando correctamente!")
                print(f"  - Batches creados: {len(data.get('created', []))}")
                print(f"  - Batches omitidos: {len(data.get('skipped', []))}")
            else:
                print(f"❌ Error en el endpoint: {data.get('error')}")
        else:
            print(f"❌ Error HTTP {response.status_code}")
            print(f"  Respuesta: {response.text}")

    except requests.exceptions.ConnectionError as e:
        print("❌ ERROR DE CONEXIÓN")
        print(f"  No se pudo conectar a {BASE_URL}")
        print(f"  Detalles: {e}")
        print()
        print("📝 Posibles causas:")
        print("  1. Flask no está corriendo")
        print("  2. El puerto es incorrecto")
        print("  3. Firewall bloqueando la conexión")
        print()
        print("💡 Solución:")
        print("  Ejecuta: python app.py")

    except requests.exceptions.Timeout as e:
        print("❌ ERROR DE TIMEOUT")
        print(f"  El servidor tardó más de 5 segundos en responder")
        print(f"  Detalles: {e}")

    except Exception as e:
        print(f"❌ ERROR INESPERADO: {type(e).__name__}")
        print(f"  Detalles: {e}")

if __name__ == "__main__":
    test_quick_create()
