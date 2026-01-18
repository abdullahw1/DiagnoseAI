"""
Integration tests for Agent C: Image Findings Extraction

Tests the agent with sample ultrasound images and validates
the findings extraction against expected results.
"""

import pytest
import os
from unittest.mock import patch, Mock
import json
from app.agents.agent_c_findings import FindingsExtractionAgent


class TestFindingsExtractionIntegration:
    """Integration test suite for FindingsExtractionAgent."""
    
    @pytest.fixture
    def sample_image_path(self):
        """Get path to a sample ultrasound image for testing."""
        # Use an actual test image from the uploads directory
        test_image = 'instance/uploads/ai_tests/1/ai_test_20260106_231433_934350_COARSE_lLIVER.jpg'
        if os.path.exists(test_image):
            return test_image
        # Fallback to any available image
        uploads_dir = 'instance/uploads/1'
        if os.path.exists(uploads_dir):
            images = [f for f in os.listdir(uploads_dir) if f.endswith(('.jpg', '.png'))]
            if images:
                return os.path.join(uploads_dir, images[0])
        return None
    
    @patch('app.agents.agent_c_findings.OpenAI')
    def test_findings_extraction_with_clinical_context(self, mock_openai_class, sample_image_path):
        """Test findings extraction with clinical context integration."""
        if not sample_image_path or not os.path.exists(sample_image_path):
            pytest.skip("No sample image available for integration test")
        
        # Mock OpenAI response with realistic findings
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'organ_assessment': {
                'size': 'Normal (14.5 cm craniocaudal)',
                'echogenicity': 'Increased echogenicity',
                'echotexture': 'Coarse, heterogeneous',
                'surface': 'Mildly nodular'
            },
            'focal_lesions': [],
            'vascular_findings': {
                'portal_vein': 'Normal caliber (11 mm), patent with hepatopetal flow',
                'hepatic_veins': 'Patent, normal caliber',
                'abnormalities': []
            },
            'biliary_system': {
                'intrahepatic_ducts': 'Normal, not dilated',
                'common_bile_duct': 'Not well visualized in this view',
                'abnormalities': []
            },
            'additional_findings': {
                'ascites': 'Absent',
                'other': ['Increased parenchymal echogenicity consistent with fatty infiltration']
            },
            'measurements': {
                'liver_length': '14.5 cm',
                'portal_vein_diameter': '11 mm'
            },
            'confidence_assessment': {
                'overall_confidence': 0.85,
                'limitations': ['Limited views', 'Suboptimal acoustic window']
            },
            'summary': 'Liver demonstrates increased echogenicity with coarse echotexture and mildly nodular surface, consistent with chronic liver disease. No focal lesions identified. Portal vein patent.'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            # Prepare input with clinical context
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': [sample_image_path]
                },
                'clinical_context': {
                    'clinical_indication': 'Elevated liver enzymes, assess for chronic liver disease',
                    'relevant_history': 'History of chronic hepatitis C, alcohol use',
                    'pertinent_labs': {
                        'ALT': '95 U/L (elevated)',
                        'AST': '110 U/L (elevated)',
                        'Bilirubin': '1.8 mg/dL (elevated)'
                    },
                    'risk_factors': ['Chronic hepatitis C', 'Alcohol use', 'Elevated liver enzymes'],
                    'clinical_questions': ['Assess for cirrhosis', 'Rule out focal lesions']
                }
            }
            
            # Execute the agent
            result = agent.execute(input_data)
            
            # Verify execution was successful
            assert result['success'] is True
            assert result['output'] is not None
            assert result['error'] is None
            
            # Verify output structure
            output = result['output']
            assert 'organ_assessment' in output
            assert 'focal_lesions' in output
            assert 'vascular_findings' in output
            assert 'biliary_system' in output
            assert 'additional_findings' in output
            assert 'measurements' in output
            assert 'confidence_assessment' in output
            assert 'summary' in output
            
            # Verify organ assessment details
            assert output['organ_assessment']['echogenicity'] == 'Increased echogenicity'
            assert output['organ_assessment']['echotexture'] == 'Coarse, heterogeneous'
            
            # Verify measurements
            assert 'liver_length' in output['measurements']
            
            # Verify confidence assessment
            assert 0 <= output['confidence_assessment']['overall_confidence'] <= 1
            
            # Verify summary is present
            assert len(output['summary']) > 0
            assert 'liver' in output['summary'].lower()
    
    @patch('app.agents.agent_c_findings.OpenAI')
    def test_findings_extraction_with_focal_lesion(self, mock_openai_class, sample_image_path):
        """Test findings extraction when focal lesion is present."""
        if not sample_image_path or not os.path.exists(sample_image_path):
            pytest.skip("No sample image available for integration test")
        
        # Mock OpenAI response with focal lesion
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'organ_assessment': {
                'size': 'Normal (15 cm)',
                'echogenicity': 'Normal',
                'echotexture': 'Homogeneous',
                'surface': 'Smooth'
            },
            'focal_lesions': [
                {
                    'location': 'Segment 7, posterior right lobe',
                    'size': '2.8 cm x 2.3 cm',
                    'echogenicity': 'Hypoechoic',
                    'margins': 'Well-defined',
                    'characteristics': 'Solid, homogeneous',
                    'posterior_acoustic': 'Mild posterior enhancement',
                    'description': 'Well-defined hypoechoic solid lesion with mild posterior acoustic enhancement, likely represents hemangioma'
                }
            ],
            'vascular_findings': {
                'portal_vein': 'Normal caliber (12 mm), patent',
                'hepatic_veins': 'Patent',
                'abnormalities': []
            },
            'biliary_system': {
                'intrahepatic_ducts': 'Normal',
                'common_bile_duct': '5 mm (normal)',
                'abnormalities': []
            },
            'additional_findings': {
                'ascites': 'Absent',
                'other': []
            },
            'measurements': {
                'liver_length': '15 cm',
                'lesion_size': '2.8 x 2.3 cm',
                'portal_vein_diameter': '12 mm',
                'cbd_diameter': '5 mm'
            },
            'confidence_assessment': {
                'overall_confidence': 0.82,
                'limitations': ['Lesion characterization limited without contrast or MRI correlation']
            },
            'summary': 'Normal liver parenchyma with single well-defined hypoechoic lesion in segment 7 measuring 2.8 cm, likely hemangioma. Recommend MRI for further characterization.'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 2,
                'case_data': {
                    'image_paths': [sample_image_path]
                },
                'clinical_context': {
                    'clinical_indication': 'Incidental finding on CT, characterize liver lesion',
                    'relevant_history': 'No significant liver disease history'
                }
            }
            
            result = agent.execute(input_data)
            
            assert result['success'] is True
            output = result['output']
            
            # Verify focal lesion was detected
            assert len(output['focal_lesions']) == 1
            lesion = output['focal_lesions'][0]
            
            # Verify lesion details
            assert 'location' in lesion
            assert 'size' in lesion
            assert 'echogenicity' in lesion
            assert 'Hypoechoic' in lesion['echogenicity']
            assert 'description' in lesion
            
            # Verify measurements include lesion size
            assert 'lesion_size' in output['measurements']
            
            # Verify summary mentions the lesion
            assert 'lesion' in output['summary'].lower()
    
    @patch('app.agents.agent_c_findings.OpenAI')
    def test_findings_extraction_normal_study(self, mock_openai_class, sample_image_path):
        """Test findings extraction for normal study."""
        if not sample_image_path or not os.path.exists(sample_image_path):
            pytest.skip("No sample image available for integration test")
        
        # Mock OpenAI response for normal findings
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'organ_assessment': {
                'size': 'Normal (14 cm craniocaudal)',
                'echogenicity': 'Normal',
                'echotexture': 'Homogeneous',
                'surface': 'Smooth'
            },
            'focal_lesions': [],
            'vascular_findings': {
                'portal_vein': 'Normal caliber (11 mm), patent with hepatopetal flow',
                'hepatic_veins': 'Patent, normal caliber',
                'abnormalities': []
            },
            'biliary_system': {
                'intrahepatic_ducts': 'Normal, not dilated',
                'common_bile_duct': '4 mm (normal)',
                'abnormalities': []
            },
            'additional_findings': {
                'ascites': 'Absent',
                'other': []
            },
            'measurements': {
                'liver_length': '14 cm',
                'portal_vein_diameter': '11 mm',
                'cbd_diameter': '4 mm'
            },
            'confidence_assessment': {
                'overall_confidence': 0.92,
                'limitations': []
            },
            'summary': 'Normal liver ultrasound. No focal lesions, no biliary dilatation, patent vasculature.'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 3,
                'case_data': {
                    'image_paths': [sample_image_path]
                },
                'clinical_context': {
                    'clinical_indication': 'Routine screening',
                    'relevant_history': 'No significant medical history'
                }
            }
            
            result = agent.execute(input_data)
            
            assert result['success'] is True
            output = result['output']
            
            # Verify normal findings
            assert output['organ_assessment']['echogenicity'] == 'Normal'
            assert output['organ_assessment']['surface'] == 'Smooth'
            assert len(output['focal_lesions']) == 0
            assert len(output['vascular_findings']['abnormalities']) == 0
            assert len(output['biliary_system']['abnormalities']) == 0
            assert output['additional_findings']['ascites'] == 'Absent'
            
            # Verify high confidence for normal study
            assert output['confidence_assessment']['overall_confidence'] > 0.8
            
            # Verify summary indicates normal findings
            assert 'normal' in output['summary'].lower()
    
    def test_findings_extraction_without_clinical_context(self, sample_image_path):
        """Test findings extraction without clinical context."""
        if not sample_image_path or not os.path.exists(sample_image_path):
            pytest.skip("No sample image available for integration test")
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            # Test that agent can handle missing clinical context
            input_data = {
                'case_id': 4,
                'case_data': {
                    'image_paths': [sample_image_path]
                }
                # No clinical_context provided
            }
            
            # Should not raise an error
            # The agent should format an empty clinical context
            context_summary = agent._format_clinical_context({})
            assert 'No clinical context provided' in context_summary
    
    def test_findings_extraction_multiple_images(self):
        """Test findings extraction with multiple images."""
        # Find multiple test images
        uploads_dir = 'instance/uploads/ai_tests/1'
        if not os.path.exists(uploads_dir):
            pytest.skip("No test images directory available")
        
        images = [os.path.join(uploads_dir, f) for f in os.listdir(uploads_dir) 
                  if f.endswith(('.jpg', '.png'))][:3]  # Take up to 3 images
        
        if len(images) < 2:
            pytest.skip("Not enough test images available")
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            # Test encoding multiple images
            encoded = agent._encode_images(images)
            
            # Verify all images were encoded
            assert len(encoded) == len(images)
            
            # Verify each encoded image has required fields
            for idx, img in enumerate(encoded):
                assert img['index'] == idx
                assert 'base64' in img
                assert 'mime_type' in img
                assert img['path'] in images
