# Docker Troubleshooting Guide for OOTDiffusion

This guide helps resolve common Docker build and deployment issues.

## 🚨 Common Issues and Solutions

### 1. CUDA Base Image Not Found

**Error**: `nvidia/cuda:11.8-devel-ubuntu22.04: not found`

**Cause**: The specific CUDA base image tag is not available or has been deprecated.

**Solutions**:

#### Option A: Use Updated CUDA Image
```bash
# The main Dockerfile now uses CUDA 12.1
docker-compose up -d
```

#### Option B: Use Alternative Dockerfile (CPU-only)
```bash
# Use the alternative Dockerfile for CPU-only deployment
docker-compose -f docker-compose.alternative.yml up -d
```

#### Option C: Use Different CUDA Version
Edit `Dockerfile` and change the base image:
```dockerfile
# Try these alternatives:
FROM nvidia/cuda:12.0-devel-ubuntu22.04 as base
# OR
FROM nvidia/cuda:11.7-devel-ubuntu22.04 as base
# OR
FROM nvidia/cuda:12.2-devel-ubuntu20.04 as base
```

### 2. GPU Support Issues

**Error**: `nvidia-container-cli: requirement error`

**Cause**: NVIDIA Container Toolkit not installed or configured.

**Solutions**:

#### Install NVIDIA Container Toolkit
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

#### Test GPU Access
```bash
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
```

### 3. Build Context Issues

**Error**: `failed to solve: failed to compute cache key`

**Cause**: Large build context or missing files.

**Solutions**:

#### Check .dockerignore
Ensure `.dockerignore` excludes unnecessary files:
```dockerignore
checkpoints/
*.ckpt
*.safetensors
.git/
*.log
temp/
```

#### Clean Build
```bash
docker system prune -f
docker-compose build --no-cache
```

### 4. Memory Issues

**Error**: `out of memory` or `killed`

**Cause**: Insufficient system memory or Docker memory limits.

**Solutions**:

#### Increase Docker Memory
- Docker Desktop: Settings → Resources → Memory
- Docker Engine: Edit `/etc/docker/daemon.json`

#### Use CPU-only Mode
```bash
# Use alternative compose file
docker-compose -f docker-compose.alternative.yml up -d
```

### 5. Network Issues

**Error**: `failed to fetch` or `network error`

**Cause**: Network connectivity issues during build.

**Solutions**:

#### Check Internet Connection
```bash
ping google.com
ping huggingface.co
```

#### Use Proxy (if behind corporate firewall)
```bash
# Set proxy in Dockerfile
ENV HTTP_PROXY=http://proxy.company.com:8080
ENV HTTPS_PROXY=http://proxy.company.com:8080
```

### 6. Permission Issues

**Error**: `permission denied` or `access denied`

**Cause**: File permission issues.

**Solutions**:

#### Fix Permissions
```bash
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

#### Run as Non-root
```bash
# Add to docker-compose.yml
user: "1000:1000"
```

## 🔧 Build Strategies

### 1. Multi-Stage Build Optimization

The Dockerfile uses multi-stage builds for efficiency:

```dockerfile
# Base stage - common dependencies
FROM nvidia/cuda:12.1-devel-ubuntu22.04 as base

# Development stage - includes dev tools
FROM base as development

# Production stage - minimal, secure
FROM base as production
```

### 2. Layer Caching

Optimize build times by ordering Dockerfile commands:

```dockerfile
# Copy requirements first (changes less frequently)
COPY requirements-prod.txt .
RUN pip install -r requirements-prod.txt

# Copy application code last (changes more frequently)
COPY . .
```

### 3. Build Arguments

Use build arguments for flexibility:

```dockerfile
ARG CUDA_VERSION=12.1
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu22.04 as base
```

## 🚀 Deployment Options

### 1. GPU-Enabled Deployment
```bash
# Requires NVIDIA Container Toolkit
docker-compose up -d
```

### 2. CPU-Only Deployment
```bash
# No GPU required
docker-compose -f docker-compose.alternative.yml up -d
```

### 3. Development Mode
```bash
# Includes dev tools and hot reload
docker-compose --profile dev up -d
```

### 4. Production with Caching
```bash
# Includes Redis for caching
docker-compose --profile cache up -d
```

## 📊 Monitoring and Debugging

### 1. Check Container Status
```bash
docker-compose ps
docker-compose logs -f
```

### 2. Health Checks
```bash
# Check API health
curl http://localhost:7865/health

# Check container health
docker inspect ootd-api | grep Health -A 10
```

### 3. Resource Usage
```bash
# Monitor resource usage
docker stats

# Check disk usage
docker system df
```

### 4. Debug Container
```bash
# Enter running container
docker-compose exec ootd-api bash

# Run new container for debugging
docker run -it --rm ootd-api bash
```

## 🛠️ Advanced Troubleshooting

### 1. Build Debugging
```bash
# Build with verbose output
docker-compose build --progress=plain --no-cache

# Build specific stage
docker build --target development -t ootd-dev .
```

### 2. Runtime Debugging
```bash
# Check container logs
docker-compose logs ootd-api

# Check specific service
docker-compose logs -f ootd-api | grep ERROR
```

### 3. Network Debugging
```bash
# Test network connectivity
docker-compose exec ootd-api ping google.com
docker-compose exec ootd-api curl -I https://huggingface.co
```

### 4. Volume Debugging
```bash
# Check volume mounts
docker-compose exec ootd-api ls -la /app/checkpoints
docker-compose exec ootd-api df -h
```

## 📋 Quick Fixes

### If Docker Build Fails:
1. Try alternative Dockerfile: `docker-compose -f docker-compose.alternative.yml up -d`
2. Clean build: `docker system prune -f && docker-compose build --no-cache`
3. Check base image: Update CUDA version in Dockerfile

### If Container Won't Start:
1. Check logs: `docker-compose logs ootd-api`
2. Check health: `curl http://localhost:7865/health`
3. Check resources: `docker stats`

### If Models Won't Download:
1. Check network: `docker-compose exec ootd-api ping huggingface.co`
2. Check git-lfs: `docker-compose exec ootd-api git lfs version`
3. Manual download: `docker-compose exec ootd-api python scripts/auto_download_models.py`

### If API Not Responding:
1. Check port: `netstat -tlnp | grep 7865`
2. Check firewall: `sudo ufw status`
3. Check container: `docker-compose ps`

## 🆘 Getting Help

### 1. Check Logs
```bash
docker-compose logs -f ootd-api
```

### 2. Run Health Check
```bash
python scripts/verify_setup.py
```

### 3. Test Manually
```bash
python quick_start.py
```

### 4. Check Documentation
- `README-HOSTING.md` - Hosting guide
- `HOSTING_CHECKLIST.md` - Complete checklist
- `test_interface.html` - Test interface

---

**Your OOTDiffusion Docker setup should now work smoothly! 🐳✨**


