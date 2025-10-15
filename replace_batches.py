#!/usr/bin/env python3
"""
Script para reemplazar todos los batches en la base de datos
"""

from db import get_db
from datetime import datetime

# Lista de nuevos batches
new_batches = [
    "batch_000001F", "batch_000002F", "batch_000003F", "batch_000004F", "batch_000005F",
    "batch_000006F", "batch_000007F", "batch_000008F", "batch_000009F", "batch_000010F",
    "batch_000011F", "batch_000012F", "batch_000013F", "batch_000014F", "batch_000015F",
    "batch_000016F", "batch_000017F", "batch_000018F", "batch_000019F", "batch_000020F",
    "batch_000021F", "batch_000022F", "batch_000023F", "batch_000024F", "batch_000027F",
    "batch_000028F", "batch_000029F", "batch_000030F", "batch_000031F", "batch_000032F",
    "batch_000033F", "batch_000034F", "batch_000035F", "batch_000036F", "batch_000037F",
    "batch_000038F", "batch_000039F", "batch_000040F", "batch_000041F", "batch_000042F",
    "batch_000043F", "batch_000044F", "batch_000045F", "batch_000046F", "batch_000047F",
    "batch_000048F", "batch_000049F", "batch_000050F", "batch_000051F", "batch_000052F",
    "batch_000053F", "batch_000054F", "batch_000055F", "batch_000056F", "batch_000057F",
    "batch_000058F", "batch_000059F", "batch_000060F", "batch_000061F", "batch_000062F",
    "batch_000063F", "batch_000064F", "batch_000065F", "batch_000066F", "batch_000067F",
    "batch_000068F", "batch_000069F", "batch_000070F", "batch_000071F", "batch_000072F",
    "batch_000073F", "batch_000074F", "batch_000075F", "batch_000076F", "batch_000077F",
    "batch_000078F", "batch_000079F", "batch_000080F", "batch_000081F", "batch_000082F",
    "batch_000083F", "batch_000084F", "batch_000085F", "batch_000086F", "batch_000087F",
    "batch_000088F", "batch_000089F", "batch_000090F", "batch_000091F", "batch_000092F",
    "batch_000093F", "batch_000094F", "batch_000095F", "batch_000096F", "batch_000097F",
    "batch_000098F", "batch_000099F", "batch_000100F", "batch_000101F", "batch_000102F",
    "batch_000103F", "batch_000104F", "batch_000105F", "batch_000106F", "batch_000107F",
    "batch_000108F", "batch_000109F", "batch_000110F", "batch_000111F", "batch_000112F",
    "batch_000129F", "batch_000130F", "batch_000131F", "batch_000132F", "batch_000133F",
    "batch_000134F", "batch_000135F", "batch_000136F", "batch_000137F", "batch_000138F",
    "batch_000139F", "batch_000140F", "batch_000141F", "batch_000142F", "batch_000143F",
    "batch_000144F", "batch_000145F", "batch_000146F", "batch_000147F", "batch_000148F",
    "batch_000149F", "batch_000150F", "batch_000151F", "batch_000152F", "batch_000153F",
    "batch_000154F", "batch_000155F", "batch_000156F", "batch_000157F", "batch_000158F",
    "batch_000159F", "batch_000160F", "batch_000161F", "batch_000162F", "batch_000163F",
    "batch_000164F", "batch_000165F", "batch_000166F", "batch_000167F", "batch_000168F",
    "batch_000169F", "batch_000170F", "batch_000171F", "batch_000172F", "batch_000173F",
    "batch_000174F", "batch_000175F", "batch_000176F", "batch_000177F", "batch_000178F",
    "batch_000179F", "batch_000180F", "batch_000181F", "batch_000182F", "batch_000183F",
    "batch_000184F", "batch_000185F", "batch_000186F", "batch_000187F", "batch_000188F",
    "batch_000189F", "batch_000190F", "batch_000191F", "batch_000192F", "batch_000193F",
    "batch_000194F", "batch_000195F", "batch_000196F", "batch_000197F", "batch_000198F",
    "batch_000199F", "batch_000200F", "batch_000201F", "batch_000202F", "batch_000203F",
    "batch_000204F", "batch_000205F", "batch_000206F", "batch_000207F", "batch_000208F",
    "batch_000209F", "batch_000210F", "batch_000211F", "batch_000212F", "batch_000213F",
    "batch_000214F", "batch_000215F", "batch_000216F", "batch_000217F", "batch_000218F",
    "batch_000219F", "batch_000220F", "batch_000221F", "batch_000222F", "batch_000223F",
    "batch_000224F", "batch_000225F", "batch_000226F", "batch_000227F", "batch_000228F",
    "batch_000229F", "batch_000230F", "batch_000231F", "batch_000232F", "batch_000233F",
    "batch_000234F", "batch_000235F", "batch_000236F", "batch_000237F", "batch_000238F",
    "batch_000239F", "batch_000240F", "batch_000241F", "batch_000242F", "batch_000243F",
    "batch_000244F", "batch_000245F", "batch_000246F", "batch_000247F", "batch_000248F",
    "batch_000249F", "batch_000250F", "batch_000251F", "batch_000252F", "batch_000253F",
    "batch_000254F", "batch_000255F", "batch_000256F", "batch_000257F", "batch_000258F",
    "batch_000259F", "batch_000260F", "batch_000261F", "batch_000262F", "batch_000263F",
    "batch_000264F", "batch_000265F", "batch_000266F", "batch_000267F", "batch_000268F",
    "batch_000269F", "batch_000270F", "batch_000271F", "batch_000272F", "batch_000273F",
    "batch_000274F", "batch_000275F", "batch_000276F", "batch_000277F", "batch_000278F",
    "batch_000279F", "batch_000280F", "batch_000281F", "batch_000282F", "batch_000283F",
    "batch_000284F",
    "batch_T000002", "batch_T000003", "batch_T000004", "batch_T000005", "batch_T000006",
    "batch_T000007", "batch_T000008", "batch_T000009", "batch_T000010", "batch_T000011",
    "batch_T000012", "batch_T000013", "batch_T000014", "batch_T000015", "batch_T000016",
    "batch_T000017", "batch_T000018", "batch_T000019", "batch_T000020", "batch_T000021",
    "batch_T000022", "batch_T000023", "batch_T000024", "batch_T000025", "batch_T000026",
    "batch_T000027", "batch_T000028", "batch_T000029", "batch_T000030", "batch_T000031",
    "batch_T000032", "batch_T000035", "batch_T000036", "batch_T000037", "batch_T000038",
    "batch_T000039", "batch_T000040", "batch_T000041", "batch_T000042", "batch_T000043",
    "batch_T000044", "batch_T000045", "batch_T000046", "batch_T000047", "batch_T000048",
    "batch_T000049", "batch_T000050", "batch_T000051", "batch_T000052", "batch_T000053",
    "batch_T000054", "batch_T000055", "batch_T000056", "batch_T000057", "batch_T000058",
    "batch_T000061", "batch_T000062", "batch_T000063", "batch_T000064", "batch_T000065",
    "batch_T000066", "batch_T000067", "batch_T000068", "batch_T000069", "batch_T000070",
    "batch_T000071", "batch_T000072", "batch_T000073", "batch_T000074", "batch_T000075",
    "batch_T000076", "batch_T000077", "batch_T000078", "batch_T000079", "batch_T000080",
    "batch_T000081", "batch_T000082", "batch_T000083", "batch_T000084", "batch_T000085",
    "batch_T000086", "batch_T000087", "batch_T000088", "batch_T000089", "batch_T000090",
    "batch_T000091", "batch_T000092", "batch_T000093", "batch_T000094", "batch_T000095",
    "batch_T000096", "batch_T000097", "batch_T000098", "batch_T000099", "batch_T000100",
    "batch_T000101", "batch_T000102", "batch_T000103", "batch_T000104", "batch_T000105",
    "batch_T000106", "batch_T000107", "batch_T000108", "batch_T000109", "batch_T000110",
    "batch_T000111", "batch_T000112", "batch_T000113", "batch_T000114", "batch_T000115",
    "batch_T000116", "batch_T000117", "batch_T000118", "batch_T000119", "batch_T000120",
    "batch_T000121", "batch_T000122", "batch_T000123", "batch_T000124", "batch_T000125",
    "batch_T000126", "batch_T000127", "batch_T000128", "batch_T000129", "batch_T000130",
    "batch_T000131", "batch_T000132", "batch_T000133", "batch_T000134", "batch_T000135",
    "batch_T000136", "batch_T000137", "batch_T000138", "batch_T000139", "batch_T000140",
    "batch_T000141", "batch_T000142", "batch_T000143", "batch_T000144", "batch_T000145",
    "batch_T000146", "batch_T000147", "batch_T000148", "batch_T000149", "batch_T000150",
    "batch_T000151", "batch_T000152", "batch_T000153", "batch_T000154", "batch_T000155",
    "batch_T000156", "batch_T000157", "batch_T000158", "batch_T000159", "batch_T000160",
    "batch_T000161", "batch_T000162", "batch_T000163", "batch_T000164", "batch_T000165",
    "batch_T000166", "batch_T000167", "batch_T000168"
]

