"""
Production-ready configuration management for OOTDiffusion
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for model paths and settings"""
    # Model paths
    ootd_path: str = "checkpoints/ootd"
    humanparsing_path: str = "checkpoints/humanparsing"
    openpose_path: str = "checkpoints/openpose"
    clip_path: str = "checkpoints/clip-vit-large-patch14"
    
    # Model settings
    device: str = "cuda:0"
    torch_dtype: str = "float16"
    use_safetensors: bool = True
    
    # Performance settings
    enable_attention_slicing: bool = True
    enable_memory_efficient_attention: bool = True
    enable_cpu_offload: bool = False

@dataclass
class ServerConfig:
    """Configuration for server settings"""
    host: str = "0.0.0.0"
    port: int = 7865
    workers: int = 1
    max_request_size: int = 50 * 1024 * 1024  # 50MB
    timeout: int = 300  # 5 minutes
    
    # Security
    allowed_origins: list = field(default_factory=lambda: ["*"])
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = field(default_factory=lambda: [".jpg", ".jpeg", ".png", ".bmp"])

@dataclass
class ProcessingConfig:
    """Configuration for image processing"""
    # Image dimensions
    hd_width: int = 768
    hd_height: int = 1024
    dc_width: int = 768
    dc_height: int = 1024
    
    # Processing parameters
    default_samples: int = 1
    max_samples: int = 4
    default_steps: int = 20
    max_steps: int = 40
    default_scale: float = 2.0
    min_scale: float = 1.0
    max_scale: float = 5.0
    
    # Quality settings
    image_quality: int = 95
    resize_algorithm: str = "LANCZOS"

@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class ProductionConfig:
    """Main production configuration"""
    model: ModelConfig = field(default_factory=ModelConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # Environment
    environment: str = "production"
    debug: bool = False
    
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent)
    checkpoints_dir: Path = field(default_factory=lambda: Path("checkpoints"))
    temp_dir: Path = field(default_factory=lambda: Path("temp"))
    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    
    def __post_init__(self):
        """Initialize configuration after creation"""
        # Set up environment variables
        self._load_from_env()
        
        # Create necessary directories
        self._create_directories()
        
        # Validate configuration
        self._validate()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Model settings
        if os.getenv("OOTD_DEVICE"):
            self.model.device = os.getenv("OOTD_DEVICE")
        
        if os.getenv("OOTD_TORCH_DTYPE"):
            self.model.torch_dtype = os.getenv("OOTD_TORCH_DTYPE")
        
        # Server settings
        if os.getenv("OOTD_HOST"):
            self.server.host = os.getenv("OOTD_HOST")
        
        if os.getenv("OOTD_PORT"):
            self.server.port = int(os.getenv("OOTD_PORT"))
        
        if os.getenv("OOTD_WORKERS"):
            self.server.workers = int(os.getenv("OOTD_WORKERS"))
        
        # Environment
        if os.getenv("OOTD_ENVIRONMENT"):
            self.environment = os.getenv("OOTD_ENVIRONMENT")
        
        if os.getenv("OOTD_DEBUG"):
            self.debug = os.getenv("OOTD_DEBUG").lower() == "true"
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.checkpoints_dir,
            self.temp_dir,
            self.output_dir,
            self.temp_dir / "uploads",
            self.temp_dir / "processed",
            self.output_dir / "results"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def _validate(self):
        """Validate configuration"""
        # Check if checkpoints exist
        required_checkpoints = [
            self.checkpoints_dir / "ootd",
            self.checkpoints_dir / "humanparsing",
            self.checkpoints_dir / "openpose",
            self.checkpoints_dir / "clip-vit-large-patch14"
        ]
        
        missing_checkpoints = []
        for checkpoint in required_checkpoints:
            if not checkpoint.exists():
                missing_checkpoints.append(str(checkpoint))
        
        if missing_checkpoints:
            logger.warning(f"Missing checkpoints: {missing_checkpoints}")
            logger.warning("Please download the required model checkpoints from Hugging Face")
        
        # Validate device
        if self.model.device.startswith("cuda") and not self._is_cuda_available():
            logger.warning("CUDA not available, falling back to CPU")
            self.model.device = "cpu"
    
    def _is_cuda_available(self) -> bool:
        """Check if CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def get_model_paths(self) -> Dict[str, str]:
        """Get all model paths as a dictionary"""
        return {
            "ootd": str(self.checkpoints_dir / "ootd"),
            "humanparsing": str(self.checkpoints_dir / "humanparsing"),
            "openpose": str(self.checkpoints_dir / "openpose"),
            "clip": str(self.checkpoints_dir / "clip-vit-large-patch14")
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "model": self.model.__dict__,
            "server": self.server.__dict__,
            "processing": self.processing.__dict__,
            "logging": self.logging.__dict__,
            "environment": self.environment,
            "debug": self.debug,
            "project_root": str(self.project_root),
            "checkpoints_dir": str(self.checkpoints_dir),
            "temp_dir": str(self.temp_dir),
            "output_dir": str(self.output_dir)
        }

# Global configuration instance
config = ProductionConfig()

# Environment-specific configurations
def get_config(environment: str = "production") -> ProductionConfig:
    """Get configuration for specific environment"""
    if environment == "development":
        config.environment = "development"
        config.debug = True
        config.logging.level = "DEBUG"
        config.server.workers = 1
    elif environment == "testing":
        config.environment = "testing"
        config.debug = True
        config.logging.level = "DEBUG"
        config.server.workers = 1
        config.model.device = "cpu"  # Use CPU for testing
    else:  # production
        config.environment = "production"
        config.debug = False
        config.logging.level = "INFO"
    
    return config

# Export the main configuration
__all__ = ["config", "get_config", "ProductionConfig", "ModelConfig", "ServerConfig", "ProcessingConfig", "LoggingConfig"]
