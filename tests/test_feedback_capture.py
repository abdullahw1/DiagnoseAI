"""
Unit tests for feedback capture service.

Tests the feedback capture functions for approve, modify, and reject actions.
"""

import pytest
from datetime import datetime
from app import db
from app.models import User, Case, Report, Feedback, Patient
from app.feedback.capture import (
    capture_approval,
    capture_modification,
    capture_rejection,
    _calculate_diff
)


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    return user_id


@pytest.fixture
def test_patient(app, test_user):
    """Create a test patient."""
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
    """Create a test case with report."""
    with app.app_context():
        case = Case(
            case_number='000001',
            user_id=test_user,
            patient_id=test_patient,
            image_filename='test.jpg',
            image_path='/tmp/test.jpg',
            status='draft_ready'
        )
        db.session.add(case)
        db.session.flush()
        
        report = Report(
            case_id=case.id,
            draft_text='Original AI-generated report with findings.',
            confidence_score=0.85,
            safety_flags={'flags': ['Low confidence in finding A']}
        )
        db.session.add(report)
        db.session.commit()
        
        case_id = case.id
        report_id = report.id
    
    return {'case_id': case_id, 'report_id': report_id}


class TestCaptureApproval:
    """Tests for capture_approval function."""
    
    def test_capture_approval_success(self, app, test_user, test_case_with_report):
        """Test successful approval capture."""
        with app.app_context():
            feedback = capture_approval(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                confidence_level=4,
                notes='Report looks accurate'
            )
            
            assert feedback is not None
            assert feedback.action == 'approve'
            assert feedback.confidence_level == 4
            assert feedback.case_id == test_case_with_report['case_id']
            assert feedback.report_id == test_case_with_report['report_id']
            assert feedback.user_id == test_user
            assert feedback.modifications['notes'] == 'Report looks accurate'
            assert 'approval_timestamp' in feedback.modifications
            assert 'report_length' in feedback.modifications
            assert 'confidence_score' in feedback.modifications
            assert feedback.modifications['confidence_score'] == 0.85
    
    def test_capture_approval_without_notes(self, app, test_user, test_case_with_report):
        """Test approval capture without optional notes."""
        with app.app_context():
            feedback = capture_approval(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                confidence_level=5
            )
            
            assert feedback is not None
            assert feedback.action == 'approve'
            assert feedback.confidence_level == 5
            assert feedback.modifications['notes'] is None
    
    def test_capture_approval_invalid_confidence_level(self, app, test_user, test_case_with_report):
        """Test approval fails with invalid confidence level."""
        with app.app_context():
            with pytest.raises(ValueError, match="Confidence level must be between 1 and 5"):
                capture_approval(
                    case_id=test_case_with_report['case_id'],
                    report_id=test_case_with_report['report_id'],
                    user_id=test_user,
                    confidence_level=6
                )
            
            with pytest.raises(ValueError, match="Confidence level must be between 1 and 5"):
                capture_approval(
                    case_id=test_case_with_report['case_id'],
                    report_id=test_case_with_report['report_id'],
                    user_id=test_user,
                    confidence_level=0
                )
    
    def test_capture_approval_invalid_case_id(self, app, test_user, test_case_with_report):
        """Test approval fails with invalid case ID."""
        with app.app_context():
            with pytest.raises(ValueError, match="Case .* not found"):
                capture_approval(
                    case_id=99999,
                    report_id=test_case_with_report['report_id'],
                    user_id=test_user,
                    confidence_level=4
                )
    
    def test_capture_approval_invalid_report_id(self, app, test_user, test_case_with_report):
        """Test approval fails with invalid report ID."""
        with app.app_context():
            with pytest.raises(ValueError, match="Report .* not found"):
                capture_approval(
                    case_id=test_case_with_report['case_id'],
                    report_id=99999,
                    user_id=test_user,
                    confidence_level=4
                )
    
    def test_capture_approval_mismatched_case_report(self, app, test_user, test_patient, test_case_with_report):
        """Test approval fails when report doesn't belong to case."""
        with app.app_context():
            # Create another case and report
            case2 = Case(
                case_number='000002',
                user_id=test_user,
                patient_id=test_patient,
                image_filename='test2.jpg',
                image_path='/tmp/test2.jpg'
            )
            db.session.add(case2)
            db.session.flush()
            
            report2 = Report(
                case_id=case2.id,
                draft_text='Another report'
            )
            db.session.add(report2)
            db.session.commit()
            
            # Try to use report2 with case1 from fixture
            with pytest.raises(ValueError, match="does not belong to case"):
                capture_approval(
                    case_id=test_case_with_report['case_id'],
                    report_id=report2.id,
                    user_id=test_user,
                    confidence_level=4
                )
    
    def test_capture_approval_stores_safety_flags(self, app, test_user, test_case_with_report):
        """Test that approval captures safety flags from report."""
        with app.app_context():
            feedback = capture_approval(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                confidence_level=3
            )
            
            assert 'safety_flags' in feedback.modifications
            assert feedback.modifications['safety_flags'] == {'flags': ['Low confidence in finding A']}


class TestCaptureModification:
    """Tests for capture_modification function."""
    
    def test_capture_modification_success(self, app, test_user, test_case_with_report):
        """Test successful modification capture."""
        with app.app_context():
            original_text = 'Original AI-generated report with findings.'
            modified_text = 'Modified report with corrected findings and additional details.'
            
            feedback = capture_modification(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                original_text=original_text,
                modified_text=modified_text,
                notes='Corrected finding description and added details'
            )
            
            assert feedback is not None
            assert feedback.action == 'modify'
            assert feedback.case_id == test_case_with_report['case_id']
            assert feedback.report_id == test_case_with_report['report_id']
            assert feedback.user_id == test_user
            assert feedback.modifications['notes'] == 'Corrected finding description and added details'
            assert 'modification_timestamp' in feedback.modifications
            assert 'diff' in feedback.modifications
            assert 'additions' in feedback.modifications
            assert 'deletions' in feedback.modifications
            assert feedback.modifications['additions'] > 0
            assert feedback.modifications['deletions'] > 0
    
    def test_capture_modification_calculates_diff(self, app, test_user, test_case_with_report):
        """Test that modification calculates accurate diff."""
        with app.app_context():
            original_text = 'Line 1\nLine 2\nLine 3'
            modified_text = 'Line 1\nModified Line 2\nLine 3\nLine 4'
            
            feedback = capture_modification(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                original_text=original_text,
                modified_text=modified_text,
                notes='Modified line 2 and added line 4'
            )
            
            assert feedback.modifications['original_length'] == 3
            assert feedback.modifications['modified_length'] == 4
            assert feedback.modifications['additions'] == 2  # Modified line + new line
            assert feedback.modifications['deletions'] == 1  # Original line 2
            assert 'change_percentage' in feedback.modifications
            assert feedback.modifications['change_percentage'] > 0
    
    def test_capture_modification_empty_modified_text(self, app, test_user, test_case_with_report):
        """Test modification fails with empty modified text."""
        with app.app_context():
            with pytest.raises(ValueError, match="Modified text cannot be empty"):
                capture_modification(
                    case_id=test_case_with_report['case_id'],
                    report_id=test_case_with_report['report_id'],
                    user_id=test_user,
                    original_text='Original text',
                    modified_text='',
                    notes='Some notes'
                )
    
    def test_capture_modification_empty_notes(self, app, test_user, test_case_with_report):
        """Test modification fails without notes."""
        with app.app_context():
            with pytest.raises(ValueError, match="Modification notes are required"):
                capture_modification(
                    case_id=test_case_with_report['case_id'],
                    report_id=test_case_with_report['report_id'],
                    user_id=test_user,
                    original_text='Original text',
                    modified_text='Modified text',
                    notes=''
                )
    
    def test_capture_modification_with_empty_original(self, app, test_user, test_case_with_report):
        """Test modification handles empty original text."""
        with app.app_context():
            feedback = capture_modification(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                original_text='',
                modified_text='New text',
                notes='Added new content'
            )
            
            assert feedback is not None
            assert feedback.modifications['original_length'] == 0
            assert feedback.modifications['modified_length'] == 1
            assert feedback.modifications['additions'] == 1
            assert feedback.modifications['deletions'] == 0
    
    def test_capture_modification_stores_added_deleted_lines(self, app, test_user, test_case_with_report):
        """Test that modification stores actual added and deleted line content."""
        with app.app_context():
            original_text = 'Keep this line\nDelete this line\nKeep this too'
            modified_text = 'Keep this line\nAdd this new line\nKeep this too'
            
            feedback = capture_modification(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                original_text=original_text,
                modified_text=modified_text,
                notes='Replaced middle line'
            )
            
            assert 'added_lines' in feedback.modifications
            assert 'deleted_lines' in feedback.modifications
            assert len(feedback.modifications['added_lines']) > 0
            assert len(feedback.modifications['deleted_lines']) > 0


class TestCaptureRejection:
    """Tests for capture_rejection function."""
    
    def test_capture_rejection_success(self, app, test_user, test_case_with_report):
        """Test successful rejection capture."""
        with app.app_context():
            feedback = capture_rejection(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                rejection_category='incorrect_findings',
                rejection_details='AI missed critical finding of liver lesion',
                correct_interpretation='Liver shows 2cm hypoechoic lesion in right lobe'
            )
            
            assert feedback is not None
            assert feedback.action == 'reject'
            assert feedback.case_id == test_case_with_report['case_id']
            assert feedback.report_id == test_case_with_report['report_id']
            assert feedback.user_id == test_user
            assert feedback.rejection_reason == 'AI missed critical finding of liver lesion'
            assert feedback.modifications['rejection_category'] == 'incorrect_findings'
            assert feedback.modifications['rejection_details'] == 'AI missed critical finding of liver lesion'
            assert feedback.modifications['correct_interpretation'] == 'Liver shows 2cm hypoechoic lesion in right lobe'
            assert 'rejection_timestamp' in feedback.modifications
            assert 'rejected_draft' in feedback.modifications
    
    def test_capture_rejection_without_correct_interpretation(self, app, test_user, test_case_with_report):
        """Test rejection without optional correct interpretation."""
        with app.app_context():
            feedback = capture_rejection(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                rejection_category='poor_quality',
                rejection_details='Report is too vague and lacks specificity'
            )
            
            assert feedback is not None
            assert feedback.action == 'reject'
            assert feedback.modifications['correct_interpretation'] is None
            assert 'diff_from_correct' not in feedback.modifications
    
    def test_capture_rejection_empty_category(self, app, test_user, test_case_with_report):
        """Test rejection fails without category."""
        with app.app_context():
            with pytest.raises(ValueError, match="Rejection category is required"):
                capture_rejection(
                    case_id=test_case_with_report['case_id'],
                    report_id=test_case_with_report['report_id'],
                    user_id=test_user,
                    rejection_category='',
                    rejection_details='Some details'
                )
    
    def test_capture_rejection_empty_details(self, app, test_user, test_case_with_report):
        """Test rejection fails without details."""
        with app.app_context():
            with pytest.raises(ValueError, match="Rejection details are required"):
                capture_rejection(
                    case_id=test_case_with_report['case_id'],
                    report_id=test_case_with_report['report_id'],
                    user_id=test_user,
                    rejection_category='incorrect_findings',
                    rejection_details=''
                )
    
    def test_capture_rejection_stores_rejected_draft(self, app, test_user, test_case_with_report):
        """Test that rejection stores the rejected draft text."""
        with app.app_context():
            report = Report.query.get(test_case_with_report['report_id'])
            original_draft = report.draft_text
            
            feedback = capture_rejection(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                rejection_category='missed_findings',
                rejection_details='Critical finding not mentioned'
            )
            
            assert feedback.modifications['rejected_draft'] == original_draft
            assert 'rejected_draft_length' in feedback.modifications
            assert feedback.modifications['rejected_draft_length'] == len(original_draft)
    
    def test_capture_rejection_with_correct_interpretation_calculates_diff(self, app, test_user, test_case_with_report):
        """Test that rejection with correct interpretation calculates diff."""
        with app.app_context():
            feedback = capture_rejection(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                rejection_category='wrong_diagnosis',
                rejection_details='Diagnosis is completely incorrect',
                correct_interpretation='Correct diagnosis: Normal liver with no abnormalities'
            )
            
            assert 'diff_from_correct' in feedback.modifications
            assert 'additions' in feedback.modifications['diff_from_correct']
            assert 'deletions' in feedback.modifications['diff_from_correct']
            assert 'change_percentage' in feedback.modifications['diff_from_correct']
    
    def test_capture_rejection_stores_safety_flags(self, app, test_user, test_case_with_report):
        """Test that rejection captures safety flags from report."""
        with app.app_context():
            feedback = capture_rejection(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                rejection_category='incorrect_findings',
                rejection_details='Findings are wrong'
            )
            
            assert 'safety_flags' in feedback.modifications
            assert feedback.modifications['safety_flags'] == {'flags': ['Low confidence in finding A']}


