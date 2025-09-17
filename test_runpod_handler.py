#!/usr/bin/env python3
"""
Test script for RunPod Handler
Tests the handler locally to ensure it works before deployment
"""

import os
import sys
import json
import base64
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_handler():
    """Test the RunPod handler locally"""
    print("🧪 Testing RunPod Handler...")
    
    try:
        # Import the handler
        from runpod_handler import handler
        print("✅ Handler imported successfully")
        
        # Create a simple test job
        test_job = {
            "input": {
                "user_image": "dummy_base64_user_image",
                "cloth_image": "dummy_base64_cloth_image",
                "garment_type": "upper",
                "model_type": "hd",
                "samples": 1
            }
        }
        
        print("🚀 Testing handler with dummy data...")
        
        # This will test the handler structure without actually running inference
        # (since we don't have real images)
        result = handler(test_job)
        
        print("📋 Handler response:")
        print(json.dumps(result, indent=2))
        
        if "error" in result:
            print("❌ Handler returned error (expected with dummy data)")
            return False
        else:
            print("✅ Handler structure is correct")
            return True
            
    except Exception as e:
        print(f"❌ Handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Test that all required imports work"""
    print("🔍 Testing imports...")
    
    try:
        import runpod
        print("✅ RunPod imported successfully")
    except ImportError as e:
        print(f"❌ RunPod import failed: {e}")
        return False
    
    try:
        from run.inference import inference
        print("✅ Inference function imported successfully")
    except ImportError as e:
        print(f"❌ Inference import failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🎭 RunPod Handler Test Suite")
    print("=" * 50)
    
    # Test imports
    print("\n1. Testing Imports")
    print("-" * 30)
    imports_ok = test_imports()
    
    if not imports_ok:
        print("❌ Import tests failed. Check dependencies.")
        return
    
    # Test handler
    print("\n2. Testing Handler")
    print("-" * 30)
    handler_ok = test_handler()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"Handler: {'✅ PASS' if handler_ok else '❌ FAIL'}")
    
    if imports_ok and handler_ok:
        print("\n🎉 All tests passed! Handler is ready for RunPod deployment.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
