"""
Agent A: Clinical Context Extraction

This agent extracts and structures clinical information from patient history,
clinical indication, and lab results to provide context for subsequent agents.

The agent processes unstructured clinical notes and returns a structured JSON
containing relevant clinical information that will guide image analysis and
diagnostic reasoning.
"""

import logging
import json
from typing import Dict, Any, Optional
from openai import OpenAI
import os
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ClinicalContextAgent(BaseAgent):
    """
    Agent A: Clinical Context Extraction
    
    Extracts structured clinical information from:
    - Patient history
    - Clinical indication
    - Lab results
    - Clinical notes
    
    Output includes:
    - Relevant medical history
    - Current symptoms and indication
    - Pertinent lab values
    - Risk factors
    - Clinical questions to address
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Clinical Context Agent.
        
        Args:
            config: Optional configuration dictionary containing:
                - api_key: OpenAI API key (defaults to env variable)
                - model: Model to use (defaults to gpt-4o)
                - temperature: Temperature for generation (defaults to 0.1)
        """
        super().__init__(agent_name='agent_a_context', config=config)
        
        # Initialize OpenAI client
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.1)
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for clinical context extraction.
        
        Returns:
            The system prompt for the agent
        """
        return """You are a clinical context extraction specialist for radiology AI systems.

Your task is to analyze clinical information and extract structured, relevant context that will guide ultrasound image analysis and diagnostic reasoning.

Extract and structure the following information:

1. **Relevant Medical History**: Past medical conditions, surgeries, or diagnoses relevant to the current study
2. **Current Clinical Indication**: The reason for the imaging study and presenting symptoms
3. **Pertinent Lab Results**: Any lab values that may inform image interpretation (liver enzymes, bilirubin, etc.)
4. **Risk Factors**: Patient risk factors relevant to potential diagnoses (age, comorbidities, medications)
5. **Clinical Questions**: Specific questions the referring physician wants answered

**Output Format**: Return a valid JSON object with the following structure:
{
    "relevant_history": "string - concise summary of relevant medical history",
    "clinical_indication": "string - reason for study and presenting symptoms",
    "pertinent_labs": {
        "lab_name": "value and interpretation"
    },
    "risk_factors": ["list", "of", "risk", "factors"],
    "clinical_questions": ["list", "of", "questions", "to", "address"],
    "summary": "string - brief clinical context summary for radiologist"
}

**Guidelines**:
- Be concise but comprehensive
- Focus on information relevant to ultrasound interpretation
- If information is missing or not provided, use null or empty arrays
- Maintain clinical accuracy and appropriate medical terminology
- Do not make assumptions beyond the provided information

