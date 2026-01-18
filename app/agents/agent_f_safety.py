"""
Agent F: Safety and Consistency Validation

This agent performs final validation of the complete radiology report to ensure:
- Consistency between findings and impression
- Completeness of all required sections
- Safety checks for critical findings
- Confidence scoring based on data quality
- Flagging of potential errors or omissions

The agent acts as a quality control checkpoint before the report is presented
to the radiologist for review.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from openai import OpenAI
import os
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SafetyValidationAgent(BaseAgent):
    """
    Agent F: Safety and Consistency Validation
    
    Validates the complete report for:
    - Consistency: Findings match impression, no contradictions
    - Completeness: All required sections present and adequate
    - Safety: Critical findings properly flagged and addressed
    - Quality: Confidence scoring based on image quality and diagnostic certainty
    - Errors: Common mistakes, omissions, or logical inconsistencies
    
    Input from previous agents:
    - Agent A: Clinical context
    - Agent B: Quality assessment
    - Agent C: Findings
    - Agent D: Diagnostic reasoning
    - Agent E: Draft report
    
    Output includes:
    - Validation status (pass/fail/warning)
    - Consistency checks results
    - Completeness assessment
    - Safety flags for critical findings
    - Confidence score (0-1)
    - List of issues found
    - Recommendations for improvement
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Safety Validation Agent.
        
        Args:
            config: Optional configuration dictionary containing:
                - api_key: OpenAI API key (defaults to env variable)
                - model: Model to use (defaults to gpt-4o)
                - temperature: Temperature for generation (defaults to 0.1)
        """
        super().__init__(agent_name='agent_f_safety', config=config)
        
        # Initialize OpenAI client
        api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in config or environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = self.config.get('model', 'gpt-4o')
        self.temperature = self.config.get('temperature', 0.1)
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for safety validation.
        
        Returns:
            The system prompt for the agent
        """
        return """You are a safety and quality validation specialist for AI-assisted radiology reporting systems.

Your task is to perform comprehensive validation of a complete radiology report and all intermediate agent outputs to ensure safety, consistency, completeness, and quality.

You will be provided with:
1. **Clinical Context**: Patient history, indication, labs
2. **Quality Assessment**: Image quality scores and limitations
3. **Findings**: Structured imaging findings
4. **Diagnostic Reasoning**: Differential diagnosis and reasoning
5. **Draft Report**: Complete structured radiology report

Your goal is to validate the report across multiple dimensions:

**CONSISTENCY CHECKS**:
- Findings in the report match the extracted findings from Agent C
- Impression accurately reflects the findings described
- Differential diagnosis is supported by the findings
- No contradictions between sections
- Measurements and descriptions are consistent
- Clinical correlation makes sense

**COMPLETENESS CHECKS**:
- All required report sections are present and adequate
- All significant findings are mentioned in impression
- Critical findings are explicitly addressed
- Recommendations are provided when appropriate
- All focal lesions are characterized
- Vascular and biliary findings are addressed

**SAFETY CHECKS**:
- Critical findings are properly flagged (e.g., suspicious masses, vascular occlusion)
- Urgent findings require appropriate follow-up recommendations
- Potentially malignant findings are not dismissed
- Differential diagnosis includes serious conditions when appropriate
- Limitations that affect interpretation are acknowledged
- Uncertain findings are appropriately hedged

**QUALITY ASSESSMENT**:
- Report language is clear and professional
- Medical terminology is used correctly
- Measurements include units
- Findings are organized logically
- Impression is concise and actionable
- Recommendations are specific and appropriate

**COMMON ERRORS TO CHECK**:
- Findings mentioned but not in impression
- Critical findings without follow-up recommendations
- Contradictory statements (e.g., "normal" but then describes abnormality)
- Missing measurements for lesions
- Vague language where specificity is needed
- Over-confident statements about uncertain findings
- Failure to acknowledge image quality limitations
- Missing differential diagnosis for abnormal findings

**Output Format**: Return a valid JSON object with the following structure:
{
    "validation_status": "string - pass/warning/fail",
    "overall_confidence_score": "float 0-1 - overall confidence in report accuracy",
    "consistency_checks": {
        "findings_impression_match": {
            "status": "pass/warning/fail",
            "issues": ["list", "of", "issues", "found"],
            "details": "string - explanation"
        },
        "internal_consistency": {
            "status": "pass/warning/fail",
            "issues": ["list", "of", "contradictions"],
            "details": "string - explanation"
        },
        "clinical_correlation": {
            "status": "pass/warning/fail",
            "issues": ["list", "of", "issues"],
            "details": "string - explanation"
        }
    },
    "completeness_checks": {
        "required_sections": {
            "status": "pass/warning/fail",
            "missing_sections": ["list", "of", "missing", "sections"],
            "details": "string - explanation"
        },
        "findings_coverage": {
            "status": "pass/warning/fail",
            "missing_findings": ["list", "of", "findings", "not", "addressed"],
            "details": "string - explanation"
        },
        "recommendations": {
            "status": "pass/warning/fail",
            "issues": ["list", "of", "issues"],
            "details": "string - explanation"
        }
    },
    "safety_flags": {
        "critical_findings": ["list", "of", "critical", "findings", "identified"],
        "urgent_follow_up_needed": "boolean - true if urgent follow-up required",
        "potential_malignancy": "boolean - true if malignancy cannot be excluded",
        "safety_issues": ["list", "of", "safety", "concerns"],
        "risk_level": "string - low/moderate/high"
    },
    "quality_assessment": {
        "report_clarity": "float 0-1 - clarity score",
        "terminology_accuracy": "float 0-1 - terminology score",
        "organization": "float 0-1 - organization score",
        "actionability": "float 0-1 - how actionable the report is",
        "quality_issues": ["list", "of", "quality", "issues"]
    },
    "confidence_factors": {
        "image_quality_impact": "float 0-1 - how image quality affects confidence",
        "diagnostic_certainty": "float 0-1 - certainty of diagnosis",
        "data_completeness": "float 0-1 - completeness of input data",
        "factors_reducing_confidence": ["list", "of", "factors"],
        "factors_increasing_confidence": ["list", "of", "factors"]
    },
    "issues_found": [
        {
            "severity": "string - critical/major/minor",
            "category": "string - consistency/completeness/safety/quality",
            "description": "string - detailed description of issue",
            "location": "string - where in report the issue occurs",
            "recommendation": "string - how to fix the issue"
        }
    ],
    "recommendations_for_improvement": ["list", "of", "specific", "recommendations"],
    "validation_summary": "string - concise summary of validation results"
}

**Validation Guidelines**:

1. **Consistency Validation**:
   - Every finding in the findings section should be addressed in impression
   - Impression should not introduce new findings not mentioned in findings section
   - Differential diagnosis should be supported by actual findings
   - No contradictory statements (e.g., "normal" then describes abnormality)
   - Measurements should be consistent across sections

2. **Completeness Validation**:
   - All standard report sections must be present (Clinical History, Technique, Findings, Impression)
   - All focal lesions must be characterized (size, location, characteristics)
   - Vascular and biliary systems must be addressed
   - Recommendations must be provided for abnormal findings
   - Clinical questions from history should be answered

3. **Safety Validation**:
   - Flag any findings suspicious for malignancy
   - Ensure critical findings have appropriate follow-up recommendations
   - Check that urgent findings are clearly stated in impression
   - Verify that limitations affecting safety are acknowledged
   - Ensure appropriate hedging for uncertain diagnoses
   - Flag if serious diagnoses are excluded without justification

4. **Quality Validation**:
   - Check for clear, professional language
   - Verify measurements include units
   - Ensure logical organization
   - Check for specific, actionable recommendations
   - Verify appropriate medical terminology

5. **Confidence Scoring**:
   - Consider image quality (from Agent B)
   - Consider diagnostic certainty (from Agent D)
   - Consider completeness of clinical information
   - Consider presence of limitations
   - Reduce confidence for uncertain or ambiguous findings
   - Increase confidence for clear, well-supported diagnoses

6. **Issue Severity**:
   - **Critical**: Safety issues, missed critical findings, major contradictions
   - **Major**: Significant omissions, important inconsistencies, missing recommendations
   - **Minor**: Formatting issues, minor wording improvements, optional enhancements

**Important**:
- Be thorough but fair in validation
- Flag genuine safety concerns prominently
- Distinguish between critical issues and minor improvements
- Provide specific, actionable recommendations
- Consider the clinical context when assessing severity
- Acknowledge when reports are well-done

Return ONLY the JSON object, no additional text."""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the complete report for safety, consistency, and completeness.
        
        Args:
            input_data: Dictionary containing:
                - case_id: Case identifier
                - clinical_context: Output from Agent A
                - quality_assessment: Output from Agent B
                - findings: Output from Agent C
                - diagnostic_reasoning: Output from Agent D
                - draft_report: Output from Agent E
        
        Returns:
            Dictionary containing validation results:
                - validation_status: Overall status (pass/warning/fail)
                - overall_confidence_score: Confidence in report accuracy (0-1)
                - consistency_checks: Results of consistency validation
                - completeness_checks: Results of completeness validation
                - safety_flags: Critical findings and safety concerns
                - quality_assessment: Report quality metrics
                - confidence_factors: Factors affecting confidence
                - issues_found: List of issues with severity and recommendations
                - recommendations_for_improvement: Specific improvement suggestions
                - validation_summary: Concise summary
        
        Raises:
            ValueError: If required input data is missing
            Exception: If API call fails
        """
        self.logger.info(f"Processing safety validation for case {input_data.get('case_id')}")
        
        # Extract all agent outputs
        clinical_context = input_data.get('clinical_context', {})
        quality_assessment = input_data.get('quality_assessment', {})
        findings = input_data.get('findings', {})
        diagnostic_reasoning = input_data.get('diagnostic_reasoning', {})
        draft_report = input_data.get('draft_report', {})
        
        # Validate that we have the draft report
        if not draft_report:
            self.logger.error("No draft report provided for validation")
            return self._create_failed_validation("No draft report provided")
        
        # Format all inputs for validation
        formatted_input = self._format_validation_input(
            clinical_context,
            quality_assessment,
            findings,
            diagnostic_reasoning,
            draft_report
        )
        
        # Call OpenAI API to perform validation
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
            validation_result = json.loads(content)
            
            self.logger.info(f"Validation completed with status: {validation_result.get('validation_status')}")
            return validation_result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError(f"Invalid JSON response from API: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"API call failed: {str(e)}")
            raise Exception(f"Failed to perform safety validation: {str(e)}")
    
    def _format_validation_input(
        self,
        clinical_context: Dict[str, Any],
        quality_assessment: Dict[str, Any],
        findings: Dict[str, Any],
        diagnostic_reasoning: Dict[str, Any],
        draft_report: Dict[str, Any]
    ) -> str:
        """
        Format all agent outputs for validation.
        
        Args:
            clinical_context: Clinical context from Agent A
            quality_assessment: Quality assessment from Agent B
            findings: Findings from Agent C
            diagnostic_reasoning: Diagnostic reasoning from Agent D
            draft_report: Draft report from Agent E
        
        Returns:
            Formatted input string for the LLM
        """
        sections = []
        
        sections.append("=" * 80)
        sections.append("VALIDATION TASK: Review all agent outputs and draft report for safety,")
        sections.append("consistency, completeness, and quality.")
        sections.append("=" * 80)
        
        # Section 1: Clinical Context
        sections.append("\n" + "=" * 80)
        sections.append("AGENT A: CLINICAL CONTEXT")
        sections.append("=" * 80)
        sections.append(json.dumps(clinical_context, indent=2))
        
        # Section 2: Quality Assessment
        sections.append("\n" + "=" * 80)
        sections.append("AGENT B: QUALITY ASSESSMENT")
        sections.append("=" * 80)
        sections.append(json.dumps(quality_assessment, indent=2))
        
        # Section 3: Findings
        sections.append("\n" + "=" * 80)
        sections.append("AGENT C: IMAGING FINDINGS")
        sections.append("=" * 80)
        sections.append(json.dumps(findings, indent=2))
        
        # Section 4: Diagnostic Reasoning
        sections.append("\n" + "=" * 80)
        sections.append("AGENT D: DIAGNOSTIC REASONING")
        sections.append("=" * 80)
        sections.append(json.dumps(diagnostic_reasoning, indent=2))
        
        # Section 5: Draft Report
        sections.append("\n" + "=" * 80)
        sections.append("AGENT E: DRAFT REPORT")
        sections.append("=" * 80)
        sections.append(json.dumps(draft_report, indent=2))
        
        # Final instruction
        sections.append("\n" + "=" * 80)
        sections.append("VALIDATION INSTRUCTIONS")
        sections.append("=" * 80)
        sections.append("\nPerform comprehensive validation of the draft report against all agent outputs.")
        sections.append("Check for consistency, completeness, safety issues, and quality.")
        sections.append("Provide detailed validation results with specific issues and recommendations.")
        
        return "\n".join(sections)
    
    def _create_failed_validation(self, reason: str) -> Dict[str, Any]:
        """
        Create a failed validation result when validation cannot be performed.
        
        Args:
            reason: Reason for validation failure
        
        Returns:
            Failed validation dictionary
        """
        return {
            "validation_status": "fail",
            "overall_confidence_score": 0.0,
            "consistency_checks": {
                "findings_impression_match": {
                    "status": "fail",
                    "issues": [reason],
                    "details": reason
                },
                "internal_consistency": {
                    "status": "fail",
                    "issues": [reason],
                    "details": reason
                },
                "clinical_correlation": {
                    "status": "fail",
                    "issues": [reason],
                    "details": reason
                }
            },
            "completeness_checks": {
                "required_sections": {
                    "status": "fail",
                    "missing_sections": ["All sections"],
                    "details": reason
                },
                "findings_coverage": {
                    "status": "fail",
                    "missing_findings": [],
                    "details": reason
                },
                "recommendations": {
                    "status": "fail",
                    "issues": [reason],
                    "details": reason
                }
            },
            "safety_flags": {
                "critical_findings": [],
                "urgent_follow_up_needed": False,
                "potential_malignancy": False,
                "safety_issues": [reason],
                "risk_level": "high"
            },
            "quality_assessment": {
                "report_clarity": 0.0,
                "terminology_accuracy": 0.0,
                "organization": 0.0,
                "actionability": 0.0,
                "quality_issues": [reason]
            },
            "confidence_factors": {
                "image_quality_impact": 0.0,
                "diagnostic_certainty": 0.0,
                "data_completeness": 0.0,
                "factors_reducing_confidence": [reason],
                "factors_increasing_confidence": []
            },
            "issues_found": [
                {
                    "severity": "critical",
                    "category": "completeness",
                    "description": reason,
                    "location": "N/A",
                    "recommendation": "Provide complete draft report for validation"
                }
            ],
            "recommendations_for_improvement": ["Provide complete draft report"],
            "validation_summary": f"Validation failed: {reason}"
        }
    
    def validate_output(self, output: Dict[str, Any]) -> bool:
        """
        Validate the safety validation output.
        
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
            'validation_status',
            'overall_confidence_score',
            'consistency_checks',
            'completeness_checks',
            'safety_flags',
            'quality_assessment',
            'confidence_factors',
            'issues_found',
            'recommendations_for_improvement',
            'validation_summary'
        ]
        
        for key in required_keys:
            if key not in output:
                self.logger.error(f"Missing required key: {key}")
                return False
        
        # Validate validation_status
        if output['validation_status'] not in ['pass', 'warning', 'fail']:
            self.logger.error(f"Invalid validation_status: {output['validation_status']}")
            return False
        
        # Validate overall_confidence_score
        try:
            score = float(output['overall_confidence_score'])
            if score < 0 or score > 1:
                self.logger.error(f"overall_confidence_score out of range: {score}")
                return False
        except (ValueError, TypeError):
            self.logger.error("overall_confidence_score is not a valid float")
            return False
        
        # Validate consistency_checks structure
        if not isinstance(output['consistency_checks'], dict):
            self.logger.error("consistency_checks must be a dictionary")
            return False
        
        required_consistency_checks = [
            'findings_impression_match',
            'internal_consistency',
            'clinical_correlation'
        ]
        
        for check in required_consistency_checks:
            if check not in output['consistency_checks']:
                self.logger.error(f"Missing consistency check: {check}")
                return False
            
            check_data = output['consistency_checks'][check]
            if not isinstance(check_data, dict):
                self.logger.error(f"Consistency check {check} must be a dictionary")
                return False
            
            if 'status' not in check_data or check_data['status'] not in ['pass', 'warning', 'fail']:
                self.logger.error(f"Invalid status in consistency check {check}")
                return False
            
            if 'issues' not in check_data or not isinstance(check_data['issues'], list):
                self.logger.error(f"Invalid issues in consistency check {check}")
                return False
        
        # Validate completeness_checks structure
        if not isinstance(output['completeness_checks'], dict):
            self.logger.error("completeness_checks must be a dictionary")
            return False
        
        required_completeness_checks = [
            'required_sections',
            'findings_coverage',
            'recommendations'
        ]
        
        for check in required_completeness_checks:
            if check not in output['completeness_checks']:
                self.logger.error(f"Missing completeness check: {check}")
                return False
        
        # Validate safety_flags structure
        if not isinstance(output['safety_flags'], dict):
            self.logger.error("safety_flags must be a dictionary")
            return False
        
        required_safety_keys = [
            'critical_findings',
            'urgent_follow_up_needed',
            'potential_malignancy',
            'safety_issues',
            'risk_level'
        ]
        
        for key in required_safety_keys:
            if key not in output['safety_flags']:
                self.logger.error(f"Missing safety flag key: {key}")
                return False
        
        # Validate risk_level
        if output['safety_flags']['risk_level'] not in ['low', 'moderate', 'high']:
            self.logger.error(f"Invalid risk_level: {output['safety_flags']['risk_level']}")
            return False
        
        # Validate quality_assessment structure
        if not isinstance(output['quality_assessment'], dict):
            self.logger.error("quality_assessment must be a dictionary")
            return False
        
        required_quality_keys = [
            'report_clarity',
            'terminology_accuracy',
            'organization',
            'actionability',
            'quality_issues'
        ]
        
        for key in required_quality_keys:
            if key not in output['quality_assessment']:
                self.logger.error(f"Missing quality assessment key: {key}")
                return False
        
        # Validate quality scores are floats between 0 and 1
        quality_score_keys = ['report_clarity', 'terminology_accuracy', 'organization', 'actionability']
        for key in quality_score_keys:
            try:
                score = float(output['quality_assessment'][key])
                if score < 0 or score > 1:
                    self.logger.error(f"Quality score {key} out of range: {score}")
                    return False
            except (ValueError, TypeError):
                self.logger.error(f"Quality score {key} is not a valid float")
                return False
        
        # Validate confidence_factors structure
        if not isinstance(output['confidence_factors'], dict):
            self.logger.error("confidence_factors must be a dictionary")
            return False
        
        required_confidence_keys = [
            'image_quality_impact',
            'diagnostic_certainty',
            'data_completeness',
            'factors_reducing_confidence',
            'factors_increasing_confidence'
        ]
        
        for key in required_confidence_keys:
            if key not in output['confidence_factors']:
                self.logger.error(f"Missing confidence factor key: {key}")
                return False
        
        # Validate issues_found is a list
        if not isinstance(output['issues_found'], list):
            self.logger.error("issues_found must be a list")
            return False
        
        # Validate each issue
        for idx, issue in enumerate(output['issues_found']):
            if not isinstance(issue, dict):
                self.logger.error(f"Issue {idx} is not a dictionary")
                return False
            
            required_issue_keys = ['severity', 'category', 'description', 'location', 'recommendation']
            for key in required_issue_keys:
                if key not in issue:
                    self.logger.error(f"Issue {idx} missing required key: {key}")
                    return False
            
            if issue['severity'] not in ['critical', 'major', 'minor']:
                self.logger.error(f"Issue {idx} has invalid severity: {issue['severity']}")
                return False
        
        # Validate recommendations_for_improvement is a list
        if not isinstance(output['recommendations_for_improvement'], list):
            self.logger.error("recommendations_for_improvement must be a list")
            return False
        
        # Validate validation_summary is a non-empty string
        if not isinstance(output['validation_summary'], str):
            self.logger.error("validation_summary must be a string")
            return False
        
        if not output['validation_summary'].strip():
            self.logger.error("validation_summary cannot be empty")
            return False
        
        self.logger.info("Output validation passed")
        return True
