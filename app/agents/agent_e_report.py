"""
Agent E: Structured Report Drafting

This agent creates a structured radiology report by synthesizing outputs from
all previous agents in the pipeline. It generates a comprehensive, professional
report following standard radiology report format.

The agent combines clinical context, quality assessment, findings, and diagnostic
reasoning to produce a complete draft report ready for radiologist review.
"""

import logging
import json
from typing import Dict, Any, Optional
from openai import OpenAI
import os
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ReportDraftingAgent(BaseAgent):
    """
    Agent E: Structured Report Drafting
    
    Synthesizes all previous agent outputs to create:
    - Complete structured radiology report
    - Standard report sections (Clinical History, Technique, Findings, Impression)
    - Professional medical language and formatting
    - Appropriate hedging and uncertainty language
    - Actionable recommendations
    
    Input from previous agents:
    - Agent A: Clinical context
    - Agent B: Quality assessment
    - Agent C: Findings
    - Agent D: Diagnostic reasoning
    
    Output includes:
    - Structured report with all standard sections
    - Professional formatting and language
    - Appropriate medical terminology
    - Clear and actionable impression
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Report Drafting Agent.
        
        Args:
            config: Optional configuration dictionary containing:
                - api_key: OpenAI API key (defaults to env variable)
                - model: Model to use (defaults to gpt-4o)
                - temperature: Temperature for generation (defaults to 0.3)
        """
        super().__init__(agent_name='agent_e_report', config=config)
        
        # Initialize OpenAI client
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.3)
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for report drafting.
        
        Returns:
            The system prompt for the agent
        """
        return """You are a radiology report drafting specialist for AI-assisted reporting systems.

Your task is to synthesize all previous agent outputs into a complete, professional radiology report following standard format and conventions.

You will be provided with:
1. **Clinical Context**: Patient history, indication, labs, and clinical questions
2. **Quality Assessment**: Image quality scores and technical adequacy
3. **Findings**: Structured imaging findings from ultrasound analysis
4. **Diagnostic Reasoning**: Differential diagnosis and clinical correlation

Your goal is to create a structured radiology report with the following sections:

**CLINICAL HISTORY**
- Brief summary of relevant clinical information
- Indication for the study
- Pertinent patient history

**TECHNIQUE**
- Imaging modality and approach
- Image quality assessment
- Any technical limitations

**FINDINGS**
- Detailed description of imaging findings
- Organized by anatomical structures
- Include measurements with units
- Describe normal and abnormal findings
- Use standard radiological terminology

**IMPRESSION**
- Concise summary of key findings
- Primary diagnosis or most likely diagnosis
- Differential diagnoses if applicable
- Clinical significance
- Recommendations for follow-up or additional studies

**Output Format**: Return a valid JSON object with the following structure:
{
    "report_sections": {
        "clinical_history": "string - formatted clinical history section",
        "technique": "string - formatted technique section",
        "findings": "string - formatted findings section with detailed descriptions",
        "impression": "string - formatted impression section with diagnosis and recommendations"
    },
    "structured_data": {
        "primary_diagnosis": "string - primary diagnosis",
        "secondary_diagnoses": ["list", "of", "secondary", "diagnoses"],
        "key_findings": ["list", "of", "key", "findings"],
        "recommendations": ["list", "of", "recommendations"],
        "critical_findings": ["list", "of", "critical", "findings", "requiring", "immediate", "attention"]
    },
    "report_metadata": {
        "study_type": "string - type of ultrasound study",
        "quality_assessment": "string - overall quality (excellent/good/adequate/limited/poor)",
        "confidence_level": "string - high/moderate/low",
        "limitations": ["list", "of", "study", "limitations"]
    },
    "full_report_text": "string - complete formatted report as continuous text",
    "summary": "string - one-sentence summary of the report"
}

**Guidelines for Report Writing**:

1. **Professional Language**:
   - Use standard medical terminology
   - Write in third person, past tense
   - Be clear, concise, and precise
   - Avoid ambiguous language

2. **Clinical History Section**:
   - Start with patient age and gender if available
   - State the clinical indication
   - Include relevant history (brief, 2-3 sentences)
   - Mention pertinent lab values if relevant

3. **Technique Section**:
   - State imaging modality (e.g., "Grayscale and color Doppler ultrasound of the liver")
   - Mention image quality and adequacy
   - Note any technical limitations
   - Keep brief (1-2 sentences)

