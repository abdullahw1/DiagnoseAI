"""
Unit tests for structured findings display in templates.

Tests cover:
- Findings display in case detail view
- AI test findings display
- User vs AI findings differentiation
- Empty findings handling
"""

import pytest
from datetime import datetime
from app import db
from app.models import (
    User, Patient, Case, StructuredFindings, 
    AIGeneratedFindings, AITestResult
)


class TestFindingsDisplayInCaseDetail:
    """Test suite for findings display in case detail view."""
    
    def test_case_detail_displays_user_findings(self, client, auth, app):
        """Test that case detail view displays user-provided findings."""
        auth.login()
        
        with app.app_context():
            # Create patient and case directly
            user = User.query.filter_by(username='testuser').first()
            patient = Patient(
                patient_id='P001',
                first_name='John',
                last_name='Doe',
                date_of_birth=datetime(1980, 1, 1),
                gender='M',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.flush()
            
            # Create case directly
            case = Case(
                case_number='001',
                user_id=user.id,
                patient_id=patient.id,
                study_type='Ultrasound',
                body_part='Abdomen',
                indication='Test indication',
                priority='routine'
            )
            db.session.add(case)
            db.session.flush()
            
            # Create structured findings
            findings = StructuredFindings(
                case_id=case.id,
                liver_size='Enlarged',
                liver_texture='Fatty',
                spleen_size='Normal',
                gb_calculus='Present',
                comments='Test findings'
            )
            db.session.add(findings)
            db.session.commit()
            
            # View case detail
            response = client.get(f'/case/{case.id}')
            assert response.status_code == 200
            
            # Check that findings section is displayed
            assert b'Structured Ultrasound Findings' in response.data
            assert b'User-Provided Findings' in response.data
            
            # Check specific findings are displayed
            assert b'Enlarged' in response.data
            assert b'Fatty' in response.data
            assert b'Normal' in response.data
            assert b'Present' in response.data
            assert b'Test findings' in response.data
    
    def test_case_detail_displays_ai_findings(self, client, auth, app):
        """Test that case detail view displays AI-generated findings."""
        auth.login()
        
        with app.app_context():
            # Create patient and case
            user = User.query.filter_by(username='testuser').first()
            patient = Patient(
                patient_id='P002',
                first_name='Jane',
                last_name='Smith',
                date_of_birth=datetime(1985, 5, 15),
                gender='F',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.flush()
            
            case = Case(
                case_number='002',
                user_id=user.id,
                patient_id=patient.id,
                study_type='Ultrasound',
                body_part='Abdomen',
                indication='Test indication',
                priority='routine'
            )
            db.session.add(case)
            db.session.flush()
            
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=case.id,
                liver_size='Normal',
                liver_texture='Normal',
                spleen_size='Enlarged',
                gb_calculus='Absent',
                comments='AI analysis complete',
                confidence_scores={'overall': 0.92}
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # View case detail
            response = client.get(f'/case/{case.id}')
            assert response.status_code == 200
            
            # Check that AI findings section is displayed
            assert b'Structured Ultrasound Findings' in response.data
            assert b'AI-Generated Findings' in response.data
            
            # Check specific AI findings are displayed
            assert b'Enlarged' in response.data  # Spleen
            assert b'Absent' in response.data
            assert b'AI analysis complete' in response.data
    
    def test_case_detail_no_findings_section(self, client, auth, app):
        """Test that case detail doesn't show findings section when no findings exist."""
        auth.login()
        
        with app.app_context():
            # Create patient and case without findings
            user = User.query.filter_by(username='testuser').first()
            patient = Patient(
                patient_id='P004',
                first_name='Alice',
                last_name='Williams',
                date_of_birth=datetime(1990, 7, 10),
                gender='F',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.flush()
            
            case = Case(
                case_number='004',
                user_id=user.id,
                patient_id=patient.id,
                study_type='Ultrasound',
                body_part='Abdomen',
                indication='Test indication',
                priority='routine'
            )
            db.session.add(case)
            db.session.commit()
            
            # View case detail
            response = client.get(f'/case/{case.id}')
            assert response.status_code == 200
            
            # The findings section should not be displayed if no findings exist
            assert b'Structured Ultrasound Findings' not in response.data


class TestAITestFindingsDisplay:
    """Test suite for AI test findings display."""
    
    def test_ai_test_findings_page_displays_findings(self, client, auth, app):
        """Test that AI test findings page displays structured findings."""
        auth.login()
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # Create AI test result
            ai_test = AITestResult(
                user_id=user.id,
                original_filename='test_ai.jpg',
                saved_filename='saved_test.jpg',
                image_path='/tmp/test.jpg',
                view_type='Left Lobe TR View',
                image_context='Test context',
                ai_analysis='Test analysis result'
            )
            db.session.add(ai_test)
            db.session.flush()
            
            # Create AI findings for the test
            ai_findings = AIGeneratedFindings(
                ai_test_result_id=ai_test.id,
                liver_size='Enlarged',
                liver_texture='Coarse',
                spleen_size='Normal',
                comments='AI test findings',
                confidence_scores={'overall': 0.88}
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # View AI test findings page
            response = client.get(f'/ai-test/{ai_test.id}/findings')
            assert response.status_code == 200
            
            # Check that findings are displayed
            assert b'AI-Generated Structured Findings' in response.data
            assert b'Enlarged' in response.data
            assert b'Coarse' in response.data
            assert b'Normal' in response.data
            assert b'AI test findings' in response.data
    
    def test_ai_test_findings_page_no_findings(self, client, auth, app):
        """Test AI test findings page when no findings are available."""
        auth.login()
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # Create AI test result without findings
            ai_test = AITestResult(
                user_id=user.id,
                original_filename='test_ai2.jpg',
                saved_filename='saved_test2.jpg',
                image_path='/tmp/test2.jpg',
                ai_analysis='Test analysis'
            )
            db.session.add(ai_test)
            db.session.commit()
            
            # View AI test findings page
            response = client.get(f'/ai-test/{ai_test.id}/findings')
            assert response.status_code == 200
            
            # Check that no findings message is displayed
            assert b'No Structured Findings Available' in response.data
            assert b'Test Another Image' in response.data
    
    def test_ai_test_findings_shows_evaluate_button(self, client, auth, app):
        """Test that evaluate button is shown when findings exist."""
        auth.login()
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            
            # Create AI test result with findings
            ai_test = AITestResult(
                user_id=user.id,
                original_filename='test_ai3.jpg',
                saved_filename='saved_test3.jpg',
                image_path='/tmp/test3.jpg',
                ai_analysis='Test analysis'
            )
            db.session.add(ai_test)
            db.session.flush()
            
            ai_findings = AIGeneratedFindings(
                ai_test_result_id=ai_test.id,
                liver_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # View AI test findings page
            response = client.get(f'/ai-test/{ai_test.id}/findings')
            assert response.status_code == 200
            
            # Check that evaluate button is present
            assert b'Evaluate Findings' in response.data
            assert f'/ai-test/result/{ai_test.id}/evaluate-findings'.encode() in response.data


class TestFindingsDisplayPartial:
    """Test suite for the _findings_display.html partial template."""
    
    def test_findings_display_shows_only_non_empty_fields(self, client, auth, app):
        """Test that only non-empty finding fields are displayed."""
        auth.login()
        
        with app.app_context():
            # Create patient and case
            user = User.query.filter_by(username='testuser').first()
            patient = Patient(
                patient_id='P005',
                first_name='Charlie',
                last_name='Brown',
                date_of_birth=datetime(1988, 11, 5),
                gender='M',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.flush()
            
            # Create case with only liver findings
            case = Case(
                case_number='005',
                user_id=user.id,
                patient_id=patient.id,
                study_type='Ultrasound',
                body_part='Abdomen',
                indication='Test',
                priority='routine'
            )
            db.session.add(case)
            db.session.flush()
            
            # Create structured findings with only liver data
            findings = StructuredFindings(
                case_id=case.id,
                liver_size='Enlarged',
                liver_texture='Fatty'
                # All other fields are None/empty
            )
            db.session.add(findings)
            db.session.commit()
            
            # View case detail
            response = client.get(f'/case/{case.id}')
            assert response.status_code == 200
            
            # Check that liver section is displayed
            assert b'Liver' in response.data
            assert b'Enlarged' in response.data
            assert b'Fatty' in response.data
            
            # Check that other organ sections are NOT displayed
            # (they should be hidden since all fields are empty)
            assert b'Spleen' not in response.data
            assert b'Gall Bladder' not in response.data
            assert b'Pancreas' not in response.data
    
    def test_findings_display_formats_timestamps(self, client, auth, app):
        """Test that timestamps are properly formatted in findings display."""
        auth.login()
        
        with app.app_context():
            user = User.query.filter_by(username='testuser').first()
            patient = Patient(
                patient_id='P006',
                first_name='Diana',
                last_name='Prince',
                date_of_birth=datetime(1992, 2, 14),
                gender='F',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.flush()
            
            case = Case(
                case_number='006',
                user_id=user.id,
                patient_id=patient.id,
                study_type='Ultrasound',
                body_part='Abdomen',
                indication='Test',
                priority='routine'
            )
            db.session.add(case)
            db.session.flush()
            
            findings = StructuredFindings(
                case_id=case.id,
                liver_size='Normal',
                created_at=datetime(2024, 1, 15, 10, 30, 0)
            )
            db.session.add(findings)
            db.session.commit()
            
            # View case detail
            response = client.get(f'/case/{case.id}')
            assert response.status_code == 200
            
            # Check that timestamp is displayed in correct format
            assert b'2024-01-15 10:30' in response.data
