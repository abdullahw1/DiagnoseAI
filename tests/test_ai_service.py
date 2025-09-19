"""
Unit tests for AI service functionality.

Tests the OpenAI GPT-4o integration for generating draft radiology reports.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from app.ai_service import AIService, AIServiceError, generate_draft_report


class TestAIService:
    """Test cases for the AIService class."""
    
    def test_initialization_success(self):
        """Test successful AI service initialization."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.ai_service.OpenAI') as mock_openai:
                service = AIService()
                assert service.client is not None
                mock_openai.assert_called_once_with(api_key='test-key')
    
    def test_initialization_no_api_key(self):
        """Test AI service initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AIServiceError, match="OpenAI API key not configured"):
                AIService()
    
    def test_initialization_client_error(self):
        """Test AI service initialization fails with client error."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.ai_service.OpenAI', side_effect=Exception("Client error")):
                with pytest.raises(AIServiceError, match="Failed to initialize OpenAI client"):
                    AIService()
    
    def test_encode_image_success(self):
        """Test successful image encoding."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.ai_service.OpenAI'):
                service = AIService()
                
                # Create a temporary image file
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    temp_file.write(b'fake image data')
                    temp_path = temp_file.name
                
                try:
                    encoded = service._encode_image(temp_path)
                    assert encoded == 'ZmFrZSBpbWFnZSBkYXRh'  # base64 of 'fake image data'
                finally:
                    os.unlink(temp_path)
    
    def test_encode_image_file_not_found(self):
        """Test image encoding fails when file doesn't exist."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.ai_service.OpenAI'):
                service = AIService()
                
                with pytest.raises(AIServiceError, match="Image file not found"):
                    service._encode_image('/nonexistent/path.jpg')
    
    def test_create_prompt_with_notes(self):
        """Test prompt creation with clinical notes."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.ai_service.OpenAI'):
                service = AIService()
                
                notes = "Patient presents with abdominal pain"
                prompt = service._create_prompt(notes)
                
                assert "Patient presents with abdominal pain" in prompt
                assert "CLINICAL NOTES:" in prompt
                assert "TECHNICAL QUALITY:" in prompt
                assert "FINDINGS:" in prompt
                assert "IMPRESSION:" in prompt
                assert "RECOMMENDATIONS:" in prompt
                assert "preliminary AI-generated report" in prompt
    
    def test_create_prompt_without_notes(self):
        """Test prompt creation without clinical notes."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.ai_service.OpenAI'):
                service = AIService()
                
                prompt = service._create_prompt("")
                
                assert "No clinical notes provided." in prompt
                assert "CLINICAL NOTES:" in prompt
    
    @patch('app.ai_service.OpenAI')
    def test_generate_draft_report_success(self, mock_openai_class):
        """Test successful draft report generation."""
        # Mock the OpenAI client and response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test radiology report content"
        mock_response.usage.total_tokens = 150
        mock_response.model_dump.return_value = {
            "id": "test-id",
            "choices": [{"message": {"content": "Test radiology report content"}}],
            "usage": {"total_tokens": 150}
        }
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            # Create a temporary image file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(b'fake image data')
                temp_path = temp_file.name
            
            try:
                service = AIService()
                raw_response, formatted_text = service.generate_draft_report(
                    temp_path, 
                    "Test clinical notes"
                )
                
                assert formatted_text == "Test radiology report content"
                assert raw_response["id"] == "test-id"
                assert raw_response["usage"]["total_tokens"] == 150
                
                # Verify the API call was made correctly
                mock_client.chat.completions.create.assert_called_once()
                call_args = mock_client.chat.completions.create.call_args
                
                assert call_args[1]["model"] == "gpt-4o"
                assert call_args[1]["max_tokens"] == 1500
                assert call_args[1]["temperature"] == 0.3
                assert len(call_args[1]["messages"]) == 2
                assert call_args[1]["messages"][0]["role"] == "system"
                assert call_args[1]["messages"][1]["role"] == "user"
                
            finally:
                os.unlink(temp_path)
    
    @patch('app.ai_service.OpenAI')
    def test_generate_draft_report_api_error(self, mock_openai_class):
        """Test draft report generation with API error."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(b'fake image data')
                temp_path = temp_file.name
            
            try:
                service = AIService()
                
                with pytest.raises(AIServiceError, match="Failed to generate draft report"):
                    service.generate_draft_report(temp_path, "Test notes")
                    
            finally:
                os.unlink(temp_path)
    
    def test_generate_draft_report_no_client(self):
        """Test draft report generation fails without initialized client."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.ai_service.OpenAI'):
                service = AIService()
                service.client = None  # Simulate uninitialized client
                
                with pytest.raises(AIServiceError, match="OpenAI client not initialized"):
                    service.generate_draft_report("/fake/path.jpg", "Test notes")


