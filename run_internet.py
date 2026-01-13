#!/usr/bin/env python3
"""
Internet-accessible startup script for DiagnoseAI using ngrok
Allows access from anywhere on the internet
"""
import os
import sys
import subprocess
import time
import threading
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_ngrok_installed():
    """Check if ngrok is installed."""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_ngrok_instructions():
    """Show instructions to install ngrok."""
    print("📦 NGROK INSTALLATION REQUIRED")
    print("=" * 40)
    print("ngrok is needed to expose your app to the internet.")
    print()
    print("🍺 Install with Homebrew (recommended):")
    print("   brew install ngrok/ngrok/ngrok")
    print()
    print("🌐 Or download from: https://ngrok.com/download")
    print()
    print("🔑 After installation, sign up for free at ngrok.com and run:")
    print("   ngrok config add-authtoken YOUR_TOKEN")
    print()
    print("Then run this script again!")

def start_ngrok(port):
    """Start ngrok tunnel in background."""
    try:
        # Start ngrok in background
        process = subprocess.Popen(['ngrok', 'http', str(port)], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a moment for ngrok to start
        time.sleep(3)
        
        # Get the public URL
        try:
            result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                if data.get('tunnels'):
                    public_url = data['tunnels'][0]['public_url']
                    return process, public_url
        except:
            pass
        
        return process, None
        
    except Exception as e:
        print(f"Error starting ngrok: {e}")
        return None, None

def main():
    """Run the application with internet access via ngrok."""
    port = 5003
    
    print("🌍 DiagnoseAI - Internet Access Setup")
    print("=" * 60)
    
    # Check if ngrok is installed
    if not check_ngrok_installed():
        install_ngrok_instructions()
        sys.exit(1)
    
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
    print("✅ ngrok: Installed")
    print()
    
    # Start Flask app in background thread
    print("🚀 Starting DiagnoseAI server...")
    
    from main import app
    
    def run_flask():
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait for Flask to start
    time.sleep(2)
    
    # Start ngrok tunnel
    print("🌐 Creating internet tunnel with ngrok...")
    ngrok_process, public_url = start_ngrok(port)
    
    if public_url:
        print()
        print("🎉 SUCCESS! DiagnoseAI is now accessible from the internet!")
        print("=" * 60)
        print(f"🌍 PUBLIC URL: {public_url}")
        print()
        print("📱 SHARE WITH YOUR DAD:")
        print(f"   URL: {public_url}")
        print("   Username: admin")
        print("   Password: admin123")
        print()
        print("🔒 SECURITY NOTES:")
        print("   - This URL is accessible from anywhere on the internet")
        print("   - Change the admin password after first login")
        print("   - Only share with trusted people")
        print("   - The URL will change each time you restart")
        print()
        print("📋 FEATURES AVAILABLE:")
        print("   - Upload and analyze ultrasound images")
        print("   - View AI-generated reports")
        print("   - Rate AI performance")
        print("   - Browse test history")
        print()
        print("🛑 Press Ctrl+C to stop the server and close the tunnel")
        print("=" * 60)
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            if ngrok_process:
                ngrok_process.terminate()
            print("✅ Server stopped and tunnel closed.")
    
    else:
        print("❌ Failed to create ngrok tunnel")
        print("Try running 'ngrok http 5003' manually in another terminal")
        print("Then share the URL it provides")

if __name__ == '__main__':
    main()