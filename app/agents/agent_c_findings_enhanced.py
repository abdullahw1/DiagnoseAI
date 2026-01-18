"""
Agent C Enhanced: Structured Findings Extraction

This agent extends the base FindingsExtractionAgent to extract structured
ultrasound findings in a format that matches the StructuredFindings model.
It analyzes images and returns findings organized by organ system with
specific enumerated values and free text fields.
"""

import logging
import json
from typing import Dict, Any, Optional
from openai import OpenAI
import os
from app.agents.agent_c_findings import FindingsExtractionAgent

logger = logging.getLogger(__name__)


class FindingsExtractionAgentEnhanced(FindingsExtractionAgent):
    """
    Agent C Enhanced: Structured Findings Extraction
    
    Extends FindingsExtractionAgent to extract findings in the structured
    format required for AIGeneratedFindings model. Returns findings organized
    by organ system with enumerated values matching the database schema.
    
    Output includes:
    - Liver findings (size, texture, focal defect, CBD, PV)
    - Spleen findings (size, focal defect)
    - Gall Bladder findings (calculus, wall edema)
    - Right/Left Kidney findings (size, texture, other)
    - Pancreas findings (free text)
    - Urinary Bladder findings (filling, stone/mass, mucosal irregularity)
    - Prostate findings (free text)
    - Additional findings (ascites, pleural effusions, lymph nodes, other)
    - Comments (free text)
    - Confidence scores per field
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Enhanced Findings Extraction Agent.
        
        Args:
            config: Optional configuration dictionary containing:
                - api_key: OpenAI API key (defaults to env variable)
                - model: Model to use (defaults to gpt-4o)
                - temperature: Temperature for generation (defaults to 0.1)
        """
        super().__init__(config=config)
        self.agent_name = 'agent_c_findings_enhanced'
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for structured findings extraction.
        
        Returns:
            The system prompt for the agent
        """
        return """You are a specialized ultrasound findings extraction agent for radiology AI systems.

Your task is to analyze ultrasound images and extract structured findings in a specific format that matches a standardized database schema. You must provide findings for each organ system using predefined enumerated values where specified.

**Clinical Context**: You will be provided with clinical context including patient history, indication, lab results, and potentially user-provided findings. Use this to guide your analysis but focus on objective imaging findings.

**IMPORTANT**: You must return findings using ONLY the allowed values specified below for each field.

Extract findings for the following organ systems:

1. **Liver**:
   - size: "Normal" | "Enlarged" | "Shrunken"
   - texture: "Normal" | "Fatty" | "Coarse"
   - focal_defect: "Absent" | "Present"
   - cbd: "Normal" | "Dilated"
   - pv: "Normal" | "Dilated"

2. **Spleen**:
   - size: "Normal" | "Enlarged"
   - focal_defect: "Absent" | "Present"

3. **Gall Bladder**:
   - calculus: "Absent" | "Present"
   - wall_edema: "Absent" | "Present"

4. **Right Kidney**:
   - size: "Normal" | "Shrunken"
   - texture: "Normal" | "Echogenic"
   - other: Free text (max 200 chars) - describe stones, cysts, hydronephrosis

5. **Left Kidney**:
   - size: "Normal" | "Shrunken"
   - texture: "Normal" | "Echogenic"
   - other: Free text (max 200 chars) - describe stones, cysts, hydronephrosis

6. **Pancreas**:
   - findings: Free text (max 500 chars) - describe pancreas appearance

7. **Urinary Bladder**:
   - filling: "Full" | "Partially filled" | "Empty"
   - stone_mass: "Absent" | "Present"
   - mucosal_irregularity: "Absent" | "Present"

8. **Prostate**:
   - findings: Free text (max 500 chars) - describe prostate appearance

9. **Additional Findings**:
   - ascites: "Absent" | "Present"
   - pleural_effusions: "Absent" | "Present"
   - para_aortic_lymph_nodes: "Absent" | "Present"
   - other: Free text (max 200 chars) - other relevant findings

10. **Comments**: Free text (max 1000 chars) - additional observations

