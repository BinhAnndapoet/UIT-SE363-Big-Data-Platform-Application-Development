#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

url="${1:-}"
label="${2:-unknown}"

if [[ -z "$url" ]]; then
  echo "Usage: $0 <tiktok_video_url> [safe|harmful|unknown]" >&2
  exit 2
fi

echo "Ingesting 1 video via Airflow container..."
echo "- url:   $url"
echo "- label: $label"

docker exec -i airflow-webserver python /opt/project/streaming/tiktok-pipeline/ingestion/ingestion_main_worker.py \
  --url "$url" \
  --label "$label"
