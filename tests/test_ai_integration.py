"""
Integration tests for AI service integration with case creation workflow.

Tests the complete flow from case upload to AI report generation.
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock
from io import BytesIO
from PIL import Image
from app.models import User, Case, Report
from app.ai_service import AIServiceError


class TestAIIntegration:
    """Integration tests for AI service with case workflow."""
    
    def test_case_creation_with_successful_ai_generation(self, client, auth, app):
        """Test case creation triggers successful AI report generation."""
        # Login as test user
        auth.login()
        
        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        image.save(img_io, 'JPEG')
        img_io.seek(0)
        
        # Mock the AI service
        mock_raw_response = {
            "id": "chatcmpl-test123",
            "model": "gpt-4o",
            "choices": [{
                "message": {
                    "content": "Test AI-generated radiology report with findings and recommendations."
                }
            }],
            "usage": {"total_tokens": 150}
        }
        
        with patch('app.main.generate_draft_report') as mock_generate:
            mock_generate.return_value = (
                mock_raw_response,
                "Test AI-generated radiology report with findings and recommendations."
            )
            
            # Submit upload form
            response = client.post('/upload', data={
                'image': (img_io, 'test_ultrasound.jpg'),
                'clinical_notes': 'Patient presents with abdominal pain. Rule out gallbladder pathology.',
                'csrf_token': 'test-token'  # This would be handled by WTF-Forms in real scenario
            }, follow_redirects=True)
            
            # Verify successful upload and redirect
            assert response.status_code == 200
            assert b'created successfully' in response.data
            assert b'AI draft report has been generated' in response.data
            
            # Verify database records
            with app.app_context():
                case = Case.query.first()
                assert case is not None
                assert case.status == 'draft_ready'
                assert case.clinical_notes == 'Patient presents with abdominal pain. Rule out gallbladder pathology.'
                
                report = Report.query.filter_by(case_id=case.id).first()
                assert report is not None
                assert report.draft_json == mock_raw_response
                assert report.draft_text == "Test AI-generated radiology report with findings and recommendations."
                assert report.is_finalized is False
                
                # Verify AI service was called correctly
                mock_generate.assert_called_once_with(
                    image_path=case.image_path,
                    clinical_notes=case.clinical_notes
                )
    
    def test_case_creation_with_ai_service_error(self, client, auth, app):
        """Test case creation handles AI service errors gracefully."""
        # Login as test user
        auth.login()
        
        # Create a test image
        image = Image.new('RGB', (100, 100), color='blue')
        img_io = BytesIO()
        image.save(img_io, 'JPEG')
        img_io.seek(0)
        
        # Mock AI service to raise an error
        with patch('app.main.generate_draft_report') as mock_generate:
            mock_generate.side_effect = AIServiceError("OpenAI API rate limit exceeded")
            
            # Submit upload form
            response = client.post('/upload', data={
                'image': (img_io, 'test_ultrasound.jpg'),
                'clinical_notes': 'Test clinical notes for error scenario.',
                'csrf_token': 'test-token'
            }, follow_redirects=True)
            
            # Verify upload succeeded but AI generation failed
            assert response.status_code == 200
            assert b'created successfully' in response.data
            assert b'AI report generation failed' in response.data
            assert b'marked for manual review' in response.data
            
            # Verify database state
            with app.app_context():
                case = Case.query.first()
                assert case is not None
                assert case.status == 'ai_failed'
                assert case.clinical_notes == 'Test clinical notes for error scenario.'
                
                # No report should be created on AI failure
                report = Report.query.filter_by(case_id=case.id).first()
                assert report is None
    
    def test_case_creation_with_unexpected_error(self, client, auth, app):
        """Test case creation handles unexpected errors during AI generation."""
        # Login as test user
        auth.login()
        
        # Create a test image
        image = Image.new('RGB', (100, 100), color='green')
        img_io = BytesIO()
        image.save(img_io, 'JPEG')
        img_io.seek(0)
        
        # Mock AI service to raise an unexpected error
        with patch('app.main.generate_draft_report') as mock_generate:
            mock_generate.side_effect = Exception("Unexpected database connection error")
            
            # Submit upload form
            response = client.post('/upload', data={
                'image': (img_io, 'test_ultrasound.jpg'),
                'clinical_notes': 'Test notes for unexpected error.',
                'csrf_token': 'test-token'
            }, follow_redirects=True)
            
            # Verify upload succeeded but AI generation failed
            assert response.status_code == 200
            assert b'created successfully' in response.data
            assert b'AI report generation encountered an error' in response.data
            
            # Verify database state
            with app.app_context():
                case = Case.query.first()
                assert case is not None
                assert case.status == 'ai_failed'
    
    def test_case_detail_view_with_draft_report(self, client, auth, app):
        """Test case detail view displays AI-generated draft report."""
        # Login and create a case with report
        auth.login()
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # Create case
            case = Case(
                user_id=user.id,
                image_filename='test_image.jpg',
                image_path='/fake/path/test_image.jpg',
                clinical_notes='Test clinical notes for viewing.',
                status='draft_ready'
            )
            from app import db
            db.session.add(case)
            db.session.flush()
            
            # Create report
            report = Report(
                case_id=case.id,
                draft_json={"test": "json_data"},
                draft_text="TECHNICAL QUALITY: Good image quality.\n\nFINDINGS: Normal findings.\n\nIMPRESSION: Normal study.",
                is_finalized=False
            )
            db.session.add(report)
            db.session.commit()
            
            case_id = case.id
        
        # View the case
        response = client.get(f'/case/{case_id}')
        assert response.status_code == 200
        
        # Verify draft report is displayed
        assert b'AI-Generated Draft Report' in response.data
        assert b'TECHNICAL QUALITY: Good image quality.' in response.data
        assert b'FINDINGS: Normal findings.' in response.data
        assert b'IMPRESSION: Normal study.' in response.data
        assert b'Draft - Requires Review' in response.data
        assert b'preliminary report that requires review' in response.data
    
    def test_case_detail_view_with_finalized_report(self, client, auth, app):
        """Test case detail view displays finalized report correctly."""
        # Login and create a case with finalized report
        auth.login()
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # Create case
            case = Case(
                user_id=user.id,
                image_filename='test_finalized.jpg',
                image_path='/fake/path/test_finalized.jpg',
                clinical_notes='Clinical notes for finalized case.',
                status='draft_ready'
            )
            from app import db
            db.session.add(case)
            db.session.flush()
            
            # Create finalized report
            report = Report(
                case_id=case.id,
                draft_json={"test": "json_data"},
                draft_text="Original AI draft text",
                final_text="Reviewed and finalized report text",
                is_finalized=True
            )
            db.session.add(report)
            db.session.commit()
            
            case_id = case.id
        
        # View the case
        response = client.get(f'/case/{case_id}')
        assert response.status_code == 200
        
        # Verify finalized report is displayed
        assert b'AI-Generated Draft Report' in response.data
        assert b'Finalized' in response.data
        assert b'Original AI draft text' in response.data  # Should show draft text
        assert b'Report Completed' in response.data
    
    def test_case_detail_view_ai_failed_status(self, client, auth, app):
        """Test case detail view for cases where AI generation failed."""
        # Login and create a case with AI failure
        auth.login()
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # Create case with AI failure status
            case = Case(
                user_id=user.id,
                image_filename='test_failed.jpg',
                image_path='/fake/path/test_failed.jpg',
                clinical_notes='Clinical notes for failed AI case.',
                status='ai_failed'
            )
            from app import db
            db.session.add(case)
            db.session.commit()
            
            case_id = case.id
        
        # View the case
        response = client.get(f'/case/{case_id}')
        assert response.status_code == 200
        
        # Verify AI failure status is displayed
        assert b'AI Generation Failed' in response.data
        assert b'marked for manual review' in response.data
        assert b'AI-Generated Draft Report' not in response.data
    
    def test_dashboard_status_display(self, client, auth, app):
        """Test dashboard displays correct status for different case types."""
        # Login and create various case types
        auth.login()
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            from app import db
            
            # Case 1: Uploaded (processing)
            case1 = Case(
                user_id=user.id,
                image_filename='processing.jpg',
                image_path='/fake/path/processing.jpg',
                clinical_notes='Processing case',
                status='uploaded'
            )
            db.session.add(case1)
            
            # Case 2: Draft ready
            case2 = Case(
                user_id=user.id,
                image_filename='draft_ready.jpg',
                image_path='/fake/path/draft_ready.jpg',
                clinical_notes='Draft ready case',
                status='draft_ready'
            )
            db.session.add(case2)
            db.session.flush()
            
            report2 = Report(
                case_id=case2.id,
                draft_json={"test": "data"},
                draft_text="Draft report text",
                is_finalized=False
            )
            db.session.add(report2)
            
            # Case 3: AI failed
            case3 = Case(
                user_id=user.id,
                image_filename='ai_failed.jpg',
                image_path='/fake/path/ai_failed.jpg',
                clinical_notes='AI failed case',
                status='ai_failed'
            )
            db.session.add(case3)
            
            # Case 4: Completed
            case4 = Case(
                user_id=user.id,
                image_filename='completed.jpg',
                image_path='/fake/path/completed.jpg',
                clinical_notes='Completed case',
                status='draft_ready'
            )
            db.session.add(case4)
            db.session.flush()
            
            report4 = Report(
                case_id=case4.id,
                draft_json={"test": "data"},
                draft_text="Draft text",
                final_text="Final text",
                is_finalized=True
            )
            db.session.add(report4)
            
            db.session.commit()
        
        # View dashboard
        response = client.get('/dashboard')
        assert response.status_code == 200
        
        # Verify status badges are displayed correctly
        assert b'Processing' in response.data
        assert b'Draft Ready' in response.data
        assert b'AI Failed' in response.data
        assert b'Completed' in response.data
        
        # Verify statistics
        assert b'Total Cases' in response.data
        assert b'4</h2>' in response.data  # Total cases count
        assert b'Completed Reports' in response.data
        assert b'1</h2>' in response.data  # Completed reports count (case4)
        assert b'Pending Review' in response.data
        assert b'3</h2>' in response.data  # Pending review count (cases 1, 2, 3)


class TestAIServiceEnvironmentConfiguration:
    """Test AI service configuration in different environments."""
    
    def test_ai_service_with_missing_env_var(self, app):
        """Test AI service behavior when environment variable is missing."""
        with app.app_context():
            # Remove the OpenAI API key from environment
            with patch.dict(os.environ, {}, clear=True):
                with patch('app.ai_service.AIService') as mock_service_class:
                    mock_service_class.side_effect = AIServiceError("OpenAI API key not configured")
                    
                    # Import should still work, but service initialization should fail
                    from app.ai_service import generate_draft_report
                    
                    with pytest.raises(AIServiceError):
                        generate_draft_report("/fake/path.jpg", "test notes")
    
    def test_ai_service_logging(self, app, caplog):
        """Test that AI service logs appropriate messages."""
        with app.app_context():
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                with patch('app.ai_service.OpenAI') as mock_openai:
                    mock_client = Mock()
                    mock_openai.return_value = mock_client
                    
                    # Test successful initialization logging
                    from app.ai_service import AIService
                    service = AIService()
                    
                    # Check that initialization was logged
                    assert "OpenAI client initialized successfully" in caplog.text