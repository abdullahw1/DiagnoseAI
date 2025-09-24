import pytest
import tempfile
import os
from app.models import User, Case, Report
from app import db


class TestReportEditing:
    """Test cases for report editing and finalization functionality."""
    
    def test_edit_report_page_access_requires_login(self, client):
        """Test that edit report page requires authentication."""
        response = client.get('/case/1/edit')
        assert response.status_code == 302  # Redirect to login
        assert '/auth/login' in response.location
    
    def test_edit_report_page_with_invalid_case(self, client, auth, user):
        """Test accessing edit page for non-existent case."""
        auth.login()
        response = client.get('/case/999/edit')
        assert response.status_code == 404
    
    def test_edit_report_page_without_report(self, client, auth, user, app):
        """Test accessing edit page for case without report."""
        with app.app_context():
            # Create a case without a report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='uploaded'
            )
            db.session.add(case)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        response = client.get(f'/case/{case_id}/edit', follow_redirects=True)
        assert b'No report found for this case' in response.data
    
    def test_edit_report_page_with_finalized_report(self, client, auth, user, app):
        """Test accessing edit page for finalized report."""
        with app.app_context():
            # Create a case with finalized report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='completed'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='AI generated draft',
                final_text='Finalized report',
                is_finalized=True
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        response = client.get(f'/case/{case_id}/edit', follow_redirects=True)
        assert b'already been finalized' in response.data
    
    def test_edit_report_page_displays_correctly(self, client, auth, user, app):
        """Test that edit report page displays correctly for draft report."""
        with app.app_context():
            # Create a case with draft report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test clinical notes',
                status='draft_ready'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='AI generated draft report content',
                is_finalized=False
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        response = client.get(f'/case/{case_id}/edit')
        assert response.status_code == 200
        assert b'Edit Report - Case #' in response.data
        assert b'AI generated draft report content' in response.data
        assert b'Test clinical notes' in response.data
    
    def test_save_draft_report(self, client, auth, user, app):
        """Test saving draft report changes."""
        with app.app_context():
            # Create a case with draft report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='draft_ready'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='Original draft',
                is_finalized=False
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        
        # Submit edited report as draft
        response = client.post(f'/case/{case_id}/edit', data={
            'report_text': 'Edited draft report content',
            'case_id': case_id,
            'save_draft': 'Save Draft'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Draft report' in response.data
        assert b'saved successfully' in response.data
        
        # Verify changes in database
        with app.app_context():
            updated_report = Report.query.filter_by(case_id=case_id).first()
            updated_case = Case.query.get(case_id)
            assert updated_report.final_text == 'Edited draft report content'
            assert not updated_report.is_finalized
            assert updated_case.status == 'draft_edited'
    
    def test_finalize_report(self, client, auth, user, app):
        """Test finalizing a report."""
        with app.app_context():
            # Create a case with draft report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='draft_ready'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='Original draft',
                is_finalized=False
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        
        # Submit finalized report
        response = client.post(f'/case/{case_id}/edit', data={
            'report_text': 'Final report content',
            'case_id': case_id,
            'finalize_report': 'Finalize Report'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'finalized successfully' in response.data
        
        # Verify changes in database
        with app.app_context():
            updated_report = Report.query.filter_by(case_id=case_id).first()
            updated_case = Case.query.get(case_id)
            assert updated_report.final_text == 'Final report content'
            assert updated_report.is_finalized
            assert updated_case.status == 'completed'
    
    def test_form_validation_empty_report(self, client, auth, user, app):
        """Test form validation for empty report content."""
        with app.app_context():
            # Create a case with draft report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='draft_ready'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='Original draft',
                is_finalized=False
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        
        # Submit empty report
        response = client.post(f'/case/{case_id}/edit', data={
            'report_text': '',
            'case_id': case_id,
            'save_draft': 'Save Draft'
        })
        
        assert response.status_code == 200
        assert b'Report content is required' in response.data
    
    def test_form_validation_report_too_short(self, client, auth, user, app):
        """Test form validation for report content that's too short."""
        with app.app_context():
            # Create a case with draft report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='draft_ready'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='Original draft',
                is_finalized=False
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        
        # Submit report that's too short
        response = client.post(f'/case/{case_id}/edit', data={
            'report_text': 'Too short',
            'case_id': case_id,
            'save_draft': 'Save Draft'
        })
        
        assert response.status_code == 200
        assert b'must be between 50 and 5000 characters' in response.data
    
    def test_case_detail_shows_edit_button_for_draft(self, client, auth, user, app):
        """Test that case detail page shows edit button for draft reports."""
        with app.app_context():
            # Create a case with draft report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='draft_ready'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='Draft report content',
                is_finalized=False
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        response = client.get(f'/case/{case_id}')
        
        assert response.status_code == 200
        assert b'Review &amp; Edit Report' in response.data
        assert f'/case/{case_id}/edit'.encode() in response.data
    
    def test_case_detail_shows_finalized_status(self, client, auth, user, app):
        """Test that case detail page shows correct status for finalized reports."""
        with app.app_context():
            # Create a case with finalized report
            case = Case(
                user_id=user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='completed'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='Original draft',
                final_text='Final report content',
                is_finalized=True
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        auth.login()
        response = client.get(f'/case/{case_id}')
        
        assert response.status_code == 200
        assert b'Final Report' in response.data
        assert b'Finalized' in response.data
        assert b'Final report content' in response.data
        assert b'Review &amp; Edit Report' not in response.data
    
    def test_user_can_only_edit_own_reports(self, client, auth, user, app):
        """Test that users can only edit their own reports."""
        with app.app_context():
            # Create another user
            other_user = User(username='otheruser', email='other@example.com')
            other_user.set_password('password')
            db.session.add(other_user)
            db.session.flush()
            
            # Create a case for the other user
            case = Case(
                user_id=other_user.id,
                image_filename='test.jpg',
                image_path='/test/path/test.jpg',
                clinical_notes='Test notes',
                status='draft_ready'
            )
            db.session.add(case)
            db.session.flush()
            
            report = Report(
                case_id=case.id,
                draft_text='Draft report',
                is_finalized=False
            )
            db.session.add(report)
            db.session.commit()
            case_id = case.id
        
        # Login as the first user and try to access other user's case
        auth.login()
        response = client.get(f'/case/{case_id}/edit')
        assert response.status_code == 404