4. **Findings Section**:
   - Start with overall organ assessment
   - Describe findings systematically by structure
   - Include measurements with units
   - Describe focal lesions in detail (location, size, characteristics)
   - Mention normal structures when relevant
   - Use numbered or bulleted lists for multiple findings
   - Be thorough but organized

5. **Impression Section**:
   - Start with primary diagnosis or "No significant abnormality"
   - List differential diagnoses if applicable
   - State clinical significance
   - Provide clear recommendations
   - Use numbered list for multiple impressions
   - Be decisive but acknowledge uncertainty when appropriate

6. **Uncertainty and Hedging**:
   - Use "likely", "suggestive of", "compatible with" when appropriate
   - State "cannot exclude" for diagnoses requiring additional workup
   - Acknowledge limitations explicitly
   - Recommend correlation with clinical findings when needed

7. **Critical Findings**:
   - Clearly identify urgent or critical findings
   - Place critical findings prominently in impression
   - Recommend immediate clinical correlation or follow-up

8. **Formatting**:
   - Use proper capitalization for section headers
   - Use complete sentences
   - Organize findings logically
   - Use consistent terminology throughout

**Important**:
- Synthesize information from all agents coherently
- Maintain consistency between findings and impression
- Ensure all significant findings are mentioned in impression
- Provide actionable recommendations
- If quality is limited, acknowledge impact on interpretation
- Never fabricate findings not present in agent outputs
- Use appropriate hedging for uncertain findings

