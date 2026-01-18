"""
Tests for multi-agent architecture database models.
"""
import pytest
from datetime import datetime, date
from app import db
from app.models import (
    User, Case, Report, AgentOutput, Feedback, 
    Metric, PromptVersion, RAGCase, Patient
)


def test_user_role_field(app):
    """Test that User model has role field."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            role='radiologist'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        retrieved_user = User.query.filter_by(username='testuser').first()
        assert retrieved_user is not None
        assert retrieved_user.role == 'radiologist'


def test_case_multi_agent_fields(app):
    """Test that Case model has new multi-agent fields."""
    with app.app_context():
        # Create user and patient first
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        patient = Patient(
            patient_id='TEST001',
            first_name='Test',
            last_name='Patient',
            created_by=user.id
        )
        db.session.add(patient)
        db.session.flush()
        
        case = Case(
            case_number='000001',
            user_id=user.id,
            patient_id=patient.id,
            patient_history='Patient has history of liver disease',
            clinical_indication='Suspected hepatic lesion',
            lab_results='ALT: 45, AST: 38'
        )
        db.session.add(case)
        db.session.commit()
        
        retrieved_case = Case.query.filter_by(case_number='000001').first()
        assert retrieved_case is not None
        assert retrieved_case.patient_history == 'Patient has history of liver disease'
        assert retrieved_case.clinical_indication == 'Suspected hepatic lesion'
        assert retrieved_case.lab_results == 'ALT: 45, AST: 38'


def test_report_confidence_and_safety_fields(app):
    """Test that Report model has confidence_score and safety_flags fields."""
    with app.app_context():
        # Create necessary dependencies
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        patient = Patient(
            patient_id='TEST001',
            first_name='Test',
            last_name='Patient',
            created_by=user.id
        )
        db.session.add(patient)
        db.session.flush()
        
        case = Case(
            case_number='000001',
            user_id=user.id,
            patient_id=patient.id
        )
        db.session.add(case)
        db.session.flush()
        
        report = Report(
            case_id=case.id,
            draft_text='Test report',
            confidence_score=0.85,
            safety_flags={'critical_findings': False, 'uncertain_findings': ['lesion_size']}
        )
        db.session.add(report)
        db.session.commit()
        
        retrieved_report = Report.query.filter_by(case_id=case.id).first()
        assert retrieved_report is not None
        assert retrieved_report.confidence_score == 0.85
        assert retrieved_report.safety_flags is not None
        assert retrieved_report.safety_flags['critical_findings'] is False


def test_agent_output_model(app):
    """Test AgentOutput model creation and retrieval."""
    with app.app_context():
        # Create necessary dependencies
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        patient = Patient(
            patient_id='TEST001',
            first_name='Test',
            last_name='Patient',
            created_by=user.id
        )
        db.session.add(patient)
        db.session.flush()
        
        case = Case(
            case_number='000001',
            user_id=user.id,
            patient_id=patient.id
        )
        db.session.add(case)
        db.session.flush()
        
        agent_output = AgentOutput(
            case_id=case.id,
            agent_name='agent_a_context',
            input_data={'clinical_notes': 'Test notes'},
            output_data={'structured_context': 'Extracted context'},
            execution_time_ms=150
        )
        db.session.add(agent_output)
        db.session.commit()
        
        retrieved = AgentOutput.query.filter_by(case_id=case.id).first()
        assert retrieved is not None
        assert retrieved.agent_name == 'agent_a_context'
        assert retrieved.execution_time_ms == 150


def test_feedback_model(app):
    """Test Feedback model creation and retrieval."""
    with app.app_context():
        # Create necessary dependencies
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        patient = Patient(
            patient_id='TEST001',
            first_name='Test',
            last_name='Patient',
            created_by=user.id
        )
        db.session.add(patient)
        db.session.flush()
        
        case = Case(
            case_number='000001',
            user_id=user.id,
            patient_id=patient.id
        )
        db.session.add(case)
        db.session.flush()
        
        report = Report(
            case_id=case.id,
            draft_text='Test report'
        )
        db.session.add(report)
        db.session.flush()
        
        feedback = Feedback(
            case_id=case.id,
            report_id=report.id,
            user_id=user.id,
            action='modify',
            modifications={'changes': ['Updated finding description']},
            confidence_level=4
        )
        db.session.add(feedback)
        db.session.commit()
        
        retrieved = Feedback.query.filter_by(report_id=report.id).first()
        assert retrieved is not None
        assert retrieved.action == 'modify'
        assert retrieved.confidence_level == 4


def test_metric_model(app):
    """Test Metric model creation and retrieval."""
    with app.app_context():
        metric = Metric(
            metric_name='acceptance_rate',
            metric_value=0.75,
            metric_category='overall',
            time_period='weekly',
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 7)
        )
        db.session.add(metric)
        db.session.commit()
        
        retrieved = Metric.query.filter_by(metric_name='acceptance_rate').first()
        assert retrieved is not None
        assert retrieved.metric_value == 0.75
        assert retrieved.time_period == 'weekly'


def test_prompt_version_model(app):
    """Test PromptVersion model creation and retrieval."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        prompt_version = PromptVersion(
            agent_name='agent_a_context',
            version=1,
            prompt_template='Extract clinical context from: {input}',
            change_description='Initial prompt version',
            is_active=True,
            created_by=user.id
        )
        db.session.add(prompt_version)
        db.session.commit()
        
        retrieved = PromptVersion.query.filter_by(agent_name='agent_a_context').first()
        assert retrieved is not None
        assert retrieved.version == 1
        assert retrieved.is_active is True


