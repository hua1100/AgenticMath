# Multi-stage build for AgenticMath
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install comprehensive system dependencies for PaddleOCR and OpenCV
# 包含所有 PaddleOCR 和 OpenCV 需要的系統依賴
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    cmake \
    git \
    wget \
    # PostgreSQL client
    libpq-dev \
    # OpenMP for parallel processing
    libgomp1 \
    # GLib and GTK dependencies
    libglib2.0-0 \
    libgthread-2.0-0 \
    # X11 and rendering libraries
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxrender1 \
    libfontconfig1 \
    libice6 \
    # OpenGL libraries
    libgl1-mesa-glx \
    libgl1-mesa-dev \
    libglu1-mesa \
    libglu1-mesa-dev \
    # Image processing libraries
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    # Video codec libraries (for OpenCV)
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    # Additional OpenCV dependencies
    libatlas-base-dev \
    gfortran \
    # Font libraries (for text rendering in OCR)
    fonts-liberation \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install runtime dependencies (matching builder dependencies)
# 安裝運行時依賴（與構建階段匹配）
RUN apt-get update && apt-get install -y \
    # PostgreSQL client library
    libpq5 \
    # OpenMP for parallel processing
    libgomp1 \
    # GLib and GTK
    libglib2.0-0 \
    libgthread-2.0-0 \
    # X11 and rendering
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libice6 \
    # OpenGL
    libgl1-mesa-glx \
    libglu1-mesa \
    # Image formats
    libjpeg62-turbo \
    libpng16-16 \
    libtiff5 \
    libwebp6 \
    # Video codecs
    libavcodec58 \
    libavformat58 \
    libswscale5 \
    # BLAS for numerical operations
    libatlas3-base \
    # CJK fonts for OCR
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 agenticmath && \
    mkdir -p /app /app/logs /app/uploads && \
    chown -R agenticmath:agenticmath /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=agenticmath:agenticmath . .

# Switch to app user
USER agenticmath

# Create necessary directories
RUN mkdir -p logs uploads

# Expose port (if running API)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.storage.database import engine; engine.connect()" || exit 1

# Default command (CLI)
ENTRYPOINT ["python", "-m", "src.cli.main"]

# For API mode, use:
# CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
