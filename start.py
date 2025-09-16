#!/usr/bin/env python3
"""
OOTDiffusion Production Startup Script
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).absolute().parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_and_download_models():
    """Check if models exist and download them if needed"""
    from pathlib import Path
    
    checkpoints_dir = Path("checkpoints")
    required_models = ["ootd", "humanparsing", "openpose", "clip-vit-large-patch14"]
    
    # Check if all models exist
    missing_models = []
    for model in required_models:
        model_path = checkpoints_dir / model
        if not model_path.exists() or not any(model_path.iterdir()):
            missing_models.append(model)
    
    if missing_models:
        print(f"📥 Missing models: {', '.join(missing_models)}")
        print("🔄 Starting automatic model download...")
        
        # Run the auto-download script
        import subprocess
        try:
            result = subprocess.run([
                sys.executable, "scripts/auto_download_models.py"
            ], check=True, capture_output=True, text=True)
            print("✅ Models downloaded successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Model download failed: {e}")
            print("Please run: python scripts/download_models.py")
            return False
    else:
        print("✅ All models are available")
        return True

def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(description="Start OOTDiffusion in different modes")
    parser.add_argument(
        "--mode", 
        choices=["api", "gradio", "test"], 
        default="api",
        help="Startup mode (default: api)"
    )
    parser.add_argument(
        "--environment",
        choices=["development", "testing", "production"],
        default="production",
        help="Environment mode (default: production)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7865,
        help="Port to bind to (default: 7865)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of workers (default: 1)"
    )
    parser.add_argument(
        "--skip-model-check",
        action="store_true",
        help="Skip automatic model download check"
    )
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["OOTD_ENVIRONMENT"] = args.environment
    os.environ["OOTD_HOST"] = args.host
    os.environ["OOTD_PORT"] = str(args.port)
    os.environ["OOTD_WORKERS"] = str(args.workers)
    
    # Check and download models if needed (except for test mode)
    if not args.skip_model_check and args.mode != "test":
        if not check_and_download_models():
            print("⚠️  Continuing without all models. Some features may not work.")
    
    if args.mode == "api":
        start_api()
    elif args.mode == "gradio":
        start_gradio()
    elif args.mode == "test":
        start_tests()

def start_api():
    """Start FastAPI server"""
    print("🚀 Starting OOTDiffusion API server...")
    
    try:
        import uvicorn
        from api.app import app
        from config import config
        
        uvicorn.run(
            app,
            host=config.server.host,
            port=config.server.port,
            workers=config.server.workers,
            log_level=config.logging.level.lower()
        )
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Please install production dependencies: pip install -r requirements-prod.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting API: {e}")
        sys.exit(1)

def start_gradio():
    """Start Gradio interface (legacy)"""
    print("🚀 Starting OOTDiffusion Gradio interface...")
    
    try:
        import subprocess
        subprocess.run([
            sys.executable, 
            "run/gradio_ootd.py"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Gradio: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

def start_tests():
    """Run test suite"""
    print("🧪 Running OOTDiffusion test suite...")
    
    try:
        import subprocess
        subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", "-v", "--tb=short"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
