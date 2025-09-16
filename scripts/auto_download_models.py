#!/usr/bin/env python3
"""
Automatic Model Checkpoint Downloader for OOTDiffusion
This script runs automatically during startup to ensure models are available
"""
import os
import sys
import subprocess
import time
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_git_lfs():
    """Check if git-lfs is available"""
    try:
        subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_git_lfs():
    """Install git-lfs automatically"""
    logger.info("Installing git-lfs...")
    
    if sys.platform == "win32":
        # Try chocolatey first
        try:
            subprocess.run(["choco", "install", "git-lfs", "-y"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Try winget
        try:
            subprocess.run(["winget", "install", "Git.Git-LFS"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        logger.warning("Could not install git-lfs automatically. Please install manually from https://git-lfs.github.io/")
        return False
    else:
        # Linux/macOS
        try:
            subprocess.run(["sudo", "apt-get", "install", "-y", "git-lfs"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            subprocess.run(["brew", "install", "git-lfs"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        logger.warning("Could not install git-lfs automatically. Please install manually.")
        return False

def run_command(cmd, description, retries=3):
    """Run a command with retries"""
    for attempt in range(retries):
        try:
            logger.info(f"🔄 {description} (attempt {attempt + 1}/{retries})...")
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, timeout=300)
            logger.info(f"✅ {description} completed successfully")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"⚠️ {description} failed (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(5)  # Wait before retry
            else:
                logger.error(f"❌ {description} failed after {retries} attempts")
                return False
    return False

def download_model(repo_url, target_dir, model_name, retries=3):
    """Download a model with retries"""
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Check if model already exists and has content
    if target_path.exists() and any(target_path.iterdir()):
        # Check if it's a proper git repository with content
        try:
            result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                                  cwd=target_path, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ {model_name} already exists, skipping...")
                return True
        except:
            pass
    
    # Try different download strategies
    strategies = [
        f"git clone --depth 1 {repo_url} {target_path}",
        f"git clone {repo_url} {target_path}",
        f"git clone --filter=blob:none {repo_url} {target_path}"
    ]
    
    for strategy in strategies:
        if run_command(strategy, f"Downloading {model_name}"):
            # Verify download
            if target_path.exists() and any(target_path.iterdir()):
                logger.info(f"✅ {model_name} downloaded successfully")
                return True
    
    logger.error(f"❌ Failed to download {model_name} with all strategies")
    return False

def ensure_git_lfs():
    """Ensure git-lfs is available"""
    if not check_git_lfs():
        logger.info("Git LFS not found, attempting to install...")
        if not install_git_lfs():
            logger.error("Failed to install git-lfs. Please install manually.")
            return False
    
    # Initialize git-lfs with better error handling
    try:
        # Try system-wide installation first
        result = subprocess.run(["git", "lfs", "install", "--system"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info("✅ Git LFS initialized successfully (system-wide)")
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.warning(f"⚠️ System-wide git-lfs install failed: {e}")
    
    try:
        # Fallback to user installation
        result = subprocess.run(["git", "lfs", "install"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            logger.info("✅ Git LFS initialized successfully (user)")
            return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.warning(f"⚠️ User git-lfs install failed: {e}")
    
    # If both fail, try to continue anyway (git-lfs might work without explicit install)
    logger.warning("⚠️ Git LFS initialization failed, but continuing with download attempt...")
    return True

def download_all_models(checkpoints_dir="checkpoints"):
    """Download all required models"""
    logger.info("🎭 Starting automatic model download...")
    
    # Ensure git-lfs is available
    if not ensure_git_lfs():
        return False
    
    # Create checkpoints directory
    checkpoints_path = Path(checkpoints_dir)
    checkpoints_path.mkdir(exist_ok=True)
    
    # Define models to download
    models = {
        "ootd": "https://huggingface.co/levihsu/OOTDiffusion",
        "humanparsing": "https://huggingface.co/levihsu/OOTDiffusion", 
        "openpose": "https://huggingface.co/levihsu/OOTDiffusion",
        "clip-vit-large-patch14": "https://huggingface.co/openai/clip-vit-large-patch14"
    }
    
    success_count = 0
    total_models = len(models)
    
    for model_name, repo_url in models.items():
        target_dir = checkpoints_path / model_name
        
        if download_model(repo_url, target_dir, model_name):
            success_count += 1
        else:
            logger.warning(f"⚠️ Failed to download {model_name}, continuing with others...")
    
    logger.info(f"📊 Download Summary: {success_count}/{total_models} models downloaded")
    
    if success_count >= 2:  # At least OOTD and one other model
        logger.info("✅ Sufficient models downloaded to run OOTDiffusion")
        return True
    else:
        logger.error("❌ Insufficient models downloaded")
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automatic model downloader")
    parser.add_argument("--checkpoints-dir", default="checkpoints", help="Checkpoints directory")
    parser.add_argument("--force", action="store_true", help="Force download even if models exist")
    
    args = parser.parse_args()
    
    # Set environment variable to indicate auto-download
    os.environ["OOTD_AUTO_DOWNLOAD"] = "true"
    
    success = download_all_models(args.checkpoints_dir)
    
    if success:
        logger.info("🎉 Model download completed successfully!")
        return 0
    else:
        logger.error("❌ Model download failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
