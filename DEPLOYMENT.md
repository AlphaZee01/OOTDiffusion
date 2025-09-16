# OOTDiffusion Production Deployment Guide

This guide covers deploying OOTDiffusion in various production environments.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   Nginx Proxy   │────│   FastAPI App   │
│   (Optional)    │    │   (Optional)    │    │   (Container)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐            │
                       │   Redis Cache   │────────────┘
                       │   (Optional)    │
                       └─────────────────┘
```

## 🚀 Quick Deployment

### Single Server Deployment

1. **Prerequisites**
   ```bash
   # Install Docker and Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo usermod -aG docker $USER
   
   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Deploy Application**
   ```bash
   # Clone repository
   git clone https://github.com/levihsu/OOTDiffusion.git
   cd OOTDiffusion
   
   # Run setup
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   
   # Download models (see model setup section)
   
   # Start services
   docker-compose up -d
   ```

3. **Verify Deployment**
   ```bash
   # Check health
   curl http://localhost:7865/health
   
   # Check logs
   docker-compose logs -f ootd-api
   ```

### Multi-Server Deployment

1. **Load Balancer Setup (Nginx)**
   ```nginx
   upstream ootd_backend {
       server ootd-server-1:7865;
       server ootd-server-2:7865;
       server ootd-server-3:7865;
   }
   
   server {
       listen 80;
       location / {
           proxy_pass http://ootd_backend;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Deploy on Each Server**
   ```bash
   # On each server
   git clone https://github.com/levihsu/OOTDiffusion.git
   cd OOTDiffusion
   ./scripts/setup.sh
   docker-compose up -d
   ```

## ☁️ Cloud Deployment

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Create ECS Cluster**
   ```bash
   aws ecs create-cluster --cluster-name ootd-cluster
   ```

2. **Create Task Definition**
   ```json
   {
     "family": "ootd-task",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "2048",
     "memory": "8192",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "ootd-api",
         "image": "your-account.dkr.ecr.region.amazonaws.com/ootd:latest",
         "portMappings": [
           {
             "containerPort": 7865,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "OOTD_ENVIRONMENT",
             "value": "production"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/ootd",
             "awslogs-region": "us-west-2",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

3. **Create Service**
   ```bash
   aws ecs create-service \
     --cluster ootd-cluster \
     --service-name ootd-service \
     --task-definition ootd-task \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
   ```

#### Using EKS (Elastic Kubernetes Service)

1. **Create Kubernetes Deployment**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: ootd-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: ootd-api
     template:
       metadata:
         labels:
           app: ootd-api
       spec:
         containers:
         - name: ootd-api
           image: your-account.dkr.ecr.region.amazonaws.com/ootd:latest
           ports:
           - containerPort: 7865
           env:
           - name: OOTD_ENVIRONMENT
             value: "production"
           resources:
             requests:
               memory: "4Gi"
               cpu: "1000m"
               nvidia.com/gpu: 1
             limits:
               memory: "8Gi"
               cpu: "2000m"
               nvidia.com/gpu: 1
   ```

2. **Create Service**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: ootd-service
   spec:
     selector:
       app: ootd-api
     ports:
     - port: 80
       targetPort: 7865
     type: LoadBalancer
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and Push Image**
   ```bash
   # Build image
   docker build -t gcr.io/PROJECT_ID/ootd .
   
   # Push to registry
   docker push gcr.io/PROJECT_ID/ootd
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy ootd-api \
     --image gcr.io/PROJECT_ID/ootd \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 8Gi \
     --cpu 2 \
     --max-instances 10
   ```

#### Using GKE (Google Kubernetes Engine)

1. **Create Cluster with GPU**
   ```bash
   gcloud container clusters create ootd-cluster \
     --zone us-central1-a \
     --machine-type n1-standard-4 \
     --accelerator type=nvidia-tesla-t4,count=1 \
     --num-nodes 3
   ```

2. **Deploy Application**
   ```bash
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   ```

### Azure Deployment

#### Using Container Instances

1. **Create Resource Group**
   ```bash
   az group create --name ootd-rg --location eastus
   ```

2. **Deploy Container**
   ```bash
   az container create \
     --resource-group ootd-rg \
     --name ootd-api \
     --image your-registry.azurecr.io/ootd:latest \
     --cpu 2 \
     --memory 8 \
     --ports 7865 \
     --environment-variables OOTD_ENVIRONMENT=production
   ```

## 🔧 Configuration

### Environment-Specific Configs

#### Development
```bash
export OOTD_ENVIRONMENT=development
export OOTD_DEBUG=true
export OOTD_LOG_LEVEL=DEBUG
export OOTD_WORKERS=1
```

#### Staging
```bash
export OOTD_ENVIRONMENT=staging
export OOTD_DEBUG=false
export OOTD_LOG_LEVEL=INFO
export OOTD_WORKERS=2
```

#### Production
```bash
export OOTD_ENVIRONMENT=production
export OOTD_DEBUG=false
export OOTD_LOG_LEVEL=WARNING
export OOTD_WORKERS=4
```

### Model Configuration

#### GPU Configuration
```python
# config.py
@dataclass
class ModelConfig:
    device: str = "cuda:0"  # Primary GPU
    torch_dtype: str = "float16"  # Memory optimization
    enable_attention_slicing: bool = True
    enable_memory_efficient_attention: bool = True
    enable_cpu_offload: bool = False  # Set to True for large models
```

#### Multi-GPU Setup
```python
# For multiple GPUs
@dataclass
class ModelConfig:
    device: str = "cuda:0"
    secondary_device: str = "cuda:1"  # For DC models
    enable_model_parallelism: bool = True
```

## 📊 Monitoring and Logging

### Prometheus Metrics

1. **Add Prometheus Client**
   ```python
   from prometheus_client import Counter, Histogram, generate_latest
   
   # Metrics
   request_count = Counter('ootd_requests_total', 'Total requests')
   request_duration = Histogram('ootd_request_duration_seconds', 'Request duration')
   ```

2. **Expose Metrics Endpoint**
   ```python
   @app.get("/metrics")
   async def metrics():
       return Response(generate_latest(), media_type="text/plain")
   ```

### Grafana Dashboard

1. **Create Dashboard**
   ```json
   {
     "dashboard": {
       "title": "OOTDiffusion Metrics",
       "panels": [
         {
           "title": "Request Rate",
           "type": "graph",
           "targets": [
             {
               "expr": "rate(ootd_requests_total[5m])"
             }
           ]
         }
       ]
     }
   }
   ```

### Log Aggregation

#### ELK Stack
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
  
  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
  
  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

## 🔒 Security

### SSL/TLS Configuration

1. **Generate Certificates**
   ```bash
   # Using Let's Encrypt
   certbot certonly --standalone -d your-domain.com
   ```

2. **Update Nginx Config**
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
       
       location / {
           proxy_pass http://ootd_backend;
       }
   }
   ```

### Authentication

1. **API Key Authentication**
   ```python
   from fastapi import HTTPException, Depends
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   def verify_token(token: str = Depends(security)):
       if token.credentials != "your-api-key":
           raise HTTPException(status_code=401, detail="Invalid API key")
       return token
   ```

2. **JWT Authentication**
   ```python
   from jose import JWTError, jwt
   
   def verify_jwt_token(token: str = Depends(security)):
       try:
           payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
           return payload
       except JWTError:
           raise HTTPException(status_code=401, detail="Invalid token")
   ```

## 🚨 Troubleshooting

### Common Issues

#### Out of Memory
```bash
# Check memory usage
docker stats

# Reduce memory usage
export OOTD_WORKERS=1
export OOTD_ENABLE_CPU_OFFLOAD=true
```

#### GPU Issues
```bash
# Check GPU availability
nvidia-smi

# Test GPU in container
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu22.04 nvidia-smi
```

#### Model Loading Issues
```bash
# Check model paths
ls -la checkpoints/

# Verify model files
python -c "from config import config; print(config.get_model_paths())"
```

### Performance Optimization

#### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  ootd-api:
    deploy:
      replicas: 3
    environment:
      - OOTD_WORKERS=1
```

#### Vertical Scaling
```yaml
# Increase resources
services:
  ootd-api:
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '4'
```

## 📈 Scaling Strategies

### Auto-Scaling

#### Kubernetes HPA
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ootd-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ootd-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Docker Swarm
```bash
# Create service with scaling
docker service create \
  --name ootd-api \
  --replicas 3 \
  --publish 7865:7865 \
  your-registry/ootd:latest
```

### Load Balancing

#### Nginx Load Balancer
```nginx
upstream ootd_backend {
    least_conn;
    server ootd-1:7865 weight=3;
    server ootd-2:7865 weight=2;
    server ootd-3:7865 weight=1;
}
```

#### HAProxy
```haproxy
backend ootd_backend
    balance roundrobin
    server ootd-1 ootd-1:7865 check
    server ootd-2 ootd-2:7865 check
    server ootd-3 ootd-3:7865 check
```

## 🔄 Backup and Recovery

### Data Backup

1. **Model Checkpoints**
   ```bash
   # Backup models
   tar -czf models-backup-$(date +%Y%m%d).tar.gz checkpoints/
   
   # Upload to cloud storage
   aws s3 cp models-backup-$(date +%Y%m%d).tar.gz s3://your-bucket/backups/
   ```

2. **Configuration Backup**
   ```bash
   # Backup configuration
   tar -czf config-backup-$(date +%Y%m%d).tar.gz config.py .env docker-compose.yml
   ```

### Disaster Recovery

1. **Restore from Backup**
   ```bash
   # Download backup
   aws s3 cp s3://your-bucket/backups/models-backup-20241219.tar.gz .
   
   # Extract backup
   tar -xzf models-backup-20241219.tar.gz
   
   # Restart services
   docker-compose up -d
   ```

2. **Health Check After Recovery**
   ```bash
   # Verify services
   curl http://localhost:7865/health
   
   # Run tests
   pytest tests/ -v
   ```

## 📞 Support

### Monitoring Alerts

1. **Set up Alerts**
   ```yaml
   # alertmanager.yml
   groups:
   - name: ootd
     rules:
     - alert: OOTDServiceDown
       expr: up{job="ootd-api"} == 0
       for: 1m
       labels:
         severity: critical
       annotations:
         summary: "OOTD API is down"
   ```

2. **Notification Channels**
   - Email alerts
   - Slack notifications
   - PagerDuty integration

### Maintenance Windows

1. **Scheduled Maintenance**
   ```bash
   # Create maintenance script
   #!/bin/bash
   echo "Starting maintenance window..."
   docker-compose down
   # Perform maintenance tasks
   docker-compose up -d
   echo "Maintenance completed"
   ```

2. **Zero-Downtime Updates**
   ```bash
   # Rolling update
   docker-compose up -d --no-deps ootd-api
   ```

---

This deployment guide provides comprehensive instructions for deploying OOTDiffusion in various production environments. Choose the approach that best fits your infrastructure and requirements.
