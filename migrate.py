#!/usr/bin/env python
"""Run database migrations"""
from app import create_app, db
from flask_migrate import upgrade

app = create_app()

with app.app_context():
    print("Running database migrations...")
    upgrade()
    print("Migrations completed successfully!")
