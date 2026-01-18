"""
Agent D: Diagnostic Reasoning

This agent generates diagnostic reasoning and differential diagnosis based on
the findings extracted from ultrasound images and clinical context. It synthesizes
information from previous agents to provide a structured diagnostic assessment.

The agent processes findings and clinical context to generate a differential
diagnosis list with supporting reasoning for each potential diagnosis.
"""

import logging
import json
from typing import Dict, Any, Optional
from openai import OpenAI
import os
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DiagnosticReasoningAgent(BaseAgent):
    """
    Agent D: Diagnostic Reasoning
    
    Generates diagnostic reasoning from:
    - Clinical context (from Agent A)
    - Image findings (from Agent C)
    
    Output includes:
    - Differential diagnosis list (ranked by likelihood)
    - Supporting reasoning for each diagnosis
    - Key findings that support or refute each diagnosis
    - Recommended follow-up or additional studies
    - Clinical significance assessment
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Diagnostic Reasoning Agent.
        
        Args:
            config: Optional configuration dictionary containing:
                - api_key: OpenAI API key (defaults to env variable)
                - model: Model to use (defaults to gpt-4o)
                - temperature: Temperature for generation (defaults to 0.2)
        """
        super().__init__(agent_name='agent_d_reasoning', config=config)
        
        # Initialize OpenAI client
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.2)
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for diagnostic reasoning.
        
        Returns:
            The system prompt for the agent
        """
        return """You are a diagnostic reasoning specialist for radiology AI systems.

Your task is to synthesize clinical context and imaging findings to generate a structured differential diagnosis with supporting reasoning.

You will be provided with:
1. **Clinical Context**: Patient history, indication, lab results, and clinical questions
2. **Imaging Findings**: Structured findings from ultrasound image analysis

Your goal is to:
- Generate a ranked differential diagnosis list
- Provide clear reasoning for each diagnosis
- Identify key findings that support or refute each diagnosis
- Assess clinical significance
- Recommend appropriate follow-up

**Output Format**: Return a valid JSON object with the following structure:
{
    "differential_diagnosis": [
        {
            "diagnosis": "string - specific diagnosis name",
            "likelihood": "string - high/moderate/low/cannot exclude",
            "supporting_findings": ["list", "of", "findings", "that", "support", "this"],
            "contradicting_findings": ["list", "of", "findings", "against", "this"],
            "reasoning": "string - detailed explanation of diagnostic reasoning",
            "clinical_significance": "string - significance and urgency assessment"
        }
    ],
    "primary_diagnosis": "string - most likely diagnosis based on available information",
    "key_findings_summary": ["list", "of", "most", "important", "findings"],
    "clinical_correlation": "string - how findings correlate with clinical presentation",
    "recommendations": {
        "follow_up_imaging": ["list", "of", "recommended", "imaging", "studies"],
        "clinical_follow_up": ["list", "of", "recommended", "clinical", "actions"],
        "additional_workup": ["list", "of", "additional", "tests", "or", "consultations"]
    },
    "confidence_assessment": {
        "diagnostic_confidence": "float 0-1 - confidence in primary diagnosis",
        "factors_affecting_confidence": ["list", "of", "factors", "affecting", "confidence"]
    },
    "summary": "string - concise summary of diagnostic reasoning"
}

