#!/usr/bin/env python3
"""
Simple DiagnoseAI startup script
"""
import os
import socket
import sys

def is_port_available(host, port):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False

def main():
    """Start the DiagnoseAI server."""
    HOST = '127.0.0.1'
    PORT = 5003
    
    print("🏥 DiagnoseAI - Radiology AI Application")
    print("=" * 50)
    
    # Simple port check
    if not is_port_available(HOST, PORT):
        print(f"⚠️  Port {PORT} is already in use.")
        print(f"💡 Please stop any other services on port {PORT} or use a different port.")
        print(f"   You can check what's using the port with: lsof -i :{PORT}")
        sys.exit(1)
    
    print(f"✅ Port {PORT} is available")
    print(f"🌐 Starting server on http://{HOST}:{PORT}")
    print("📝 Press Ctrl+C to stop")
    print("-" * 50)
    
    # Set environment variables
    os.environ.setdefault('DATABASE_URL', 'postgresql://diagnoseai_user:diagnoseai_pass@localhost:5432/diagnoseai')
    os.environ.setdefault('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    try:
        # Import and create the Flask app
        from app import create_app
        app = create_app()
        
        # Start the server
        app.run(
            host=HOST,
            port=PORT,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()