import pytest
import os
import tempfile
from io import BytesIO
from PIL import Image
from flask import url_for
from app.models import User, Case
from app import db

class TestFileUpload:
    """Test file upload functionality."""
    
    def create_test_image(self, format='JPEG', size=(100, 100)):
        """Create a test image file in memory."""
        img = Image.new('RGB', size, color='red')
        img_io = BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        return img_io
    
    def test_upload_page_requires_login(self, client):
        """Test that upload page requires authentication."""
        response = client.get('/upload')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_upload_page_loads_for_authenticated_user(self, client, auth):
        """Test that upload page loads for authenticated users."""
        auth.login()
        response = client.get('/upload')
        assert response.status_code == 200
        assert b'Upload Ultrasound Image' in response.data
        assert b'Clinical Notes' in response.data
    
    def test_successful_image_upload(self, client, auth, app):
        """Test successful image upload and case creation."""
        auth.login()
        
        # Create test image
        test_image = self.create_test_image()
        
        # Submit upload form
        response = client.post('/upload', data={
            'image': (test_image, 'test_ultrasound.jpg'),
            'clinical_notes': 'Patient presents with abdominal pain. Requesting ultrasound examination.',
            'csrf_token': auth.get_csrf_token('/upload')
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully' in response.data
        
        # Verify case was created in database
        with app.app_context():
            case = Case.query.first()
            assert case is not None
            assert case.user_id == 1  # First user
            assert 'test_ultrasound.jpg' in case.image_filename
            assert case.clinical_notes == 'Patient presents with abdominal pain. Requesting ultrasound examination.'
            assert case.status == 'uploaded'
    
    def test_upload_without_image(self, client, auth):
        """Test upload form validation when no image is provided."""
        auth.login()
        
        response = client.post('/upload', data={
            'clinical_notes': 'Test clinical notes',
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        assert response.status_code == 200
        assert b'Please select an image file' in response.data
    
    def test_upload_without_clinical_notes(self, client, auth):
        """Test upload form validation when no clinical notes are provided."""
        auth.login()
        
        test_image = self.create_test_image()
        
        response = client.post('/upload', data={
            'image': (test_image, 'test.jpg'),
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        assert response.status_code == 200
        assert b'Clinical notes are required' in response.data
    
    def test_upload_invalid_file_type(self, client, auth):
        """Test upload validation for invalid file types."""
        auth.login()
        
        # Create a text file instead of image
        text_file = BytesIO(b'This is not an image file')
        
        response = client.post('/upload', data={
            'image': (text_file, 'test.txt'),
            'clinical_notes': 'Test clinical notes for invalid file',
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        assert response.status_code == 200
        assert b'Only image files are allowed' in response.data
    
    def test_upload_clinical_notes_too_short(self, client, auth):
        """Test validation for clinical notes that are too short."""
        auth.login()
        
        test_image = self.create_test_image()
        
        response = client.post('/upload', data={
            'image': (test_image, 'test.jpg'),
            'clinical_notes': 'Short',  # Less than 10 characters
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        assert response.status_code == 200
        assert b'Clinical notes must be between 10 and 2000 characters' in response.data
    
    def test_upload_clinical_notes_too_long(self, client, auth):
        """Test validation for clinical notes that are too long."""
        auth.login()
        
        test_image = self.create_test_image()
        long_notes = 'A' * 2001  # More than 2000 characters
        
        response = client.post('/upload', data={
            'image': (test_image, 'test.jpg'),
            'clinical_notes': long_notes,
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        assert response.status_code == 200
        assert b'Clinical notes must be between 10 and 2000 characters' in response.data
    
    def test_upload_creates_user_directory(self, client, auth, app):
        """Test that upload creates user-specific directory."""
        auth.login()
        
        test_image = self.create_test_image()
        
        client.post('/upload', data={
            'image': (test_image, 'test.jpg'),
            'clinical_notes': 'Test clinical notes for directory creation',
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        # Check that user directory was created
        with app.app_context():
            user_dir = os.path.join(app.config['UPLOAD_FOLDER'], '1')
            assert os.path.exists(user_dir)
    
    def test_upload_filename_security(self, client, auth, app):
        """Test that uploaded filenames are properly secured."""
        auth.login()
        
        test_image = self.create_test_image()
        
        # Try to upload with malicious filename
        client.post('/upload', data={
            'image': (test_image, '../../../malicious.jpg'),
            'clinical_notes': 'Test clinical notes for filename security',
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        with app.app_context():
            case = Case.query.first()
            assert case is not None
            # Filename should be sanitized and not contain path traversal
            assert '../' not in case.image_filename
            assert 'malicious.jpg' in case.image_filename
    
    def test_multiple_uploads_different_filenames(self, client, auth, app):
        """Test that multiple uploads get different filenames."""
        auth.login()
        
        # Upload first image
        test_image1 = self.create_test_image()
        client.post('/upload', data={
            'image': (test_image1, 'same_name.jpg'),
            'clinical_notes': 'First upload with same filename',
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        # Upload second image with same name
        test_image2 = self.create_test_image()
        client.post('/upload', data={
            'image': (test_image2, 'same_name.jpg'),
            'clinical_notes': 'Second upload with same filename',
            'csrf_token': auth.get_csrf_token('/upload')
        })
        
        with app.app_context():
            cases = Case.query.all()
            assert len(cases) == 2
            # Filenames should be different due to timestamp
            assert cases[0].image_filename != cases[1].image_filename
            assert 'same_name.jpg' in cases[0].image_filename
            assert 'same_name.jpg' in cases[1].image_filename


class TestCaseManagement:
    """Test case management functionality."""
    
    def test_dashboard_shows_user_cases_only(self, client, auth, app):
        """Test that dashboard only shows cases for the current user."""
        # Create two users and cases
        with app.app_context():
            user1 = User(username='user1', email='user1@test.com')
            user1.set_password('password')
            user2 = User(username='user2', email='user2@test.com')
            user2.set_password('password')
            
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            case1 = Case(user_id=user1.id, image_filename='user1_image.jpg', 
                        image_path='/path/to/user1_image.jpg', clinical_notes='User 1 notes')
            case2 = Case(user_id=user2.id, image_filename='user2_image.jpg',
                        image_path='/path/to/user2_image.jpg', clinical_notes='User 2 notes')
            
            db.session.add(case1)
            db.session.add(case2)
            db.session.commit()
        
        # Login as user1 and check dashboard
        auth.login(username='user1', password='password')
        response = client.get('/dashboard')
        
        assert response.status_code == 200
        assert b'user1_image.jpg' in response.data
        assert b'user2_image.jpg' not in response.data
    
    def test_case_detail_view(self, client, auth, app):
        """Test case detail view functionality."""
        auth.login()
        
        # Create a test case
        with app.app_context():
            user = User.query.first()
            case = Case(
                user_id=user.id,
                image_filename='test_detail.jpg',
                image_path='/path/to/test_detail.jpg',
                clinical_notes='Detailed clinical notes for testing\nWith multiple lines'
            )
            db.session.add(case)
            db.session.commit()
            case_id = case.id
        
        # View case detail
        response = client.get(f'/case/{case_id}')
        
        assert response.status_code == 200
        assert b'Case #' in response.data
        assert b'test_detail.jpg' in response.data
        assert b'Detailed clinical notes for testing' in response.data
        assert b'With multiple lines' in response.data
    
    def test_case_detail_access_control(self, client, auth, app):
        """Test that users can only view their own cases."""
        # Create two users
        with app.app_context():
            user1 = User(username='user1', email='user1@test.com')
            user1.set_password('password')
            user2 = User(username='user2', email='user2@test.com')
            user2.set_password('password')
            
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()
            
            # Create case for user2
            case = Case(
                user_id=user2.id,
                image_filename='private_case.jpg',
                image_path='/path/to/private_case.jpg',
                clinical_notes='Private case notes'
            )
            db.session.add(case)
            db.session.commit()
            case_id = case.id
        
        # Login as user1 and try to access user2's case
        auth.login(username='user1', password='password')
        response = client.get(f'/case/{case_id}')
        
        assert response.status_code == 404
    
    def test_dashboard_case_statistics(self, client, auth, app):
        """Test that dashboard shows correct case statistics."""
        auth.login()
        
        # Create test cases with different statuses
        with app.app_context():
            user = User.query.first()
            
            # Case with no report
            case1 = Case(user_id=user.id, image_filename='case1.jpg', 
                        image_path='/path/case1.jpg', clinical_notes='Notes 1')
            
            # Case with draft report
            case2 = Case(user_id=user.id, image_filename='case2.jpg',
                        image_path='/path/case2.jpg', clinical_notes='Notes 2')
            
            # Case with finalized report
            case3 = Case(user_id=user.id, image_filename='case3.jpg',
                        image_path='/path/case3.jpg', clinical_notes='Notes 3')
            
            db.session.add_all([case1, case2, case3])
            db.session.commit()
            
            # Add reports
            from app.models import Report
            
            draft_report = Report(case_id=case2.id, draft_text='Draft report', is_finalized=False)
            final_report = Report(case_id=case3.id, final_text='Final report', is_finalized=True)
            
            db.session.add_all([draft_report, final_report])
            db.session.commit()
        
        response = client.get('/dashboard')
        
        assert response.status_code == 200
        # Should show 3 total cases, 1 completed, 2 pending
        assert b'<h2>3</h2>' in response.data  # Total cases
        assert b'<h2>1</h2>' in response.data  # Completed reports
        assert b'<h2>2</h2>' in response.data  # Pending review
    
    def test_empty_dashboard(self, client, auth):
        """Test dashboard display when user has no cases."""
        auth.login()
        
        response = client.get('/dashboard')
        
        assert response.status_code == 200
        assert b'No cases yet' in response.data
        assert b'Upload your first ultrasound image' in response.data