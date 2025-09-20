"""
AI Service Module for OpenAI GPT-4o Integration

This module handles communication with OpenAI's GPT-4o API for generating
preliminary radiology reports from ultrasound images and clinical notes.
"""

import os
import json
import logging
from typing import Dict, Optional, Tuple
from openai import OpenAI
from flask import current_app

# Configure logging
logger = logging.getLogger(__name__)

class AIServiceError(Exception):
    """Custom exception for AI service errors."""
    pass

class AIService:
    """Service class for OpenAI GPT-4o integration."""
    
    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenAI client with API key."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise AIServiceError("OpenAI API key not configured")
        
        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise AIServiceError(f"Failed to initialize OpenAI client: {str(e)}")
    
    def generate_draft_report(self, image_path: str, clinical_notes: str) -> Tuple[Dict, str]:
        """
        Generate a preliminary radiology report using GPT-4o.
        
        Args:
            image_path (str): Path to the ultrasound image file
            clinical_notes (str): Clinical notes provided by the healthcare professional
            
        Returns:
            Tuple[Dict, str]: Raw JSON response and formatted text report
            
        Raises:
            AIServiceError: If report generation fails
        """
        if not self.client:
            raise AIServiceError("OpenAI client not initialized")
        
        try:
            # Read and encode the image
            image_data = self._encode_image(image_path)
            
            # Prepare the prompt
            prompt = self._create_prompt(clinical_notes)
            
            # Make API call to GPT-4o with timeout
            logger.info("Starting OpenAI API call for draft report generation")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert radiologist assistant. Analyze the provided ultrasound image and clinical notes to generate a preliminary radiology report. Be thorough but concise, and always include appropriate medical disclaimers."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.3,
                timeout=120  # 2 minute timeout
            )
            logger.info("OpenAI API call completed successfully")
            
            # Extract response content
            raw_response = response.model_dump()
            formatted_text = response.choices[0].message.content
            
            logger.info(f"Successfully generated draft report. Tokens used: {response.usage.total_tokens}")
            
            return raw_response, formatted_text
            
        except Exception as e:
            logger.error(f"Error generating draft report: {str(e)}")
            raise AIServiceError(f"Failed to generate draft report: {str(e)}")
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode image file to base64 string.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: Base64 encoded image data
            
        Raises:
            AIServiceError: If image encoding fails
        """
        try:
            import base64
            
            if not os.path.exists(image_path):
                raise AIServiceError(f"Image file not found: {image_path}")
            
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            return encoded_string
            
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {str(e)}")
            raise AIServiceError(f"Failed to encode image: {str(e)}")
    
    def _create_prompt(self, clinical_notes: str) -> str:
        """
        Create a structured prompt for the AI model.
        
        Args:
            clinical_notes (str): Clinical notes from the healthcare professional
            
        Returns:
            str: Formatted prompt for the AI model
        """
        prompt = f"""
Please analyze this ultrasound image and provide a preliminary radiology report based on the following clinical information:

CLINICAL NOTES:
{clinical_notes if clinical_notes else "No clinical notes provided."}

Please provide a structured report including:

1. TECHNICAL QUALITY: Comment on image quality and technical adequacy
2. FINDINGS: Describe what you observe in the ultrasound image
3. IMPRESSION: Provide your preliminary diagnostic impression
4. RECOMMENDATIONS: Suggest any follow-up studies or clinical correlation needed

IMPORTANT DISCLAIMERS:
- This is a preliminary AI-generated report that requires review by a qualified radiologist
- Clinical correlation is recommended
- This report should not be used as the sole basis for clinical decision-making

Please format the report in a clear, professional manner suitable for medical documentation.
"""
        return prompt.strip()

# Global AI service instance (lazy-loaded)
_ai_service = None

def get_ai_service():
    """Get or create the global AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

def generate_draft_report(image_path: str, clinical_notes: str) -> Tuple[Dict, str]:
    """
    Convenience function to generate a draft report.
    
    Args:
        image_path (str): Path to the ultrasound image
        clinical_notes (str): Clinical notes
        
    Returns:
        Tuple[Dict, str]: Raw JSON response and formatted text
    """
    return get_ai_service().generate_draft_report(image_path, clinical_notes)