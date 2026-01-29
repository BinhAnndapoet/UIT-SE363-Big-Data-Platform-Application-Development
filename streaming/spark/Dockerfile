# =============================================================================
# Spark Processor Dockerfile - Optimized for Layer Caching
# Build context: streaming/spark/
# =============================================================================
FROM apache/spark:3.5.0

USER root

# -----------------------------------------------------------------------------
# LAYER 1: System dependencies (rarely changes)
# -----------------------------------------------------------------------------
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# LAYER 2: Python version constraints (rarely changes)
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir "typing-extensions<4.6.0" "zipp<3.16.0"

# -----------------------------------------------------------------------------
# LAYER 3: PyTorch CPU-only (LARGE ~2GB - very stable)
# Using CPU-only index to avoid CUDA bloat
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    torch==2.1.2 \
    --index-url https://download.pytorch.org/whl/cpu

# -----------------------------------------------------------------------------
# LAYER 4: AI/ML libraries (medium size - stable)
# NOTE: transformers 4.40+ required for HuggingFace Hub model tokenizer compatibility
# transformers 4.40.0 is the last version supporting Python 3.8
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir \
    transformers==4.40.0 \
    tokenizers==0.19.1 \
    huggingface_hub==0.22.0 \
    sentencepiece \
    protobuf==3.20.0 \
    scipy==1.10.1 \
    av \
    pillow

# decord installed separately (build issues with some versions)
RUN pip install --no-cache-dir decord || echo "decord install failed, will use av fallback"
# -----------------------------------------------------------------------------
# LAYER 5: Utility libraries (small - may change)
# COPY requirements.txt first for layer caching
# -----------------------------------------------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# -----------------------------------------------------------------------------
# LAYER 6: Create working directories with proper permissions
# -----------------------------------------------------------------------------
RUN mkdir -p /tmp/.ivy && chmod -R 777 /tmp/.ivy && \
    mkdir -p /opt/spark/work && chmod -R 777 /opt/spark/work && \
    mkdir -p /app/processing && chmod -R 777 /app/processing

# -----------------------------------------------------------------------------
# LAYER 7: Copy application code (changes frequently - LAST)
# -----------------------------------------------------------------------------
COPY spark_processor.py /app/processing/

# Switch back to spark user for security
USER spark

WORKDIR /app
