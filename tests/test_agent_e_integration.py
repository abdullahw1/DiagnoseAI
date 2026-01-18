"""
Integration tests for Agent E: Structured Report Drafting

Tests the report drafting agent with real API calls and complete pipeline outputs.
"""

import pytest
import os
from app.agents.agent_e_report import ReportDraftingAgent


@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="OpenAI API key not available"
)
class TestReportDraftingAgentIntegration:
    """Integration test suite for ReportDraftingAgent with real API calls"""
    
    @pytest.fixture
    def agent(self):
        """Create a ReportDraftingAgent instance with real API key"""
        return ReportDraftingAgent()
    
    @pytest.fixture
    def complete_pipeline_output(self):
        """Complete output from all previous agents for integration testing"""
        return {
            "case_id": 999,
            "clinical_context": {
                "clinical_indication": "Abdominal pain, elevated liver enzymes",
                "relevant_history": "45-year-old male with history of alcohol use",
                "pertinent_labs": {
                    "ALT": "85 U/L",
                    "AST": "110 U/L"
                },
                "risk_factors": ["Alcohol use", "Obesity"],
                "clinical_questions": ["Assess liver parenchyma", "Rule out focal lesions"]
            },
            "quality_assessment": {
                "overall_quality": "good",
                "image_views": [
                    {
                        "anatomical_view": "Right lobe",
                        "quality_score": 8.0,
                        "technical_adequacy": "adequate"
                    }
                ],
                "technical_factors": {
                    "penetration": "adequate",
                    "resolution": "good"
                },
                "limitations": []
            },
            "findings": {
                "organ_assessment": {
                    "size": "Normal, 14 cm",
                    "echogenicity": "Increased",
                    "echotexture": "Coarse",
                    "surface": "Smooth"
                },
                "focal_lesions": [],
                "vascular_findings": {
                    "portal_vein": "Patent, 11 mm",
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
                    "liver_length": "14 cm"
                },
                "confidence_assessment": {
                    "overall_confidence": 0.9,
                    "limitations": []
                },
                "summary": "Increased hepatic echogenicity with coarse echotexture, no focal lesions"
            },
            "diagnostic_reasoning": {
                "differential_diagnosis": [
                    {
                        "diagnosis": "Hepatic steatosis",
                        "likelihood": "high",
                        "supporting_findings": ["Increased echogenicity", "Alcohol use history"],
                        "contradicting_findings": [],
                        "reasoning": "Increased echogenicity consistent with fatty infiltration",
                        "clinical_significance": "Common finding in alcohol use and obesity"
                    }
                ],
                "primary_diagnosis": "Hepatic steatosis",
                "key_findings_summary": ["Increased hepatic echogenicity", "Coarse echotexture"],
                "clinical_correlation": "Findings consistent with fatty liver disease",
                "recommendations": {
                    "follow_up_imaging": [],
                    "clinical_follow_up": ["Lifestyle modification", "Repeat LFTs in 3 months"],
                    "additional_workup": []
                },
                "confidence_assessment": {
                    "diagnostic_confidence": 0.85,
                    "factors_affecting_confidence": []
                },
                "summary": "Hepatic steatosis, likely related to alcohol use and obesity"
            }
        }
    
    def test_generate_report_with_complete_data(self, agent, complete_pipeline_output):
        """Test report generation with complete pipeline output"""
        # Process the complete input
        result = agent.process(complete_pipeline_output)
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert 'report_sections' in result
        assert 'structured_data' in result
        assert 'report_metadata' in result
        assert 'full_report_text' in result
        assert 'summary' in result
        
        # Verify report sections are present and non-empty
        assert 'clinical_history' in result['report_sections']
        assert len(result['report_sections']['clinical_history']) > 0
        assert 'technique' in result['report_sections']
        assert len(result['report_sections']['technique']) > 0
        assert 'findings' in result['report_sections']
        assert len(result['report_sections']['findings']) > 0
        assert 'impression' in result['report_sections']
        assert len(result['report_sections']['impression']) > 0
        
        # Verify structured data
        assert 'primary_diagnosis' in result['structured_data']
        assert len(result['structured_data']['primary_diagnosis']) > 0
        assert isinstance(result['structured_data']['key_findings'], list)
        assert isinstance(result['structured_data']['recommendations'], list)
        
        # Verify full report text contains all sections
        full_text = result['full_report_text']
        assert 'CLINICAL HISTORY' in full_text or 'Clinical History' in full_text
        assert 'TECHNIQUE' in full_text or 'Technique' in full_text
        assert 'FINDINGS' in full_text or 'Findings' in full_text
        assert 'IMPRESSION' in full_text or 'Impression' in full_text
        
        # Verify validation passes
        assert agent.validate_output(result) is True
    
    def test_execute_with_complete_data(self, agent, complete_pipeline_output):
        """Test execute() method with complete pipeline output"""
        # Execute the agent
        result = agent.execute(complete_pipeline_output)
        
        # Verify execution success
        assert result['success'] is True
        assert result['error'] is None
        assert 'output' in result
        assert 'execution_time_ms' in result
        assert result['execution_time_ms'] > 0
        
        # Verify output structure
        output = result['output']
        assert 'report_sections' in output
        assert 'structured_data' in output
        assert 'full_report_text' in output
    
    def test_report_content_quality(self, agent, complete_pipeline_output):
        """Test that generated report has appropriate medical content"""
        result = agent.process(complete_pipeline_output)
        
        # Check that clinical information is incorporated
        clinical_history = result['report_sections']['clinical_history']
        assert 'elevated liver enzymes' in clinical_history.lower() or 'alt' in clinical_history.lower()
        
        # Check that findings are described
        findings = result['report_sections']['findings']
        assert 'echogenicity' in findings.lower() or 'echotexture' in findings.lower()
        
        # Check that impression includes diagnosis
        impression = result['report_sections']['impression']
        assert 'steatosis' in impression.lower() or 'fatty' in impression.lower()
        
        # Check that primary diagnosis matches reasoning
        assert 'steatosis' in result['structured_data']['primary_diagnosis'].lower() or \
               'fatty' in result['structured_data']['primary_diagnosis'].lower()
    
    def test_report_with_focal_lesion(self, agent, complete_pipeline_output):
        """Test report generation when focal lesion is present"""
        # Add a focal lesion to the findings
        complete_pipeline_output['findings']['focal_lesions'] = [
            {
                "location": "Right lobe, segment 6",
                "size": "1.5 cm",
                "echogenicity": "Hyperechoic",
                "margins": "Well-defined",
                "characteristics": "Solid",
                "description": "Small hyperechoic lesion"
            }
        ]
        
        # Update diagnostic reasoning
        complete_pipeline_output['diagnostic_reasoning']['differential_diagnosis'].append({
            "diagnosis": "Hepatic hemangioma",
            "likelihood": "moderate",
            "supporting_findings": ["Hyperechoic lesion", "Well-defined margins"],
            "contradicting_findings": [],
            "reasoning": "Small hyperechoic lesion consistent with hemangioma",
            "clinical_significance": "Benign finding, may require follow-up"
        })
        
        result = agent.process(complete_pipeline_output)
        
        # Verify lesion is mentioned in findings
        findings = result['report_sections']['findings']
        assert 'lesion' in findings.lower()
        assert '1.5' in findings or '1.5 cm' in findings
        
        # Verify lesion is addressed in impression
        impression = result['report_sections']['impression']
        assert 'lesion' in impression.lower() or 'hemangioma' in impression.lower()
    
    def test_report_with_critical_findings(self, agent, complete_pipeline_output):
        """Test report generation with critical findings"""
        # Add critical findings
        complete_pipeline_output['diagnostic_reasoning']['differential_diagnosis'] = [
            {
                "diagnosis": "Portal vein thrombosis",
                "likelihood": "high",
                "supporting_findings": ["Portal vein abnormality"],
                "contradicting_findings": [],
                "reasoning": "Concerning for acute thrombosis",
                "clinical_significance": "Requires immediate clinical attention"
            }
        ]
        complete_pipeline_output['diagnostic_reasoning']['primary_diagnosis'] = "Portal vein thrombosis"
        
        result = agent.process(complete_pipeline_output)
        
        # Verify critical findings are highlighted
        impression = result['report_sections']['impression']
        assert 'thrombosis' in impression.lower() or 'portal vein' in impression.lower()
        
        # Check if critical findings are flagged in structured data
        if result['structured_data']['critical_findings']:
            assert len(result['structured_data']['critical_findings']) > 0
    
    def test_report_consistency(self, agent, complete_pipeline_output):
        """Test that report maintains consistency between sections"""
        result = agent.process(complete_pipeline_output)
        
        # Primary diagnosis should appear in both impression and structured data
        primary_dx = result['structured_data']['primary_diagnosis'].lower()
        impression = result['report_sections']['impression'].lower()
        
        # Check for key terms from primary diagnosis in impression
        key_terms = ['steatosis', 'fatty', 'liver']
        assert any(term in impression for term in key_terms)
        
        # Key findings should be mentioned in findings section
        findings_text = result['report_sections']['findings'].lower()
        for finding in result['structured_data']['key_findings']:
            # At least some key terms from findings should appear
            finding_terms = finding.lower().split()
            # Check if at least one significant term appears
            significant_terms = [t for t in finding_terms if len(t) > 4]
            if significant_terms:
                assert any(term in findings_text for term in significant_terms[:2])
