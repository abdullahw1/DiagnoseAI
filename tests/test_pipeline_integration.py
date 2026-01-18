"""
Integration tests for the complete multi-agent pipeline.

These tests verify that:
1. Case creation triggers the orchestrator
2. All agent outputs are stored in the database
3. Report generation uses Agent E output
4. Error handling and retry logic work correctly
5. The complete pipeline executes end-to-end
"""

import pytest
import os
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from app.models import Case, Report, Patient, CaseImage, AgentOutput, User
from app import db
from app.main import run_multi_agent_pipeline


class TestPipelineIntegration:
    """Integration tests for multi-agent pipeline with case workflow."""
    
    @pytest.fixture
    def test_user(self, app):
        """Create a test user."""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
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
                patient_id='TEST001',
                first_name='Test',
                last_name='Patient',
                created_by=test_user.id
            )
            db.session.add(patient)
            db.session.commit()
            yield patient
            db.session.delete(patient)
            db.session.commit()
    
    @pytest.fixture
    def test_case(self, app, test_user, test_patient):
        """Create a test case with images."""
        with app.app_context():
            case = Case(
                case_number='000001',
                user_id=test_user.id,
                patient_id=test_patient.id,
                study_type='Ultrasound',
                body_part='Liver',
                indication='Evaluate for liver disease',
                clinical_history='Patient with elevated liver enzymes',
                patient_history='History of hepatitis',
                clinical_indication='Elevated ALT/AST',
                lab_results='ALT: 120 U/L, AST: 95 U/L',
                status='processing'
            )
            db.session.add(case)
            db.session.commit()
            
            # Add a test image
            case_image = CaseImage(
                case_id=case.id,
                filename='test_image.jpg',
                original_filename='test_image.jpg',
                image_path='/tmp/test_image.jpg',
                order_index=0,
                file_size=1024,
                mime_type='image/jpeg'
            )
            db.session.add(case_image)
            
            # Set legacy fields
            case.image_filename = 'test_image.jpg'
            case.image_path = '/tmp/test_image.jpg'
            
            db.session.commit()
            yield case
            
            # Cleanup
            db.session.delete(case)
            db.session.commit()
    
    def test_pipeline_stores_all_agent_outputs(self, app, test_case):
        """Test that all agent outputs are stored in the database."""
        with app.app_context():
            # Mock all agent executions to return success
            mock_agents = {}
            for agent_name in ['agent_a', 'agent_b', 'agent_c', 'agent_d', 'agent_e', 'agent_f']:
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {
                        'test_key': f'test_value_from_{agent_name}',
                        'agent_name': agent_name
                    },
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
                
                # Run the pipeline
                result = run_multi_agent_pipeline(test_case.id)
                
                # Verify success
                assert result['success'] is True
                assert result['report_id'] is not None
                assert len(result['errors']) == 0
                
                # Verify all agent outputs were stored
                agent_outputs = AgentOutput.query.filter_by(case_id=test_case.id).all()
                assert len(agent_outputs) == 6
                
                # Verify each agent's output was stored
                agent_names = [output.agent_name for output in agent_outputs]
                expected_agents = ['agent_a', 'agent_b', 'agent_c', 'agent_d', 'agent_e', 'agent_f']
                for expected_agent in expected_agents:
                    assert expected_agent in agent_names
                
                # Verify output data was stored correctly
                for output in agent_outputs:
                    assert output.output_data is not None
                    assert output.execution_time_ms > 0
                    assert output.error_message is None
    
    def test_pipeline_creates_report_with_agent_e_output(self, app, test_case):
        """Test that report is created using Agent E output."""
        with app.app_context():
            # Mock agents with specific outputs
            mock_report_text = "This is a test radiology report generated by Agent E."
            mock_confidence_score = 0.85
            mock_safety_flags = {"critical_findings": [], "warnings": []}
            
            mock_agents = {}
            for agent_name in ['agent_a', 'agent_b', 'agent_c', 'agent_d']:
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {'data': f'{agent_name}_output'},
                    'error': None,
                    'execution_time_ms': 100
                }
                mock_agents[agent_name] = mock_agent
            
            # Agent E returns report text
            mock_agent_e = Mock()
            mock_agent_e.execute.return_value = {
                'success': True,
                'output': {
                    'report_text': mock_report_text,
                    'structured_sections': {
                        'findings': 'Test findings',
                        'impression': 'Test impression'
                    }
                },
                'error': None,
                'execution_time_ms': 150
            }
            mock_agents['agent_e'] = mock_agent_e
            
            # Agent F returns safety validation
            mock_agent_f = Mock()
            mock_agent_f.execute.return_value = {
                'success': True,
                'output': {
                    'confidence_score': mock_confidence_score,
                    'safety_flags': mock_safety_flags,
                    'validation_passed': True
                },
                'error': None,
                'execution_time_ms': 80
            }
            mock_agents['agent_f'] = mock_agent_f
            
            # Mock the agent classes
            with patch('app.main.ClinicalContextAgent', return_value=mock_agents['agent_a']), \
                 patch('app.main.QualityAssessmentAgent', return_value=mock_agents['agent_b']), \
                 patch('app.main.FindingsExtractionAgent', return_value=mock_agents['agent_c']), \
                 patch('app.main.DiagnosticReasoningAgent', return_value=mock_agents['agent_d']), \
                 patch('app.main.ReportDraftingAgent', return_value=mock_agents['agent_e']), \
                 patch('app.main.SafetyValidationAgent', return_value=mock_agents['agent_f']):
                
                # Run the pipeline
                result = run_multi_agent_pipeline(test_case.id)
                
                # Verify report was created
                assert result['success'] is True
                report_id = result['report_id']
                assert report_id is not None
                
                # Verify report contains Agent E output
                report = Report.query.get(report_id)
                assert report is not None
                assert report.case_id == test_case.id
                assert report.draft_text == mock_report_text
                assert report.confidence_score == mock_confidence_score
                assert report.safety_flags == mock_safety_flags
                assert report.is_finalized is False
                
                # Verify draft_json contains all agent outputs
                assert report.draft_json is not None
                assert 'draft_report' in report.draft_json
                assert report.draft_json['draft_report']['report_text'] == mock_report_text
    
    def test_pipeline_handles_agent_failure(self, app, test_case):
        """Test that pipeline handles agent failures gracefully."""
        with app.app_context():
            # Mock agents where Agent C fails
            mock_agents = {}
            for agent_name in ['agent_a', 'agent_b']:
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {'data': f'{agent_name}_output'},
                    'error': None,
                    'execution_time_ms': 100
                }
                mock_agents[agent_name] = mock_agent
            
            # Agent C fails
            mock_agent_c = Mock()
            mock_agent_c.execute.return_value = {
                'success': False,
                'output': None,
                'error': 'Agent C failed: API timeout',
                'execution_time_ms': 5000
            }
            mock_agents['agent_c'] = mock_agent_c
            
            # Remaining agents
            for agent_name in ['agent_d', 'agent_e', 'agent_f']:
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {'data': f'{agent_name}_output'},
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
                
                # Run the pipeline
                result = run_multi_agent_pipeline(test_case.id)
                
                # Verify failure was captured
                assert result['success'] is False
                assert len(result['errors']) > 0
                assert any('Agent C failed' in error for error in result['errors'])
                
                # Verify agent outputs were still stored for successful agents
                agent_outputs = AgentOutput.query.filter_by(case_id=test_case.id).all()
                assert len(agent_outputs) >= 2  # At least A and B succeeded
                
                # Verify failed agent output was logged
                failed_output = AgentOutput.query.filter_by(
                    case_id=test_case.id,
                    agent_name='agent_c'
                ).first()
                assert failed_output is not None
                assert failed_output.error_message is not None
                assert 'Agent C failed' in failed_output.error_message
                
                # Verify case status was updated
                case = Case.query.get(test_case.id)
                assert case.status == 'analysis_failed'
    
    def test_pipeline_updates_case_status(self, app, test_case):
        """Test that pipeline updates case status appropriately."""
        with app.app_context():
            # Mock successful pipeline
            mock_agents = {}
            for agent_name in ['agent_a', 'agent_b', 'agent_c', 'agent_d', 'agent_e', 'agent_f']:
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {'data': f'{agent_name}_output'},
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
                
                # Verify initial status
                assert test_case.status == 'processing'
                
                # Run the pipeline
                result = run_multi_agent_pipeline(test_case.id)
                
                # Verify status was updated to analysis_complete
                case = Case.query.get(test_case.id)
                assert case.status == 'analysis_complete'
    
    def test_pipeline_execution_log(self, app, test_case):
        """Test that pipeline maintains execution log."""
        with app.app_context():
            # Mock agents with varying execution times
            mock_agents = {}
            execution_times = {
                'agent_a': 150,
                'agent_b': 200,
                'agent_c': 300,
                'agent_d': 180,
                'agent_e': 250,
                'agent_f': 120
            }
            
            for agent_name, exec_time in execution_times.items():
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {'data': f'{agent_name}_output'},
                    'error': None,
                    'execution_time_ms': exec_time
                }
                mock_agents[agent_name] = mock_agent
            
            # Mock the agent classes
            with patch('app.main.ClinicalContextAgent', return_value=mock_agents['agent_a']), \
                 patch('app.main.QualityAssessmentAgent', return_value=mock_agents['agent_b']), \
                 patch('app.main.FindingsExtractionAgent', return_value=mock_agents['agent_c']), \
                 patch('app.main.DiagnosticReasoningAgent', return_value=mock_agents['agent_d']), \
                 patch('app.main.ReportDraftingAgent', return_value=mock_agents['agent_e']), \
                 patch('app.main.SafetyValidationAgent', return_value=mock_agents['agent_f']):
                
                # Run the pipeline
                result = run_multi_agent_pipeline(test_case.id)
                
                # Verify execution log
                assert 'execution_log' in result
                assert len(result['execution_log']) == 6
                
                # Verify each agent is in the log
                logged_agents = [entry['agent'] for entry in result['execution_log']]
                for agent_name in execution_times.keys():
                    assert agent_name in logged_agents
                
                # Verify execution times are logged
                for entry in result['execution_log']:
                    assert 'execution_time_ms' in entry
                    assert entry['execution_time_ms'] > 0
                    assert 'success' in entry
                    assert 'timestamp' in entry
    
    def test_pipeline_with_minimal_clinical_data(self, app, test_user, test_patient):
        """Test pipeline with minimal clinical information."""
        with app.app_context():
            # Create case with minimal data
            case = Case(
                case_number='000002',
                user_id=test_user.id,
                patient_id=test_patient.id,
                study_type='Ultrasound',
                indication='Routine screening',
                status='processing'
            )
            db.session.add(case)
            db.session.commit()
            
            # Mock agents
            mock_agents = {}
            for agent_name in ['agent_a', 'agent_b', 'agent_c', 'agent_d', 'agent_e', 'agent_f']:
                mock_agent = Mock()
                mock_agent.execute.return_value = {
                    'success': True,
                    'output': {'data': f'{agent_name}_output'},
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
                
                # Run the pipeline
                result = run_multi_agent_pipeline(case.id)
                
                # Verify pipeline still succeeds with minimal data
                assert result['success'] is True
                assert result['report_id'] is not None
                
                # Cleanup
                db.session.delete(case)
                db.session.commit()
    
    def test_pipeline_error_recovery(self, app, test_case):
        """Test that pipeline can recover from transient errors."""
        with app.app_context():
            # This test verifies that the orchestrator's error handling
            # properly logs errors and continues execution
            
            # Mock agents where one fails but others succeed
            mock_agents = {}
            for agent_name in ['agent_a', 'agent_b', 'agent_c', 'agent_d', 'agent_e', 'agent_f']:
                mock_agent = Mock()
                if agent_name == 'agent_d':
                    # Agent D fails
                    mock_agent.execute.return_value = {
                        'success': False,
                        'output': None,
                        'error': 'Transient API error',
                        'execution_time_ms': 100
                    }
                else:
                    mock_agent.execute.return_value = {
                        'success': True,
                        'output': {'data': f'{agent_name}_output'},
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
                
                # Run the pipeline
                result = run_multi_agent_pipeline(test_case.id)
                
                # Verify error was captured
                assert result['success'] is False
                assert len(result['errors']) > 0
                
                # Verify all agents were attempted (even after failure)
                agent_outputs = AgentOutput.query.filter_by(case_id=test_case.id).all()
                assert len(agent_outputs) == 6  # All agents attempted
                
                # Verify the failed agent's error was logged
                failed_output = AgentOutput.query.filter_by(
                    case_id=test_case.id,
                    agent_name='agent_d'
                ).first()
                assert failed_output is not None
                assert failed_output.error_message is not None