class TestCalculateDiff:
    """Tests for _calculate_diff helper function."""
    
    def test_calculate_diff_basic(self):
        """Test basic diff calculation."""
        original = 'Line 1\nLine 2\nLine 3'
        modified = 'Line 1\nModified Line 2\nLine 3'
        
        result = _calculate_diff(original, modified)
        
        assert result['original_length'] == 3
        assert result['modified_length'] == 3
        assert result['additions'] == 1
        assert result['deletions'] == 1
        assert 'diff_lines' in result
        assert 'change_percentage' in result
    
    def test_calculate_diff_additions_only(self):
        """Test diff with only additions."""
        original = 'Line 1\nLine 2'
        modified = 'Line 1\nLine 2\nLine 3\nLine 4'
        
        result = _calculate_diff(original, modified)
        
        assert result['additions'] == 2
        assert result['deletions'] == 0
        assert result['modified_length'] == 4
    
    def test_calculate_diff_deletions_only(self):
        """Test diff with only deletions."""
        original = 'Line 1\nLine 2\nLine 3\nLine 4'
        modified = 'Line 1\nLine 2'
        
        result = _calculate_diff(original, modified)
        
        assert result['additions'] == 0
        assert result['deletions'] == 2
        assert result['modified_length'] == 2
    
    def test_calculate_diff_empty_original(self):
        """Test diff with empty original text."""
        original = ''
        modified = 'New Line 1\nNew Line 2'
        
        result = _calculate_diff(original, modified)
        
        assert result['original_length'] == 0
        assert result['modified_length'] == 2
        assert result['additions'] == 2
        assert result['deletions'] == 0
    
    def test_calculate_diff_empty_modified(self):
        """Test diff with empty modified text."""
        original = 'Line 1\nLine 2'
        modified = ''
        
        result = _calculate_diff(original, modified)
        
        assert result['original_length'] == 2
        assert result['modified_length'] == 0
        assert result['additions'] == 0
        assert result['deletions'] == 2
    
    def test_calculate_diff_identical_texts(self):
        """Test diff with identical texts."""
        text = 'Line 1\nLine 2\nLine 3'
        
        result = _calculate_diff(text, text)
        
        assert result['additions'] == 0
        assert result['deletions'] == 0
        assert result['change_percentage'] == 0
    
    def test_calculate_diff_change_percentage(self):
        """Test change percentage calculation."""
        original = 'Line 1\nLine 2\nLine 3\nLine 4'
        modified = 'Line 1\nModified\nLine 3\nLine 4'
        
        result = _calculate_diff(original, modified)
        
        # 1 deletion + 1 addition = 2 changes out of 4 lines = 50%
        assert result['change_percentage'] == 50.0
    
    def test_calculate_diff_stores_line_content(self):
        """Test that diff stores actual line content."""
        original = 'Keep this\nDelete this\nKeep that'
        modified = 'Keep this\nAdd this\nKeep that'
        
        result = _calculate_diff(original, modified)
        
        assert 'added_lines' in result
        assert 'deleted_lines' in result
        assert len(result['added_lines']) > 0
        assert len(result['deleted_lines']) > 0
        assert 'Add this' in result['added_lines']
        assert 'Delete this' in result['deleted_lines']
    
    def test_calculate_diff_limits_output(self):
        """Test that diff output is limited to prevent excessive data."""
        # Create large texts
        original_lines = [f'Original line {i}' for i in range(200)]
        modified_lines = [f'Modified line {i}' for i in range(200)]
        
        original = '\n'.join(original_lines)
        modified = '\n'.join(modified_lines)
        
        result = _calculate_diff(original, modified)
        
        # Should limit diff_lines to 100
        assert len(result['diff_lines']) <= 100
        # Should limit added/deleted lines to 50 each
        assert len(result['added_lines']) <= 50
        assert len(result['deleted_lines']) <= 50


class TestFeedbackIntegration:
    """Integration tests for feedback capture with database."""
    
    def test_feedback_persists_to_database(self, app, test_user, test_case_with_report):
        """Test that feedback is properly persisted to database."""
        with app.app_context():
            feedback = capture_approval(
                case_id=test_case_with_report['case_id'],
                report_id=test_case_with_report['report_id'],
                user_id=test_user,
                confidence_level=4,
                notes='Test approval'
            )
            
            db.session.commit()
            
            # Query feedback from database
            saved_feedback = Feedback.query.filter_by(
                case_id=test_case_with_report['case_id']
            ).first()
            
            assert saved_feedback is not None
            assert saved_feedback.action == 'approve'
            assert saved_feedback.confidence_level == 4
    
    def test_multiple_feedback_records(self, app, test_user, test_patient):
        """Test that multiple feedback records can be created for different cases."""
        with app.app_context():
            # Create two cases with reports
            case1 = Case(
                case_number='000010',
                user_id=test_user,
                patient_id=test_patient,
                image_filename='test1.jpg',
                image_path='/tmp/test1.jpg'
            )
            case2 = Case(
                case_number='000011',
                user_id=test_user,
                patient_id=test_patient,
                image_filename='test2.jpg',
                image_path='/tmp/test2.jpg'
            )
            db.session.add_all([case1, case2])
            db.session.flush()
            
            report1 = Report(case_id=case1.id, draft_text='Report 1')
            report2 = Report(case_id=case2.id, draft_text='Report 2')
            db.session.add_all([report1, report2])
            db.session.commit()
            
            # Capture feedback for both
            feedback1 = capture_approval(
                case_id=case1.id,
                report_id=report1.id,
                user_id=test_user,
                confidence_level=5
            )
            feedback2 = capture_rejection(
                case_id=case2.id,
                report_id=report2.id,
                user_id=test_user,
                rejection_category='incorrect',
                rejection_details='Wrong diagnosis'
            )
            
            db.session.commit()
            
            # Verify both exist
            all_feedback = Feedback.query.all()
            assert len(all_feedback) == 2
            assert any(f.action == 'approve' for f in all_feedback)
            assert any(f.action == 'reject' for f in all_feedback)
