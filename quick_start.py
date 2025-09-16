#!/usr/bin/env python3
"""
Quick Start Script for OOTDiffusion
One-command setup and start for hosting the repository
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("🎭 OOTDiffusion - Quick Start")
    print("=" * 60)
    print("This script will:")
    print("1. Check and install dependencies")
    print("2. Download model checkpoints automatically")
    print("3. Start the production API")
    print("=" * 60)
    print()

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Install production requirements
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-prod.txt"
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def download_models():
    """Download model checkpoints"""
    print("📥 Checking for model checkpoints...")
    
    # Check if models exist
    checkpoints_dir = Path("checkpoints")
    required_models = ["ootd", "humanparsing", "openpose", "clip-vit-large-patch14"]
    
    missing_models = []
    for model in required_models:
        model_path = checkpoints_dir / model
        if not model_path.exists() or not any(model_path.iterdir()):
            missing_models.append(model)
    
    if missing_models:
        print(f"📥 Missing models: {', '.join(missing_models)}")
        print("🔄 Starting automatic download...")
        print("⏱️  This may take 10-30 minutes depending on your internet speed...")
        
        try:
            subprocess.run([
                sys.executable, "scripts/auto_download_models.py"
            ], check=True)
            print("✅ Models downloaded successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Model download failed: {e}")
            print("Please run: python scripts/download_models.py")
            return False
    else:
        print("✅ All models are available")
        return True

def start_api():
    """Start the API server"""
    print("🚀 Starting OOTDiffusion API server...")
    print("📍 API will be available at: http://localhost:7865")
    print("📖 API documentation: http://localhost:7865/docs")
    print("🧪 Test interface: Open test_interface.html in your browser")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        subprocess.run([
            sys.executable, "start.py", "--mode", "api"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Download models
    if not download_models():
        print("⚠️  Continuing without all models. Some features may not work.")
    
    # Start API
    start_api()
    return 0

if __name__ == "__main__":
    sys.exit(main())
