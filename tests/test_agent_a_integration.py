"""
Integration tests for Agent A with the orchestrator.

Tests the integration of ClinicalContextAgent with the AgentOrchestrator
to ensure proper data flow and execution.
"""

import pytest
import json
from unittest.mock import Mock, patch
from app.agents.agent_a_context import ClinicalContextAgent
from app.agents.orchestrator import AgentOrchestrator
from app.models import Case, Patient, User


class TestAgentAIntegration:
    """Integration tests for Agent A with orchestrator."""
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_agent_a_with_orchestrator(self, mock_openai_class, app):
        """Test Agent A integration with orchestrator."""
        with app.app_context(), patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            # Mock OpenAI response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                'relevant_history': 'History of chronic liver disease',
                'clinical_indication': 'Elevated liver enzymes, rule out hepatic lesion',
                'pertinent_labs': {
                    'ALT': '85 U/L (elevated)',
                    'AST': '72 U/L (elevated)',
                    'Bilirubin': '1.2 mg/dL (normal)'
                },
                'risk_factors': ['Chronic liver disease', 'Elevated transaminases', 'Age > 50'],
                'clinical_questions': [
                    'Assess liver parenchyma echogenicity',
                    'Rule out focal hepatic lesions',
                    'Evaluate for signs of cirrhosis'
                ],
                'summary': 'Patient with chronic liver disease presenting with elevated liver enzymes. Clinical concern for hepatic lesion.'
            })
            
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client
            
            # Create test data
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            from app import db
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                patient_id='P001',
                first_name='Test',
                last_name='Patient',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            case = Case(
                case_number='C001',
                user_id=user.id,
                patient_id=patient.id,
                status='pending',
                patient_history='History of chronic liver disease diagnosed 5 years ago',
                clinical_indication='Elevated liver enzymes, rule out hepatic lesion',
                lab_results='ALT: 85 U/L, AST: 72 U/L, Bilirubin: 1.2 mg/dL'
            )
            db.session.add(case)
            db.session.commit()
            
            # Create orchestrator and register Agent A
            orchestrator = AgentOrchestrator()
            agent_a = ClinicalContextAgent()
            orchestrator.register_agent('agent_a', agent_a)
            
            # Prepare input for Agent A
            input_data = {
                'case_id': case.id,
                'case_data': {
                    'patient_history': case.patient_history,
                    'clinical_indication': case.clinical_indication,
                    'lab_results': case.lab_results
                }
            }
            
            # Execute Agent A through orchestrator's execute method
            result = agent_a.execute(input_data)
            
            # Verify execution was successful
            assert result['success'] is True
            assert result['output'] is not None
            assert result['error'] is None
            
            # Verify output structure
            output = result['output']
            assert 'relevant_history' in output
            assert 'clinical_indication' in output
            assert 'pertinent_labs' in output
            assert 'risk_factors' in output
            assert 'clinical_questions' in output
            assert 'summary' in output
            
            # Verify content
            assert 'chronic liver disease' in output['relevant_history'].lower()
            assert 'elevated liver enzymes' in output['clinical_indication'].lower()
            assert 'ALT' in output['pertinent_labs']
            assert len(output['risk_factors']) > 0
            assert len(output['clinical_questions']) > 0
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_agent_a_state_passing(self, mock_openai_class, app):
        """Test that Agent A output is properly passed in orchestrator state."""
        with app.app_context(), patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            # Mock OpenAI response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = json.dumps({
                'relevant_history': 'Test history',
                'clinical_indication': 'Test indication',
                'pertinent_labs': {'Test': 'Value'},
                'risk_factors': ['Risk1'],
                'clinical_questions': ['Question1'],
                'summary': 'Test summary'
            })
            
            mock_client = Mock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_class.return_value = mock_client
            
            # Create orchestrator and agent
            orchestrator = AgentOrchestrator()
            agent_a = ClinicalContextAgent()
            orchestrator.register_agent('agent_a', agent_a)
            
            # Create initial state
            state = {
                'case_id': 1,
                'case_data': {
                    'patient_history': 'Test history',
                    'clinical_indication': 'Test indication'
                },
                'clinical_context': None,
                'quality_assessment': None,
                'findings': None,
                'diagnostic_reasoning': None,
                'draft_report': None,
                'safety_validation': None,
                'errors': [],
                'execution_log': []
            }
            
            # Execute Agent A through orchestrator
            with patch.object(orchestrator, '_log_agent_execution'):
                result_state = orchestrator._execute_agent('agent_a', state, 'clinical_context')
            
            # Verify state was updated
            assert result_state['clinical_context'] is not None
            assert 'relevant_history' in result_state['clinical_context']
            assert 'summary' in result_state['clinical_context']
            assert len(result_state['errors']) == 0
            assert len(result_state['execution_log']) == 1
            assert result_state['execution_log'][0]['agent'] == 'agent_a'
            assert result_state['execution_log'][0]['success'] is True
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_agent_a_minimal_clinical_info(self, mock_openai_class, app):
        """Test Agent A with minimal clinical information."""
        with app.app_context(), patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            
            # Create orchestrator and agent
            orchestrator = AgentOrchestrator()
            agent_a = ClinicalContextAgent()
            orchestrator.register_agent('agent_a', agent_a)
            
            # Create state with minimal info
            state = {
                'case_id': 1,
                'case_data': {
                    'patient_history': '',
                    'clinical_indication': '',
                    'lab_results': ''
                },
                'clinical_context': None,
                'quality_assessment': None,
                'findings': None,
                'diagnostic_reasoning': None,
                'draft_report': None,
                'safety_validation': None,
                'errors': [],
                'execution_log': []
            }
            
            # Execute Agent A
            with patch.object(orchestrator, '_log_agent_execution'):
                result_state = orchestrator._execute_agent('agent_a', state, 'clinical_context')
            
            # Verify minimal context was created
            assert result_state['clinical_context'] is not None
            assert result_state['clinical_context']['clinical_indication'] == "No clinical indication provided"
            assert 'Limited clinical information' in result_state['clinical_context']['summary']
            assert len(result_state['errors']) == 0
            
            # Verify API was not called (since no info provided)
            mock_client.chat.completions.create.assert_not_called()
