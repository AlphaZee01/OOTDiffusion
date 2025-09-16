#!/bin/bash

# OOTDiffusion Production Setup Script
set -e

echo "🚀 Setting up OOTDiffusion for production..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if NVIDIA Docker is available
if ! docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    print_warning "NVIDIA Docker runtime not available. GPU acceleration will not work."
    print_warning "Please install nvidia-docker2 for GPU support."
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p checkpoints
mkdir -p outputs/results
mkdir -p temp/uploads
mkdir -p temp/processed
mkdir -p logs
mkdir -p ssl

# Set proper permissions
chmod 755 checkpoints outputs temp logs ssl
chmod 755 outputs/results temp/uploads temp/processed

print_status "Directories created successfully"

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
# OOTDiffusion Environment Configuration
OOTD_ENVIRONMENT=production
OOTD_DEBUG=false
OOTD_HOST=0.0.0.0
OOTD_PORT=7865
OOTD_WORKERS=1
OOTD_DEVICE=cuda:0

# Logging
OOTD_LOG_LEVEL=INFO
OOTD_LOG_FILE=logs/ootd.log

# File upload limits
OOTD_MAX_FILE_SIZE=10485760
OOTD_ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.bmp

# Security
OOTD_SECRET_KEY=$(openssl rand -hex 32)
OOTD_ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF

print_status "Environment file created"

# Download model checkpoints if not present
print_status "Checking for model checkpoints..."

if [ ! -d "checkpoints/ootd" ]; then
    print_warning "OOTD model checkpoints not found."
    print_warning "Please download them from: https://huggingface.co/levihsu/OOTDiffusion"
    print_warning "Place them in the checkpoints/ directory"
fi

if [ ! -d "checkpoints/humanparsing" ]; then
    print_warning "Human parsing model checkpoints not found."
    print_warning "Please download them from: https://huggingface.co/levihsu/OOTDiffusion"
    print_warning "Place them in the checkpoints/ directory"
fi

if [ ! -d "checkpoints/openpose" ]; then
    print_warning "OpenPose model checkpoints not found."
    print_warning "Please download them from: https://huggingface.co/levihsu/OOTDiffusion"
    print_warning "Place them in the checkpoints/ directory"
fi

if [ ! -d "checkpoints/clip-vit-large-patch14" ]; then
    print_warning "CLIP model checkpoints not found."
    print_warning "Please download them from: https://huggingface.co/openai/clip-vit-large-patch14"
    print_warning "Place them in the checkpoints/ directory"
fi

# Create systemd service file
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/ootd.service > /dev/null << EOF
[Unit]
Description=OOTDiffusion API Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

print_status "Systemd service created"

# Create nginx configuration
print_status "Creating nginx configuration..."
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream ootd_backend {
        server ootd-api:7865;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;

    server {
        listen 80;
        server_name _;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # File upload size
        client_max_body_size 50M;

        # API endpoints
        location / {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://ootd_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;
        }

        # Static files
        location /static/ {
            proxy_pass http://ootd_backend;
            expires 1d;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

print_status "Nginx configuration created"

# Create monitoring script
print_status "Creating monitoring script..."
cat > scripts/monitor.sh << 'EOF'
#!/bin/bash

# OOTDiffusion Monitoring Script

check_service() {
    local service_name=$1
    local container_name=$2
    
    if docker ps | grep -q $container_name; then
        echo "✅ $service_name is running"
        return 0
    else
        echo "❌ $service_name is not running"
        return 1
    fi
}

check_health() {
    local url=$1
    local service_name=$2
    
    if curl -f -s $url > /dev/null; then
        echo "✅ $service_name health check passed"
        return 0
    else
        echo "❌ $service_name health check failed"
        return 1
    fi
}

echo "🔍 Checking OOTDiffusion services..."

# Check containers
check_service "OOTD API" "ootdiffusion-ootd-api-1"
check_service "Redis" "ootdiffusion-redis-1" 2>/dev/null || true
check_service "Nginx" "ootdiffusion-nginx-1" 2>/dev/null || true

# Check health endpoints
check_health "http://localhost:7865/health" "OOTD API"

echo "📊 System resources:"
echo "CPU usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory usage: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
echo "Disk usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo "📈 GPU status:"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null || echo "GPU not available"
EOF

chmod +x scripts/monitor.sh

print_status "Monitoring script created"

# Create backup script
print_status "Creating backup script..."
cat > scripts/backup.sh << 'EOF'
#!/bin/bash

# OOTDiffusion Backup Script

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "📦 Creating backup in $BACKUP_DIR..."

# Backup configuration
cp -r config.py $BACKUP_DIR/
cp -r .env $BACKUP_DIR/
cp -r docker-compose.yml $BACKUP_DIR/
cp -r nginx.conf $BACKUP_DIR/

# Backup outputs (if any)
if [ -d "outputs" ] && [ "$(ls -A outputs)" ]; then
    cp -r outputs $BACKUP_DIR/
fi

# Backup logs
if [ -d "logs" ] && [ "$(ls -A logs)" ]; then
    cp -r logs $BACKUP_DIR/
fi

echo "✅ Backup completed: $BACKUP_DIR"
EOF

chmod +x scripts/backup.sh

print_status "Backup script created"

# Create update script
print_status "Creating update script..."
cat > scripts/update.sh << 'EOF'
#!/bin/bash

# OOTDiffusion Update Script

echo "🔄 Updating OOTDiffusion..."

# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build --no-cache

# Restart services
docker-compose down
docker-compose up -d

echo "✅ Update completed"
EOF

chmod +x scripts/update.sh

print_status "Update script created"

print_status "🎉 Setup completed successfully!"
print_status ""
print_status "Next steps:"
print_status "1. Download model checkpoints to the checkpoints/ directory"
print_status "2. Run: docker-compose up -d"
print_status "3. Check status: ./scripts/monitor.sh"
print_status "4. Access API at: http://localhost:7865"
print_status ""
print_status "For development:"
print_status "1. Run: docker-compose --profile dev up -d"
print_status "2. Access dev API at: http://localhost:7866"
print_status ""
print_status "For production with nginx:"
print_status "1. Run: docker-compose --profile nginx up -d"
print_status "2. Access via nginx at: http://localhost"
