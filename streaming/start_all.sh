#!/bin/bash
# File: streaming/start_all.sh

PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DATA_PATH="$PROJECT_ROOT/data"
CSV_FILE="$DATA_PATH/crawl/tiktok_links_viet.csv"
STATE_DIR="$PROJECT_ROOT/state"
CHROME_PROFILE_DIR="$STATE_DIR/chrome_profile" # runtime state

# Load environment variables (optional)
# Docker Compose cũng tự đọc `.env` trong cùng thư mục, nhưng script này cần đồng bộ credential.
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$PROJECT_ROOT/.env"
    set +a
fi

# Defaults (giữ nguyên hành vi cũ nếu .env thiếu biến)
POSTGRES_USER="${POSTGRES_USER:-user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"
POSTGRES_DB="${POSTGRES_DB:-tiktok_safety_db}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

# --- [MỚI] Auto-detect Tailscale IP cho MinIO public endpoint ---
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || hostname -I | awk '{print $1}' || echo "localhost")
export MINIO_PUBLIC_ENDPOINT="${MINIO_PUBLIC_ENDPOINT:-http://${TAILSCALE_IP}:9000}"
echo "📡 MinIO Public Endpoint: ${MINIO_PUBLIC_ENDPOINT}"

# Màu sắc
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔥 KHỞI ĐỘNG HỆ THỐNG TIKTOK SAFETY (FULL AUTO)...${NC}"

# 0. KIỂM TRA PORT CONFLICTS
echo -e "${YELLOW}🔍 Kiểm tra port conflicts...${NC}"
if [ -f "$PROJECT_ROOT/scripts/check_ports.sh" ]; then
    if ! "$PROJECT_ROOT/scripts/check_ports.sh"; then
        echo -e "${RED}❌ Port conflicts detected! Please resolve before continuing.${NC}"
        exit 1
    fi
fi

# 1. DỌN DẸP DỮ LIỆU CŨ
echo -e "${YELLOW}🧹 Đang dọn dẹp hệ thống cũ...${NC}"
docker compose down --remove-orphans

# Fix: Force remove container postgres nếu còn tồn tại (conflict từ lần chạy trước)
if docker ps -a --format '{{.Names}}' | grep -q "^postgres$"; then
    echo "   🗑️  Force removing orphaned container 'postgres'..."
    docker rm -f postgres 2>/dev/null || true
fi

# Xóa file CSV để Crawler quét lại từ đầu
if [ -f "$CSV_FILE" ]; then
    echo "   🗑️  Đã xóa file CSV cũ: $CSV_FILE"
    rm -f "$CSV_FILE"
fi

# 2. CẤP QUYỀN HẠN (Fix lỗi Permission Denied)
echo -e "${YELLOW}🔑 Đang cấu hình quyền hạn thư mục...${NC}"
mkdir -p "$STATE_DIR/airflow_logs"
mkdir -p "$STATE_DIR/spark_checkpoints"
mkdir -p "$DATA_PATH/crawl"
mkdir -p "$PROJECT_ROOT/ingestion/temp_downloads"
mkdir -p "$STATE_DIR/ivy2"

# --- [MỚI] TỰ ĐỘNG TẠO FOLDER CHROME PROFILE ---
if [ ! -d "$CHROME_PROFILE_DIR" ]; then
    echo "   📁 Tạo mới thư mục chrome_profile..."
    mkdir -p "$CHROME_PROFILE_DIR/Default" # Tạo luôn subfolder Default cho chắc
fi
# -----------------------------------------------

# Dùng Alpine để chmod nhanh gọn (Bao gồm cả chrome_profile)
docker run --rm -v "$PROJECT_ROOT:/workspace" alpine sh -c "
    chmod -R 777 /workspace/state/airflow_logs && \
    chmod -R 777 /workspace/state/spark_checkpoints && \
    chmod -R 777 /workspace/data && \
    chmod -R 777 /workspace/ingestion/temp_downloads && \
    chmod -R 777 /workspace/state/ivy2 && \
    chmod -R 777 /workspace/state/chrome_profile && \
    if [ -f /workspace/ingestion/cookies.txt ]; then 
        chmod 666 /workspace/ingestion/cookies.txt; 
    fi
"
echo "   ✅ Đã cấp quyền 777 cho chrome_profile, spark_checkpoints và các thư mục khác."

# 3. KHỞI ĐỘNG CONTAINER
echo -e "${GREEN}🚀 Đang build và khởi động Docker Compose...${NC}"
cd "$PROJECT_ROOT"
docker compose up -d --build

# 4. CHỜ DỊCH VỤ SẴN SÀNG & CẤU HÌNH TỰ ĐỘNG
echo -e "${YELLOW}⏳ Đang đợi các dịch vụ khởi động...${NC}"
echo "   - Đợi Infrastructure (10s)..."
sleep 10

# Đợi Airflow Webserver sẵn sàng (quan trọng cho DAG parsing)
echo "   - Đợi Airflow Webserver parse DAGs (60s)..."
TIMEOUT=60
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if timeout 3 curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        echo "   ✅ Airflow Webserver ready!"
        break
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo "      ... waiting ($ELAPSED/$TIMEOUT)s"
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo "   ⚠️  Airflow Webserver timeout - có thể cần thêm thời gian"
fi

# Đợi thêm 15s để Airflow Scheduler parse DAGs
echo "   - Đợi Airflow Scheduler parse DAGs (15s)..."
sleep 15

# --- Cấu hình Airflow ---
echo "🛠️  Cấu hình Airflow Connection..."
docker exec airflow-webserver airflow connections add 'postgres_pipeline' \
    --conn-type 'postgres' \
    --conn-host "${POSTGRES_HOST}" \
    --conn-login "${POSTGRES_USER}" \
    --conn-password "${POSTGRES_PASSWORD}" \
    --conn-schema "${POSTGRES_DB}" \
    --conn-port "${POSTGRES_PORT}" 2>/dev/null || echo "   ⚠️  Connection đã tồn tại."

# --- MinIO Init ---
# Bucket/Policy được tự động tạo bởi service `minio-init` (image minio/mc) trong docker-compose.yml.
# Điều này giúp tránh phụ thuộc vào việc container MinIO server có sẵn binary `mc`.

# 5. HIỂN THỊ THÔNG TIN TRUY CẬP
if [ -f "$PROJECT_ROOT/link_host.sh" ]; then
    chmod +x "$PROJECT_ROOT/link_host.sh"
    "$PROJECT_ROOT/link_host.sh"
else
    echo -e "${GREEN}✅ Hệ thống đã lên! Truy cập Dashboard: http://localhost:8501${NC}"
fi

echo -e "${YELLOW}👉 HƯỚNG DẪN TIẾP THEO:${NC}"
echo "1. Vào Airflow (http://localhost:8080)."
echo "2. Trigger DAG 1 (1_TIKTOK_ETL_COLLECTOR) -> Đợi nó chạy xong (Success)."
echo "3. Trigger DAG 2 (2_TIKTOK_STREAMING_PIPELINE)."