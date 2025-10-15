#!/bin/bash
set -euo pipefail

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    VERIFICACIÓN DE SERVIDOR MONGODB DE CARLOS    ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}\n"

# Datos de conexión
MONGO_USER="carlos"
MONGO_PASS="EnervDeepEye0930"
SERVER_IP="189.187.242.54"
LOCAL_PORT="27018"

# URI de conexión
MONGO_URI="mongodb://${MONGO_USER}:${MONGO_PASS}@localhost:${LOCAL_PORT}/?authSource=admin"

echo -e "${YELLOW}[1/6]${NC} Cerrando túneles SSH previos..."
pkill -f "L ${LOCAL_PORT}:localhost:27017" 2>/dev/null || true
sleep 2

echo -e "${YELLOW}[2/6]${NC} Abriendo túnel SSH a ${SERVER_IP}..."
ssh -f -N -L ${LOCAL_PORT}:localhost:27017 carlos@${SERVER_IP}
sleep 3

echo -e "${YELLOW}[3/6]${NC} Verificando túnel activo..."
if ss -ltnp | grep -q ${LOCAL_PORT}; then
    echo -e "${GREEN}✓${NC} Túnel activo en puerto ${LOCAL_PORT}"
else
    echo -e "${RED}✗${NC} Túnel no está activo"
    exit 1
fi

echo -e "${YELLOW}[4/6]${NC} Probando conexión a MongoDB..."
if mongosh "${MONGO_URI}" --quiet --eval "db.adminCommand('ping')" &>/dev/null; then
    echo -e "${GREEN}✓${NC} Conexión exitosa a MongoDB"
else
    echo -e "${RED}✗${NC} No se pudo conectar a MongoDB"
    echo -e "${RED}   Verifica usuario/password${NC}"
    exit 1
fi

echo -e "${YELLOW}[5/6]${NC} Listando bases de datos disponibles..."
echo -e "${BLUE}Bases de datos:${NC}"
mongosh "${MONGO_URI}" --quiet --eval "db.getMongo().getDBNames().forEach(db => print('  - ' + db))"

echo -e "\n${YELLOW}[6/6]${NC} Buscando máscaras..."

# Verificar en QUALITY_IEMSA
if mongosh "${MONGO_URI}/QUALITY_IEMSA" --quiet --eval "db.getCollectionNames()" 2>/dev/null | grep -q "training_metrics.masks.files"; then
    MASK_COUNT=$(mongosh "${MONGO_URI}/QUALITY_IEMSA" --quiet --eval "db['training_metrics.masks.files'].countDocuments()" 2>/dev/null)
    echo -e "${GREEN}✓${NC} QUALITY_IEMSA.training_metrics.masks.files → ${MASK_COUNT} máscaras"
fi

# Verificar en seg_lab
if mongosh "${MONGO_URI}/seg_lab" --quiet --eval "db.getCollectionNames()" 2>/dev/null | grep -q "masks"; then
    MASK_COUNT_SEG=$(mongosh "${MONGO_URI}/seg_lab" --quiet --eval "db['masks.files'].countDocuments()" 2>/dev/null || echo "0")
    echo -e "${GREEN}✓${NC} seg_lab.masks.files → ${MASK_COUNT_SEG} máscaras"
fi

# Buscar en todas las bases de datos
echo -e "\n${BLUE}Buscando colecciones 'masks' en todas las bases...${NC}"
mongosh "${MONGO_URI}" --quiet --eval "
db.getMongo().getDBNames().forEach(function(dbName) {
  var db = db.getMongo().getDB(dbName);
  var collections = db.getCollectionNames().filter(c => c.includes('mask'));
  if (collections.length > 0) {
    print('  📁 ' + dbName + ':');
    collections.forEach(c => {
      var count = db[c].countDocuments();
      print('     - ' + c + ' (' + count + ' documentos)');
    });
  }
});
"

echo -e "\n${GREEN}╔═════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         VERIFICACIÓN COMPLETADA             ║${NC}"
echo -e "${GREEN}╚═════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}🔌 Túnel activo en:${NC} localhost:${LOCAL_PORT}"
echo -e "${BLUE}🧪 Probar conexión:${NC}"
echo -e "   mongosh \"${MONGO_URI}\""
echo -e "\n${BLUE}🛑 Cerrar túnel:${NC}"
echo -e "   pkill -f \"L ${LOCAL_PORT}\""
