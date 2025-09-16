#!/bin/bash
echo "🎭 OOTDiffusion - Quick Start"
echo "=============================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "quick_start.py" ]; then
    echo "❌ quick_start.py not found"
    echo "Please run this script from the OOTDiffusion directory"
    exit 1
fi

echo "🚀 Starting OOTDiffusion..."
python3 quick_start.py
