import pytest
from flask import url_for
from app import db
from app.models import User

class TestUserModel:
    """Test User model functionality."""
    
    def test_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('testpassword')
            
            # Password should be hashed, not stored in plain text
            assert user.password_hash != 'testpassword'
            assert len(user.password_hash) > 0
            
            # Should be able to verify correct password
            assert user.check_password('testpassword') is True
            
            # Should reject incorrect password
            assert user.check_password('wrongpassword') is False
    
    def test_user_creation(self, app):
        """Test user creation and database storage."""
        with app.app_context():
            user = User(username='newuser', email='new@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # User should be retrievable from database
            retrieved_user = User.query.filter_by(username='newuser').first()
            assert retrieved_user is not None
            assert retrieved_user.email == 'new@example.com'
            assert retrieved_user.check_password('password123') is True

class TestAuthRoutes:
    """Test authentication routes."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads correctly."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data
        assert b'Username' in response.data
        assert b'Password' in response.data
    
    def test_register_page_loads(self, client):
        """Test that registration page loads correctly."""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Register' in response.data
        assert b'Username' in response.data
        assert b'Email' in response.data
        assert b'Password' in response.data
    
    def test_successful_registration(self, client, app):
        """Test successful user registration."""
        response = client.post('/auth/register', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123',
            'submit': 'Register'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Registration successful' in response.data
        
        # Verify user was created in database
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.email == 'new@example.com'
    
    def test_duplicate_username_registration(self, client, user):
        """Test registration with duplicate username."""
        response = client.post('/auth/register', data={
            'username': 'testuser',  # Same as fixture user
            'email': 'different@example.com',
            'password': 'password123',
            'submit': 'Register'
        })
        
        assert response.status_code == 200
        assert b'Username already exists' in response.data
    
    def test_duplicate_email_registration(self, client, user):
        """Test registration with duplicate email."""
        response = client.post('/auth/register', data={
            'username': 'differentuser',
            'email': 'test@example.com',  # Same as fixture user
            'password': 'password123',
            'submit': 'Register'
        })
        
        assert response.status_code == 200
        assert b'Email already registered' in response.data
    
    def test_successful_login(self, client, user):
        """Test successful user login."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword',
            'submit': 'Sign In'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Login successful' in response.data
        assert b'Dashboard' in response.data
    
    def test_invalid_login_credentials(self, client, user):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'wrongpassword',
            'submit': 'Sign In'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_nonexistent_user_login(self, client):
        """Test login with nonexistent user."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'password',
            'submit': 'Sign In'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_logout(self, client, user):
        """Test user logout functionality."""
        # First login
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword',
            'submit': 'Sign In'
        })
        
        # Then logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'You have been logged out' in response.data
        assert b'Sign In' in response.data  # Should be back to login page

class TestAuthenticationRequired:
    """Test authentication requirements for protected routes."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard redirects to login when not authenticated."""
        response = client.get('/dashboard')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_dashboard_accessible_when_logged_in(self, client, user):
        """Test that dashboard is accessible when logged in."""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpassword',
            'submit': 'Sign In'
        })
        
        # Access dashboard
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_logout_requires_login(self, client):
        """Test that logout route requires authentication."""
        response = client.get('/auth/logout')
        assert response.status_code == 302
        assert '/auth/login' in response.location

class TestFormValidation:
    """Test form validation."""
    
    def test_login_form_validation(self, client):
        """Test login form validation."""
        # Empty form
        response = client.post('/auth/login', data={
            'submit': 'Sign In'
        })
        assert response.status_code == 200
        # Should stay on login page with validation errors
        assert b'Sign In' in response.data
    
    def test_registration_form_validation(self, client):
        """Test registration form validation."""
        # Password too short
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123',  # Too short
            'submit': 'Register'
        })
        assert response.status_code == 200
        # Should stay on registration page
        assert b'Register' in response.data
        
        # Invalid email
        response = client.post('/auth/register', data={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'password123',
            'submit': 'Register'
        })
        assert response.status_code == 200
        assert b'Register' in response.data