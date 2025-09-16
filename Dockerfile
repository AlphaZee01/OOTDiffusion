# Multi-stage Dockerfile for OOTDiffusion production deployment
FROM python:3.10-slim as base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV OOTD_DEVICE=cpu

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-prod.txt .

# Install PyTorch first from their CPU wheels
RUN pip install --no-cache-dir \
    torch==2.0.1+cpu torchvision==0.15.2+cpu \
    --index-url https://download.pytorch.org/whl/cpu

# Then install everything else from PyPI
RUN pip install --no-cache-dir -r requirements-prod.txt --extra-index-url https://pypi.org/simple

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p checkpoints temp outputs/logs

# Set permissions
RUN chmod +x scripts/*.sh 2>/dev/null || true

# Install git-lfs for model downloading
RUN apt-get update && apt-get install -y git-lfs && \
    rm -rf /var/lib/apt/lists/*

# Initialize git-lfs after installation
RUN git lfs install --system

# Create entrypoint script for automatic model download
RUN echo '#!/bin/bash\n\
echo "🎭 OOTDiffusion - Starting with automatic model download..."\n\
\n\
# Check if models exist\n\
if [ ! -d "checkpoints/ootd" ] || [ ! "$(ls -A checkpoints/ootd)" ]; then\n\
    echo "📥 Models not found, starting download..."\n\
    python scripts/auto_download_models.py\n\
    echo "✅ Model download completed"\n\
else\n\
    echo "✅ Models already available"\n\
fi\n\
\n\
# Start the application\n\
echo "🚀 Starting OOTDiffusion API..."\n\
exec "$@"' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 7865

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:7865/health || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "api/app.py"]

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Set environment for development
ENV OOTD_ENVIRONMENT=development
ENV OOTD_DEBUG=true

# Production stage
FROM base as production

# Set environment for production
ENV OOTD_ENVIRONMENT=production
ENV OOTD_DEBUG=false

# Create non-root user for security
RUN groupadd -r ootd && useradd -r -g ootd ootd
RUN chown -R ootd:ootd /app
USER ootd

# Use production command
CMD ["python", "api/app.py"]
