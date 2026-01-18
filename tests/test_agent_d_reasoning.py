"""
Unit tests for Agent D: Diagnostic Reasoning

Tests the diagnostic reasoning agent's ability to generate differential
diagnoses from clinical context and imaging findings.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.agents.agent_d_reasoning import DiagnosticReasoningAgent


class TestDiagnosticReasoningAgent:
    """Test suite for DiagnosticReasoningAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create a DiagnosticReasoningAgent instance for testing"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-api-key'}):
            with patch('app.agents.agent_d_reasoning.OpenAI'):
                config = {
                    'api_key': 'test-api-key',
                    'model': 'gpt-4o',
                    'temperature': 0.2
                }
                return DiagnosticReasoningAgent(config=config)
    
    @pytest.fixture
    def sample_clinical_context(self):
        """Sample clinical context from Agent A"""
        return {
            "relevant_history": "History of chronic hepatitis B infection",
            "clinical_indication": "Elevated liver enzymes, right upper quadrant pain",
            "pertinent_labs": {
                "ALT": "120 U/L (elevated)",
                "AST": "95 U/L (elevated)",
                "Bilirubin": "1.8 mg/dL (mildly elevated)"
            },
            "risk_factors": ["Chronic hepatitis B", "Age 55", "Male"],
            "clinical_questions": [
                "Assess for cirrhosis",
                "Evaluate for focal liver lesions"
            ],
            "summary": "Patient with chronic hepatitis B presenting with elevated liver enzymes"
        }
    
    @pytest.fixture
    def sample_findings_cirrhosis(self):
        """Sample findings suggesting cirrhosis"""
        return {
            "organ_assessment": {
                "size": "Normal to slightly small, measuring 14 cm in length",
                "echogenicity": "Increased, heterogeneous",
                "echotexture": "Coarse",
                "surface": "Nodular contour"
            },
            "focal_lesions": [],
            "vascular_findings": {
                "portal_vein": "Dilated, measuring 14 mm in diameter",
                "hepatic_veins": "Patent but attenuated",
                "abnormalities": ["Portal vein dilation"]
            },
            "biliary_system": {
                "intrahepatic_ducts": "Normal, not dilated",
                "common_bile_duct": "Normal caliber, 5 mm",
                "abnormalities": []
            },
            "additional_findings": {
                "ascites": "Present, small amount of perihepatic ascites",
                "other": ["Splenomegaly"]
            },
            "measurements": {
                "liver_length": "14 cm",
                "portal_vein_diameter": "14 mm",
                "spleen_length": "14 cm"
            },
            "confidence_assessment": {
                "overall_confidence": 0.85,
                "limitations": []
            },
            "summary": "Coarse, heterogeneous liver with nodular surface, portal vein dilation, and ascites"
        }
    
    @pytest.fixture
    def sample_findings_focal_lesion(self):
        """Sample findings with focal lesion"""
        return {
            "organ_assessment": {
                "size": "Normal, measuring 15 cm in length",
                "echogenicity": "Normal",
                "echotexture": "Homogeneous",
                "surface": "Smooth"
            },
            "focal_lesions": [
                {
                    "location": "Right hepatic lobe, segment 7",
                    "size": "2.3 x 2.1 cm",
                    "echogenicity": "Hyperechoic",
                    "margins": "Well-defined",
                    "characteristics": "Solid",
                    "posterior_acoustic": "Enhancement",
                    "description": "Well-circumscribed hyperechoic lesion with posterior acoustic enhancement"
                }
            ],
            "vascular_findings": {
                "portal_vein": "Normal caliber and flow",
                "hepatic_veins": "Patent",
                "abnormalities": []
            },
            "biliary_system": {
                "intrahepatic_ducts": "Normal",
                "common_bile_duct": "Normal, 4 mm",
                "abnormalities": []
            },
            "additional_findings": {
                "ascites": "Absent",
                "other": []
            },
            "measurements": {
                "liver_length": "15 cm",
                "lesion_size": "2.3 x 2.1 cm"
            },
            "confidence_assessment": {
                "overall_confidence": 0.9,
                "limitations": []
            },
            "summary": "2.3 cm hyperechoic lesion in right hepatic lobe with posterior enhancement"
        }
    
    @pytest.fixture
    def sample_reasoning_output(self):
        """Sample valid diagnostic reasoning output"""
        return {
            "differential_diagnosis": [
                {
                    "diagnosis": "Hepatic cirrhosis",
                    "likelihood": "high",
                    "supporting_findings": [
                        "Coarse, heterogeneous echotexture",
                        "Nodular surface contour",
                        "Portal vein dilation (14 mm)",
                        "Ascites",
                        "Splenomegaly"
                    ],
                    "contradicting_findings": [],
                    "reasoning": "The combination of coarse echotexture, nodular surface, portal hypertension signs (dilated portal vein, ascites, splenomegaly), and history of chronic hepatitis B strongly suggests cirrhosis.",
                    "clinical_significance": "High significance - cirrhosis is a chronic condition requiring ongoing monitoring and management"
                },
                {
                    "diagnosis": "Portal hypertension",
                    "likelihood": "high",
                    "supporting_findings": [
                        "Portal vein dilation",
                        "Ascites",
                        "Splenomegaly"
                    ],
                    "contradicting_findings": [],
                    "reasoning": "Portal hypertension is evident from the dilated portal vein, ascites, and splenomegaly, likely secondary to cirrhosis.",
                    "clinical_significance": "High significance - may lead to complications such as variceal bleeding"
                }
            ],
            "primary_diagnosis": "Hepatic cirrhosis with portal hypertension",
            "key_findings_summary": [
                "Coarse, nodular liver",
                "Portal vein dilation (14 mm)",
                "Ascites",
                "Splenomegaly"
            ],
            "clinical_correlation": "Findings correlate well with clinical presentation of elevated liver enzymes and chronic hepatitis B infection",
            "recommendations": {
                "follow_up_imaging": [
                    "Consider CT or MRI for further characterization",
                    "Surveillance imaging every 6 months for hepatocellular carcinoma screening"
                ],
                "clinical_follow_up": [
                    "Hepatology consultation",
                    "Endoscopy for variceal screening"
                ],
                "additional_workup": [
                    "Alpha-fetoprotein level",
                    "Complete hepatitis panel"
                ]
            },
            "confidence_assessment": {
                "diagnostic_confidence": 0.85,
                "factors_affecting_confidence": [
                    "Classic imaging features present",
                    "Strong clinical correlation"
                ]
            },
            "summary": "Imaging findings are consistent with hepatic cirrhosis and portal hypertension in the setting of chronic hepatitis B infection"
        }
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.agent_name == 'agent_d_reasoning'
        assert agent.model == 'gpt-4o'
        assert agent.temperature == 0.2
    
    def test_agent_initialization_without_api_key(self):
        """Test agent raises error without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                DiagnosticReasoningAgent(config={})
    
    def test_get_prompt_template(self, agent):
        """Test prompt template is returned"""
        prompt = agent.get_prompt_template()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "differential diagnosis" in prompt.lower()
        assert "reasoning" in prompt.lower()
        assert "json" in prompt.lower()
    
    def test_format_reasoning_input(self, agent, sample_clinical_context, sample_findings_cirrhosis):
        """Test formatting of reasoning input"""
        formatted = agent._format_reasoning_input(sample_clinical_context, sample_findings_cirrhosis)
        
        assert isinstance(formatted, str)
        assert "CLINICAL CONTEXT" in formatted
        assert "IMAGING FINDINGS" in formatted
        assert "hepatitis" in formatted.lower()
        assert "coarse" in formatted.lower()
        assert "nodular" in formatted.lower()
    
    def test_format_reasoning_input_with_focal_lesion(
        self,
        agent,
        sample_clinical_context,
        sample_findings_focal_lesion
    ):
        """Test formatting includes focal lesion details"""
        formatted = agent._format_reasoning_input(
            sample_clinical_context,
            sample_findings_focal_lesion
        )
        
        assert "Focal Lesions" in formatted
        assert "2.3 x 2.1 cm" in formatted
        assert "Hyperechoic" in formatted
        assert "segment 7" in formatted
    
    def test_create_minimal_reasoning(self, agent):
        """Test creation of minimal reasoning when no findings available"""
        minimal = agent._create_minimal_reasoning()
        
        assert isinstance(minimal, dict)
        assert 'differential_diagnosis' in minimal
        assert 'primary_diagnosis' in minimal
        assert len(minimal['differential_diagnosis']) > 0
        assert minimal['confidence_assessment']['diagnostic_confidence'] == 0.0
    
    def test_process_with_cirrhosis_findings(
        self,
        agent,
        sample_clinical_context,
        sample_findings_cirrhosis,
        sample_reasoning_output
    ):
        """Test processing with cirrhosis findings"""
        # Mock the agent's client directly
        agent.client = Mock()
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(sample_reasoning_output)
        agent.client.chat.completions.create.return_value = mock_response
        
        # Process input
        input_data = {
            'case_id': 1,
            'clinical_context': sample_clinical_context,
            'findings': sample_findings_cirrhosis
        }
        
        result = agent.process(input_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'differential_diagnosis' in result
        assert 'primary_diagnosis' in result
        assert len(result['differential_diagnosis']) > 0
        
        # Verify API was called
        agent.client.chat.completions.create.assert_called_once()
        call_args = agent.client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4o'
        assert call_args[1]['temperature'] == 0.2
    
    def test_process_with_focal_lesion(
        self,
        agent,
        sample_clinical_context,
        sample_findings_focal_lesion
    ):
        """Test processing with focal lesion findings"""
        # Mock OpenAI response for hemangioma
        hemangioma_reasoning = {
            "differential_diagnosis": [
                {
                    "diagnosis": "Hepatic hemangioma",
                    "likelihood": "high",
                    "supporting_findings": [
                        "Hyperechoic lesion",
                        "Well-defined margins",
                        "Posterior acoustic enhancement"
                    ],
                    "contradicting_findings": [],
                    "reasoning": "Classic appearance of hemangioma with hyperechoic echotexture and posterior enhancement",
                    "clinical_significance": "Benign lesion, typically requires no treatment"
                }
            ],
            "primary_diagnosis": "Hepatic hemangioma",
            "key_findings_summary": ["2.3 cm hyperechoic lesion with enhancement"],
            "clinical_correlation": "Incidental finding, likely benign",
            "recommendations": {
                "follow_up_imaging": ["Consider MRI for definitive characterization if needed"],
                "clinical_follow_up": ["Routine follow-up"],
                "additional_workup": []
            },
            "confidence_assessment": {
                "diagnostic_confidence": 0.8,
                "factors_affecting_confidence": ["Classic imaging features"]
            },
            "summary": "Findings consistent with hepatic hemangioma"
        }
        
        # Mock the agent's client directly
        agent.client = Mock()
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(hemangioma_reasoning)
        agent.client.chat.completions.create.return_value = mock_response
        
        # Process input
        input_data = {
            'case_id': 2,
            'clinical_context': sample_clinical_context,
            'findings': sample_findings_focal_lesion
        }
        
        result = agent.process(input_data)
        
        # Verify hemangioma diagnosis
        assert result['primary_diagnosis'] == "Hepatic hemangioma"
        assert any('hemangioma' in d['diagnosis'].lower() 
                  for d in result['differential_diagnosis'])
    
    def test_process_without_findings(self, agent, sample_clinical_context):
        """Test processing without findings returns minimal reasoning"""
        input_data = {
            'case_id': 3,
            'clinical_context': sample_clinical_context,
            'findings': {}
        }
        
        result = agent.process(input_data)
        
        assert isinstance(result, dict)
        assert result['confidence_assessment']['diagnostic_confidence'] == 0.0
        assert "Insufficient information" in result['primary_diagnosis']
    
    def test_process_api_error(self, agent, sample_clinical_context, sample_findings_cirrhosis):
        """Test handling of API errors"""
        agent.client = Mock()
        agent.client.chat.completions.create.side_effect = Exception("API Error")
        
        input_data = {
            'case_id': 4,
            'clinical_context': sample_clinical_context,
            'findings': sample_findings_cirrhosis
        }
        
        with pytest.raises(Exception, match="Failed to generate diagnostic reasoning"):
            agent.process(input_data)
    
    def test_process_invalid_json_response(
        self,
        agent,
        sample_clinical_context,
        sample_findings_cirrhosis
    ):
        """Test handling of invalid JSON response"""
        agent.client = Mock()
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        agent.client.chat.completions.create.return_value = mock_response
        
        input_data = {
            'case_id': 5,
            'clinical_context': sample_clinical_context,
            'findings': sample_findings_cirrhosis
        }
        
        with pytest.raises(ValueError, match="Invalid JSON response"):
            agent.process(input_data)
    
    def test_validate_output_valid(self, agent, sample_reasoning_output):
        """Test validation of valid output"""
        assert agent.validate_output(sample_reasoning_output) is True
    
    def test_validate_output_not_dict(self, agent):
        """Test validation fails for non-dictionary"""
        assert agent.validate_output("not a dict") is False
        assert agent.validate_output([]) is False
    
    def test_validate_output_missing_keys(self, agent, sample_reasoning_output):
        """Test validation fails for missing required keys"""
        incomplete = sample_reasoning_output.copy()
        del incomplete['primary_diagnosis']
        assert agent.validate_output(incomplete) is False
    
    def test_validate_output_invalid_differential_diagnosis(self, agent, sample_reasoning_output):
        """Test validation fails for invalid differential_diagnosis"""
        invalid = sample_reasoning_output.copy()
        invalid['differential_diagnosis'] = "not a list"
        assert agent.validate_output(invalid) is False
        
        invalid['differential_diagnosis'] = []
        assert agent.validate_output(invalid) is False
    
    def test_validate_output_invalid_diagnosis_entry(self, agent, sample_reasoning_output):
        """Test validation fails for invalid diagnosis entry"""
        invalid = sample_reasoning_output.copy()
        invalid['differential_diagnosis'] = [
            {
                "diagnosis": "Test",
                # Missing required keys
            }
        ]
        assert agent.validate_output(invalid) is False
    
    def test_validate_output_invalid_confidence(self, agent, sample_reasoning_output):
        """Test validation fails for invalid confidence value"""
        invalid = sample_reasoning_output.copy()
        invalid['confidence_assessment']['diagnostic_confidence'] = 1.5
        assert agent.validate_output(invalid) is False
        
        invalid['confidence_assessment']['diagnostic_confidence'] = -0.1
        assert agent.validate_output(invalid) is False
        
        invalid['confidence_assessment']['diagnostic_confidence'] = "not a number"
        assert agent.validate_output(invalid) is False
    
    def test_validate_output_missing_summary(self, agent, sample_reasoning_output):
        """Test validation fails for missing or empty summary"""
        invalid = sample_reasoning_output.copy()
        invalid['summary'] = ""
        assert agent.validate_output(invalid) is False
        
        del invalid['summary']
        assert agent.validate_output(invalid) is False
    
    def test_validate_output_invalid_recommendations(self, agent, sample_reasoning_output):
        """Test validation fails for invalid recommendations structure"""
        invalid = sample_reasoning_output.copy()
        invalid['recommendations'] = "not a dict"
        assert agent.validate_output(invalid) is False
        
        invalid['recommendations'] = {}
        assert agent.validate_output(invalid) is False
        
        invalid['recommendations'] = {
            'follow_up_imaging': "not a list"
        }
        assert agent.validate_output(invalid) is False
    
    def test_execute_method(self, agent, sample_clinical_context, sample_findings_cirrhosis, sample_reasoning_output):
        """Test execute method with timing and error handling"""
        agent.client = Mock()
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(sample_reasoning_output)
        agent.client.chat.completions.create.return_value = mock_response
        
        input_data = {
            'case_id': 6,
            'clinical_context': sample_clinical_context,
            'findings': sample_findings_cirrhosis
        }
        
        result = agent.execute(input_data)
        
        assert result['success'] is True
        assert result['output'] is not None
        assert result['error'] is None
        assert 'execution_time_ms' in result
        assert isinstance(result['execution_time_ms'], int)
    
    def test_execute_method_with_error(self, agent, sample_clinical_context, sample_findings_cirrhosis):
        """Test execute method handles errors gracefully"""
        agent.client = Mock()
        agent.client.chat.completions.create.side_effect = Exception("API Error")
        
        input_data = {
            'case_id': 7,
            'clinical_context': sample_clinical_context,
            'findings': sample_findings_cirrhosis
        }
        
        result = agent.execute(input_data)
        
        assert result['success'] is False
        assert result['output'] is None
        assert result['error'] is not None
        assert 'execution_time_ms' in result
