#!/usr/bin/env python3
"""
DiagnoseAI - Server startup script with port management
"""
import os
import sys
import socket
import subprocess
import time

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import flask
        import psycopg2
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_database_connection():
    """Check if PostgreSQL database is accessible."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="diagnoseai",
            user="diagnoseai_user",
            password="diagnoseai_pass"
        )
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("💡 Make sure PostgreSQL is running and the database is set up")
        return False

def is_port_available(host, port):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False

def kill_process_on_port(port):
    """Kill process on specified port."""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True, check=False)
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"🔄 Terminating process {pid} on port {port}...")
                    subprocess.run(['kill', '-15', pid], check=False)  # SIGTERM first
                    time.sleep(2)
                    # Force kill if still running
                    subprocess.run(['kill', '-9', pid], check=False)
            return True
        return False
    except Exception as e:
        print(f"⚠️  Error managing process on port {port}: {e}")
        return False

def main():
    """Main server startup function."""
    HOST = '127.0.0.1'
    PORT = 5003
    
    print("🏥 DiagnoseAI Server Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database
    if not check_database_connection():
        print("⚠️  Continuing without database verification...")
    
    # Check port availability
    if not is_port_available(HOST, PORT):
        print(f"⚠️  Port {PORT} is in use. Attempting to free it...")
        if kill_process_on_port(PORT):
            time.sleep(2)
            if not is_port_available(HOST, PORT):
                print(f"❌ Could not free port {PORT}")
                sys.exit(1)
        else:
            print(f"❌ Port {PORT} is occupied and cannot be freed")
            sys.exit(1)
    
    print(f"✅ Port {PORT} is available")
    
    # Start the Flask application
    print(f"\n🚀 Starting DiagnoseAI on http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        # Import and run the Flask app
        from main import app
        app.run(host=HOST, port=PORT, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()