"""
Unit tests for structured findings integration into AI pipeline.

Tests cover:
- ClinicalContextAgent with structured findings
- FindingsExtractionAgentEnhanced
- Orchestrator storing AI findings
- Integration with existing pipeline
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from app.agents.agent_a_context import ClinicalContextAgent
from app.agents.agent_c_findings_enhanced import FindingsExtractionAgentEnhanced
from app.agents.orchestrator import AgentOrchestrator
from app.models import Case, StructuredFindings, AIGeneratedFindings


class TestClinicalContextAgentWithFindings:
    """Test suite for ClinicalContextAgent with structured findings."""
    
    def test_combine_clinical_info_with_findings(self):
        """Test combining clinical information with structured findings."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            structured_findings = {
                'liver_size': 'Enlarged',
                'liver_texture': 'Fatty',
                'spleen_size': 'Normal',
                'gb_calculus': 'Present',
                'comments': 'Test findings'
            }
            
            combined = agent._combine_clinical_info(
                patient_history="History of diabetes",
                clinical_indication="Abdominal pain",
                lab_results="ALT: 45 U/L",
                clinical_history="",
                indication="",
                structured_findings=structured_findings
            )
            
            assert "History of diabetes" in combined
            assert "Abdominal pain" in combined
            assert "ALT: 45 U/L" in combined
            assert "User-Provided Structured Findings" in combined
            assert "Liver" in combined
            assert "Enlarged" in combined
    
    def test_format_structured_findings_complete(self):
        """Test formatting complete structured findings."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            findings = {
                'liver_size': 'Enlarged',
                'liver_texture': 'Fatty',
                'liver_focal_defect': 'Absent',
                'liver_cbd': 'Normal',
                'liver_pv': 'Dilated',
                'spleen_size': 'Normal',
                'spleen_focal_defect': 'Absent',
                'gb_calculus': 'Present',
                'gb_wall_edema': 'Absent',
                'right_kidney_size': 'Normal',
                'right_kidney_texture': 'Normal',
                'right_kidney_other': 'No stones',
                'left_kidney_size': 'Shrunken',
                'left_kidney_texture': 'Echogenic',
                'left_kidney_other': 'Cyst present',
                'pancreas_findings': 'Normal appearance',
                'bladder_filling': 'Full',
                'bladder_stone_mass': 'Absent',
                'bladder_mucosal_irregularity': 'Absent',
                'prostate_findings': 'Enlarged',
                'ascites': 'Present',
                'pleural_effusions': 'Absent',
                'para_aortic_lymph_nodes': 'Absent',
                'other_findings': 'None',
                'comments': 'Overall assessment normal'
            }
            
            formatted = agent._format_structured_findings(findings)
            
            assert 'Liver: Size: Enlarged' in formatted
            assert 'Fatty' in formatted
            assert 'Spleen: Size: Normal' in formatted
            assert 'Gall Bladder: Calculus: Present' in formatted
            assert 'Right Kidney: Size: Normal' in formatted
            assert 'Left Kidney: Size: Shrunken' in formatted
            assert 'Pancreas: Normal appearance' in formatted
            assert 'Urinary Bladder: Filling: Full' in formatted
            assert 'Prostate: Enlarged' in formatted
            assert 'Additional: Ascites: Present' in formatted
            assert 'Comments: Overall assessment normal' in formatted
    
    def test_format_structured_findings_partial(self):
        """Test formatting partial structured findings."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            findings = {
                'liver_size': 'Enlarged',
                'spleen_size': 'Normal',
                'gb_calculus': None,
                'comments': 'Limited findings'
            }
            
            formatted = agent._format_structured_findings(findings)
            
            assert 'Liver: Size: Enlarged' in formatted
            assert 'Spleen: Size: Normal' in formatted
            assert 'Gall Bladder' not in formatted  # No GB findings
            assert 'Comments: Limited findings' in formatted
    
    def test_format_structured_findings_empty(self):
        """Test formatting empty structured findings."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            formatted = agent._format_structured_findings({})
            assert formatted == ""
            
            formatted = agent._format_structured_findings(None)
            assert formatted == ""
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_process_with_structured_findings(self, mock_openai_class):
        """Test processing with structured findings included."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'relevant_history': 'History of liver disease',
            'clinical_indication': 'Follow-up ultrasound',
            'pertinent_labs': {'ALT': '45 U/L'},
            'risk_factors': ['Liver disease'],
            'clinical_questions': ['Assess liver size'],
            'summary': 'Patient with known liver disease for follow-up'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            structured_findings = {
                'liver_size': 'Enlarged',
                'liver_texture': 'Fatty'
            }
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'patient_history': 'History of liver disease',
                    'clinical_indication': 'Follow-up ultrasound',
                    'lab_results': 'ALT: 45 U/L',
                    'structured_findings': structured_findings
                }
            }
            
            result = agent.process(input_data)
            
            # Verify structured findings are included in result
            assert 'structured_findings' in result
            assert result['structured_findings'] == structured_findings
            assert result['relevant_history'] == 'History of liver disease'
    
    @patch('app.agents.agent_a_context.OpenAI')
    def test_process_with_findings_no_other_info(self, mock_openai_class):
        """Test processing with only structured findings and no other clinical info."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'relevant_history': None,
            'clinical_indication': 'No specific indication',
            'pertinent_labs': {},
            'risk_factors': [],
            'clinical_questions': [],
            'summary': 'User-provided findings available for reference'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ClinicalContextAgent()
            
            structured_findings = {
                'liver_size': 'Enlarged',
                'spleen_size': 'Normal'
            }
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'patient_history': '',
                    'clinical_indication': '',
                    'lab_results': '',
                    'clinical_history': '',
                    'indication': '',
                    'structured_findings': structured_findings
                }
            }
            
            result = agent.process(input_data)
            
            # Should include structured findings in result
            assert 'structured_findings' in result
            assert result['structured_findings'] == structured_findings
            
            # API should be called because structured findings provide content
            mock_client.chat.completions.create.assert_called_once()


class TestFindingsExtractionAgentEnhanced:
    """Test suite for FindingsExtractionAgentEnhanced."""
    
    def test_agent_initialization(self):
        """Test that enhanced agent initializes correctly."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            assert agent.agent_name == 'agent_c_findings_enhanced'
            assert agent.model == 'gpt-4o'
            assert agent.client is not None
    
    def test_get_prompt_template(self):
        """Test that enhanced prompt template includes structured format."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            prompt = agent.get_prompt_template()
            
            assert isinstance(prompt, str)
            assert 'liver' in prompt.lower()
            assert 'spleen' in prompt.lower()
            assert 'kidney' in prompt.lower()
            assert 'Normal|Enlarged|Shrunken' in prompt
            assert 'confidence_scores' in prompt
    
    def test_validate_enum_exact_match(self):
        """Test enum validation with exact match."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            allowed = ['Normal', 'Enlarged', 'Shrunken']
            
            assert agent._validate_enum('Normal', allowed) == 'Normal'
            assert agent._validate_enum('Enlarged', allowed) == 'Enlarged'
            assert agent._validate_enum('Shrunken', allowed) == 'Shrunken'
    
    def test_validate_enum_case_insensitive(self):
        """Test enum validation with case-insensitive match."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            allowed = ['Normal', 'Enlarged', 'Shrunken']
            
            assert agent._validate_enum('normal', allowed) == 'Normal'
            assert agent._validate_enum('ENLARGED', allowed) == 'Enlarged'
            assert agent._validate_enum('shrunken', allowed) == 'Shrunken'
    
    def test_validate_enum_invalid(self):
        """Test enum validation with invalid value."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            allowed = ['Normal', 'Enlarged', 'Shrunken']
            
            assert agent._validate_enum('Invalid', allowed) is None
            assert agent._validate_enum('', allowed) is None
    
    def test_validate_enum_none(self):
        """Test enum validation with None value."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            allowed = ['Normal', 'Enlarged']
            assert agent._validate_enum(None, allowed) is None
    
    def test_truncate_text_within_limit(self):
        """Test text truncation when within limit."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            text = "Short text"
            assert agent._truncate_text(text, 100) == "Short text"
    
    def test_truncate_text_exceeds_limit(self):
        """Test text truncation when exceeding limit."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            text = "A" * 300
            truncated = agent._truncate_text(text, 200)
            
            assert len(truncated) == 200
            assert truncated == "A" * 200
    
    def test_truncate_text_none(self):
        """Test text truncation with None value."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            assert agent._truncate_text(None, 100) is None
    
    def test_truncate_text_empty(self):
        """Test text truncation with empty string."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            assert agent._truncate_text('', 100) is None
            assert agent._truncate_text('   ', 100) is None
    
    def test_normalize_findings_complete(self):
        """Test normalization of complete findings."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            raw_findings = {
                'liver': {
                    'size': 'Enlarged',
                    'texture': 'Fatty',
                    'focal_defect': 'Absent',
                    'cbd': 'Normal',
                    'pv': 'Dilated'
                },
                'spleen': {
                    'size': 'Normal',
                    'focal_defect': 'Absent'
                },
                'gall_bladder': {
                    'calculus': 'Present',
                    'wall_edema': 'Absent'
                },
                'right_kidney': {
                    'size': 'Normal',
                    'texture': 'Normal',
                    'other': 'No abnormalities'
                },
                'left_kidney': {
                    'size': 'Shrunken',
                    'texture': 'Echogenic',
                    'other': 'Cyst present'
                },
                'pancreas': {
                    'findings': 'Normal appearance'
                },
                'urinary_bladder': {
                    'filling': 'Full',
                    'stone_mass': 'Absent',
                    'mucosal_irregularity': 'Absent'
                },
                'prostate': {
                    'findings': 'Enlarged'
                },
                'additional': {
                    'ascites': 'Present',
                    'pleural_effusions': 'Absent',
                    'para_aortic_lymph_nodes': 'Absent',
                    'other': 'None'
                },
                'comments': 'Overall assessment',
                'confidence_scores': {'overall': 0.9}
            }
            
            normalized = agent._normalize_findings(raw_findings)
            
            assert normalized['liver_size'] == 'Enlarged'
            assert normalized['liver_texture'] == 'Fatty'
            assert normalized['liver_focal_defect'] == 'Absent'
            assert normalized['liver_cbd'] == 'Normal'
            assert normalized['liver_pv'] == 'Dilated'
            assert normalized['spleen_size'] == 'Normal'
            assert normalized['spleen_focal_defect'] == 'Absent'
            assert normalized['gb_calculus'] == 'Present'
            assert normalized['gb_wall_edema'] == 'Absent'
            assert normalized['right_kidney_size'] == 'Normal'
            assert normalized['right_kidney_texture'] == 'Normal'
            assert normalized['right_kidney_other'] == 'No abnormalities'
            assert normalized['left_kidney_size'] == 'Shrunken'
            assert normalized['left_kidney_texture'] == 'Echogenic'
            assert normalized['left_kidney_other'] == 'Cyst present'
            assert normalized['pancreas_findings'] == 'Normal appearance'
            assert normalized['bladder_filling'] == 'Full'
            assert normalized['bladder_stone_mass'] == 'Absent'
            assert normalized['bladder_mucosal_irregularity'] == 'Absent'
            assert normalized['prostate_findings'] == 'Enlarged'
            assert normalized['ascites'] == 'Present'
            assert normalized['pleural_effusions'] == 'Absent'
            assert normalized['para_aortic_lymph_nodes'] == 'Absent'
            assert normalized['other_findings'] == 'None'
            assert normalized['comments'] == 'Overall assessment'
            assert normalized['confidence_scores'] == {'overall': 0.9}
    
    def test_normalize_findings_case_insensitive(self):
        """Test normalization handles case-insensitive values."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            raw_findings = {
                'liver': {
                    'size': 'enlarged',  # lowercase
                    'texture': 'FATTY',  # uppercase
                    'focal_defect': 'absent'
                },
                'spleen': {},
                'gall_bladder': {},
                'right_kidney': {},
                'left_kidney': {},
                'pancreas': {},
                'urinary_bladder': {},
                'prostate': {},
                'additional': {},
                'confidence_scores': {}
            }
            
            normalized = agent._normalize_findings(raw_findings)
            
            assert normalized['liver_size'] == 'Enlarged'
            assert normalized['liver_texture'] == 'Fatty'
            assert normalized['liver_focal_defect'] == 'Absent'
    
    def test_normalize_findings_invalid_values(self):
        """Test normalization handles invalid enumerated values."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            raw_findings = {
                'liver': {
                    'size': 'Invalid',  # Invalid value
                    'texture': 'Normal'
                },
                'spleen': {},
                'gall_bladder': {},
                'right_kidney': {},
                'left_kidney': {},
                'pancreas': {},
                'urinary_bladder': {},
                'prostate': {},
                'additional': {},
                'confidence_scores': {}
            }
            
            normalized = agent._normalize_findings(raw_findings)
            
            assert normalized['liver_size'] is None  # Invalid value becomes None
            assert normalized['liver_texture'] == 'Normal'
    
    def test_normalize_findings_text_truncation(self):
        """Test normalization truncates long text fields."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            long_text = "A" * 300
            
            raw_findings = {
                'liver': {},
                'spleen': {},
                'gall_bladder': {},
                'right_kidney': {
                    'other': long_text  # Exceeds 200 char limit
                },
                'left_kidney': {},
                'pancreas': {},
                'urinary_bladder': {},
                'prostate': {},
                'additional': {},
                'confidence_scores': {}
            }
            
            normalized = agent._normalize_findings(raw_findings)
            
            assert len(normalized['right_kidney_other']) == 200
    
    def test_create_minimal_structured_findings(self):
        """Test creation of minimal structured findings."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            minimal = agent._create_minimal_structured_findings()
            
            # All fields should be None except comments and confidence
            assert minimal['liver_size'] is None
            assert minimal['spleen_size'] is None
            assert minimal['gb_calculus'] is None
            assert minimal['comments'] is not None
            assert 'missing images' in minimal['comments'].lower()
            assert minimal['confidence_scores']['overall'] == 0.0
    
    def test_validate_output_valid(self):
        """Test validation of valid structured findings output."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            valid_output = {
                'liver_size': 'Normal',
                'liver_texture': 'Normal',
                'liver_focal_defect': 'Absent',
                'liver_cbd': 'Normal',
                'liver_pv': 'Normal',
                'spleen_size': 'Normal',
                'spleen_focal_defect': 'Absent',
                'gb_calculus': 'Absent',
                'gb_wall_edema': 'Absent',
                'right_kidney_size': 'Normal',
                'right_kidney_texture': 'Normal',
                'right_kidney_other': None,
                'left_kidney_size': 'Normal',
                'left_kidney_texture': 'Normal',
                'left_kidney_other': None,
                'pancreas_findings': None,
                'bladder_filling': 'Full',
                'bladder_stone_mass': 'Absent',
                'bladder_mucosal_irregularity': 'Absent',
                'prostate_findings': None,
                'ascites': 'Absent',
                'pleural_effusions': 'Absent',
                'para_aortic_lymph_nodes': 'Absent',
                'other_findings': None,
                'comments': 'Normal study',
                'confidence_scores': {'overall': 0.9}
            }
            
            assert agent.validate_output(valid_output) is True
    
    def test_validate_output_missing_key(self):
        """Test validation fails when required key is missing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            invalid_output = {
                'liver_size': 'Normal',
                # Missing many required keys
                'confidence_scores': {}
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_format_clinical_context_with_findings(self):
        """Test formatting clinical context with user findings."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgentEnhanced()
            
            clinical_context = {
                'clinical_indication': 'Abdominal pain',
                'relevant_history': 'Diabetes',
                'pertinent_labs': {'ALT': '45 U/L'},
                'clinical_questions': ['Rule out hepatomegaly'],
                'structured_findings': {
                    'liver_size': 'Enlarged',
                    'spleen_size': 'Normal'
                }
            }
            
            formatted = agent._format_clinical_context_with_findings(clinical_context)
            
            assert 'Indication: Abdominal pain' in formatted
            assert 'History: Diabetes' in formatted
            assert 'Labs: ALT: 45 U/L' in formatted
            assert 'Questions: Rule out hepatomegaly' in formatted
            assert 'User-Provided Findings' in formatted
            assert 'liver_size' in formatted


class TestOrchestratorWithFindings:
    """Test suite for orchestrator with findings integration."""
    
    def test_serialize_structured_findings(self):
        """Test serialization of StructuredFindings model."""
        orchestrator = AgentOrchestrator()
        
        # Create mock StructuredFindings without spec to avoid app context issues
        findings = Mock()
        findings.liver_size = 'Enlarged'
        findings.liver_texture = 'Fatty'
        findings.liver_focal_defect = 'Absent'
        findings.liver_cbd = 'Normal'
        findings.liver_pv = 'Dilated'
        findings.spleen_size = 'Normal'
        findings.spleen_focal_defect = 'Absent'
        findings.gb_calculus = 'Present'
        findings.gb_wall_edema = 'Absent'
        findings.right_kidney_size = 'Normal'
        findings.right_kidney_texture = 'Normal'
        findings.right_kidney_other = None
        findings.left_kidney_size = 'Shrunken'
        findings.left_kidney_texture = 'Echogenic'
        findings.left_kidney_other = 'Cyst'
        findings.pancreas_findings = 'Normal'
        findings.bladder_filling = 'Full'
        findings.bladder_stone_mass = 'Absent'
        findings.bladder_mucosal_irregularity = 'Absent'
        findings.prostate_findings = None
        findings.ascites = 'Present'
        findings.pleural_effusions = 'Absent'
        findings.para_aortic_lymph_nodes = 'Absent'
        findings.other_findings = None
        findings.comments = 'Test comment'
        
        serialized = orchestrator._serialize_structured_findings(findings)
        
        assert serialized['liver_size'] == 'Enlarged'
        assert serialized['liver_texture'] == 'Fatty'
        assert serialized['spleen_size'] == 'Normal'
        assert serialized['gb_calculus'] == 'Present'
        assert serialized['left_kidney_size'] == 'Shrunken'
        assert serialized['ascites'] == 'Present'
        assert serialized['comments'] == 'Test comment'
    
    def test_is_structured_findings_format_true(self):
        """Test detection of structured findings format."""
        orchestrator = AgentOrchestrator()
        
        structured_data = {
            'liver_size': 'Normal',
            'spleen_size': 'Normal',
            'confidence_scores': {}
        }
        
        assert orchestrator._is_structured_findings_format(structured_data) is True
    
    def test_is_structured_findings_format_false(self):
        """Test detection of non-structured findings format."""
        orchestrator = AgentOrchestrator()
        
        non_structured_data = {
            'organ_assessment': {},
            'focal_lesions': [],
            'summary': 'Test'
        }
        
        assert orchestrator._is_structured_findings_format(non_structured_data) is False
    
    def test_is_structured_findings_format_empty(self):
        """Test detection with empty data."""
        orchestrator = AgentOrchestrator()
        
        assert orchestrator._is_structured_findings_format({}) is False
