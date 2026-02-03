#!/bin/bash
# File: streaming/scripts/check_ports.sh
# Check if required ports are available before starting services

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PORTS=(8080 8501 5000 9000 9001 9090 9092 5432)
PORT_SERVICES=("Airflow" "Dashboard" "MLflow" "MinIO" "MinIO Console" "Spark" "Kafka" "PostgreSQL")

echo -e "${YELLOW}🔍 Checking port availability...${NC}"

CONFLICTS=0
for i in "${!PORTS[@]}"; do
    PORT=${PORTS[$i]}
    SERVICE=${PORT_SERVICES[$i]}
    
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
        PROCESS=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
        echo -e "  ${RED}❌ Port $PORT ($SERVICE) is in use by PID $PID ($PROCESS)${NC}"
        CONFLICTS=$((CONFLICTS + 1))
    else
        echo -e "  ${GREEN}✅ Port $PORT ($SERVICE) is available${NC}"
    fi
done

if [ $CONFLICTS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Found $CONFLICTS port conflicts!${NC}"
    echo -e "${YELLOW}Options:${NC}"
    echo "  1. Kill conflicting processes manually"
    echo "  2. Run: docker compose down (if old containers still running)"
    echo "  3. Reboot system to clear all"
    exit 1
else
    echo -e "\n${GREEN}✅ All ports are available!${NC}"
    exit 0
fi
