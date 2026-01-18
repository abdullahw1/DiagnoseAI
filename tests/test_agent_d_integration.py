"""
Integration tests for Agent D: Diagnostic Reasoning

Tests the diagnostic reasoning agent with real OpenAI API calls
to verify end-to-end functionality.
"""

import pytest
import os
from app.agents.agent_d_reasoning import DiagnosticReasoningAgent


@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="OpenAI API key not available"
)
class TestDiagnosticReasoningAgentIntegration:
    """Integration test suite for DiagnosticReasoningAgent with real API"""
    
    @pytest.fixture
    def agent(self):
        """Create agent with real API key"""
        return DiagnosticReasoningAgent()
    
    @pytest.fixture
    def cirrhosis_case(self):
        """Complete case data for cirrhosis"""
        return {
            'case_id': 1,
            'clinical_context': {
                "relevant_history": "History of chronic hepatitis C infection for 15 years, previous alcohol use disorder",
                "clinical_indication": "Elevated liver enzymes, abdominal distension, fatigue",
                "pertinent_labs": {
                    "ALT": "145 U/L (elevated)",
                    "AST": "180 U/L (elevated)",
                    "Albumin": "2.8 g/dL (low)",
                    "Platelet count": "95,000/μL (low)",
                    "INR": "1.4 (elevated)"
                },
                "risk_factors": [
                    "Chronic hepatitis C",
                    "History of alcohol use",
                    "Age 58",
                    "Male"
                ],
                "clinical_questions": [
                    "Assess for cirrhosis",
                    "Evaluate for portal hypertension",
                    "Screen for hepatocellular carcinoma"
                ],
                "summary": "Patient with chronic hepatitis C and elevated liver enzymes, concern for cirrhosis"
            },
            'findings': {
                "organ_assessment": {
                    "size": "Small, measuring 13 cm in length (normal 15-17 cm)",
                    "echogenicity": "Markedly increased and heterogeneous",
                    "echotexture": "Coarse, nodular",
                    "surface": "Irregular, nodular contour"
                },
                "focal_lesions": [],
                "vascular_findings": {
                    "portal_vein": "Dilated, measuring 15 mm in diameter (normal <13 mm)",
                    "hepatic_veins": "Patent but attenuated",
                    "abnormalities": [
                        "Portal vein dilation",
                        "Hepatofugal flow direction (reversed)"
                    ]
                },
                "biliary_system": {
                    "intrahepatic_ducts": "Normal, not dilated",
                    "common_bile_duct": "Normal caliber, 6 mm",
                    "abnormalities": []
                },
                "additional_findings": {
                    "ascites": "Present, moderate amount of ascites in perihepatic and perisplenic regions",
                    "other": [
                        "Splenomegaly (16 cm)",
                        "Recanalized paraumbilical vein"
                    ]
                },
                "measurements": {
                    "liver_length": "13 cm",
                    "portal_vein_diameter": "15 mm",
                    "spleen_length": "16 cm",
                    "common_bile_duct": "6 mm"
                },
                "confidence_assessment": {
                    "overall_confidence": 0.9,
                    "limitations": []
                },
                "summary": "Small, coarse, nodular liver with portal hypertension signs including dilated portal vein, ascites, splenomegaly, and recanalized paraumbilical vein"
            }
        }
    
    @pytest.fixture
    def hemangioma_case(self):
        """Complete case data for hepatic hemangioma"""
        return {
            'case_id': 2,
            'clinical_context': {
                "relevant_history": "No significant past medical history",
                "clinical_indication": "Incidental finding on CT, further characterization requested",
                "pertinent_labs": {
                    "ALT": "28 U/L (normal)",
                    "AST": "32 U/L (normal)"
                },
                "risk_factors": ["Female", "Age 42"],
                "clinical_questions": ["Characterize liver lesion"],
                "summary": "Healthy patient with incidental liver lesion on CT"
            },
            'findings': {
                "organ_assessment": {
                    "size": "Normal, measuring 16 cm in length",
                    "echogenicity": "Normal",
                    "echotexture": "Homogeneous",
                    "surface": "Smooth"
                },
                "focal_lesions": [
                    {
                        "location": "Right hepatic lobe, segment 6",
                        "size": "3.2 x 2.8 cm",
                        "echogenicity": "Hyperechoic",
                        "margins": "Well-defined, sharp borders",
                        "characteristics": "Solid, homogeneous",
                        "posterior_acoustic": "Enhancement",
                        "description": "Well-circumscribed hyperechoic lesion with homogeneous internal echotexture and posterior acoustic enhancement"
                    }
                ],
                "vascular_findings": {
                    "portal_vein": "Normal caliber and patency",
                    "hepatic_veins": "Patent, normal",
                    "abnormalities": []
                },
                "biliary_system": {
                    "intrahepatic_ducts": "Normal",
                    "common_bile_duct": "Normal, 5 mm",
                    "abnormalities": []
                },
                "additional_findings": {
                    "ascites": "Absent",
                    "other": []
                },
                "measurements": {
                    "liver_length": "16 cm",
                    "lesion_size": "3.2 x 2.8 cm"
                },
                "confidence_assessment": {
                    "overall_confidence": 0.85,
                    "limitations": []
                },
                "summary": "3.2 cm well-defined hyperechoic lesion in right hepatic lobe with posterior enhancement, otherwise normal liver"
            }
        }
    
    def test_reasoning_for_cirrhosis_case(self, agent, cirrhosis_case):
        """Test diagnostic reasoning for cirrhosis case with real API"""
        result = agent.execute(cirrhosis_case)
        
        # Verify execution success
        assert result['success'] is True
        assert result['error'] is None
        assert result['execution_time_ms'] > 0
        
        output = result['output']
        
        # Verify output structure
        assert 'differential_diagnosis' in output
        assert 'primary_diagnosis' in output
        assert 'recommendations' in output
        
        # Verify differential diagnosis
        assert len(output['differential_diagnosis']) > 0
        
        # Check for cirrhosis in differential
        diagnoses = [d['diagnosis'].lower() for d in output['differential_diagnosis']]
        assert any('cirrhosis' in d or 'cirrhotic' in d for d in diagnoses), \
            f"Expected cirrhosis in differential, got: {diagnoses}"
        
        # Verify primary diagnosis mentions cirrhosis
        assert 'cirrhosis' in output['primary_diagnosis'].lower() or \
               'cirrhotic' in output['primary_diagnosis'].lower()
        
        # Verify key findings are captured
        key_findings = ' '.join(output['key_findings_summary']).lower()
        assert any(term in key_findings for term in ['nodular', 'coarse', 'ascites', 'portal'])
        
        # Verify recommendations are present
        assert len(output['recommendations']['follow_up_imaging']) > 0 or \
               len(output['recommendations']['clinical_follow_up']) > 0
        
        # Verify confidence assessment
        assert 0 <= output['confidence_assessment']['diagnostic_confidence'] <= 1
        
        print(f"\nCirrhosis Case Results:")
        print(f"Primary Diagnosis: {output['primary_diagnosis']}")
        print(f"Differential Diagnoses: {[d['diagnosis'] for d in output['differential_diagnosis']]}")
        print(f"Confidence: {output['confidence_assessment']['diagnostic_confidence']}")
    
    def test_reasoning_for_hemangioma_case(self, agent, hemangioma_case):
        """Test diagnostic reasoning for hemangioma case with real API"""
        result = agent.execute(hemangioma_case)
        
        # Verify execution success
        assert result['success'] is True
        assert result['error'] is None
        
        output = result['output']
        
        # Verify output structure
        assert 'differential_diagnosis' in output
        assert 'primary_diagnosis' in output
        
        # Check for hemangioma in differential
        diagnoses = [d['diagnosis'].lower() for d in output['differential_diagnosis']]
        assert any('hemangioma' in d for d in diagnoses), \
            f"Expected hemangioma in differential, got: {diagnoses}"
        
        # Verify recommendations
        assert 'recommendations' in output
        
        # Verify confidence
        assert output['confidence_assessment']['diagnostic_confidence'] > 0
        
        print(f"\nHemangioma Case Results:")
        print(f"Primary Diagnosis: {output['primary_diagnosis']}")
        print(f"Differential Diagnoses: {[d['diagnosis'] for d in output['differential_diagnosis']]}")
        print(f"Confidence: {output['confidence_assessment']['diagnostic_confidence']}")
    
    def test_reasoning_validates_output(self, agent, cirrhosis_case):
        """Test that agent validates its own output"""
        result = agent.execute(cirrhosis_case)
        
        # If execution succeeded, validation must have passed
        if result['success']:
            assert agent.validate_output(result['output']) is True
    
    def test_reasoning_with_minimal_context(self, agent):
        """Test reasoning with minimal clinical context"""
        minimal_case = {
            'case_id': 3,
            'clinical_context': {
                "relevant_history": None,
                "clinical_indication": "Abdominal ultrasound",
                "pertinent_labs": {},
                "risk_factors": [],
                "clinical_questions": [],
                "summary": "Limited clinical information"
            },
            'findings': {
                "organ_assessment": {
                    "size": "Normal",
                    "echogenicity": "Normal",
                    "echotexture": "Homogeneous",
                    "surface": "Smooth"
                },
                "focal_lesions": [],
                "vascular_findings": {
                    "portal_vein": "Normal",
                    "hepatic_veins": "Normal",
                    "abnormalities": []
                },
                "biliary_system": {
                    "intrahepatic_ducts": "Normal",
                    "common_bile_duct": "Normal",
                    "abnormalities": []
                },
                "additional_findings": {
                    "ascites": "Absent",
                    "other": []
                },
                "measurements": {},
                "confidence_assessment": {
                    "overall_confidence": 0.9,
                    "limitations": []
                },
                "summary": "Normal liver ultrasound"
            }
        }
        
        result = agent.execute(minimal_case)
        
        assert result['success'] is True
        output = result['output']
        
        # Should indicate normal findings
        primary = output['primary_diagnosis'].lower()
        assert any(term in primary for term in ['normal', 'no significant', 'unremarkable'])
        
        print(f"\nNormal Case Results:")
        print(f"Primary Diagnosis: {output['primary_diagnosis']}")
    
    def test_reasoning_execution_timing(self, agent, cirrhosis_case):
        """Test that execution timing is recorded"""
        result = agent.execute(cirrhosis_case)
        
        assert 'execution_time_ms' in result
        assert result['execution_time_ms'] > 0
        assert result['execution_time_ms'] < 60000  # Should complete within 60 seconds
        
        print(f"\nExecution time: {result['execution_time_ms']}ms")
