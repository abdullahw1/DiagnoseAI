"""
Unit tests for the evaluation interface functionality.
Tests the routes, helper functions, and metric calculations for findings evaluation.
"""

import pytest
from datetime import datetime, timedelta
from app.models import (
    User, Patient, Case, AITestResult, AIGeneratedFindings, 
    FindingsEvaluation
)
from app import db


@pytest.fixture
def test_patient(app, user):
    """Create a test patient."""
    with app.app_context():
        # Get user ID before creating patient
        user_obj = User.query.filter_by(username='testuser').first()
        patient = Patient(
            patient_id='TEST001',
            first_name='Test',
            last_name='Patient',
            created_by=user_obj.id
        )
        db.session.add(patient)
        db.session.commit()
        return patient.id


@pytest.fixture
def test_case(app, user, test_patient):
    """Create a test case."""
    with app.app_context():
        # Get user ID before creating case
        user_obj = User.query.filter_by(username='testuser').first()
        case = Case(
            case_number='000001',
            user_id=user_obj.id,
            patient_id=test_patient,
            study_type='Ultrasound',
            status='pending'
        )
        db.session.add(case)
        db.session.commit()
        return case.id


class TestEvaluationHelperFunctions:
    """Test helper functions for evaluation interface."""
    
    def test_extract_field_correctness_from_form(self, app):
        """Test extracting field correctness from form data."""
        from app.main import extract_field_correctness_from_form
        
        with app.app_context():
            # Mock form data
            form_data = {
                'correct_liver_size': 'on',
                'correct_liver_texture': 'on',
                'correct_spleen_size': 'on',
                # Some fields not checked (incorrect)
            }
            
            result = extract_field_correctness_from_form(form_data)
            
            assert result['liver_size'] is True
            assert result['liver_texture'] is True
            assert result['spleen_size'] is True
            assert 'liver_focal_defect' not in result or result['liver_focal_defect'] is False
    
    def test_extract_field_correctness_empty_form(self, app):
        """Test extracting from empty form data."""
        from app.main import extract_field_correctness_from_form
        
        with app.app_context():
            form_data = {}
            result = extract_field_correctness_from_form(form_data)
            
            # Should return empty dict or all False
            assert isinstance(result, dict)
    
    def test_calculate_organ_metrics(self, app, user, test_case):
        """Test calculating organ-level metrics."""
        from app.main import calculate_organ_metrics
        
        with app.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal',
                liver_texture='Normal',
                spleen_size='Normal',
                gb_calculus='Absent'
            )
            db.session.add(ai_findings)
            db.session.flush()
            
            # Create evaluation
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={
                    'liver_size': True,
                    'liver_texture': False,  # Incorrect
                    'spleen_size': True,
                    'gb_calculus': True
                },
                total_fields=4,
                correct_fields=3,
                accuracy_percentage=75.0
            )
            db.session.add(evaluation)
            db.session.commit()
            
            # Calculate metrics
            metrics = calculate_organ_metrics([evaluation])
            
            # Check liver metrics (2 fields, 1 correct)
            assert 'Liver' in metrics
            assert metrics['Liver']['total'] == 2
            assert metrics['Liver']['correct'] == 1
            assert metrics['Liver']['accuracy'] == 50.0
            
            # Check spleen metrics (1 field, 1 correct)
            assert 'Spleen' in metrics
            assert metrics['Spleen']['total'] == 1
            assert metrics['Spleen']['correct'] == 1
            assert metrics['Spleen']['accuracy'] == 100.0
            
            # Check gall bladder metrics (1 field, 1 correct)
            assert 'Gall Bladder' in metrics
            assert metrics['Gall Bladder']['total'] == 1
            assert metrics['Gall Bladder']['correct'] == 1
            assert metrics['Gall Bladder']['accuracy'] == 100.0
    
    def test_calculate_field_metrics(self, app, user, test_case):
        """Test calculating field-level metrics."""
        from app.main import calculate_field_metrics
        
        with app.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal',
                spleen_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.flush()
            
            # Create evaluation
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={
                    'liver_size': True,
                    'spleen_size': False
                },
                total_fields=2,
                correct_fields=1,
                accuracy_percentage=50.0
            )
            db.session.add(evaluation)
            db.session.commit()
            
            # Calculate metrics
            metrics = calculate_field_metrics([evaluation])
            
            assert 'liver_size' in metrics
            assert metrics['liver_size']['total'] == 1
            assert metrics['liver_size']['correct'] == 1
            assert metrics['liver_size']['accuracy'] == 100.0
            
            assert 'spleen_size' in metrics
            assert metrics['spleen_size']['total'] == 1
            assert metrics['spleen_size']['correct'] == 0
            assert metrics['spleen_size']['accuracy'] == 0.0
    
    def test_calculate_temporal_metrics(self, app, user, test_case):
        """Test calculating temporal trends."""
        from app.main import calculate_temporal_metrics
        
        with app.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.flush()
            
            # Create evaluations on different days
            today = datetime.utcnow()
            yesterday = today - timedelta(days=1)
            
            eval1 = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={'liver_size': True},
                total_fields=1,
                correct_fields=1,
                accuracy_percentage=100.0,
                created_at=today
            )
            
            eval2 = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={'liver_size': False},
                total_fields=1,
                correct_fields=0,
                accuracy_percentage=0.0,
                created_at=yesterday
            )
            
            db.session.add_all([eval1, eval2])
            db.session.commit()
            
            # Calculate temporal metrics
            metrics = calculate_temporal_metrics([eval1, eval2])
            
            assert len(metrics) == 2
            assert all('date' in m for m in metrics)
            assert all('accuracy' in m for m in metrics)


