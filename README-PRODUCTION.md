# OOTDiffusion - Production Ready

[![Production Ready](https://img.shields.io/badge/Production-Ready-green.svg)](https://github.com/levihsu/OOTDiffusion)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-red.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org/)

A production-ready implementation of OOTDiffusion: Outfitting Fusion based Latent Diffusion for Controllable Virtual Try-on.

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose**
- **NVIDIA GPU** with CUDA support (recommended)
- **8GB+ RAM** (16GB+ recommended)
- **10GB+ free disk space** for models

### 1. Clone and Setup

```bash
git clone https://github.com/levihsu/OOTDiffusion.git
cd OOTDiffusion
```

### 2. Run Setup Script

**Linux/macOS:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Windows:**
```cmd
scripts\setup.bat
```

### 3. Download Model Checkpoints

Download the required model checkpoints:

```bash
# Create checkpoints directory
mkdir -p checkpoints

# Download OOTDiffusion models
cd checkpoints
git lfs install
git clone https://huggingface.co/levihsu/OOTDiffusion ootd
git clone https://huggingface.co/levihsu/OOTDiffusion humanparsing
git clone https://huggingface.co/levihsu/OOTDiffusion openpose
git clone https://huggingface.co/openai/clip-vit-large-patch14
cd ..
```

### 4. Deploy with Docker

**Production:**
```bash
docker-compose up -d
```

**Development:**
```bash
docker-compose --profile dev up -d
```

**With Nginx (Production):**
```bash
docker-compose --profile nginx up -d
```

### 5. Access the API

- **API Documentation:** http://localhost:7865/docs
- **Health Check:** http://localhost:7865/health
- **With Nginx:** http://localhost

## 📋 API Usage

### Process Images

**Endpoint:** `POST /process`

**Parameters:**
- `model_file`: Model image (required)
- `cloth_file`: Garment image (required)
- `model_type`: "hd" or "dc" (default: "hd")
- `category`: 0=upperbody, 1=lowerbody, 2=dress (default: 0)
- `samples`: Number of samples (1-4, default: 1)
- `steps`: Inference steps (1-40, default: 20)
- `scale`: Guidance scale (1.0-5.0, default: 2.0)
- `seed`: Random seed (-1 for random, default: -1)

**Example with cURL:**
```bash
curl -X POST "http://localhost:7865/process" \
  -F "model_file=@model.jpg" \
  -F "cloth_file=@cloth.jpg" \
  -F "model_type=hd" \
  -F "category=0" \
  -F "samples=1" \
  -F "steps=20" \
  -F "scale=2.0" \
  -F "seed=42"
```

**Response:**
```json
{
  "success": true,
  "message": "Images processed successfully",
  "result_paths": ["/static/results/result_20241219_143022_0.png"],
  "processing_time": 15.2
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-19T14:30:22.123456",
  "version": "1.0.0",
  "environment": "production",
  "models_loaded": true,
  "gpu_available": true
}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Basic Configuration
OOTD_ENVIRONMENT=production
OOTD_DEBUG=false
OOTD_HOST=0.0.0.0
OOTD_PORT=7865
OOTD_WORKERS=1

# Model Configuration
OOTD_DEVICE=cuda:0
OOTD_TORCH_DTYPE=float16

# Logging
OOTD_LOG_LEVEL=INFO
OOTD_LOG_FILE=logs/ootd.log

# Security
OOTD_SECRET_KEY=your-secret-key-here
OOTD_MAX_FILE_SIZE=10485760
OOTD_ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.bmp
```

### Model Configuration

Edit `config.py` to customize model settings:

```python
@dataclass
class ModelConfig:
    device: str = "cuda:0"
    torch_dtype: str = "float16"
    enable_attention_slicing: bool = True
    enable_memory_efficient_attention: bool = True
    enable_cpu_offload: bool = False
```

## 🐳 Docker Deployment

### Production Deployment

```bash
# Build and run
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f ootd-api

# Stop services
docker-compose down
```

### Development Deployment

```bash
# Run with development profile
docker-compose --profile dev up -d

# Access development API at port 7866
curl http://localhost:7866/health
```

### Custom Configuration

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  ootd-api:
    environment:
      - OOTD_WORKERS=4
      - OOTD_DEVICE=cuda:0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
```

## 📊 Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:7865/health

# Check container status
docker-compose ps

# View resource usage
docker stats
```

### Monitoring Script

```bash
# Run monitoring script
./scripts/monitor.sh  # Linux/macOS
scripts\monitor.bat   # Windows
```

### Logs

```bash
# View API logs
docker-compose logs -f ootd-api

# View all logs
docker-compose logs -f

# Save logs to file
docker-compose logs > logs/ootd.log
```

## 🔒 Security

### Input Validation

- File type verification using MIME type detection
- File size limits (configurable, default: 10MB)
- Image dimension validation
- Parameter range checking
- Filename sanitization

### Container Security

- Non-root user execution
- Minimal base images
- Security headers
- Resource limits
- No unnecessary packages

### API Security

- Rate limiting (configurable)
- CORS configuration
- Input sanitization
- Error message sanitization
- Request size limits

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=api --cov-report=html
```

### Test API Endpoints

```bash
# Test health endpoint
curl http://localhost:7865/health

# Test with sample images
curl -X POST "http://localhost:7865/process" \
  -F "model_file=@run/examples/model/model_1.png" \
  -F "cloth_file=@run/examples/garment/03244_00.jpg" \
  -F "model_type=hd"
```

## 📈 Performance

### Optimization Tips

1. **GPU Memory:**
   - Use `enable_attention_slicing=True`
   - Use `enable_memory_efficient_attention=True`
   - Consider `enable_cpu_offload=True` for large models

2. **Processing:**
   - Reduce `steps` for faster processing
   - Use fewer `samples` for quicker results
   - Optimize image dimensions

3. **Scaling:**
   - Increase `OOTD_WORKERS` for more concurrent requests
   - Use multiple GPU devices
   - Implement load balancing

### Benchmarking

```bash
# Run performance tests
pytest tests/test_performance.py -v

# Monitor resource usage
docker stats ootdiffusion-ootd-api-1
```

## 🚨 Troubleshooting

### Common Issues

#### Models Not Loading
```bash
# Check if checkpoints exist
ls -la checkpoints/

# Verify model paths in config.py
python -c "from config import config; print(config.get_model_paths())"
```

#### GPU Not Available
```bash
# Check NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi

# Check CUDA in container
docker-compose exec ootd-api nvidia-smi
```

#### Out of Memory
```bash
# Reduce batch size
export OOTD_WORKERS=1

# Enable CPU offload
# Edit config.py: enable_cpu_offload=True
```

#### Port Already in Use
```bash
# Change port in .env
echo "OOTD_PORT=7866" >> .env

# Restart services
docker-compose down && docker-compose up -d
```

### Debug Mode

```bash
# Enable debug mode
export OOTD_DEBUG=true
export OOTD_LOG_LEVEL=DEBUG

# Restart with debug
docker-compose down && docker-compose up -d
```

### Log Analysis

```bash
# View error logs
docker-compose logs ootd-api | grep ERROR

# View performance logs
docker-compose logs ootd-api | grep "execution_time"

# Export logs
docker-compose logs ootd-api > debug.log
```

## 🔄 Maintenance

### Updates

```bash
# Update application
./scripts/update.sh  # Linux/macOS
scripts\update.bat   # Windows

# Or manually
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

### Backups

```bash
# Create backup
./scripts/backup.sh  # Linux/macOS
scripts\backup.bat   # Windows

# Restore from backup
tar -xzf backups/20241219_143022.tar.gz
```

### Cleanup

```bash
# Clean temporary files
docker-compose exec ootd-api python -c "from utils.error_handling import cleanup_temp_files; cleanup_temp_files()"

# Clean old results
find outputs/results -name "*.png" -mtime +7 -delete

# Clean Docker
docker system prune -f
```

## 📚 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| POST | `/process` | Process images |
| GET | `/results/{filename}` | Download results |
| GET | `/docs` | API documentation |

### Models

| Model Type | Description | Categories |
|------------|-------------|------------|
| `hd` | Half-body model | 0=upperbody |
| `dc` | Full-body model | 0=upperbody, 1=lowerbody, 2=dress |

### Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 422 | Validation Error |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/levihsu/OOTDiffusion.git
cd OOTDiffusion

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v
```

### Code Style

```bash
# Format code
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original OOTDiffusion authors for the research implementation
- FastAPI team for the excellent web framework
- Docker team for containerization support
- Open source community for various dependencies

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/levihsu/OOTDiffusion/issues)
- **Discussions:** [GitHub Discussions](https://github.com/levihsu/OOTDiffusion/discussions)
- **Documentation:** [API Docs](http://localhost:7865/docs)

---

**Made with ❤️ for the AI community**
