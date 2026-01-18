"""
Feedback capture service for Human-in-the-Loop (HITL) workflow.

This module provides functions to capture radiologist actions (approve, modify, reject)
on AI-generated reports. All feedback is stored in structured format for continuous
improvement without model retraining.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import difflib
from datetime import datetime
from typing import Dict, Optional, List
from app import db
from app.models import Feedback, Report, Case


def capture_approval(
    case_id: int,
    report_id: int,
    user_id: int,
    confidence_level: int,
    notes: Optional[str] = None
) -> Feedback:
    """
    Capture radiologist approval of AI-generated report.
    
    When a radiologist approves a report without modifications, this function
    stores the approval with confidence level tracking for continuous improvement.
    
    Args:
        case_id: ID of the case being approved
        report_id: ID of the report being approved
        user_id: ID of the user approving the report
        confidence_level: Confidence level (1-5 scale) in the AI report
        notes: Optional notes about the approval
    
    Returns:
        Feedback: The created feedback record
    
    Raises:
        ValueError: If confidence_level is not between 1 and 5
        ValueError: If case_id, report_id, or user_id are invalid
    
    Requirements: 9.1
    """
    # Validate confidence level
    if not isinstance(confidence_level, int) or confidence_level < 1 or confidence_level > 5:
        raise ValueError(f"Confidence level must be between 1 and 5, got {confidence_level}")
    
    # Validate IDs
    if not case_id or not report_id or not user_id:
        raise ValueError("case_id, report_id, and user_id are required")
    
    # Verify case and report exist
    case = Case.query.get(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")
    
    report = Report.query.get(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")
    
    if report.case_id != case_id:
        raise ValueError(f"Report {report_id} does not belong to case {case_id}")
    
    # Create structured modifications data
    modifications = {
        'notes': notes,
        'approval_timestamp': datetime.utcnow().isoformat(),
        'report_length': len(report.draft_text) if report.draft_text else 0,
        'confidence_score': report.confidence_score,
        'safety_flags': report.safety_flags
    }
    
    # Create feedback record
    feedback = Feedback(
        case_id=case_id,
        report_id=report_id,
        user_id=user_id,
        action='approve',
        confidence_level=confidence_level,
        modifications=modifications,
        rejection_reason=None
    )
    
    db.session.add(feedback)
    
    return feedback


def capture_modification(
    case_id: int,
    report_id: int,
    user_id: int,
    original_text: str,
    modified_text: str,
    notes: str
) -> Feedback:
    """
    Capture radiologist modifications to AI-generated report.
    
    When a radiologist modifies a report, this function calculates the diff
    between original and modified text, capturing specific changes for
    continuous improvement analysis.
    
    Args:
        case_id: ID of the case being modified
        report_id: ID of the report being modified
        user_id: ID of the user modifying the report
        original_text: Original AI-generated report text
        modified_text: Modified report text after radiologist edits
        notes: Summary of modifications made
    
    Returns:
        Feedback: The created feedback record with diff information
    
    Raises:
        ValueError: If modified_text is empty
        ValueError: If notes is empty
        ValueError: If case_id, report_id, or user_id are invalid
    
    Requirements: 9.2
    """
    # Validate inputs
    if not modified_text or not modified_text.strip():
        raise ValueError("Modified text cannot be empty")
    
    if not notes or not notes.strip():
        raise ValueError("Modification notes are required")
    
    if not case_id or not report_id or not user_id:
        raise ValueError("case_id, report_id, and user_id are required")
    
    # Verify case and report exist
    case = Case.query.get(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")
    
    report = Report.query.get(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")
    
    if report.case_id != case_id:
        raise ValueError(f"Report {report_id} does not belong to case {case_id}")
    
    # Calculate diff between original and modified text
    diff_data = _calculate_diff(original_text or '', modified_text)
    
    # Create structured modifications data
    modifications = {
        'notes': notes,
        'modification_timestamp': datetime.utcnow().isoformat(),
        'diff': diff_data['diff_lines'],
        'additions': diff_data['additions'],
        'deletions': diff_data['deletions'],
        'original_length': diff_data['original_length'],
        'modified_length': diff_data['modified_length'],
        'change_percentage': diff_data['change_percentage'],
        'added_lines': diff_data['added_lines'],
        'deleted_lines': diff_data['deleted_lines'],
        'confidence_score': report.confidence_score,
        'safety_flags': report.safety_flags
    }
    
    # Create feedback record
    feedback = Feedback(
        case_id=case_id,
        report_id=report_id,
        user_id=user_id,
        action='modify',
        confidence_level=None,
        modifications=modifications,
        rejection_reason=None
    )
    
    db.session.add(feedback)
    
    return feedback


def capture_rejection(
    case_id: int,
    report_id: int,
    user_id: int,
    rejection_category: str,
    rejection_details: str,
    correct_interpretation: Optional[str] = None
) -> Feedback:
    """
    Capture radiologist rejection of AI-generated report.
    
    When a radiologist rejects a report, this function captures the rejection
    reason, detailed explanation, and optionally the correct interpretation
    for continuous improvement analysis.
    
    Args:
        case_id: ID of the case being rejected
        report_id: ID of the report being rejected
        user_id: ID of the user rejecting the report
        rejection_category: Category of rejection (e.g., 'incorrect_findings',
                           'missed_findings', 'poor_quality', 'wrong_diagnosis')
        rejection_details: Detailed explanation of why the report was rejected
        correct_interpretation: Optional correct interpretation provided by radiologist
    
    Returns:
        Feedback: The created feedback record with rejection information
    
    Raises:
        ValueError: If rejection_category is empty
        ValueError: If rejection_details is empty
        ValueError: If case_id, report_id, or user_id are invalid
    
    Requirements: 9.3
    """
    # Validate inputs
    if not rejection_category or not rejection_category.strip():
        raise ValueError("Rejection category is required")
    
    if not rejection_details or not rejection_details.strip():
        raise ValueError("Rejection details are required")
    
    if not case_id or not report_id or not user_id:
        raise ValueError("case_id, report_id, and user_id are required")
    
    # Verify case and report exist
    case = Case.query.get(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")
    
    report = Report.query.get(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")
    
    if report.case_id != case_id:
        raise ValueError(f"Report {report_id} does not belong to case {case_id}")
    
    # Create structured modifications data
    modifications = {
        'rejection_category': rejection_category,
        'rejection_details': rejection_details,
        'correct_interpretation': correct_interpretation,
        'rejection_timestamp': datetime.utcnow().isoformat(),
        'rejected_draft': report.draft_text,
        'rejected_draft_length': len(report.draft_text) if report.draft_text else 0,
        'confidence_score': report.confidence_score,
        'safety_flags': report.safety_flags
    }
    
    # If correct interpretation provided, calculate what was wrong
    if correct_interpretation and report.draft_text:
        diff_data = _calculate_diff(report.draft_text, correct_interpretation)
        modifications['diff_from_correct'] = {
            'additions': diff_data['additions'],
            'deletions': diff_data['deletions'],
            'change_percentage': diff_data['change_percentage']
        }
    
    # Create feedback record
    feedback = Feedback(
        case_id=case_id,
        report_id=report_id,
        user_id=user_id,
        action='reject',
        confidence_level=None,
        modifications=modifications,
        rejection_reason=rejection_details
    )
    
    db.session.add(feedback)
    
    return feedback


def _calculate_diff(original_text: str, modified_text: str) -> Dict:
    """
    Calculate detailed diff between original and modified text.
    
    This internal function computes line-by-line differences, counts additions
    and deletions, and calculates change percentage for analysis.
    
    Args:
        original_text: Original text
        modified_text: Modified text
    
    Returns:
        Dict containing:
            - diff_lines: List of diff lines (limited to first 100)
            - additions: Count of added lines
            - deletions: Count of deleted lines
            - original_length: Number of lines in original
            - modified_length: Number of lines in modified
            - change_percentage: Percentage of text changed
            - added_lines: List of added line content
            - deleted_lines: List of deleted line content
    """
    # Split into lines
    original_lines = original_text.splitlines() if original_text else []
    modified_lines = modified_text.splitlines() if modified_text else []
    
    # Generate unified diff
    diff = list(difflib.unified_diff(
        original_lines,
        modified_lines,
        lineterm='',
        n=0  # No context lines
    ))
    
    # Count changes and extract content
    additions = 0
    deletions = 0
    added_lines = []
    deleted_lines = []
    
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            additions += 1
            added_lines.append(line[1:])  # Remove '+' prefix
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1
            deleted_lines.append(line[1:])  # Remove '-' prefix
    
    # Calculate change percentage
    total_lines = max(len(original_lines), len(modified_lines))
    change_percentage = ((additions + deletions) / total_lines * 100) if total_lines > 0 else 0
    
    return {
        'diff_lines': diff[:100],  # Limit to first 100 lines
        'additions': additions,
        'deletions': deletions,
        'original_length': len(original_lines),
        'modified_length': len(modified_lines),
        'change_percentage': round(change_percentage, 2),
        'added_lines': added_lines[:50],  # Limit to first 50 added lines
        'deleted_lines': deleted_lines[:50]  # Limit to first 50 deleted lines
    }
