# Multi-Agent Architecture Database Migration

## Overview

This migration adds support for the multi-agent architecture to the DiagnoseAI application. It introduces new tables for storing agent outputs, feedback, metrics, prompt versions, and RAG cases, as well as adding new fields to existing tables.

## Migration Details

**Migration ID:** `440e57b541d7`  
**Migration Name:** Add multi-agent architecture tables and fields  
**Created:** 2026-01-17

## Changes

### New Tables

1. **agent_outputs** - Stores intermediate results from each agent in the pipeline
   - `id` (INTEGER, PRIMARY KEY)
   - `case_id` (INTEGER, FOREIGN KEY → cases.id)
   - `agent_name` (VARCHAR(50)) - Name of the agent (e.g., agent_a_context)
   - `input_data` (JSON) - Input passed to the agent
   - `output_data` (JSON) - Output produced by the agent
   - `execution_time_ms` (INTEGER) - Execution time in milliseconds
   - `error_message` (TEXT) - Error message if agent failed
   - `created_at` (DATETIME)

2. **feedback** - Captures radiologist actions and modifications
   - `id` (INTEGER, PRIMARY KEY)
   - `case_id` (INTEGER, FOREIGN KEY → cases.id)
   - `report_id` (INTEGER, FOREIGN KEY → reports.id)
   - `user_id` (INTEGER, FOREIGN KEY → users.id)
   - `action` (VARCHAR(20)) - 'approve', 'modify', or 'reject'
   - `modifications` (JSON) - Diff of changes made
   - `rejection_reason` (TEXT) - Reason for rejection
   - `confidence_level` (INTEGER) - 1-5 scale for approval confidence
   - `created_at` (DATETIME)

3. **metrics** - Stores calculated performance metrics
   - `id` (INTEGER, PRIMARY KEY)
   - `metric_name` (VARCHAR(100)) - Name of the metric
   - `metric_value` (FLOAT) - Calculated value
   - `metric_category` (VARCHAR(50)) - Category (e.g., 'overall', 'finding_type')
   - `time_period` (VARCHAR(20)) - Time period (e.g., 'daily', 'weekly')
   - `period_start` (DATE)
   - `period_end` (DATE)
   - `created_at` (DATETIME)

4. **prompt_versions** - Tracks prompt changes with rollback capability
   - `id` (INTEGER, PRIMARY KEY)
   - `agent_name` (VARCHAR(50)) - Which agent this prompt is for
   - `version` (INTEGER) - Version number
   - `prompt_template` (TEXT) - The actual prompt text
   - `change_description` (TEXT) - Description of what changed
   - `is_active` (BOOLEAN) - Currently active version
   - `created_by` (INTEGER, FOREIGN KEY → users.id)
   - `created_at` (DATETIME)

5. **rag_cases** - Stores approved cases for RAG-based retrieval
   - `id` (INTEGER, PRIMARY KEY)
   - `case_id` (INTEGER, FOREIGN KEY → cases.id)
   - `report_id` (INTEGER, FOREIGN KEY → reports.id)
   - `embedding` (BLOB) - Vector embedding for similarity search
   - `pathology_tags` (JSON) - Array of pathology tags
   - `quality_score` (FLOAT) - Quality score for this case
   - `is_exemplar` (BOOLEAN) - Marked as exemplar case
   - `created_at` (DATETIME)

### Updated Tables

1. **users** - Added role field
   - `role` (VARCHAR(50)) - User role (e.g., 'radiologist', 'admin')

2. **cases** - Added multi-agent context fields
   - `patient_history` (TEXT) - Additional patient history
   - `clinical_indication` (TEXT) - Structured clinical indication
   - `lab_results` (TEXT) - Lab results for context

3. **reports** - Added AI confidence and safety fields
   - `confidence_score` (FLOAT) - AI confidence score
   - `safety_flags` (JSON) - Safety validation flags

## Usage

### Apply Migration

```bash
flask db upgrade
```

### Rollback Migration

```bash
flask db downgrade
```

### Check Current Migration Status

```bash
flask db current
```

### View Migration History

```bash
flask db history
```

## Testing

The migration has been tested with:
- SQLite (development)
- Unit tests for all new models and relationships

To run the tests:

```bash
pytest tests/test_multi_agent_models.py -v
```

## Requirements Addressed

This migration addresses the following requirements from the design document:

- **Requirement 7.1**: Multi-agent pipeline infrastructure
- **Requirement 8.5**: Human-in-the-Loop feedback capture
- **Requirement 9.4**: Structured feedback storage
- **Requirement 10.6**: Prompt versioning and rollback
- **Requirement 11.6**: Metrics storage and tracking

## Notes

- All new fields in existing tables are nullable to maintain backward compatibility
- Foreign key constraints ensure referential integrity
- JSON fields are used for flexible data storage (agent outputs, feedback, metrics)
- The migration uses batch operations for SQLite compatibility
- Default values are set for the `role` field in users table ('radiologist')

## Next Steps

After applying this migration, you can:

1. Implement the LangGraph orchestrator (Task 8)
2. Create individual agent modules (Tasks 9-14)
3. Integrate the multi-agent pipeline with case workflow (Task 15)
4. Implement Human-in-the-Loop review interface (Task 16)
5. Build feedback capture and continuous improvement systems (Tasks 17-22)
6. Implement metrics calculation and dashboard (Tasks 23-24)
