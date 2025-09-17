#!/usr/bin/env python3
"""
Test script for OOTDiffusion RunPod Handler
Demonstrates how to use the handler locally for testing
"""

import os
import sys
import json
import base64
import requests
from pathlib import Path
from PIL import Image

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def encode_image_to_base64(image_path):
    """Convert image file to base64 string"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def decode_base64_to_image(base64_string, output_path):
    """Convert base64 string to image file"""
    image_data = base64.b64decode(base64_string)
    with open(output_path, 'wb') as f:
        f.write(image_data)

def test_local_handler():
    """Test the handler locally (without RunPod)"""
    print("🧪 Testing OOTDiffusion Handler Locally...")
    
    # Import the handler function
    from handler import handler
    
    # Test with sample images (you'll need to provide these)
    user_image_path = "run/examples/model/model_1.png"
    cloth_image_path = "run/examples/garment/00055_00.jpg"
    
    if not os.path.exists(user_image_path) or not os.path.exists(cloth_image_path):
        print("❌ Sample images not found. Please ensure you have:")
        print(f"   - {user_image_path}")
        print(f"   - {cloth_image_path}")
        return False
    
    # Encode images
    print("📸 Encoding images...")
    user_image_b64 = encode_image_to_base64(user_image_path)
    cloth_image_b64 = encode_image_to_base64(cloth_image_path)
    
    # Create test job
    test_job = {
        "input": {
            "user_image": user_image_b64,
            "cloth_image": cloth_image_b64,
            "garment_type": "upper",
            "model_type": "hd",
            "samples": 1,
            "steps": 20,
            "scale": 2.0,
            "seed": 42
        }
    }
    
    print("🚀 Running inference...")
    try:
        # Call the handler
        result = handler(test_job)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return False
        
        if result.get("output", {}).get("success"):
            print("✅ Inference successful!")
            
            # Save results
            output_dir = "test_output"
            os.makedirs(output_dir, exist_ok=True)
            
            images = result["output"]["images"]
            print(f"📁 Saving {len(images)} result image(s)...")
            
            for i, img_b64 in enumerate(images):
                output_path = f"{output_dir}/result_{i}.png"
                decode_base64_to_image(img_b64, output_path)
                print(f"   💾 Saved: {output_path}")
            
            print("🎉 Test completed successfully!")
            return True
        else:
            print("❌ Inference failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_runpod_endpoint(endpoint_url, user_image_path, cloth_image_path):
    """Test the handler via RunPod endpoint"""
    print(f"🌐 Testing RunPod Endpoint: {endpoint_url}")
    
    if not os.path.exists(user_image_path) or not os.path.exists(cloth_image_path):
        print("❌ Image files not found")
        return False
    
    # Encode images
    print("📸 Encoding images...")
    user_image_b64 = encode_image_to_base64(user_image_path)
    cloth_image_b64 = encode_image_to_base64(cloth_image_path)
    
    # Create request payload
    payload = {
        "input": {
            "user_image": user_image_b64,
            "cloth_image": cloth_image_b64,
            "garment_type": "upper",
            "model_type": "hd",
            "samples": 1
        }
    }
    
    print("🚀 Sending request to RunPod...")
    try:
        response = requests.post(endpoint_url, json=payload, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("output", {}).get("success"):
            print("✅ RunPod request successful!")
            
            # Save results
            output_dir = "runpod_output"
            os.makedirs(output_dir, exist_ok=True)
            
            images = result["output"]["images"]
            print(f"📁 Saving {len(images)} result image(s)...")
            
            for i, img_b64 in enumerate(images):
                output_path = f"{output_dir}/runpod_result_{i}.png"
                decode_base64_to_image(img_b64, output_path)
                print(f"   💾 Saved: {output_path}")
            
            print("🎉 RunPod test completed successfully!")
            return True
        else:
            print(f"❌ RunPod request failed: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main test function"""
    print("🎭 OOTDiffusion Handler Test Suite")
    print("=" * 50)
    
    # Check if we have the required dependencies
    try:
        import runpod
        print("✅ RunPod dependency found")
    except ImportError:
        print("❌ RunPod not installed. Install with: pip install runpod")
        return
    
    # Test local handler
    print("\n1. Testing Local Handler")
    print("-" * 30)
    local_success = test_local_handler()
    
    # Test RunPod endpoint (if provided)
    print("\n2. Testing RunPod Endpoint")
    print("-" * 30)
    
    # You can set these environment variables or modify the values here
    endpoint_url = os.getenv("RUNPOD_ENDPOINT_URL")
    user_img = os.getenv("USER_IMAGE_PATH", "run/examples/model/model_1.png")
    cloth_img = os.getenv("CLOTH_IMAGE_PATH", "run/examples/garment/00055_00.jpg")
    
    if endpoint_url:
        runpod_success = test_runpod_endpoint(endpoint_url, user_img, cloth_img)
    else:
        print("ℹ️  Set RUNPOD_ENDPOINT_URL environment variable to test RunPod endpoint")
        print("   Example: export RUNPOD_ENDPOINT_URL='https://api.runpod.ai/v2/your-endpoint-id/tryon'")
        runpod_success = None
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Local Handler: {'✅ PASS' if local_success else '❌ FAIL'}")
    if runpod_success is not None:
        print(f"RunPod Endpoint: {'✅ PASS' if runpod_success else '❌ FAIL'}")
    else:
        print("RunPod Endpoint: ⏭️  SKIPPED")
    
    if local_success and (runpod_success is None or runpod_success):
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
