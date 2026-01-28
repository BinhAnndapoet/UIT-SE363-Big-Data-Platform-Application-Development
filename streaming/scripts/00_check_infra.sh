#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== docker compose services =="
docker compose ps

echo
echo "== health quick checks =="
for c in postgres kafka minio airflow-webserver spark-processor; do
  if docker inspect -f '{{.State.Health.Status}}' "$c" >/dev/null 2>&1; then
    echo "- $c: $(docker inspect -f '{{.State.Health.Status}}' "$c")"
  else
    echo "- $c: (no healthcheck) state=$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo 'missing')"
  fi
done

echo
echo "== postgres connectivity =="
docker exec -i postgres pg_isready -U "${POSTGRES_USER:-user}" -d "${POSTGRES_DB:-tiktok_safety_db}" >/dev/null

echo "OK"
