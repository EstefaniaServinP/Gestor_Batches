#!/bin/bash
set -euo pipefail

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     HEALTH CHECK - Dashboard de Segmentación     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════╝${NC}\n"

# Variables
LOCAL_PORT="27017"
REMOTE_PORT="27019"
LOCAL_URI="mongodb://127.0.0.1:${LOCAL_PORT}"
REMOTE_URI="mongodb://127.0.0.1:${REMOTE_PORT}/QUALITY_IEMSA?directConnection=true"

check_passed=0
check_failed=0

# Función para checks
run_check() {
    local name=$1
    local command=$2

    echo -n -e "${YELLOW}[CHECK]${NC} ${name}... "

    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((check_passed++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((check_failed++))
        return 1
    fi
}

echo -e "${BLUE}═══ 1. VERIFICACIÓN DE TÚNEL SSH ═══${NC}\n"

run_check "Túnel SSH activo en puerto ${REMOTE_PORT}" "ss -ltnp | grep -q ${REMOTE_PORT}"

echo -e "\n${BLUE}═══ 2. MONGODB LOCAL (${LOCAL_PORT}) ═══${NC}\n"

run_check "Ping a MongoDB local" "mongosh '${LOCAL_URI}' --quiet --eval 'db.adminCommand(\"ping\")'"

if mongosh "${LOCAL_URI}" --quiet --eval 'db.getMongo().getDBNames()' &>/dev/null; then
    echo -e "${YELLOW}[INFO]${NC} Bases de datos locales:"
    mongosh "${LOCAL_URI}" --quiet --eval 'db.getMongo().getDBNames().forEach(db => print("  - " + db))'
    echo ""
fi

run_check "Base de datos 'segmentacion_db' existe" "mongosh '${LOCAL_URI}/segmentacion_db' --quiet --eval 'db.getName()' | grep -q segmentacion_db"

run_check "Base de datos 'Quality_dashboard' existe" "mongosh '${LOCAL_URI}/Quality_dashboard' --quiet --eval 'db.getName()' | grep -q Quality_dashboard"

run_check "Colección 'batches' existe" "mongosh '${LOCAL_URI}/segmentacion_db' --quiet --eval 'db.getCollectionNames()' | grep -q batches"

run_check "Colección 'segmentadores' existe" "mongosh '${LOCAL_URI}/Quality_dashboard' --quiet --eval 'db.getCollectionNames()' | grep -q segmentadores"

echo -e "\n${BLUE}═══ 3. MONGODB REMOTO (${REMOTE_PORT} vía túnel) ═══${NC}\n"

run_check "Ping a MongoDB remoto" "mongosh '${REMOTE_URI}' --quiet --eval 'db.adminCommand(\"ping\")'"

if mongosh "${REMOTE_URI}" --quiet --eval 'db.getMongo().getDBNames()' &>/dev/null; then
    echo -e "${YELLOW}[INFO]${NC} Bases de datos remotas:"
    mongosh "${REMOTE_URI}" --quiet --eval 'db.getMongo().getDBNames().forEach(db => print("  - " + db))'
    echo ""
fi

run_check "Base de datos 'QUALITY_IEMSA' existe" "mongosh '${REMOTE_URI}' --quiet --eval 'db.getName()' | grep -q QUALITY_IEMSA"

run_check "Colección 'training_metrics.masks.files' existe" "mongosh '${REMOTE_URI}' --quiet --eval 'db.getCollectionNames()' | grep -q 'training_metrics.masks.files'"

if mongosh "${REMOTE_URI}" --quiet --eval "db['training_metrics.masks.files'].countDocuments()" &>/dev/null; then
    MASK_COUNT=$(mongosh "${REMOTE_URI}" --quiet --eval "db['training_metrics.masks.files'].countDocuments()")
    echo -e "${YELLOW}[INFO]${NC} Máscaras encontradas: ${MASK_COUNT}"
fi

echo -e "\n${BLUE}═══ 4. SAMPLE QUERIES ═══${NC}\n"

echo -e "${YELLOW}[QUERY]${NC} Listar primeros 3 batches:"
mongosh "${LOCAL_URI}/segmentacion_db" --quiet --eval "db.batches.find({}, {id: 1, assignee: 1, status: 1, _id: 0}).limit(3).forEach(printjson)" 2>/dev/null || echo -e "${RED}  Error ejecutando query${NC}"

echo -e "\n${YELLOW}[QUERY]${NC} Listar primeras 3 máscaras:"
mongosh "${REMOTE_URI}" --quiet --eval "db['training_metrics.masks.files'].find({}, {filename: 1, uploadDate: 1, _id: 0}).limit(3).forEach(printjson)" 2>/dev/null || echo -e "${RED}  Error ejecutando query${NC}"

echo -e "\n${BLUE}═══ 5. RESUMEN ═══${NC}\n"

echo -e "${GREEN}✓ Checks pasados:${NC} ${check_passed}"
echo -e "${RED}✗ Checks fallidos:${NC} ${check_failed}"

if [ $check_failed -eq 0 ]; then
    echo -e "\n${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ TODOS LOS CHECKS PASARON - LISTO PARA  ║${NC}"
    echo -e "${GREEN}║            INICIAR LA APLICACIÓN           ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}\n"
    exit 0
else
    echo -e "\n${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ HAY PROBLEMAS - REVISA LOS ERRORES     ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}\n"

    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. MongoDB local: ${BLUE}sudo systemctl status mongod${NC}"
    echo -e "  2. Túnel SSH: ${BLUE}ssh -f -N -L 27019:127.0.0.1:27017 carlos@192.168.1.93${NC}"
    echo -e "  3. Ver túnel: ${BLUE}ss -ltnp | grep 27019${NC}"
    echo -e ""
    exit 1
fi
