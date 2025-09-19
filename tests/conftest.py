import pytest
import tempfile
import os
from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create app with testing configuration using PostgreSQL
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_migrate import Migrate
    from flask_login import LoginManager
    import os
    
    # Set template folder to tests/templates
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    app = Flask(__name__, template_folder=template_dir)
    
    # Use a separate test database
    test_db_url = 'postgresql://diagnoseai_user:diagnoseai_pass@localhost:5432/diagnoseai_test'
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': test_db_url,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key'
    })
    
    # Initialize extensions
    from app import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    with app.app_context():
        # Create test database if it doesn't exist
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import ProgrammingError
        
        # Connect to postgres database to create test database
        admin_engine = create_engine('postgresql://diagnoseai_user:diagnoseai_pass@localhost:5432/diagnoseai')
        with admin_engine.connect() as conn:
            conn.execute(text("COMMIT"))  # End any existing transaction
            try:
                conn.execute(text("CREATE DATABASE diagnoseai_test"))
            except ProgrammingError:
                # Database already exists
                pass
        
        # Now create tables in test database
        db.create_all()
        yield app
        
        # Clean up: drop all tables
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def user(app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        return user