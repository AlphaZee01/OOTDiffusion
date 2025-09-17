#!/usr/bin/env python3
"""
RunPod Serverless Handler for OOTDiffusion
Simplified handler following RunPod best practices
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import RunPod
try:
    import runpod
except ImportError:
    logger.error("RunPod not installed. Install with: pip install runpod")
    sys.exit(1)

# Global variables for model caching
models_initialized = False
inference_function = None

def initialize_models():
    """Initialize models once on startup"""
    global models_initialized, inference_function
    
    if models_initialized:
        return True
    
    try:
        logger.info("Initializing OOTDiffusion models...")
        
        # Import inference function
        from run.inference import inference
        inference_function = inference
        
        # Initialize models with CPU device for RunPod compatibility
        inference(
            user_image="dummy",  # Will be replaced in actual calls
            cloth_image="dummy",
            garment_type="upper",
            model_type="hd",
            gpu_id=0
        )
        
        models_initialized = True
        logger.info("✅ Models initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize models: {e}")
        logger.error(traceback.format_exc())
        return False

def handler(job):
    """
    RunPod serverless handler function
    
    Expected input format:
    {
        "input": {
            "user_image": "base64_encoded_image",
            "cloth_image": "base64_encoded_image", 
            "garment_type": "upper",  # optional
            "model_type": "hd",       # optional
            "category": 0,            # optional
            "scale": 2.0,             # optional
            "steps": 20,              # optional
            "samples": 1,             # optional
            "seed": -1,               # optional
            "gpu_id": 0               # optional
        }
    }
    """
    try:
        # Initialize models if not already done
        if not models_initialized:
            if not initialize_models():
                return {
                    "error": "Failed to initialize models"
                }
        
        # Extract inputs
        inputs = job.get("input", {})
        
        # Required inputs
        user_image = inputs.get("user_image")
        cloth_image = inputs.get("cloth_image")
        
        if not user_image:
            return {
                "error": "Missing required input: user_image"
            }
        
        if not cloth_image:
            return {
                "error": "Missing required input: cloth_image"
            }
        
        # Optional inputs with defaults
        garment_type = inputs.get("garment_type", "upper")
        model_type = inputs.get("model_type", "hd")
        category = inputs.get("category", 0)
        scale = inputs.get("scale", 2.0)
        steps = inputs.get("steps", 20)
        samples = inputs.get("samples", 1)
        seed = inputs.get("seed", -1)
        gpu_id = inputs.get("gpu_id", 0)
        
        logger.info(f"Processing request: garment_type={garment_type}, model_type={model_type}, samples={samples}")
        
        # Run inference
        result_images = inference_function(
            user_image=user_image,
            cloth_image=cloth_image,
            garment_type=garment_type,
            model_type=model_type,
            category=category,
            scale=scale,
            steps=steps,
            samples=samples,
            seed=seed,
            gpu_id=gpu_id
        )
        
        logger.info(f"Generated {len(result_images)} result images")
        
        return {
            "output": {
                "success": True,
                "images": result_images,
                "message": f"Successfully generated {len(result_images)} result image(s)",
                "parameters": {
                    "garment_type": garment_type,
                    "model_type": model_type,
                    "category": category,
                    "scale": scale,
                    "steps": steps,
                    "samples": samples,
                    "seed": seed
                }
            }
        }
        
    except Exception as e:
        error_msg = f"Handler error: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        return {
            "error": error_msg,
            "traceback": traceback.format_exc()
        }

# Initialize models on module load
logger.info("Starting OOTDiffusion RunPod serverless handler...")
initialize_models()

# Start the RunPod serverless handler
if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