Return ONLY the JSON object, no additional text."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured radiology report from all agent outputs.
        
        Args:
            input_data: Dictionary containing:
                - case_id: Case identifier
                - clinical_context: Output from Agent A
                - quality_assessment: Output from Agent B
                - findings: Output from Agent C
                - diagnostic_reasoning: Output from Agent D
        
        Returns:
            Dictionary containing structured report:
                - report_sections: Dictionary with clinical_history, technique, findings, impression
                - structured_data: Primary diagnosis, key findings, recommendations
                - report_metadata: Study type, quality, confidence, limitations
                - full_report_text: Complete formatted report text
                - summary: One-sentence summary
        
        Raises:
            ValueError: If required input data is missing
            Exception: If API call fails
        """
        self.logger.info(f"Processing report drafting for case {input_data.get('case_id')}")
        
        # Extract agent outputs
        clinical_context = input_data.get('clinical_context', {})
        quality_assessment = input_data.get('quality_assessment', {})
        findings = input_data.get('findings', {})
        diagnostic_reasoning = input_data.get('diagnostic_reasoning', {})
        
        # Validate that we have at least some data to work with
        if not any([clinical_context, findings, diagnostic_reasoning]):
            self.logger.warning("Insufficient data for report generation")
            return self._create_minimal_report()
        
        # Format all agent outputs for the LLM
        formatted_input = self._format_report_input(
            clinical_context,
            quality_assessment,
            findings,
            diagnostic_reasoning
        )
        
        # Call OpenAI API to generate the report
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_prompt_template()},
                    {"role": "user", "content": formatted_input}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"},
                max_tokens=4000
            )
            
            # Parse the response
            content = response.choices[0].message.content
            report = json.loads(content)
            
            self.logger.info("Successfully generated structured report")
            return report
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise Exception(f"Failed to generate report: {str(e)}")
    
    def _format_report_input(
        self,
        clinical_context: Dict[str, Any],
        quality_assessment: Dict[str, Any],
        findings: Dict[str, Any],
        diagnostic_reasoning: Dict[str, Any]
    ) -> str:
        """
        Format all agent outputs into a comprehensive input for report generation.
        
        Args:
            clinical_context: Clinical context from Agent A
            quality_assessment: Quality assessment from Agent B
            findings: Findings from Agent C
            diagnostic_reasoning: Diagnostic reasoning from Agent D
        
        Returns:
            Formatted input string for the LLM
        """
        sections = []
        
        # Section 1: Clinical Context
        sections.append("=" * 60)
        sections.append("AGENT A: CLINICAL CONTEXT")
        sections.append("=" * 60)
        
        if clinical_context:
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
        else:
            sections.append("\nNo clinical context available.")
        
        # Section 2: Quality Assessment
        sections.append("\n\n" + "=" * 60)
        sections.append("AGENT B: QUALITY ASSESSMENT")
        sections.append("=" * 60)
        
        if quality_assessment:
            if quality_assessment.get('overall_quality'):
                sections.append(f"\nOverall Quality: {quality_assessment['overall_quality']}")
            
            if quality_assessment.get('image_views'):
                views = quality_assessment['image_views']
                if views:
                    sections.append(f"\nImage Views ({len(views)}):")
                    for idx, view in enumerate(views, 1):
                        sections.append(f"  View {idx}:")
                        sections.append(f"    - Anatomical View: {view.get('anatomical_view', 'Not specified')}")
                        sections.append(f"    - Quality Score: {view.get('quality_score', 'Not specified')}")
                        sections.append(f"    - Technical Adequacy: {view.get('technical_adequacy', 'Not specified')}")
            
            if quality_assessment.get('technical_factors'):
                factors = quality_assessment['technical_factors']
                sections.append(f"\nTechnical Factors:")
                for key, value in factors.items():
                    sections.append(f"  - {key}: {value}")
            
            if quality_assessment.get('limitations'):
                limitations = quality_assessment['limitations']
                if limitations:
                    sections.append(f"\nLimitations:\n  - " + "\n  - ".join(limitations))
        else:
            sections.append("\nNo quality assessment available.")
        
        # Section 3: Findings
        sections.append("\n\n" + "=" * 60)
        sections.append("AGENT C: IMAGING FINDINGS")
        sections.append("=" * 60)
        
        if findings:
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
                        sections.append(f"    - Margins: {lesion.get('margins', 'Not specified')}")
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
            
            if findings.get('summary'):
                sections.append(f"\nFindings Summary:\n{findings['summary']}")
        else:
            sections.append("\nNo findings available.")
        
        # Section 4: Diagnostic Reasoning
        sections.append("\n\n" + "=" * 60)
        sections.append("AGENT D: DIAGNOSTIC REASONING")
        sections.append("=" * 60)
        
        if diagnostic_reasoning:
            if diagnostic_reasoning.get('primary_diagnosis'):
                sections.append(f"\nPrimary Diagnosis: {diagnostic_reasoning['primary_diagnosis']}")
            
            if diagnostic_reasoning.get('differential_diagnosis'):
                diff_dx = diagnostic_reasoning['differential_diagnosis']
                if diff_dx:
                    sections.append(f"\nDifferential Diagnosis ({len(diff_dx)}):")
                    for idx, dx in enumerate(diff_dx, 1):
                        sections.append(f"\n  {idx}. {dx.get('diagnosis', 'Not specified')} (Likelihood: {dx.get('likelihood', 'Not specified')})")
                        sections.append(f"     Reasoning: {dx.get('reasoning', 'Not specified')}")
                        if dx.get('supporting_findings'):
                            sections.append(f"     Supporting: " + ", ".join(dx['supporting_findings']))
                        if dx.get('contradicting_findings'):
                            sections.append(f"     Contradicting: " + ", ".join(dx['contradicting_findings']))
            
            if diagnostic_reasoning.get('key_findings_summary'):
                key_findings = diagnostic_reasoning['key_findings_summary']
                if key_findings:
                    sections.append(f"\nKey Findings:\n  - " + "\n  - ".join(key_findings))
            
            if diagnostic_reasoning.get('clinical_correlation'):
                sections.append(f"\nClinical Correlation:\n{diagnostic_reasoning['clinical_correlation']}")
            
            if diagnostic_reasoning.get('recommendations'):
                recs = diagnostic_reasoning['recommendations']
                if recs.get('follow_up_imaging'):
                    sections.append(f"\nFollow-up Imaging:\n  - " + "\n  - ".join(recs['follow_up_imaging']))
                if recs.get('clinical_follow_up'):
                    sections.append(f"\nClinical Follow-up:\n  - " + "\n  - ".join(recs['clinical_follow_up']))
                if recs.get('additional_workup'):
                    sections.append(f"\nAdditional Workup:\n  - " + "\n  - ".join(recs['additional_workup']))
            
            if diagnostic_reasoning.get('confidence_assessment'):
                conf = diagnostic_reasoning['confidence_assessment']
                sections.append(f"\nDiagnostic Confidence: {conf.get('diagnostic_confidence', 'Not specified')}")
                if conf.get('factors_affecting_confidence'):
                    sections.append(f"Factors Affecting Confidence:\n  - " + "\n  - ".join(conf['factors_affecting_confidence']))
        else:
            sections.append("\nNo diagnostic reasoning available.")
        
        # Final instruction
        sections.append("\n\n" + "=" * 60)
        sections.append("TASK")
        sections.append("=" * 60)
        sections.append("\nUsing all the information above, generate a complete, professional radiology report with all required sections.")
        
        return "\n".join(sections)
    
    def _create_minimal_report(self) -> Dict[str, Any]:
        """
        Create minimal report when insufficient data is available.
        
        Returns:
            Minimal report dictionary
        """
        minimal_text = """CLINICAL HISTORY
