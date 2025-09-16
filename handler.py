#!/usr/bin/env python3
"""
RunPod Handler for OOTDiffusion
Production-ready handler script for RunPod deployment
"""

import os
import sys
import json
import asyncio
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
import uvicorn
from contextlib import asynccontextmanager

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/workspace/logs/runpod.log')
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs('/workspace/logs', exist_ok=True)

class RunPodHandler:
    """Handler for RunPod requests"""
    
    def __init__(self):
        self.app = None
        self.model_manager = None
        self.setup_complete = False
        
    async def setup(self):
        """Setup the application and models"""
        try:
            logger.info("Starting OOTDiffusion RunPod handler setup...")
            
            # Set environment variables for RunPod
            os.environ.setdefault('OOTD_HOST', '0.0.0.0')
            os.environ.setdefault('OOTD_PORT', '8000')
            os.environ.setdefault('OOTD_WORKERS', '1')
            os.environ.setdefault('OOTD_DEVICE', 'cuda:0')
            os.environ.setdefault('OOTD_TORCH_DTYPE', 'float16')
            os.environ.setdefault('OOTD_ENVIRONMENT', 'production')
            os.environ.setdefault('OOTD_DEBUG', 'false')
            
            # Set PyTorch CUDA memory allocation
            os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'max_split_size_mb:512')
            
            # Import and initialize the FastAPI app
            from api.app import app, model_manager
            
            self.app = app
            self.model_manager = model_manager
            
            # Wait for models to load
            logger.info("Waiting for models to load...")
            max_wait_time = 300  # 5 minutes
            wait_time = 0
            while not model_manager.models_loaded and wait_time < max_wait_time:
                await asyncio.sleep(5)
                wait_time += 5
                logger.info(f"Waiting for models... ({wait_time}s)")
            
            if not model_manager.models_loaded:
                raise RuntimeError("Models failed to load within timeout period")
            
            logger.info("All models loaded successfully")
            self.setup_complete = True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def handler(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Main handler function for RunPod requests"""
        try:
            if not self.setup_complete:
                await self.setup()
            
            # Extract request data
            input_data = event.get('input', {})
            method = input_data.get('method', 'POST')
            endpoint = input_data.get('endpoint', '/process')
            
            # Handle different endpoints
            if endpoint == '/health':
                return await self._handle_health()
            elif endpoint == '/process':
                return await self._handle_process(input_data)
            elif endpoint == '/docs':
                return await self._handle_docs()
            else:
                return {
                    'error': f'Unknown endpoint: {endpoint}',
                    'status': 'error'
                }
                
        except Exception as e:
            logger.error(f"Handler error: {e}")
            logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'status': 'error',
                'traceback': traceback.format_exc()
            }
    
    async def _handle_health(self) -> Dict[str, Any]:
        """Handle health check requests"""
        try:
            import torch
            from datetime import datetime
            
            return {
                'status': 'healthy' if self.model_manager.models_loaded else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'environment': 'production',
                'models_loaded': self.model_manager.models_loaded,
                'gpu_available': torch.cuda.is_available() if 'torch' in sys.modules else False,
                'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _handle_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle image processing requests"""
        try:
            # Extract parameters
            model_type = input_data.get('model_type', 'hd')
            category = input_data.get('category', 0)
            samples = input_data.get('samples', 1)
            steps = input_data.get('steps', 20)
            scale = input_data.get('scale', 2.0)
            seed = input_data.get('seed', -1)
            
            # Handle file uploads
            model_file = input_data.get('model_file')
            cloth_file = input_data.get('cloth_file')
            
            if not model_file or not cloth_file:
                return {
                    'error': 'Both model_file and cloth_file are required',
                    'status': 'error'
                }
            
            # Create temporary files
            import tempfile
            import shutil
            from PIL import Image
            import io
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as model_temp:
                if isinstance(model_file, str):
                    # Base64 encoded or file path
                    if model_file.startswith('data:image'):
                        import base64
                        header, data = model_file.split(',', 1)
                        model_temp.write(base64.b64decode(data))
                    else:
                        shutil.copy2(model_file, model_temp.name)
                else:
                    # File object
                    model_temp.write(model_file)
                model_path = model_temp.name
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as cloth_temp:
                if isinstance(cloth_file, str):
                    if cloth_file.startswith('data:image'):
                        import base64
                        header, data = cloth_file.split(',', 1)
                        cloth_temp.write(base64.b64decode(data))
                    else:
                        shutil.copy2(cloth_file, cloth_temp.name)
                else:
                    cloth_temp.write(cloth_file)
                cloth_path = cloth_temp.name
            
            try:
                # Create request object
                from api.app import ProcessRequest
                request = ProcessRequest(
                    model_type=model_type,
                    category=category,
                    samples=samples,
                    steps=steps,
                    scale=scale,
                    seed=seed
                )
                
                # Process images
                from datetime import datetime
                start_time = datetime.now()
                
                result_paths = self.model_manager.process_image(
                    model_path,
                    cloth_path,
                    request
                )
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Read result images
                result_images = []
                for result_path in result_paths:
                    with open(result_path, 'rb') as f:
                        import base64
                        result_images.append(base64.b64encode(f.read()).decode())
                
                return {
                    'success': True,
                    'message': 'Images processed successfully',
                    'result_images': result_images,
                    'result_paths': result_paths,
                    'processing_time': processing_time,
                    'status': 'success'
                }
                
            finally:
                # Clean up temporary files
                try:
                    os.unlink(model_path)
                    os.unlink(cloth_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Process error: {e}")
            logger.error(traceback.format_exc())
            return {
                'error': str(e),
                'status': 'error',
                'traceback': traceback.format_exc()
            }
    
    async def _handle_docs(self) -> Dict[str, Any]:
        """Handle API documentation requests"""
        return {
            'message': 'API Documentation',
            'endpoints': {
                '/health': 'GET - Health check',
                '/process': 'POST - Process images',
                '/docs': 'GET - API documentation'
            },
            'status': 'success'
        }

# Global handler instance
handler_instance = RunPodHandler()

async def main():
    """Main function to start the handler"""
    try:
        await handler_instance.setup()
        
        # Start the FastAPI server
        config = uvicorn.Config(
            app=handler_instance.app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        
        logger.info("Starting OOTDiffusion API server on port 8000...")
        await server.serve()
        
    except Exception as e:
        logger.error(f"Failed to start handler: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

def runpod_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """Synchronous wrapper for RunPod"""
    try:
        # Create new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(handler_instance.handler(event))
        loop.close()
        
        return result
        
    except Exception as e:
        logger.error(f"RunPod handler error: {e}")
        logger.error(traceback.format_exc())
        return {
            'error': str(e),
            'status': 'error',
            'traceback': traceback.format_exc()
        }

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())

