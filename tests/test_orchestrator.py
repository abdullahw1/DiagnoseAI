"""
Unit tests for the LangGraph orchestrator and agent pipeline.

Tests cover:
- Agent registration
- Graph building
- State management
- Agent execution flow
- Error handling and retry logic
- Audit logging
- Report storage
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from app.agents.orchestrator import AgentOrchestrator, AgentState
from app.agents.base_agent import BaseAgent
from app.models import Case, AgentOutput, Report, Patient, User


class MockAgent(BaseAgent):
    """Mock agent for testing purposes."""
    
    def __init__(self, agent_name, should_fail=False, output_data=None):
        super().__init__(agent_name)
        self.should_fail = should_fail
        self.output_data = output_data or {'result': f'{agent_name}_output'}
    
    def process(self, input_data):
        """Mock process method."""
        if self.should_fail:
            raise Exception(f"Mock error in {self.agent_name}")
        return self.output_data
    
    def validate_output(self, output):
        """Mock validation - always returns True unless output is None."""
        return output is not None


class TestAgentOrchestrator:
    """Test suite for AgentOrchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test that orchestrator initializes correctly."""
        orchestrator = AgentOrchestrator()
        
        assert orchestrator.agents == {}
        assert orchestrator.graph is None
        assert orchestrator.logger is not None
    
    def test_orchestrator_initialization_with_agents(self):
        """Test orchestrator initialization with pre-registered agents."""
        agents = {
            'agent_a': MockAgent('agent_a'),
            'agent_b': MockAgent('agent_b')
        }
        orchestrator = AgentOrchestrator(agents=agents)
        
        assert len(orchestrator.agents) == 2
        assert 'agent_a' in orchestrator.agents
        assert 'agent_b' in orchestrator.agents
    
    def test_register_agent(self):
        """Test agent registration."""
        orchestrator = AgentOrchestrator()
        agent = MockAgent('test_agent')
        
        orchestrator.register_agent('test_agent', agent)
        
        assert 'test_agent' in orchestrator.agents
        assert orchestrator.agents['test_agent'] == agent
    
    def test_build_graph(self):
        """Test that the agent pipeline graph is built correctly."""
        orchestrator = AgentOrchestrator()
        
        # Register all required agents
        for agent_name in ['agent_a', 'agent_b', 'agent_c', 'agent_d', 'agent_e', 'agent_f']:
            orchestrator.register_agent(agent_name, MockAgent(agent_name))
        
        graph = orchestrator.build_graph()
        
        assert graph is not None
        assert orchestrator.graph is not None
    
    def test_prepare_agent_input_agent_a(self):
        """Test input preparation for Agent A."""
        orchestrator = AgentOrchestrator()
        state = {
            'case_id': 1,
            'case_data': {'test': 'data'},
            'clinical_context': None,
            'quality_assessment': None,
            'findings': None,
            'diagnostic_reasoning': None,
            'draft_report': None,
            'safety_validation': None,
            'errors': [],
            'execution_log': []
        }
        
        input_data = orchestrator._prepare_agent_input('agent_a', state)
        
        assert input_data['case_id'] == 1
        assert input_data['case_data'] == {'test': 'data'}
        assert 'clinical_context' not in input_data
    
    def test_prepare_agent_input_agent_c(self):
        """Test input preparation for Agent C with clinical context."""
        orchestrator = AgentOrchestrator()
        state = {
            'case_id': 1,
            'case_data': {'test': 'data'},
            'clinical_context': {'context': 'clinical_data'},
            'quality_assessment': None,
            'findings': None,
            'diagnostic_reasoning': None,
            'draft_report': None,
            'safety_validation': None,
            'errors': [],
            'execution_log': []
        }
        
        input_data = orchestrator._prepare_agent_input('agent_c', state)
        
        assert input_data['case_id'] == 1
        assert input_data['clinical_context'] == {'context': 'clinical_data'}
    
    def test_prepare_agent_input_agent_e(self):
        """Test input preparation for Agent E with all previous outputs."""
        orchestrator = AgentOrchestrator()
        state = {
            'case_id': 1,
            'case_data': {'test': 'data'},
            'clinical_context': {'context': 'data'},
            'quality_assessment': {'quality': 'data'},
            'findings': {'findings': 'data'},
            'diagnostic_reasoning': {'reasoning': 'data'},
            'draft_report': None,
            'safety_validation': None,
            'errors': [],
            'execution_log': []
        }
        
        input_data = orchestrator._prepare_agent_input('agent_e', state)
        
        assert 'clinical_context' in input_data
        assert 'quality_assessment' in input_data
        assert 'findings' in input_data
        assert 'diagnostic_reasoning' in input_data
    
    def test_execute_agent_success(self, app):
        """Test successful agent execution."""
        with app.app_context():
            orchestrator = AgentOrchestrator()
            agent = MockAgent('test_agent', output_data={'test': 'output'})
            orchestrator.register_agent('test_agent', agent)
            
            state = {
                'case_id': 1,
                'case_data': {'test': 'data'},
                'clinical_context': None,
                'quality_assessment': None,
                'findings': None,
                'diagnostic_reasoning': None,
                'draft_report': None,
                'safety_validation': None,
                'errors': [],
                'execution_log': []
            }
            
            # Mock the database logging
            with patch.object(orchestrator, '_log_agent_execution'):
                result_state = orchestrator._execute_agent('test_agent', state, 'test_output')
            
            assert result_state['test_output'] == {'test': 'output'}
            assert len(result_state['errors']) == 0
            assert len(result_state['execution_log']) == 1
            assert result_state['execution_log'][0]['agent'] == 'test_agent'
            assert result_state['execution_log'][0]['success'] is True
    
    def test_execute_agent_failure(self, app):
        """Test agent execution with failure."""
        with app.app_context():
            orchestrator = AgentOrchestrator()
            agent = MockAgent('test_agent', should_fail=True)
            orchestrator.register_agent('test_agent', agent)
            
            state = {
                'case_id': 1,
                'case_data': {'test': 'data'},
                'clinical_context': None,
                'quality_assessment': None,
                'findings': None,
                'diagnostic_reasoning': None,
                'draft_report': None,
                'safety_validation': None,
                'errors': [],
                'execution_log': []
            }
            
            # Mock the database logging
            with patch.object(orchestrator, '_log_agent_execution'):
                result_state = orchestrator._execute_agent('test_agent', state, 'test_output')
            
            assert 'test_output' not in result_state or result_state['test_output'] is None
            assert len(result_state['errors']) > 0
            assert 'test_agent' in result_state['errors'][0]
    
    def test_execute_agent_not_registered(self, app):
        """Test execution of unregistered agent."""
        with app.app_context():
            orchestrator = AgentOrchestrator()
            
            state = {
                'case_id': 1,
                'case_data': {'test': 'data'},
                'clinical_context': None,
                'quality_assessment': None,
                'findings': None,
                'diagnostic_reasoning': None,
                'draft_report': None,
                'safety_validation': None,
                'errors': [],
                'execution_log': []
            }
            
            result_state = orchestrator._execute_agent('nonexistent_agent', state, 'test_output')
            
            assert len(result_state['errors']) > 0
            assert 'not registered' in result_state['errors'][0]
    
    def test_log_agent_execution(self, app):
        """Test that agent execution is logged to database."""
        with app.app_context():
            orchestrator = AgentOrchestrator()
            
            # Create a test case
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
                status='pending'
            )
            db.session.add(case)
            db.session.commit()
            
            # Log an agent execution
            orchestrator._log_agent_execution(
                case_id=case.id,
                agent_name='test_agent',
                input_data={'test': 'input'},
                result={
                    'success': True,
                    'output': {'test': 'output'},
                    'execution_time_ms': 100
                }
            )
            
            # Verify the log was created
            agent_output = AgentOutput.query.filter_by(
                case_id=case.id,
                agent_name='test_agent'
            ).first()
            
            assert agent_output is not None
            assert agent_output.input_data == {'test': 'input'}
            assert agent_output.output_data == {'test': 'output'}
            assert agent_output.execution_time_ms == 100
            assert agent_output.error_message is None
    
    def test_log_agent_execution_with_error(self, app):
        """Test logging of failed agent execution."""
        with app.app_context():
            orchestrator = AgentOrchestrator()
            
            # Create a test case
            user = User(username='testuser2', email='test2@example.com')
            user.set_password('password')
            from app import db
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                patient_id='P002',
                first_name='Test',
                last_name='Patient',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            case = Case(
                case_number='C002',
                user_id=user.id,
                patient_id=patient.id,
                status='pending'
            )
            db.session.add(case)
            db.session.commit()
            
            # Log a failed agent execution
            orchestrator._log_agent_execution(
                case_id=case.id,
                agent_name='test_agent',
                input_data={'test': 'input'},
                result={
                    'success': False,
                    'output': None,
                    'error': 'Test error message',
                    'execution_time_ms': 50
                }
            )
            
            # Verify the error was logged
            agent_output = AgentOutput.query.filter_by(
                case_id=case.id,
                agent_name='test_agent'
            ).first()
            
            assert agent_output is not None
            assert agent_output.error_message == 'Test error message'
            assert agent_output.output_data is None
    
    def test_store_report(self, app):
        """Test storing the final report in database."""
        with app.app_context():
            orchestrator = AgentOrchestrator()
            
            # Create a test case
            user = User(username='testuser3', email='test3@example.com')
            user.set_password('password')
            from app import db
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                patient_id='P003',
                first_name='Test',
                last_name='Patient',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            case = Case(
                case_number='C003',
                user_id=user.id,
                patient_id=patient.id,
                status='pending'
            )
            db.session.add(case)
            db.session.commit()
            
            # Create final state
            final_state = {
                'case_id': case.id,
                'case_data': {},
                'clinical_context': {'context': 'data'},
                'quality_assessment': {'quality': 'good'},
                'findings': {'findings': 'test'},
                'diagnostic_reasoning': {'reasoning': 'test'},
                'draft_report': {'report_text': 'Test report'},
                'safety_validation': {
                    'confidence_score': 0.85,
                    'safety_flags': {'critical': False}
                },
                'errors': [],
                'execution_log': []
            }
            
            # Store the report
            report_id = orchestrator._store_report(case.id, final_state)
            
            assert report_id is not None
            
            # Verify the report was created
            report = Report.query.get(report_id)
            assert report is not None
            assert report.case_id == case.id
            assert report.draft_text == 'Test report'
            assert report.confidence_score == 0.85
            assert report.is_finalized is False
    
    def test_handle_agent_error_with_retry(self):
        """Test error handling with retry logic."""
        orchestrator = AgentOrchestrator()
        error = Exception("Test error")
        
        result = orchestrator.handle_agent_error(
            agent_name='test_agent',
            error=error,
            retry_count=0,
            max_retries=3
        )
        
        assert result['should_retry'] is True
        assert result['retry_count'] == 1
        assert 'Test error' in result['error_message']
    
    def test_handle_agent_error_max_retries(self):
        """Test error handling when max retries exceeded."""
        orchestrator = AgentOrchestrator()
        error = Exception("Test error")
        
        result = orchestrator.handle_agent_error(
            agent_name='test_agent',
            error=error,
            retry_count=3,
            max_retries=3
        )
        
        assert result['should_retry'] is False
        assert result['retry_count'] == 3
        assert 'Max retries exceeded' in result['error_message']
    
    def test_orchestrate_analysis_case_not_found(self, app):
        """Test orchestration with non-existent case."""
        with app.app_context():
            orchestrator = AgentOrchestrator()
            
            result = orchestrator.orchestrate_analysis(case_id=99999)
            
            assert result['success'] is False
            assert result['report_id'] is None
            assert len(result['errors']) > 0
            assert 'not found' in result['errors'][0].lower()
    
    def test_orchestrate_analysis_success(self, app):
        """Test successful orchestration of complete pipeline."""
        with app.app_context():
            # Create test data
            user = User(username='testuser4', email='test4@example.com')
            user.set_password('password')
            from app import db
            db.session.add(user)
            db.session.commit()
            
            patient = Patient(
                patient_id='P004',
                first_name='Test',
                last_name='Patient',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.commit()
            
            case = Case(
                case_number='C004',
                user_id=user.id,
                patient_id=patient.id,
                status='pending',
                patient_history='Test history',
                clinical_indication='Test indication'
            )
            db.session.add(case)
            db.session.commit()
            
            # Create orchestrator with mock agents
            orchestrator = AgentOrchestrator()
            for agent_name in ['agent_a', 'agent_b', 'agent_c', 'agent_d', 'agent_e', 'agent_f']:
                output_data = {'result': f'{agent_name}_output'}
                if agent_name == 'agent_e':
                    output_data = {'report_text': 'Generated report'}
                elif agent_name == 'agent_f':
                    output_data = {
                        'confidence_score': 0.9,
                        'safety_flags': {'critical': False}
                    }
                orchestrator.register_agent(agent_name, MockAgent(agent_name, output_data=output_data))
            
            # Execute orchestration
            result = orchestrator.orchestrate_analysis(case.id)
            
            assert result['success'] is True
            assert result['report_id'] is not None
            assert len(result['errors']) == 0
            
            # Verify case status updated
            db.session.refresh(case)
            assert case.status == 'analysis_complete'
            
            # Verify report was created
            report = Report.query.get(result['report_id'])
            assert report is not None
            assert report.case_id == case.id


class TestAgentState:
    """Test suite for AgentState TypedDict."""
    
    def test_agent_state_structure(self):
        """Test that AgentState has the correct structure."""
        state: AgentState = {
            'case_id': 1,
            'case_data': {},
            'clinical_context': None,
            'quality_assessment': None,
            'findings': None,
            'diagnostic_reasoning': None,
            'draft_report': None,
            'safety_validation': None,
            'errors': [],
            'execution_log': []
        }
        
        assert 'case_id' in state
        assert 'case_data' in state
        assert 'errors' in state
        assert 'execution_log' in state
        assert isinstance(state['errors'], list)
        assert isinstance(state['execution_log'], list)
