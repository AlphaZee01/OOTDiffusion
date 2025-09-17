"""
Production-ready FastAPI application for OOTDiffusion
"""
import os
import sys
from pathlib import Path
from typing import List, Optional, Union
import asyncio
import tempfile
import shutil
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn
from PIL import Image
import logging

# Import our modules
from config import config, get_config
from utils.error_handling import (
    OOTDError, ModelLoadError, ProcessingError, ValidationError,
    error_handler, performance_monitor, logger, error_tracker
)
from utils.validation import validator, validate_and_convert_category, create_temp_file

# Import OOTDiffusion models
from ootd.inference_ootd_hd import OOTDiffusionHD
from ootd.inference_ootd_dc import OOTDiffusionDC
from preprocess.openpose.run_openpose import OpenPose
from preprocess.humanparsing.run_parsing import Parsing
from run.utils_ootd import get_mask_location

# Pydantic models for API
class ProcessRequest(BaseModel):
    model_type: str = Field(default="hd", description="Model type: 'hd' or 'dc'")
    category: Union[int, str] = Field(default=0, description="Garment category: 0=upperbody, 1=lowerbody, 2=dress")
    samples: int = Field(default=1, ge=1, le=4, description="Number of samples to generate")
    steps: int = Field(default=20, ge=1, le=40, description="Number of inference steps")
    scale: float = Field(default=2.0, ge=1.0, le=5.0, description="Guidance scale")
    seed: int = Field(default=-1, ge=-1, le=2147483647, description="Random seed (-1 for random)")

class ProcessResponse(BaseModel):
    success: bool
    message: str
    result_paths: Optional[List[str]] = None
    processing_time: Optional[float] = None
    error_code: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: str
    models_loaded: bool
    gpu_available: bool

