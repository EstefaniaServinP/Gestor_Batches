#!/usr/bin/env python3
"""
Script de Validación: Máscaras y Batches
=========================================

Este script verifica que:
1. La conexión a MongoDB funciona correctamente
2. training_metrics.masks.files contiene archivos
3. Los batches existen en segmentacion_db
4. La extracción de batch_id funciona correctamente
5. La sincronización puede realizarse

Uso:
    python validate_masks_fix.py

Autor: Claude (Anthropic)
Fecha: 2025-10-10
"""

import sys
import re
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

# Configuración
MONGO_URI = "mongodb://127.0.0.1:27018"
SEGMENTACION_DB = "segmentacion_db"
TRAINING_DB = "QUALITY_IEMSA"  # Base de datos real donde están las máscaras
QUALITY_DB = "QUALITY_IEMSA"

def print_header(text):
    """Imprime un encabezado con estilo"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_section(text):
    """Imprime una sección con estilo"""
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print(f"{'─'*70}")

def print_success(text):
    """Imprime mensaje de éxito"""
    print(f"✅ {text}")

def print_error(text):
    """Imprime mensaje de error"""
    print(f"❌ {text}")

def print_warning(text):
    """Imprime mensaje de advertencia"""
    print(f"⚠️  {text}")

def print_info(text):
    """Imprime mensaje informativo"""
    print(f"ℹ️  {text}")

def test_connection():
    """Prueba 1: Verificar conexión a MongoDB"""
    print_section("Prueba 1: Conexión a MongoDB")

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print_success(f"Conexión exitosa a MongoDB en {MONGO_URI}")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print_error(f"No se pudo conectar a MongoDB: {e}")
        print_info("Verifica que:")
        print("   1. El túnel SSH está activo (127.0.0.1:27018)")
        print("   2. MongoDB está corriendo en el servidor remoto")
        return None

def test_training_metrics(client):
    """Prueba 2: Verificar QUALITY_IEMSA.training_metrics.masks.files"""
    print_section("Prueba 2: Verificando QUALITY_IEMSA.training_metrics.masks.files")

    try:
        db = client[TRAINING_DB]
        collection = db["training_metrics.masks.files"]

        # Contar documentos
        count = collection.count_documents({})
        print_success(f"Base de datos '{TRAINING_DB}' encontrada")
        print_success(f"Colección 'training_metrics.masks.files' tiene {count} archivos")

        if count == 0:
            print_warning("No hay archivos en training_metrics.masks.files")
            print_info("Asegúrate de haber subido máscaras a MongoDB usando GridFS")
            return False

        # Obtener algunos ejemplos
        samples = list(collection.find({}, {"filename": 1, "uploadDate": 1}).limit(5))
        print_info(f"Ejemplos de archivos encontrados:")
        for i, sample in enumerate(samples, 1):
            filename = sample.get("filename", "Sin nombre")
            upload_date = sample.get("uploadDate", "Sin fecha")
            print(f"   {i}. {filename} (subido: {upload_date})")

        return True

    except Exception as e:
        print_error(f"Error accediendo a training_metrics.masks.files: {e}")
        return False

def test_batches(client):
    """Prueba 3: Verificar batches en segmentacion_db"""
    print_section("Prueba 3: Verificando batches en segmentacion_db")

    try:
        db = client[SEGMENTACION_DB]
        collection = db["batches"]

        count = collection.count_documents({})
        print_success(f"Base de datos '{SEGMENTACION_DB}' encontrada")
        print_success(f"Colección 'batches' tiene {count} registros")

        if count == 0:
            print_warning("No hay batches en segmentacion_db.batches")
            print_info("Carga batches desde el archivo batches.json")
            return False

        # Estadísticas de mongo_uploaded
        uploaded_count = collection.count_documents({"mongo_uploaded": True})
        not_uploaded_count = collection.count_documents({"mongo_uploaded": False})

        print_info(f"Batches con mongo_uploaded=True: {uploaded_count}")
        print_info(f"Batches con mongo_uploaded=False: {not_uploaded_count}")

        # Obtener algunos ejemplos
        samples = list(collection.find({}, {"id": 1, "mongo_uploaded": 1}).limit(5))
        print_info(f"Ejemplos de batches:")
        for i, sample in enumerate(samples, 1):
            batch_id = sample.get("id", "Sin ID")
            uploaded = sample.get("mongo_uploaded", False)
            status = "✓" if uploaded else "✗"
            print(f"   {i}. {batch_id} - mongo_uploaded: {status}")

        return True

    except Exception as e:
        print_error(f"Error accediendo a segmentacion_db.batches: {e}")
        return False

def test_batch_id_extraction():
    """Prueba 4: Verificar extracción de batch_id"""
    print_section("Prueba 4: Probando extracción de batch_id desde filenames")

    test_cases = [
        ("masks_batch_20251002T133007.tar.xz", "20251002T133007"),
        ("batch_200071T.tar.xz", "200071T"),
        ("masks_batch_9.tar.xz", "9"),
        ("Batch_20250909T0001.tar.xz", "20250909T0001"),
        ("masks_20251002T132967.tar.xz", "20251002T132967"),
    ]

    pattern = r'[Bb]atch[_\-]?(\d+[A-Z]?\d*)'
    all_passed = True

    for filename, expected_id in test_cases:
        matches = re.findall(pattern, filename)
        if matches:
            extracted_id = matches[0]
            if extracted_id == expected_id:
                print_success(f"{filename} → batch_{extracted_id}")
            else:
                print_error(f"{filename} → batch_{extracted_id} (esperaba: batch_{expected_id})")
                all_passed = False
        else:
            print_error(f"{filename} → No se pudo extraer ID")
            all_passed = False

    return all_passed

def test_sync_simulation(client):
    """Prueba 5: Simular sincronización"""
    print_section("Prueba 5: Simulando sincronización de máscaras con batches")

    try:
        # Obtener batches
        batches_db = client[SEGMENTACION_DB]
        batches_col = batches_db["batches"]
        batches = list(batches_col.find({}, {"id": 1}).limit(10))

        if not batches:
            print_warning("No hay batches para sincronizar")
            return False

        # Obtener máscaras
        training_db = client[TRAINING_DB]
        masks_col = training_db["training_metrics.masks.files"]

        # Extraer números de batch
        batch_numbers = {}
        for batch in batches:
            batch_id = batch["id"]
            match = re.search(r'(\d+[A-Z]?\d*)', batch_id)
            if match:
                batch_numbers[batch_id] = match.group(1)

        if not batch_numbers:
            print_warning("No se pudieron extraer números de batch")
            return False

        # Buscar archivos que coincidan
        all_numbers = list(batch_numbers.values())
        numbers_pattern = "|".join(all_numbers)
        mega_pattern = f"(masks_)?(batch_|Batch_)?({numbers_pattern})"

        files = list(masks_col.find(
            {"filename": {"$regex": mega_pattern, "$options": "i"}},
            {"filename": 1}
        ))

        print_success(f"Encontrados {len(files)} archivos que coinciden con {len(batch_numbers)} batches")

        # Mapear archivos a batches
        batch_file_map = {}
        for batch_id, batch_num in batch_numbers.items():
            matching_files = [f for f in files if batch_num in f.get("filename", "")]
            batch_file_map[batch_id] = matching_files

            if matching_files:
                print_success(f"{batch_id} → {len(matching_files)} archivo(s) encontrado(s)")
            else:
                print_info(f"{batch_id} → Sin archivos")

        # Resumen
        batches_with_files = sum(1 for files in batch_file_map.values() if files)
        print_info(f"\nResumen: {batches_with_files}/{len(batch_numbers)} batches tienen archivos")

        return True

    except Exception as e:
        print_error(f"Error en simulación de sincronización: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print_header("VALIDACIÓN: Correcciones de Máscaras y Batches")
    print_info("Este script verifica que las correcciones funcionan correctamente")

    # Prueba 1: Conexión
    client = test_connection()
    if not client:
        print_error("\n❌ FALLO: No se pudo conectar a MongoDB")
        print_info("Solución: Verifica el túnel SSH y la conexión a MongoDB")
        sys.exit(1)

    # Prueba 2: training_metrics
    training_ok = test_training_metrics(client)

    # Prueba 3: batches
    batches_ok = test_batches(client)

    # Prueba 4: extracción de batch_id
    extraction_ok = test_batch_id_extraction()

    # Prueba 5: simulación de sincronización
    sync_ok = False
    if training_ok and batches_ok:
        sync_ok = test_sync_simulation(client)
    else:
        print_section("Prueba 5: Simulación de sincronización")
        print_warning("Saltando prueba (faltan datos previos)")

    # Resumen final
    print_section("RESUMEN FINAL")

    results = {
        "Conexión a MongoDB": client is not None,
        "training_metrics.masks.files": training_ok,
        "segmentacion_db.batches": batches_ok,
        "Extracción de batch_id": extraction_ok,
        "Simulación de sincronización": sync_ok,
    }

    all_passed = all(results.values())

    for test_name, passed in results.items():
        if passed:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")

    print("\n" + "="*70)
    if all_passed:
        print("✅ ¡TODAS LAS PRUEBAS PASARON!")
        print("\nPróximos pasos:")
        print("  1. Reinicia el servidor Flask: python app.py")
        print("  2. Abre el dashboard en tu navegador")
        print("  3. Haz clic en 'Sincronizar Archivos' en el dashboard")
        print("  4. Verifica que los batches muestren mongo_uploaded=True")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("\nRevisa los errores arriba y corrige los problemas antes de continuar")
    print("="*70)

    client.close()
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
