# Multi-Agent Pipeline Architecture

This directory contains the LangGraph-based multi-agent pipeline for radiology report generation.

## Overview

The multi-agent system uses LangGraph to orchestrate six specialized agents that work sequentially to analyze ultrasound images and generate structured radiology reports.

## Components

### Base Agent (`base_agent.py`)

Abstract base class that all agents inherit from. Provides:
- Common interface (`process`, `validate_output`)
- Execution wrapper with timing and error handling
- Logging capabilities
- Prompt template management

### Orchestrator (`orchestrator.py`)

Coordinates the execution of the agent pipeline using LangGraph. Features:
- State management between agents
- Sequential agent execution (A → B → C → D → E → F)
- Audit logging to database
- Error handling and retry logic
- Report storage

## Agent Pipeline

```
START
  ↓
Agent A: Clinical Context Extraction
  ↓
Agent B: View Identification & Quality Assessment
  ↓
Agent C: Image Findings Extraction
  ↓
Agent D: Diagnostic Reasoning
  ↓
Agent E: Structured Report Drafting
  ↓
Agent F: Safety & Consistency Validation
  ↓
END
```

## Usage

### Creating a Custom Agent

```python
from app.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name='my_agent')
    
    def process(self, input_data):
        # Your agent logic here
        result = {'output': 'processed data'}
        return result
    
    def validate_output(self, output):
        # Validate the output
        return 'output' in output
```

### Using the Orchestrator

```python
from app.agents import AgentOrchestrator

# Create orchestrator
orchestrator = AgentOrchestrator()

# Register agents
orchestrator.register_agent('agent_a', agent_a_instance)
orchestrator.register_agent('agent_b', agent_b_instance)
# ... register all agents

# Build the pipeline graph
orchestrator.build_graph()

# Execute analysis for a case
result = orchestrator.orchestrate_analysis(case_id=123)

if result['success']:
    print(f"Report created: {result['report_id']}")
else:
    print(f"Errors: {result['errors']}")
```

## State Management

The `AgentState` TypedDict defines the data structure passed between agents:

```python
{
    'case_id': int,
    'case_data': dict,
    'clinical_context': dict,      # From Agent A
    'quality_assessment': dict,    # From Agent B
    'findings': dict,              # From Agent C
    'diagnostic_reasoning': dict,  # From Agent D
    'draft_report': dict,          # From Agent E
    'safety_validation': dict,     # From Agent F
    'errors': list,
    'execution_log': list
}
```

## Database Logging

All agent executions are logged to the `agent_outputs` table:
- Input data
- Output data
- Execution time
- Error messages (if any)

Final reports are stored in the `reports` table with:
- Complete JSON of all agent outputs
- Draft report text
- Confidence scores
- Safety flags

## Error Handling

The orchestrator provides robust error handling:
- Individual agent failures don't crash the pipeline
- Errors are logged and accumulated in state
- Retry logic available via `handle_agent_error()`
- Case status updated based on success/failure

## Testing

Run the test suite:

```bash
python -m pytest tests/test_orchestrator.py -v
```

## Implemented Agents

### Agent A: Clinical Context Extraction (`agent_a_context.py`)

**Status**: ✅ Implemented

Extracts structured clinical information from patient history, clinical indication, and lab results.

**Input**:
- Patient history
- Clinical indication
- Lab results
- Clinical notes

**Output**:
- Relevant medical history
- Current clinical indication
- Pertinent lab values
- Risk factors
- Clinical questions to address
- Summary

### Agent B: View Identification and Quality Assessment (`agent_b_quality.py`)

**Status**: ✅ Implemented

Analyzes ultrasound images using multimodal LLM to identify anatomical views and assess image quality.

**Input**:
- Ultrasound image paths (single or multiple)

**Output**:
- Per-image assessments:
  - View identification (e.g., "Sagittal Right Lobe Liver")
  - View confidence score (0-1)
  - Quality score (0-100)
  - Technical assessment (resolution, contrast, penetration, field of view)
  - Identified artifacts
  - Technical limitations
  - Diagnostic adequacy
  - Optimization recommendations
- Overall quality assessment
- Summary

**Features**:
- Supports multiple image formats (JPEG, PNG, etc.)
- Base64 encoding for API transmission
- Handles missing or invalid image files gracefully
- Provides detailed technical quality metrics

## Next Steps

To complete the multi-agent system:
1. ✅ ~~Implement Agent A: Clinical Context Extraction~~
2. ✅ ~~Implement Agent B: View Identification & Quality Assessment~~
3. Implement Agent C: Image Findings Extraction
4. Implement Agent D: Diagnostic Reasoning
5. Implement Agent E: Structured Report Drafting
6. Implement Agent F: Safety & Consistency Validation
