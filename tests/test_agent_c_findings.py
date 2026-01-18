"""
Unit tests for Agent C: Image Findings Extraction

Tests cover:
- Agent initialization
- Findings extraction from images
- Clinical context integration
- Output validation
- Error handling
- Edge cases (missing images, invalid data)
"""

import pytest
import json
from unittest.mock import Mock, patch, mock_open
from app.agents.agent_c_findings import FindingsExtractionAgent


class TestFindingsExtractionAgent:
    """Test suite for FindingsExtractionAgent."""
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly with API key."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            assert agent.agent_name == 'agent_c_findings'
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
        agent = FindingsExtractionAgent(config=config)
        
        assert agent.model == 'gpt-4'
        assert agent.temperature == 0.2
    
    def test_agent_initialization_no_api_key(self):
        """Test that agent raises error when no API key is provided."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                FindingsExtractionAgent()
    
    def test_get_prompt_template(self):
        """Test that prompt template is returned correctly."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            prompt = agent.get_prompt_template()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert 'findings' in prompt.lower()
            assert 'ultrasound' in prompt.lower()
            assert 'JSON' in prompt
    
    def test_get_image_paths_from_list(self):
        """Test extracting image paths from list."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            case_data = {
                'image_paths': ['/path/to/image1.jpg', '/path/to/image2.jpg']
            }
            
            paths = agent._get_image_paths(case_data)
            
            assert len(paths) == 2
            assert '/path/to/image1.jpg' in paths
            assert '/path/to/image2.jpg' in paths
    
    def test_get_image_paths_from_single_path(self):
        """Test extracting image path from legacy single path field."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            case_data = {
                'image_path': '/path/to/image.jpg'
            }
            
            paths = agent._get_image_paths(case_data)
            
            assert len(paths) == 1
            assert paths[0] == '/path/to/image.jpg'
    
    def test_get_image_paths_empty(self):
        """Test extracting image paths when none are provided."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            case_data = {}
            
            paths = agent._get_image_paths(case_data)
            
            assert len(paths) == 0
    
    def test_get_image_paths_filters_none(self):
        """Test that None values are filtered from image paths."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            case_data = {
                'image_paths': ['/path/to/image1.jpg', None, '/path/to/image2.jpg']
            }
            
            paths = agent._get_image_paths(case_data)
            
            assert len(paths) == 2
            assert None not in paths
    
    def test_get_mime_type(self):
        """Test MIME type detection from file extensions."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            assert agent._get_mime_type('.jpg') == 'image/jpeg'
            assert agent._get_mime_type('.jpeg') == 'image/jpeg'
            assert agent._get_mime_type('.png') == 'image/png'
            assert agent._get_mime_type('.gif') == 'image/gif'
            assert agent._get_mime_type('.JPG') == 'image/jpeg'  # Case insensitive
            assert agent._get_mime_type('.unknown') == 'image/jpeg'  # Default
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_encode_images_success(self, mock_exists, mock_file):
        """Test successful image encoding."""
        mock_exists.return_value = True
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            image_paths = ['/path/to/image1.jpg', '/path/to/image2.png']
            encoded = agent._encode_images(image_paths)
            
            assert len(encoded) == 2
            assert encoded[0]['index'] == 0
            assert encoded[0]['path'] == '/path/to/image1.jpg'
            assert encoded[0]['mime_type'] == 'image/jpeg'
            assert 'base64' in encoded[0]
            assert encoded[1]['mime_type'] == 'image/png'
    
    @patch('os.path.exists')
    def test_encode_images_file_not_found(self, mock_exists):
        """Test encoding when image file doesn't exist."""
        mock_exists.return_value = False
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            image_paths = ['/path/to/nonexistent.jpg']
            encoded = agent._encode_images(image_paths)
            
            assert len(encoded) == 0
    
    @patch('builtins.open', side_effect=IOError("Cannot read file"))
    @patch('os.path.exists')
    def test_encode_images_read_error(self, mock_exists, mock_file):
        """Test encoding when file read fails."""
        mock_exists.return_value = True
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            image_paths = ['/path/to/image.jpg']
            encoded = agent._encode_images(image_paths)
            
            assert len(encoded) == 0
    
    def test_format_clinical_context_complete(self):
        """Test formatting clinical context with all fields."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            clinical_context = {
                'clinical_indication': 'Elevated liver enzymes',
                'relevant_history': 'History of chronic liver disease',
                'pertinent_labs': {
                    'ALT': '85 U/L',
                    'AST': '72 U/L'
                },
                'clinical_questions': ['Assess liver parenchyma', 'Rule out focal lesions']
            }
            
            formatted = agent._format_clinical_context(clinical_context)
            
            assert 'Elevated liver enzymes' in formatted
            assert 'chronic liver disease' in formatted
            assert 'ALT: 85 U/L' in formatted
            assert 'Assess liver parenchyma' in formatted
    
    def test_format_clinical_context_partial(self):
        """Test formatting clinical context with some fields missing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            clinical_context = {
                'clinical_indication': 'Abdominal pain',
                'relevant_history': None,
                'pertinent_labs': {},
                'clinical_questions': []
            }
            
            formatted = agent._format_clinical_context(clinical_context)
            
            assert 'Abdominal pain' in formatted
            assert 'History:' not in formatted
    
    def test_format_clinical_context_empty(self):
        """Test formatting clinical context when empty."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            formatted = agent._format_clinical_context({})
            
            assert 'No clinical context provided' in formatted
    
    def test_build_multimodal_content(self):
        """Test building multimodal content for API request."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            encoded_images = [
                {
                    'index': 0,
                    'path': '/path/to/image1.jpg',
                    'base64': 'base64data1',
                    'mime_type': 'image/jpeg'
                }
            ]
            
            context_summary = "Indication: Elevated liver enzymes"
            
            content = agent._build_multimodal_content(encoded_images, context_summary)
            
            assert len(content) == 2  # 1 text + 1 image
            assert content[0]['type'] == 'text'
            assert 'Elevated liver enzymes' in content[0]['text']
            assert '1' in content[0]['text']  # Should mention number of images
            assert content[1]['type'] == 'image_url'
            assert 'data:image/jpeg;base64,base64data1' in content[1]['image_url']['url']
    
    def test_create_minimal_findings(self):
        """Test creation of minimal findings when no images are available."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            minimal = agent._create_minimal_findings()
            
            assert minimal['organ_assessment']['size'] == 'Not assessed - no images available'
            assert minimal['focal_lesions'] == []
            assert minimal['measurements'] == {}
            assert minimal['confidence_assessment']['overall_confidence'] == 0.0
            assert 'No images available' in minimal['confidence_assessment']['limitations'][0]
            assert 'could not be performed' in minimal['summary']
    
    def test_validate_output_valid(self):
        """Test validation of valid output."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            valid_output = {
                'organ_assessment': {
                    'size': 'Normal',
                    'echogenicity': 'Normal',
                    'echotexture': 'Homogeneous',
                    'surface': 'Smooth'
                },
                'focal_lesions': [
                    {
                        'location': 'Right lobe',
                        'size': '2.5 cm',
                        'echogenicity': 'Hypoechoic'
                    }
                ],
                'vascular_findings': {
                    'portal_vein': 'Normal caliber',
                    'hepatic_veins': 'Patent',
                    'abnormalities': []
                },
                'biliary_system': {
                    'intrahepatic_ducts': 'Normal',
                    'common_bile_duct': '5 mm',
                    'abnormalities': []
                },
                'additional_findings': {
                    'ascites': 'Absent',
                    'other': []
                },
                'measurements': {
                    'liver_length': '15 cm'
                },
                'confidence_assessment': {
                    'overall_confidence': 0.85,
                    'limitations': []
                },
                'summary': 'Normal liver with single hypoechoic lesion in right lobe'
            }
            
            assert agent.validate_output(valid_output) is True
    
    def test_validate_output_missing_key(self):
        """Test validation fails when required key is missing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            invalid_output = {
                'organ_assessment': {},
                'focal_lesions': [],
                'vascular_findings': {},
                'biliary_system': {},
                'additional_findings': {},
                'measurements': {}
                # Missing 'confidence_assessment' and 'summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_wrong_type_organ_assessment(self):
        """Test validation fails when organ_assessment has wrong type."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            invalid_output = {
                'organ_assessment': 'not a dict',  # Should be dict
                'focal_lesions': [],
                'vascular_findings': {},
                'biliary_system': {},
                'additional_findings': {},
                'measurements': {},
                'confidence_assessment': {'overall_confidence': 0.8},
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_wrong_type_focal_lesions(self):
        """Test validation fails when focal_lesions has wrong type."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            invalid_output = {
                'organ_assessment': {},
                'focal_lesions': 'not a list',  # Should be list
                'vascular_findings': {},
                'biliary_system': {},
                'additional_findings': {},
                'measurements': {},
                'confidence_assessment': {'overall_confidence': 0.8},
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_focal_lesion_not_dict(self):
        """Test validation fails when focal lesion is not a dictionary."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            invalid_output = {
                'organ_assessment': {},
                'focal_lesions': ['not a dict'],  # Should be list of dicts
                'vascular_findings': {},
                'biliary_system': {},
                'additional_findings': {},
                'measurements': {},
                'confidence_assessment': {'overall_confidence': 0.8},
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_confidence_out_of_range(self):
        """Test validation fails when confidence is out of range."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            invalid_output = {
                'organ_assessment': {},
                'focal_lesions': [],
                'vascular_findings': {},
                'biliary_system': {},
                'additional_findings': {},
                'measurements': {},
                'confidence_assessment': {
                    'overall_confidence': 1.5  # Out of range
                },
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_confidence_negative(self):
        """Test validation fails when confidence is negative."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            invalid_output = {
                'organ_assessment': {},
                'focal_lesions': [],
                'vascular_findings': {},
                'biliary_system': {},
                'additional_findings': {},
                'measurements': {},
                'confidence_assessment': {
                    'overall_confidence': -0.1  # Negative
                },
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_empty_summary(self):
        """Test validation fails when summary is empty."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            invalid_output = {
                'organ_assessment': {},
                'focal_lesions': [],
                'vascular_findings': {},
                'biliary_system': {},
                'additional_findings': {},
                'measurements': {},
                'confidence_assessment': {'overall_confidence': 0.8},
                'summary': ''  # Empty summary
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_not_dict(self):
        """Test validation fails when output is not a dictionary."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            assert agent.validate_output("not a dict") is False
            assert agent.validate_output([]) is False
            assert agent.validate_output(None) is False
    
    @patch('app.agents.agent_c_findings.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_process_success(self, mock_exists, mock_file, mock_openai_class):
        """Test successful processing of findings extraction."""
        mock_exists.return_value = True
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'organ_assessment': {
                'size': 'Normal (15 cm craniocaudal)',
                'echogenicity': 'Normal',
                'echotexture': 'Homogeneous',
                'surface': 'Smooth'
            },
            'focal_lesions': [
                {
                    'location': 'Segment 7, right lobe',
                    'size': '2.3 cm',
                    'echogenicity': 'Hypoechoic',
                    'margins': 'Well-defined',
                    'characteristics': 'Solid',
                    'posterior_acoustic': 'None',
                    'description': 'Well-defined hypoechoic solid lesion'
                }
            ],
            'vascular_findings': {
                'portal_vein': 'Normal caliber (12 mm), patent',
                'hepatic_veins': 'Patent, normal size',
                'abnormalities': []
            },
            'biliary_system': {
                'intrahepatic_ducts': 'Normal, not dilated',
                'common_bile_duct': '5 mm (normal)',
                'abnormalities': []
            },
            'additional_findings': {
                'ascites': 'Absent',
                'other': []
            },
            'measurements': {
                'liver_length': '15 cm',
                'portal_vein_diameter': '12 mm',
                'cbd_diameter': '5 mm'
            },
            'confidence_assessment': {
                'overall_confidence': 0.88,
                'limitations': []
            },
            'summary': 'Normal liver parenchyma with single well-defined hypoechoic lesion in segment 7 measuring 2.3 cm'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/liver_image.jpg']
                },
                'clinical_context': {
                    'clinical_indication': 'Elevated liver enzymes',
                    'relevant_history': 'History of chronic liver disease'
                }
            }
            
            result = agent.process(input_data)
            
            assert result['organ_assessment']['size'] == 'Normal (15 cm craniocaudal)'
            assert len(result['focal_lesions']) == 1
            assert result['focal_lesions'][0]['size'] == '2.3 cm'
            assert result['vascular_findings']['portal_vein'] == 'Normal caliber (12 mm), patent'
            assert result['confidence_assessment']['overall_confidence'] == 0.88
            assert result['summary'] is not None
    
    @patch('app.agents.agent_c_findings.OpenAI')
    def test_process_no_images(self, mock_openai_class):
        """Test processing when no images are provided."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': []
                }
            }
            
            result = agent.process(input_data)
            
            # Should return minimal findings without calling API
            assert result['organ_assessment']['size'] == 'Not assessed - no images available'
            assert result['focal_lesions'] == []
            assert result['confidence_assessment']['overall_confidence'] == 0.0
            
            # Verify API was not called
            mock_client.chat.completions.create.assert_not_called()
    
    @patch('app.agents.agent_c_findings.OpenAI')
    @patch('os.path.exists')
    def test_process_images_not_found(self, mock_exists, mock_openai_class):
        """Test processing when image files don't exist."""
        mock_exists.return_value = False
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/nonexistent.jpg']
                }
            }
            
            result = agent.process(input_data)
            
            # Should return minimal findings when encoding fails
            assert result['focal_lesions'] == []
            
            # Verify API was not called
            mock_client.chat.completions.create.assert_not_called()
    
    @patch('app.agents.agent_c_findings.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_process_api_error(self, mock_exists, mock_file, mock_openai_class):
        """Test handling of API errors."""
        mock_exists.return_value = True
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/image.jpg']
                }
            }
            
            with pytest.raises(Exception, match="Failed to extract findings"):
                agent.process(input_data)
    
    @patch('app.agents.agent_c_findings.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_process_invalid_json_response(self, mock_exists, mock_file, mock_openai_class):
        """Test handling of invalid JSON response from API."""
        mock_exists.return_value = True
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Not valid JSON"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/image.jpg']
                }
            }
            
            with pytest.raises(ValueError, match="Invalid JSON response"):
                agent.process(input_data)
    
    @patch('app.agents.agent_c_findings.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_execute_success(self, mock_exists, mock_file, mock_openai_class):
        """Test successful execution through base agent execute method."""
        mock_exists.return_value = True
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'organ_assessment': {'size': 'Normal'},
            'focal_lesions': [],
            'vascular_findings': {'portal_vein': 'Normal', 'hepatic_veins': 'Normal', 'abnormalities': []},
            'biliary_system': {'intrahepatic_ducts': 'Normal', 'common_bile_duct': 'Normal', 'abnormalities': []},
            'additional_findings': {'ascites': 'Absent', 'other': []},
            'measurements': {},
            'confidence_assessment': {'overall_confidence': 0.9},
            'summary': 'Normal findings'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/image.jpg']
                }
            }
            
            result = agent.execute(input_data)
            
            assert result['success'] is True
            assert result['output'] is not None
            assert result['error'] is None
            assert result['execution_time_ms'] >= 0
    
    @patch('app.agents.agent_c_findings.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_execute_failure(self, mock_exists, mock_file, mock_openai_class):
        """Test execution failure through base agent execute method."""
        mock_exists.return_value = True
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = FindingsExtractionAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/image.jpg']
                }
            }
            
            result = agent.execute(input_data)
            
            assert result['success'] is False
            assert result['output'] is None
            assert result['error'] is not None
            assert 'Failed to extract findings' in result['error']
