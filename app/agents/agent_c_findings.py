"""
Agent C: Image Findings Extraction

This agent analyzes ultrasound images to extract observable findings using
multimodal LLM capabilities. It combines image analysis with clinical context
to identify and document relevant radiological findings.

The agent processes ultrasound images along with clinical context and returns
structured information about observable findings including echogenicity,
lesions, measurements, and other relevant observations.
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


class FindingsExtractionAgent(BaseAgent):
    """
    Agent C: Image Findings Extraction
    
    Analyzes ultrasound images to extract:
    - Echogenicity patterns (normal, increased, decreased, heterogeneous)
    - Focal lesions (location, size, characteristics)
    - Organ measurements and dimensions
    - Vascular findings (portal vein, hepatic veins)
    - Bile duct assessment
    - Presence of ascites or fluid collections
    - Surface characteristics (smooth, nodular)
    - Other relevant observations
    
    Output includes:
    - Structured findings by category
    - Measurements with units
    - Lesion characteristics and locations
    - Comparison with clinical context
    - Confidence levels for findings
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Findings Extraction Agent.
        
        Args:
            config: Optional configuration dictionary containing:
                - api_key: OpenAI API key (defaults to env variable)
                - model: Model to use (defaults to gpt-4o)
                - temperature: Temperature for generation (defaults to 0.1)
        """
        super().__init__(agent_name='agent_c_findings', config=config)
        
        # Initialize OpenAI client
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.1)
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for findings extraction.
        
        Returns:
            The system prompt for the agent
        """
        return """You are an ultrasound findings extraction specialist for radiology AI systems.

Your task is to analyze ultrasound images and extract structured, observable findings that will inform diagnostic reasoning and report generation.

**Clinical Context**: You will be provided with clinical context including patient history, indication, and lab results. Use this to guide your analysis but focus on objective imaging findings.

For each image, identify and document:

1. **Organ Appearance**:
   - Size (normal, enlarged, small)
   - Echogenicity (normal, increased, decreased, heterogeneous)
   - Echotexture (homogeneous, coarse, fine)
   - Surface contour (smooth, nodular, irregular)

2. **Focal Lesions** (if present):
   - Location (specific lobe/segment)
   - Size (measurements in cm)
   - Echogenicity (hyperechoic, hypoechoic, isoechoic, anechoic)
   - Margins (well-defined, ill-defined)
   - Internal characteristics (solid, cystic, complex)
   - Posterior acoustic features (enhancement, shadowing, none)

3. **Vascular Structures**:
   - Portal vein (diameter, patency, flow direction if Doppler available)
   - Hepatic veins (size, patency)
   - Hepatic artery (if visualized)
   - Thrombosis or abnormal flow patterns

4. **Biliary System**:
   - Intrahepatic bile ducts (normal, dilated)
   - Common bile duct (diameter if measured)
   - Gallbladder (if visualized)

5. **Additional Findings**:
   - Ascites (present/absent, amount)
   - Pleural effusion (if visible)
   - Lymphadenopathy
   - Other relevant observations

6. **Measurements**:
   - Organ dimensions (length, width, thickness)
   - Lesion sizes
   - Vessel diameters
   - Always include units (cm, mm)

**Output Format**: Return a valid JSON object with the following structure:
{
    "organ_assessment": {
        "size": "string - normal/enlarged/small with measurements if available",
        "echogenicity": "string - normal/increased/decreased/heterogeneous",
        "echotexture": "string - homogeneous/coarse/fine",
        "surface": "string - smooth/nodular/irregular"
    },
    "focal_lesions": [
        {
            "location": "string - specific anatomical location",
            "size": "string - measurements with units",
            "echogenicity": "string - hyperechoic/hypoechoic/isoechoic/anechoic",
            "margins": "string - well-defined/ill-defined",
            "characteristics": "string - solid/cystic/complex",
            "posterior_acoustic": "string - enhancement/shadowing/none",
            "description": "string - detailed description"
        }
    ],
    "vascular_findings": {
        "portal_vein": "string - assessment including diameter if measured",
        "hepatic_veins": "string - assessment",
        "abnormalities": ["list", "of", "vascular", "abnormalities"]
    },
    "biliary_system": {
        "intrahepatic_ducts": "string - normal/dilated",
        "common_bile_duct": "string - diameter if measured",
        "abnormalities": ["list", "of", "biliary", "abnormalities"]
    },
    "additional_findings": {
        "ascites": "string - present/absent with description",
        "other": ["list", "of", "other", "findings"]
    },
    "measurements": {
        "measurement_name": "value with units"
    },
    "confidence_assessment": {
        "overall_confidence": "float 0-1 - confidence in findings",
        "limitations": ["list", "of", "factors", "limiting", "assessment"]
    },
    "summary": "string - concise summary of key findings"
}

**Guidelines**:
- Report only what is objectively visible in the images
- Use standard radiological terminology
- Include measurements with appropriate units
- Note if structures are not well-visualized
- Consider clinical context but remain objective
- If no abnormalities are seen, state "No significant abnormality detected"
- Indicate confidence level and any limitations
- Be specific about locations and characteristics

Return ONLY the JSON object, no additional text."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured findings from ultrasound images.
        
        Args:
            input_data: Dictionary containing:
                - case_id: Case identifier
                - case_data: Dictionary with image and clinical information including:
                    - image_paths: List of paths to ultrasound images
                    - image_path: Single image path (legacy support)
                - clinical_context: Clinical context from Agent A (optional)
        
        Returns:
            Dictionary containing structured findings:
                - organ_assessment: Organ appearance details
                - focal_lesions: List of identified lesions
                - vascular_findings: Vascular structure assessment
                - biliary_system: Biliary system assessment
                - additional_findings: Other relevant findings
                - measurements: Quantitative measurements
                - confidence_assessment: Confidence and limitations
                - summary: Brief findings summary
        
        Raises:
            ValueError: If required input data is missing
            Exception: If API call fails
        """
        self.logger.info(f"Processing findings extraction for case {input_data.get('case_id')}")
        
        # Extract case data
        case_data = input_data.get('case_data', {})
        clinical_context = input_data.get('clinical_context', {})
        
        # Get image paths
        image_paths = self._get_image_paths(case_data)
        
        if not image_paths:
            self.logger.warning("No images provided, returning minimal findings")
            return self._create_minimal_findings()
        
        # Encode images to base64
        encoded_images = self._encode_images(image_paths)
        
        if not encoded_images:
            self.logger.warning("Failed to encode images, returning minimal findings")
            return self._create_minimal_findings()
        
        # Prepare clinical context summary
        context_summary = self._format_clinical_context(clinical_context)
        
        # Call OpenAI API with multimodal input
        try:
            # Prepare messages with images and clinical context
            messages = [
                {"role": "system", "content": self.get_prompt_template()},
                {
                    "role": "user",
                    "content": self._build_multimodal_content(encoded_images, context_summary)
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"},
                max_tokens=3000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            findings = json.loads(content)
            
            self.logger.info(f"Successfully extracted findings from {len(encoded_images)} images")
            return findings
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise Exception(f"Failed to extract findings: {str(e)}")
    
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
    
    def _format_clinical_context(self, clinical_context: Dict[str, Any]) -> str:
        """
        Format clinical context for inclusion in the prompt.
        
        Args:
            clinical_context: Clinical context dictionary from Agent A
        
        Returns:
            Formatted clinical context string
        """
        if not clinical_context:
            return "No clinical context provided."
        
        sections = []
        
        if clinical_context.get('clinical_indication'):
            sections.append(f"Indication: {clinical_context['clinical_indication']}")
        
        if clinical_context.get('relevant_history'):
            sections.append(f"History: {clinical_context['relevant_history']}")
        
        if clinical_context.get('pertinent_labs'):
            labs = clinical_context['pertinent_labs']
            if labs:
                lab_str = ", ".join([f"{k}: {v}" for k, v in labs.items()])
                sections.append(f"Labs: {lab_str}")
        
        if clinical_context.get('clinical_questions'):
            questions = clinical_context['clinical_questions']
            if questions:
                sections.append(f"Questions: {', '.join(questions)}")
        
        return "\n".join(sections) if sections else "No clinical context provided."
    
    def _build_multimodal_content(
        self,
        encoded_images: List[Dict[str, Any]],
        context_summary: str
    ) -> List[Dict[str, Any]]:
        """
        Build multimodal content array for API request.
        
        Args:
            encoded_images: List of encoded image dictionaries
            context_summary: Formatted clinical context string
        
        Returns:
            List of content items for API request
        """
        content = [
            {
                "type": "text",
                "text": f"""Clinical Context:
{context_summary}

Please analyze the following {len(encoded_images)} ultrasound image(s) and extract structured findings:"""
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
    
    def _create_minimal_findings(self) -> Dict[str, Any]:
        """
        Create minimal findings when no images are available.
        
        Returns:
            Minimal findings dictionary
        """
        return {
            "organ_assessment": {
                "size": "Not assessed - no images available",
                "echogenicity": "Not assessed",
                "echotexture": "Not assessed",
                "surface": "Not assessed"
            },
            "focal_lesions": [],
            "vascular_findings": {
                "portal_vein": "Not visualized",
                "hepatic_veins": "Not visualized",
                "abnormalities": []
            },
            "biliary_system": {
                "intrahepatic_ducts": "Not visualized",
                "common_bile_duct": "Not visualized",
                "abnormalities": []
            },
            "additional_findings": {
                "ascites": "Not assessed",
                "other": []
            },
            "measurements": {},
            "confidence_assessment": {
                "overall_confidence": 0.0,
                "limitations": ["No images available for assessment"]
            },
            "summary": "Findings extraction could not be performed due to missing images."
        }
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the findings extraction output.
        
        Args:
            output: The output dictionary to validate
        
        Returns:
            True if output is valid, False otherwise
        """
        if not isinstance(output, dict):
            self.logger.error("Output is not a dictionary")
            return False
        
        # Required keys
        required_keys = [
            'organ_assessment',
            'focal_lesions',
            'vascular_findings',
            'biliary_system',
            'additional_findings',
            'measurements',
            'confidence_assessment',
            'summary'
        ]
        
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        # Validate organ_assessment structure
        if not isinstance(output['organ_assessment'], dict):
            self.logger.error("organ_assessment must be a dictionary")
            return False
        
        # Validate focal_lesions is a list
        if not isinstance(output['focal_lesions'], list):
            self.logger.error("focal_lesions must be a list")
            return False
        
        # Validate each focal lesion
        for idx, lesion in enumerate(output['focal_lesions']):
            if not isinstance(lesion, dict):
                self.logger.error(f"Focal lesion {idx} is not a dictionary")
                return False
        
        # Validate vascular_findings structure
        if not isinstance(output['vascular_findings'], dict):
            self.logger.error("vascular_findings must be a dictionary")
            return False
        
        # Validate biliary_system structure
        if not isinstance(output['biliary_system'], dict):
            self.logger.error("biliary_system must be a dictionary")
            return False
        
        # Validate additional_findings structure
        if not isinstance(output['additional_findings'], dict):
            self.logger.error("additional_findings must be a dictionary")
            return False
        
        # Validate measurements is a dictionary
        if not isinstance(output['measurements'], dict):
            self.logger.error("measurements must be a dictionary")
            return False
        
        # Validate confidence_assessment structure
        if not isinstance(output['confidence_assessment'], dict):
            self.logger.error("confidence_assessment must be a dictionary")
            return False
        
        confidence = output['confidence_assessment']
        if 'overall_confidence' in confidence:
            try:
                conf_value = float(confidence['overall_confidence'])
                if conf_value < 0 or conf_value > 1:
                    self.logger.error(f"overall_confidence out of range: {conf_value}")
                    return False
            except (ValueError, TypeError):
                self.logger.error("overall_confidence is not a valid float")
                return False
        
        # Ensure summary is present and non-empty
        if not output.get('summary'):
            self.logger.error("summary must be present and non-empty")
            return False
        
        self.logger.info("Output validation passed")
        return True