Return ONLY the JSON object, no additional text."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured clinical context from case data.
        
        Args:
            input_data: Dictionary containing:
                - case_id: Case identifier
                - case_data: Dictionary with clinical information including:
                    - patient_history: Patient medical history
                    - clinical_indication: Indication for study
                    - lab_results: Laboratory results
                    - clinical_history: Additional clinical history
                    - indication: Study indication
                    - structured_findings: User-provided structured findings (optional)
        
        Returns:
            Dictionary containing structured clinical context:
                - relevant_history: Relevant medical history
                - clinical_indication: Reason for study
                - pertinent_labs: Relevant lab values
                - risk_factors: Patient risk factors
                - clinical_questions: Questions to address
                - summary: Brief clinical summary
                - structured_findings: User-provided findings (if available)
        
        Raises:
            ValueError: If required input data is missing
            Exception: If API call fails
        """
        self.logger.info(f"Processing clinical context for case {input_data.get('case_id')}")
        
        # Extract case data
        case_data = input_data.get('case_data', {})
        
        # Gather all available clinical information
        patient_history = case_data.get('patient_history', '')
        clinical_indication = case_data.get('clinical_indication', '')
        lab_results = case_data.get('lab_results', '')
        clinical_history = case_data.get('clinical_history', '')
        indication = case_data.get('indication', '')
        structured_findings = case_data.get('structured_findings')
        
        # Combine all clinical information
        clinical_info = self._combine_clinical_info(
            patient_history=patient_history,
            clinical_indication=clinical_indication,
            lab_results=lab_results,
            clinical_history=clinical_history,
            indication=indication,
            structured_findings=structured_findings
        )
        
        if not clinical_info.strip():
            self.logger.warning("No clinical information provided, returning minimal context")
            context = self._create_minimal_context()
            # Include structured findings even if other clinical info is missing
            if structured_findings:
                context['structured_findings'] = structured_findings
            return context
        
        # Call OpenAI API to extract structured context
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_prompt_template()},
                    {"role": "user", "content": f"Clinical Information:\n\n{clinical_info}"}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            content = response.choices[0].message.content
            clinical_context = json.loads(content)
            
            # Include structured findings in the context
            if structured_findings:
                clinical_context['structured_findings'] = structured_findings
            
            self.logger.info("Successfully extracted clinical context")
            return clinical_context
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise Exception(f"Failed to extract clinical context: {str(e)}")
    
    def _combine_clinical_info(
        self,
        patient_history: str,
        clinical_indication: str,
        lab_results: str,
        clinical_history: str,
        indication: str,
        structured_findings: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Combine all available clinical information into a single text.
        
        Args:
            patient_history: Patient medical history
            clinical_indication: Clinical indication for study
            lab_results: Laboratory results
            clinical_history: Additional clinical history
            indication: Study indication
            structured_findings: User-provided structured findings (optional)
        
        Returns:
            Combined clinical information text
        """
        sections = []
        
        if patient_history and patient_history.strip():
            sections.append(f"Patient History:\n{patient_history.strip()}")
        
        if clinical_history and clinical_history.strip():
            sections.append(f"Clinical History:\n{clinical_history.strip()}")
        
        # Combine indication fields (avoid duplication)
        indication_text = clinical_indication or indication
        if indication_text and indication_text.strip():
            sections.append(f"Clinical Indication:\n{indication_text.strip()}")
        
        if lab_results and lab_results.strip():
            sections.append(f"Laboratory Results:\n{lab_results.strip()}")
        
        # Include structured findings if provided
        if structured_findings:
            findings_text = self._format_structured_findings(structured_findings)
            if findings_text:
                sections.append(f"User-Provided Structured Findings:\n{findings_text}")
        
        return "\n\n".join(sections)
    
    def _create_minimal_context(self) -> Dict[str, Any]:
        """
        Create a minimal clinical context when no information is provided.
        
        Returns:
            Minimal clinical context dictionary
        """
        return {
            "relevant_history": None,
            "clinical_indication": "No clinical indication provided",
            "pertinent_labs": {},
            "risk_factors": [],
            "clinical_questions": [],
            "summary": "Limited clinical information available. Interpretation based on imaging findings only."
        }
    
    def _format_structured_findings(self, findings: Dict[str, Any]) -> str:
        """
        Format structured findings dictionary into readable text.
        
        Args:
            findings: Dictionary containing structured findings
        
        Returns:
            Formatted findings text
        """
        if not findings:
            return ""
        
        sections = []
        
        # Liver findings
        liver_items = []
        if findings.get('liver_size'):
            liver_items.append(f"Size: {findings['liver_size']}")
        if findings.get('liver_texture'):
            liver_items.append(f"Texture: {findings['liver_texture']}")
        if findings.get('liver_focal_defect'):
            liver_items.append(f"Focal defect: {findings['liver_focal_defect']}")
        if findings.get('liver_cbd'):
            liver_items.append(f"CBD: {findings['liver_cbd']}")
        if findings.get('liver_pv'):
            liver_items.append(f"Portal vein: {findings['liver_pv']}")
        if liver_items:
            sections.append(f"Liver: {', '.join(liver_items)}")
        
        # Spleen findings
        spleen_items = []
        if findings.get('spleen_size'):
            spleen_items.append(f"Size: {findings['spleen_size']}")
        if findings.get('spleen_focal_defect'):
            spleen_items.append(f"Focal defect: {findings['spleen_focal_defect']}")
        if spleen_items:
            sections.append(f"Spleen: {', '.join(spleen_items)}")
        
        # Gall Bladder findings
        gb_items = []
        if findings.get('gb_calculus'):
            gb_items.append(f"Calculus: {findings['gb_calculus']}")
        if findings.get('gb_wall_edema'):
            gb_items.append(f"Wall edema: {findings['gb_wall_edema']}")
        if gb_items:
            sections.append(f"Gall Bladder: {', '.join(gb_items)}")
        
        # Kidney findings
        for side in ['right', 'left']:
            kidney_items = []
            if findings.get(f'{side}_kidney_size'):
                kidney_items.append(f"Size: {findings[f'{side}_kidney_size']}")
            if findings.get(f'{side}_kidney_texture'):
                kidney_items.append(f"Texture: {findings[f'{side}_kidney_texture']}")
            if findings.get(f'{side}_kidney_other'):
                kidney_items.append(f"Other: {findings[f'{side}_kidney_other']}")
            if kidney_items:
                sections.append(f"{side.capitalize()} Kidney: {', '.join(kidney_items)}")
        
        # Pancreas
        if findings.get('pancreas_findings'):
            sections.append(f"Pancreas: {findings['pancreas_findings']}")
        
        # Urinary Bladder
        bladder_items = []
        if findings.get('bladder_filling'):
            bladder_items.append(f"Filling: {findings['bladder_filling']}")
        if findings.get('bladder_stone_mass'):
            bladder_items.append(f"Stone/mass: {findings['bladder_stone_mass']}")
        if findings.get('bladder_mucosal_irregularity'):
            bladder_items.append(f"Mucosal irregularity: {findings['bladder_mucosal_irregularity']}")
        if bladder_items:
            sections.append(f"Urinary Bladder: {', '.join(bladder_items)}")
        
        # Prostate
        if findings.get('prostate_findings'):
            sections.append(f"Prostate: {findings['prostate_findings']}")
        
        # Additional findings
        additional_items = []
        if findings.get('ascites'):
            additional_items.append(f"Ascites: {findings['ascites']}")
        if findings.get('pleural_effusions'):
            additional_items.append(f"Pleural effusions: {findings['pleural_effusions']}")
        if findings.get('para_aortic_lymph_nodes'):
            additional_items.append(f"Para-aortic lymph nodes: {findings['para_aortic_lymph_nodes']}")
        if findings.get('other_findings'):
            additional_items.append(f"Other: {findings['other_findings']}")
        if additional_items:
            sections.append(f"Additional: {', '.join(additional_items)}")
        
        # Comments
        if findings.get('comments'):
            sections.append(f"Comments: {findings['comments']}")
        
        return "\n".join(sections)
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the clinical context output.
        
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
            'relevant_history',
            'clinical_indication',
            'pertinent_labs',
            'risk_factors',
            'clinical_questions',
            'summary'
        ]
        
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        # Type validation
        if not isinstance(output['pertinent_labs'], dict):
            self.logger.error("pertinent_labs must be a dictionary")
            return False
        
        if not isinstance(output['risk_factors'], list):
            self.logger.error("risk_factors must be a list")
            return False
        
        if not isinstance(output['clinical_questions'], list):
            self.logger.error("clinical_questions must be a list")
            return False
        
        # Ensure summary is present and non-empty
        if not output.get('summary'):
            self.logger.error("summary must be present and non-empty")
            return False
        
        self.logger.info("Output validation passed")
        return True
