#!/usr/bin/env python3
"""
OOTDiffusion Inference Function for RunPod
"""
import os
import sys
import base64
import tempfile
from pathlib import Path
from PIL import Image
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils_ootd import get_mask_location
from preprocess.openpose.run_openpose import OpenPose
from preprocess.humanparsing.run_parsing import Parsing
from ootd.inference_ootd_hd import OOTDiffusionHD
from ootd.inference_ootd_dc import OOTDiffusionDC

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instances (initialized once)
openpose_model = None
parsing_model = None
hd_model = None
dc_model = None

def initialize_models(gpu_id=0):
    """Initialize models once"""
    global openpose_model, parsing_model, hd_model, dc_model
    
    if openpose_model is None:
        logger.info("Initializing OpenPose model...")
        openpose_model = OpenPose(gpu_id)
    
    if parsing_model is None:
        logger.info("Initializing Parsing model...")
        parsing_model = Parsing(gpu_id)
    
    if hd_model is None:
        logger.info("Initializing OOTDiffusion HD model...")
        hd_model = OOTDiffusionHD(gpu_id)
    
    if dc_model is None:
        logger.info("Initializing OOTDiffusion DC model...")
        dc_model = OOTDiffusionDC(gpu_id)

def base64_to_image(base64_string):
    """Convert base64 string to PIL Image"""
    import io
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        image_data = base64.b64decode(base64_string)
        
        # Create PIL Image
        image = Image.open(io.BytesIO(image_data))
        return image
    except Exception as e:
        logger.error(f"Error converting base64 to image: {e}")
        raise ValueError(f"Invalid base64 image data: {e}")

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    import io
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

def inference(user_image, cloth_image, garment_type="upper", model_type="hd", 
             category=0, scale=2.0, steps=20, samples=1, seed=-1, gpu_id=0):
    """
    Main inference function for OOTDiffusion
    
    Args:
        user_image: Base64 encoded user image or PIL Image
        cloth_image: Base64 encoded cloth image or PIL Image  
        garment_type: "upper", "lower", or "dress"
        model_type: "hd" or "dc"
        category: 0=upperbody, 1=lowerbody, 2=dress
        scale: Guidance scale
        steps: Number of inference steps
        samples: Number of samples to generate
        seed: Random seed (-1 for random)
        gpu_id: GPU ID to use
    
    Returns:
        List of base64 encoded result images
    """
    try:
        # Initialize models if not already done
        initialize_models(gpu_id)
        
        # Convert garment_type to category if needed
        if garment_type == "upper":
            category = 0
        elif garment_type == "lower":
            category = 1
        elif garment_type == "dress":
            category = 2
        
        # Validate model_type and category combination
        if model_type == 'hd' and category != 0:
            raise ValueError("model_type 'hd' requires category == 0 (upperbody)!")
        
        # Convert inputs to PIL Images
        if isinstance(user_image, str):
            user_img = base64_to_image(user_image)
        else:
            user_img = user_image
            
        if isinstance(cloth_image, str):
            cloth_img = base64_to_image(cloth_image)
        else:
            cloth_img = cloth_image
        
        # Resize images
        cloth_img = cloth_img.resize((768, 1024))
        user_img = user_img.resize((768, 1024))
        
        # Get keypoints and parsing
        logger.info("Processing user image...")
        keypoints = openpose_model(user_img.resize((384, 512)))
        model_parse, _ = parsing_model(user_img.resize((384, 512)))
        
        # Get mask
        category_dict_utils = ['upper_body', 'lower_body', 'dresses']
        mask, mask_gray = get_mask_location(model_type, category_dict_utils[category], model_parse, keypoints)
        mask = mask.resize((768, 1024), Image.NEAREST)
        mask_gray = mask_gray.resize((768, 1024), Image.NEAREST)
        
        # Create masked image
        masked_vton_img = Image.composite(mask_gray, user_img, mask)
        
        # Select model
        if model_type == "hd":
            model = hd_model
        elif model_type == "dc":
            model = dc_model
        else:
            raise ValueError("model_type must be 'hd' or 'dc'!")
        
        # Run inference
        logger.info(f"Running inference with {model_type} model...")
        category_dict = ['upperbody', 'lowerbody', 'dress']
        images = model(
            model_type=model_type,
            category=category_dict[category],
            image_garm=cloth_img,
            image_vton=masked_vton_img,
            mask=mask,
            image_ori=user_img,
            num_samples=samples,
            num_steps=steps,
            image_scale=scale,
            seed=seed,
        )
        
        # Convert results to base64
        result_images = []
        for i, image in enumerate(images):
            base64_img = image_to_base64(image)
            result_images.append(base64_img)
        
        logger.info(f"Generated {len(result_images)} result images")
        return result_images
        
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        raise e

if __name__ == "__main__":
    # Test the inference function
    import argparse
    parser = argparse.ArgumentParser(description='Test OOTDiffusion inference')
    parser.add_argument('--user_image', type=str, required=True, help='Path to user image')
    parser.add_argument('--cloth_image', type=str, required=True, help='Path to cloth image')
    parser.add_argument('--garment_type', type=str, default='upper', help='Garment type: upper, lower, dress')
    parser.add_argument('--model_type', type=str, default='hd', help='Model type: hd, dc')
    parser.add_argument('--gpu_id', type=int, default=0, help='GPU ID')
    
    args = parser.parse_args()
    
    # Load images
    user_img = Image.open(args.user_image)
    cloth_img = Image.open(args.cloth_image)
    
    # Run inference
    results = inference(user_img, cloth_img, args.garment_type, args.model_type, gpu_id=args.gpu_id)
    
    # Save results
    for i, result_base64 in enumerate(results):
        result_img = base64_to_image(result_base64)
        result_img.save(f'./result_{i}.png')
        print(f"Saved result_{i}.png")
