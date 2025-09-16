# OOTDiffusion - Hosting Guide

This guide explains how to host and deploy OOTDiffusion with automatic model downloading.

## 🚀 One-Command Setup

### For New Users (Recommended)
```bash
python quick_start.py
```

This single command will:
- ✅ Install all dependencies
- ✅ Download model checkpoints automatically
- ✅ Start the production API
- ✅ Provide access to test interface

## 🐳 Docker Deployment (Production)

### Quick Docker Start
```bash
# Clone the repository
git clone https://github.com/AlphaZee01/OOTDiffusion.git
cd OOTDiffusion

# Start with automatic model download
docker-compose up -d

# Check status
docker-compose logs -f
```

### What Happens Automatically:
1. **Model Download**: Models download automatically on first run
2. **API Startup**: Production API starts on port 7865
3. **Health Checks**: Automatic health monitoring
4. **Persistent Storage**: Models are cached for future runs

## 🌐 Access Points

Once running, your OOTDiffusion instance will be available at:

- **API Endpoint**: `http://localhost:7865`
- **API Documentation**: `http://localhost:7865/docs`
- **Health Check**: `http://localhost:7865/health`
- **Test Interface**: Open `test_interface.html` in your browser

## 📋 Hosting Options

### 1. Local Development
```bash
python quick_start.py
```

### 2. Docker (Recommended for Production)
```bash
docker-compose up -d
```

### 3. Cloud Deployment

#### AWS EC2
```bash
# Launch EC2 instance with GPU
# Install Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker $USER

# Clone and run
git clone https://github.com/your-username/OOTDiffusion.git
cd OOTDiffusion
docker-compose up -d
```

#### Google Cloud Platform
```bash
# Create VM with GPU
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone and run
git clone https://github.com/your-username/OOTDiffusion.git
cd OOTDiffusion
docker-compose up -d
```

#### Azure
```bash
# Create VM with GPU
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone and run
git clone https://github.com/your-username/OOTDiffusion.git
cd OOTDiffusion
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file to customize settings:

```bash
# API Configuration
OOTD_HOST=0.0.0.0
OOTD_PORT=7865
OOTD_WORKERS=1

# Model Configuration
OOTD_DEVICE=cuda:0
OOTD_TORCH_DTYPE=float16

# Logging
OOTD_LOG_LEVEL=INFO
OOTD_DEBUG=false
```

### Custom Model Paths
```bash
# If you want to use custom model locations
export OOTD_MODEL_PATH=/path/to/custom/models
```

## 📊 Monitoring

### Health Check
```bash
curl http://localhost:7865/health
```

### Docker Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f ootd-api
```

### Resource Usage
```bash
# Check container resources
docker stats

# Check disk usage
docker system df
```

## 🔄 Updates

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Update Models
```bash
# Models are automatically updated when you pull the latest code
# Or manually update:
python scripts/auto_download_models.py --force
```

## 🛠️ Troubleshooting

### Common Issues

#### Models Not Downloading
```bash
# Check internet connection
ping huggingface.co

# Check git-lfs
git lfs version

# Manual download
python scripts/download_models.py
```

#### Out of Memory
```bash
# Reduce workers
export OOTD_WORKERS=1

# Use CPU offload
# Edit config.py: enable_cpu_offload=True
```

#### Port Already in Use
```bash
# Change port
export OOTD_PORT=7866

# Or kill process using port
sudo lsof -ti:7865 | xargs kill -9
```

### Docker Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs ootd-api

# Rebuild container
docker-compose build --no-cache
docker-compose up -d
```

#### Permission Issues
```bash
# Fix permissions
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
```

## 📈 Scaling

### Horizontal Scaling
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  ootd-api:
    deploy:
      replicas: 3
    environment:
      - OOTD_WORKERS=1
```

### Load Balancing
```nginx
# nginx.conf
upstream ootd_backend {
    server ootd-api-1:7865;
    server ootd-api-2:7865;
    server ootd-api-3:7865;
}

server {
    listen 80;
    location / {
        proxy_pass http://ootd_backend;
    }
}
```

## 🔒 Security

### Basic Security
```bash
# Set up firewall
sudo ufw allow 7865
sudo ufw enable

# Use HTTPS (recommended for production)
# Set up SSL certificates
```

### API Security
```python
# Add authentication to api/app.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_token(token: str = Depends(security)):
    if token.credentials != "your-api-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return token
```

## 📝 API Usage

### Basic Usage
```bash
# Process images
curl -X POST "http://localhost:7865/process" \
  -F "model_file=@model.jpg" \
  -F "cloth_file=@cloth.jpg" \
  -F "model_type=hd" \
  -F "samples=1"
```

### Python Client
```python
import requests

# Process images
files = {
    'model_file': open('model.jpg', 'rb'),
    'cloth_file': open('cloth.jpg', 'rb')
}
data = {
    'model_type': 'hd',
    'category': 0,
    'samples': 1
}

response = requests.post('http://localhost:7865/process', files=files, data=data)
result = response.json()
print(result)
```

## 🎯 Performance Tips

### GPU Optimization
```bash
# Use multiple GPUs
export CUDA_VISIBLE_DEVICES=0,1

# Optimize memory usage
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Caching
```bash
# Enable Redis caching
docker-compose --profile cache up -d
```

## 📞 Support

### Getting Help
1. **Check logs**: `docker-compose logs -f`
2. **Test health**: `curl http://localhost:7865/health`
3. **Check models**: `ls -la checkpoints/`
4. **Run diagnostics**: `python scripts/auto_download_models.py`

### Common Commands
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

---

**Your OOTDiffusion instance is now ready for hosting! 🎉**

The automatic model download ensures that anyone can clone your repository and get started immediately without manual setup.
