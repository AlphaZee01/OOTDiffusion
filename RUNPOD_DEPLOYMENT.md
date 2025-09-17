# OOTDiffusion RunPod Deployment Guide

## 🚀 Quick Start

### 1. Prerequisites
- RunPod account with credits
- Docker installed locally (for testing)
- Python 3.10+ (for local testing)

### 2. Deploy to RunPod

#### Option A: Deploy from GitHub
1. Go to [RunPod Console](https://console.runpod.io)
2. Click "Deploy" → "Serverless"
3. Select "Deploy from GitHub"
4. Enter repository: `AlphaZee01/OOTDiffusion`
5. Set branch: `main`
6. Configure resources:
   - **GPU**: A100 (recommended) or RTX 4090
   - **Memory**: 32GB+ RAM
   - **Storage**: 50GB+
7. Click "Deploy"

#### Option B: Deploy from Docker Image
1. Build and push Docker image to registry
2. Use image URL in RunPod deployment
3. Configure environment variables
4. Deploy

### 3. Test Your Deployment

#### Using the Test Script
```bash
# Set your endpoint URL
export RUNPOD_ENDPOINT_URL="https://api.runpod.ai/v2/your-endpoint-id/tryon"

# Run the test
python test_handler.py
```

#### Using cURL
```bash
curl -X POST 'https://api.runpod.ai/v2/your-endpoint-id/tryon' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": {
      "user_image": "base64_encoded_user_image",
      "cloth_image": "base64_encoded_cloth_image",
      "garment_type": "upper",
      "model_type": "hd",
      "samples": 1
    }
  }'
```

## 📋 Configuration

### Environment Variables
```bash
# Required
OOTD_DEVICE=cpu  # or cuda:0 for GPU
OOTD_ENVIRONMENT=production

# Optional
OOTD_DEBUG=false
OOTD_TORCH_DTYPE=float16
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Resource Requirements
- **Minimum**: 16GB RAM, 20GB storage
- **Recommended**: 32GB RAM, 50GB storage, A100 GPU
- **CPU-only**: Works but slower (15-30s per image)

## 🔧 API Reference

### Endpoint: `/tryon`
**Method**: POST  
**Content-Type**: application/json

#### Request Body
```json
{
  "input": {
    "user_image": "base64_encoded_image",
    "cloth_image": "base64_encoded_image",
    "garment_type": "upper",     // optional: "upper", "lower", "dress"
    "model_type": "hd",          // optional: "hd", "dc"
    "category": 0,               // optional: 0=upperbody, 1=lowerbody, 2=dress
    "scale": 2.0,                // optional: guidance scale (1.0-5.0)
    "steps": 20,                 // optional: inference steps (1-40)
    "samples": 1,                // optional: number of samples (1-4)
    "seed": -1,                  // optional: random seed (-1 for random)
    "gpu_id": 0                  // optional: GPU ID
  }
}
```

#### Response Body
```json
{
  "output": {
    "success": true,
    "images": ["base64_result1", "base64_result2"],
    "message": "Successfully generated 1 result image(s)",
    "parameters": {
      "garment_type": "upper",
      "model_type": "hd",
      "category": 0,
      "scale": 2.0,
      "steps": 20,
      "samples": 1,
      "seed": -1
    }
  }
}
```

#### Error Response
```json
{
  "error": "Error message",
  "traceback": "Detailed error traceback"
}
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Model Download Fails
**Symptoms**: Handler starts but models don't load  
**Solutions**:
- Check internet connection
- Verify disk space (need 20GB+)
- Check RunPod logs for git-lfs errors

#### 2. Out of Memory
**Symptoms**: Handler crashes with OOM error  
**Solutions**:
- Increase RAM allocation
- Use CPU device: `OOTD_DEVICE=cpu`
- Reduce samples: `samples=1`

#### 3. Slow Processing
**Symptoms**: Requests take >60 seconds  
**Solutions**:
- Use GPU: `OOTD_DEVICE=cuda:0`
- Reduce steps: `steps=10`
- Use smaller images

#### 4. Invalid Image Format
**Symptoms**: "Invalid base64 image data" error  
**Solutions**:
- Ensure images are base64 encoded
- Check image format (JPG, PNG supported)
- Verify base64 encoding is correct

### Debug Mode
Enable debug logging:
```bash
export OOTD_DEBUG=true
```

Check logs in RunPod console or `/workspace/logs/runpod.log`

## 📊 Performance Optimization

### GPU Configuration
```bash
# For A100 GPU
export OOTD_DEVICE=cuda:0
export OOTD_TORCH_DTYPE=float16
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### CPU Configuration
```bash
# For CPU-only deployment
export OOTD_DEVICE=cpu
export OOTD_TORCH_DTYPE=float32
```

### Memory Optimization
- Use `float16` for GPU inference
- Set `samples=1` for single image generation
- Use `steps=10-20` for faster processing

## 🔒 Security Best Practices

### Input Validation
- Validate image formats before processing
- Set reasonable size limits
- Sanitize all input parameters

### Error Handling
- Don't expose sensitive information in errors
- Log errors for debugging
- Return user-friendly error messages

### Resource Limits
- Set timeout limits for requests
- Monitor memory usage
- Implement rate limiting if needed

## 📈 Monitoring

### Key Metrics
- **Request latency**: Target <30 seconds
- **Success rate**: Target >95%
- **Memory usage**: Monitor for leaks
- **Error rate**: Target <5%

### Logging
- All requests are logged
- Errors include stack traces
- Performance metrics tracked

## 🆘 Support

### Getting Help
1. Check RunPod logs first
2. Review this documentation
3. Test with `test_handler.py`
4. Open GitHub issue if needed

### Useful Commands
```bash
# Test locally
python test_handler.py

# Check handler status
curl https://api.runpod.ai/v2/your-endpoint-id/health

# View logs
# (Check RunPod console)
```

---

**Need more help?** Check the [GitHub Issues](https://github.com/AlphaZee01/OOTDiffusion/issues) or [Discussions](https://github.com/AlphaZee01/OOTDiffusion/discussions)
