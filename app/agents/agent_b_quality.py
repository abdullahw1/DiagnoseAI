"""
Agent B: View Identification and Quality Assessment

This agent analyzes ultrasound images to identify anatomical views and assess
image quality. It uses multimodal LLM capabilities to evaluate technical adequacy
and provide quality scores.

The agent processes ultrasound images and returns structured information about:
- Identified anatomical views
- Image quality scores
- Technical adequacy assessment
- Recommendations for image optimization
"""

import logging
import json
import base64
from typing import Dict, Any, Optional, List
from openai import OpenAI
import os
from pathlib import Path
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QualityAssessmentAgent(BaseAgent):
    """
    Agent B: View Identification and Quality Assessment
    
    Analyzes ultrasound images to:
    - Identify anatomical views (e.g., sagittal liver, transverse gallbladder)
    - Assess image quality (resolution, contrast, artifacts)
    - Evaluate technical adequacy for diagnostic interpretation
    - Provide quality scores and recommendations
    
    Output includes:
    - Identified views for each image
    - Quality scores (0-100 scale)
    - Technical adequacy assessment
    - Artifacts or limitations noted
    - Overall assessment summary
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Quality Assessment Agent.
        
        Args:
            config: Optional configuration dictionary containing:
                - api_key: OpenAI API key (defaults to env variable)
                - model: Model to use (defaults to gpt-4o)
                - temperature: Temperature for generation (defaults to 0.1)
        """
        super().__init__(agent_name='agent_b_quality', config=config)
        
        # Initialize OpenAI client
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.1)
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for view identification and quality assessment.
        
        Returns:
            The system prompt for the agent
        """
        return """You are an ultrasound image quality assessment specialist for radiology AI systems.

Your task is to analyze ultrasound images and provide structured assessment of anatomical views and image quality.

For each image, evaluate and extract:

1. **Anatomical View Identification**: Identify the specific anatomical view shown (e.g., "Sagittal Right Lobe Liver", "Transverse Gallbladder", "Portal Vein View")

2. **Image Quality Score**: Rate overall image quality on a 0-100 scale where:
   - 90-100: Excellent quality, optimal for diagnosis
   - 70-89: Good quality, adequate for diagnosis
   - 50-69: Fair quality, diagnostic with limitations
   - 30-49: Poor quality, limited diagnostic value
   - 0-29: Inadequate quality, non-diagnostic

3. **Technical Adequacy**: Assess technical factors:
   - Resolution and clarity
   - Contrast and brightness
   - Depth of penetration
   - Field of view adequacy
   - Proper gain settings

4. **Artifacts and Limitations**: Identify any:
   - Acoustic shadowing
   - Reverberation artifacts
   - Motion artifacts
   - Poor acoustic window
   - Suboptimal patient positioning

5. **Diagnostic Adequacy**: Determine if the image is adequate for diagnostic interpretation

**Output Format**: Return a valid JSON object with the following structure:
{
    "images": [
        {
            "image_index": 0,
            "view_identified": "string - specific anatomical view name",
            "view_confidence": "float 0-1 - confidence in view identification",
            "quality_score": "integer 0-100 - overall quality score",
            "technical_assessment": {
                "resolution": "string - excellent/good/fair/poor",
                "contrast": "string - excellent/good/fair/poor",
                "penetration": "string - adequate/limited/inadequate",
                "field_of_view": "string - optimal/adequate/suboptimal"
            },
            "artifacts": ["list", "of", "identified", "artifacts"],
            "limitations": ["list", "of", "technical", "limitations"],
            "diagnostic_adequacy": "string - excellent/adequate/limited/inadequate",
            "recommendations": "string - suggestions for image optimization if needed"
        }
    ],
    "overall_quality": "string - overall assessment across all images",
    "summary": "string - brief quality assessment summary"
}

**Guidelines**:
- Be specific in view identification (include laterality, orientation, anatomical landmarks)
- Provide objective quality assessments based on technical criteria
- Note any factors that may limit diagnostic interpretation
- If view cannot be confidently identified, indicate uncertainty
- Consider clinical utility in your assessment

