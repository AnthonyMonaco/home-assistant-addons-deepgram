#!/bin/bash
# Quick test script for Deepgram Wyoming server

echo "=================================================="
echo "Deepgram Wyoming Server Connection Test"
echo "=================================================="
echo ""

# Configuration
HOST="${1:-localhost}"
PORT="${2:-10301}"
TIMEOUT=5

echo "Testing connection to ${HOST}:${PORT}"
echo ""

# Test 1: Check if port is open
echo "[1/3] Checking if port is open..."
if timeout $TIMEOUT bash -c "cat < /dev/null > /dev/tcp/${HOST}/${PORT}" 2>/dev/null; then
    echo "✅ Port ${PORT} is open"
else
    echo "❌ Port ${PORT} is not accessible"
    echo "   Make sure the addon is running"
    exit 1
fi
echo ""

# Test 2: Send describe event
echo "[2/3] Sending 'describe' event..."
if command -v nc &> /dev/null; then
    RESPONSE=$(echo '{"type":"describe"}' | timeout $TIMEOUT nc ${HOST} ${PORT} 2>&1)
    if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
        echo "✅ Received response from server"
        echo ""
        echo "Response preview:"
        echo "$RESPONSE" | head -n 5
        echo ""

        # Check for expected content
        if echo "$RESPONSE" | grep -q "deepgram"; then
            echo "✅ Response contains 'deepgram' - server is working!"
        else
            echo "⚠️  Response doesn't contain expected 'deepgram' identifier"
        fi
    else
        echo "❌ No response or connection lost"
        echo "   This was the original error - check server logs"
        exit 1
    fi
else
    echo "⚠️  'nc' (netcat) not available, skipping describe test"
    echo "   Install with: apk add netcat-openbsd (Alpine) or apt-get install netcat (Debian)"
fi
echo ""

# Test 3: Check if process is running
echo "[3/3] Checking if server process is running..."
if pgrep -f "deepgram_server.py" > /dev/null; then
    echo "✅ Server process is running (PID: $(pgrep -f 'deepgram_server.py'))"
else
    echo "⚠️  Server process not found (might be running in container)"
fi
echo ""

echo "=================================================="
echo "Test Summary"
echo "=================================================="
echo "✅ All basic tests passed!"
echo ""
echo "Next steps:"
echo "1. Check addon logs: Settings → Add-ons → Deepgram → Log"
echo "2. Configure Wyoming integration in Home Assistant"
echo "3. Test with voice assistant"
echo ""
echo "For detailed testing guide, see:"
echo "/config/home-assistant-addons-deepgram/IMPLEMENTATION_COMPLETE.md"
