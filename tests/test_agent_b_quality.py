"""
Unit tests for Agent B: View Identification and Quality Assessment

Tests cover:
- Agent initialization
- Image quality assessment
- View identification
- Output validation
- Error handling
- Edge cases (missing images, invalid paths)
"""

import pytest
import json
import base64
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from app.agents.agent_b_quality import QualityAssessmentAgent


class TestQualityAssessmentAgent:
    """Test suite for QualityAssessmentAgent."""
    
    def test_agent_initialization(self):
        """Test that agent initializes correctly with API key."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            assert agent.agent_name == 'agent_b_quality'
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
        agent = QualityAssessmentAgent(config=config)
        
        assert agent.model == 'gpt-4'
        assert agent.temperature == 0.2
    
    def test_agent_initialization_no_api_key(self):
        """Test that agent raises error when no API key is provided."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not found"):
                QualityAssessmentAgent()
    
    def test_get_prompt_template(self):
        """Test that prompt template is returned correctly."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            prompt = agent.get_prompt_template()
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            assert 'ultrasound' in prompt.lower()
            assert 'quality' in prompt.lower()
            assert 'JSON' in prompt
            assert 'view' in prompt.lower()
    
    def test_get_image_paths_from_list(self):
        """Test extracting image paths from list."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
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
            agent = QualityAssessmentAgent()
            
            case_data = {
                'image_path': '/path/to/image.jpg'
            }
            
            paths = agent._get_image_paths(case_data)
            
            assert len(paths) == 1
            assert paths[0] == '/path/to/image.jpg'
    
    def test_get_image_paths_empty(self):
        """Test extracting image paths when none are provided."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            case_data = {}
            
            paths = agent._get_image_paths(case_data)
            
            assert len(paths) == 0
    
    def test_get_image_paths_filters_none(self):
        """Test that None values are filtered from image paths."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            case_data = {
                'image_paths': ['/path/to/image1.jpg', None, '/path/to/image2.jpg']
            }
            
            paths = agent._get_image_paths(case_data)
            
            assert len(paths) == 2
            assert None not in paths
    
    def test_get_mime_type(self):
        """Test MIME type detection from file extensions."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
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
            agent = QualityAssessmentAgent()
            
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
            agent = QualityAssessmentAgent()
            
            image_paths = ['/path/to/nonexistent.jpg']
            encoded = agent._encode_images(image_paths)
            
            assert len(encoded) == 0
    
    @patch('builtins.open', side_effect=IOError("Cannot read file"))
    @patch('os.path.exists')
    def test_encode_images_read_error(self, mock_exists, mock_file):
        """Test encoding when file read fails."""
        mock_exists.return_value = True
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            image_paths = ['/path/to/image.jpg']
            encoded = agent._encode_images(image_paths)
            
            assert len(encoded) == 0
    
    def test_build_multimodal_content(self):
        """Test building multimodal content for API request."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            encoded_images = [
                {
                    'index': 0,
                    'path': '/path/to/image1.jpg',
                    'base64': 'base64data1',
                    'mime_type': 'image/jpeg'
                },
                {
                    'index': 1,
                    'path': '/path/to/image2.png',
                    'base64': 'base64data2',
                    'mime_type': 'image/png'
                }
            ]
            
            content = agent._build_multimodal_content(encoded_images)
            
            assert len(content) == 3  # 1 text + 2 images
            assert content[0]['type'] == 'text'
            assert '2' in content[0]['text']  # Should mention number of images
            assert content[1]['type'] == 'image_url'
            assert 'data:image/jpeg;base64,base64data1' in content[1]['image_url']['url']
            assert content[2]['type'] == 'image_url'
            assert 'data:image/png;base64,base64data2' in content[2]['image_url']['url']
    
    def test_create_minimal_assessment(self):
        """Test creation of minimal assessment when no images are available."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            minimal = agent._create_minimal_assessment()
            
            assert minimal['images'] == []
            assert 'No images' in minimal['overall_quality']
            assert 'could not be performed' in minimal['summary']
    
    def test_validate_output_valid(self):
        """Test validation of valid output."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            valid_output = {
                'images': [
                    {
                        'image_index': 0,
                        'view_identified': 'Sagittal Right Lobe Liver',
                        'view_confidence': 0.95,
                        'quality_score': 85,
                        'technical_assessment': {
                            'resolution': 'good',
                            'contrast': 'excellent'
                        },
                        'artifacts': [],
                        'limitations': [],
                        'diagnostic_adequacy': 'adequate',
                        'recommendations': 'None'
                    }
                ],
                'overall_quality': 'Good quality images',
                'summary': 'Images are adequate for diagnostic interpretation'
            }
            
            assert agent.validate_output(valid_output) is True
    
    def test_validate_output_missing_key(self):
        """Test validation fails when required key is missing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            invalid_output = {
                'images': [],
                'overall_quality': 'Good'
                # Missing 'summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_images_not_list(self):
        """Test validation fails when images is not a list."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            invalid_output = {
                'images': 'not a list',
                'overall_quality': 'Good',
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_image_missing_required_key(self):
        """Test validation fails when image assessment is missing required key."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            invalid_output = {
                'images': [
                    {
                        'image_index': 0,
                        'view_identified': 'Liver',
                        'quality_score': 85
                        # Missing 'diagnostic_adequacy'
                    }
                ],
                'overall_quality': 'Good',
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_quality_score_out_of_range(self):
        """Test validation fails when quality score is out of range."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            invalid_output = {
                'images': [
                    {
                        'image_index': 0,
                        'view_identified': 'Liver',
                        'quality_score': 150,  # Out of range
                        'diagnostic_adequacy': 'adequate'
                    }
                ],
                'overall_quality': 'Good',
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_quality_score_negative(self):
        """Test validation fails when quality score is negative."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            invalid_output = {
                'images': [
                    {
                        'image_index': 0,
                        'view_identified': 'Liver',
                        'quality_score': -10,  # Negative
                        'diagnostic_adequacy': 'adequate'
                    }
                ],
                'overall_quality': 'Good',
                'summary': 'Summary'
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_empty_summary(self):
        """Test validation fails when summary is empty."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            invalid_output = {
                'images': [],
                'overall_quality': 'Good',
                'summary': ''  # Empty summary
            }
            
            assert agent.validate_output(invalid_output) is False
    
    def test_validate_output_not_dict(self):
        """Test validation fails when output is not a dictionary."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            assert agent.validate_output("not a dict") is False
            assert agent.validate_output([]) is False
            assert agent.validate_output(None) is False
    
    @patch('app.agents.agent_b_quality.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_process_success(self, mock_exists, mock_file, mock_openai_class):
        """Test successful processing of quality assessment."""
        mock_exists.return_value = True
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'images': [
                {
                    'image_index': 0,
                    'view_identified': 'Sagittal Right Lobe Liver',
                    'view_confidence': 0.92,
                    'quality_score': 85,
                    'technical_assessment': {
                        'resolution': 'good',
                        'contrast': 'excellent',
                        'penetration': 'adequate',
                        'field_of_view': 'optimal'
                    },
                    'artifacts': ['Minor acoustic shadowing'],
                    'limitations': [],
                    'diagnostic_adequacy': 'adequate',
                    'recommendations': 'Image quality is sufficient for diagnostic interpretation'
                }
            ],
            'overall_quality': 'Good quality ultrasound images',
            'summary': 'Single liver view with good technical quality and adequate diagnostic value'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/liver_image.jpg']
                }
            }
            
            result = agent.process(input_data)
            
            assert len(result['images']) == 1
            assert result['images'][0]['view_identified'] == 'Sagittal Right Lobe Liver'
            assert result['images'][0]['quality_score'] == 85
            assert result['images'][0]['diagnostic_adequacy'] == 'adequate'
            assert result['overall_quality'] == 'Good quality ultrasound images'
            assert result['summary'] is not None
    
    @patch('app.agents.agent_b_quality.OpenAI')
    def test_process_no_images(self, mock_openai_class):
        """Test processing when no images are provided."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': []
                }
            }
            
            result = agent.process(input_data)
            
            # Should return minimal assessment without calling API
            assert result['images'] == []
            assert 'No images' in result['overall_quality']
            
            # Verify API was not called
            mock_client.chat.completions.create.assert_not_called()
    
    @patch('app.agents.agent_b_quality.OpenAI')
    @patch('os.path.exists')
    def test_process_images_not_found(self, mock_exists, mock_openai_class):
        """Test processing when image files don't exist."""
        mock_exists.return_value = False
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/nonexistent.jpg']
                }
            }
            
            result = agent.process(input_data)
            
            # Should return minimal assessment when encoding fails
            assert result['images'] == []
            
            # Verify API was not called
            mock_client.chat.completions.create.assert_not_called()
    
    @patch('app.agents.agent_b_quality.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_process_api_error(self, mock_exists, mock_file, mock_openai_class):
        """Test handling of API errors."""
        mock_exists.return_value = True
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/image.jpg']
                }
            }
            
            with pytest.raises(Exception, match="Failed to assess image quality"):
                agent.process(input_data)
    
    @patch('app.agents.agent_b_quality.OpenAI')
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
            agent = QualityAssessmentAgent()
            
            input_data = {
                'case_id': 1,
                'case_data': {
                    'image_paths': ['/path/to/image.jpg']
                }
            }
            
            with pytest.raises(ValueError, match="Invalid JSON response"):
                agent.process(input_data)
    
    @patch('app.agents.agent_b_quality.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_execute_success(self, mock_exists, mock_file, mock_openai_class):
        """Test successful execution through base agent execute method."""
        mock_exists.return_value = True
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            'images': [
                {
                    'image_index': 0,
                    'view_identified': 'Test View',
                    'quality_score': 80,
                    'diagnostic_adequacy': 'adequate'
                }
            ],
            'overall_quality': 'Good',
            'summary': 'Test summary'
        })
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
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
    
    @patch('app.agents.agent_b_quality.OpenAI')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_image_data')
    @patch('os.path.exists')
    def test_execute_failure(self, mock_exists, mock_file, mock_openai_class):
        """Test execution failure through base agent execute method."""
        mock_exists.return_value = True
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = QualityAssessmentAgent()
            
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
            assert 'Failed to assess image quality' in result['error']
