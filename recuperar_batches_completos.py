#!/usr/bin/env python3
"""
Script para recuperar TODOS los batches que estaban hardcodeados en el sistema.

Este script toma la lista completa de batches del historial de Git y los
agrega a MongoDB con la configuración correcta.
"""

import os
import json
from datetime import datetime
from db import get_db

# Lista COMPLETA de batches que estaban hardcodeados (del historial de Git)
ALL_HARDCODED_BATCHES = [
    # Batches con timestamps
    'batch_20251002T105618', 'batch_20251002T105716', 'batch_20251002T105814', 'batch_20251002T105912',
    'batch_20251002T110010', 'batch_20251002T110107', 'batch_20251002T110205', 'batch_20251002T110302',
    'batch_20251002T110359', 'batch_20251002T110457', 'batch_20251002T110554', 'batch_20251002T110652',
    'batch_20251002T110749', 'batch_20251002T110847', 'batch_20251002T110945', 'batch_20251002T111044',
    'batch_20251002T111141', 'batch_20251002T111238', 'batch_20251002T111335', 'batch_20251002T111433',
    'batch_20251002T111530', 'batch_20251002T111628', 'batch_20251002T111726', 'batch_20251002T111823',
    'batch_20251002T111921', 'batch_20251002T112017', 'batch_20251002T112114', 'batch_20251002T112210',
    'batch_20251002T112308', 'batch_20251002T112405', 'batch_20251002T112501', 'batch_20251002T112557',
    'batch_20251002T112652', 'batch_20251002T112744', 'batch_20251002T112836', 'batch_20251002T112929',
    'batch_20251002T113021', 'batch_20251002T113113', 'batch_20251002T113205', 'batch_20251002T113257',
    'batch_20251002T113349', 'batch_20251002T113441', 'batch_20251002T113533', 'batch_20251002T113626',
    'batch_20251002T113718', 'batch_20251002T113810', 'batch_20251002T113902', 'batch_20251002T113954',
    'batch_20251002T114046', 'batch_20251002T114138', 'batch_20251002T114230', 'batch_20251002T114322',
    'batch_20251002T114415', 'batch_20251002T114507', 'batch_20251002T114559', 'batch_20251002T114651',
    'batch_20251002T114743', 'batch_20251002T125401', 'batch_20251002T125515', 'batch_20251002T125617',
    'batch_20251002T125718', 'batch_20251002T125820', 'batch_20251002T125922', 'batch_20251002T130024',
    'batch_20251002T130126', 'batch_20251002T130228', 'batch_20251002T130330', 'batch_20251002T130431',
    'batch_20251002T130533', 'batch_20251002T130637', 'batch_20251002T130741', 'batch_20251002T130844',
    'batch_20251002T130949', 'batch_20251002T131048', 'batch_20251002T131152', 'batch_20251002T131257',
    'batch_20251002T131359', 'batch_20251002T131502', 'batch_20251002T131605', 'batch_20251002T131709',
    'batch_20251002T131812', 'batch_20251002T131914', 'batch_20251002T132017', 'batch_20251002T132121',
    'batch_20251002T132224', 'batch_20251002T132327', 'batch_20251002T132430', 'batch_20251002T132535',
    'batch_20251002T132640', 'batch_20251002T132745', 'batch_20251002T132849', 'batch_20251002T132952',
    'batch_20251002T134417', 'batch_20251002T134509', 'batch_20251002T135139', 'batch_20251002T135234',
    'batch_20251002T135329', 'batch_20251002T135424', 'batch_20251002T135520', 'batch_20251002T135615',
    'batch_20251002T135707', 'batch_20251002T135759', 'batch_20251002T135851', 'batch_20251002T135943',
    'batch_20251002T140035', 'batch_20251002T140127', 'batch_20251002T140219', 'batch_20251002T140311',
    'batch_20251002T140403', 'batch_20251002T140455', 'batch_20251002T140547', 'batch_20251002T140639',
    'batch_20251002T140731', 'batch_20251002T140823', 'batch_20251002T140915', 'batch_20251002T141007',
    'batch_20251002T141059', 'batch_20251002T141151', 'batch_20251002T141243', 'batch_20251002T141335',
    'batch_20251002T141427', 'batch_20251002T141519', 'batch_20251002T141611', 'batch_20251002T141704',
    'batch_20251002T141756', 'batch_20251002T141848', 'batch_20251002T141940',

    # Batches numerados principales
    'batch_9', 'batch_10', 'batch_11', 'batch_12', 'batch_13', 'batch_14', 'batch_15',
    'batch_16', 'batch_17', 'batch_18', 'batch_19', 'batch_20', 'batch_21', 'batch_22',
    'batch_23', 'batch_24', 'batch_25', 'batch_26', 'batch_27', 'batch_28', 'batch_29',
    'batch_30', 'batch_31', 'batch_32', 'batch_33', 'batch_34', 'batch_35', 'batch_36',
    'batch_37', 'batch_38', 'batch_39', 'batch_40', 'batch_41', 'batch_42', 'batch_43',
    'batch_44', 'batch_45', 'batch_46', 'batch_47', 'batch_48', 'batch_49', 'batch_50',
    'batch_51', 'batch_52', 'batch_53', 'batch_54', 'batch_55', 'batch_56', 'batch_57',
    'batch_58', 'batch_59', 'batch_60', 'batch_61', 'batch_62', 'batch_63', 'batch_64', 'batch_65',
    'batch_66', 'batch_67', 'batch_68', 'batch_69', 'batch_70', 'batch_71', 'batch_72', 'batch_73',
    'batch_74', 'batch_75', 'batch_76', 'batch_77', 'batch_78', 'batch_79', 'batch_80', 'batch_81',
    'batch_82', 'batch_83', 'batch_84', 'batch_85', 'batch_86', 'batch_87', 'batch_88', 'batch_89',
    'batch_90', 'batch_91', 'batch_92', 'batch_93', 'batch_94', 'batch_95', 'batch_96', 'batch_97',
    'batch_98', 'batch_99', 'batch_100', 'batch_101', 'batch_102', 'batch_103', 'batch_104', 'batch_105',
    'batch_106', 'batch_107', 'batch_108', 'batch_109', 'batch_110', 'batch_111', 'batch_112', 'batch_113',
    'batch_114', 'batch_115', 'batch_116', 'batch_117', 'batch_118', 'batch_119', 'batch_120', 'batch_121',
    'batch_122', 'batch_123', 'batch_124', 'batch_125', 'batch_126', 'batch_127', 'batch_128', 'batch_129',
    'batch_130', 'batch_131', 'batch_132', 'batch_133', 'batch_134', 'batch_135', 'batch_136', 'batch_137',
    'batch_138', 'batch_139', 'batch_140', 'batch_141', 'batch_142', 'batch_143', 'batch_144', 'batch_145',
    'batch_146', 'batch_147', 'batch_148', 'batch_149', 'batch_150', 'batch_151', 'batch_152', 'batch_153',
    'batch_154', 'batch_155', 'batch_156', 'batch_157', 'batch_158', 'batch_159', 'batch_160', 'batch_161',
    'batch_162', 'batch_163', 'batch_164', 'batch_165', 'batch_166', 'batch_167', 'batch_168', 'batch_169',
    'batch_170', 'batch_171', 'batch_172', 'batch_173', 'batch_174', 'batch_175', 'batch_176', 'batch_177',
    'batch_178', 'batch_179', 'batch_180', 'batch_181', 'batch_182', 'batch_183', 'batch_184', 'batch_185',
    'batch_186', 'batch_187', 'batch_188', 'batch_189', 'batch_190', 'batch_191', 'batch_192', 'batch_193',
    'batch_194', 'batch_195', 'batch_196', 'batch_197', 'batch_198', 'batch_199', 'batch_200',

    # Más batches numerados
    'batch_361', 'batch_362', 'batch_363', 'batch_364', 'batch_365', 'batch_366', 'batch_367', 'batch_368', 'batch_369',
    'batch_370', 'batch_371', 'batch_372', 'batch_373', 'batch_374', 'batch_375', 'batch_376', 'batch_377',
    'batch_378', 'batch_379', 'batch_380', 'batch_381', 'batch_382', 'batch_383', 'batch_384', 'batch_385',
    'batch_386', 'batch_387', 'batch_388', 'batch_389', 'batch_390', 'batch_391', 'batch_393', 'batch_394',
    'batch_395', 'batch_396', 'batch_397', 'batch_398', 'batch_399', 'batch_400', 'batch_401', 'batch_402',
    'batch_403', 'batch_404', 'batch_405', 'batch_406', 'batch_407', 'batch_408', 'batch_409', 'batch_410',
    'batch_411', 'batch_412', 'batch_413', 'batch_414', 'batch_415', 'batch_416', 'batch_417', 'batch_418',
    'batch_419', 'batch_420', 'batch_421', 'batch_422', 'batch_423', 'batch_424', 'batch_425', 'batch_426',
    'batch_427', 'batch_428', 'batch_429', 'batch_430', 'batch_431', 'batch_432', 'batch_433', 'batch_434',
    'batch_435', 'batch_436', 'batch_437', 'batch_438', 'batch_439', 'batch_440', 'batch_441', 'batch_442',
    'batch_443', 'batch_444', 'batch_445', 'batch_446', 'batch_447', 'batch_448', 'batch_449', 'batch_450',
    'batch_451', 'batch_452', 'batch_453', 'batch_454', 'batch_455', 'batch_456', 'batch_457', 'batch_458',
    'batch_459', 'batch_460', 'batch_461', 'batch_462', 'batch_463', 'batch_464', 'batch_465', 'batch_466',
    'batch_467', 'batch_468', 'batch_469', 'batch_470', 'batch_471', 'batch_472', 'batch_473', 'batch_474',
    'batch_475', 'batch_476', 'batch_477', 'batch_478', 'batch_479', 'batch_480', 'batch_481', 'batch_482',
    'batch_483', 'batch_484', 'batch_485', 'batch_486', 'batch_487', 'batch_488',

    # Batches 2400+
    'batch_2402', 'batch_2403', 'batch_2409', 'batch_2410', 'batch_2411', 'batch_2412', 'batch_2413', 'batch_2414',
    'batch_2416', 'batch_2417', 'batch_2421', 'batch_2422', 'batch_2423', 'batch_2424', 'batch_2426', 'batch_2427',
    'batch_2430', 'batch_2432', 'batch_2433', 'batch_2434', 'batch_2435', 'batch_2436', 'batch_2437', 'batch_2438',
    'batch_2439', 'batch_2440', 'batch_2441', 'batch_2442', 'batch_2443', 'batch_2444', 'batch_2445', 'batch_2446',
    'batch_2447', 'batch_2448', 'batch_2449', 'batch_2450', 'batch_2451', 'batch_2452', 'batch_2453', 'batch_2454',
    'batch_2455', 'batch_2456', 'batch_2457', 'batch_2458', 'batch_2459', 'batch_2460', 'batch_2461', 'batch_2462',
    'batch_2463', 'batch_2464', 'batch_2465', 'batch_2466', 'batch_2467', 'batch_2468', 'batch_2469', 'batch_2470',
    'batch_2471', 'batch_2472', 'batch_2473', 'batch_2474', 'batch_2475', 'batch_2477', 'batch_2478', 'batch_2479',
    'batch_2480', 'batch_2481', 'batch_2482', 'batch_2484', 'batch_2485', 'batch_2486', 'batch_2487', 'batch_2488',
    'batch_2490', 'batch_2491', 'batch_2493', 'batch_2494', 'batch_2496', 'batch_2497', 'batch_2498',

    # Batches 2500+
    'batch_2520', 'batch_2521', 'batch_2522', 'batch_2523', 'batch_2524', 'batch_2525', 'batch_2526', 'batch_2527',
    'batch_2528', 'batch_2529', 'batch_2530', 'batch_2531', 'batch_2532', 'batch_2533', 'batch_2534', 'batch_2535',
    'batch_2536', 'batch_2537', 'batch_2538', 'batch_2539', 'batch_2540', 'batch_2541', 'batch_2542', 'batch_2543',
    'batch_2544', 'batch_2545', 'batch_2546', 'batch_2547', 'batch_2548', 'batch_2549', 'batch_2550', 'batch_2551',
    'batch_2552', 'batch_2553', 'batch_2554', 'batch_2555', 'batch_2556', 'batch_2557', 'batch_2558', 'batch_2559',
    'batch_2560', 'batch_2561', 'batch_2562', 'batch_2563', 'batch_2564'
]

