from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://diagnoseai_user:diagnoseai_pass@localhost:5432/diagnoseai')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.instance_path, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Import models to ensure they're registered with SQLAlchemy
    from app import models
    
    # Register custom template filters
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks."""
        if text is None:
            return ''
        return text.replace('\n', '<br>\n')
    
    @app.template_filter('markdown_to_html')
    def markdown_to_html_filter(text):
        """Convert basic markdown formatting to HTML."""
        if text is None:
            return ''
        
        import re
        from markupsafe import Markup
        
        # Convert **bold** to <strong>bold</strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        
        # Convert *italic* to <em>italic</em> (but not if it's already inside ** tags)
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
        
        # Convert numbered sections like "1. SECTION:" to styled headers
        text = re.sub(r'^(\d+\.\s+)([A-Z\s:]+)$', r'<div class="report-section"><strong>\1\2</strong></div>', text, flags=re.MULTILINE)
        
        # Convert double newlines to paragraph breaks
        text = re.sub(r'\n\s*\n', '<br><br>', text)
        
        # Convert single newlines to <br> tags
        text = text.replace('\n', '<br>')
        
        # Return as safe HTML
        return Markup(text)
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    return app