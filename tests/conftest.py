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
    
    # Create temporary directory for test uploads
    temp_dir = tempfile.mkdtemp()
    
    # Use SQLite for testing (simpler setup)
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-secret-key',
        'UPLOAD_FOLDER': temp_dir,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024
    })
    
    # Initialize extensions
    from app import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register custom template filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks."""
        if text is None:
            return ''
        return text.replace('\n', '<br>\n')
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    with app.app_context():
        # Create tables in test database
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

class AuthActions:
    """Helper class for authentication actions in tests."""
    
    def __init__(self, client):
        self._client = client
    
    def login(self, username='testuser', password='testpassword'):
        """Log in a user."""
        return self._client.post('/auth/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        """Log out the current user."""
        return self._client.get('/auth/logout', follow_redirects=True)
    
    def get_csrf_token(self, url):
        """Get CSRF token from a form page."""
        response = self._client.get(url)
        # For testing, we'll return a dummy token since CSRF is disabled
        return 'test-csrf-token'

@pytest.fixture
def auth(client, user):
    """Authentication helper fixture."""
    return AuthActions(client)