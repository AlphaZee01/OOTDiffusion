"""
Input validation utilities for OOTDiffusion
"""
import os
from pathlib import Path
from typing import Union, List, Optional, Tuple
from PIL import Image
import magic
import logging

from config import config
from utils.error_handling import ValidationError, logger

class InputValidator:
    """Comprehensive input validation for OOTDiffusion"""
    
    def __init__(self):
        self.allowed_extensions = config.server.allowed_extensions
        self.max_file_size = config.server.max_file_size
        self.max_dimensions = (4096, 4096)  # Maximum image dimensions
        self.min_dimensions = (64, 64)      # Minimum image dimensions
    
    def validate_image_file(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate image file
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                return False, f"File does not exist: {file_path}"
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                return False, f"File too large: {file_size} bytes (max: {self.max_file_size})"
            
            # Check file extension
            if file_path.suffix.lower() not in self.allowed_extensions:
                return False, f"Invalid file extension: {file_path.suffix} (allowed: {self.allowed_extensions})"
            
            # Check MIME type
            mime_type = magic.from_file(str(file_path), mime=True)
            if not mime_type.startswith('image/'):
                return False, f"File is not an image: {mime_type}"
            
            # Try to open as image
            try:
                with Image.open(file_path) as img:
                    # Check image dimensions
                    width, height = img.size
                    if width < self.min_dimensions[0] or height < self.min_dimensions[1]:
                        return False, f"Image too small: {width}x{height} (min: {self.min_dimensions[0]}x{self.min_dimensions[1]})"
                    
                    if width > self.max_dimensions[0] or height > self.max_dimensions[1]:
                        return False, f"Image too large: {width}x{height} (max: {self.max_dimensions[0]}x{self.max_dimensions[1]})"
                    
                    # Check if image can be loaded
                    img.verify()
                
                return True, "Valid image file"
                
            except Exception as e:
                return False, f"Invalid image file: {str(e)}"
                
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def validate_model_path(self, model_path: Union[str, Path]) -> Tuple[bool, str]:
        """Validate model image path"""
        return self.validate_image_file(model_path)
    
    def validate_cloth_path(self, cloth_path: Union[str, Path]) -> Tuple[bool, str]:
        """Validate cloth image path"""
        return self.validate_image_file(cloth_path)
    
    def validate_model_type(self, model_type: str) -> Tuple[bool, str]:
        """Validate model type"""
        valid_types = ['hd', 'dc']
        if model_type not in valid_types:
            return False, f"Invalid model type: {model_type} (valid: {valid_types})"
        return True, "Valid model type"
    
    def validate_category(self, category: Union[int, str], model_type: str = 'dc') -> Tuple[bool, str]:
        """Validate garment category"""
        if model_type == 'hd':
            # HD model only supports upperbody (category 0)
            if category != 0 and category != 'upperbody':
                return False, "HD model only supports upperbody garments"
            return True, "Valid category for HD model"
        
        elif model_type == 'dc':
            # DC model supports 0=upperbody, 1=lowerbody, 2=dress
            valid_categories = [0, 1, 2, 'upperbody', 'lowerbody', 'dress']
            if category not in valid_categories:
                return False, f"Invalid category: {category} (valid: {valid_categories})"
            return True, "Valid category for DC model"
        
        return False, f"Unknown model type: {model_type}"
    
    def validate_samples(self, samples: int) -> Tuple[bool, str]:
        """Validate number of samples"""
        if not isinstance(samples, int):
            return False, f"Samples must be an integer, got: {type(samples)}"
        
        if samples < 1:
            return False, f"Samples must be at least 1, got: {samples}"
        
        if samples > config.processing.max_samples:
            return False, f"Samples too high: {samples} (max: {config.processing.max_samples})"
        
        return True, "Valid samples count"
    
    def validate_steps(self, steps: int) -> Tuple[bool, str]:
        """Validate number of inference steps"""
        if not isinstance(steps, int):
            return False, f"Steps must be an integer, got: {type(steps)}"
        
        if steps < 1:
            return False, f"Steps must be at least 1, got: {steps}"
        
        if steps > config.processing.max_steps:
            return False, f"Steps too high: {steps} (max: {config.processing.max_steps})"
        
        return True, "Valid steps count"
    
    def validate_scale(self, scale: float) -> Tuple[bool, str]:
        """Validate guidance scale"""
        if not isinstance(scale, (int, float)):
            return False, f"Scale must be a number, got: {type(scale)}"
        
        if scale < config.processing.min_scale:
            return False, f"Scale too low: {scale} (min: {config.processing.min_scale})"
        
        if scale > config.processing.max_scale:
            return False, f"Scale too high: {scale} (max: {config.processing.max_scale})"
        
        return True, "Valid scale value"
    
    def validate_seed(self, seed: int) -> Tuple[bool, str]:
        """Validate random seed"""
        if not isinstance(seed, int):
            return False, f"Seed must be an integer, got: {type(seed)}"
        
        if seed < -1:
            return False, f"Seed must be -1 or positive, got: {seed}"
        
        if seed > 2147483647:  # Max 32-bit integer
            return False, f"Seed too large: {seed} (max: 2147483647)"
        
        return True, "Valid seed value"
    
    def validate_request(self, request_data: dict) -> Tuple[bool, List[str]]:
        """
        Validate complete request data
        
        Returns:
            tuple: (is_valid: bool, error_messages: List[str])
        """
        errors = []
        
        # Required fields
        required_fields = ['model_path', 'cloth_path']
        for field in required_fields:
            if field not in request_data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        # Validate model path
        is_valid, error_msg = self.validate_model_path(request_data['model_path'])
        if not is_valid:
            errors.append(f"Model path: {error_msg}")
        
        # Validate cloth path
        is_valid, error_msg = self.validate_cloth_path(request_data['cloth_path'])
        if not is_valid:
            errors.append(f"Cloth path: {error_msg}")
        
        # Validate model type
        model_type = request_data.get('model_type', 'hd')
        is_valid, error_msg = self.validate_model_type(model_type)
        if not is_valid:
            errors.append(f"Model type: {error_msg}")
        
        # Validate category
        category = request_data.get('category', 0)
        is_valid, error_msg = self.validate_category(category, model_type)
        if not is_valid:
            errors.append(f"Category: {error_msg}")
        
        # Validate optional parameters
        if 'samples' in request_data:
            is_valid, error_msg = self.validate_samples(request_data['samples'])
            if not is_valid:
                errors.append(f"Samples: {error_msg}")
        
        if 'steps' in request_data:
            is_valid, error_msg = self.validate_steps(request_data['steps'])
            if not is_valid:
                errors.append(f"Steps: {error_msg}")
        
        if 'scale' in request_data:
            is_valid, error_msg = self.validate_scale(request_data['scale'])
            if not is_valid:
                errors.append(f"Scale: {error_msg}")
        
        if 'seed' in request_data:
            is_valid, error_msg = self.validate_seed(request_data['seed'])
            if not is_valid:
                errors.append(f"Seed: {error_msg}")
        
        return len(errors) == 0, errors

def validate_and_convert_category(category: Union[int, str], model_type: str = 'dc') -> int:
    """
    Validate and convert category to integer
    
    Returns:
        int: Category as integer (0=upperbody, 1=lowerbody, 2=dress)
    """
    validator = InputValidator()
    
    # Validate category
    is_valid, error_msg = validator.validate_category(category, model_type)
    if not is_valid:
        raise ValidationError(f"Invalid category: {error_msg}", "category")
    
    # Convert to integer
    if isinstance(category, str):
        category_map = {
            'upperbody': 0,
            'lowerbody': 1,
            'dress': 2
        }
        return category_map[category.lower()]
    
    return int(category)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    import re
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def create_temp_file(original_filename: str, temp_dir: Optional[Path] = None) -> Path:
    """
    Create a temporary file with sanitized name
    
    Args:
        original_filename: Original filename
        temp_dir: Temporary directory (defaults to config temp dir)
        
    Returns:
        Path: Path to temporary file
    """
    if temp_dir is None:
        temp_dir = config.temp_dir
    
    # Sanitize filename
    safe_filename = sanitize_filename(original_filename)
    
    # Create unique filename
    import uuid
    name, ext = os.path.splitext(safe_filename)
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    
    temp_file = temp_dir / "uploads" / unique_filename
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    
    return temp_file

# Global validator instance
validator = InputValidator()

# Export main utilities
__all__ = [
    "InputValidator", "validator", "validate_and_convert_category",
    "sanitize_filename", "create_temp_file"
]
