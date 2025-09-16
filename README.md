# OOTDiffusion
This repository is the official implementation of OOTDiffusion

🤗 [Try out OOTDiffusion](https://huggingface.co/spaces/levihsu/OOTDiffusion)

(Thanks to [ZeroGPU](https://huggingface.co/zero-gpu-explorers) for providing A100 GPUs)

<!-- Or [try our own demo](https://ootd.ibot.cn/) on RTX 4090 GPUs -->

> **OOTDiffusion: Outfitting Fusion based Latent Diffusion for Controllable Virtual Try-on** [[arXiv paper](https://arxiv.org/abs/2403.01779)]<br>
> [Yuhao Xu](http://levihsu.github.io/), [Tao Gu](https://github.com/T-Gu), [Weifeng Chen](https://github.com/ShineChen1024), [Chengcai Chen](https://www.researchgate.net/profile/Chengcai-Chen)<br>
> Xiao-i Research


Our model checkpoints trained on [VITON-HD](https://github.com/shadow2496/VITON-HD) (half-body) and [Dress Code](https://github.com/aimagelab/dress-code) (full-body) have been released

* 🤗 [Hugging Face link](https://huggingface.co/levihsu/OOTDiffusion) for ***checkpoints*** (ootd, humanparsing, and openpose)
* 📢📢 We support ONNX for [humanparsing](https://github.com/GoGoDuck912/Self-Correction-Human-Parsing) now. Most environmental issues should have been addressed : )
* Please also download [clip-vit-large-patch14](https://huggingface.co/openai/clip-vit-large-patch14) into ***checkpoints*** folder
* We've only tested our code and models on Linux (Ubuntu 22.04)

![demo](images/demo.png)&nbsp;
![workflow](images/workflow.png)&nbsp;

## 🚀 Quick Start (Recommended)

### One-Command Setup
```bash
# Clone the repository
git clone https://github.com/your-username/OOTDiffusion
cd OOTDiffusion

# One-command setup (automatically downloads models and starts API)
python quick_start.py
```

### Docker Setup (Production)
```bash
# Clone and start with Docker
git clone https://github.com/your-username/OOTDiffusion
cd OOTDiffusion
docker-compose up -d
```

**Access your OOTDiffusion instance:**
- API: http://localhost:7865
- Documentation: http://localhost:7865/docs
- Test Interface: Open `test_interface.html` in your browser

## 📦 Manual Installation

### Prerequisites
- Python 3.8+
- Git LFS (for model downloads)
- CUDA (optional, for GPU acceleration)

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/OOTDiffusion
cd OOTDiffusion
```

### Step 2: Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-prod.txt
```

### Step 3: Download Models (Automatic)
```bash
# Models download automatically on first run
python start.py --mode api

# Or download manually
python scripts/download_models.py
```

### Step 4: Start the Application
```bash
# Start production API
python start.py --mode api

# Or start with Gradio interface
python start.py --mode gradio
```

## Inference
1. Half-body model

```sh
cd OOTDiffusion/run
python run_ootd.py --model_path <model-image-path> --cloth_path <cloth-image-path> --scale 2.0 --sample 4
```

2. Full-body model 

> Garment category must be paired: 0 = upperbody; 1 = lowerbody; 2 = dress

```sh
cd OOTDiffusion/run
python run_ootd.py --model_path <model-image-path> --cloth_path <cloth-image-path> --model_type dc --category 2 --scale 2.0 --sample 4
```

## Citation
```
@article{xu2024ootdiffusion,
  title={OOTDiffusion: Outfitting Fusion based Latent Diffusion for Controllable Virtual Try-on},
  author={Xu, Yuhao and Gu, Tao and Chen, Weifeng and Chen, Chengcai},
  journal={arXiv preprint arXiv:2403.01779},
  year={2024}
}
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=levihsu/OOTDiffusion&type=Date)](https://star-history.com/#levihsu/OOTDiffusion&Date)

## TODO List
- [x] Paper
- [x] Gradio demo
- [x] Inference code
- [x] Model weights
- [ ] Training code
