#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Triggering Airflow DAG: 1_TIKTOK_ETL_COLLECTOR"
docker exec -i airflow-webserver airflow dags trigger 1_TIKTOK_ETL_COLLECTOR

echo "Done. Check logs in dashboard or run: docker exec -i postgres psql -U user -d tiktok_safety_db -c \"SELECT * FROM system_logs WHERE dag_id='1_TIKTOK_ETL_COLLECTOR' ORDER BY created_at DESC LIMIT 20;\""
