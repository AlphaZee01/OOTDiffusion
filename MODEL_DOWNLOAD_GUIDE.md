# Model Checkpoint Download Guide

This guide explains how to download the required model checkpoints for OOTDiffusion.

## 📋 Required Models

You need to download these model checkpoints:

1. **OOTDiffusion Models** - Main diffusion models
2. **Human Parsing Models** - For human body segmentation
3. **OpenPose Models** - For pose detection
4. **CLIP Models** - For image encoding

## 🚀 Quick Download (Recommended)

### Windows Users
```cmd
scripts\download_models.bat
```

### Linux/macOS Users
```bash
python scripts/download_models.py
```

## 📥 Manual Download Steps

### Prerequisites

1. **Install Git** (if not already installed)
   - Windows: Download from [git-scm.com](https://git-scm.com/download/win)
   - Linux: `sudo apt-get install git`
   - macOS: `brew install git`

2. **Install Git LFS** (for large files)
   - Windows: Download from [git-lfs.github.io](https://git-lfs.github.io/)
   - Linux: `sudo apt-get install git-lfs`
   - macOS: `brew install git-lfs`

### Step 1: Initialize Git LFS
```bash
git lfs install
```

### Step 2: Create Checkpoints Directory
```bash
mkdir checkpoints
cd checkpoints
```

### Step 3: Download Models

#### OOTDiffusion Models
```bash
git clone https://huggingface.co/levihsu/OOTDiffusion ootd
```

#### Human Parsing Models
```bash
git clone https://huggingface.co/levihsu/OOTDiffusion humanparsing
```

#### OpenPose Models
```bash
git clone https://huggingface.co/levihsu/OOTDiffusion openpose
```

#### CLIP Models
```bash
git clone https://huggingface.co/openai/clip-vit-large-patch14
```

### Step 4: Verify Download
Your `checkpoints` directory should look like this:
```
checkpoints/
├── ootd/
├── humanparsing/
├── openpose/
└── clip-vit-large-patch14/
```

## 🔧 Troubleshooting

### Git LFS Issues

**Problem**: Files show as pointers instead of actual content
**Solution**:
```bash
git lfs pull
```

**Problem**: Git LFS not installed
**Solution**:
- Windows: Download installer from [git-lfs.github.io](https://git-lfs.github.io/)
- Linux: `sudo apt-get install git-lfs`
- macOS: `brew install git-lfs`

### Network Issues

**Problem**: Clone fails due to network timeout
**Solution**:
```bash
# Increase timeout
git config --global http.lowSpeedLimit 0
git config --global http.lowSpeedTime 999999

# Try again
git clone https://huggingface.co/levihsu/OOTDiffusion ootd
```

**Problem**: Large file download fails
**Solution**:
```bash
# Use shallow clone first
git clone --depth 1 https://huggingface.co/levihsu/OOTDiffusion ootd
cd ootd
git lfs pull
```

### Storage Space

**Required Space**: Approximately 15-20 GB
- OOTDiffusion models: ~8 GB
- Human parsing models: ~2 GB
- OpenPose models: ~2 GB
- CLIP models: ~3 GB

## 🐳 Alternative: Docker Download

If you prefer to download models inside a Docker container:

```bash
# Create a temporary container for downloading
docker run -it --rm -v $(pwd)/checkpoints:/checkpoints ubuntu:22.04 bash

# Inside the container
apt update && apt install -y git git-lfs
git lfs install
cd /checkpoints

# Download models
git clone https://huggingface.co/levihsu/OOTDiffusion ootd
git clone https://huggingface.co/levihsu/OOTDiffusion humanparsing
git clone https://huggingface.co/levihsu/OOTDiffusion openpose
git clone https://huggingface.co/openai/clip-vit-large-patch14
```

## 📊 Model Details

### OOTDiffusion Models
- **Size**: ~8 GB
- **Contents**: 
  - UNet models for garment and virtual try-on
  - VAE models
  - Text encoders
  - Schedulers

### Human Parsing Models
- **Size**: ~2 GB
- **Contents**:
  - Segmentation models
  - ONNX runtime models
  - Configuration files

### OpenPose Models
- **Size**: ~2 GB
- **Contents**:
  - Pose detection models
  - Hand and face models
  - Configuration files

### CLIP Models
- **Size**: ~3 GB
- **Contents**:
  - Vision transformer models
  - Text encoders
  - Preprocessing utilities

## ✅ Verification

After downloading, verify the models are working:

```bash
# Test the API
python start.py --mode api

# Check health endpoint
curl http://localhost:7865/health
```

The health check should show `"models_loaded": true`.

## 🆘 Support

If you encounter issues:

1. **Check internet connection**
2. **Verify Git LFS is installed**: `git lfs version`
3. **Check available disk space**: At least 20 GB free
4. **Try downloading one model at a time**
5. **Use the automated scripts provided**

## 📝 Notes

- Models are downloaded from Hugging Face Hub
- Git LFS is required for large files
- Download time depends on internet speed
- Models are cached locally after first download
- You can update models by running `git pull` in each model directory
