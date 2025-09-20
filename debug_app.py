#!/usr/bin/env python3
"""
Debug script to check DiagnoseAI application state
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """Check environment variables."""
    print("🔧 Environment Variables:")
    required_vars = ['SECRET_KEY', 'DATABASE_URL', 'OPENAI_API_KEY']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'OPENAI_API_KEY':
                print(f"   ✅ {var}: {value[:10]}...")
            elif var == 'SECRET_KEY':
                print(f"   ✅ {var}: {'*' * len(value)}")
            else:
                print(f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: Not set")

def check_database():
    """Check database connectivity."""
    print("\n🗄️  Database Connectivity:")
    try:
        # Set the correct working directory context
        import sys
        import os
        
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models import User, Case, Report
            from app import db
            
            # Try to query the database
            user_count = User.query.count()
            case_count = Case.query.count()
            report_count = Report.query.count()
            
            print(f"   ✅ Database connected")
            print(f"   📊 Users: {user_count}")
            print(f"   📊 Cases: {case_count}")
            print(f"   📊 Reports: {report_count}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def check_uploads():
    """Check upload directory and files."""
    print("\n📁 Upload Directory:")
    upload_folder = os.getenv('UPLOAD_FOLDER', 'static/uploads')
    
    # Check both relative and absolute paths
    paths_to_check = [upload_folder, f'DiagnoseAI/{upload_folder}']
    upload_exists = False
    
    for path in paths_to_check:
        if os.path.exists(path):
            upload_exists = True
            upload_folder = path
            break
    
    if upload_exists:
        print(f"   ✅ Upload folder exists: {upload_folder}")
        
        # Count files in upload directory
        file_count = 0
        for root, dirs, files in os.walk(upload_folder):
            file_count += len(files)
        
        print(f"   📊 Files in upload directory: {file_count}")
        
        # Check instance/uploads as well
        instance_uploads = 'instance/uploads'
        if os.path.exists(instance_uploads):
            instance_file_count = 0
            for root, dirs, files in os.walk(instance_uploads):
                instance_file_count += len(files)
            print(f"   📊 Files in instance/uploads: {instance_file_count}")
            
            # List recent uploads
            if instance_file_count > 0:
                print("   📋 Recent uploads:")
                for root, dirs, files in os.walk(instance_uploads):
                    for file in files[-3:]:  # Show last 3 files
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        print(f"      • {file} ({size} bytes)")
    else:
        print(f"   ❌ Upload folder not found: {upload_folder}")

def check_recent_cases():
    """Check recent cases and their status."""
    print("\n📋 Recent Cases:")
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.models import Case
            
            recent_cases = Case.query.order_by(Case.created_at.desc()).limit(5).all()
            
            if recent_cases:
                for case in recent_cases:
                    print(f"   📄 Case #{case.id}: {case.status} ({case.created_at})")
                    if case.reports:
                        print(f"      📝 Report: {'Finalized' if case.reports[0].is_finalized else 'Draft'}")
                    else:
                        print(f"      ❌ No report generated")
            else:
                print("   📭 No cases found")
                
    except Exception as e:
        print(f"   ❌ Error checking cases: {e}")

def main():
    """Run all diagnostic checks."""
    print("🔍 DiagnoseAI Application Diagnostics")
    print("=" * 40)
    
    check_environment()
    check_database()
    check_uploads()
    check_recent_cases()
    
    print("\n💡 Troubleshooting Tips:")
    print("   • If uploads are hanging, check OpenAI API connectivity")
    print("   • Check server logs for detailed error messages")
    print("   • Ensure all required environment variables are set")
    print("   • Verify database is running and accessible")

if __name__ == '__main__':
    main()