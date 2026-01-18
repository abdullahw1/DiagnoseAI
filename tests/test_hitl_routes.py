"""
Unit tests for Human-in-the-Loop (HITL) review interface routes.

Tests the approve, modify, and reject routes for AI-generated reports.
"""

import pytest
from datetime import datetime
from app import db
from app.models import User, Case, Report, Feedback, Patient


@pytest.fixture
def test_user(app):
    """Create a test user and return user_id."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    return user_id


@pytest.fixture
def test_patient(app, test_user):
    """Create a test patient and return patient_id."""
    with app.app_context():
        patient = Patient(
            patient_id='TEST001',
            first_name='Test',
            last_name='Patient',
            created_by=test_user
        )
        db.session.add(patient)
        db.session.commit()
        patient_id = patient.id
    return patient_id


@pytest.fixture
def test_case_with_report(app, test_user, test_patient):
    """Create a test case with an AI-generated report and return case_id."""
    with app.app_context():
        case = Case(
            case_number='000001',
            user_id=test_user,
            patient_id=test_patient,
            image_filename='test.jpg',
            image_path='/tmp/test.jpg',
            indication='Test indication',
            status='draft_ready'
        )
        db.session.add(case)
        db.session.flush()
        
        report = Report(
            case_id=case.id,
            draft_text='Test AI-generated report with findings.',
            confidence_score=0.85,
            safety_flags={'flags': []}
        )
        db.session.add(report)
        db.session.commit()
        case_id = case.id
        
    return case_id


def test_review_case_page_loads(client, test_user, test_case_with_report):
    """Test that the review page loads successfully."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Access review page
    response = client.get(f'/case/{test_case_with_report}/review')
    
    assert response.status_code == 200
    assert b'Review AI Report' in response.data
    assert b'APPROVE' in response.data
    assert b'MODIFY' in response.data
    assert b'REJECT' in response.data
    assert b'Test AI-generated report' in response.data


