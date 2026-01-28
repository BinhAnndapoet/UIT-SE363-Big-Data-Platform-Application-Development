#!/bin/bash
# ============================================================================
# Layer 3: DATABASE LAYER - Run Script
# ============================================================================
# Purpose: Test or manage the PostgreSQL database layer
# Components: PostgreSQL, System Logs, Video Predictions
#
# Usage:
#   ./scripts/run_database.sh [mode]
#
# Modes:
#   test      - Run unit tests for database layer
#   start     - Start PostgreSQL container
#   connect   - Connect to PostgreSQL via psql
#   logs      - View database logs
#   reset     - Reset database (WARNING: deletes all data!)
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMING_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment
if [ -f "$STREAMING_DIR/.env" ]; then
    set -a
    source "$STREAMING_DIR/.env"
    set +a
fi

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"
POSTGRES_DB="${POSTGRES_DB:-tiktok_safety_db}"

print_header() {
    echo ""
    echo -e "${GREEN}============================================================================${NC}"
    echo -e "${GREEN}  DATABASE LAYER - $1${NC}"
    echo -e "${GREEN}============================================================================${NC}"
}

run_tests() {
    print_header "UNIT TESTS"
    cd "$STREAMING_DIR"
    
    echo "Running database layer tests..."
    pytest tests/test_db_layer.py -v --tb=short
    
    echo -e "${GREEN}✅ Database tests completed!${NC}"
}

start_db() {
    print_header "START POSTGRESQL"
    cd "$STREAMING_DIR"
    
    echo "🐳 Starting PostgreSQL container..."
    docker compose up postgres -d
    
    echo ""
    echo "📋 Connection Info:"
    echo "   Host:     $POSTGRES_HOST"
    echo "   Port:     $POSTGRES_PORT"
    echo "   User:     $POSTGRES_USER"
    echo "   Database: $POSTGRES_DB"
}

connect_db() {
    print_header "CONNECT TO POSTGRESQL"
    
    echo "🔌 Connecting to PostgreSQL..."
    docker exec -it postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
}

view_logs() {
    print_header "VIEW LOGS"
    
    echo "📋 Recent system logs:"
    docker exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
        "SELECT timestamp, level, message FROM system_logs ORDER BY timestamp DESC LIMIT 20;"
}

reset_db() {
    print_header "RESET DATABASE"
    echo -e "${RED}⚠️  WARNING: This will delete ALL data in tables!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" == "yes" ]; then
        echo "🗑️  Resetting database tables..."
        docker exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
            "TRUNCATE TABLE video_predictions, system_logs CASCADE;"
        echo -e "${GREEN}✅ Database reset complete.${NC}"
    else
        echo "Cancelled."
    fi
}

show_help() {
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  test      Run unit tests for database layer"
    echo "  start     Start PostgreSQL container"
    echo "  connect   Connect to PostgreSQL via psql"
    echo "  logs      View recent system logs"
    echo "  reset     Reset database (WARNING: deletes data!)"
    echo ""
    echo "Tables:"
    echo "  video_predictions  - AI classification results"
    echo "  system_logs        - System logs from Spark processor"
}

# Main
case "${1:-test}" in
    test)
        run_tests
        ;;
    start)
        start_db
        ;;
    connect)
        connect_db
        ;;
    logs)
        view_logs
        ;;
    reset)
        reset_db
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
