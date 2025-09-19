#!/usr/bin/env python3
"""
DiagnoseAI - Main application entry point
"""
import os
from app import create_app

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'postgresql://diagnoseai_user:diagnoseai_pass@localhost:5432/diagnoseai')
os.environ.setdefault('SECRET_KEY', 'dev-secret-key-change-in-production')

# Create Flask app
app = create_app()

if __name__ == '__main__':
    print("🏥 Starting DiagnoseAI...")
    print("📊 Database: PostgreSQL")
    print("🌐 Server: http://127.0.0.1:5000")
    print("🔐 Authentication: Enabled")
    print("\n📝 Available routes:")
    print("   • http://127.0.0.1:5000/auth/register - Register new account")
    print("   • http://127.0.0.1:5000/auth/login - Login")
    print("   • http://127.0.0.1:5000/dashboard - Main dashboard (requires login)")
    print("\n🚀 Starting server...")
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )