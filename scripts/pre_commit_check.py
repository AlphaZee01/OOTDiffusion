#!/usr/bin/env python3
"""
Pre-commit check for OOTDiffusion
Ensures everything is ready for hosting before committing
"""
import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - MISSING")
        return False

def check_file_content(file_path, required_content, description):
    """Check if file contains required content"""
    if not Path(file_path).exists():
        print(f"❌ {description}: {file_path} - FILE NOT FOUND")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if any(keyword in content for keyword in required_content):
                print(f"✅ {description}: {file_path}")
                return True
            else:
                print(f"❌ {description}: {file_path} - MISSING REQUIRED CONTENT")
                return False
    except Exception as e:
        print(f"❌ {description}: {file_path} - ERROR: {e}")
        return False

def check_python_syntax(file_path):
    """Check Python file syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), file_path, 'exec')
        print(f"✅ Python syntax: {file_path}")
        return True
    except SyntaxError as e:
        print(f"❌ Python syntax error in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking {file_path}: {e}")
        return False

def main():
    """Main pre-commit check"""
    print("🔍 OOTDiffusion Pre-commit Check")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 0
    
    # Critical files that must exist
    critical_files = [
        ("config.py", "Configuration management"),
        ("start.py", "Startup script"),
        ("quick_start.py", "Quick start script"),
        ("api/app.py", "FastAPI application"),
        ("utils/error_handling.py", "Error handling utilities"),
        ("utils/validation.py", "Input validation utilities"),
        ("scripts/auto_download_models.py", "Automatic model downloader"),
        ("scripts/verify_setup.py", "Setup verification script"),
        ("test_interface.html", "Test interface"),
        ("Dockerfile", "Docker configuration"),
        ("docker-compose.yml", "Docker Compose configuration"),
        ("requirements-prod.txt", "Production requirements"),
        ("requirements-dev.txt", "Development requirements"),
        ("README-HOSTING.md", "Hosting documentation"),
        ("CHANGELOG.md", "Changelog"),
    ]
    
    print("\n📁 Checking critical files...")
    for file_path, description in critical_files:
        total_checks += 1
        if check_file_exists(file_path, description):
            checks_passed += 1
    
    # Check Python syntax
    print("\n🐍 Checking Python syntax...")
    python_files = [
        "config.py",
        "start.py", 
        "quick_start.py",
        "api/app.py",
        "utils/error_handling.py",
        "utils/validation.py",
        "scripts/auto_download_models.py",
        "scripts/verify_setup.py",
        "scripts/pre_commit_check.py"
    ]
    
    for file_path in python_files:
        if Path(file_path).exists():
            total_checks += 1
            if check_python_syntax(file_path):
                checks_passed += 1
    
    # Check key content in critical files
    print("\n📝 Checking file content...")
    
    # Check start.py has model download functionality
    total_checks += 1
    if check_file_content("start.py", ["check_and_download_models", "auto_download_models"], "Model download integration"):
        checks_passed += 1
    
    # Check Dockerfile has entrypoint
    total_checks += 1
    if check_file_content("Dockerfile", ["ENTRYPOINT", "auto_download_models"], "Docker automatic download"):
        checks_passed += 1
    
    # Check README has quick start
    total_checks += 1
    if check_file_content("README.md", ["quick_start.py", "One-Command Setup"], "Quick start documentation"):
        checks_passed += 1
    
    # Check hosting guide has correct repo URL
    total_checks += 1
    if check_file_content("README-HOSTING.md", ["AlphaZee01/OOTDiffusion"], "Correct repository URL"):
        checks_passed += 1
    
    # Check test interface has API integration
    total_checks += 1
    if check_file_content("test_interface.html", ["process", "health", "API"], "Test interface functionality"):
        checks_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Pre-commit Check Results: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✅ All checks passed! Ready for commit and hosting.")
        return 0
    else:
        print("❌ Some checks failed. Please fix issues before committing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
