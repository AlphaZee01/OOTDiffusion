"""
Production-ready error handling and logging utilities for OOTDiffusion
"""
import logging
import traceback
import functools
import time
from typing import Any, Callable, Optional, Dict, Union
from pathlib import Path
import json
from datetime import datetime

from config import config

class OOTDError(Exception):
    """Base exception for OOTDiffusion errors"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ModelLoadError(OOTDError):
    """Error when loading models"""
    def __init__(self, message: str, model_name: str, details: Optional[Dict] = None):
        super().__init__(message, "MODEL_LOAD_ERROR", details)
        self.model_name = model_name

class ProcessingError(OOTDError):
    """Error during image processing"""
    def __init__(self, message: str, step: str, details: Optional[Dict] = None):
        super().__init__(message, "PROCESSING_ERROR", details)
        self.step = step

class ValidationError(OOTDError):
    """Error during input validation"""
    def __init__(self, message: str, field: str, details: Optional[Dict] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field

class ResourceError(OOTDError):
    """Error when resources are not available"""
    def __init__(self, message: str, resource_type: str, details: Optional[Dict] = None):
        super().__init__(message, "RESOURCE_ERROR", details)
        self.resource_type = resource_type

class Logger:
    """Enhanced logger with structured logging"""
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, config.logging.level.upper()))
        
        # Create formatter
        formatter = logging.Formatter(config.logging.format)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent duplicate logs
        self.logger.propagate = False
    
    def info(self, message: str, **kwargs):
        """Log info message with additional context"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message with additional context"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, **kwargs):
        """Log error message with additional context"""
        self.logger.error(self._format_message(message, **kwargs))
    
    def debug(self, message: str, **kwargs):
        """Log debug message with additional context"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with additional context"""
        if kwargs:
            context = json.dumps(kwargs, default=str)
            return f"{message} | Context: {context}"
        return message

# Global logger instance
logger = Logger("ootd")

def error_handler(
    reraise: bool = False,
    return_value: Any = None,
    log_error: bool = True
):
    """
    Decorator for error handling
    
    Args:
        reraise: Whether to reraise the exception
        return_value: Value to return if an error occurs
        log_error: Whether to log the error
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except OOTDError as e:
                if log_error:
                    logger.error(
                        f"OOTD Error in {func.__name__}: {e.message}",
                        error_code=e.error_code,
                        details=e.details,
                        function=func.__name__
                    )
                if reraise:
                    raise
                return return_value
            except Exception as e:
                if log_error:
                    logger.error(
                        f"Unexpected error in {func.__name__}: {str(e)}",
                        error_type=type(e).__name__,
                        traceback=traceback.format_exc(),
                        function=func.__name__
                    )
                if reraise:
                    raise
                return return_value
        return wrapper
    return decorator

def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(
                f"Function {func.__name__} completed successfully",
                execution_time=execution_time,
                function=func.__name__
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func.__name__} failed after {execution_time:.2f}s",
                error=str(e),
                execution_time=execution_time,
                function=func.__name__
            )
            raise
    return wrapper

def validate_input(func: Callable) -> Callable:
    """Decorator to validate function inputs"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Basic validation
        if not args and not kwargs:
            raise ValidationError("No arguments provided", "args")
        
        # Log function call
        logger.debug(
            f"Calling {func.__name__}",
            args_count=len(args),
            kwargs_keys=list(kwargs.keys()),
            function=func.__name__
        )
        
        return func(*args, **kwargs)
    return wrapper

class ErrorTracker:
    """Track and analyze errors"""
    
    def __init__(self, log_file: str = "error_tracker.json"):
        self.log_file = Path(log_file)
        self.errors = []
        self.load_errors()
    
    def track_error(self, error: Exception, context: Optional[Dict] = None):
        """Track an error with context"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "traceback": traceback.format_exc()
        }
        
        self.errors.append(error_data)
        self.save_errors()
        
        logger.error(
            "Error tracked",
            error_type=error_data["error_type"],
            error_message=error_data["error_message"],
            context=context
        )
    
    def load_errors(self):
        """Load errors from file"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    self.errors = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.errors = []
    
    def save_errors(self):
        """Save errors to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.errors, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save errors: {e}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of tracked errors"""
        if not self.errors:
            return {"total_errors": 0}
        
        error_types = {}
        for error in self.errors:
            error_type = error["error_type"]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.errors),
            "error_types": error_types,
            "recent_errors": self.errors[-10:]  # Last 10 errors
        }

# Global error tracker
error_tracker = ErrorTracker()

def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """
    Safely execute a function and return success status and result
    
    Returns:
        tuple: (success: bool, result: Any)
    """
    try:
        result = func(*args, **kwargs)
        return True, result
    except Exception as e:
        error_tracker.track_error(e, {
            "function": func.__name__,
            "args": str(args)[:100],  # Truncate long args
            "kwargs": str(kwargs)[:100]
        })
        return False, e

def cleanup_temp_files(temp_dir: Union[str, Path] = None):
    """Clean up temporary files"""
    if temp_dir is None:
        temp_dir = config.temp_dir
    else:
        temp_dir = Path(temp_dir)
    
    if not temp_dir.exists():
        return
    
    try:
        import shutil
        for item in temp_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        logger.info(f"Cleaned up temporary files in {temp_dir}")
    except Exception as e:
        logger.error(f"Failed to cleanup temp files: {e}")

# Export main utilities
__all__ = [
    "OOTDError", "ModelLoadError", "ProcessingError", "ValidationError", "ResourceError",
    "Logger", "logger", "error_handler", "performance_monitor", "validate_input",
    "ErrorTracker", "error_tracker", "safe_execute", "cleanup_temp_files"
]