def main():
    print("=" * 70)
    print("🔄 REEMPLAZO DE BATCHES EN LA BASE DE DATOS")
    print("=" * 70)

    # Conectar a la base de datos
    print("\n📡 Conectando a MongoDB...")
    db = get_db(raise_on_fail=True)
    batches_col = db["batches"]

    # Contar batches existentes
    existing_count = batches_col.count_documents({})
    print(f"📊 Batches actuales en la base de datos: {existing_count}")

    # Preguntar confirmación
    if existing_count > 0:
        print(f"\n⚠️  ADVERTENCIA: Se eliminarán {existing_count} batches existentes")
        confirm = input("¿Continuar? (si/no): ").strip().lower()
        if confirm not in ['si', 's', 'yes', 'y']:
            print("❌ Operación cancelada")
            return

    # Eliminar todos los batches existentes
    print(f"\n🗑️  Eliminando {existing_count} batches existentes...")
    result = batches_col.delete_many({})
    print(f"✅ {result.deleted_count} batches eliminados")

    # Crear nuevos batches
    print(f"\n📝 Creando {len(new_batches)} nuevos batches...")

    batches_to_insert = []
    for batch_id in new_batches:
        batch = {
            "id": batch_id,
            "assignee": None,  # Sin asignar inicialmente
            "folder": f"/home/faservin/american_project/{batch_id}",
            "tasks": ["segmentar", "subir_mascaras", "revisar"],
            "metadata": {
                "assigned_at": None,
                "due_date": "",
                "priority": "media",
                "reviewed_at": None
            },
            "status": "NS",  # No Segmentado
            "mongo_uploaded": False,
            "comments": "",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        batches_to_insert.append(batch)

    # Insertar en bulk
    if batches_to_insert:
        result = batches_col.insert_many(batches_to_insert)
        print(f"✅ {len(result.inserted_ids)} batches creados exitosamente")

    # Verificar resultado final
    final_count = batches_col.count_documents({})
    print(f"\n📊 Total de batches en la base de datos: {final_count}")

    # Mostrar algunos ejemplos
    print("\n📋 Primeros 10 batches creados:")
    for batch in batches_col.find({}, {"id": 1, "status": 1, "assignee": 1, "_id": 0}).limit(10):
        print(f"   - {batch['id']} | Status: {batch['status']} | Assignee: {batch.get('assignee', 'Sin asignar')}")

    print("\n" + "=" * 70)
    print("✅ PROCESO COMPLETADO")
    print("=" * 70)
    print(f"\nResumen:")
    print(f"  • Batches eliminados: {existing_count}")
    print(f"  • Batches creados: {len(new_batches)}")
    print(f"  • Total final: {final_count}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
