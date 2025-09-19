#!/usr/bin/env python3
"""
DiagnoseAI - Main application entry point
"""
import os
import socket
import subprocess
import sys
from app import create_app

def is_port_available(host, port):
    """Check if a port is available for use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False

def kill_process_on_port(port):
    """Kill any process running on the specified port."""
    try:
        # Find process using the port
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True, check=False)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"🔄 Killing process {pid} on port {port}...")
                    subprocess.run(['kill', '-9', pid], check=False)
            return True
        return False
    except Exception as e:
        print(f"⚠️  Error killing process on port {port}: {e}")
        return False

def ensure_port_available(host, port, max_attempts=3):
    """Ensure the specified port is available, killing processes if necessary."""
    for attempt in range(max_attempts):
        if is_port_available(host, port):
            print(f"✅ Port {port} is available")
            return True
        
        print(f"⚠️  Port {port} is in use (attempt {attempt + 1}/{max_attempts})")
        
        if attempt < max_attempts - 1:
            if kill_process_on_port(port):
                # Wait a moment for the process to be killed
                import time
                time.sleep(1)
            else:
                print(f"❌ Could not free port {port}")
                return False
    
    return is_port_available(host, port)

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'postgresql://diagnoseai_user:diagnoseai_pass@localhost:5432/diagnoseai')
os.environ.setdefault('SECRET_KEY', 'dev-secret-key-change-in-production')

# Create Flask app
app = create_app()

if __name__ == '__main__':
    # Use 0.0.0.0 in Docker/production, 127.0.0.1 for local development
    HOST = '0.0.0.0' if os.environ.get('FLASK_ENV') == 'production' else '127.0.0.1'
    PORT = 5003
    
    # Only check port availability if this is the main process (not a Flask reloader child)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("🏥 Starting DiagnoseAI...")
        print("📊 Database: PostgreSQL")
        print(f"🌐 Server: http://{HOST}:{PORT}")
        print("🔐 Authentication: Enabled")
        
        # Check and ensure port availability only on initial startup
        if not ensure_port_available(HOST, PORT):
            print(f"❌ Unable to free port {PORT}. Please manually stop any processes using this port.")
            sys.exit(1)
        
        print("\n📝 Available routes:")
        print(f"   • http://{HOST}:{PORT}/auth/register - Register new account")
        print(f"   • http://{HOST}:{PORT}/auth/login - Login")
        print(f"   • http://{HOST}:{PORT}/dashboard - Main dashboard (requires login)")
        print(f"   • http://{HOST}:{PORT}/upload - Upload ultrasound images (requires login)")
        print("\n🚀 Starting server...")
    
    try:
        app.run(
            host=HOST,
            port=PORT,
            debug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)