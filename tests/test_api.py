"""
Test suite for OOTDiffusion API
"""
import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from PIL import Image
import numpy as np
from fastapi.testclient import TestClient
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from api.app import app, model_manager
from config import get_config

# Test configuration
test_config = get_config("testing")

class TestAPIBasic:
    """Basic API functionality tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        self.test_image_size = (256, 256)  # Smaller for testing
    
    def create_test_image(self, filename: str, size: tuple = None) -> Path:
        """Create a test image file"""
        if size is None:
            size = self.test_image_size
        
        # Create a simple test image
        img = Image.new('RGB', size, color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name)
        return Path(temp_file.name)
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "OOTDiffusion API"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "environment" in data
    
    def test_docs_endpoint(self):
        """Test API documentation endpoint"""
        response = self.client.get("/docs")
        # Should return 200 in debug mode, 404 in production
        assert response.status_code in [200, 404]

class TestImageProcessing:
    """Image processing tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
        self.test_image_size = (256, 256)
    
    def create_test_image(self, filename: str, size: tuple = None) -> Path:
        """Create a test image file"""
        if size is None:
            size = self.test_image_size
        
        img = Image.new('RGB', size, color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name)
        return Path(temp_file.name)
    
    def test_process_images_hd(self):
        """Test HD model image processing"""
        # Create test images
        model_img = self.create_test_image("model.png")
        cloth_img = self.create_test_image("cloth.png")
        
        try:
            # Test with HD model
            with open(model_img, "rb") as f1, open(cloth_img, "rb") as f2:
                files = {
                    "model_file": ("model.png", f1, "image/png"),
                    "cloth_file": ("cloth.png", f2, "image/png")
                }
                data = {
                    "model_type": "hd",
                    "category": 0,
                    "samples": 1,
                    "steps": 5,  # Reduced for testing
                    "scale": 2.0,
                    "seed": 42
                }
                
                response = self.client.post("/process", files=files, data=data)
                
                # Should return 200 or 503 (if models not loaded)
                assert response.status_code in [200, 503]
                
                if response.status_code == 200:
                    data = response.json()
                    assert data["success"] is True
                    assert "result_paths" in data
                    assert len(data["result_paths"]) == 1
        
        finally:
            # Cleanup
            if model_img.exists():
                model_img.unlink()
            if cloth_img.exists():
                cloth_img.unlink()
    
    def test_process_images_dc(self):
        """Test DC model image processing"""
        # Create test images
        model_img = self.create_test_image("model.png")
        cloth_img = self.create_test_image("cloth.png")
        
        try:
            # Test with DC model
            with open(model_img, "rb") as f1, open(cloth_img, "rb") as f2:
                files = {
                    "model_file": ("model.png", f1, "image/png"),
                    "cloth_file": ("cloth.png", f2, "image/png")
                }
                data = {
                    "model_type": "dc",
                    "category": "upperbody",
                    "samples": 1,
                    "steps": 5,  # Reduced for testing
                    "scale": 2.0,
                    "seed": 42
                }
                
                response = self.client.post("/process", files=files, data=data)
                
                # Should return 200 or 503 (if models not loaded)
                assert response.status_code in [200, 503]
        
        finally:
            # Cleanup
            if model_img.exists():
                model_img.unlink()
            if cloth_img.exists():
                cloth_img.unlink()
    
    def test_invalid_file_type(self):
        """Test with invalid file type"""
        # Create a text file instead of image
        temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        temp_file.write(b"This is not an image")
        temp_file.close()
        
        try:
            with open(temp_file.name, "rb") as f:
                files = {
                    "model_file": ("test.txt", f, "text/plain"),
                    "cloth_file": ("test.txt", f, "text/plain")
                }
                data = {
                    "model_type": "hd",
                    "category": 0
                }
                
                response = self.client.post("/process", files=files, data=data)
                assert response.status_code == 400
        
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_missing_files(self):
        """Test with missing files"""
        data = {
            "model_type": "hd",
            "category": 0
        }
        
        response = self.client.post("/process", data=data)
        assert response.status_code == 422  # Validation error

class TestValidation:
    """Input validation tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
    
    def test_invalid_model_type(self):
        """Test invalid model type"""
        model_img = self.create_test_image("model.png")
        cloth_img = self.create_test_image("cloth.png")
        
        try:
            with open(model_img, "rb") as f1, open(cloth_img, "rb") as f2:
                files = {
                    "model_file": ("model.png", f1, "image/png"),
                    "cloth_file": ("cloth.png", f2, "image/png")
                }
                data = {
                    "model_type": "invalid",
                    "category": 0
                }
                
                response = self.client.post("/process", files=files, data=data)
                assert response.status_code == 400
        
        finally:
            if model_img.exists():
                model_img.unlink()
            if cloth_img.exists():
                cloth_img.unlink()
    
    def test_invalid_category(self):
        """Test invalid category"""
        model_img = self.create_test_image("model.png")
        cloth_img = self.create_test_image("cloth.png")
        
        try:
            with open(model_img, "rb") as f1, open(cloth_img, "rb") as f2:
                files = {
                    "model_file": ("model.png", f1, "image/png"),
                    "cloth_file": ("cloth.png", f2, "image/png")
                }
                data = {
                    "model_type": "hd",
                    "category": 5  # Invalid category for HD
                }
                
                response = self.client.post("/process", files=files, data=data)
                assert response.status_code == 400
        
        finally:
            if model_img.exists():
                model_img.unlink()
            if cloth_img.exists():
                cloth_img.unlink()
    
    def test_invalid_samples(self):
        """Test invalid samples count"""
        model_img = self.create_test_image("model.png")
        cloth_img = self.create_test_image("cloth.png")
        
        try:
            with open(model_img, "rb") as f1, open(cloth_img, "rb") as f2:
                files = {
                    "model_file": ("model.png", f1, "image/png"),
                    "cloth_file": ("cloth.png", f2, "image/png")
                }
                data = {
                    "model_type": "hd",
                    "category": 0,
                    "samples": 10  # Too many samples
                }
                
                response = self.client.post("/process", files=files, data=data)
                assert response.status_code == 400
        
        finally:
            if model_img.exists():
                model_img.unlink()
            if cloth_img.exists():
                cloth_img.unlink()
    
    def create_test_image(self, filename: str) -> Path:
        """Create a test image file"""
        img = Image.new('RGB', (256, 256), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name)
        return Path(temp_file.name)

class TestErrorHandling:
    """Error handling tests"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
    
    def test_large_file(self):
        """Test with file too large"""
        # Create a large file (simulate)
        large_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        large_file.write(b'x' * (50 * 1024 * 1024))  # 50MB
        large_file.close()
        
        try:
            with open(large_file.name, "rb") as f:
                files = {
                    "model_file": ("large.png", f, "image/png"),
                    "cloth_file": ("large.png", f, "image/png")
                }
                data = {
                    "model_type": "hd",
                    "category": 0
                }
                
                response = self.client.post("/process", files=files, data=data)
                # Should handle large files gracefully
                assert response.status_code in [200, 400, 413]
        
        finally:
            if os.path.exists(large_file.name):
                os.unlink(large_file.name)
    
    def test_malformed_request(self):
        """Test malformed request"""
        response = self.client.post("/process", json={"invalid": "data"})
        assert response.status_code == 422

# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
