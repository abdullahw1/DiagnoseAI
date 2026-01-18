"""
Unit tests for Agent E: Structured Report Drafting

Tests the report drafting agent's ability to synthesize all previous agent
outputs into a complete, professional radiology report.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.agents.agent_e_report import ReportDraftingAgent


class TestReportDraftingAgent:
    """Test suite for ReportDraftingAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create a ReportDraftingAgent instance for testing"""
        config = {
            'api_key': 'test-api-key',
            'model': 'gpt-4o',
            'temperature': 0.3
        }
        return ReportDraftingAgent(config=config)
    
    @pytest.fixture
    def sample_clinical_context(self):
        """Sample clinical context from Agent A"""
        return {
            "clinical_indication": "Elevated liver enzymes, rule out hepatic pathology",
            "relevant_history": "Patient with history of chronic hepatitis C, now with rising ALT/AST",
            "pertinent_labs": {
                "ALT": "120 U/L (elevated)",
                "AST": "95 U/L (elevated)",
                "Bilirubin": "1.2 mg/dL (normal)"
            },
            "risk_factors": ["Chronic hepatitis C", "Alcohol use"],
            "clinical_questions": ["Assess for cirrhosis", "Evaluate for focal lesions"]
        }
    
    @pytest.fixture
    def sample_quality_assessment(self):
        """Sample quality assessment from Agent B"""
        return {
            "overall_quality": "good",
            "image_views": [
                {
                    "anatomical_view": "Right lobe longitudinal",
                    "quality_score": 8.5,
                    "technical_adequacy": "adequate"
                },
                {
                    "anatomical_view": "Left lobe",
                    "quality_score": 7.0,
                    "technical_adequacy": "adequate"
                }
            ],
            "technical_factors": {
                "penetration": "adequate",
                "resolution": "good",
                "artifacts": "minimal"
            },
            "limitations": ["Limited visualization of posterior segments"]
        }
    
    @pytest.fixture
    def sample_findings(self):
        """Sample findings from Agent C"""
        return {
            "organ_assessment": {
                "size": "Normal, measuring 15 cm in length",
                "echogenicity": "Increased, coarse echotexture",
                "echotexture": "Coarse, heterogeneous",
                "surface": "Nodular contour"
            },
            "focal_lesions": [
                {
                    "location": "Right lobe, segment 7",
                    "size": "2.3 x 2.1 cm",
                    "echogenicity": "Hypoechoic",
                    "margins": "Well-defined",
                    "characteristics": "Solid",
                    "posterior_acoustic": "None",
                    "description": "Well-circumscribed hypoechoic lesion"
                }
            ],
            "vascular_findings": {
                "portal_vein": "Patent, diameter 12 mm",
                "hepatic_veins": "Patent",
                "abnormalities": []
            },
            "biliary_system": {
                "intrahepatic_ducts": "Not dilated",
                "common_bile_duct": "Normal, 5 mm",
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
                "overall_confidence": 0.85,
                "limitations": ["Posterior segments not fully visualized"]
            },
            "summary": "Coarse, heterogeneous liver with nodular surface and focal hypoechoic lesion in right lobe"
        }
    
    @pytest.fixture
    def sample_diagnostic_reasoning(self):
        """Sample diagnostic reasoning from Agent D"""
        return {
            "differential_diagnosis": [
                {
                    "diagnosis": "Hepatocellular carcinoma",
                    "likelihood": "moderate",
                    "supporting_findings": ["Focal lesion in cirrhotic liver", "Hepatitis C history"],
                    "contradicting_findings": ["Lesion is hypoechoic rather than hyperechoic"],
                    "reasoning": "Focal lesion in setting of chronic liver disease raises concern for HCC",
                    "clinical_significance": "Requires further characterization with contrast-enhanced imaging"
                },
                {
                    "diagnosis": "Cirrhosis",
                    "likelihood": "high",
                    "supporting_findings": ["Coarse echotexture", "Nodular surface", "Hepatitis C history"],
                    "contradicting_findings": [],
                    "reasoning": "Imaging features consistent with cirrhotic morphology",
                    "clinical_significance": "Established cirrhosis requiring surveillance"
                }
            ],
            "primary_diagnosis": "Cirrhosis with focal hepatic lesion requiring further characterization",
            "key_findings_summary": [
                "Coarse, heterogeneous liver with nodular surface",
                "2.3 cm hypoechoic lesion in right lobe",
                "Patent vasculature"
            ],
            "clinical_correlation": "Imaging findings correlate with clinical history of chronic hepatitis C and elevated liver enzymes",
            "recommendations": {
                "follow_up_imaging": ["MRI liver with contrast for lesion characterization", "Consider CT if MRI contraindicated"],
                "clinical_follow_up": ["Hepatology consultation", "AFP level"],
                "additional_workup": ["Liver biopsy if imaging indeterminate"]
            },
            "confidence_assessment": {
                "diagnostic_confidence": 0.8,
                "factors_affecting_confidence": ["Lesion requires contrast imaging for definitive characterization"]
            },
            "summary": "Cirrhotic liver with focal lesion requiring contrast-enhanced imaging to exclude HCC"
        }
    
    @pytest.fixture
    def sample_complete_input(self, sample_clinical_context, sample_quality_assessment, 
                              sample_findings, sample_diagnostic_reasoning):
        """Complete input data with all agent outputs"""
        return {
            "case_id": 123,
            "clinical_context": sample_clinical_context,
            "quality_assessment": sample_quality_assessment,
            "findings": sample_findings,
            "diagnostic_reasoning": sample_diagnostic_reasoning
        }
    
    @pytest.fixture
    def sample_report_output(self):
        """Sample valid report output"""
        return {
            "report_sections": {
                "clinical_history": "Patient with history of chronic hepatitis C presents with elevated liver enzymes (ALT 120 U/L, AST 95 U/L). Clinical indication is to rule out hepatic pathology and assess for cirrhosis and focal lesions.",
                "technique": "Grayscale ultrasound of the liver was performed. Image quality was good with adequate visualization of most hepatic segments. Limited visualization of posterior segments noted.",
                "findings": "The liver measures 15 cm in length. The liver demonstrates increased echogenicity with coarse, heterogeneous echotexture and nodular surface contour, consistent with cirrhotic morphology.\n\nA well-circumscribed hypoechoic solid lesion measuring 2.3 x 2.1 cm is identified in the right lobe, segment 7. The lesion has well-defined margins without posterior acoustic features.\n\nThe portal vein is patent with diameter of 12 mm. Hepatic veins are patent. No vascular abnormalities identified.\n\nIntrahepatic bile ducts are not dilated. Common bile duct measures 5 mm, within normal limits.\n\nNo ascites is identified.",
                "impression": "1. Cirrhosis: Coarse, heterogeneous liver parenchyma with nodular surface contour consistent with cirrhotic morphology in patient with known chronic hepatitis C.\n\n2. Focal hepatic lesion: 2.3 cm hypoechoic lesion in right lobe (segment 7) requires further characterization. In the setting of cirrhosis, hepatocellular carcinoma cannot be excluded.\n\nRECOMMENDATIONS:\n- MRI liver with contrast for definitive lesion characterization\n- Hepatology consultation\n- AFP level\n- Consider liver biopsy if imaging remains indeterminate"
            },
            "structured_data": {
                "primary_diagnosis": "Cirrhosis with focal hepatic lesion requiring further characterization",
                "secondary_diagnoses": ["Hepatocellular carcinoma (cannot exclude)"],
                "key_findings": [
                    "Coarse, heterogeneous liver with nodular surface",
                    "2.3 cm hypoechoic lesion in right lobe",
                    "Patent vasculature"
                ],
                "recommendations": [
                    "MRI liver with contrast for lesion characterization",
                    "Hepatology consultation",
                    "AFP level"
                ],
                "critical_findings": ["Focal hepatic lesion in cirrhotic liver requiring urgent characterization"]
            },
            "report_metadata": {
                "study_type": "Ultrasound liver",
                "quality_assessment": "good",
                "confidence_level": "moderate",
                "limitations": ["Limited visualization of posterior segments"]
            },
            "full_report_text": "CLINICAL HISTORY\nPatient with history of chronic hepatitis C presents with elevated liver enzymes (ALT 120 U/L, AST 95 U/L). Clinical indication is to rule out hepatic pathology and assess for cirrhosis and focal lesions.\n\nTECHNIQUE\nGrayscale ultrasound of the liver was performed. Image quality was good with adequate visualization of most hepatic segments. Limited visualization of posterior segments noted.\n\nFINDINGS\nThe liver measures 15 cm in length. The liver demonstrates increased echogenicity with coarse, heterogeneous echotexture and nodular surface contour, consistent with cirrhotic morphology.\n\nA well-circumscribed hypoechoic solid lesion measuring 2.3 x 2.1 cm is identified in the right lobe, segment 7. The lesion has well-defined margins without posterior acoustic features.\n\nThe portal vein is patent with diameter of 12 mm. Hepatic veins are patent. No vascular abnormalities identified.\n\nIntrahepatic bile ducts are not dilated. Common bile duct measures 5 mm, within normal limits.\n\nNo ascites is identified.\n\nIMPRESSION\n1. Cirrhosis: Coarse, heterogeneous liver parenchyma with nodular surface contour consistent with cirrhotic morphology in patient with known chronic hepatitis C.\n\n2. Focal hepatic lesion: 2.3 cm hypoechoic lesion in right lobe (segment 7) requires further characterization. In the setting of cirrhosis, hepatocellular carcinoma cannot be excluded.\n\nRECOMMENDATIONS:\n- MRI liver with contrast for definitive lesion characterization\n- Hepatology consultation\n- AFP level\n- Consider liver biopsy if imaging remains indeterminate",
            "summary": "Cirrhotic liver with focal lesion requiring contrast-enhanced imaging to exclude HCC"
        }
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly"""
        assert agent.agent_name == 'agent_e_report'
        assert agent.model == 'gpt-4o'
        assert agent.temperature == 0.3
        assert agent.client is not None
    
    def test_agent_initialization_without_api_key(self):
        """Test that agent raises error without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                ReportDraftingAgent(config={})
    
    def test_get_prompt_template(self, agent):
        """Test that prompt template is returned"""
        prompt = agent.get_prompt_template()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "radiology report" in prompt.lower()
        assert "clinical history" in prompt.lower()
        assert "technique" in prompt.lower()
        assert "findings" in prompt.lower()
        assert "impression" in prompt.lower()
    
    @patch('app.agents.agent_e_report.OpenAI')
    def test_process_with_complete_data(self, mock_openai_class, agent, 
                                       sample_complete_input, sample_report_output):
        """Test report generation with complete agent outputs"""
        # Mock the OpenAI API response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_report_output)
        mock_client.chat.completions.create.return_value = mock_response
        agent.client = mock_client
        
        # Process the input
        result = agent.process(sample_complete_input)
        
        # Verify the result
        assert isinstance(result, dict)
        assert 'report_sections' in result
        assert 'structured_data' in result
        assert 'report_metadata' in result
        assert 'full_report_text' in result
        assert 'summary' in result
        
        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4o'
        assert call_args[1]['temperature'] == 0.3
        assert call_args[1]['response_format'] == {"type": "json_object"}
    
    @patch('app.agents.agent_e_report.OpenAI')
    def test_process_with_minimal_data(self, mock_openai_class, agent):
        """Test report generation with minimal data"""
        minimal_input = {
            "case_id": 123,
            "clinical_context": {},
            "quality_assessment": {},
            "findings": {},
            "diagnostic_reasoning": {}
        }
        
        # Process should return minimal report without calling API
        result = agent.process(minimal_input)
        
        # Verify minimal report structure
        assert isinstance(result, dict)
        assert 'report_sections' in result
        assert 'Insufficient' in result['report_sections']['clinical_history']
        assert result['structured_data']['primary_diagnosis'] == "Insufficient data for diagnosis"
    
    @patch('app.agents.agent_e_report.OpenAI')
    def test_process_api_failure(self, mock_openai_class, agent, sample_complete_input):
        """Test handling of API failures"""
        # Mock API failure
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        agent.client = mock_client
        
        # Process should raise exception
        with pytest.raises(Exception, match="Failed to generate report"):
            agent.process(sample_complete_input)
    
    @patch('app.agents.agent_e_report.OpenAI')
    def test_process_invalid_json_response(self, mock_openai_class, agent, sample_complete_input):
        """Test handling of invalid JSON response"""
        # Mock invalid JSON response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        mock_client.chat.completions.create.return_value = mock_response
        agent.client = mock_client
        
        # Process should raise ValueError
        with pytest.raises(ValueError, match="Invalid JSON response"):
            agent.process(sample_complete_input)
    
    def test_format_report_input(self, agent, sample_clinical_context, 
                                 sample_quality_assessment, sample_findings, 
                                 sample_diagnostic_reasoning):
        """Test formatting of agent outputs for report generation"""
        formatted = agent._format_report_input(
            sample_clinical_context,
            sample_quality_assessment,
            sample_findings,
            sample_diagnostic_reasoning
        )
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        
        # Check that all sections are included
        assert "AGENT A: CLINICAL CONTEXT" in formatted
        assert "AGENT B: QUALITY ASSESSMENT" in formatted
        assert "AGENT C: IMAGING FINDINGS" in formatted
        assert "AGENT D: DIAGNOSTIC REASONING" in formatted
        
        # Check that key data is included
        assert "Elevated liver enzymes" in formatted
        assert "good" in formatted  # quality
        assert "Coarse" in formatted  # findings
        assert "Cirrhosis" in formatted  # diagnosis
    
    def test_format_report_input_with_empty_data(self, agent):
        """Test formatting with empty agent outputs"""
        formatted = agent._format_report_input({}, {}, {}, {})
        
        assert isinstance(formatted, str)
        assert "No clinical context available" in formatted
        assert "No quality assessment available" in formatted
        assert "No findings available" in formatted
        assert "No diagnostic reasoning available" in formatted
    
    def test_create_minimal_report(self, agent):
        """Test creation of minimal report"""
        minimal = agent._create_minimal_report()
        
        assert isinstance(minimal, dict)
        assert 'report_sections' in minimal
        assert 'structured_data' in minimal
        assert 'report_metadata' in minimal
        assert 'full_report_text' in minimal
        assert 'summary' in minimal
        
        # Verify minimal content
        assert "Insufficient" in minimal['report_sections']['clinical_history']
        assert minimal['structured_data']['primary_diagnosis'] == "Insufficient data for diagnosis"
        assert minimal['report_metadata']['quality_assessment'] == "insufficient"
    
    def test_validate_output_valid(self, agent, sample_report_output):
        """Test validation of valid report output"""
        assert agent.validate_output(sample_report_output) is True
    
    def test_validate_output_not_dict(self, agent):
        """Test validation fails for non-dictionary output"""
        assert agent.validate_output("not a dict") is False
        assert agent.validate_output([]) is False
        assert agent.validate_output(None) is False
    
    def test_validate_output_missing_keys(self, agent, sample_report_output):
        """Test validation fails for missing required keys"""
        # Remove required key
        invalid_output = sample_report_output.copy()
        del invalid_output['report_sections']
        assert agent.validate_output(invalid_output) is False
        
        # Remove another key
        invalid_output = sample_report_output.copy()
        del invalid_output['structured_data']
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_missing_report_sections(self, agent, sample_report_output):
        """Test validation fails for missing report sections"""
        invalid_output = sample_report_output.copy()
        del invalid_output['report_sections']['clinical_history']
        assert agent.validate_output(invalid_output) is False
        
        invalid_output = sample_report_output.copy()
        del invalid_output['report_sections']['impression']
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_empty_sections(self, agent, sample_report_output):
        """Test validation fails for empty report sections"""
        invalid_output = sample_report_output.copy()
        invalid_output['report_sections']['findings'] = ""
        assert agent.validate_output(invalid_output) is False
        
        invalid_output = sample_report_output.copy()
        invalid_output['report_sections']['impression'] = "   "
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_invalid_structured_data(self, agent, sample_report_output):
        """Test validation fails for invalid structured data"""
        # primary_diagnosis not a string
        invalid_output = sample_report_output.copy()
        invalid_output['structured_data']['primary_diagnosis'] = 123
        assert agent.validate_output(invalid_output) is False
        
        # key_findings not a list
        invalid_output = sample_report_output.copy()
        invalid_output['structured_data']['key_findings'] = "not a list"
        assert agent.validate_output(invalid_output) is False
        
        # recommendations not a list
        invalid_output = sample_report_output.copy()
        invalid_output['structured_data']['recommendations'] = {}
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_invalid_metadata(self, agent, sample_report_output):
        """Test validation fails for invalid metadata"""
        # Missing metadata key
        invalid_output = sample_report_output.copy()
        del invalid_output['report_metadata']['study_type']
        assert agent.validate_output(invalid_output) is False
        
        # limitations not a list
        invalid_output = sample_report_output.copy()
        invalid_output['report_metadata']['limitations'] = "not a list"
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_empty_full_report_text(self, agent, sample_report_output):
        """Test validation fails for empty full_report_text"""
        invalid_output = sample_report_output.copy()
        invalid_output['full_report_text'] = ""
        assert agent.validate_output(invalid_output) is False
        
        invalid_output = sample_report_output.copy()
        invalid_output['full_report_text'] = "   "
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_empty_summary(self, agent, sample_report_output):
        """Test validation fails for empty summary"""
        invalid_output = sample_report_output.copy()
        invalid_output['summary'] = ""
        assert agent.validate_output(invalid_output) is False
    
    @patch('app.agents.agent_e_report.OpenAI')
    def test_execute_success(self, mock_openai_class, agent, sample_complete_input, 
                            sample_report_output):
        """Test successful execution through execute() method"""
        # Mock the OpenAI API response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_report_output)
        mock_client.chat.completions.create.return_value = mock_response
        agent.client = mock_client
        
        # Execute the agent
        result = agent.execute(sample_complete_input)
        
        # Verify success
        assert result['success'] is True
        assert result['error'] is None
        assert 'output' in result
        assert 'execution_time_ms' in result
        assert result['execution_time_ms'] >= 0
    
    @patch('app.agents.agent_e_report.OpenAI')
    def test_execute_failure(self, mock_openai_class, agent, sample_complete_input):
        """Test failed execution through execute() method"""
        # Mock API failure
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        agent.client = mock_client
        
        # Execute the agent
        result = agent.execute(sample_complete_input)
        
        # Verify failure
        assert result['success'] is False
        assert result['error'] is not None
        assert "API Error" in result['error']
        assert result['output'] is None
        assert 'execution_time_ms' in result
