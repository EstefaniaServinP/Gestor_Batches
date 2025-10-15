#!/bin/bash
set -euo pipefail

# ============================================================================
# Script: Setup MongoDB SSH Tunnel
# Descripción: Establece túnel SSH al servidor remoto para acceder a QUALITY_IEMSA
# Autor: Claude Code Assistant
# Fecha: 2025-10-11
# ============================================================================

# CONFIGURACIÓN - Ajusta estos valores según tu entorno
REMOTE_USER="${REMOTE_USER:-faservin}"
REMOTE_HOST="${REMOTE_HOST:-192.168.1.93}"
REMOTE_PORT="${REMOTE_PORT:-22}"
LOCAL_PORT="${LOCAL_PORT:-27018}"
REMOTE_MONGO_PORT="27017"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# FUNCIONES
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Verificar si el puerto local está en uso
check_port_in_use() {
    local port=$1
    if ss -tuln | grep -q ":${port} "; then
        return 0  # Puerto en uso
    else
        return 1  # Puerto libre
    fi
}

# Cerrar túneles SSH existentes en el puerto
kill_existing_tunnels() {
    local port=$1
    log_info "Buscando túneles SSH en puerto ${port}..."

    # Buscar procesos SSH con el puerto en la línea de comando
    local pids=$(ps aux | grep "[s]sh.*${port}:127.0.0.1:${REMOTE_MONGO_PORT}" | awk '{print $2}')

    if [ -z "$pids" ]; then
        log_info "No hay túneles SSH activos en puerto ${port}"
        return 0
    fi

    log_warning "Cerrando túneles existentes: $pids"
    echo "$pids" | xargs -r kill -9
    sleep 2
    log_success "Túneles cerrados"
}

# Verificar conectividad SSH al servidor
test_ssh_connection() {
    log_info "Probando conexión SSH a ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}..."

    if ssh -o ConnectTimeout=5 -o BatchMode=yes -p "${REMOTE_PORT}" "${REMOTE_USER}@${REMOTE_HOST}" "exit" 2>/dev/null; then
        log_success "Conexión SSH exitosa"
        return 0
    else
        log_error "No se pudo conectar vía SSH"
        log_info "Intenta: ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"
        return 1
    fi
}

# Crear túnel SSH
create_tunnel() {
    local local_port=$1

    log_info "Creando túnel SSH: localhost:${local_port} → ${REMOTE_HOST}:${REMOTE_MONGO_PORT}"

    ssh -f -N -L "${local_port}:127.0.0.1:${REMOTE_MONGO_PORT}" \
        -p "${REMOTE_PORT}" \
        "${REMOTE_USER}@${REMOTE_HOST}" \
        -o ServerAliveInterval=60 \
        -o ServerAliveCountMax=3 \
        -o ExitOnForwardFailure=yes

    local ssh_pid=$!
    sleep 2

    if check_port_in_use "${local_port}"; then
        log_success "Túnel SSH creado exitosamente en puerto ${local_port}"
        return 0
    else
        log_error "Falló la creación del túnel"
        return 1
    fi
}

# Probar conexión a MongoDB remoto a través del túnel
test_mongo_connection() {
    local port=$1

    log_info "Probando conexión a MongoDB remoto en localhost:${port}..."

    if mongosh "mongodb://127.0.0.1:${port}" --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        log_success "MongoDB remoto accesible"

        # Verificar que existe QUALITY_IEMSA
        local has_db=$(mongosh "mongodb://127.0.0.1:${port}" --quiet --eval "db.getMongo().getDBNames().includes('QUALITY_IEMSA')" 2>/dev/null)

        if [ "$has_db" = "true" ]; then
            log_success "Base de datos QUALITY_IEMSA encontrada"

            # Contar máscaras
            local mask_count=$(mongosh "mongodb://127.0.0.1:${port}/QUALITY_IEMSA" --quiet --eval "db['training_metrics.masks.files'].countDocuments()" 2>/dev/null)
            log_success "Máscaras encontradas: ${mask_count}"
        else
            log_warning "QUALITY_IEMSA no encontrada en el servidor remoto"
        fi

        return 0
    else
        log_error "No se pudo conectar a MongoDB"
        return 1
    fi
}

# Mostrar información de uso
show_usage_info() {
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════════════╗
║           TÚNEL SSH A MONGODB CONFIGURADO EXITOSAMENTE        ║
╚════════════════════════════════════════════════════════════════╝${NC}

${BLUE}📡 Conexión Activa:${NC}
   Local:  localhost:${LOCAL_PORT}
   Remoto: ${REMOTE_HOST}:${REMOTE_MONGO_PORT}

${BLUE}🔧 Uso en Aplicación Flask:${NC}
   La aplicación ya está configurada para usar:
   - Puerto 27017: MongoDB local (segmentacion_db, Quality_dashboard)
   - Puerto 27018: MongoDB remoto (QUALITY_IEMSA - máscaras)

${BLUE}🧪 Probar Conexión:${NC}
   mongosh "mongodb://127.0.0.1:${LOCAL_PORT}/QUALITY_IEMSA"

${BLUE}📊 Ver Máscaras:${NC}
   mongosh "mongodb://127.0.0.1:${LOCAL_PORT}/QUALITY_IEMSA" --eval "db['training_metrics.masks.files'].find().limit(5)"

${BLUE}🔍 MongoDB Compass:${NC}
   URI: mongodb://127.0.0.1:${LOCAL_PORT}

${BLUE}🛑 Cerrar Túnel:${NC}
   ps aux | grep ssh | grep ${LOCAL_PORT} | awk '{print \$2}' | xargs kill

${BLUE}📝 Variables de Entorno (opcional):${NC}
   export TRAINING_MONGO_URI="mongodb://127.0.0.1:${LOCAL_PORT}"

EOF
}

# ============================================================================
# FLUJO PRINCIPAL
# ============================================================================

main() {
    echo -e "${BLUE}"
    cat << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║        CONFIGURACIÓN DE TÚNEL SSH PARA MONGODB REMOTO        ║
╔═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"

    log_info "Servidor: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}"
    log_info "Puerto local: ${LOCAL_PORT}"

    # 1. Verificar dependencias
    if ! command -v mongosh &> /dev/null; then
        log_error "mongosh no está instalado"
        exit 1
    fi

    # 2. Cerrar túneles existentes
    kill_existing_tunnels "${LOCAL_PORT}"

    # 3. Si el puerto sigue ocupado, intentar con fallback
    if check_port_in_use "${LOCAL_PORT}"; then
        log_warning "Puerto ${LOCAL_PORT} aún en uso, intentando con 27019..."
        LOCAL_PORT=27019

        if check_port_in_use "${LOCAL_PORT}"; then
            log_error "Puerto ${LOCAL_PORT} también en uso. Limpia manualmente:"
            log_error "  ss -tulpn | grep 2701[89]"
            exit 1
        fi
    fi

    # 4. Verificar conectividad SSH
    if ! test_ssh_connection; then
        log_error "Verifica que puedes conectarte: ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"
        exit 1
    fi

    # 5. Crear túnel
    if ! create_tunnel "${LOCAL_PORT}"; then
        log_error "No se pudo crear el túnel SSH"
        exit 1
    fi

    # 6. Probar MongoDB
    if ! test_mongo_connection "${LOCAL_PORT}"; then
        log_error "MongoDB no responde a través del túnel"
        exit 1
    fi

    # 7. Mostrar información de uso
    show_usage_info

    log_success "Túnel configurado y listo para usar"
}

# Ejecutar
main "$@"