Return ONLY the JSON object, no additional text."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze ultrasound images for view identification and quality assessment.
        
        Args:
            input_data: Dictionary containing:
                - case_id: Case identifier
                - case_data: Dictionary with image information including:
                    - image_paths: List of paths to ultrasound images
                    - image_path: Single image path (legacy support)
        
        Returns:
            Dictionary containing quality assessment:
                - images: List of per-image assessments with:
                    - image_index: Index of the image
                    - view_identified: Identified anatomical view
                    - view_confidence: Confidence in view identification
                    - quality_score: Quality score (0-100)
                    - technical_assessment: Technical quality factors
                    - artifacts: List of identified artifacts
                    - limitations: List of technical limitations
                    - diagnostic_adequacy: Overall diagnostic adequacy
                    - recommendations: Optimization suggestions
                - overall_quality: Overall quality assessment
                - summary: Brief summary
        
        Raises:
            ValueError: If required input data is missing
            Exception: If API call fails
        """
        self.logger.info(f"Processing quality assessment for case {input_data.get('case_id')}")
        
        # Extract case data
        case_data = input_data.get('case_data', {})
        
        # Get image paths
        image_paths = self._get_image_paths(case_data)
        
        if not image_paths:
            self.logger.warning("No images provided, returning minimal assessment")
            return self._create_minimal_assessment()
        
        # Encode images to base64
        encoded_images = self._encode_images(image_paths)
        
        if not encoded_images:
            self.logger.warning("Failed to encode images, returning minimal assessment")
            return self._create_minimal_assessment()
        
        # Call OpenAI API with multimodal input
        try:
            # Prepare messages with images
            messages = [
                {"role": "system", "content": self.get_prompt_template()},
                {
                    "role": "user",
                    "content": self._build_multimodal_content(encoded_images)
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            quality_assessment = json.loads(content)
            
            self.logger.info(f"Successfully assessed {len(encoded_images)} images")
            return quality_assessment
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise Exception(f"Failed to assess image quality: {str(e)}")
    
    def _get_image_paths(self, case_data: Dict[str, Any]) -> List[str]:
        """
        Extract image paths from case data.
        
        Args:
            case_data: Case data dictionary
        
        Returns:
            List of image file paths
        """
        # Try multiple possible keys for image paths
        image_paths = case_data.get('image_paths', [])
        
        # Support legacy single image path
        if not image_paths:
            single_path = case_data.get('image_path')
            if single_path:
                image_paths = [single_path]
        
        # Filter out None values and ensure all are strings
        image_paths = [str(p) for p in image_paths if p]
        
        return image_paths
    
    def _encode_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Encode images to base64 for API transmission.
        
        Args:
            image_paths: List of image file paths
        
        Returns:
            List of dictionaries with image data and metadata
        """
        encoded_images = []
        
        for idx, image_path in enumerate(image_paths):
            try:
                # Check if file exists
                if not os.path.exists(image_path):
                    self.logger.warning(f"Image file not found: {image_path}")
                    continue
                
                # Read and encode image
                with open(image_path, 'rb') as image_file:
                    image_data = image_file.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # Determine image format from extension
                ext = Path(image_path).suffix.lower()
                mime_type = self._get_mime_type(ext)
                
                encoded_images.append({
                    'index': idx,
                    'path': image_path,
                    'base64': base64_image,
                    'mime_type': mime_type
                })
                
            except Exception as e:
                self.logger.error(f"Failed to encode image {image_path}: {str(e)}")
                continue
        
        return encoded_images
    
    def _get_mime_type(self, extension: str) -> str:
        """
        Get MIME type from file extension.
        
        Args:
            extension: File extension (e.g., '.jpg', '.png')
        
        Returns:
            MIME type string
        """
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        return mime_types.get(extension.lower(), 'image/jpeg')
    
    def _build_multimodal_content(self, encoded_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build multimodal content array for API request.
        
        Args:
            encoded_images: List of encoded image dictionaries
        
        Returns:
            List of content items for API request
        """
        content = [
            {
                "type": "text",
                "text": f"Please analyze the following {len(encoded_images)} ultrasound image(s) and provide quality assessment:"
            }
        ]
        
        # Add each image
        for img in encoded_images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img['mime_type']};base64,{img['base64']}"
                }
            })
        
        return content
    
    def _create_minimal_assessment(self) -> Dict[str, Any]:
        """
        Create a minimal quality assessment when no images are available.
        
        Returns:
            Minimal quality assessment dictionary
        """
        return {
            "images": [],
            "overall_quality": "No images available for assessment",
            "summary": "Quality assessment could not be performed due to missing images."
        }
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the quality assessment output.
        
        Args:
            output: The output dictionary to validate
        
        Returns:
            True if output is valid, False otherwise
        """
        if not isinstance(output, dict):
            self.logger.error("Output is not a dictionary")
            return False
        
        # Required keys
        required_keys = ['images', 'overall_quality', 'summary']
        
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        # Validate images array
        if not isinstance(output['images'], list):
            self.logger.error("images must be a list")
            return False
        
        # Validate each image assessment
        for idx, img_assessment in enumerate(output['images']):
            if not isinstance(img_assessment, dict):
                self.logger.error(f"Image assessment {idx} is not a dictionary")
                return False
            
            # Required keys for each image
            image_required_keys = [
                'image_index',
                'view_identified',
                'quality_score',
                'diagnostic_adequacy'
            ]
            
            for key in image_required_keys:
                if key not in img_assessment:
                    self.logger.error(f"Image {idx} missing required key: {key}")
                    return False
            
            # Validate quality score range
            quality_score = img_assessment.get('quality_score')
            if quality_score is not None:
                try:
                    score = int(quality_score)
                    if score < 0 or score > 100:
                        self.logger.error(f"Image {idx} quality_score out of range: {score}")
                        return False
                except (ValueError, TypeError):
                    self.logger.error(f"Image {idx} quality_score is not a valid integer")
                    return False
        
        # Ensure summary is present and non-empty
        if not output.get('summary'):
            self.logger.error("summary must be present and non-empty")
            return False
        
        self.logger.info("Output validation passed")
        return True
