#!/usr/bin/env python3
"""
Model Checkpoint Downloader for OOTDiffusion
Downloads all required model checkpoints from Hugging Face
"""
import os
import sys
import subprocess
from pathlib import Path
import argparse

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_git_lfs():
    """Check if git-lfs is installed"""
    try:
        subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_git_lfs():
    """Install git-lfs"""
    print("📦 Installing git-lfs...")
    
    # Try different installation methods based on OS
    if sys.platform == "win32":
        # Windows - try chocolatey first, then direct download
        if run_command("choco install git-lfs -y", "Installing git-lfs via Chocolatey"):
            return True
        else:
            print("⚠️  Chocolatey not found. Please install git-lfs manually:")
            print("   1. Download from: https://git-lfs.github.io/")
            print("   2. Run the installer")
            print("   3. Restart your terminal")
            return False
    else:
        # Linux/macOS
        if run_command("curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | sudo bash", "Adding git-lfs repository"):
            if run_command("sudo apt-get install git-lfs -y", "Installing git-lfs"):
                return True
        
        # Try brew for macOS
        if run_command("brew install git-lfs", "Installing git-lfs via Homebrew"):
            return True
        
        print("⚠️  Please install git-lfs manually:")
        print("   Linux: sudo apt-get install git-lfs")
        print("   macOS: brew install git-lfs")
        return False

def download_model(repo_url, target_dir, model_name):
    """Download a model from Hugging Face"""
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    if target_path.exists() and any(target_path.iterdir()):
        print(f"✅ {model_name} already exists, skipping...")
        return True
    
    print(f"📥 Downloading {model_name}...")
    cmd = f"git clone {repo_url} {target_path}"
    
    if run_command(cmd, f"Downloading {model_name}"):
        print(f"✅ {model_name} downloaded successfully")
        return True
    else:
        print(f"❌ Failed to download {model_name}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download OOTDiffusion model checkpoints")
    parser.add_argument("--checkpoints-dir", default="checkpoints", help="Directory to store checkpoints")
    parser.add_argument("--skip-git-lfs", action="store_true", help="Skip git-lfs installation check")
    parser.add_argument("--models", nargs="+", choices=["ootd", "humanparsing", "openpose", "clip"], 
                       help="Specific models to download (default: all)")
    
    args = parser.parse_args()
    
    print("🎭 OOTDiffusion Model Checkpoint Downloader")
    print("=" * 50)
    
    # Check if git-lfs is installed
    if not args.skip_git_lfs and not check_git_lfs():
        print("⚠️  git-lfs is not installed. It's required for downloading large model files.")
        if not install_git_lfs():
            print("❌ Please install git-lfs manually and run this script again.")
            return 1
    else:
        print("✅ git-lfs is available")
    
    # Initialize git-lfs
    run_command("git lfs install", "Initializing git-lfs")
    
    # Define models to download
    models = {
        "ootd": "https://huggingface.co/levihsu/OOTDiffusion",
        "humanparsing": "https://huggingface.co/levihsu/OOTDiffusion",
        "openpose": "https://huggingface.co/levihsu/OOTDiffusion", 
        "clip": "https://huggingface.co/openai/clip-vit-large-patch14"
    }
    
    # Filter models if specific ones requested
    if args.models:
        models = {k: v for k, v in models.items() if k in args.models}
    
    # Create checkpoints directory
    checkpoints_dir = Path(args.checkpoints_dir)
    checkpoints_dir.mkdir(exist_ok=True)
    
    print(f"📁 Checkpoints will be saved to: {checkpoints_dir.absolute()}")
    print()
    
    # Download each model
    success_count = 0
    total_models = len(models)
    
    for model_name, repo_url in models.items():
        target_dir = checkpoints_dir / model_name
        
        if download_model(repo_url, target_dir, model_name):
            success_count += 1
        print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Download Summary: {success_count}/{total_models} models downloaded successfully")
    
    if success_count == total_models:
        print("🎉 All models downloaded successfully!")
        print("\n📋 Next steps:")
        print("1. Run the setup script: scripts/setup.bat (Windows) or scripts/setup.sh (Linux/macOS)")
        print("2. Start the API: python start.py --mode api")
        print("3. Open test_interface.html to test the functionality")
        return 0
    else:
        print("⚠️  Some models failed to download. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
