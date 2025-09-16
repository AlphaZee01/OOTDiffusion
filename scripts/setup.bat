@echo off
REM OOTDiffusion Production Setup Script for Windows

echo 🚀 Setting up OOTDiffusion for production...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "checkpoints" mkdir checkpoints
if not exist "outputs\results" mkdir outputs\results
if not exist "temp\uploads" mkdir temp\uploads
if not exist "temp\processed" mkdir temp\processed
if not exist "logs" mkdir logs
if not exist "ssl" mkdir ssl

echo [INFO] Directories created successfully

REM Create environment file
echo [INFO] Creating environment configuration...
(
echo # OOTDiffusion Environment Configuration
echo OOTD_ENVIRONMENT=production
echo OOTD_DEBUG=false
echo OOTD_HOST=0.0.0.0
echo OOTD_PORT=7865
echo OOTD_WORKERS=1
echo OOTD_DEVICE=cuda:0
echo.
echo # Logging
echo OOTD_LOG_LEVEL=INFO
echo OOTD_LOG_FILE=logs/ootd.log
echo.
echo # File upload limits
echo OOTD_MAX_FILE_SIZE=10485760
echo OOTD_ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.bmp
echo.
echo # Security
echo OOTD_SECRET_KEY=your-secret-key-here
echo OOTD_ACCESS_TOKEN_EXPIRE_MINUTES=30
) > .env

echo [INFO] Environment file created

REM Check for model checkpoints
echo [INFO] Checking for model checkpoints...

if not exist "checkpoints\ootd" (
    echo [WARNING] OOTD model checkpoints not found.
    echo [WARNING] Please download them from: https://huggingface.co/levihsu/OOTDiffusion
    echo [WARNING] Place them in the checkpoints\ directory
)

if not exist "checkpoints\humanparsing" (
    echo [WARNING] Human parsing model checkpoints not found.
    echo [WARNING] Please download them from: https://huggingface.co/levihsu/OOTDiffusion
    echo [WARNING] Place them in the checkpoints\ directory
)

if not exist "checkpoints\openpose" (
    echo [WARNING] OpenPose model checkpoints not found.
    echo [WARNING] Please download them from: https://huggingface.co/levihsu/OOTDiffusion
    echo [WARNING] Place them in the checkpoints\ directory
)

if not exist "checkpoints\clip-vit-large-patch14" (
    echo [WARNING] CLIP model checkpoints not found.
    echo [WARNING] Please download them from: https://huggingface.co/openai/clip-vit-large-patch14
    echo [WARNING] Place them in the checkpoints\ directory
)

REM Create nginx configuration
echo [INFO] Creating nginx configuration...
(
echo events {
echo     worker_connections 1024;
echo }
echo.
echo http {
echo     upstream ootd_backend {
echo         server ootd-api:7865;
echo     }
echo.
echo     # Rate limiting
echo     limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
echo.
echo     server {
echo         listen 80;
echo         server_name _;
echo.
echo         # Security headers
echo         add_header X-Frame-Options DENY;
echo         add_header X-Content-Type-Options nosniff;
echo         add_header X-XSS-Protection "1; mode=block";
echo.
echo         # File upload size
echo         client_max_body_size 50M;
echo.
echo         # API endpoints
echo         location / {
echo             limit_req zone=api burst=20 nodelay;
echo             proxy_pass http://ootd_backend;
echo             proxy_set_header Host $host;
echo             proxy_set_header X-Real-IP $remote_addr;
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo             proxy_set_header X-Forwarded-Proto $scheme;
echo             
echo             # Timeouts
echo             proxy_connect_timeout 60s;
echo             proxy_send_timeout 60s;
echo             proxy_read_timeout 300s;
echo         }
echo.
echo         # Static files
echo         location /static/ {
echo             proxy_pass http://ootd_backend;
echo             expires 1d;
echo             add_header Cache-Control "public, immutable";
echo         }
echo     }
echo }
) > nginx.conf

echo [INFO] Nginx configuration created

REM Create monitoring script
echo [INFO] Creating monitoring script...
(
echo @echo off
echo REM OOTDiffusion Monitoring Script
echo.
echo echo 🔍 Checking OOTDiffusion services...
echo.
echo REM Check containers
echo docker ps --filter "name=ootdiffusion-ootd-api-1" --format "table {{.Names}}\t{{.Status}}"
echo docker ps --filter "name=ootdiffusion-redis-1" --format "table {{.Names}}\t{{.Status}}" 2^>nul
echo docker ps --filter "name=ootdiffusion-nginx-1" --format "table {{.Names}}\t{{.Status}}" 2^>nul
echo.
echo REM Check health endpoints
echo curl -f -s http://localhost:7865/health ^>nul
echo if %errorlevel% equ 0 ^(
echo     echo ✅ OOTD API health check passed
echo ^) else ^(
echo     echo ❌ OOTD API health check failed
echo ^)
echo.
echo echo 📊 System resources:
echo wmic cpu get loadpercentage /value ^| find "LoadPercentage"
echo wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /value
echo.
echo echo 📈 GPU status:
echo nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2^>nul ^|^| echo GPU not available
) > scripts\monitor.bat

echo [INFO] Monitoring script created

REM Create backup script
echo [INFO] Creating backup script...
(
echo @echo off
echo REM OOTDiffusion Backup Script
echo.
echo set BACKUP_DIR=backups\%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
echo set BACKUP_DIR=%BACKUP_DIR: =0%
echo mkdir %BACKUP_DIR%
echo.
echo echo 📦 Creating backup in %BACKUP_DIR%...
echo.
echo REM Backup configuration
echo copy config.py %BACKUP_DIR%\
echo copy .env %BACKUP_DIR%\
echo copy docker-compose.yml %BACKUP_DIR%\
echo copy nginx.conf %BACKUP_DIR%\
echo.
echo REM Backup outputs ^(if any^)
echo if exist "outputs" ^(
echo     xcopy outputs %BACKUP_DIR%\outputs\ /E /I /Q
echo ^)
echo.
echo REM Backup logs
echo if exist "logs" ^(
echo     xcopy logs %BACKUP_DIR%\logs\ /E /I /Q
echo ^)
echo.
echo echo ✅ Backup completed: %BACKUP_DIR%
) > scripts\backup.bat

echo [INFO] Backup script created

REM Create update script
echo [INFO] Creating update script...
(
echo @echo off
echo REM OOTDiffusion Update Script
echo.
echo echo 🔄 Updating OOTDiffusion...
echo.
echo REM Pull latest changes
echo git pull origin main
echo.
echo REM Rebuild containers
echo docker-compose build --no-cache
echo.
echo REM Restart services
echo docker-compose down
echo docker-compose up -d
echo.
echo echo ✅ Update completed
) > scripts\update.bat

echo [INFO] Update script created

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Download model checkpoints to the checkpoints\ directory
echo 2. Run: docker-compose up -d
echo 3. Check status: scripts\monitor.bat
echo 4. Access API at: http://localhost:7865
echo.
echo For development:
echo 1. Run: docker-compose --profile dev up -d
echo 2. Access dev API at: http://localhost:7866
echo.
echo For production with nginx:
echo 1. Run: docker-compose --profile nginx up -d
echo 2. Access via nginx at: http://localhost
