# AgenticMath Dockerfile
# Python 3.11 with PaddleOCR support

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PaddleOCR and OpenCV
RUN apt-get update && apt-get install -y \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    libgthread-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for PaddleOCR models
RUN mkdir -p /root/.paddleocr

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PADDLE_HOME=/root/.paddleocr

# Expose port if running API server
EXPOSE 8000

# Default command
CMD ["python", "-m", "pytest", "tests/"]