**Guidelines**:
- Rank diagnoses by likelihood based on findings and clinical context
- Be specific with diagnosis names (avoid vague terms)
- Clearly explain reasoning using medical knowledge
- Consider both common and serious diagnoses (don't miss critical findings)
- If findings are normal, state "No significant abnormality" as primary diagnosis
- Include "cannot exclude" for diagnoses that require additional workup
- Correlate imaging findings with clinical presentation
- Recommend appropriate follow-up based on findings
- Be honest about diagnostic uncertainty
- Use standard medical terminology
- Consider differential diagnosis breadth (typically 2-5 diagnoses)

**Important**:
- Always consider clinical context when interpreting findings
- Flag urgent or critical findings that require immediate attention
- If findings are non-specific, acknowledge limitations
- Provide actionable recommendations for clinicians

Return ONLY the JSON object, no additional text."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate diagnostic reasoning from findings and clinical context.
        
        Args:
            input_data: Dictionary containing:
                - case_id: Case identifier
                - clinical_context: Clinical context from Agent A
                - findings: Findings from Agent C
        
        Returns:
            Dictionary containing diagnostic reasoning:
                - differential_diagnosis: List of potential diagnoses with reasoning
                - primary_diagnosis: Most likely diagnosis
                - key_findings_summary: Most important findings
                - clinical_correlation: Correlation with clinical presentation
                - recommendations: Follow-up and additional workup recommendations
                - confidence_assessment: Confidence in diagnosis
                - summary: Brief diagnostic reasoning summary
        
        Raises:
            ValueError: If required input data is missing
            Exception: If API call fails
        """
        self.logger.info(f"Processing diagnostic reasoning for case {input_data.get('case_id')}")
        
        # Extract required data
        clinical_context = input_data.get('clinical_context', {})
        findings = input_data.get('findings', {})
        
        # Validate inputs
        if not clinical_context:
            self.logger.warning("No clinical context provided")
        
        if not findings:
            self.logger.warning("No findings provided")
            return self._create_minimal_reasoning()
        
        # Format inputs for the LLM
        formatted_input = self._format_reasoning_input(clinical_context, findings)
        
        # Call OpenAI API to generate diagnostic reasoning
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_prompt_template()},
                    {"role": "user", "content": formatted_input}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"},
                max_tokens=3000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            diagnostic_reasoning = json.loads(content)
            
            self.logger.info("Successfully generated diagnostic reasoning")
            return diagnostic_reasoning
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise Exception(f"Failed to generate diagnostic reasoning: {str(e)}")
    
    def _format_reasoning_input(
        self,
        clinical_context: Dict[str, Any],
        findings: Dict[str, Any]
    ) -> str:
        """
        Format clinical context and findings for the reasoning prompt.
        
        Args:
            clinical_context: Clinical context dictionary from Agent A
            findings: Findings dictionary from Agent C
        
        Returns:
            Formatted input string for the LLM
        """
        sections = []
        
        # Format clinical context
        sections.append("=== CLINICAL CONTEXT ===")
        
        if clinical_context.get('clinical_indication'):
            sections.append(f"\nClinical Indication:\n{clinical_context['clinical_indication']}")
        
        if clinical_context.get('relevant_history'):
            sections.append(f"\nRelevant History:\n{clinical_context['relevant_history']}")
        
        if clinical_context.get('pertinent_labs'):
            labs = clinical_context['pertinent_labs']
            if labs:
                lab_str = "\n".join([f"  - {k}: {v}" for k, v in labs.items()])
                sections.append(f"\nPertinent Labs:\n{lab_str}")
        
        if clinical_context.get('risk_factors'):
            risk_factors = clinical_context['risk_factors']
            if risk_factors:
                sections.append(f"\nRisk Factors:\n  - " + "\n  - ".join(risk_factors))
        
        if clinical_context.get('clinical_questions'):
            questions = clinical_context['clinical_questions']
            if questions:
                sections.append(f"\nClinical Questions:\n  - " + "\n  - ".join(questions))
        
        # Format findings
        sections.append("\n\n=== IMAGING FINDINGS ===")
        
        if findings.get('summary'):
            sections.append(f"\nFindings Summary:\n{findings['summary']}")
        
        if findings.get('organ_assessment'):
            organ = findings['organ_assessment']
            sections.append(f"\nOrgan Assessment:")
            sections.append(f"  - Size: {organ.get('size', 'Not specified')}")
            sections.append(f"  - Echogenicity: {organ.get('echogenicity', 'Not specified')}")
            sections.append(f"  - Echotexture: {organ.get('echotexture', 'Not specified')}")
            sections.append(f"  - Surface: {organ.get('surface', 'Not specified')}")
        
        if findings.get('focal_lesions'):
            lesions = findings['focal_lesions']
            if lesions:
                sections.append(f"\nFocal Lesions ({len(lesions)}):")
                for idx, lesion in enumerate(lesions, 1):
                    sections.append(f"  Lesion {idx}:")
                    sections.append(f"    - Location: {lesion.get('location', 'Not specified')}")
                    sections.append(f"    - Size: {lesion.get('size', 'Not specified')}")
                    sections.append(f"    - Echogenicity: {lesion.get('echogenicity', 'Not specified')}")
                    sections.append(f"    - Characteristics: {lesion.get('characteristics', 'Not specified')}")
                    if lesion.get('description'):
                        sections.append(f"    - Description: {lesion['description']}")
        
        if findings.get('vascular_findings'):
            vascular = findings['vascular_findings']
            sections.append(f"\nVascular Findings:")
            sections.append(f"  - Portal Vein: {vascular.get('portal_vein', 'Not specified')}")
            sections.append(f"  - Hepatic Veins: {vascular.get('hepatic_veins', 'Not specified')}")
            if vascular.get('abnormalities'):
                sections.append(f"  - Abnormalities: " + ", ".join(vascular['abnormalities']))
        
        if findings.get('biliary_system'):
            biliary = findings['biliary_system']
            sections.append(f"\nBiliary System:")
            sections.append(f"  - Intrahepatic Ducts: {biliary.get('intrahepatic_ducts', 'Not specified')}")
            sections.append(f"  - Common Bile Duct: {biliary.get('common_bile_duct', 'Not specified')}")
            if biliary.get('abnormalities'):
                sections.append(f"  - Abnormalities: " + ", ".join(biliary['abnormalities']))
        
        if findings.get('additional_findings'):
            additional = findings['additional_findings']
            sections.append(f"\nAdditional Findings:")
            sections.append(f"  - Ascites: {additional.get('ascites', 'Not specified')}")
            if additional.get('other'):
                sections.append(f"  - Other: " + ", ".join(additional['other']))
        
        if findings.get('measurements'):
            measurements = findings['measurements']
            if measurements:
                sections.append(f"\nMeasurements:")
                for key, value in measurements.items():
                    sections.append(f"  - {key}: {value}")
        
        return "\n".join(sections)
    
    def _create_minimal_reasoning(self) -> Dict[str, Any]:
        """
        Create minimal diagnostic reasoning when no findings are available.
        
        Returns:
            Minimal diagnostic reasoning dictionary
        """
        return {
            "differential_diagnosis": [
                {
                    "diagnosis": "Insufficient information for diagnosis",
                    "likelihood": "cannot exclude",
                    "supporting_findings": [],
                    "contradicting_findings": [],
                    "reasoning": "No imaging findings available for diagnostic reasoning.",
                    "clinical_significance": "Unable to assess without imaging findings."
                }
            ],
            "primary_diagnosis": "Insufficient information for diagnosis",
            "key_findings_summary": ["No findings available"],
            "clinical_correlation": "Unable to correlate without imaging findings.",
            "recommendations": {
                "follow_up_imaging": ["Repeat imaging study with adequate image quality"],
                "clinical_follow_up": ["Clinical assessment by referring physician"],
                "additional_workup": []
            },
            "confidence_assessment": {
                "diagnostic_confidence": 0.0,
                "factors_affecting_confidence": ["No imaging findings available"]
            },
            "summary": "Diagnostic reasoning could not be performed due to missing imaging findings."
        }
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the diagnostic reasoning output.
        
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
            'differential_diagnosis',
            'primary_diagnosis',
            'key_findings_summary',
            'clinical_correlation',
            'recommendations',
            'confidence_assessment',
            'summary'
        ]
        
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        # Validate differential_diagnosis is a list
        if not isinstance(output['differential_diagnosis'], list):
            self.logger.error("differential_diagnosis must be a list")
            return False
        
        # Validate at least one diagnosis is present
        if len(output['differential_diagnosis']) == 0:
            self.logger.error("differential_diagnosis must contain at least one diagnosis")
            return False
        
        # Validate each diagnosis entry
        for idx, diagnosis in enumerate(output['differential_diagnosis']):
            if not isinstance(diagnosis, dict):
                self.logger.error(f"Diagnosis {idx} is not a dictionary")
                return False
            
            required_diagnosis_keys = [
                'diagnosis',
                'likelihood',
                'supporting_findings',
                'contradicting_findings',
                'reasoning',
                'clinical_significance'
            ]
            
            for key in required_diagnosis_keys:
                if key not in diagnosis:
                    self.logger.error(f"Diagnosis {idx} missing required key: {key}")
                    return False
            
            # Validate lists
            if not isinstance(diagnosis['supporting_findings'], list):
                self.logger.error(f"Diagnosis {idx} supporting_findings must be a list")
                return False
            
            if not isinstance(diagnosis['contradicting_findings'], list):
                self.logger.error(f"Diagnosis {idx} contradicting_findings must be a list")
                return False
        
        # Validate primary_diagnosis is a string
        if not isinstance(output['primary_diagnosis'], str):
            self.logger.error("primary_diagnosis must be a string")
            return False
        
        # Validate key_findings_summary is a list
        if not isinstance(output['key_findings_summary'], list):
            self.logger.error("key_findings_summary must be a list")
            return False
        
        # Validate clinical_correlation is a string
        if not isinstance(output['clinical_correlation'], str):
            self.logger.error("clinical_correlation must be a string")
            return False
        
        # Validate recommendations structure
        if not isinstance(output['recommendations'], dict):
            self.logger.error("recommendations must be a dictionary")
            return False
        
        recommendations = output['recommendations']
        required_rec_keys = ['follow_up_imaging', 'clinical_follow_up', 'additional_workup']
        
        for key in required_rec_keys:
            if key not in recommendations:
                self.logger.error(f"recommendations missing required key: {key}")
                return False
            
            if not isinstance(recommendations[key], list):
                self.logger.error(f"recommendations.{key} must be a list")
                return False
        
        # Validate confidence_assessment structure
        if not isinstance(output['confidence_assessment'], dict):
            self.logger.error("confidence_assessment must be a dictionary")
            return False
        
        confidence = output['confidence_assessment']
        
        if 'diagnostic_confidence' not in confidence:
            self.logger.error("confidence_assessment missing diagnostic_confidence")
            return False
        
        try:
            conf_value = float(confidence['diagnostic_confidence'])
            if conf_value < 0 or conf_value > 1:
                self.logger.error(f"diagnostic_confidence out of range: {conf_value}")
                return False
        except (ValueError, TypeError):
            self.logger.error("diagnostic_confidence is not a valid float")
            return False
        
        if 'factors_affecting_confidence' not in confidence:
            self.logger.error("confidence_assessment missing factors_affecting_confidence")
            return False
        
        if not isinstance(confidence['factors_affecting_confidence'], list):
            self.logger.error("factors_affecting_confidence must be a list")
            return False
        
        # Ensure summary is present and non-empty
        if not output.get('summary'):
            self.logger.error("summary must be present and non-empty")
            return False
        
        self.logger.info("Output validation passed")
        return True
