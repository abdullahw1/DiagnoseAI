#!/usr/bin/env python3
"""
Create an admin user for testing the application locally.
"""
import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import User

# Load environment variables
load_dotenv()

def create_admin_user():
    """Create an admin user for testing."""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("✅ Admin user already exists!")
            print("   Username: admin")
            print("   Email: admin@diagnoseai.local")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@diagnoseai.local',
            first_name='Admin',
            last_name='User'
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@diagnoseai.local")
        print("\n🔐 Please change the password after first login!")

if __name__ == '__main__':
    create_admin_user()