#!/bin/bash
# File: streaming/link_host.sh

# Lấy địa chỉ IP (ưu tiên Tailscale, nếu không có lấy IP nội bộ)
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || hostname -I | awk '{print $1}' || echo "127.0.0.1")
LOCAL_IP=$(hostname -I | awk '{print $1}')
USER_NAME=$(whoami)

# Màu sắc cho đẹp
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n================================================================"
echo -e "      ${GREEN}🛡️  HỆ THỐNG TIKTOK SAFETY - TRUNG TÂM ĐIỀU KHIỂN${NC}"
echo -e "================================================================"

echo -e "\n${YELLOW}🌐 TRUY CẬP TRỰC TIẾP (Qua Tailscale - Không cần SSH Tunnel):${NC}"
echo -e "   📍 Dashboard (Streamlit):    ${CYAN}http://${TAILSCALE_IP}:8501${NC}"
echo -e "   📍 Airflow UI (Quản lý):     ${CYAN}http://${TAILSCALE_IP}:8080${NC} (admin/admin)"
echo -e "   📍 MinIO Console:            ${CYAN}http://${TAILSCALE_IP}:9001${NC} (admin/password123)"
echo -e "   📍 Spark Master UI:          ${CYAN}http://${TAILSCALE_IP}:9090${NC}"

echo -e "\n${YELLOW}🌐 TRUY CẬP QUA LOCAL NETWORK:${NC}"
echo -e "   📍 Dashboard (Streamlit):    ${CYAN}http://${LOCAL_IP}:8501${NC}"
echo -e "   📍 Airflow UI (Quản lý):     ${CYAN}http://${LOCAL_IP}:8080${NC}"

echo -e "\n----------------------------------------------------------------"
echo -e "${YELLOW}🔒 LỆNH SSH TUNNEL (Nếu cần - chạy trên máy cá nhân):${NC}"
echo -e "${CYAN}ssh -L 8501:localhost:8501 -L 8080:localhost:8080 -L 9090:localhost:9090 -L 9001:localhost:9001 -L 9000:localhost:9000 ${USER_NAME}@${TAILSCALE_IP}${NC}"
echo -e "----------------------------------------------------------------"

echo -e "\n${YELLOW}🛠️  CLI QUICK CHECK (Copy lệnh bên dưới chạy trên Server này):${NC}"

echo -e "\n1️⃣  ${GREEN}Kiểm tra Database (Xem 5 kết quả mới nhất):${NC}"
echo -e "${CYAN}docker exec -it postgres psql -U user -d tiktok_safety_db -c \"SELECT video_id, left(raw_text, 30) as content, final_decision, avg_score, processed_at FROM processed_results ORDER BY processed_at DESC LIMIT 5;\"${NC}"

echo -e "\n2️⃣  ${GREEN}Kiểm tra Kafka (Xem tin nhắn real-time):${NC}"
echo -e "${CYAN}docker exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic tiktok_raw_data --from-beginning --max-messages 1${NC}"

echo -e "\n3️⃣  ${GREEN}Kiểm tra MinIO (Xem file trong folder):${NC}"
echo -e "${CYAN}docker run --rm --network tiktok-network minio/mc sh -c 'mc alias set local http://minio:9000 \$MINIO_ROOT_USER \$MINIO_ROOT_PASSWORD >/dev/null 2>&1 && mc ls -r local/\$MINIO_BUCKET_VIDEOS/ | tail -n 5'${NC}"

echo -e "\n----------------------------------------------------------------"
echo -e "${RED}🧨 DANGER ZONE: RESET TOÀN BỘ HỆ THỐNG (Xóa sạch dữ liệu để chạy lại)${NC}"
echo -e "Copy và chạy khối lệnh dưới đây:"
echo -e "${RED}"
echo "docker exec -it postgres psql -U user -d tiktok_safety_db -c \"TRUNCATE TABLE processed_results;\""
echo "rm -f streaming/tiktok-pipeline/data_viet/crawl/tiktok_links_viet.csv"
echo "# MinIO reset (không phụ thuộc mc trong container minio):"
echo "docker run --rm --network tiktok-network minio/mc sh -c 'mc alias set local http://minio:9000 \$MINIO_ROOT_USER \$MINIO_ROOT_PASSWORD && mc rm -r --force local/\$MINIO_BUCKET_VIDEOS/ && mc rm -r --force local/\$MINIO_BUCKET_AUDIOS/ && mc mb local/\$MINIO_BUCKET_VIDEOS --ignore-existing && mc mb local/\$MINIO_BUCKET_AUDIOS --ignore-existing && mc anonymous set download local/\$MINIO_BUCKET_VIDEOS && mc anonymous set download local/\$MINIO_BUCKET_AUDIOS'"
echo "docker restart airflow-scheduler spark-processor dashboard"
echo -e "${NC}"
echo -e "----------------------------------------------------------------"

echo -e "\n${YELLOW}🔍 TRẠNG THÁI CONTAINER:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "airflow|spark|dashboard|minio|kafka|postgres"
echo -e "================================================================\n"