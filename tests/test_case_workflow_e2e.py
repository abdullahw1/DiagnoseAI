"""
End-to-end tests for case workflow with multi-agent pipeline integration.

These tests verify the complete workflow from case creation through
report generation using the multi-agent pipeline.
"""

import pytest
import os
from unittest.mock import Mock, patch
from app.models import Case, Report, Patient, User, AgentOutput
from app import db


class TestCaseWorkflowE2E:
    """End-to-end tests for case creation and multi-agent pipeline integration."""
    
    @pytest.fixture
    def test_user(self, app):
        """Create a test user."""
        with app.app_context():
            user = User(username='e2euser', email='e2e@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            yield user
            db.session.delete(user)
            db.session.commit()
    
    @pytest.fixture
    def test_patient(self, app, test_user):
        """Create a test patient."""
        with app.app_context():
            patient = Patient(
                patient_id='E2E001',
                first_name='E2E',
                last_name='Patient',
                created_by=test_user.id
            )
            db.session.add(patient)
            db.session.commit()
            yield patient
            db.session.delete(patient)
            db.session.commit()
    
    @pytest.fixture
    def mock_successful_agents(self):
        """Create mock agents that all succeed."""
        mock_agents = {}
        
        # Agent A: Clinical Context
        mock_agent_a = Mock()
        mock_agent_a.execute.return_value = {
            'success': True,
            'output': {
                'relevant_history': 'Patient with chronic liver disease',
                'clinical_indication': 'Elevated liver enzymes',
                'pertinent_labs': {'ALT': '120 U/L', 'AST': '95 U/L'},
                'risk_factors': ['Hepatitis history', 'Elevated enzymes'],
                'clinical_questions': ['Assess liver parenchyma', 'Evaluate for focal lesions'],
                'summary': 'Patient with elevated liver enzymes and hepatitis history'
            },
            'error': None,
            'execution_time_ms': 150
        }
        mock_agents['agent_a'] = mock_agent_a
        
        # Agent B: Quality Assessment
        mock_agent_b = Mock()
        mock_agent_b.execute.return_value = {
            'success': True,
            'output': {
                'views_identified': ['Sagittal liver', 'Transverse liver'],
                'quality_scores': {'overall': 4, 'clarity': 4, 'positioning': 4},
                'technical_adequacy': 'Adequate for diagnostic interpretation',
                'limitations': []
            },
            'error': None,
            'execution_time_ms': 200
        }
        mock_agents['agent_b'] = mock_agent_b
        
        # Agent C: Findings
        mock_agent_c = Mock()
        mock_agent_c.execute.return_value = {
            'success': True,
            'output': {
                'findings': [
                    {
                        'category': 'Parenchyma',
                        'finding': 'Increased echogenicity',
                        'severity': 'Moderate'
                    },
                    {
                        'category': 'Surface',
                        'finding': 'Smooth contour',
                        'severity': 'Normal'
                    }
                ],
                'measurements': {'liver_span': '15 cm'},
                'summary': 'Increased hepatic echogenicity suggesting fatty infiltration'
            },
            'error': None,
            'execution_time_ms': 300
        }
        mock_agents['agent_c'] = mock_agent_c
        
        # Agent D: Reasoning
        mock_agent_d = Mock()
        mock_agent_d.execute.return_value = {
            'success': True,
            'output': {
                'differential_diagnosis': [
                    'Hepatic steatosis (most likely)',
                    'Chronic hepatitis',
                    'Early cirrhosis'
                ],
                'reasoning': 'Increased echogenicity with elevated enzymes suggests fatty liver',
                'recommendations': ['Clinical correlation', 'Follow-up imaging in 6 months']
            },
            'error': None,
            'execution_time_ms': 180
        }
        mock_agents['agent_d'] = mock_agent_d
        
        # Agent E: Report
        mock_agent_e = Mock()
        mock_agent_e.execute.return_value = {
            'success': True,
            'output': {
                'report_text': 'FINDINGS: Increased hepatic echogenicity. IMPRESSION: Hepatic steatosis.',
                'structured_sections': {
                    'technique': 'Ultrasound examination of the liver',
                    'findings': 'Increased hepatic echogenicity consistent with fatty infiltration',
                    'impression': 'Hepatic steatosis',
                    'recommendations': 'Clinical correlation and follow-up'
                },
                'summary': 'Hepatic steatosis identified'
            },
            'error': None,
            'execution_time_ms': 250
        }
        mock_agents['agent_e'] = mock_agent_e
        
        # Agent F: Safety
        mock_agent_f = Mock()
        mock_agent_f.execute.return_value = {
            'success': True,
            'output': {
                'validation_passed': True,
                'confidence_score': 0.87,
                'safety_flags': {'critical_findings': [], 'warnings': []},
                'consistency_checks': {'passed': True},
                'issues': [],
                'summary': 'Report validated successfully'
            },
            'error': None,
            'execution_time_ms': 120
        }
        mock_agents['agent_f'] = mock_agent_f
        
        return mock_agents
    
    def test_case_creation_triggers_pipeline(self, app, test_user, test_patient, mock_successful_agents):
        """Test that creating a case triggers the multi-agent pipeline."""
        with app.app_context():
            # Create a case
            case = Case(
                case_number='E2E001',
                user_id=test_user.id,
                patient_id=test_patient.id,
                study_type='Ultrasound',
                body_part='Liver',
                indication='Evaluate liver',
                clinical_history='Elevated enzymes',
                status='processing'
            )
            db.session.add(case)
            db.session.commit()
            
            # Mock the agent classes
            with patch('app.main.ClinicalContextAgent', return_value=mock_successful_agents['agent_a']), \
                 patch('app.main.QualityAssessmentAgent', return_value=mock_successful_agents['agent_b']), \
                 patch('app.main.FindingsExtractionAgent', return_value=mock_successful_agents['agent_c']), \
                 patch('app.main.DiagnosticReasoningAgent', return_value=mock_successful_agents['agent_d']), \
                 patch('app.main.ReportDraftingAgent', return_value=mock_successful_agents['agent_e']), \
                 patch('app.main.SafetyValidationAgent', return_value=mock_successful_agents['agent_f']):
                
                # Import and run the pipeline function
                from app.main import run_multi_agent_pipeline
                result = run_multi_agent_pipeline(case.id)
                
                # Verify pipeline executed successfully
                assert result['success'] is True
                assert result['report_id'] is not None
                
                # Verify case status was updated
                case = Case.query.get(case.id)
                assert case.status == 'analysis_complete'
                
                # Verify report was created
                report = Report.query.get(result['report_id'])
                assert report is not None
                assert report.case_id == case.id
                assert report.draft_text == 'FINDINGS: Increased hepatic echogenicity. IMPRESSION: Hepatic steatosis.'
                assert report.confidence_score == 0.87
                
                # Verify all agent outputs were stored
                agent_outputs = AgentOutput.query.filter_by(case_id=case.id).all()
                assert len(agent_outputs) == 6
                
                # Cleanup
                db.session.delete(case)
                db.session.commit()
    
    def test_pipeline_failure_updates_case_status(self, app, test_user, test_patient):
        """Test that pipeline failure updates case status appropriately."""
        with app.app_context():
            # Create a case
            case = Case(
                case_number='E2E002',
                user_id=test_user.id,
                patient_id=test_patient.id,
                study_type='Ultrasound',
                indication='Test case',
                status='processing'
            )
            db.session.add(case)
            db.session.commit()
            
            # Mock agents where one fails
            mock_agents = {}
            for agent_name in ['agent_a', 'agent_b']:
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {'data': 'test'},
                    'error': None,
                    'execution_time_ms': 100
                }
                mock_agents[agent_name] = mock_agent
            
            # Agent C fails
            mock_agent_c = Mock()
            mock_agent_c.execute.return_value = {
                'success': False,
                'output': None,
                'error': 'API timeout',
                'execution_time_ms': 5000
            }
            mock_agents['agent_c'] = mock_agent_c
            
            for agent_name in ['agent_d', 'agent_e', 'agent_f']:
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {'data': 'test'},
                    'error': None,
                    'execution_time_ms': 100
                }
                mock_agents[agent_name] = mock_agent
            
            # Mock the agent classes
            with patch('app.main.ClinicalContextAgent', return_value=mock_agents['agent_a']), \
                 patch('app.main.QualityAssessmentAgent', return_value=mock_agents['agent_b']), \
                 patch('app.main.FindingsExtractionAgent', return_value=mock_agents['agent_c']), \
                 patch('app.main.DiagnosticReasoningAgent', return_value=mock_agents['agent_d']), \
                 patch('app.main.ReportDraftingAgent', return_value=mock_agents['agent_e']), \
                 patch('app.main.SafetyValidationAgent', return_value=mock_agents['agent_f']):
                
                # Import and run the pipeline function
                from app.main import run_multi_agent_pipeline
                result = run_multi_agent_pipeline(case.id)
                
                # Verify pipeline failed
                assert result['success'] is False
                assert len(result['errors']) > 0
                
                # Verify case status was updated to failed
                case = Case.query.get(case.id)
                assert case.status == 'analysis_failed'
                
                # Cleanup
                db.session.delete(case)
                db.session.commit()
    
    def test_report_contains_all_agent_data(self, app, test_user, test_patient, mock_successful_agents):
        """Test that the final report contains data from all agents."""
        with app.app_context():
            # Create a case
            case = Case(
                case_number='E2E003',
                user_id=test_user.id,
                patient_id=test_patient.id,
                study_type='Ultrasound',
                indication='Test case',
                status='processing'
            )
            db.session.add(case)
            db.session.commit()
            
            # Mock the agent classes
            with patch('app.main.ClinicalContextAgent', return_value=mock_successful_agents['agent_a']), \
                 patch('app.main.QualityAssessmentAgent', return_value=mock_successful_agents['agent_b']), \
                 patch('app.main.FindingsExtractionAgent', return_value=mock_successful_agents['agent_c']), \
                 patch('app.main.DiagnosticReasoningAgent', return_value=mock_successful_agents['agent_d']), \
                 patch('app.main.ReportDraftingAgent', return_value=mock_successful_agents['agent_e']), \
                 patch('app.main.SafetyValidationAgent', return_value=mock_successful_agents['agent_f']):
                
                # Import and run the pipeline function
                from app.main import run_multi_agent_pipeline
                result = run_multi_agent_pipeline(case.id)
                
                # Get the report
                report = Report.query.get(result['report_id'])
                
                # Verify draft_json contains all agent outputs
                assert 'clinical_context' in report.draft_json
                assert 'quality_assessment' in report.draft_json
                assert 'findings' in report.draft_json
                assert 'diagnostic_reasoning' in report.draft_json
                assert 'draft_report' in report.draft_json
                assert 'safety_validation' in report.draft_json
                
                # Verify specific data from each agent
                assert report.draft_json['clinical_context']['summary'] == 'Patient with elevated liver enzymes and hepatitis history'
                assert report.draft_json['quality_assessment']['technical_adequacy'] == 'Adequate for diagnostic interpretation'
                assert report.draft_json['findings']['summary'] == 'Increased hepatic echogenicity suggesting fatty infiltration'
                assert any('Hepatic steatosis' in dx for dx in report.draft_json['diagnostic_reasoning']['differential_diagnosis'])
                assert report.draft_json['draft_report']['summary'] == 'Hepatic steatosis identified'
                assert report.draft_json['safety_validation']['validation_passed'] is True
                
                # Cleanup
                db.session.delete(case)
                db.session.commit()
