CREATE TABLE IF NOT EXISTS processed_results (
    video_id VARCHAR(50) PRIMARY KEY,
    raw_text TEXT,
    human_label VARCHAR(20),
    text_verdict VARCHAR(20),
    text_score FLOAT,
    video_verdict VARCHAR(20),
    video_score FLOAT,
    avg_score FLOAT,
    threshold FLOAT,
    final_decision VARCHAR(50),
    -- Cột này phải có sẵn để Dashboard không bị lỗi
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);

-- 2. Bảng Logs hệ thống (MỚI - Thêm vào đây)
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    dag_id VARCHAR(50),
    task_name VARCHAR(50),
    log_level VARCHAR(10), -- INFO, ERROR, WARNING
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);