Insufficient clinical information available.

TECHNIQUE
Ultrasound examination. Image quality and technical details not available.

FINDINGS
Insufficient imaging data available for interpretation.

IMPRESSION
Study cannot be adequately interpreted due to insufficient data. Recommend repeat examination with complete clinical information and adequate image quality."""
        
        return {
            "report_sections": {
                "clinical_history": "Insufficient clinical information available.",
                "technique": "Ultrasound examination. Image quality and technical details not available.",
                "findings": "Insufficient imaging data available for interpretation.",
                "impression": "Study cannot be adequately interpreted due to insufficient data. Recommend repeat examination with complete clinical information and adequate image quality."
            },
            "structured_data": {
                "primary_diagnosis": "Insufficient data for diagnosis",
                "secondary_diagnoses": [],
                "key_findings": ["Insufficient data"],
                "recommendations": ["Repeat examination with complete clinical information"],
                "critical_findings": []
            },
            "report_metadata": {
                "study_type": "Ultrasound",
                "quality_assessment": "insufficient",
                "confidence_level": "low",
                "limitations": ["Insufficient clinical data", "Insufficient imaging data"]
            },
            "full_report_text": minimal_text,
            "summary": "Study cannot be adequately interpreted due to insufficient data."
        }
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the report drafting output.
        
        Args:
            output: The output dictionary to validate
        
        Returns:
            True if output is valid, False otherwise
        """
        if not isinstance(output, dict):
            self.logger.error("Output is not a dictionary")
            return False
        
        # Required top-level keys
        required_keys = [
            'report_sections',
            'structured_data',
            'report_metadata',
            'full_report_text',
            'summary'
        ]
        
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        # Validate report_sections structure
        if not isinstance(output['report_sections'], dict):
            self.logger.error("report_sections must be a dictionary")
            return False
        
        required_sections = ['clinical_history', 'technique', 'findings', 'impression']
        for section in required_sections:
            if section not in output['report_sections']:
                self.logger.error(f"Missing required report section: {section}")
                return False
            
            if not isinstance(output['report_sections'][section], str):
                self.logger.error(f"Report section {section} must be a string")
                return False
            
            if not output['report_sections'][section].strip():
                self.logger.error(f"Report section {section} cannot be empty")
                return False
        
        # Validate structured_data structure
        if not isinstance(output['structured_data'], dict):
            self.logger.error("structured_data must be a dictionary")
            return False
        
        required_structured_keys = [
            'primary_diagnosis',
            'secondary_diagnoses',
            'key_findings',
            'recommendations',
            'critical_findings'
        ]
        
        for key in required_structured_keys:
            if key not in output['structured_data']:
                self.logger.error(f"Missing required structured_data key: {key}")
                return False
        
        # Validate primary_diagnosis is a string
        if not isinstance(output['structured_data']['primary_diagnosis'], str):
            self.logger.error("primary_diagnosis must be a string")
            return False
        
        # Validate lists in structured_data
        list_keys = ['secondary_diagnoses', 'key_findings', 'recommendations', 'critical_findings']
        for key in list_keys:
            if not isinstance(output['structured_data'][key], list):
                self.logger.error(f"structured_data.{key} must be a list")
                return False
        
        # Validate report_metadata structure
        if not isinstance(output['report_metadata'], dict):
            self.logger.error("report_metadata must be a dictionary")
            return False
        
        required_metadata_keys = ['study_type', 'quality_assessment', 'confidence_level', 'limitations']
        for key in required_metadata_keys:
            if key not in output['report_metadata']:
                self.logger.error(f"Missing required report_metadata key: {key}")
                return False
        
        # Validate limitations is a list
        if not isinstance(output['report_metadata']['limitations'], list):
            self.logger.error("report_metadata.limitations must be a list")
            return False
        
        # Validate full_report_text is a non-empty string
        if not isinstance(output['full_report_text'], str):
            self.logger.error("full_report_text must be a string")
            return False
        
        if not output['full_report_text'].strip():
            self.logger.error("full_report_text cannot be empty")
            return False
        
        # Validate summary is a non-empty string
        if not isinstance(output['summary'], str):
            self.logger.error("summary must be a string")
            return False
        
        if not output['summary'].strip():
            self.logger.error("summary cannot be empty")
            return False
        
        self.logger.info("Output validation passed")
        return True