def test_rag_case_model(app):
    """Test RAGCase model creation and retrieval."""
    with app.app_context():
        # Create necessary dependencies
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        patient = Patient(
            patient_id='TEST001',
            first_name='Test',
            last_name='Patient',
            created_by=user.id
        )
        db.session.add(patient)
        db.session.flush()
        
        case = Case(
            case_number='000001',
            user_id=user.id,
            patient_id=patient.id
        )
        db.session.add(case)
        db.session.flush()
        
        report = Report(
            case_id=case.id,
            draft_text='Test report',
            is_finalized=True
        )
        db.session.add(report)
        db.session.flush()
        
        rag_case = RAGCase(
            case_id=case.id,
            report_id=report.id,
            embedding=b'fake_embedding_data',
            pathology_tags=['hepatic_lesion', 'cirrhosis'],
            quality_score=0.9,
            is_exemplar=True
        )
        db.session.add(rag_case)
        db.session.commit()
        
        retrieved = RAGCase.query.filter_by(case_id=case.id).first()
        assert retrieved is not None
        assert retrieved.quality_score == 0.9
        assert retrieved.is_exemplar is True
        assert 'hepatic_lesion' in retrieved.pathology_tags


def test_case_relationships(app):
    """Test that Case has relationships with AgentOutput and Feedback."""
    with app.app_context():
        # Create necessary dependencies
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        patient = Patient(
            patient_id='TEST001',
            first_name='Test',
            last_name='Patient',
            created_by=user.id
        )
        db.session.add(patient)
        db.session.flush()
        
        case = Case(
            case_number='000001',
            user_id=user.id,
            patient_id=patient.id
        )
        db.session.add(case)
        db.session.flush()
        
        # Add agent output
        agent_output = AgentOutput(
            case_id=case.id,
            agent_name='agent_a_context',
            output_data={'test': 'data'}
        )
        db.session.add(agent_output)
        
        # Add report and feedback
        report = Report(case_id=case.id, draft_text='Test')
        db.session.add(report)
        db.session.flush()
        
        feedback = Feedback(
            case_id=case.id,
            report_id=report.id,
            user_id=user.id,
            action='approve'
        )
        db.session.add(feedback)
        db.session.commit()
        
        # Test relationships
        retrieved_case = Case.query.filter_by(case_number='000001').first()
        assert len(retrieved_case.agent_outputs) == 1
        assert len(retrieved_case.feedback) == 1
        assert retrieved_case.agent_outputs[0].agent_name == 'agent_a_context'