**Output Format**: Return a valid JSON object with the following structure:
{
    "liver": {
        "size": "Normal|Enlarged|Shrunken",
        "texture": "Normal|Fatty|Coarse",
        "focal_defect": "Absent|Present",
        "cbd": "Normal|Dilated",
        "pv": "Normal|Dilated"
    },
    "spleen": {
        "size": "Normal|Enlarged",
        "focal_defect": "Absent|Present"
    },
    "gall_bladder": {
        "calculus": "Absent|Present",
        "wall_edema": "Absent|Present"
    },
    "right_kidney": {
        "size": "Normal|Shrunken",
        "texture": "Normal|Echogenic",
        "other": "string - free text description"
    },
    "left_kidney": {
        "size": "Normal|Shrunken",
        "texture": "Normal|Echogenic",
        "other": "string - free text description"
    },
    "pancreas": {
        "findings": "string - free text description"
    },
    "urinary_bladder": {
        "filling": "Full|Partially filled|Empty",
        "stone_mass": "Absent|Present",
        "mucosal_irregularity": "Absent|Present"
    },
    "prostate": {
        "findings": "string - free text description"
    },
    "additional": {
        "ascites": "Absent|Present",
        "pleural_effusions": "Absent|Present",
        "para_aortic_lymph_nodes": "Absent|Present",
        "other": "string - free text description"
    },
    "comments": "string - additional observations",
    "confidence_scores": {
        "liver_size": 0.95,
        "liver_texture": 0.88,
        "overall": 0.90
    }
}

**Guidelines**:
- Use ONLY the exact enumerated values specified above (case-sensitive)
- If a structure is not visualized or cannot be assessed, use null for that field
- Provide confidence scores (0.0-1.0) for each assessed field
- Include an overall confidence score
- Be objective and report only what is visible in the images
- Consider user-provided findings as reference but verify with images
- Use standard radiological terminology in free text fields
- Keep free text concise and focused on key findings
- If no abnormalities are detected, use "Normal" or "Absent" as appropriate

