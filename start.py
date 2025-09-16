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
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["OOTD_ENVIRONMENT"] = args.environment
    os.environ["OOTD_HOST"] = args.host
    os.environ["OOTD_PORT"] = str(args.port)
    os.environ["OOTD_WORKERS"] = str(args.workers)
    
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
