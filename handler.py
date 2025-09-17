#!/usr/bin/env python3
"""
RunPod Serverless Handler for OOTDiffusion
Production-ready handler script for RunPod serverless deployment
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import RunPod
try:
    import runpod
except ImportError:
    logger.error("RunPod not installed. Install with: pip install runpod")
    sys.exit(1)

# Import our inference function
from run.inference import inference

def handler(job):
    """
    RunPod serverless handler function
    
    Expected input format:
    {
        "input": {
            "user_image": "base64_encoded_image",
            "cloth_image": "base64_encoded_image", 
            "garment_type": "upper",  # optional: "upper", "lower", "dress"
            "model_type": "hd",       # optional: "hd", "dc"
            "category": 0,            # optional: 0=upperbody, 1=lowerbody, 2=dress
            "scale": 2.0,             # optional: guidance scale
            "steps": 20,              # optional: inference steps
            "samples": 1,             # optional: number of samples
            "seed": -1,               # optional: random seed (-1 for random)
            "gpu_id": 0               # optional: GPU ID
        }
    }
    
    Returns:
    {
        "output": {
            "success": True,
            "images": ["base64_encoded_result1", "base64_encoded_result2", ...],
            "message": "Processing completed successfully"
        }
    }
    """
    try:
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
        result_images = inference(
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

if __name__ == "__main__":
    # Start the RunPod serverless handler
    logger.info("Starting OOTDiffusion RunPod serverless handler...")
    runpod.serverless.start({"handler": handler})