Return ONLY the JSON object, no additional text."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured findings from ultrasound images.
        
        Args:
            input_data: Dictionary containing:
                - case_id: Case identifier
                - case_data: Dictionary with image and clinical information
                - clinical_context: Clinical context from Agent A (optional)
        
        Returns:
            Dictionary containing structured findings in AIGeneratedFindings format:
                - liver: Liver findings dict
                - spleen: Spleen findings dict
                - gall_bladder: Gall bladder findings dict
                - right_kidney: Right kidney findings dict
                - left_kidney: Left kidney findings dict
                - pancreas: Pancreas findings dict
                - urinary_bladder: Urinary bladder findings dict
                - prostate: Prostate findings dict
                - additional: Additional findings dict
                - comments: Comments string
                - confidence_scores: Confidence scores dict
        
        Raises:
            ValueError: If required input data is missing
            Exception: If API call fails
        """
        self.logger.info(f"Processing enhanced findings extraction for case {input_data.get('case_id')}")
        
        # Extract case data
        case_data = input_data.get('case_data', {})
        clinical_context = input_data.get('clinical_context', {})
        
        # Get image paths
        image_paths = self._get_image_paths(case_data)
        
        if not image_paths:
            self.logger.warning("No images provided, returning minimal findings")
            return self._create_minimal_structured_findings()
        
        # Encode images to base64
        encoded_images = self._encode_images(image_paths)
        
        if not encoded_images:
            self.logger.warning("Failed to encode images, returning minimal findings")
            return self._create_minimal_structured_findings()
        
        # Prepare clinical context summary including user-provided findings
        context_summary = self._format_clinical_context_with_findings(clinical_context)
        
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
            
            # Validate and normalize the findings
            normalized_findings = self._normalize_findings(findings)
            
            self.logger.info(f"Successfully extracted structured findings from {len(encoded_images)} images")
            return normalized_findings
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise Exception(f"Failed to extract structured findings: {str(e)}")
    
    def _format_clinical_context_with_findings(self, clinical_context: Dict[str, Any]) -> str:
        """
        Format clinical context including user-provided findings.
        
        Args:
            clinical_context: Clinical context dictionary from Agent A
        
        Returns:
            Formatted clinical context string
        """
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
        
        # Include user-provided structured findings if available
        if clinical_context.get('structured_findings'):
            user_findings = clinical_context['structured_findings']
            sections.append(f"\nUser-Provided Findings (for reference):")
            sections.append(self._format_user_findings(user_findings))
        
        return "\n".join(sections) if sections else "No clinical context provided."
    
    def _format_user_findings(self, findings: Dict[str, Any]) -> str:
        """
        Format user-provided findings for inclusion in prompt.
        
        Args:
            findings: User-provided structured findings dictionary
        
        Returns:
            Formatted findings string
        """
        lines = []
        
        for organ, data in findings.items():
            if isinstance(data, dict):
                items = [f"{k}: {v}" for k, v in data.items() if v]
                if items:
                    lines.append(f"  {organ}: {', '.join(items)}")
            elif data:
                lines.append(f"  {organ}: {data}")
        
        return "\n".join(lines) if lines else "  No user findings provided"
    
    def _normalize_findings(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate findings to match database schema.
        
        Args:
            findings: Raw findings from LLM
        
        Returns:
            Normalized findings dictionary
        """
        # Define allowed values for enumerated fields
        allowed_values = {
            'liver_size': ['Normal', 'Enlarged', 'Shrunken'],
            'liver_texture': ['Normal', 'Fatty', 'Coarse'],
            'liver_focal_defect': ['Absent', 'Present'],
            'liver_cbd': ['Normal', 'Dilated'],
            'liver_pv': ['Normal', 'Dilated'],
            'spleen_size': ['Normal', 'Enlarged'],
            'spleen_focal_defect': ['Absent', 'Present'],
            'gb_calculus': ['Absent', 'Present'],
            'gb_wall_edema': ['Absent', 'Present'],
            'kidney_size': ['Normal', 'Shrunken'],
            'kidney_texture': ['Normal', 'Echogenic'],
            'bladder_filling': ['Full', 'Partially filled', 'Empty'],
            'bladder_stone_mass': ['Absent', 'Present'],
            'bladder_mucosal_irregularity': ['Absent', 'Present'],
            'ascites': ['Absent', 'Present'],
            'pleural_effusions': ['Absent', 'Present'],
            'para_aortic_lymph_nodes': ['Absent', 'Present']
        }
        
        normalized = {}
        
        # Normalize liver findings
        liver = findings.get('liver', {})
        normalized['liver_size'] = self._validate_enum(liver.get('size'), allowed_values['liver_size'])
        normalized['liver_texture'] = self._validate_enum(liver.get('texture'), allowed_values['liver_texture'])
        normalized['liver_focal_defect'] = self._validate_enum(liver.get('focal_defect'), allowed_values['liver_focal_defect'])
        normalized['liver_cbd'] = self._validate_enum(liver.get('cbd'), allowed_values['liver_cbd'])
        normalized['liver_pv'] = self._validate_enum(liver.get('pv'), allowed_values['liver_pv'])
        
        # Normalize spleen findings
        spleen = findings.get('spleen', {})
        normalized['spleen_size'] = self._validate_enum(spleen.get('size'), allowed_values['spleen_size'])
        normalized['spleen_focal_defect'] = self._validate_enum(spleen.get('focal_defect'), allowed_values['spleen_focal_defect'])
        
        # Normalize gall bladder findings
        gb = findings.get('gall_bladder', {})
        normalized['gb_calculus'] = self._validate_enum(gb.get('calculus'), allowed_values['gb_calculus'])
        normalized['gb_wall_edema'] = self._validate_enum(gb.get('wall_edema'), allowed_values['gb_wall_edema'])
        
        # Normalize kidney findings
        for side in ['right', 'left']:
            kidney = findings.get(f'{side}_kidney', {})
            normalized[f'{side}_kidney_size'] = self._validate_enum(kidney.get('size'), allowed_values['kidney_size'])
            normalized[f'{side}_kidney_texture'] = self._validate_enum(kidney.get('texture'), allowed_values['kidney_texture'])
            normalized[f'{side}_kidney_other'] = self._truncate_text(kidney.get('other'), 200)
        
        # Normalize pancreas findings
        pancreas = findings.get('pancreas', {})
        normalized['pancreas_findings'] = self._truncate_text(pancreas.get('findings'), 500)
        
        # Normalize urinary bladder findings
        bladder = findings.get('urinary_bladder', {})
        normalized['bladder_filling'] = self._validate_enum(bladder.get('filling'), allowed_values['bladder_filling'])
        normalized['bladder_stone_mass'] = self._validate_enum(bladder.get('stone_mass'), allowed_values['bladder_stone_mass'])
        normalized['bladder_mucosal_irregularity'] = self._validate_enum(bladder.get('mucosal_irregularity'), allowed_values['bladder_mucosal_irregularity'])
        
        # Normalize prostate findings
        prostate = findings.get('prostate', {})
        normalized['prostate_findings'] = self._truncate_text(prostate.get('findings'), 500)
        
        # Normalize additional findings
        additional = findings.get('additional', {})
        normalized['ascites'] = self._validate_enum(additional.get('ascites'), allowed_values['ascites'])
        normalized['pleural_effusions'] = self._validate_enum(additional.get('pleural_effusions'), allowed_values['pleural_effusions'])
        normalized['para_aortic_lymph_nodes'] = self._validate_enum(additional.get('para_aortic_lymph_nodes'), allowed_values['para_aortic_lymph_nodes'])
        normalized['other_findings'] = self._truncate_text(additional.get('other'), 200)
        
        # Normalize comments
        normalized['comments'] = self._truncate_text(findings.get('comments'), 1000)
        
        # Include confidence scores
        normalized['confidence_scores'] = findings.get('confidence_scores', {})
        
        return normalized
    
    def _validate_enum(self, value: Optional[str], allowed: list) -> Optional[str]:
        """
        Validate that a value is in the allowed list.
        
        Args:
            value: Value to validate
            allowed: List of allowed values
        
        Returns:
            The value if valid, None otherwise
        """
        if value is None:
            return None
        
        # Check exact match
        if value in allowed:
            return value
        
        # Check case-insensitive match
        for allowed_val in allowed:
            if value.lower() == allowed_val.lower():
                return allowed_val
        
        # Log warning for invalid value
        self.logger.warning(f"Invalid enumerated value: {value}. Allowed: {allowed}")
        return None
    
    def _truncate_text(self, text: Optional[str], max_length: int) -> Optional[str]:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
        
        Returns:
            Truncated text or None
        """
        if text is None:
            return None
        
        text = str(text).strip()
        if not text:
            return None
        
        if len(text) > max_length:
            self.logger.warning(f"Truncating text from {len(text)} to {max_length} characters")
            return text[:max_length]
        
        return text
    
    def _create_minimal_structured_findings(self) -> Dict[str, Any]:
        """
        Create minimal structured findings when no images are available.
        
        Returns:
            Minimal structured findings dictionary
        """
        return {
            'liver_size': None,
            'liver_texture': None,
            'liver_focal_defect': None,
            'liver_cbd': None,
            'liver_pv': None,
            'spleen_size': None,
            'spleen_focal_defect': None,
            'gb_calculus': None,
            'gb_wall_edema': None,
            'right_kidney_size': None,
            'right_kidney_texture': None,
            'right_kidney_other': None,
            'left_kidney_size': None,
            'left_kidney_texture': None,
            'left_kidney_other': None,
            'pancreas_findings': None,
            'bladder_filling': None,
            'bladder_stone_mass': None,
            'bladder_mucosal_irregularity': None,
            'prostate_findings': None,
            'ascites': None,
            'pleural_effusions': None,
            'para_aortic_lymph_nodes': None,
            'other_findings': None,
            'comments': 'Findings extraction could not be performed due to missing images.',
            'confidence_scores': {'overall': 0.0}
        }
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the structured findings output.
        
        Args:
            output: The output dictionary to validate
        
        Returns:
            True if output is valid, False otherwise
        """
        if not isinstance(output, dict):
            self.logger.error("Output is not a dictionary")
            return False
        
        # Required keys (all fields from AIGeneratedFindings model)
        required_keys = [
            'liver_size', 'liver_texture', 'liver_focal_defect', 'liver_cbd', 'liver_pv',
            'spleen_size', 'spleen_focal_defect',
            'gb_calculus', 'gb_wall_edema',
            'right_kidney_size', 'right_kidney_texture', 'right_kidney_other',
            'left_kidney_size', 'left_kidney_texture', 'left_kidney_other',
            'pancreas_findings',
            'bladder_filling', 'bladder_stone_mass', 'bladder_mucosal_irregularity',
            'prostate_findings',
            'ascites', 'pleural_effusions', 'para_aortic_lymph_nodes', 'other_findings',
            'comments',
            'confidence_scores'
        ]
        
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        # Validate confidence_scores is a dictionary
        if not isinstance(output['confidence_scores'], dict):
            self.logger.error("confidence_scores must be a dictionary")
            return False
        
        self.logger.info("Output validation passed")
        return True