class TestConvenienceFunction:
    """Test cases for the convenience function."""
    
    @patch('app.ai_service.get_ai_service')
    def test_generate_draft_report_function(self, mock_get_service):
        """Test the convenience function calls the service correctly."""
        mock_service = Mock()
        mock_get_service.return_value = mock_service
        mock_service.generate_draft_report.return_value = (
            {"test": "response"}, 
            "Test report text"
        )
        
        raw_response, formatted_text = generate_draft_report(
            "/test/path.jpg", 
            "Test clinical notes"
        )
        
        assert raw_response == {"test": "response"}
        assert formatted_text == "Test report text"
        
        mock_service.generate_draft_report.assert_called_once_with(
            "/test/path.jpg", 
            "Test clinical notes"
        )


class TestIntegrationScenarios:
    """Integration test scenarios for AI service."""
    
    @patch('app.ai_service.OpenAI')
    def test_complete_workflow_success(self, mock_openai_class):
        """Test complete workflow from image to report."""
        # Setup mock
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
TECHNICAL QUALITY: Good image quality with adequate penetration.

FINDINGS: 
- Normal liver echogenicity
- No focal lesions identified
- Portal vein appears patent

IMPRESSION: Normal abdominal ultrasound

RECOMMENDATIONS: No further imaging required at this time.

IMPORTANT DISCLAIMERS:
- This is a preliminary AI-generated report that requires review by a qualified radiologist
- Clinical correlation is recommended
"""
        mock_response.usage.total_tokens = 200
        mock_response.model_dump.return_value = {
            "id": "chatcmpl-test123",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "gpt-4o",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": mock_response.choices[0].message.content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 150,
                "total_tokens": 200
            }
        }
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-api-key'}):
            # Create a temporary image file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(b'fake ultrasound image data')
                temp_path = temp_file.name
            
            try:
                service = AIService()
                raw_response, formatted_text = service.generate_draft_report(
                    temp_path,
                    "35-year-old female with right upper quadrant pain. Rule out gallbladder pathology."
                )
                
                # Verify response structure
                assert "TECHNICAL QUALITY:" in formatted_text
                assert "FINDINGS:" in formatted_text
                assert "IMPRESSION:" in formatted_text
                assert "RECOMMENDATIONS:" in formatted_text
                assert "preliminary AI-generated report" in formatted_text
                
                # Verify raw response structure
                assert raw_response["id"] == "chatcmpl-test123"
                assert raw_response["model"] == "gpt-4o"
                assert raw_response["usage"]["total_tokens"] == 200
                
                # Verify API call parameters
                call_args = mock_client.chat.completions.create.call_args[1]
                assert call_args["model"] == "gpt-4o"
                assert call_args["max_tokens"] == 1500
                assert call_args["temperature"] == 0.3
                
                # Verify message structure
                messages = call_args["messages"]
                assert len(messages) == 2
                assert messages[0]["role"] == "system"
                assert "expert radiologist assistant" in messages[0]["content"]
                assert messages[1]["role"] == "user"
                assert len(messages[1]["content"]) == 2  # text and image
                assert messages[1]["content"][0]["type"] == "text"
                assert messages[1]["content"][1]["type"] == "image_url"
                assert "35-year-old female" in messages[1]["content"][0]["text"]
                
            finally:
                os.unlink(temp_path)
    
    @patch('app.ai_service.OpenAI')
    def test_error_handling_chain(self, mock_openai_class):
        """Test error handling through the entire chain."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Test different types of errors
        error_scenarios = [
            ("Connection timeout", "Connection timeout"),
            ("Rate limit exceeded", "Rate limit exceeded"),
            ("Invalid API key", "Invalid API key"),
            ("Model not available", "Model not available")
        ]
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            service = AIService()
            
            for error_message, expected_pattern in error_scenarios:
                mock_client.chat.completions.create.side_effect = Exception(error_message)
                
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    temp_file.write(b'test data')
                    temp_path = temp_file.name
                
                try:
                    with pytest.raises(AIServiceError) as exc_info:
                        service.generate_draft_report(temp_path, "Test notes")
                    
                    assert "Failed to generate draft report" in str(exc_info.value)
                    assert error_message in str(exc_info.value)
                    
                finally:
                    os.unlink(temp_path)