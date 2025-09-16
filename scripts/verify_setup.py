#!/usr/bin/env python3
"""
Setup Verification Script for OOTDiffusion
Ensures everything is properly configured for smooth hosting
"""
import os
import sys
import subprocess
import platform
from pathlib import Path
import json

def print_status(message, status="info"):
    """Print status message with emoji"""
    emojis = {
        "success": "✅",
        "error": "❌", 
        "warning": "⚠️",
        "info": "ℹ️"
    }
    print(f"{emojis.get(status, 'ℹ️')} {message}")

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Compatible", "success")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+", "error")
        return False

def check_git():
    """Check if git is available"""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Git is available", "success")
            return True
    except FileNotFoundError:
        pass
    
    print_status("Git not found - Required for model downloads", "error")
    return False

def check_git_lfs():
    """Check if git-lfs is available"""
    try:
        result = subprocess.run(["git", "lfs", "version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Git LFS is available", "success")
            return True
    except FileNotFoundError:
        pass
    
    print_status("Git LFS not found - Required for large model files", "warning")
    print_status("Install from: https://git-lfs.github.io/", "info")
    return False

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Docker is available", "success")
            return True
    except FileNotFoundError:
        pass
    
    print_status("Docker not found - Optional for containerized deployment", "warning")
    return False

def check_docker_compose():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print_status("Docker Compose is available", "success")
            return True
    except FileNotFoundError:
        pass
    
    print_status("Docker Compose not found - Optional for containerized deployment", "warning")
    return False

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        "torch", "transformers", "diffusers", "fastapi", 
        "uvicorn", "pillow", "numpy", "opencv-python"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print_status(f"Missing packages: {', '.join(missing_packages)}", "warning")
        print_status("Run: pip install -r requirements-prod.txt", "info")
        return False
    else:
        print_status("All required packages are installed", "success")
        return True

def check_models():
    """Check if model checkpoints exist"""
    checkpoints_dir = Path("checkpoints")
    required_models = ["ootd", "humanparsing", "openpose", "clip-vit-large-patch14"]
    
    missing_models = []
    for model in required_models:
        model_path = checkpoints_dir / model
        if not model_path.exists() or not any(model_path.iterdir()):
            missing_models.append(model)
    
    if missing_models:
        print_status(f"Missing models: {', '.join(missing_models)}", "warning")
        print_status("Models will download automatically on first run", "info")
        return False
    else:
        print_status("All model checkpoints are available", "success")
        return True

def check_disk_space():
    """Check available disk space"""
    try:
        if platform.system() == "Windows":
            import shutil
            free_space = shutil.disk_usage(".").free
        else:
            import os
            statvfs = os.statvfs(".")
            free_space = statvfs.f_frsize * statvfs.f_bavail
        
        # Convert to GB
        free_gb = free_space / (1024**3)
        
        if free_gb >= 20:
            print_status(f"Disk space: {free_gb:.1f} GB available - Sufficient", "success")
            return True
        elif free_gb >= 10:
            print_status(f"Disk space: {free_gb:.1f} GB available - Minimum required", "warning")
            return True
        else:
            print_status(f"Disk space: {free_gb:.1f} GB available - Insufficient (need 10+ GB)", "error")
            return False
    except Exception as e:
        print_status(f"Could not check disk space: {e}", "warning")
        return True

def check_network():
    """Check network connectivity to required services"""
    import urllib.request
    import socket
    
    services = [
        ("Hugging Face", "huggingface.co"),
        ("GitHub", "github.com"),
        ("PyPI", "pypi.org")
    ]
    
    for name, host in services:
        try:
            socket.create_connection((host, 80), timeout=5)
            print_status(f"Network: {name} reachable", "success")
        except OSError:
            print_status(f"Network: {name} not reachable", "warning")

def check_ports():
    """Check if required ports are available"""
    import socket
    
    ports_to_check = [7865, 7866]  # API ports
    
    for port in ports_to_check:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                print_status(f"Port {port} is available", "success")
        except OSError:
            print_status(f"Port {port} is in use", "warning")

def create_startup_script():
    """Create a startup script for easy hosting"""
    if platform.system() == "Windows":
        script_content = '''@echo off
echo Starting OOTDiffusion...
python quick_start.py
pause
'''
        script_path = "start_ootd.bat"
    else:
        script_content = '''#!/bin/bash
echo "Starting OOTDiffusion..."
python3 quick_start.py
'''
        script_path = "start_ootd.sh"
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    if platform.system() != "Windows":
        os.chmod(script_path, 0o755)
    
    print_status(f"Created startup script: {script_path}", "success")

def create_env_file():
    """Create a default .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# OOTDiffusion Environment Configuration
OOTD_ENVIRONMENT=production
OOTD_DEBUG=false
OOTD_HOST=0.0.0.0
OOTD_PORT=7865
OOTD_WORKERS=1
OOTD_DEVICE=cuda:0
OOTD_TORCH_DTYPE=float16
OOTD_LOG_LEVEL=INFO
OOTD_MAX_FILE_SIZE=10485760
OOTD_ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.bmp
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print_status("Created default .env file", "success")
    else:
        print_status(".env file already exists", "info")

def main():
    """Main verification function"""
    print("=" * 60)
    print("🎭 OOTDiffusion - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Git", check_git),
        ("Git LFS", check_git_lfs),
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("Dependencies", check_dependencies),
        ("Models", check_models),
        ("Disk Space", check_disk_space),
        ("Network", check_network),
        ("Ports", check_ports)
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        results[name] = check_func()
    
    print("\n" + "=" * 60)
    print("📊 Verification Summary")
    print("=" * 60)
    
    critical_checks = ["Python Version", "Git", "Dependencies", "Disk Space"]
    optional_checks = ["Git LFS", "Docker", "Docker Compose", "Models", "Network", "Ports"]
    
    critical_passed = all(results.get(check, False) for check in critical_checks)
    optional_passed = sum(1 for check in optional_checks if results.get(check, False))
    total_optional = len(optional_checks)
    
    print(f"Critical checks: {'✅ PASSED' if critical_passed else '❌ FAILED'}")
    print(f"Optional checks: {optional_passed}/{total_optional} passed")
    
    if critical_passed:
        print_status("Setup verification PASSED - Ready for hosting!", "success")
        
        # Create helpful files
        create_startup_script()
        create_env_file()
        
        print("\n🚀 Quick Start Commands:")
        print("  python quick_start.py          # One-command setup")
        print("  docker-compose up -d           # Docker deployment")
        print("  python start.py --mode api     # Start API only")
        
        print("\n📖 Documentation:")
        print("  README-HOSTING.md              # Hosting guide")
        print("  test_interface.html            # Test interface")
        print("  http://localhost:7865/docs     # API documentation")
        
        return 0
    else:
        print_status("Setup verification FAILED - Please fix critical issues", "error")
        return 1

if __name__ == "__main__":
    sys.exit(main())
