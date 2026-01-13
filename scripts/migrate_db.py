#!/usr/bin/env python3
"""
Database Migration Script for DiagnoseAI
Handles database initialization and migrations
"""

import os
import sys
from flask import Flask
from flask_migrate import upgrade, init, migrate
from app import create_app, db
from app.models import User, Patient, Case, Report

def run_migrations():
    """Run database migrations"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if migrations directory exists
            if not os.path.exists('migrations'):
                print("🔧 Initializing migration repository...")
                init()
                print("✅ Migration repository initialized")
            
            # Run migrations
            print("🔄 Running database migrations...")
            upgrade()
            print("✅ Database migrations completed successfully")
            
            # Create tables if they don't exist
            db.create_all()
            print("✅ Database tables created/verified")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False

def create_admin_user():
    """Create an admin user if none exists"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if any users exist
            if User.query.count() == 0:
                print("👤 Creating default admin user...")
                admin = User(
                    username='admin',
                    email='admin@hospital.com',
                    first_name='System',
                    last_name='Administrator',
                    title='Dr.',
                    department='Radiology'
                )
                admin.set_password('admin123')  # Change this in production!
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created (username: admin, password: admin123)")
                print("⚠️  IMPORTANT: Change the admin password after first login!")
            else:
                print("👤 Users already exist, skipping admin creation")
                
        except Exception as e:
            print(f"❌ Failed to create admin user: {str(e)}")

if __name__ == '__main__':
    print("🏥 DiagnoseAI Database Migration")
    print("================================")
    
    if run_migrations():
        create_admin_user()
        print("\n🎉 Database setup completed successfully!")
        print("📝 Next steps:")
        print("   1. Start the application")
        print("   2. Login with admin/admin123")
        print("   3. Change the admin password")
        print("   4. Create your hospital users")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)