class ModelManager:
    """Manages model loading and inference"""
    
    def __init__(self):
        self.models = {}
        self.models_loaded = False
        self.load_models()
    
    @error_handler(reraise=True)
    def load_models(self):
        """Load all required models"""
        logger.info("Loading OOTDiffusion models...")
        
        try:
            # Load OpenPose and Parsing models
            self.models['openpose_hd'] = OpenPose(0)
            self.models['parsing_hd'] = Parsing(0)
            self.models['ootd_hd'] = OOTDiffusionHD(0)
            
            # Load DC models on different GPU if available
            gpu_id = 1 if self._is_cuda_available() and self._get_gpu_count() > 1 else 0
            self.models['openpose_dc'] = OpenPose(gpu_id)
            self.models['parsing_dc'] = Parsing(gpu_id)
            self.models['ootd_dc'] = OOTDiffusionDC(gpu_id)
            
            self.models_loaded = True
            logger.info("All models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise ModelLoadError(f"Failed to load models: {e}", "all_models")
    
    def _is_cuda_available(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _get_gpu_count(self) -> int:
        """Get number of available GPUs"""
        try:
            import torch
            return torch.cuda.device_count()
        except:
            return 0
    
    @performance_monitor
    @error_handler(reraise=True)
    def process_image(self, model_path: str, cloth_path: str, request: ProcessRequest) -> List[str]:
        """Process image with OOTDiffusion"""
        
        # Validate inputs
        is_valid, errors = validator.validate_request({
            'model_path': model_path,
            'cloth_path': cloth_path,
            'model_type': request.model_type,
            'category': request.category,
            'samples': request.samples,
            'steps': request.steps,
            'scale': request.scale,
            'seed': request.seed
        })
        
        if not is_valid:
            raise ValidationError(f"Invalid request: {', '.join(errors)}", "request")
        
        # Convert category to integer
        category = validate_and_convert_category(request.category, request.model_type)
        
        # Load and process images
        model_img = Image.open(model_path).resize((768, 1024))
        cloth_img = Image.open(cloth_path).resize((768, 1024))
        
        # Get appropriate models
        if request.model_type == 'hd':
            openpose_model = self.models['openpose_hd']
            parsing_model = self.models['parsing_hd']
            ootd_model = self.models['ootd_hd']
        else:
            openpose_model = self.models['openpose_dc']
            parsing_model = self.models['parsing_dc']
            ootd_model = self.models['ootd_dc']
        
        # Process with OpenPose and Parsing
        keypoints = openpose_model(model_img.resize((384, 512)))
        model_parse, _ = parsing_model(model_img.resize((384, 512)))
        
        # Get mask
        category_dict_utils = ['upper_body', 'lower_body', 'dresses']
        mask, mask_gray = get_mask_location(
            request.model_type, 
            category_dict_utils[category], 
            model_parse, 
            keypoints
        )
        
        mask = mask.resize((768, 1024), Image.NEAREST)
        mask_gray = mask_gray.resize((768, 1024), Image.NEAREST)
        
        masked_model_img = Image.composite(mask_gray, model_img, mask)
        
        # Generate images
        category_dict = ['upperbody', 'lowerbody', 'dress']
        images = ootd_model(
            model_type=request.model_type,
            category=category_dict[category],
            image_garm=cloth_img,
            image_vton=masked_model_img,
            mask=mask,
            image_ori=model_img,
            num_samples=request.samples,
            num_steps=request.steps,
            image_scale=request.scale,
            seed=request.seed,
        )
        
        # Save results
        result_paths = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, img in enumerate(images):
            result_filename = f"result_{timestamp}_{i}.png"
            result_path = config.output_dir / "results" / result_filename
            result_path.parent.mkdir(parents=True, exist_ok=True)
            
            img.save(result_path, "PNG", quality=config.processing.image_quality)
            result_paths.append(str(result_path))
        
        return result_paths

# Initialize FastAPI app
app = FastAPI(
    title="OOTDiffusion API",
    description="Production-ready API for Outfitting Fusion based Latent Diffusion",
    version="1.0.0",
    docs_url="/docs" if config.debug else None,
    redoc_url="/redoc" if config.debug else None
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files
app.mount("/static", StaticFiles(directory=str(config.output_dir)), name="static")

# Initialize model manager
model_manager = ModelManager()

# Dependency to get model manager
def get_model_manager() -> ModelManager:
    if not model_manager.models_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")
    return model_manager

@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "OOTDiffusion API",
        "version": "1.0.0",
        "docs": "/docs" if config.debug else "disabled",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import torch
    
    return HealthResponse(
        status="healthy" if model_manager.models_loaded else "unhealthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        environment=config.environment,
        models_loaded=model_manager.models_loaded,
        gpu_available=torch.cuda.is_available() if 'torch' in sys.modules else False
    )

@app.post("/process", response_model=ProcessResponse)
@app.post("/tryon", response_model=ProcessResponse)
async def process_images(
    background_tasks: BackgroundTasks,
    model_file: UploadFile = File(..., description="Model image file"),
    cloth_file: UploadFile = File(..., description="Cloth image file"),
    request: ProcessRequest = Depends(),
    model_manager: ModelManager = Depends(get_model_manager)
):
    """Process images with OOTDiffusion"""
    
    start_time = datetime.now()
    model_temp_path = None
    cloth_temp_path = None
    
    try:
        # Validate uploaded files
        if not model_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Model file must be an image")
        
        if not cloth_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Cloth file must be an image")
        
        # Create temporary files
        model_temp_path = create_temp_file(model_file.filename)
        cloth_temp_path = create_temp_file(cloth_file.filename)
        
        # Save uploaded files
        with open(model_temp_path, "wb") as buffer:
            shutil.copyfileobj(model_file.file, buffer)
        
        with open(cloth_temp_path, "wb") as buffer:
            shutil.copyfileobj(cloth_file.file, buffer)
        
        # Process images
        result_paths = model_manager.process_image(
            str(model_temp_path),
            str(cloth_temp_path),
            request
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_files, [model_temp_path, cloth_temp_path])
        
        return ProcessResponse(
            success=True,
            message="Images processed successfully",
            result_paths=result_paths,
            processing_time=processing_time
        )
        
    except ValidationError as e:
        logger.error(f"Validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    
    except ProcessingError as e:
        logger.error(f"Processing error: {e.message}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {e.message}")
    
    except OOTDError as e:
        logger.error(f"OOTD error: {e.message}")
        raise HTTPException(status_code=500, detail=f"Error: {e.message}")
    
    except Exception as e:
        error_tracker.track_error(e, {
            "endpoint": "process",
            "model_filename": model_file.filename,
            "cloth_filename": cloth_file.filename
        })
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    finally:
        # Cleanup on error
        if model_temp_path and model_temp_path.exists():
            model_temp_path.unlink()
        if cloth_temp_path and cloth_temp_path.exists():
            cloth_temp_path.unlink()

@app.get("/results/{filename}")
async def get_result(filename: str):
    """Get processed result image"""
    result_path = config.output_dir / "results" / filename
    
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Result not found")
    
    return FileResponse(result_path)

async def cleanup_temp_files(file_paths: List[Path]):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to cleanup {file_path}: {e}")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.logging.level.upper()),
        format=config.logging.format
    )
    
    # Run server
    uvicorn.run(
        "api.app:app",
        host=config.server.host,
        port=config.server.port,
        workers=config.server.workers,
        log_level=config.logging.level.lower()
    )
