"""
Integration tests for Agent F: Safety and Consistency Validation

Tests the safety validation agent with realistic scenarios including:
- Complete valid reports
- Reports with consistency issues
- Reports with missing critical findings
- Reports with safety concerns
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from app.agents.agent_f_safety import SafetyValidationAgent


class TestSafetyValidationAgentIntegration:
    """Integration test suite for SafetyValidationAgent"""
    
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
    def complete_valid_case(self):
        """Complete case with all agent outputs - should pass validation"""
        return {
            "case_id": 1,
            "clinical_context": {
                "clinical_indication": "Elevated liver enzymes, assess for hepatic pathology",
                "relevant_history": "Patient with chronic hepatitis C, alcohol use history",
                "pertinent_labs": {
                    "ALT": "120 U/L (elevated)",
                    "AST": "95 U/L (elevated)",
                    "Bilirubin": "1.2 mg/dL (normal)"
                },
                "risk_factors": ["Chronic hepatitis C", "Alcohol use"],
                "clinical_questions": ["Assess for cirrhosis", "Evaluate for focal lesions"]
            },
            "quality_assessment": {
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
            },
            "findings": {
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
            },
            "diagnostic_reasoning": {
                "differential_diagnosis": [
                    {
                        "diagnosis": "Hepatocellular carcinoma",
                        "likelihood": "moderate",
                        "supporting_findings": ["Focal lesion in cirrhotic liver"],
                        "contradicting_findings": [],
                        "reasoning": "Focal lesion in setting of chronic liver disease",
                        "clinical_significance": "Requires further characterization"
                    },
                    {
                        "diagnosis": "Cirrhosis",
                        "likelihood": "high",
                        "supporting_findings": ["Coarse echotexture", "Nodular surface"],
                        "contradicting_findings": [],
                        "reasoning": "Imaging features consistent with cirrhotic morphology",
                        "clinical_significance": "Established cirrhosis"
                    }
                ],
                "primary_diagnosis": "Cirrhosis with focal hepatic lesion",
                "key_findings_summary": ["Coarse liver", "Focal lesion"],
                "clinical_correlation": "Findings correlate with clinical history",
                "recommendations": {
                    "follow_up_imaging": ["MRI liver with contrast"],
                    "clinical_follow_up": ["Hepatology consultation"],
                    "additional_workup": ["AFP level"]
                },
                "confidence_assessment": {
                    "diagnostic_confidence": 0.8,
                    "factors_affecting_confidence": ["Lesion requires contrast imaging"]
                }
            },
            "draft_report": {
                "report_sections": {
                    "clinical_history": "Patient with chronic hepatitis C and elevated liver enzymes.",
                    "technique": "Grayscale ultrasound of the liver. Image quality was good.",
                    "findings": "The liver demonstrates coarse echotexture with nodular surface. A 2.3 cm hypoechoic lesion is seen in the right lobe, segment 7. Portal vein is patent. No bile duct dilation.",
                    "impression": "1. Cirrhosis\n2. Focal hepatic lesion requiring further characterization\n\nRECOMMENDATIONS:\n- MRI liver with contrast\n- Hepatology consultation\n- AFP level"
                },
                "structured_data": {
                    "primary_diagnosis": "Cirrhosis with focal hepatic lesion",
                    "secondary_diagnoses": ["Hepatocellular carcinoma (cannot exclude)"],
                    "key_findings": ["Coarse liver", "Focal lesion"],
                    "recommendations": ["MRI liver with contrast", "Hepatology consultation", "AFP level"],
                    "critical_findings": ["Focal hepatic lesion in cirrhotic liver"]
                },
                "report_metadata": {
                    "study_type": "Ultrasound liver",
                    "quality_assessment": "good",
                    "confidence_level": "moderate",
                    "limitations": ["Limited visualization of posterior segments"]
                },
                "full_report_text": "Complete report text...",
                "summary": "Cirrhotic liver with focal lesion requiring further characterization"
            }
        }
    
    @pytest.fixture
    def case_with_consistency_issue(self):
        """Case where findings don't match impression - should flag consistency issue"""
        return {
            "case_id": 2,
            "clinical_context": {"clinical_indication": "Abdominal pain"},
            "quality_assessment": {"overall_quality": "good"},
            "findings": {
                "organ_assessment": {
                    "size": "Normal",
                    "echogenicity": "Normal",
                    "echotexture": "Homogeneous",
                    "surface": "Smooth"
                },
                "focal_lesions": [
                    {
                        "location": "Right lobe",
                        "size": "3.5 cm",
                        "echogenicity": "Hyperechoic",
                        "characteristics": "Solid mass"
                    }
                ],
                "summary": "Large hyperechoic mass in right lobe"
            },
            "diagnostic_reasoning": {
                "primary_diagnosis": "Hepatic mass, likely hemangioma",
                "differential_diagnosis": [],
                "key_findings_summary": ["Large hyperechoic mass"],
                "recommendations": {"follow_up_imaging": ["MRI for characterization"]}
            },
            "draft_report": {
                "report_sections": {
                    "clinical_history": "Abdominal pain",
                    "technique": "Ultrasound",
                    "findings": "The liver is normal in size and echogenicity.",
                    "impression": "Normal liver ultrasound. No focal lesions identified."
                },
                "structured_data": {
                    "primary_diagnosis": "Normal liver",
                    "key_findings": ["Normal liver"],
                    "critical_findings": []
                },
                "full_report_text": "Normal study",
                "summary": "Normal liver"
            }
        }
    
    @pytest.fixture
    def case_with_missing_critical_finding(self):
        """Case where critical finding is not flagged - should fail safety check"""
        return {
            "case_id": 3,
            "clinical_context": {"clinical_indication": "Follow-up imaging"},
            "quality_assessment": {"overall_quality": "good"},
            "findings": {
                "vascular_findings": {
                    "portal_vein": "Thrombosed, no flow detected",
                    "abnormalities": ["Portal vein thrombosis"]
                },
                "summary": "Portal vein thrombosis identified"
            },
            "diagnostic_reasoning": {
                "primary_diagnosis": "Portal vein thrombosis",
                "differential_diagnosis": [],
                "key_findings_summary": ["Portal vein thrombosis"],
                "recommendations": {"clinical_follow_up": ["Urgent clinical correlation"]}
            },
            "draft_report": {
                "report_sections": {
                    "clinical_history": "Follow-up imaging",
                    "technique": "Ultrasound",
                    "findings": "Portal vein demonstrates reduced flow.",
                    "impression": "Reduced portal vein flow. Clinical correlation recommended."
                },
                "structured_data": {
                    "primary_diagnosis": "Reduced portal vein flow",
                    "critical_findings": [],
                    "recommendations": ["Clinical correlation"]
                },
                "full_report_text": "Reduced flow",
                "summary": "Reduced portal vein flow"
            }
        }
    
    @patch('app.agents.agent_f_safety.OpenAI')
    def test_validation_of_complete_valid_case(self, mock_openai_class, agent, complete_valid_case):
        """Test validation of a complete, well-structured case"""
        # Mock successful validation response
        validation_response = {
            "validation_status": "pass",
            "overall_confidence_score": 0.85,
            "consistency_checks": {
                "findings_impression_match": {
                    "status": "pass",
                    "issues": [],
                    "details": "All findings appropriately reflected in impression"
                },
                "internal_consistency": {
                    "status": "pass",
                    "issues": [],
                    "details": "No contradictions found"
                },
                "clinical_correlation": {
                    "status": "pass",
                    "issues": [],
                    "details": "Findings correlate with clinical presentation"
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
                "factors_reducing_confidence": ["Lesion requires contrast imaging"],
                "factors_increasing_confidence": ["Clear imaging findings"]
            },
            "issues_found": [],
            "recommendations_for_improvement": [],
            "validation_summary": "Report is well-structured and complete"
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(validation_response)
        mock_client.chat.completions.create.return_value = mock_response
        agent.client = mock_client
        
        # Execute validation
        result = agent.execute(complete_valid_case)
        
        # Verify successful validation
        assert result['success'] is True
        assert result['output']['validation_status'] == 'pass'
        assert result['output']['overall_confidence_score'] >= 0.8
        assert len(result['output']['safety_flags']['critical_findings']) > 0
        assert result['output']['safety_flags']['urgent_follow_up_needed'] is True
    
    @patch('app.agents.agent_f_safety.OpenAI')
    def test_validation_detects_consistency_issue(self, mock_openai_class, agent, case_with_consistency_issue):
        """Test that validation detects inconsistency between findings and impression"""
        # Mock validation response with consistency issue
        validation_response = {
            "validation_status": "fail",
            "overall_confidence_score": 0.3,
            "consistency_checks": {
                "findings_impression_match": {
                    "status": "fail",
                    "issues": ["Large mass mentioned in findings but not in impression"],
                    "details": "Critical inconsistency: 3.5 cm mass described in findings but impression states no focal lesions"
                },
                "internal_consistency": {
                    "status": "fail",
                    "issues": ["Contradictory statements"],
                    "details": "Findings describe mass, impression says normal"
                },
                "clinical_correlation": {
                    "status": "pass",
                    "issues": [],
                    "details": "Clinical correlation adequate"
                }
            },
            "completeness_checks": {
                "required_sections": {
                    "status": "pass",
                    "missing_sections": [],
                    "details": "All sections present"
                },
                "findings_coverage": {
                    "status": "fail",
                    "missing_findings": ["3.5 cm hyperechoic mass not addressed in impression"],
                    "details": "Significant finding omitted from impression"
                },
                "recommendations": {
                    "status": "fail",
                    "issues": ["No recommendations for mass characterization"],
                    "details": "Mass requires follow-up but no recommendations provided"
                }
            },
            "safety_flags": {
                "critical_findings": ["Unaddressed hepatic mass"],
                "urgent_follow_up_needed": True,
                "potential_malignancy": True,
                "safety_issues": ["Critical finding not mentioned in impression"],
                "risk_level": "high"
            },
            "quality_assessment": {
                "report_clarity": 0.4,
                "terminology_accuracy": 0.7,
                "organization": 0.5,
                "actionability": 0.2,
                "quality_issues": ["Major inconsistency between sections"]
            },
            "confidence_factors": {
                "image_quality_impact": 0.8,
                "diagnostic_certainty": 0.3,
                "data_completeness": 0.6,
                "factors_reducing_confidence": ["Major inconsistency in report", "Critical finding omitted"],
                "factors_increasing_confidence": []
            },
            "issues_found": [
                {
                    "severity": "critical",
                    "category": "consistency",
                    "description": "3.5 cm hepatic mass described in findings but not mentioned in impression",
                    "location": "Impression section",
                    "recommendation": "Add mass to impression with appropriate differential diagnosis and recommendations"
                }
            ],
            "recommendations_for_improvement": [
                "Include all significant findings in impression",
                "Provide recommendations for mass characterization"
            ],
            "validation_summary": "Critical consistency issue: significant finding omitted from impression"
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(validation_response)
        mock_client.chat.completions.create.return_value = mock_response
        agent.client = mock_client
        
        # Execute validation
        result = agent.execute(case_with_consistency_issue)
        
        # Verify consistency issue detected
        assert result['success'] is True
        assert result['output']['validation_status'] == 'fail'
        assert result['output']['consistency_checks']['findings_impression_match']['status'] == 'fail'
        assert len(result['output']['issues_found']) > 0
        assert any(issue['severity'] == 'critical' for issue in result['output']['issues_found'])
        assert result['output']['safety_flags']['risk_level'] == 'high'
    
    @patch('app.agents.agent_f_safety.OpenAI')
    def test_validation_detects_missing_critical_finding(self, mock_openai_class, agent, case_with_missing_critical_finding):
        """Test that validation detects when critical findings are not properly flagged"""
        # Mock validation response with safety issue
        validation_response = {
            "validation_status": "fail",
            "overall_confidence_score": 0.4,
            "consistency_checks": {
                "findings_impression_match": {
                    "status": "warning",
                    "issues": ["Severity of finding understated"],
                    "details": "Portal vein thrombosis described as 'reduced flow'"
                },
                "internal_consistency": {
                    "status": "pass",
                    "issues": [],
                    "details": "No contradictions"
                },
                "clinical_correlation": {
                    "status": "pass",
                    "issues": [],
                    "details": "Adequate"
                }
            },
            "completeness_checks": {
                "required_sections": {
                    "status": "pass",
                    "missing_sections": [],
                    "details": "All sections present"
                },
                "findings_coverage": {
                    "status": "warning",
                    "missing_findings": [],
                    "details": "Finding addressed but severity understated"
                },
                "recommendations": {
                    "status": "fail",
                    "issues": ["Inadequate urgency in recommendations"],
                    "details": "Portal vein thrombosis requires urgent evaluation, not just 'clinical correlation'"
                }
            },
            "safety_flags": {
                "critical_findings": ["Portal vein thrombosis"],
                "urgent_follow_up_needed": True,
                "potential_malignancy": False,
                "safety_issues": [
                    "Critical finding not flagged as urgent",
                    "Inadequate recommendations for urgent condition"
                ],
                "risk_level": "high"
            },
            "quality_assessment": {
                "report_clarity": 0.6,
                "terminology_accuracy": 0.7,
                "organization": 0.7,
                "actionability": 0.3,
                "quality_issues": ["Understated severity of critical finding"]
            },
            "confidence_factors": {
                "image_quality_impact": 0.8,
                "diagnostic_certainty": 0.7,
                "data_completeness": 0.8,
                "factors_reducing_confidence": ["Critical finding not properly emphasized"],
                "factors_increasing_confidence": []
            },
            "issues_found": [
                {
                    "severity": "critical",
                    "category": "safety",
                    "description": "Portal vein thrombosis is a critical finding requiring urgent evaluation but is described as 'reduced flow'",
                    "location": "Findings and Impression sections",
                    "recommendation": "Clearly state 'portal vein thrombosis' and recommend urgent clinical evaluation"
                },
                {
                    "severity": "major",
                    "category": "completeness",
                    "description": "Recommendations inadequate for urgent finding",
                    "location": "Impression section",
                    "recommendation": "Add urgent follow-up recommendations including immediate clinical notification"
                }
            ],
            "recommendations_for_improvement": [
                "Use clear, direct language for critical findings",
                "Provide urgent recommendations appropriate to severity",
                "Flag critical findings explicitly in structured data"
            ],
            "validation_summary": "Critical safety issue: portal vein thrombosis not properly emphasized or flagged"
        }
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(validation_response)
        mock_client.chat.completions.create.return_value = mock_response
        agent.client = mock_client
        
        # Execute validation
        result = agent.execute(case_with_missing_critical_finding)
        
        # Verify safety issue detected
        assert result['success'] is True
        assert result['output']['validation_status'] == 'fail'
        assert len(result['output']['safety_flags']['safety_issues']) > 0
        assert result['output']['safety_flags']['urgent_follow_up_needed'] is True
        assert result['output']['safety_flags']['risk_level'] == 'high'
        assert any(issue['category'] == 'safety' for issue in result['output']['issues_found'])
