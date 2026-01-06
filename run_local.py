#!/usr/bin/env python3
"""
Local development startup script for DiagnoseAI
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Run the application locally."""
    print("🏥 DiagnoseAI - Local Development Setup")
    print("=" * 50)
    
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
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
    print("🚀 Starting DiagnoseAI...")
    print("   Access at: http://127.0.0.1:5003")
    print("   Login with: admin / admin123")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Import and run the main application
    from main import app
    app.run(host='127.0.0.1', port=5003, debug=True)

if __name__ == '__main__':
    main()