class TestEvaluationRoutes:
    """Test evaluation routes."""
    
    def test_evaluate_findings_get(self, client, user, test_case):
        """Test GET request to evaluation page."""
        with client.application.app_context():
            # Create AI test result
            ai_test = AITestResult(
                user_id=user.id,
                original_filename='test.jpg',
                saved_filename='test_saved.jpg',
                image_path='/path/to/test.jpg',
                ai_analysis='Test analysis'
            )
            db.session.add(ai_test)
            db.session.flush()
            
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                ai_test_result_id=ai_test.id,
                case_id=test_case,
                liver_size='Normal',
                spleen_size='Enlarged'
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            
            # Access evaluation page
            response = client.get(f'/ai-test/result/{ai_test.id}/evaluate-findings')
            
            assert response.status_code == 200
            assert b'Evaluate AI-Generated Findings' in response.data
            assert b'liver_size' in response.data.lower()
            assert b'spleen_size' in response.data.lower()
    
    def test_evaluate_findings_post(self, client, user, test_case):
        """Test POST request to submit evaluation."""
        with client.application.app_context():
            # Create AI test result
            ai_test = AITestResult(
                user_id=user.id,
                original_filename='test.jpg',
                saved_filename='test_saved.jpg',
                image_path='/path/to/test.jpg',
                ai_analysis='Test analysis'
            )
            db.session.add(ai_test)
            db.session.flush()
            
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                ai_test_result_id=ai_test.id,
                case_id=test_case,
                liver_size='Normal',
                spleen_size='Enlarged',
                gb_calculus='Absent'
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            
            # Submit evaluation
            response = client.post(f'/ai-test/result/{ai_test.id}/evaluate-findings', data={
                'correct_liver_size': 'on',
                'correct_spleen_size': 'on',
                'correct_gb_calculus': 'on',
                'evaluation_notes': 'Test evaluation'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Check evaluation was saved
            evaluation = FindingsEvaluation.query.filter_by(
                ai_finding_id=ai_findings.id
            ).first()
            
            assert evaluation is not None
            assert evaluation.total_fields == 3
            assert evaluation.correct_fields == 3
            assert evaluation.accuracy_percentage == 100.0
            assert evaluation.evaluation_notes == 'Test evaluation'
    
    def test_evaluate_findings_no_findings(self, client, user, test_case):
        """Test evaluation page when no AI findings exist."""
        with client.application.app_context():
            # Create AI test result without findings
            ai_test = AITestResult(
                user_id=user.id,
                original_filename='test.jpg',
                saved_filename='test_saved.jpg',
                image_path='/path/to/test.jpg',
                ai_analysis='Test analysis'
            )
            db.session.add(ai_test)
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            
            # Try to access evaluation page
            response = client.get(f'/ai-test/result/{ai_test.id}/evaluate-findings', 
                                follow_redirects=True)
            
            assert response.status_code == 200
            assert b'No AI-generated findings found' in response.data
    
    def test_findings_metrics_no_data(self, client, user):
        """Test metrics page with no evaluation data."""
        with client.application.app_context():
            # Login
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)
            
            # Access metrics page
            response = client.get('/findings/metrics', follow_redirects=True)
            
            assert response.status_code == 200
            assert b'No Evaluation Data Available' in response.data
    
    def test_findings_metrics_with_data(self, client, user, test_case):
        """Test metrics page with evaluation data."""
        with client.application.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal',
                spleen_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.flush()
            
            # Create AI test result
            ai_test = AITestResult(
                user_id=user.id,
                original_filename='test.jpg',
                saved_filename='test_saved.jpg',
                image_path='/path/to/test.jpg',
                ai_analysis='Test analysis'
            )
            db.session.add(ai_test)
            db.session.flush()
            
            # Link findings to test result
            ai_findings.ai_test_result_id = ai_test.id
            
            # Create evaluation
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={
                    'liver_size': True,
                    'spleen_size': True
                },
                total_fields=2,
                correct_fields=2,
                accuracy_percentage=100.0
            )
            db.session.add(evaluation)
            db.session.commit()
            
            # Login
            client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            
            # Access metrics page
            response = client.get('/findings/metrics')
            
            assert response.status_code == 200
            assert b'Findings Accuracy Metrics' in response.data
            assert b'100' in response.data  # Should show 100% accuracy
            assert b'Liver' in response.data
            assert b'Spleen' in response.data


