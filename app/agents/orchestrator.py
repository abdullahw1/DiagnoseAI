"""
LangGraph orchestrator for multi-agent radiology analysis pipeline.

This module coordinates the execution of six specialized agents:
- Agent A: Clinical Context Extraction
- Agent B: View Identification and Quality Assessment
- Agent C: Image Findings Extraction
- Agent D: Diagnostic Reasoning
- Agent E: Structured Report Drafting
- Agent F: Safety and Consistency Validation

The orchestrator manages state passing between agents, audit logging,
error handling, and retry logic.
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
from langgraph.graph import StateGraph, END
from app import db
from app.models import Case, AgentOutput, Report, AIGeneratedFindings, StructuredFindings

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    State object passed between agents in the pipeline.
    
    This TypedDict defines the structure of data that flows through
    the agent pipeline, accumulating outputs from each agent.
    """
    case_id: int
    case_data: Dict[str, Any]
    
    # Agent outputs
    clinical_context: Optional[Dict[str, Any]]
    quality_assessment: Optional[Dict[str, Any]]
    findings: Optional[Dict[str, Any]]
    diagnostic_reasoning: Optional[Dict[str, Any]]
    draft_report: Optional[Dict[str, Any]]
    safety_validation: Optional[Dict[str, Any]]
    
    # Execution metadata
    errors: List[str]
    execution_log: List[Dict[str, Any]]