def test_review_case_requires_login(client, test_case_with_report):
    """Test that review page requires authentication."""
    response = client.get(f'/case/{test_case_with_report}/review')
    
    # Should redirect to login
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_review_case_without_report(client, test_user, test_patient):
    """Test review page when case has no report."""
    with client.application.app_context():
        # Create case without report
        case = Case(
            case_number='000002',
            user_id=test_user,
            patient_id=test_patient,
            image_filename='test.jpg',
            image_path='/tmp/test.jpg',
            status='uploaded'
        )
        db.session.add(case)
        db.session.commit()
        case_id = case.id
    
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to access review page
    response = client.get(f'/case/{case_id}/review', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'No report found' in response.data


def test_review_finalized_report_redirects(client, test_user, test_case_with_report):
    """Test that reviewing a finalized report redirects."""
    with client.application.app_context():
        # Finalize the report
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        report.is_finalized = True
        db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to access review page
    response = client.get(f'/case/{test_case_with_report}/review', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'already been finalized' in response.data


def test_approve_case_success(client, test_user, test_case_with_report):
    """Test successful approval of AI-generated report."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Approve the report
    response = client.post(f'/case/{test_case_with_report}/approve', data={
        'confidence_level': '4',
        'notes': 'Report looks good'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'approved and finalized' in response.data
    
    # Verify database changes
    with client.application.app_context():
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        assert report.is_finalized is True
        assert report.final_text == report.draft_text
        
        case = Case.query.get(test_case_with_report)
        assert case.status == 'completed'
        
        feedback = Feedback.query.filter_by(report_id=report.id).first()
        assert feedback is not None
        assert feedback.action == 'approve'
        assert feedback.confidence_level == 4
        assert feedback.modifications['notes'] == 'Report looks good'


def test_approve_case_without_confidence_level(client, test_user, test_case_with_report):
    """Test approval fails without confidence level."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to approve without confidence level
    response = client.post(f'/case/{test_case_with_report}/approve', data={
        'notes': 'Report looks good'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'valid confidence level' in response.data
    
    # Verify report is not finalized
    with client.application.app_context():
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        assert report.is_finalized is False


def test_approve_case_requires_login(client, test_case_with_report):
    """Test that approval requires authentication."""
    response = client.post(f'/case/{test_case_with_report}/approve', data={
        'confidence_level': '4'
    })
    
    # Should redirect to login
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_modify_case_success(client, test_user, test_case_with_report):
    """Test successful modification of AI-generated report."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Modify the report
    modified_text = 'Modified report with corrected findings.'
    response = client.post(f'/case/{test_case_with_report}/modify', data={
        'modified_text': modified_text,
        'notes': 'Corrected finding description'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'modified and finalized' in response.data
    
    # Verify database changes
    with client.application.app_context():
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        assert report.is_finalized is True
        assert report.final_text == modified_text
        assert report.draft_text != modified_text  # Original draft unchanged
        
        case = Case.query.get(test_case_with_report)
        assert case.status == 'completed'
        
        feedback = Feedback.query.filter_by(report_id=report.id).first()
        assert feedback is not None
        assert feedback.action == 'modify'
        assert feedback.modifications['notes'] == 'Corrected finding description'
        assert 'diff' in feedback.modifications
        assert 'additions' in feedback.modifications
        assert 'deletions' in feedback.modifications


def test_modify_case_without_text(client, test_user, test_case_with_report):
    """Test modification fails without modified text."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to modify without text
    response = client.post(f'/case/{test_case_with_report}/modify', data={
        'notes': 'Some notes'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'cannot be empty' in response.data
    
    # Verify report is not finalized
    with client.application.app_context():
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        assert report.is_finalized is False


def test_modify_case_without_notes(client, test_user, test_case_with_report):
    """Test modification fails without modification notes."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to modify without notes
    response = client.post(f'/case/{test_case_with_report}/modify', data={
        'modified_text': 'Modified text'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'modification summary' in response.data
    
    # Verify report is not finalized
    with client.application.app_context():
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        assert report.is_finalized is False


def test_modify_case_requires_login(client, test_case_with_report):
    """Test that modification requires authentication."""
    response = client.post(f'/case/{test_case_with_report}/modify', data={
        'modified_text': 'Modified text',
        'notes': 'Some notes'
    })
    
    # Should redirect to login
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_reject_case_success(client, test_user, test_case_with_report):
    """Test successful rejection of AI-generated report."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Reject the report
    response = client.post(f'/case/{test_case_with_report}/reject', data={
        'rejection_reason': 'incorrect_findings',
        'rejection_details': 'AI missed critical finding',
        'correct_interpretation': 'Correct interpretation here'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'rejected' in response.data
    
    # Verify database changes
    with client.application.app_context():
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        assert report.is_finalized is False
        assert report.final_text is None
        
        case = Case.query.get(test_case_with_report)
        assert case.status == 'rejected'
        
        feedback = Feedback.query.filter_by(report_id=report.id).first()
        assert feedback is not None
        assert feedback.action == 'reject'
        assert feedback.rejection_reason == 'AI missed critical finding'
        assert feedback.modifications['rejection_category'] == 'incorrect_findings'
        assert feedback.modifications['correct_interpretation'] == 'Correct interpretation here'


def test_reject_case_without_reason(client, test_user, test_case_with_report):
    """Test rejection fails without reason."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to reject without reason
    response = client.post(f'/case/{test_case_with_report}/reject', data={
        'rejection_details': 'Some details'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'rejection reason' in response.data
    
    # Verify report is not rejected
    with client.application.app_context():
        case = Case.query.get(test_case_with_report)
        assert case.status != 'rejected'


def test_reject_case_without_details(client, test_user, test_case_with_report):
    """Test rejection fails without detailed explanation."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to reject without details
    response = client.post(f'/case/{test_case_with_report}/reject', data={
        'rejection_reason': 'incorrect_findings'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'detailed explanation' in response.data
    
    # Verify report is not rejected
    with client.application.app_context():
        case = Case.query.get(test_case_with_report)
        assert case.status != 'rejected'


def test_reject_case_requires_login(client, test_case_with_report):
    """Test that rejection requires authentication."""
    response = client.post(f'/case/{test_case_with_report}/reject', data={
        'rejection_reason': 'incorrect_findings',
        'rejection_details': 'Some details'
    })
    
    # Should redirect to login
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_approve_already_finalized_report(client, test_user, test_case_with_report):
    """Test that approving an already finalized report shows warning."""
    with client.application.app_context():
        # Finalize the report
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        report.is_finalized = True
        db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to approve
    response = client.post(f'/case/{test_case_with_report}/approve', data={
        'confidence_level': '4'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'already been finalized' in response.data


def test_modify_already_finalized_report(client, test_user, test_case_with_report):
    """Test that modifying an already finalized report shows warning."""
    with client.application.app_context():
        # Finalize the report
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        report.is_finalized = True
        db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to modify
    response = client.post(f'/case/{test_case_with_report}/modify', data={
        'modified_text': 'Modified text',
        'notes': 'Some notes'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'already been finalized' in response.data


def test_reject_already_finalized_report(client, test_user, test_case_with_report):
    """Test that rejecting an already finalized report shows warning."""
    with client.application.app_context():
        # Finalize the report
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        report.is_finalized = True
        db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Try to reject
    response = client.post(f'/case/{test_case_with_report}/reject', data={
        'rejection_reason': 'incorrect_findings',
        'rejection_details': 'Some details'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'already been finalized' in response.data


def test_confidence_score_display(client, test_user, test_case_with_report):
    """Test that confidence score is displayed on review page."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Access review page
    response = client.get(f'/case/{test_case_with_report}/review')
    
    assert response.status_code == 200
    assert b'Confidence Score' in response.data
    assert b'85.0%' in response.data  # 0.85 * 100


def test_safety_flags_display(client, test_user, test_case_with_report):
    """Test that safety flags are displayed on review page."""
    with client.application.app_context():
        # Add safety flags to report
        report = Report.query.filter_by(case_id=test_case_with_report).first()
        report.safety_flags = {
            'flags': ['Potential critical finding', 'Low image quality']
        }
        db.session.commit()
    
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Access review page
    response = client.get(f'/case/{test_case_with_report}/review')
    
    assert response.status_code == 200
    assert b'Safety Flags' in response.data
    assert b'2 flag(s) detected' in response.data
    assert b'Potential critical finding' in response.data
    assert b'Low image quality' in response.data


def test_feedback_audit_trail(client, test_user, test_case_with_report):
    """Test that all HITL actions create proper audit trail."""
    # Login
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    # Approve a report
    client.post(f'/case/{test_case_with_report}/approve', data={
        'confidence_level': '5',
        'notes': 'Excellent report'
    })
    
    # Verify feedback record
    with client.application.app_context():
        feedback = Feedback.query.filter_by(case_id=test_case_with_report).first()
        assert feedback is not None
        assert feedback.user_id == test_user
        assert feedback.action == 'approve'
        assert feedback.created_at is not None
        assert isinstance(feedback.created_at, datetime)