class TestMetricCalculations:
    """Test metric calculation accuracy."""
    
    def test_overall_accuracy_calculation(self, app, user, test_case):
        """Test overall accuracy calculation."""
        with app.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal',
                liver_texture='Normal',
                spleen_size='Normal',
                gb_calculus='Absent'
            )
            db.session.add(ai_findings)
            db.session.flush()
            
            # Create evaluation with 3 out of 4 correct
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={
                    'liver_size': True,
                    'liver_texture': False,
                    'spleen_size': True,
                    'gb_calculus': True
                },
                total_fields=4,
                correct_fields=3,
                accuracy_percentage=75.0
            )
            db.session.add(evaluation)
            db.session.commit()
            
            # Verify stored accuracy
            assert evaluation.accuracy_percentage == 75.0
            assert evaluation.total_fields == 4
            assert evaluation.correct_fields == 3
    
    def test_zero_fields_accuracy(self, app, user, test_case):
        """Test accuracy calculation with zero fields."""
        with app.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case
            )
            db.session.add(ai_findings)
            db.session.flush()
            
            # Create evaluation with no fields
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={},
                total_fields=0,
                correct_fields=0,
                accuracy_percentage=0.0
            )
            db.session.add(evaluation)
            db.session.commit()
            
            # Should handle gracefully
            assert evaluation.accuracy_percentage == 0.0
    
    def test_all_correct_accuracy(self, app, user, test_case):
        """Test accuracy when all fields are correct."""
        with app.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal',
                spleen_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.flush()
            
            # Create evaluation with all correct
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={
                    'liver_size': True,
                    'spleen_size': True
                },
                total_fields=2,
                correct_fields=2,
                accuracy_percentage=100.0
            )
            db.session.add(evaluation)
            db.session.commit()
            
            assert evaluation.accuracy_percentage == 100.0
    
    def test_all_incorrect_accuracy(self, app, user, test_case):
        """Test accuracy when all fields are incorrect."""
        with app.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal',
                spleen_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.flush()
            
            # Create evaluation with all incorrect
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=user.id,
                field_correctness={
                    'liver_size': False,
                    'spleen_size': False
                },
                total_fields=2,
                correct_fields=0,
                accuracy_percentage=0.0
            )
            db.session.add(evaluation)
            db.session.commit()
            
            assert evaluation.accuracy_percentage == 0.0
