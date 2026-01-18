"""
Unit tests for structured findings models.
Tests the StructuredFindings, AIGeneratedFindings, and FindingsEvaluation models.
"""

import pytest
from datetime import datetime
from app import db
from app.models import (
    User, Patient, Case, StructuredFindings, 
    AIGeneratedFindings, FindingsEvaluation, AITestResult
)


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            username='testuser2',
            email='test2@example.com',
            first_name='Test',
            last_name='User'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def test_patient(app, test_user):
    """Create a test patient."""
    with app.app_context():
        patient = Patient(
            patient_id='P001',
            first_name='John',
            last_name='Doe',
            created_by=test_user
        )
        db.session.add(patient)
        db.session.commit()
        return patient.id


@pytest.fixture
def test_case(app, test_user, test_patient):
    """Create a test case."""
    with app.app_context():
        case = Case(
            case_number='C001',
            user_id=test_user,
            patient_id=test_patient,
            study_type='Ultrasound',
            body_part='Abdomen',
            indication='Abdominal pain'
        )
        db.session.add(case)
        db.session.commit()
        return case.id


class TestStructuredFindingsModel:
    """Test the StructuredFindings model."""
    
    def test_create_structured_findings(self, app, test_case):
        """Test creating a StructuredFindings record."""
        with app.app_context():
            findings = StructuredFindings(
                case_id=test_case,
                liver_size='Normal',
                liver_texture='Normal',
                spleen_size='Normal',
                gb_calculus='Absent',
                right_kidney_size='Normal',
                left_kidney_size='Normal',
                bladder_filling='Full',
                ascites='Absent',
                comments='All organs appear normal'
            )
            db.session.add(findings)
            db.session.commit()
            
            # Verify the record was created
            assert findings.id is not None
            assert findings.case_id == test_case
            assert findings.liver_size == 'Normal'
            assert findings.comments == 'All organs appear normal'
    
    def test_structured_findings_relationship(self, app, test_case):
        """Test the relationship between Case and StructuredFindings."""
        with app.app_context():
            findings = StructuredFindings(
                case_id=test_case,
                liver_size='Enlarged'
            )
            db.session.add(findings)
            db.session.commit()
            
            # Retrieve case and check relationship
            case = Case.query.get(test_case)
            assert case.structured_findings is not None
            assert case.structured_findings.liver_size == 'Enlarged'
    
    def test_structured_findings_unique_constraint(self, app, test_case):
        """Test that only one StructuredFindings record can exist per case."""
        with app.app_context():
            # Create first findings
            findings1 = StructuredFindings(
                case_id=test_case,
                liver_size='Normal'
            )
            db.session.add(findings1)
            db.session.commit()
            
            # Try to create second findings for same case
            findings2 = StructuredFindings(
                case_id=test_case,
                liver_size='Enlarged'
            )
            db.session.add(findings2)
            
            # Should raise an integrity error
            with pytest.raises(Exception):
                db.session.commit()


class TestAIGeneratedFindingsModel:
    """Test the AIGeneratedFindings model."""
    
    def test_create_ai_findings(self, app, test_case):
        """Test creating an AIGeneratedFindings record."""
        with app.app_context():
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal',
                liver_texture='Normal',
                confidence_scores={'liver_size': 0.95, 'liver_texture': 0.88}
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # Verify the record was created
            assert ai_findings.id is not None
            assert ai_findings.case_id == test_case
            assert ai_findings.confidence_scores is not None
            assert ai_findings.confidence_scores['liver_size'] == 0.95
    
    def test_ai_findings_relationship(self, app, test_case):
        """Test the relationship between Case and AIGeneratedFindings."""
        with app.app_context():
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Enlarged',
                spleen_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # Retrieve case and check relationship
            case = Case.query.get(test_case)
            assert len(case.ai_findings) > 0
            assert case.ai_findings[0].liver_size == 'Enlarged'
    
    def test_multiple_ai_findings_per_case(self, app, test_case):
        """Test that multiple AIGeneratedFindings can exist per case."""
        with app.app_context():
            # Create first AI findings
            ai_findings1 = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal'
            )
            db.session.add(ai_findings1)
            db.session.commit()
            
            # Create second AI findings for same case
            ai_findings2 = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Enlarged'
            )
            db.session.add(ai_findings2)
            db.session.commit()
            
            # Both should exist
            case = Case.query.get(test_case)
            assert len(case.ai_findings) == 2


class TestFindingsEvaluationModel:
    """Test the FindingsEvaluation model."""
    
    def test_create_evaluation(self, app, test_case, test_user):
        """Test creating a FindingsEvaluation record."""
        with app.app_context():
            # Create AI findings first
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal',
                liver_texture='Normal',
                spleen_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # Create evaluation
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=test_user,
                field_correctness={
                    'liver_size': True,
                    'liver_texture': True,
                    'spleen_size': False
                },
                total_fields=3,
                correct_fields=2,
                accuracy_percentage=66.67,
                evaluation_notes='Spleen size was incorrect'
            )
            db.session.add(evaluation)
            db.session.commit()
            
            # Verify the record was created
            assert evaluation.id is not None
            assert evaluation.accuracy_percentage == 66.67
            assert evaluation.field_correctness['liver_size'] is True
            assert evaluation.field_correctness['spleen_size'] is False
    
    def test_evaluation_relationships(self, app, test_case, test_user):
        """Test relationships between Evaluation, AIFindings, and User."""
        with app.app_context():
            # Create AI findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Normal'
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # Create evaluation
            evaluation = FindingsEvaluation(
                ai_finding_id=ai_findings.id,
                user_id=test_user,
                field_correctness={'liver_size': True},
                total_fields=1,
                correct_fields=1,
                accuracy_percentage=100.0
            )
            db.session.add(evaluation)
            db.session.commit()
            
            # Test relationships
            assert evaluation.ai_finding is not None
            assert evaluation.ai_finding.id == ai_findings.id
            assert evaluation.user is not None
            assert evaluation.user.id == test_user
            
            # Test backref
            assert len(ai_findings.evaluations) > 0
            assert ai_findings.evaluations[0].id == evaluation.id


class TestDataSeparation:
    """Test that user-provided and AI-generated findings are kept separate."""
    
    def test_separate_storage(self, app, test_case):
        """Test that user and AI findings are stored in separate tables."""
        with app.app_context():
            # Create user-provided findings
            user_findings = StructuredFindings(
                case_id=test_case,
                liver_size='Normal',
                comments='User provided'
            )
            db.session.add(user_findings)
            
            # Create AI-generated findings
            ai_findings = AIGeneratedFindings(
                case_id=test_case,
                liver_size='Enlarged',
                comments='AI generated'
            )
            db.session.add(ai_findings)
            db.session.commit()
            
            # Retrieve case and verify both exist separately
            case = Case.query.get(test_case)
            assert case.structured_findings is not None
            assert case.structured_findings.comments == 'User provided'
            assert len(case.ai_findings) > 0
            assert case.ai_findings[0].comments == 'AI generated'
            
            # Verify they have different values
            assert case.structured_findings.liver_size == 'Normal'
            assert case.ai_findings[0].liver_size == 'Enlarged'
