#!/bin/bash
set -euo pipefail

# ============================================================================
# Script: Setup MongoDB SSH Tunnel with AutoSSH (Auto-reconnect)
# Descripción: Túnel SSH persistente con reconexión automática
# Autor: Claude Code Assistant
# ============================================================================

# CONFIGURACIÓN
REMOTE_USER="${REMOTE_USER:-faservin}"
REMOTE_HOST="${REMOTE_HOST:-192.168.1.93}"
REMOTE_PORT="${REMOTE_PORT:-22}"
LOCAL_PORT="${LOCAL_PORT:-27018}"
REMOTE_MONGO_PORT="27017"
AUTOSSH_POLL=60  # Intervalo de monitoreo en segundos
AUTOSSH_GATETIME=0  # No esperar antes de primer intento

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# Verificar si autossh está instalado
check_autossh() {
    if ! command -v autossh &> /dev/null; then
        log_error "autossh no está instalado"
        log_info "Instalar con: sudo apt install autossh"
        exit 1
    fi
}

# Cerrar procesos autossh existentes
kill_existing_autossh() {
    local pids=$(ps aux | grep "[a]utossh.*${LOCAL_PORT}" | awk '{print $2}')

    if [ -n "$pids" ]; then
        log_warning "Cerrando procesos autossh existentes: $pids"
        echo "$pids" | xargs -r kill -9
        sleep 2
    fi
}

# Crear túnel con autossh
create_persistent_tunnel() {
    log_info "Creando túnel persistente con autossh..."

    export AUTOSSH_POLL=${AUTOSSH_POLL}
    export AUTOSSH_GATETIME=${AUTOSSH_GATETIME}
    export AUTOSSH_LOGFILE="/tmp/autossh_mongo_${LOCAL_PORT}.log"

    autossh -M 0 -f -N \
        -L "${LOCAL_PORT}:127.0.0.1:${REMOTE_MONGO_PORT}" \
        -p "${REMOTE_PORT}" \
        "${REMOTE_USER}@${REMOTE_HOST}" \
        -o "ServerAliveInterval=30" \
        -o "ServerAliveCountMax=3" \
        -o "ExitOnForwardFailure=yes" \
        -o "StrictHostKeyChecking=no"

    sleep 3

    if pgrep -f "autossh.*${LOCAL_PORT}" > /dev/null; then
        log_success "Túnel persistente creado en puerto ${LOCAL_PORT}"
        log_info "Log: ${AUTOSSH_LOGFILE}"
        return 0
    else
        log_error "No se pudo crear el túnel"
        return 1
    fi
}

# Probar conexión
test_connection() {
    log_info "Probando conexión a MongoDB..."

    if mongosh "mongodb://127.0.0.1:${LOCAL_PORT}" --quiet --eval "db.adminCommand('ping')" &>/dev/null; then
        log_success "MongoDB remoto accesible"

        local mask_count=$(mongosh "mongodb://127.0.0.1:${LOCAL_PORT}/QUALITY_IEMSA" --quiet --eval "db['training_metrics.masks.files'].countDocuments()" 2>/dev/null || echo "0")
        log_success "Máscaras encontradas: ${mask_count}"
        return 0
    else
        log_error "MongoDB no responde"
        return 1
    fi
}

# Mostrar estado
show_status() {
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════╗
║     TÚNEL PERSISTENTE MONGODB ACTIVO (CON AUTOSSH)        ║
╚════════════════════════════════════════════════════════════╝${NC}

${BLUE}🔄 AutoSSH - Reconexión Automática:${NC}
   - El túnel se reconectará automáticamente si se cae
   - Intervalo de monitoreo: ${AUTOSSH_POLL}s
   - Log: /tmp/autossh_mongo_${LOCAL_PORT}.log

${BLUE}📡 Conexión:${NC}
   localhost:${LOCAL_PORT} → ${REMOTE_HOST}:${REMOTE_MONGO_PORT}

${BLUE}🔍 Ver Estado:${NC}
   ps aux | grep autossh | grep ${LOCAL_PORT}
   tail -f /tmp/autossh_mongo_${LOCAL_PORT}.log

${BLUE}🛑 Detener Túnel:${NC}
   pkill -f "autossh.*${LOCAL_PORT}"

${BLUE}📊 Usar en Compass:${NC}
   mongodb://127.0.0.1:${LOCAL_PORT}

EOF
}

# Main
main() {
    echo -e "${BLUE}╔═══════════════════════════════════════════════════╗"
    echo -e "║  TÚNEL PERSISTENTE SSH (AUTOSSH) PARA MONGODB    ║"
    echo -e "╚═══════════════════════════════════════════════════╝${NC}\n"

    check_autossh
    kill_existing_autossh

    if ! create_persistent_tunnel; then
        log_error "No se pudo crear el túnel"
        exit 1
    fi

    if ! test_connection; then
        log_warning "Túnel creado pero MongoDB no responde (puede tardar unos segundos)"
    fi

    show_status
    log_success "Túnel persistente configurado"
}

main "$@"
