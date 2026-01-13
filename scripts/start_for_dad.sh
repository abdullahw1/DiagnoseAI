#!/bin/bash

# DiagnoseAI - Easy Network Startup Script
# Makes the app accessible to other devices on your network

echo "🏥 Starting DiagnoseAI for Network Access..."
echo "=========================================="

# Navigate to the correct directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run the local setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if database exists
if [ ! -f "instance/diagnoseai.db" ]; then
    echo "❌ Database not found!"
    echo "Setting up database..."
    export FLASK_APP=main.py
    flask db upgrade
    python scripts/create_admin_user.py
fi

# Get local IP for sharing
LOCAL_IP=$(python3 -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()")

echo ""
echo "🌐 NETWORK ACCESS READY!"
echo "========================"
echo "📱 Share this URL with your dad:"
echo "   http://$LOCAL_IP:5003"
echo ""
echo "🔑 Login credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📋 Instructions for your dad:"
echo "   1. Make sure his device is on the same WiFi"
echo "   2. Open any web browser (Safari, Chrome, etc.)"
echo "   3. Go to: http://$LOCAL_IP:5003"
echo "   4. Login with admin/admin123"
echo "   5. Click 'AI Testing' to start testing images"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Start the server
python run_network.py