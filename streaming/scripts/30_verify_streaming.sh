#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== recent Spark AI logs (system_logs) =="
docker exec -i postgres psql -U "${POSTGRES_USER:-user}" -d "${POSTGRES_DB:-tiktok_safety_db}" -c \
  "SELECT created_at, log_level, left(message,120) AS message FROM system_logs WHERE dag_id='2_TIKTOK_STREAMING_PIPELINE' ORDER BY created_at DESC LIMIT 20;" | cat

echo
echo "== recent processed_results =="
docker exec -i postgres psql -U "${POSTGRES_USER:-user}" -d "${POSTGRES_DB:-tiktok_safety_db}" -c \
  "SELECT video_id, human_label, final_decision, avg_score, processed_at FROM processed_results ORDER BY processed_at DESC LIMIT 15;" | cat

echo
echo "== spark-processor container tail =="
docker logs --tail 80 spark-processor | cat
