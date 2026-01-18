"""
Unit tests for Agent A: Clinical Context Extraction

Tests cover:
- Agent initialization
- Clinical information extraction
- Output validation
- Error handling
- Edge cases (missing data, empty inputs)
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.agents.agent_a_context import ClinicalContextAgent


class TestClinicalContextAgent:
    """Test suite for ClinicalContextAgent."""
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly with API key."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            assert agent.agent_name == 'agent_a_context'
            assert agent.model == 'gpt-4o'
            assert agent.temperature == 0.1
            assert agent.client is not None
    
    def test_agent_initialization_with_config(self):
        """Test agent initialization with custom config."""
        config = {
            'api_key': 'custom-key',
            'model': 'gpt-4',
            'temperature': 0.2
        }
        agent = ClinicalContextAgent(config=config)
        
        assert agent.model == 'gpt-4'
        assert agent.temperature == 0.2
    
    def test_agent_initialization_no_api_key(self):
        """Test that agent raises error when no API key is provided."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                ClinicalContextAgent()
    
    def test_get_prompt_template(self):
        """Test that prompt template is returned correctly."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            prompt = agent.get_prompt_template()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert 'clinical context' in prompt.lower()
            assert 'JSON' in prompt
    
    def test_combine_clinical_info_all_fields(self):
        """Test combining clinical information with all fields present."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            combined = agent._combine_clinical_info(
                patient_history="History of hypertension",
                clinical_indication="Abdominal pain",
                lab_results="ALT: 45 U/L, AST: 38 U/L",
                clinical_history="Chronic liver disease",
                indication="Rule out hepatic lesion"
            )
            
            assert "History of hypertension" in combined
            assert "Abdominal pain" in combined
            assert "ALT: 45 U/L" in combined
            assert "Chronic liver disease" in combined
    
    def test_combine_clinical_info_partial_fields(self):
        """Test combining clinical information with some fields missing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            combined = agent._combine_clinical_info(
                patient_history="History of diabetes",
                clinical_indication="",
                lab_results="",
                clinical_history="",
                indication="Screening ultrasound"
            )
            
            assert "History of diabetes" in combined
            assert "Screening ultrasound" in combined
            assert len(combined.split('\n\n')) == 2  # Only 2 sections
    
    def test_combine_clinical_info_empty(self):
        """Test combining clinical information when all fields are empty."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            combined = agent._combine_clinical_info(
                patient_history="",
                clinical_indication="",
                lab_results="",
                clinical_history="",
                indication=""
            )
            
            assert combined == ""
    
    def test_create_minimal_context(self):
        """Test creation of minimal context when no information is provided."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            minimal = agent._create_minimal_context()
            
            assert minimal['relevant_history'] is None
            assert minimal['clinical_indication'] == "No clinical indication provided"
            assert minimal['pertinent_labs'] == {}
            assert minimal['risk_factors'] == []
            assert minimal['clinical_questions'] == []
            assert 'Limited clinical information' in minimal['summary']
    
    def test_validate_output_valid(self):
        """Test validation of valid output."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            valid_output = {
                'relevant_history': 'History of hypertension',
                'clinical_indication': 'Abdominal pain',
                'pertinent_labs': {'ALT': '45 U/L'},
                'risk_factors': ['Hypertension', 'Age > 50'],
                'clinical_questions': ['Rule out hepatic lesion'],
                'summary': 'Patient with abdominal pain and history of hypertension'
            }
            
            assert agent.validate_output(valid_output) is True
    
    def test_validate_output_missing_key(self):
        """Test validation fails when required key is missing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            invalid_output = {
                'relevant_history': 'History of hypertension',
                'clinical_indication': 'Abdominal pain',
                'pertinent_labs': {},
                'risk_factors': [],
                # Missing 'clinical_questions' and 'summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_wrong_type(self):
        """Test validation fails when field has wrong type."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            invalid_output = {
                'relevant_history': 'History of hypertension',
                'clinical_indication': 'Abdominal pain',
                'pertinent_labs': 'not a dict',  # Should be dict
                'risk_factors': [],
                'clinical_questions': [],
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_empty_summary(self):
        """Test validation fails when summary is empty."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            invalid_output = {
                'relevant_history': 'History of hypertension',
                'clinical_indication': 'Abdominal pain',
                'pertinent_labs': {},
                'risk_factors': [],
                'clinical_questions': [],
                'summary': ''  # Empty summary
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_not_dict(self):
        """Test validation fails when output is not a dictionary."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            assert agent.validate_output("not a dict") is False
            assert agent.validate_output([]) is False
            assert agent.validate_output(None) is False
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_process_success(self, mock_openai_class):
        """Test successful processing of clinical context."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'relevant_history': 'History of chronic liver disease',
            'clinical_indication': 'Elevated liver enzymes',
            'pertinent_labs': {
                'ALT': '85 U/L (elevated)',
                'AST': '72 U/L (elevated)'
            },
            'risk_factors': ['Chronic liver disease', 'Elevated enzymes'],
            'clinical_questions': ['Assess liver parenchyma', 'Rule out focal lesions'],
            'summary': 'Patient with chronic liver disease presenting with elevated liver enzymes'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'patient_history': 'History of chronic liver disease',
                    'clinical_indication': 'Elevated liver enzymes',
                    'lab_results': 'ALT: 85 U/L, AST: 72 U/L'
                }
            }
            
            result = agent.process(input_data)
            
            assert result['relevant_history'] == 'History of chronic liver disease'
            assert result['clinical_indication'] == 'Elevated liver enzymes'
            assert 'ALT' in result['pertinent_labs']
            assert len(result['risk_factors']) > 0
            assert len(result['clinical_questions']) > 0
            assert result['summary'] is not None
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_process_no_clinical_info(self, mock_openai_class):
        """Test processing when no clinical information is provided."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'patient_history': '',
                    'clinical_indication': '',
                    'lab_results': ''
                }
            }
            
            result = agent.process(input_data)
            
            # Should return minimal context without calling API
            assert result['clinical_indication'] == "No clinical indication provided"
            assert result['pertinent_labs'] == {}
            assert 'Limited clinical information' in result['summary']
            
            # Verify API was not called
            mock_client.chat.completions.create.assert_not_called()
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_process_api_error(self, mock_openai_class):
        """Test handling of API errors."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'patient_history': 'Test history',
                    'clinical_indication': 'Test indication'
                }
            }
            
            with pytest.raises(Exception, match="Failed to extract clinical context"):
                agent.process(input_data)
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_process_invalid_json_response(self, mock_openai_class):
        """Test handling of invalid JSON response from API."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Not valid JSON"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'patient_history': 'Test history',
                    'clinical_indication': 'Test indication'
                }
            }
            
            with pytest.raises(ValueError, match="Invalid JSON response"):
                agent.process(input_data)
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_execute_success(self, mock_openai_class):
        """Test successful execution through base agent execute method."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'relevant_history': 'Test history',
            'clinical_indication': 'Test indication',
            'pertinent_labs': {},
            'risk_factors': [],
            'clinical_questions': [],
            'summary': 'Test summary'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'patient_history': 'Test history',
                    'clinical_indication': 'Test indication'
                }
            }
            
            result = agent.execute(input_data)
            
            assert result['success'] is True
            assert result['output'] is not None
            assert result['error'] is None
            assert result['execution_time_ms'] >= 0
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_execute_failure(self, mock_openai_class):
        """Test execution failure through base agent execute method."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'patient_history': 'Test history',
                    'clinical_indication': 'Test indication'
                }
            }
            
            result = agent.execute(input_data)
            
            assert result['success'] is False
            assert result['output'] is None
            assert result['error'] is not None
            assert 'Failed to extract clinical context' in result['error']
