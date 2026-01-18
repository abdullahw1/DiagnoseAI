"""
Unit tests for Agent F: Safety and Consistency Validation

Tests the safety validation agent's ability to validate complete reports for
consistency, completeness, safety issues, and quality.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.agents.agent_f_safety import SafetyValidationAgent


class TestSafetyValidationAgent:
    """Test suite for SafetyValidationAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create a SafetyValidationAgent instance for testing"""
        config = {
            'api_key': 'test-api-key',
            'model': 'gpt-4o',
            'temperature': 0.1
        }
        return SafetyValidationAgent(config=config)
    
    @pytest.fixture
    def sample_clinical_context(self):
        """Sample clinical context from Agent A"""
        return {
            "clinical_indication": "Elevated liver enzymes, rule out hepatic pathology",
            "relevant_history": "Patient with history of chronic hepatitis C",
            "pertinent_labs": {
                "ALT": "120 U/L (elevated)",
                "AST": "95 U/L (elevated)"
            },
            "risk_factors": ["Chronic hepatitis C"],
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
                }
            ],
            "technical_factors": {
                "penetration": "adequate",
                "resolution": "good"
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
                    "characteristics": "Solid"
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
            "summary": "Coarse liver with focal lesion"
        }
    
    @pytest.fixture
    def sample_diagnostic_reasoning(self):
        """Sample diagnostic reasoning from Agent D"""
        return {
            "differential_diagnosis": [
                {
                    "diagnosis": "Hepatocellular carcinoma",
                    "likelihood": "moderate",
                    "supporting_findings": ["Focal lesion in cirrhotic liver"],
                    "contradicting_findings": [],
                    "reasoning": "Focal lesion in setting of chronic liver disease",
                    "clinical_significance": "Requires further characterization"
                }
            ],
            "primary_diagnosis": "Cirrhosis with focal hepatic lesion",
            "key_findings_summary": ["Coarse liver", "Focal lesion"],
            "clinical_correlation": "Findings correlate with clinical history",
            "recommendations": {
                "follow_up_imaging": ["MRI liver with contrast"],
                "clinical_follow_up": ["Hepatology consultation"],
                "additional_workup": []
            },
            "confidence_assessment": {
                "diagnostic_confidence": 0.8,
                "factors_affecting_confidence": ["Lesion requires contrast imaging"]
            }
        }
    
    @pytest.fixture
    def sample_draft_report(self):
        """Sample draft report from Agent E"""
        return {
            "report_sections": {
                "clinical_history": "Patient with chronic hepatitis C and elevated liver enzymes.",
                "technique": "Grayscale ultrasound of the liver. Image quality was good.",
                "findings": "The liver demonstrates coarse echotexture with nodular surface. A 2.3 cm hypoechoic lesion is seen in the right lobe. Portal vein is patent. No bile duct dilation.",
                "impression": "1. Cirrhosis\n2. Focal hepatic lesion requiring further characterization\n\nRECOMMENDATIONS:\n- MRI liver with contrast\n- Hepatology consultation"
            },
            "structured_data": {
                "primary_diagnosis": "Cirrhosis with focal hepatic lesion",
                "secondary_diagnoses": ["Hepatocellular carcinoma (cannot exclude)"],
                "key_findings": ["Coarse liver", "Focal lesion"],
                "recommendations": ["MRI liver with contrast", "Hepatology consultation"],
                "critical_findings": ["Focal hepatic lesion in cirrhotic liver"]
            },
            "report_metadata": {
                "study_type": "Ultrasound liver",
                "quality_assessment": "good",
                "confidence_level": "moderate",
                "limitations": ["Limited visualization of posterior segments"]
            },
            "full_report_text": "CLINICAL HISTORY\nPatient with chronic hepatitis C and elevated liver enzymes.\n\nTECHNIQUE\nGrayscale ultrasound of the liver. Image quality was good.\n\nFINDINGS\nThe liver demonstrates coarse echotexture with nodular surface. A 2.3 cm hypoechoic lesion is seen in the right lobe. Portal vein is patent. No bile duct dilation.\n\nIMPRESSION\n1. Cirrhosis\n2. Focal hepatic lesion requiring further characterization\n\nRECOMMENDATIONS:\n- MRI liver with contrast\n- Hepatology consultation",
            "summary": "Cirrhotic liver with focal lesion requiring further characterization"
        }
    
    @pytest.fixture
    def sample_complete_input(self, sample_clinical_context, sample_quality_assessment,
                              sample_findings, sample_diagnostic_reasoning, sample_draft_report):
        """Complete input data with all agent outputs"""
        return {
            "case_id": 123,
            "clinical_context": sample_clinical_context,
            "quality_assessment": sample_quality_assessment,
            "findings": sample_findings,
            "diagnostic_reasoning": sample_diagnostic_reasoning,
            "draft_report": sample_draft_report
        }
    
    @pytest.fixture
    def sample_validation_output(self):
        """Sample valid validation output"""
        return {
            "validation_status": "pass",
            "overall_confidence_score": 0.85,
            "consistency_checks": {
                "findings_impression_match": {
                    "status": "pass",
                    "issues": [],
                    "details": "All findings are appropriately reflected in impression"
                },
                "internal_consistency": {
                    "status": "pass",
                    "issues": [],
                    "details": "No contradictions found"
                },
                "clinical_correlation": {
                    "status": "pass",
                    "issues": [],
                    "details": "Findings correlate well with clinical presentation"
                }
            },
            "completeness_checks": {
                "required_sections": {
                    "status": "pass",
                    "missing_sections": [],
                    "details": "All required sections present"
                },
                "findings_coverage": {
                    "status": "pass",
                    "missing_findings": [],
                    "details": "All significant findings addressed"
                },
                "recommendations": {
                    "status": "pass",
                    "issues": [],
                    "details": "Appropriate recommendations provided"
                }
            },
            "safety_flags": {
                "critical_findings": ["Focal hepatic lesion in cirrhotic liver"],
                "urgent_follow_up_needed": True,
                "potential_malignancy": True,
                "safety_issues": [],
                "risk_level": "moderate"
            },
            "quality_assessment": {
                "report_clarity": 0.9,
                "terminology_accuracy": 0.95,
                "organization": 0.9,
                "actionability": 0.85,
                "quality_issues": []
            },
            "confidence_factors": {
                "image_quality_impact": 0.85,
                "diagnostic_certainty": 0.8,
                "data_completeness": 0.9,
                "factors_reducing_confidence": ["Lesion requires contrast imaging for definitive characterization"],
                "factors_increasing_confidence": ["Clear imaging findings", "Consistent with clinical history"]
            },
            "issues_found": [],
            "recommendations_for_improvement": [],
            "validation_summary": "Report is well-structured and complete with appropriate safety considerations"
        }
    
    def test_agent_initialization(self, agent):
        """Test that agent initializes correctly"""
        assert agent.agent_name == 'agent_f_safety'
        assert agent.model == 'gpt-4o'
        assert agent.temperature == 0.1
        assert agent.client is not None
    
    def test_agent_initialization_without_api_key(self):
        """Test that agent raises error without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                SafetyValidationAgent(config={})
    
    def test_get_prompt_template(self, agent):
        """Test that prompt template is returned"""
        prompt = agent.get_prompt_template()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "safety" in prompt.lower()
        assert "consistency" in prompt.lower()
        assert "completeness" in prompt.lower()
        assert "validation" in prompt.lower()
    
    @patch('app.agents.agent_f_safety.OpenAI')
    def test_process_with_complete_data(self, mock_openai_class, agent,
                                       sample_complete_input, sample_validation_output):
        """Test validation with complete agent outputs"""
        # Mock the OpenAI API response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_validation_output)
        mock_client.chat.completions.create.return_value = mock_response
        agent.client = mock_client
        
        # Process the input
        result = agent.process(sample_complete_input)
        
        # Verify the result
        assert isinstance(result, dict)
        assert 'validation_status' in result
        assert 'overall_confidence_score' in result
        assert 'consistency_checks' in result
        assert 'completeness_checks' in result
        assert 'safety_flags' in result
        assert 'quality_assessment' in result
        assert 'confidence_factors' in result
        assert 'issues_found' in result
        assert 'recommendations_for_improvement' in result
        assert 'validation_summary' in result
        
        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4o'
        assert call_args[1]['temperature'] == 0.1
        assert call_args[1]['response_format'] == {"type": "json_object"}
    
    @patch('app.agents.agent_f_safety.OpenAI')
    def test_process_without_draft_report(self, mock_openai_class, agent):
        """Test validation fails without draft report"""
        incomplete_input = {
            "case_id": 123,
            "clinical_context": {},
            "quality_assessment": {},
            "findings": {},
            "diagnostic_reasoning": {},
            "draft_report": {}
        }
        
        # Process should return failed validation
        result = agent.process(incomplete_input)
        
        # Verify failed validation
        assert isinstance(result, dict)
        assert result['validation_status'] == 'fail'
        assert result['overall_confidence_score'] == 0.0
        assert len(result['safety_flags']['safety_issues']) > 0
    
    @patch('app.agents.agent_f_safety.OpenAI')
    def test_process_api_failure(self, mock_openai_class, agent, sample_complete_input):
        """Test handling of API failures"""
        # Mock API failure
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        agent.client = mock_client
        
        # Process should raise exception
        with pytest.raises(Exception, match="Failed to perform safety validation"):
            agent.process(sample_complete_input)
    
    @patch('app.agents.agent_f_safety.OpenAI')
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
    
    def test_format_validation_input(self, agent, sample_clinical_context,
                                     sample_quality_assessment, sample_findings,
                                     sample_diagnostic_reasoning, sample_draft_report):
        """Test formatting of agent outputs for validation"""
        formatted = agent._format_validation_input(
            sample_clinical_context,
            sample_quality_assessment,
            sample_findings,
            sample_diagnostic_reasoning,
            sample_draft_report
        )
        
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        
        # Check that all sections are included
        assert "AGENT A: CLINICAL CONTEXT" in formatted
        assert "AGENT B: QUALITY ASSESSMENT" in formatted
        assert "AGENT C: IMAGING FINDINGS" in formatted
        assert "AGENT D: DIAGNOSTIC REASONING" in formatted
        assert "AGENT E: DRAFT REPORT" in formatted
        assert "VALIDATION INSTRUCTIONS" in formatted
    
    def test_create_failed_validation(self, agent):
        """Test creation of failed validation result"""
        reason = "Test failure reason"
        failed = agent._create_failed_validation(reason)
        
        assert isinstance(failed, dict)
        assert failed['validation_status'] == 'fail'
        assert failed['overall_confidence_score'] == 0.0
        assert reason in failed['validation_summary']
        assert failed['safety_flags']['risk_level'] == 'high'
        assert len(failed['issues_found']) > 0
        assert failed['issues_found'][0]['severity'] == 'critical'
    
    def test_validate_output_valid(self, agent, sample_validation_output):
        """Test validation of valid output"""
        assert agent.validate_output(sample_validation_output) is True
    
    def test_validate_output_not_dict(self, agent):
        """Test validation fails for non-dictionary output"""
        assert agent.validate_output("not a dict") is False
        assert agent.validate_output([]) is False
        assert agent.validate_output(None) is False
    
    def test_validate_output_missing_keys(self, agent, sample_validation_output):
        """Test validation fails for missing required keys"""
        # Remove required key
        invalid_output = sample_validation_output.copy()
        del invalid_output['validation_status']
        assert agent.validate_output(invalid_output) is False
        
        # Remove another key
        invalid_output = sample_validation_output.copy()
        del invalid_output['safety_flags']
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_invalid_validation_status(self, agent, sample_validation_output):
        """Test validation fails for invalid validation_status"""
        invalid_output = sample_validation_output.copy()
        invalid_output['validation_status'] = 'invalid'
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_invalid_confidence_score(self, agent, sample_validation_output):
        """Test validation fails for invalid confidence score"""
        # Score out of range
        invalid_output = sample_validation_output.copy()
        invalid_output['overall_confidence_score'] = 1.5
        assert agent.validate_output(invalid_output) is False
        
        # Negative score
        invalid_output = sample_validation_output.copy()
        invalid_output['overall_confidence_score'] = -0.1
        assert agent.validate_output(invalid_output) is False
        
        # Not a number
        invalid_output = sample_validation_output.copy()
        invalid_output['overall_confidence_score'] = "not a number"
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_invalid_consistency_checks(self, agent, sample_validation_output):
        """Test validation fails for invalid consistency checks"""
        # Missing consistency check
        invalid_output = sample_validation_output.copy()
        del invalid_output['consistency_checks']['findings_impression_match']
        assert agent.validate_output(invalid_output) is False
        
        # Invalid status
        invalid_output = sample_validation_output.copy()
        invalid_output['consistency_checks']['internal_consistency']['status'] = 'invalid'
        assert agent.validate_output(invalid_output) is False
        
        # Missing issues list
        invalid_output = sample_validation_output.copy()
        del invalid_output['consistency_checks']['clinical_correlation']['issues']
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_invalid_safety_flags(self, agent, sample_validation_output):
        """Test validation fails for invalid safety flags"""
        # Missing safety flag key
        invalid_output = sample_validation_output.copy()
        del invalid_output['safety_flags']['critical_findings']
        assert agent.validate_output(invalid_output) is False
        
        # Invalid risk_level
        invalid_output = sample_validation_output.copy()
        invalid_output['safety_flags']['risk_level'] = 'invalid'
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_invalid_quality_scores(self, agent, sample_validation_output):
        """Test validation fails for invalid quality scores"""
        # Score out of range
        invalid_output = sample_validation_output.copy()
        invalid_output['quality_assessment']['report_clarity'] = 1.5
        assert agent.validate_output(invalid_output) is False
        
        # Not a number
        invalid_output = sample_validation_output.copy()
        invalid_output['quality_assessment']['terminology_accuracy'] = "not a number"
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_invalid_issues(self, agent, sample_validation_output):
        """Test validation fails for invalid issues"""
        # issues_found not a list
        invalid_output = sample_validation_output.copy()
        invalid_output['issues_found'] = "not a list"
        assert agent.validate_output(invalid_output) is False
        
        # Issue with invalid severity
        invalid_output = sample_validation_output.copy()
        invalid_output['issues_found'] = [
            {
                "severity": "invalid",
                "category": "consistency",
                "description": "Test issue",
                "location": "Findings",
                "recommendation": "Fix it"
            }
        ]
        assert agent.validate_output(invalid_output) is False
        
        # Issue missing required key
        invalid_output = sample_validation_output.copy()
        invalid_output['issues_found'] = [
            {
                "severity": "minor",
                "category": "quality",
                "description": "Test issue"
                # Missing location and recommendation
            }
        ]
        assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_empty_summary(self, agent, sample_validation_output):
        """Test validation fails for empty validation_summary"""
        invalid_output = sample_validation_output.copy()
        invalid_output['validation_summary'] = ""
        assert agent.validate_output(invalid_output) is False
        
        invalid_output = sample_validation_output.copy()
        invalid_output['validation_summary'] = "   "
        assert agent.validate_output(invalid_output) is False
    
    @patch('app.agents.agent_f_safety.OpenAI')
    def test_execute_success(self, mock_openai_class, agent, sample_complete_input,
                            sample_validation_output):
        """Test successful execution through execute() method"""
        # Mock the OpenAI API response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(sample_validation_output)
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
    
    @patch('app.agents.agent_f_safety.OpenAI')
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
    
    def test_validation_with_critical_findings(self, agent, sample_validation_output):
        """Test validation output with critical findings"""
        output_with_critical = sample_validation_output.copy()
        output_with_critical['safety_flags']['critical_findings'] = [
            "Large mass suspicious for malignancy",
            "Portal vein thrombosis"
        ]
        output_with_critical['safety_flags']['urgent_follow_up_needed'] = True
        output_with_critical['safety_flags']['risk_level'] = 'high'
        
        assert agent.validate_output(output_with_critical) is True
        assert len(output_with_critical['safety_flags']['critical_findings']) == 2
        assert output_with_critical['safety_flags']['urgent_follow_up_needed'] is True
    
    def test_validation_with_issues_found(self, agent, sample_validation_output):
        """Test validation output with issues found"""
        output_with_issues = sample_validation_output.copy()
        output_with_issues['validation_status'] = 'warning'
        output_with_issues['issues_found'] = [
            {
                "severity": "major",
                "category": "consistency",
                "description": "Lesion mentioned in findings but not in impression",
                "location": "Impression section",
                "recommendation": "Add lesion to impression"
            },
            {
                "severity": "minor",
                "category": "quality",
                "description": "Missing measurement units",
                "location": "Findings section",
                "recommendation": "Add units to all measurements"
            }
        ]
        
        assert agent.validate_output(output_with_issues) is True
        assert len(output_with_issues['issues_found']) == 2
        assert output_with_issues['issues_found'][0]['severity'] == 'major'
        assert output_with_issues['issues_found'][1]['severity'] == 'minor'
