#!/bin/bash

# Simple script to start DiagnoseAI with ngrok for internet access

echo "🌍 Starting DiagnoseAI with Internet Access"
echo "=========================================="

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed!"
    echo ""
    echo "📦 Install ngrok first:"
    echo "   brew install ngrok/ngrok/ngrok"
    echo ""
    echo "🔑 Then sign up at ngrok.com and run:"
    echo "   ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

# Navigate to the correct directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run the local setup first."
    exit 1
fi

echo "✅ ngrok is installed"
echo "✅ Starting DiagnoseAI..."

# Start DiagnoseAI in background
source venv/bin/activate
python run_local.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

echo "✅ DiagnoseAI started (PID: $FLASK_PID)"
echo "🌐 Creating internet tunnel..."

# Start ngrok
ngrok http 5003 &
NGROK_PID=$!

echo ""
echo "🎉 SUCCESS!"
echo "=========================================="
echo "📋 INSTRUCTIONS:"
echo "1. Look for the 'Forwarding' line above"
echo "2. Copy the https://xxxxx.ngrok.io URL"
echo "3. Send that URL to your dad"
echo "4. He can access it from anywhere!"
echo ""
echo "🔑 Login credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🛑 To stop everything:"
echo "   Press Ctrl+C or close this terminal"
echo "=========================================="

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $FLASK_PID 2>/dev/null
    kill $NGROK_PID 2>/dev/null
    echo "✅ Cleanup complete"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for user to stop
wait