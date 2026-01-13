#!/usr/bin/env python3
"""
Network-accessible startup script for DiagnoseAI
Allows access from other devices on the same network
"""
import os
import sys
import socket
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def main():
    """Run the application for network access."""
    local_ip = get_local_ip()
    port = 5003
    
    print("🏥 DiagnoseAI - Network Access Setup")
    print("=" * 60)
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your-openai-api-key-here':
        print("⚠️  WARNING: OPENAI_API_KEY not set in .env file")
        print("   AI features will not work without a valid API key")
        print("   You can still test the basic functionality")
        print()
    
    # Check if database exists
    db_path = "/Users/abdullahwaheed/Downloads/radiology-ai-application/DiagnoseAI/instance/diagnoseai.db"
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run database setup first:")
        print("   source venv/bin/activate && flask db upgrade")
        sys.exit(1)
    
    print("✅ Database: SQLite (Local)")
    print("✅ Virtual Environment: Ready")
    print("✅ Admin User: admin / admin123")
    print()
    print("🌐 NETWORK ACCESS INFORMATION")
    print("=" * 60)
    print(f"🖥️  Local Access (this Mac): http://127.0.0.1:{port}")
    print(f"📱 Network Access (other devices): http://{local_ip}:{port}")
    print()
    print("📋 SHARING INSTRUCTIONS:")
    print(f"   1. Make sure your Mac and other devices are on the same WiFi network")
    print(f"   2. Share this URL with your dad: http://{local_ip}:{port}")
    print(f"   3. He can access it from any device (phone, tablet, computer)")
    print(f"   4. Login credentials: admin / admin123")
    print()
    print("🔒 SECURITY NOTES:")
    print("   - This is HTTP (not HTTPS) - suitable for local network only")
    print("   - Only accessible from devices on your local network")
    print("   - Change the admin password after first login")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Import and run the main application
    from main import app
    
    # Run on all interfaces (0.0.0.0) to allow network access
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()