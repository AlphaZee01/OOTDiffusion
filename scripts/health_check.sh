#!/bin/bash
# OOTDiffusion Health Check Script

API_URL="http://localhost:7865"
TIMEOUT=10

echo "🔍 OOTDiffusion Health Check"
echo "================================"

# Check if API is running
echo "Checking API status..."
if curl -f -s --max-time $TIMEOUT "$API_URL/health" > /dev/null; then
    echo "✅ API is running"
    
    # Get detailed health info
    echo "📊 Health details:"
    curl -s --max-time $TIMEOUT "$API_URL/health" | python -m json.tool 2>/dev/null || echo "Could not parse health response"
    
    # Check specific endpoints
    echo "🔍 Testing endpoints..."
    
    if curl -f -s --max-time $TIMEOUT "$API_URL/" > /dev/null; then
        echo "✅ Root endpoint"
    else
        echo "❌ Root endpoint"
    fi
    
    if curl -f -s --max-time $TIMEOUT "$API_URL/docs" > /dev/null; then
        echo "✅ Docs endpoint"
    else
        echo "❌ Docs endpoint"
    fi
    
else
    echo "❌ API is not running or not responding"
    echo "💡 Try: python quick_start.py"
    exit 1
fi

echo "================================"
echo "🎉 Health check completed!"
