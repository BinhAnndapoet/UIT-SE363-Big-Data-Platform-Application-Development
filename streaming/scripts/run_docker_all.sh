#!/bin/bash
# ============================================================================
# DOCKER RUN ALL - Complete System Startup
# ============================================================================
# Purpose: Start the entire TikTok Safety streaming pipeline
#
# Usage:
#   ./scripts/run_docker_all.sh [mode]
#
# Modes:
#   up        - Start all containers (default)
#   down      - Stop all containers
#   restart   - Restart all containers
#   status    - Show container status
#   logs      - Follow logs from all containers
#   clean     - Stop containers and remove volumes
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMING_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment
if [ -f "$STREAMING_DIR/.env" ]; then
    set -a
    source "$STREAMING_DIR/.env"
    set +a
fi

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  TikTok Safety Platform - Docker Orchestration                         ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

start_all() {
    print_header
    echo -e "${GREEN}🚀 Starting all containers...${NC}"
    echo ""
    
    cd "$STREAMING_DIR"
    
    # Build and start
    docker compose up -d --build
    
    # Wait for services
    echo ""
    echo -e "${YELLOW}⏳ Waiting for services to be ready (15s)...${NC}"
    sleep 15
    
    # Show status
    show_status
    
    # Show access info
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ACCESS INFORMATION${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  📊 Dashboard (Streamlit):    http://localhost:8501"
    echo "  🌐 Airflow Web UI:           http://localhost:8080"
    echo "  📦 MinIO Console:            http://localhost:9001"
    echo "  🔬 MLflow UI:                http://localhost:5000"
    echo "  📈 Spark Master UI:          http://localhost:8081"
    echo ""
    echo -e "${YELLOW}NEXT STEPS:${NC}"
    echo "  1. Go to Airflow: http://localhost:8080 (user: admin, pass: admin)"
    echo "  2. Trigger DAG: 1_TIKTOK_ETL_COLLECTOR → Wait until Success"
    echo "  3. Trigger DAG: 2_TIKTOK_STREAMING_PIPELINE"
    echo "  4. View results on Dashboard: http://localhost:8501"
    echo ""
}

stop_all() {
    print_header
    echo -e "${YELLOW}🛑 Stopping all containers...${NC}"
    cd "$STREAMING_DIR"
    docker compose down
    echo -e "${GREEN}✅ All containers stopped.${NC}"
}

restart_all() {
    print_header
    echo -e "${YELLOW}🔄 Restarting all containers...${NC}"
    cd "$STREAMING_DIR"
    docker compose down
    docker compose up -d --build
    echo -e "${GREEN}✅ All containers restarted.${NC}"
}

show_status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  CONTAINER STATUS${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    cd "$STREAMING_DIR"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

follow_logs() {
    print_header
    echo -e "${YELLOW}📋 Following logs from all containers (Ctrl+C to exit)...${NC}"
    echo ""
    cd "$STREAMING_DIR"
    docker compose logs -f
}

clean_all() {
    print_header
    echo -e "${RED}⚠️  WARNING: This will stop all containers and remove volumes!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" == "yes" ]; then
        cd "$STREAMING_DIR"
        docker compose down -v --remove-orphans
        echo -e "${GREEN}✅ All containers and volumes removed.${NC}"
    else
        echo "Cancelled."
    fi
}

show_help() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  up        Start all containers (default)"
    echo "  down      Stop all containers"
    echo "  restart   Restart all containers"
    echo "  status    Show container status"
    echo "  logs      Follow logs from all containers"
    echo "  clean     Stop and remove volumes (WARNING!)"
    echo ""
    echo "Services:"
    echo "  - Zookeeper, Kafka (messaging)"
    echo "  - MinIO (object storage)"
    echo "  - PostgreSQL (database)"
    echo "  - Spark Master/Worker/Processor"
    echo "  - Airflow (orchestration)"
    echo "  - MLflow (model registry)"
    echo "  - Dashboard (Streamlit)"
}

# Main
case "${1:-up}" in
    up)
        start_all
        ;;
    down)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        show_status
        ;;
    logs)
        follow_logs
        ;;
    clean)
        clean_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown mode: $1${NC}"
        show_help
        exit 1
        ;;
esac
