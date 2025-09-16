# Multi-stage Dockerfile for OOTDiffusion production deployment
FROM nvidia/cuda:11.8-devel-ubuntu22.04 as base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    python3.10-venv \
    git \
    wget \
    curl \
    build-essential \
    cmake \
    ninja-build \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Upgrade pip
RUN python -m pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY requirements-prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p checkpoints temp outputs/logs

# Set permissions
RUN chmod +x scripts/*.sh 2>/dev/null || true

# Install git-lfs for model downloading
RUN apt-get update && apt-get install -y git-lfs && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

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