def recuperar_batches_completos():
    """Recupera todos los batches hardcodeados en la base de datos."""

    print("🔄 Iniciando recuperación de batches completos...")
    print(f"📊 Total de batches a recuperar: {len(ALL_HARDCODED_BATCHES)}")

    # Conectar a la base de datos
    db = get_db(raise_on_fail=False)
    if not db:
        print("❌ Error: No se pudo conectar a MongoDB")
        return

    batches_col = db["batches"]

    # Obtener batches existentes
    existing_batches = set()
    for batch in batches_col.find({}, {"id": 1, "_id": 0}):
        existing_batches.add(batch["id"])

    print(f"📊 Batches ya existentes en DB: {len(existing_batches)}")

    # Filtrar batches que no existen
    batches_to_create = []
    for batch_id in ALL_HARDCODED_BATCHES:
        if batch_id not in existing_batches:
            batches_to_create.append(batch_id)

    print(f"📝 Batches a crear: {len(batches_to_create)}")

    if not batches_to_create:
        print("✅ Todos los batches ya existen en la base de datos")
        return

    # Configuración del directorio de datos
    DATA_DIRECTORY = os.environ.get("DATA_DIRECTORY", "/home/faservin/american_project")

    # Crear batches
    created_count = 0
    for batch_id in batches_to_create:
        # Determinar assignee basado en el patrón (como en el código original)
        if batch_id in ['batch_9', 'batch_11', 'batch_13', 'batch_14', 'batch_28', 'batch_34', 'batch_36', 'batch_38', 'batch_39', 'batch_41', 'batch_42']:
            assignee = "Flor"
        elif batch_id in ['batch_15', 'batch_16', 'batch_17', 'batch_21', 'batch_46', 'batch_47', 'batch_48', 'batch_49', 'batch_50', 'batch_51', 'batch_52']:
            assignee = "Ignacio"
        else:
            assignee = ""  # Sin asignar por defecto

        # Crear batch con estructura completa
        batch = {
            "id": batch_id,
            "assignee": assignee,
            "folder": f"{DATA_DIRECTORY}/{batch_id}",
            "tasks": ["segmentar", "subir_mascaras", "revisar"],
            "metadata": {
                "assigned_at": datetime.now().strftime("%Y-%m-%d") if assignee else "",
                "due_date": "",
                "priority": "media",
                "reviewed_at": None
            },
            "status": "NS",  # No segmentado por defecto
            "mongo_uploaded": False,  # No subido por defecto
            "comments": f"Batch recuperado del sistema hardcodeado - {assignee or 'Sin asignar'}"
        }

        try:
            batches_col.insert_one(batch)
            created_count += 1
            if created_count % 50 == 0:
                print(f"✅ Creados {created_count} batches...")
        except Exception as e:
            print(f"❌ Error creando batch {batch_id}: {e}")

    print(f"🎉 ¡Recuperación completada! Se crearon {created_count} batches")
    print(f"📊 Total de batches en DB ahora: {batches_col.count_documents({})}")

if __name__ == "__main__":
    recuperar_batches_completos()