class AgentOrchestrator:
    """
    Orchestrates the multi-agent pipeline using LangGraph.
    
    The orchestrator:
    - Initializes the agent pipeline graph
    - Manages state passing between agents
    - Handles errors and retries
    - Logs all agent executions to the database
    - Stores final results in the Report table
    """
    
    def __init__(self, agents: Optional[Dict[str, Any]] = None):
        """
        Initialize the orchestrator with agent instances.
        
        Args:
            agents: Dictionary mapping agent names to agent instances.
                   If None, agents will need to be registered later.
        """
        self.agents = agents or {}
        self.graph = None
        self.logger = logging.getLogger(f"{__name__}.AgentOrchestrator")
    
    def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent_name: Unique identifier for the agent
            agent_instance: Instance of the agent (must have execute method)
        """
        self.agents[agent_name] = agent_instance
        self.logger.info(f"Registered agent: {agent_name}")
    
    def build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph for the agent pipeline.
        
        The graph defines the sequential flow:
        START -> Agent A -> Agent B -> Agent C -> Agent D -> Agent E -> Agent F -> END
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("agent_a", self._execute_agent_a)
        workflow.add_node("agent_b", self._execute_agent_b)
        workflow.add_node("agent_c", self._execute_agent_c)
        workflow.add_node("agent_d", self._execute_agent_d)
        workflow.add_node("agent_e", self._execute_agent_e)
        workflow.add_node("agent_f", self._execute_agent_f)
        
        # Define the sequential flow
        workflow.set_entry_point("agent_a")
        workflow.add_edge("agent_a", "agent_b")
        workflow.add_edge("agent_b", "agent_c")
        workflow.add_edge("agent_c", "agent_d")
        workflow.add_edge("agent_d", "agent_e")
        workflow.add_edge("agent_e", "agent_f")
        workflow.add_edge("agent_f", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        self.logger.info("Agent pipeline graph built successfully")
        
        return self.graph
    
    def _execute_agent_a(self, state: AgentState) -> AgentState:
        """Execute Agent A: Clinical Context Extraction."""
        return self._execute_agent("agent_a", state, "clinical_context")
    
    def _execute_agent_b(self, state: AgentState) -> AgentState:
        """Execute Agent B: View Identification and Quality Assessment."""
        return self._execute_agent("agent_b", state, "quality_assessment")
    
    def _execute_agent_c(self, state: AgentState) -> AgentState:
        """Execute Agent C: Image Findings Extraction."""
        return self._execute_agent("agent_c", state, "findings")
    
    def _execute_agent_d(self, state: AgentState) -> AgentState:
        """Execute Agent D: Diagnostic Reasoning."""
        return self._execute_agent("agent_d", state, "diagnostic_reasoning")
    
    def _execute_agent_e(self, state: AgentState) -> AgentState:
        """Execute Agent E: Structured Report Drafting."""
        return self._execute_agent("agent_e", state, "draft_report")
    
    def _execute_agent_f(self, state: AgentState) -> AgentState:
        """Execute Agent F: Safety and Consistency Validation."""
        return self._execute_agent("agent_f", state, "safety_validation")
    
    def _execute_agent(
        self, 
        agent_name: str, 
        state: AgentState, 
        output_key: str
    ) -> AgentState:
        """
        Execute a single agent and update the state.
        
        Args:
            agent_name: Name of the agent to execute
            state: Current pipeline state
            output_key: Key to store the agent's output in state
            
        Returns:
            Updated state with agent output
        """
        self.logger.info(f"Executing {agent_name} for case {state['case_id']}")
        
        # Get the agent instance
        agent = self.agents.get(agent_name)
        if not agent:
            error_msg = f"Agent {agent_name} not registered"
            self.logger.error(error_msg)
            state['errors'].append(error_msg)
            return state
        
        try:
            # Prepare input data for the agent
            input_data = self._prepare_agent_input(agent_name, state)
            
            # Execute the agent
            result = agent.execute(input_data)
            
            # Log execution to database
            self._log_agent_execution(
                case_id=state['case_id'],
                agent_name=agent_name,
                input_data=input_data,
                result=result
            )
            
            # Update state with result
            if result['success']:
                state[output_key] = result['output']
                self.logger.info(
                    f"{agent_name} completed successfully in {result['execution_time_ms']}ms"
                )
            else:
                error_msg = f"{agent_name} failed: {result['error']}"
                self.logger.error(error_msg)
                state['errors'].append(error_msg)
            
            # Add to execution log
            state['execution_log'].append({
                'agent': agent_name,
                'success': result['success'],
                'execution_time_ms': result['execution_time_ms'],
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            error_msg = f"Unexpected error in {agent_name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            state['errors'].append(error_msg)
            
            # Log the error to database
            self._log_agent_execution(
                case_id=state['case_id'],
                agent_name=agent_name,
                input_data={},
                result={
                    'success': False,
                    'error': error_msg,
                    'execution_time_ms': 0
                }
            )
        
        return state
    
    def _prepare_agent_input(self, agent_name: str, state: AgentState) -> Dict[str, Any]:
        """
        Prepare input data for a specific agent based on pipeline state.
        
        Args:
            agent_name: Name of the agent
            state: Current pipeline state
            
        Returns:
            Dictionary of input data for the agent
        """
        # Base input includes case data
        input_data = {
            'case_id': state['case_id'],
            'case_data': state['case_data']
        }
        
        # Add outputs from previous agents as needed
        if agent_name == 'agent_a':
            # Agent A only needs case data
            pass
        
        elif agent_name == 'agent_b':
            # Agent B needs case data (images)
            pass
        
        elif agent_name == 'agent_c':
            # Agent C needs images and clinical context
            if state.get('clinical_context'):
                input_data['clinical_context'] = state['clinical_context']
        
        elif agent_name == 'agent_d':
            # Agent D needs findings and clinical context
            if state.get('clinical_context'):
                input_data['clinical_context'] = state['clinical_context']
            if state.get('findings'):
                input_data['findings'] = state['findings']
        
        elif agent_name == 'agent_e':
            # Agent E needs all previous outputs
            for key in ['clinical_context', 'quality_assessment', 'findings', 'diagnostic_reasoning']:
                if state.get(key):
                    input_data[key] = state[key]
        
        elif agent_name == 'agent_f':
            # Agent F needs the draft report and all intermediate outputs
            for key in ['clinical_context', 'quality_assessment', 'findings', 
                       'diagnostic_reasoning', 'draft_report']:
                if state.get(key):
                    input_data[key] = state[key]
        
        return input_data
    
    def _log_agent_execution(
        self,
        case_id: int,
        agent_name: str,
        input_data: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Log agent execution to the database for audit trail.
        
        Args:
            case_id: ID of the case being processed
            agent_name: Name of the agent
            input_data: Input data passed to the agent
            result: Result from agent execution
        """
        try:
            agent_output = AgentOutput(
                case_id=case_id,
                agent_name=agent_name,
                input_data=input_data,
                output_data=result.get('output'),
                execution_time_ms=result.get('execution_time_ms', 0),
                error_message=result.get('error')
            )
            db.session.add(agent_output)
            db.session.commit()
            
        except Exception as e:
            self.logger.error(f"Failed to log agent execution: {str(e)}", exc_info=True)
            db.session.rollback()
    
    def orchestrate_analysis(self, case_id: int) -> Dict[str, Any]:
        """
        Execute the complete multi-agent pipeline for a case.
        
        This is the main entry point for running the agent pipeline.
        It initializes the state, executes the graph, and stores results.
        
        Args:
            case_id: ID of the case to analyze
            
        Returns:
            Dictionary containing:
                - success: Boolean indicating overall success
                - report_id: ID of the created report (if successful)
                - ai_findings_id: ID of the created AI findings (if successful)
                - errors: List of error messages
                - execution_log: List of agent execution details
        """
        self.logger.info(f"Starting multi-agent analysis for case {case_id}")
        
        try:
            # Load case data
            case = Case.query.get(case_id)
            if not case:
                raise ValueError(f"Case {case_id} not found")
            
            # Load user-provided structured findings if available
            structured_findings = None
            if case.structured_findings:
                structured_findings = self._serialize_structured_findings(case.structured_findings)
            
            # Prepare case data
            case_data = {
                'case_id': case.id,
                'case_number': case.case_number,
                'patient_history': case.patient_history,
                'clinical_indication': case.clinical_indication,
                'lab_results': case.lab_results,
                'clinical_history': case.clinical_history,
                'indication': case.indication,
                'image_paths': case.all_image_paths,
                'study_type': case.study_type,
                'body_part': case.body_part,
                'structured_findings': structured_findings
            }
            
            # Initialize state
            initial_state: AgentState = {
                'case_id': case_id,
                'case_data': case_data,
                'clinical_context': None,
                'quality_assessment': None,
                'findings': None,
                'diagnostic_reasoning': None,
                'draft_report': None,
                'safety_validation': None,
                'errors': [],
                'execution_log': []
            }
            
            # Build graph if not already built
            if not self.graph:
                self.build_graph()
            
            # Execute the pipeline
            final_state = self.graph.invoke(initial_state)
            
            # Store AI-generated findings if available
            ai_findings_id = self._store_ai_findings(case_id, final_state)
            
            # Store results in Report table
            report_id = self._store_report(case_id, final_state)
            
            # Update case status
            if final_state['errors']:
                case.status = 'analysis_failed'
            else:
                case.status = 'analysis_complete'
            db.session.commit()
            
            self.logger.info(
                f"Multi-agent analysis completed for case {case_id}. "
                f"Report ID: {report_id}, AI Findings ID: {ai_findings_id}, "
                f"Errors: {len(final_state['errors'])}"
            )
            
            return {
                'success': len(final_state['errors']) == 0,
                'report_id': report_id,
                'ai_findings_id': ai_findings_id,
                'errors': final_state['errors'],
                'execution_log': final_state['execution_log']
            }
            
        except Exception as e:
            error_msg = f"Orchestration failed for case {case_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            # Update case status
            try:
                case = Case.query.get(case_id)
                if case:
                    case.status = 'analysis_failed'
                    db.session.commit()
            except:
                pass
            
            return {
                'success': False,
                'report_id': None,
                'ai_findings_id': None,
                'errors': [error_msg],
                'execution_log': []
            }
    
    def _store_report(self, case_id: int, final_state: AgentState) -> Optional[int]:
        """
        Store the final report in the database.
        
        Args:
            case_id: ID of the case
            final_state: Final state from pipeline execution
            
        Returns:
            ID of the created report, or None if failed
        """
        try:
            # Extract report data from final state
            draft_report = final_state.get('draft_report', {})
            safety_validation = final_state.get('safety_validation', {})
            
            # Always format report from sections if available for proper structure
            if 'report_sections' in draft_report and draft_report['report_sections']:
                report_text = self._format_report_text(draft_report)
            else:
                # Fallback to full_report_text or report_text if sections not available
                report_text = draft_report.get('full_report_text', '') or draft_report.get('report_text', '')
            
            # Create report record
            report = Report(
                case_id=case_id,
                draft_json={
                    'clinical_context': final_state.get('clinical_context'),
                    'quality_assessment': final_state.get('quality_assessment'),
                    'findings': final_state.get('findings'),
                    'diagnostic_reasoning': final_state.get('diagnostic_reasoning'),
                    'draft_report': draft_report,
                    'safety_validation': safety_validation
                },
                draft_text=report_text,
                confidence_score=safety_validation.get('confidence_score'),
                safety_flags=safety_validation.get('safety_flags'),
                is_finalized=False
            )
            
            db.session.add(report)
            db.session.commit()
            
            self.logger.info(f"Report {report.id} created for case {case_id}")
            return report.id
            
        except Exception as e:
            self.logger.error(f"Failed to store report: {str(e)}", exc_info=True)
            db.session.rollback()
            return None
    
    def _format_report_text(self, draft_report: Dict[str, Any]) -> str:
        """
        Format report text from structured sections with proper spacing.
        
        Args:
            draft_report: Draft report dictionary from Agent E
        
        Returns:
            Properly formatted report text with sections separated by line breaks
        """
        sections = draft_report.get('report_sections', {})
        
        formatted_parts = []
        
        # Clinical History
        if sections.get('clinical_history'):
            formatted_parts.append("CLINICAL HISTORY")
            formatted_parts.append(sections['clinical_history'])
            formatted_parts.append("")  # Empty line
        
        # Technique
        if sections.get('technique'):
            formatted_parts.append("TECHNIQUE")
            formatted_parts.append(sections['technique'])
            formatted_parts.append("")  # Empty line
        
        # Findings
        if sections.get('findings'):
            formatted_parts.append("FINDINGS")
            formatted_parts.append(sections['findings'])
            formatted_parts.append("")  # Empty line
        
        # Impression
        if sections.get('impression'):
            formatted_parts.append("IMPRESSION")
            formatted_parts.append(sections['impression'])
        
        return "\n".join(formatted_parts)
    
    def _serialize_structured_findings(self, findings: StructuredFindings) -> Dict[str, Any]:
        """
        Convert StructuredFindings model to dictionary for context.
        
        Args:
            findings: StructuredFindings model instance
        
        Returns:
            Dictionary representation of findings
        """
        return {
            'liver_size': findings.liver_size,
            'liver_texture': findings.liver_texture,
            'liver_focal_defect': findings.liver_focal_defect,
            'liver_cbd': findings.liver_cbd,
            'liver_pv': findings.liver_pv,
            'spleen_size': findings.spleen_size,
            'spleen_focal_defect': findings.spleen_focal_defect,
            'gb_calculus': findings.gb_calculus,
            'gb_wall_edema': findings.gb_wall_edema,
            'right_kidney_size': findings.right_kidney_size,
            'right_kidney_texture': findings.right_kidney_texture,
            'right_kidney_other': findings.right_kidney_other,
            'left_kidney_size': findings.left_kidney_size,
            'left_kidney_texture': findings.left_kidney_texture,
            'left_kidney_other': findings.left_kidney_other,
            'pancreas_findings': findings.pancreas_findings,
            'bladder_filling': findings.bladder_filling,
            'bladder_stone_mass': findings.bladder_stone_mass,
            'bladder_mucosal_irregularity': findings.bladder_mucosal_irregularity,
            'prostate_findings': findings.prostate_findings,
            'ascites': findings.ascites,
            'pleural_effusions': findings.pleural_effusions,
            'para_aortic_lymph_nodes': findings.para_aortic_lymph_nodes,
            'other_findings': findings.other_findings,
            'comments': findings.comments
        }
    
    def _store_ai_findings(self, case_id: int, final_state: AgentState) -> Optional[int]:
        """
        Store AI-generated findings in the database.
        
        This method extracts structured findings from the pipeline state
        and stores them in the AIGeneratedFindings table. It looks for
        findings from the enhanced findings extraction agent.
        
        Args:
            case_id: ID of the case
            final_state: Final state from pipeline execution
            
        Returns:
            ID of the created AI findings record, or None if failed or no findings
        """
        try:
            # Check if we have findings from the enhanced agent
            findings_data = final_state.get('findings')
            
            if not findings_data:
                self.logger.info("No findings data in pipeline state, skipping AI findings storage")
                return None
            
            # Check if findings are in the structured format (from enhanced agent)
            # The enhanced agent returns findings with keys like 'liver_size', 'spleen_size', etc.
            if not self._is_structured_findings_format(findings_data):
                self.logger.info("Findings are not in structured format, skipping AI findings storage")
                return None
            
            # Extract confidence scores
            confidence_scores = findings_data.get('confidence_scores', {})
            
            # Create AI findings record
            ai_findings = AIGeneratedFindings(
                case_id=case_id,
                liver_size=findings_data.get('liver_size'),
                liver_texture=findings_data.get('liver_texture'),
                liver_focal_defect=findings_data.get('liver_focal_defect'),
                liver_cbd=findings_data.get('liver_cbd'),
                liver_pv=findings_data.get('liver_pv'),
                spleen_size=findings_data.get('spleen_size'),
                spleen_focal_defect=findings_data.get('spleen_focal_defect'),
                gb_calculus=findings_data.get('gb_calculus'),
                gb_wall_edema=findings_data.get('gb_wall_edema'),
                right_kidney_size=findings_data.get('right_kidney_size'),
                right_kidney_texture=findings_data.get('right_kidney_texture'),
                right_kidney_other=findings_data.get('right_kidney_other'),
                left_kidney_size=findings_data.get('left_kidney_size'),
                left_kidney_texture=findings_data.get('left_kidney_texture'),
                left_kidney_other=findings_data.get('left_kidney_other'),
                pancreas_findings=findings_data.get('pancreas_findings'),
                bladder_filling=findings_data.get('bladder_filling'),
                bladder_stone_mass=findings_data.get('bladder_stone_mass'),
                bladder_mucosal_irregularity=findings_data.get('bladder_mucosal_irregularity'),
                prostate_findings=findings_data.get('prostate_findings'),
                ascites=findings_data.get('ascites'),
                pleural_effusions=findings_data.get('pleural_effusions'),
                para_aortic_lymph_nodes=findings_data.get('para_aortic_lymph_nodes'),
                other_findings=findings_data.get('other_findings'),
                comments=findings_data.get('comments'),
                confidence_scores=confidence_scores
            )
            
            db.session.add(ai_findings)
            db.session.commit()
            
            self.logger.info(f"AI findings {ai_findings.id} created for case {case_id}")
            return ai_findings.id
            
        except Exception as e:
            self.logger.error(f"Failed to store AI findings: {str(e)}", exc_info=True)
            db.session.rollback()
            return None
    
    def _is_structured_findings_format(self, findings_data: Dict[str, Any]) -> bool:
        """
        Check if findings data is in the structured format.
        
        Args:
            findings_data: Findings data dictionary
        
        Returns:
            True if data is in structured format, False otherwise
        """
        # Check for presence of structured finding keys
        structured_keys = [
            'liver_size', 'spleen_size', 'gb_calculus',
            'right_kidney_size', 'left_kidney_size'
        ]
        
        # If any of these keys are present, it's likely structured format
        return any(key in findings_data for key in structured_keys)
    
    def handle_agent_error(
        self, 
        agent_name: str, 
        error: Exception,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Handle agent execution errors with retry logic.
        
        Args:
            agent_name: Name of the failed agent
            error: The exception that occurred
            retry_count: Current retry attempt number
            max_retries: Maximum number of retries
            
        Returns:
            Dictionary with error handling result
        """
        self.logger.warning(
            f"Agent {agent_name} error (attempt {retry_count + 1}/{max_retries}): {str(error)}"
        )
        
        if retry_count < max_retries:
            return {
                'should_retry': True,
                'retry_count': retry_count + 1,
                'error_message': str(error)
            }
        else:
            return {
                'should_retry': False,
                'retry_count': retry_count,
                'error_message': f"Max retries exceeded for {agent_name}: {str(error)}"
            }
