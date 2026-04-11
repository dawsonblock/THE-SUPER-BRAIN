#!/bin/bash

echo "🧪 Testing Brain-AI System..."
echo ""

# Test OCR Service
echo "1️⃣ Testing OCR Service (port 6001)..."
OCR_HEALTH=$(curl -s http://localhost:6001/health)
if [[ $OCR_HEALTH == *"healthy"* ]]; then
    echo "   ✅ OCR Service is healthy"
else
    echo "   ❌ OCR Service failed"
    exit 1
fi
echo ""

# Test REST API
echo "2️⃣ Testing REST API (port 5001)..."
API_HEALTH=$(curl -s http://localhost:5001/healthz)
if [[ $API_HEALTH == *"ok"* ]]; then
    echo "   ✅ REST API is healthy"
else
    echo "   ❌ REST API failed"
    exit 1
fi
echo ""

# Test GUI
echo "3️⃣ Testing GUI (port 3000)..."
GUI_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [[ $GUI_RESPONSE == "200" ]]; then
    echo "   ✅ GUI is responding"
else
    echo "   ❌ GUI failed (HTTP $GUI_RESPONSE)"
    exit 1
fi
echo ""

# Test Query Endpoint
echo "4️⃣ Testing Query Endpoint..."
QUERY_RESULT=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AI?"}')

if [[ $QUERY_RESULT == *"answer"* ]]; then
    echo "   ✅ Query endpoint working"
    echo "   Response preview: $(echo $QUERY_RESULT | jq -r '.answer' 2>/dev/null | head -c 100)..."
else
    echo "   ❌ Query endpoint failed"
    exit 1
fi
echo ""

# Test Deep Think Mode
echo "5️⃣ Testing Deep Think Mode (Multi-Agent)..."
DEEPTHINK_RESULT=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate 15% of 250"}')

if [[ $DEEPTHINK_RESULT == *"answer"* ]]; then
    echo "   ✅ Deep Think mode working"
    echo "   Response preview: $(echo $DEEPTHINK_RESULT | jq -r '.answer' 2>/dev/null | head -c 100)..."
else
    echo "   ❌ Deep Think mode failed"
    exit 1
fi
echo ""

# Summary
echo "🎉 All Tests Passed!"
echo ""
echo "📊 System Status:"
echo "   • OCR Service: http://localhost:6001"
echo "   • REST API: http://localhost:5001"
echo "   • GUI: http://localhost:3000"
echo "   • API Docs: http://localhost:5001/docs"
echo ""
echo "✨ Ready for demo recording!"
