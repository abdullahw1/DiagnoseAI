import os
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, make_response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re
from sqlalchemy import func
from app.models import (
    Case, Report, Patient, CaseImage, AITestResult, 
    StructuredFindings, AIGeneratedFindings, FindingsEvaluation,
    AgentOutput, Feedback, RAGCase
)
from app.forms import UploadForm, ReportEditForm, PatientForm, CaseForm, StructuredFindingsForm
from app.ai_service import generate_draft_report, AIServiceError
from app import db

# Import orchestrator for multi-agent pipeline
from app.agents.orchestrator import AgentOrchestrator
from app.agents.agent_a_context import ClinicalContextAgent
from app.agents.agent_b_quality import QualityAssessmentAgent
from app.agents.agent_c_findings import FindingsExtractionAgent
from app.agents.agent_d_reasoning import DiagnosticReasoningAgent
from app.agents.agent_e_report import ReportDraftingAgent
from app.agents.agent_f_safety import SafetyValidationAgent

bp = Blueprint('main', __name__)


def run_multi_agent_pipeline(case_id: int) -> dict:
    """
    Execute the multi-agent pipeline for a case.
    
    This function initializes all agents, creates an orchestrator,
    and runs the complete pipeline for the given case.
    
    Args:
        case_id: ID of the case to process
        
    Returns:
        Dictionary containing:
            - success: Boolean indicating overall success
            - report_id: ID of the created report (if successful)
            - errors: List of error messages
            - execution_log: List of agent execution details
    """
    try:
        current_app.logger.info(f"=== Starting multi-agent pipeline for case {case_id} ===")
        
        # Check if OpenAI API key is configured
        import os
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            error_msg = "OPENAI_API_KEY not configured"
            current_app.logger.error(error_msg)
            return {
                'success': False,
                'report_id': None,
                'errors': [error_msg],
                'execution_log': []
            }
        
        current_app.logger.info(f"OpenAI API key found: {api_key[:10]}...")
        
        # Initialize all agents
        current_app.logger.info("Initializing agents...")
        agents = {
            'agent_a': ClinicalContextAgent(),
            'agent_b': QualityAssessmentAgent(),
            'agent_c': FindingsExtractionAgent(),
            'agent_d': DiagnosticReasoningAgent(),
            'agent_e': ReportDraftingAgent(),
            'agent_f': SafetyValidationAgent()
        }
        current_app.logger.info(f"Initialized {len(agents)} agents")
        
        # Create orchestrator and register agents
        current_app.logger.info("Creating orchestrator...")
        orchestrator = AgentOrchestrator(agents=agents)
        
        # Build the agent pipeline graph
        current_app.logger.info("Building pipeline graph...")
        orchestrator.build_graph()
        
        # Execute the pipeline
        current_app.logger.info("Executing pipeline...")
        result = orchestrator.orchestrate_analysis(case_id)
        
        current_app.logger.info(
            f"=== Multi-agent pipeline completed for case {case_id} === "
            f"Success: {result['success']}, Report ID: {result.get('report_id')}, "
            f"Errors: {result.get('errors', [])}"
        )
        
        return result
        
    except Exception as e:
        error_msg = f"Failed to run multi-agent pipeline: {str(e)}"
        current_app.logger.error(error_msg, exc_info=True)
        return {
            'success': False,
            'report_id': None,
            'errors': [error_msg],
            'execution_log': []
        }


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(file_path):
    """Validate that the uploaded file is a valid image."""
    try:
        with Image.open(file_path) as img:
            img.verify()  # Verify it's a valid image
        return True
    except Exception:
        return False

def save_case_image(file, case_id, order_index, user_id):
    """Save a single case image and return the CaseImage object."""
    if not file or not file.filename:
        return None
    
    # Generate secure filename
    filename = secure_filename(file.filename)
    if not filename:
        return None
    
    # Add timestamp to filename to avoid conflicts
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f_')
    filename = timestamp + filename
    
    # Create user-specific upload directory
    user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Save file path
    file_path = os.path.join(user_upload_dir, filename)
    
    # Save the file
    file.save(file_path)
    
    # Validate the uploaded image
    if not validate_image(file_path):
        os.remove(file_path)  # Clean up invalid file
        return None
    
    # Get file info
    file_size = os.path.getsize(file_path)
    mime_type = file.content_type or 'image/jpeg'
    
    # Create CaseImage record
    case_image = CaseImage(
        case_id=case_id,
        filename=filename,
        original_filename=file.filename,
        image_path=file_path,
        order_index=order_index,
        file_size=file_size,
        mime_type=mime_type
    )
    
    return case_image

def has_any_findings(findings_form):
    """Check if any findings fields have been filled in."""
    for field_name, field in findings_form._fields.items():
        if field_name == 'csrf_token':
            continue
        if field.data and field.data != '':
            return True
    return False

def create_findings_from_form(findings_form, case_id):
    """Create StructuredFindings object from form data."""
    findings = StructuredFindings(
        case_id=case_id,
        liver_size=findings_form.liver_size.data if findings_form.liver_size.data else None,
        liver_texture=findings_form.liver_texture.data if findings_form.liver_texture.data else None,
        liver_focal_defect=findings_form.liver_focal_defect.data if findings_form.liver_focal_defect.data else None,
        liver_cbd=findings_form.liver_cbd.data if findings_form.liver_cbd.data else None,
        liver_pv=findings_form.liver_pv.data if findings_form.liver_pv.data else None,
        spleen_size=findings_form.spleen_size.data if findings_form.spleen_size.data else None,
        spleen_focal_defect=findings_form.spleen_focal_defect.data if findings_form.spleen_focal_defect.data else None,
        gb_calculus=findings_form.gb_calculus.data if findings_form.gb_calculus.data else None,
        gb_wall_edema=findings_form.gb_wall_edema.data if findings_form.gb_wall_edema.data else None,
        right_kidney_size=findings_form.right_kidney_size.data if findings_form.right_kidney_size.data else None,
        right_kidney_texture=findings_form.right_kidney_texture.data if findings_form.right_kidney_texture.data else None,
        right_kidney_other=findings_form.right_kidney_other.data if findings_form.right_kidney_other.data else None,
        left_kidney_size=findings_form.left_kidney_size.data if findings_form.left_kidney_size.data else None,
        left_kidney_texture=findings_form.left_kidney_texture.data if findings_form.left_kidney_texture.data else None,
        left_kidney_other=findings_form.left_kidney_other.data if findings_form.left_kidney_other.data else None,
        pancreas_findings=findings_form.pancreas_findings.data if findings_form.pancreas_findings.data else None,
        bladder_filling=findings_form.bladder_filling.data if findings_form.bladder_filling.data else None,
        bladder_stone_mass=findings_form.bladder_stone_mass.data if findings_form.bladder_stone_mass.data else None,
        bladder_mucosal_irregularity=findings_form.bladder_mucosal_irregularity.data if findings_form.bladder_mucosal_irregularity.data else None,
        prostate_findings=findings_form.prostate_findings.data if findings_form.prostate_findings.data else None,
        ascites=findings_form.ascites.data if findings_form.ascites.data else None,
        pleural_effusions=findings_form.pleural_effusions.data if findings_form.pleural_effusions.data else None,
        para_aortic_lymph_nodes=findings_form.para_aortic_lymph_nodes.data if findings_form.para_aortic_lymph_nodes.data else None,
        other_findings=findings_form.other_findings.data if findings_form.other_findings.data else None,
        comments=findings_form.comments.data if findings_form.comments.data else None
    )
    return findings

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html', title='DiagnoseAI - AI-Powered Radiology')

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_cases = Case.query.filter_by(user_id=current_user.id).count()
    total_patients = Patient.query.filter_by(created_by=current_user.id).count()
    
    # Get finalized reports count
    finalized_reports = db.session.query(Case).join(Report).filter(
        Case.user_id == current_user.id,
        Report.is_finalized == True
    ).count()
    
    # Get pending cases count
    pending_cases = total_cases - finalized_reports
    
    # Get today's statistics
    today = date.today()
    today_cases = Case.query.filter(
        Case.user_id == current_user.id,
        func.date(Case.created_at) == today
    ).count()
    
    today_reports = db.session.query(Case).join(Report).filter(
        Case.user_id == current_user.id,
        Report.is_finalized == True,
        func.date(Report.updated_at) == today
    ).count()
    
    # Get priority cases
    urgent_cases = Case.query.filter_by(user_id=current_user.id, priority='urgent').count()
    stat_cases = Case.query.filter_by(user_id=current_user.id, priority='stat').count()
    
    # Get recent cases with patient information
    recent_cases = Case.query.filter_by(user_id=current_user.id)\
        .join(Patient)\
        .order_by(Case.created_at.desc())\
        .limit(10).all()
    
    return render_template('main/dashboard.html', 
                         title='Radiology Dashboard',
                         total_cases=total_cases,
                         total_patients=total_patients,
                         finalized_reports=finalized_reports,
                         pending_cases=pending_cases,
                         today_cases=today_cases,
                         today_reports=today_reports,
                         urgent_cases=urgent_cases,
                         stat_cases=stat_cases,
                         recent_cases=recent_cases)

@bp.route('/patients/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    """Create a new patient record."""
    form = PatientForm()
    
    if form.validate_on_submit():
        try:
            # Check if patient ID already exists
            existing_patient = Patient.query.filter_by(patient_id=form.patient_id.data).first()
            if existing_patient:
                flash('A patient with this ID already exists. Please use a different ID.', 'error')
                return render_template('main/new_patient.html', title='New Patient', form=form)
            
            # Create new patient
            patient = Patient(
                patient_id=form.patient_id.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                date_of_birth=form.date_of_birth.data,
                gender=form.gender.data if form.gender.data else None,
                phone=form.phone.data,
                email=form.email.data,
                address=form.address.data,
                emergency_contact=form.emergency_contact.data,
                emergency_phone=form.emergency_phone.data,
                medical_record_number=form.medical_record_number.data,
                insurance_info=form.insurance_info.data,
                created_by=current_user.id
            )
            
            db.session.add(patient)
            db.session.commit()
            
            flash(f'Patient {patient.full_name} (ID: {patient.patient_id}) has been registered successfully!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while registering the patient. Please try again.', 'error')
            current_app.logger.error(f'Error creating patient: {str(e)}')
    
    return render_template('main/new_patient.html', title='New Patient', form=form)


@bp.route('/cases/new', methods=['GET', 'POST'])
@login_required
def new_case():
    """Create a new radiology case."""
    form = CaseForm()
    findings_form = StructuredFindingsForm()
    
    # Populate patient choices
    patients = Patient.query.filter_by(created_by=current_user.id).order_by(Patient.last_name, Patient.first_name).all()
    form.patient_id.choices = [(0, 'Select a patient...')] + [(p.id, f"{p.full_name} (ID: {p.patient_id})") for p in patients]
    
    if form.validate_on_submit() and findings_form.validate():
        try:
            # Generate unique case number
            case_count = Case.query.count() + 1
            case_number = f"{case_count:06d}"
            
            # Create new case record first
            case = Case(
                case_number=case_number,
                user_id=current_user.id,
                patient_id=form.patient_id.data,
                study_type=form.study_type.data,
                body_part=form.body_part.data,
                indication=form.indication.data,
                clinical_history=form.clinical_history.data,
                referring_physician=form.referring_physician.data,
                priority=form.priority.data,
                status='processing'
            )
            
            # Initialize saved_images list before any operations
            saved_images = []
            
            # Save case to get ID
            db.session.add(case)
            db.session.flush()  # Get the case ID without committing
            
            # Save structured findings if any provided
            if has_any_findings(findings_form):
                findings = create_findings_from_form(findings_form, case.id)
                db.session.add(findings)
                current_app.logger.info(f'Structured findings added to case {case.id}')
            
            # Process multiple images
            image_fields = [form.image1, form.image2, form.image3, form.image4]
            images_saved = 0
            
            for i, image_field in enumerate(image_fields):
                if image_field.data and image_field.data.filename:
                    case_image = save_case_image(image_field.data, case.id, i, current_user.id)
                    if case_image:
                        db.session.add(case_image)
                        saved_images.append(case_image.image_path)
                        images_saved += 1
                        
                        # Set legacy fields for backward compatibility (use first image)
                        if i == 0:
                            case.image_filename = case_image.filename
                            case.image_path = case_image.image_path
                    else:
                        flash(f'Failed to save image {i+1}. Please ensure it\'s a valid image file.', 'warning')
            
            if images_saved == 0:
                flash('No valid images were uploaded. Please try again.', 'error')
                return render_template('main/new_case.html', title='New Case', form=form, findings_form=findings_form)
            
            # Commit the case and images
            db.session.commit()
            
            # Use multi-agent pipeline for AI processing
            try:
                current_app.logger.info(
                    f'Starting multi-agent pipeline for case {case.formatted_case_number}'
                )
                
                # Run the multi-agent pipeline
                pipeline_result = run_multi_agent_pipeline(case.id)
                
                if pipeline_result['success']:
                    current_app.logger.info(
                        f'Multi-agent pipeline completed successfully for case {case.formatted_case_number}. '
                        f'Report ID: {pipeline_result["report_id"]}'
                    )
                    
                    # Update case status
                    case.status = 'draft_ready'
                    db.session.commit()
                    
                    flash(
                        f'Case {case.formatted_case_number} created successfully with {images_saved} images! '
                        f'AI draft report has been generated and is ready for review.',
                        'success'
                    )
                else:
                    # Pipeline failed but case was created
                    current_app.logger.error(
                        f'Multi-agent pipeline failed for case {case.formatted_case_number}: '
                        f'{pipeline_result["errors"]}'
                    )
                    case.status = 'ai_failed'
                    db.session.commit()
                    
                    error_summary = '; '.join(pipeline_result['errors'][:2])  # Show first 2 errors
                    flash(
                        f'Case {case.formatted_case_number} created successfully with {images_saved} images, '
                        f'but AI report generation failed: {error_summary}. '
                        f'The case has been marked for manual review.',
                        'warning'
                    )
                
            except Exception as e:
                # Log unexpected errors
                current_app.logger.error(
                    f'Unexpected error during multi-agent pipeline for case {case.formatted_case_number}: {str(e)}',
                    exc_info=True
                )
                case.status = 'ai_failed'
                db.session.commit()
                flash(
                    f'Case {case.formatted_case_number} created successfully with {images_saved} images, '
                    f'but AI report generation encountered an error: {str(e)}. '
                    f'The case has been marked for manual review.',
                    'warning'
                )
            
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            # Clean up any saved image files
            for image_path in saved_images:
                if os.path.exists(image_path):
                    os.remove(image_path)
            flash('An error occurred while creating the case. Please try again.', 'error')
            current_app.logger.error(f'Case creation error for user {current_user.id}: {str(e)}')
    
    return render_template('main/new_case.html', title='New Case', form=form, findings_form=findings_form)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle multiple ultrasound image upload and case creation."""
    form = UploadForm()
    
    if form.validate_on_submit():
        saved_images = []
        try:
            # Create a default patient for legacy uploads
            default_patient = Patient.query.filter_by(patient_id='LEGACY001').first()
            if not default_patient:
                default_patient = Patient(
                    patient_id='LEGACY001',
                    first_name='Legacy',
                    last_name='Patient',
                    created_by=current_user.id
                )
                db.session.add(default_patient)
                db.session.flush()
            
            # Generate case number
            case_count = Case.query.count() + 1
            case_number = f"{case_count:06d}"
            
            # Create case record first (without legacy image fields)
            case = Case(
                case_number=case_number,
                user_id=current_user.id,
                patient_id=default_patient.id,
                study_type='Ultrasound',
                indication=form.clinical_notes.data.strip(),
                priority='routine',
                status='processing'
            )
            
            # Save case to get ID
            db.session.add(case)
            db.session.flush()  # Get the case ID without committing
            
            # Process multiple images
            image_fields = [form.image1, form.image2, form.image3, form.image4]
            images_saved = 0
            
            for i, image_field in enumerate(image_fields):
                if image_field.data and image_field.data.filename:
                    case_image = save_case_image(image_field.data, case.id, i, current_user.id)
                    if case_image:
                        db.session.add(case_image)
                        saved_images.append(case_image.image_path)
                        images_saved += 1
                        
                        # Set legacy fields for backward compatibility (use first image)
                        if i == 0:
                            case.image_filename = case_image.filename
                            case.image_path = case_image.image_path
                    else:
                        flash(f'Failed to save image {i+1}. Please ensure it\'s a valid image file.', 'warning')
            
            if images_saved == 0:
                flash('No valid images were uploaded. Please try again.', 'error')
                return render_template('main/upload.html', title='Upload Images', form=form)
            
            # Commit the case and images
            db.session.commit()
            
            # Use multi-agent pipeline for AI processing
            try:
                current_app.logger.info(
                    f'Starting multi-agent pipeline for case {case.formatted_case_number} with {images_saved} images'
                )
                
                # Run the multi-agent pipeline
                pipeline_result = run_multi_agent_pipeline(case.id)
                
                if pipeline_result['success']:
                    current_app.logger.info(
                        f'Multi-agent pipeline completed successfully for case {case.formatted_case_number}. '
                        f'Report ID: {pipeline_result["report_id"]}'
                    )
                    
                    # Update case status
                    case.status = 'draft_ready'
                    db.session.commit()
                    
                    flash(
                        f'Case {case.formatted_case_number} created successfully with {images_saved} images! '
                        f'AI draft report has been generated and is ready for review.',
                        'success'
                    )
                else:
                    # Pipeline failed but case was created
                    current_app.logger.error(
                        f'Multi-agent pipeline failed for case {case.formatted_case_number}: '
                        f'{pipeline_result["errors"]}'
                    )
                    case.status = 'ai_failed'
                    db.session.commit()
                    
                    error_summary = '; '.join(pipeline_result['errors'][:2])  # Show first 2 errors
                    flash(
                        f'Case {case.formatted_case_number} created successfully with {images_saved} images, '
                        f'but AI report generation failed: {error_summary}. '
                        f'The case has been marked for manual review.',
                        'warning'
                    )
                
            except Exception as e:
                # Log unexpected errors
                current_app.logger.error(
                    f'Unexpected error during multi-agent pipeline for case {case.formatted_case_number}: {str(e)}',
                    exc_info=True
                )
                case.status = 'ai_failed'
                db.session.commit()
                flash(
                    f'Case {case.formatted_case_number} created successfully with {images_saved} images, '
                    f'but AI report generation encountered an error: {str(e)}. '
                    f'The case has been marked for manual review.',
                    'warning'
                )
            
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            # Clean up any saved image files
            for image_path in saved_images:
                if os.path.exists(image_path):
                    os.remove(image_path)
            flash('An error occurred while uploading your images. Please try again.', 'error')
            current_app.logger.error(f'Upload error for user {current_user.id}: {str(e)}')
    
    return render_template('main/upload.html', title='Upload Images', form=form)

@bp.route('/case/<int:case_id>')
@login_required
def view_case(case_id):
    """View details of a specific case."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    # Get the associated report if it exists
    report = None
    if case.reports:
        report = case.reports[0]  # Get the first (and should be only) report
    
    return render_template('main/case_detail.html', title=f'Case #{case.id}', case=case, report=report)


@bp.route('/case/<int:case_id>/review')
@login_required
def review_case(case_id):
    """Review AI-generated report with HITL actions (approve/modify/reject)."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    # Check if case has a report
    if not case.reports:
        flash('No report found for this case.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    report = case.reports[0]
    
    # Check if report is already finalized
    if report.is_finalized:
        flash('This report has already been finalized.', 'warning')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    return render_template('main/review.html', title=f'Review Case {case.formatted_case_number}', 
                         case=case, report=report)


@bp.route('/case/<int:case_id>/approve', methods=['POST'])
@login_required
def approve_case(case_id):
    """Approve AI-generated report without modifications."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    # Check if case has a report
    if not case.reports:
        flash('No report found for this case.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    report = case.reports[0]
    
    # Check if report is already finalized
    if report.is_finalized:
        flash('This report has already been finalized.', 'warning')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    try:
        # Get confidence level from form
        confidence_level = request.form.get('confidence_level', type=int)
        notes = request.form.get('notes', '').strip()
        
        if not confidence_level or confidence_level < 1 or confidence_level > 5:
            flash('Please select a valid confidence level.', 'error')
            return redirect(url_for('main.review_case', case_id=case_id))
        
        # Finalize the report (use draft as final)
        report.final_text = report.draft_text
        report.is_finalized = True
        report.updated_at = datetime.utcnow()
        
        # Update case status
        case.status = 'completed'
        
        # Create feedback record
        from app.models import Feedback
        feedback = Feedback(
            case_id=case.id,
            report_id=report.id,
            user_id=current_user.id,
            action='approve',
            confidence_level=confidence_level,
            modifications={'notes': notes} if notes else None
        )
        db.session.add(feedback)
        
        db.session.commit()
        
        flash(f'Report for Case {case.formatted_case_number} has been approved and finalized!', 'success')
        current_app.logger.info(
            f'Report {report.id} approved by user {current_user.id} '
            f'with confidence level {confidence_level}'
        )
        
        return redirect(url_for('main.view_case', case_id=case_id))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while approving the report. Please try again.', 'error')
        current_app.logger.error(f'Error approving report for case {case_id}: {str(e)}')
        return redirect(url_for('main.review_case', case_id=case_id))


@bp.route('/case/<int:case_id>/modify', methods=['POST'])
@login_required
def modify_case(case_id):
    """Modify AI-generated report before finalizing."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    # Check if case has a report
    if not case.reports:
        flash('No report found for this case.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    report = case.reports[0]
    
    # Check if report is already finalized
    if report.is_finalized:
        flash('This report has already been finalized.', 'warning')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    try:
        # Get modified text and notes from form
        modified_text = request.form.get('modified_text', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not modified_text:
            flash('Modified report text cannot be empty.', 'error')
            return redirect(url_for('main.review_case', case_id=case_id))
        
        if not notes:
            flash('Please provide a modification summary.', 'error')
            return redirect(url_for('main.review_case', case_id=case_id))
        
        # Calculate diff between original and modified text
        import difflib
        original_lines = report.draft_text.splitlines() if report.draft_text else []
        modified_lines = modified_text.splitlines()
        
        diff = list(difflib.unified_diff(
            original_lines,
            modified_lines,
            lineterm='',
            n=0  # No context lines
        ))
        
        # Count changes
        additions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))
        
        # Update report with modified text
        report.final_text = modified_text
        report.is_finalized = True
        report.updated_at = datetime.utcnow()
        
        # Update case status
        case.status = 'completed'
        
        # Create feedback record with diff
        from app.models import Feedback
        feedback = Feedback(
            case_id=case.id,
            report_id=report.id,
            user_id=current_user.id,
            action='modify',
            modifications={
                'notes': notes,
                'diff': diff[:100],  # Store first 100 lines of diff
                'additions': additions,
                'deletions': deletions,
                'original_length': len(original_lines),
                'modified_length': len(modified_lines)
            }
        )
        db.session.add(feedback)
        
        db.session.commit()
        
        flash(
            f'Report for Case {case.formatted_case_number} has been modified and finalized! '
            f'({additions} additions, {deletions} deletions)',
            'success'
        )
        current_app.logger.info(
            f'Report {report.id} modified by user {current_user.id}: '
            f'{additions} additions, {deletions} deletions'
        )
        
        return redirect(url_for('main.view_case', case_id=case_id))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while modifying the report. Please try again.', 'error')
        current_app.logger.error(f'Error modifying report for case {case_id}: {str(e)}')
        return redirect(url_for('main.review_case', case_id=case_id))


@bp.route('/case/<int:case_id>/reject', methods=['POST'])
@login_required
def reject_case(case_id):
    """Reject AI-generated report and provide independent interpretation."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    # Check if case has a report
    if not case.reports:
        flash('No report found for this case.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    report = case.reports[0]
    
    # Check if report is already finalized
    if report.is_finalized:
        flash('This report has already been finalized.', 'warning')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    try:
        # Get rejection details from form
        rejection_reason = request.form.get('rejection_reason', '').strip()
        rejection_details = request.form.get('rejection_details', '').strip()
        correct_interpretation = request.form.get('correct_interpretation', '').strip()
        
        if not rejection_reason:
            flash('Please select a rejection reason.', 'error')
            return redirect(url_for('main.review_case', case_id=case_id))
        
        if not rejection_details:
            flash('Please provide detailed explanation for rejection.', 'error')
            return redirect(url_for('main.review_case', case_id=case_id))
        
        # Mark report as rejected (not finalized, clear final_text)
        report.final_text = None
        report.is_finalized = False
        report.updated_at = datetime.utcnow()
        
        # Update case status to indicate manual review needed
        case.status = 'rejected'
        
        # Create feedback record with rejection details
        from app.models import Feedback
        feedback = Feedback(
            case_id=case.id,
            report_id=report.id,
            user_id=current_user.id,
            action='reject',
            rejection_reason=rejection_details,
            modifications={
                'rejection_category': rejection_reason,
                'rejection_details': rejection_details,
                'correct_interpretation': correct_interpretation,
                'rejected_draft': report.draft_text
            }
        )
        db.session.add(feedback)
        
        db.session.commit()
        
        flash(
            f'Report for Case {case.formatted_case_number} has been rejected. '
            f'The case is now marked for manual review.',
            'warning'
        )
        current_app.logger.info(
            f'Report {report.id} rejected by user {current_user.id}: '
            f'Reason: {rejection_reason}'
        )
        
        return redirect(url_for('main.view_case', case_id=case_id))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while rejecting the report. Please try again.', 'error')
        current_app.logger.error(f'Error rejecting report for case {case_id}: {str(e)}')
        return redirect(url_for('main.review_case', case_id=case_id))


@bp.route('/case/<int:case_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_report(case_id):
    """Edit and finalize a report for a specific case."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    # Check if case has a report
    if not case.reports:
        flash('No report found for this case.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    report = case.reports[0]
    
    # Check if report is already finalized
    if report.is_finalized:
        flash('This report has already been finalized and cannot be edited.', 'warning')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    form = ReportEditForm()
    
    if form.validate_on_submit():
        try:
            # Update report text
            report.final_text = form.report_text.data.strip()
            report.updated_at = datetime.utcnow()
            
            if form.finalize_report.data:
                # Finalize the report
                report.is_finalized = True
                case.status = 'completed'
                db.session.commit()
                
                flash(f'Report for Case #{case.id} has been finalized successfully!', 'success')
                current_app.logger.info(f'Report finalized for case {case.id} by user {current_user.id}')
                
                return redirect(url_for('main.view_case', case_id=case_id))
                
            elif form.save_draft.data:
                # Save as draft
                case.status = 'draft_edited'
                db.session.commit()
                
                flash(f'Draft report for Case #{case.id} has been saved successfully!', 'success')
                current_app.logger.info(f'Draft report saved for case {case.id} by user {current_user.id}')
                
                # Stay on edit page for further editing
                
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving the report. Please try again.', 'error')
            current_app.logger.error(f'Error saving report for case {case_id}: {str(e)}')
    
    # Pre-populate form with existing content
    if request.method == 'GET':
        # Use final_text if available, otherwise use draft_text
        form.report_text.data = report.final_text or report.draft_text or ''
        form.case_id.data = case_id
    
    return render_template('main/edit_report.html', 
                         title=f'Edit Report - Case #{case.id}', 
                         case=case, 
                         report=report, 
                         form=form)


@bp.route('/case/<int:case_id>/download/text')
@login_required
def download_text_report(case_id):
    """Download report as plain text file."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    if not case.reports or not case.reports[0].is_finalized:
        flash('No finalized report available for download.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    report = case.reports[0]
    
    # Create text content
    content = f"""RADIOLOGY REPORT
Case ID: #{case.id}
Date: {case.created_at.strftime('%Y-%m-%d %H:%M')}
Patient Information: [REDACTED FOR PRIVACY]

CLINICAL INFORMATION:
Indication: {case.indication or 'No indication provided.'}
{f'Clinical History: {case.clinical_history}' if case.clinical_history else ''}
{f'Body Part: {case.body_part}' if case.body_part else ''}

REPORT:
{report.final_text or report.draft_text}

Report finalized on: {report.updated_at.strftime('%Y-%m-%d %H:%M')}
Generated by DiagnoseAI System
"""
    
    # Create response
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = f'attachment; filename="report_case_{case_id}.txt"'
    
    current_app.logger.info(f'Text report downloaded for case {case_id} by user {current_user.id}')
    return response


@bp.route('/case/<int:case_id>/download/pdf')
@login_required
def download_pdf_report(case_id):
    """Download report as PDF file."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    if not case.reports or not case.reports[0].is_finalized:
        flash('No finalized report available for download.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    report = case.reports[0]
    
    try:
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor='#2c3e50'
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("RADIOLOGY REPORT", title_style))
        story.append(Spacer(1, 20))
        
        # Case information
        story.append(Paragraph("CASE INFORMATION", heading_style))
        story.append(Paragraph(f"<b>Case ID:</b> #{case.id}", styles['Normal']))
        story.append(Paragraph(f"<b>Date Created:</b> {case.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"<b>Report Finalized:</b> {report.updated_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"<b>Image File:</b> {case.image_filename}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Clinical information
        story.append(Paragraph("CLINICAL INFORMATION", heading_style))
        
        # Indication
        indication_text = f"<b>Indication:</b> {case.indication or 'No indication provided.'}"
        story.append(Paragraph(indication_text, styles['Normal']))
        
        # Clinical history if available
        if case.clinical_history:
            history_text = f"<b>Clinical History:</b> {case.clinical_history}"
            story.append(Paragraph(history_text, styles['Normal']))
        
        # Body part if available
        if case.body_part:
            body_part_text = f"<b>Body Part:</b> {case.body_part}"
            story.append(Paragraph(body_part_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Report content
        story.append(Paragraph("RADIOLOGY REPORT", heading_style))
        
        # Convert markdown-like formatting to PDF-friendly format
        report_text = report.final_text or report.draft_text
        if report_text:
            # Convert **bold** to <b>bold</b>
            report_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', report_text)
            # Convert *italic* to <i>italic</i>
            report_text = re.sub(r'\*([^*]+?)\*', r'<i>\1</i>', report_text)
            
            # Split into paragraphs and add to story
            paragraphs = report_text.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), styles['Normal']))
                    story.append(Spacer(1, 12))
        
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(Paragraph("Generated by DiagnoseAI System", styles['Italic']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        current_app.logger.info(f'PDF report generated for case {case_id} by user {current_user.id}')
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'report_case_{case_id}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f'Error generating PDF for case {case_id}: {str(e)}')
        flash('Error generating PDF report. Please try again.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))


@bp.route('/patients')
@login_required
def all_patients():
    """View all patients."""
    patients = Patient.query.filter_by(created_by=current_user.id)\
        .order_by(Patient.last_name, Patient.first_name).all()
    return render_template('main/patients.html', title='Patients', patients=patients)


@bp.route('/cases')
@login_required
def all_cases():
    """View all cases."""
    cases = Case.query.filter_by(user_id=current_user.id)\
        .join(Patient)\
        .order_by(Case.created_at.desc()).all()
    return render_template('main/cases.html', title='All Cases', cases=cases)


@bp.route('/cases/pending')
@login_required
def pending_cases():
    """View pending cases that need review."""
    cases = Case.query.filter_by(user_id=current_user.id)\
        .join(Patient)\
        .outerjoin(Report)\
        .filter(
            (Report.id == None) | (Report.is_finalized == False)
        )\
        .order_by(Case.priority.desc(), Case.created_at.asc()).all()
    return render_template('main/pending_cases.html', title='Pending Cases', cases=cases)


@bp.route('/patients/<int:patient_id>')
@login_required
def view_patient(patient_id):
    """View patient details."""
    patient = Patient.query.filter_by(id=patient_id, created_by=current_user.id).first_or_404()
    cases = Case.query.filter_by(patient_id=patient_id, user_id=current_user.id)\
        .order_by(Case.created_at.desc()).all()
    return render_template('main/patient_detail.html', title=f'Patient: {patient.full_name}', 
                         patient=patient, cases=cases)


@bp.route('/case/<int:case_id>/delete', methods=['POST'])
@login_required
def delete_case(case_id):
    """Delete a case and its associated files and reports."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    try:
        # Store case info for flash message
        case_number = case.formatted_case_number
        patient_name = case.patient.full_name
        
        # Delete associated image files
        # Delete case images
        for case_image in case.images:
            if case_image.image_path and os.path.exists(case_image.image_path):
                try:
                    os.remove(case_image.image_path)
                    current_app.logger.info(f'Deleted image file: {case_image.image_path}')
                except OSError as e:
                    current_app.logger.warning(f'Could not delete image file {case_image.image_path}: {str(e)}')
        
        # Delete legacy single image if it exists
        if case.image_path and os.path.exists(case.image_path):
            try:
                os.remove(case.image_path)
                current_app.logger.info(f'Deleted image file: {case.image_path}')
            except OSError as e:
                current_app.logger.warning(f'Could not delete image file {case.image_path}: {str(e)}')
        
        # Explicitly delete related records (for SQLite compatibility)
        # Delete structured findings
        if case.structured_findings:
            db.session.delete(case.structured_findings)
        
        # Delete AI generated findings
        for ai_finding in case.ai_findings:
            # Delete evaluations for this AI finding
            FindingsEvaluation.query.filter_by(ai_finding_id=ai_finding.id).delete()
            db.session.delete(ai_finding)
        
        # Delete agent outputs
        AgentOutput.query.filter_by(case_id=case_id).delete()
        
        # Delete feedback
        Feedback.query.filter_by(case_id=case_id).delete()
        
        # Delete RAG cases
        RAGCase.query.filter_by(case_id=case_id).delete()
        
        # Delete case images
        CaseImage.query.filter_by(case_id=case_id).delete()
        
        # Delete reports (and their associated feedback)
        for report in case.reports:
            Feedback.query.filter_by(report_id=report.id).delete()
            db.session.delete(report)
        
        # Finally, delete the case
        db.session.delete(case)
        db.session.commit()
        
        flash(f'Case {case_number} for patient {patient_name} has been successfully deleted.', 'success')
        current_app.logger.info(f'Case {case_number} deleted by user {current_user.id}')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the case. Please try again.', 'error')
        current_app.logger.error(f'Error deleting case {case_id}: {str(e)}')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    return redirect(url_for('main.dashboard'))


@bp.route('/case/<int:case_id>/image')
@login_required
def view_case_image(case_id):
    """Serve the case image file."""
    case = Case.query.filter_by(id=case_id, user_id=current_user.id).first_or_404()
    
    if not case.image_path or not os.path.exists(case.image_path):
        flash('Image file not found.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))
    
    try:
        return send_file(case.image_path, as_attachment=False)
    except Exception as e:
        current_app.logger.error(f'Error serving image for case {case_id}: {str(e)}')
        flash('Error loading image.', 'error')
        return redirect(url_for('main.view_case', case_id=case_id))


@bp.route('/ai-test', methods=['GET', 'POST'])
@login_required
def ai_test():
    """AI Testing page for analyzing ultrasound images without patient data."""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'test_image' not in request.files:
                flash('No image file selected.', 'error')
                return redirect(request.url)
            
            file = request.files['test_image']
            if file.filename == '':
                flash('No image file selected.', 'error')
                return redirect(request.url)
            
            if not allowed_file(file.filename):
                flash('Invalid file type. Please upload a JPG, PNG, or other supported image format.', 'error')
                return redirect(request.url)
            
            # Get optional context from form
            image_context = request.form.get('image_context', '').strip()
            view_type = request.form.get('view_type', '').strip()
            
            # Save uploaded file permanently for testing records
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f_')
            saved_filename = f"ai_test_{timestamp}{filename}"
            
            # Create permanent test upload directory
            test_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'ai_tests', str(current_user.id))
            os.makedirs(test_upload_dir, exist_ok=True)
            
            file_path = os.path.join(test_upload_dir, saved_filename)
            file.save(file_path)
            
            # Validate the uploaded image
            if not validate_image(file_path):
                os.remove(file_path)
                flash('Invalid image file. Please upload a valid image.', 'error')
                return redirect(request.url)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            mime_type = file.content_type or 'image/jpeg'
            
            # Generate AI analysis
            try:
                current_app.logger.info(f'Starting AI test analysis for image: {filename}')
                
                # Create clinical context for AI
                clinical_notes = "AI TESTING MODE - No patient data available.\n"
                if view_type:
                    clinical_notes += f"Image Type: {view_type}\n"
                if image_context:
                    clinical_notes += f"Additional Context: {image_context}\n"
                clinical_notes += "Please analyze this ultrasound image and provide detailed findings."
                
                raw_response, formatted_text = generate_draft_report(
                    image_path=file_path,
                    clinical_notes=clinical_notes
                )
                
                current_app.logger.info(f'AI test analysis completed for image: {saved_filename}')
                
                # Save AI test result to database
                try:
                    ai_test_result = AITestResult(
                        user_id=current_user.id,
                        original_filename=file.filename,
                        saved_filename=saved_filename,
                        image_path=file_path,
                        view_type=view_type,
                        image_context=image_context,
                        ai_analysis=formatted_text,
                        raw_response=raw_response,
                        file_size=file_size,
                        mime_type=mime_type
                    )
                    
                    db.session.add(ai_test_result)
                    db.session.commit()
                    
                    current_app.logger.info(f'AI test result saved to database with ID: {ai_test_result.id}')
                    
                except Exception as db_error:
                    current_app.logger.error(f'Failed to save AI test result to database: {str(db_error)}')
                    db.session.rollback()
                    # Continue anyway - don't fail the analysis because of DB issues
                
                # Return results (now with saved test result ID)
                return render_template('main/ai_test_results.html', 
                                     title='AI Test Results',
                                     original_filename=file.filename,
                                     view_type=view_type,
                                     image_context=image_context,
                                     ai_analysis=formatted_text,
                                     raw_response=raw_response,
                                     analysis_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                     test_result_id=ai_test_result.id if 'ai_test_result' in locals() else None)
                
            except AIServiceError as e:
                # Clean up file on error
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                current_app.logger.error(f'AI service error during test: {str(e)}')
                flash(f'AI analysis failed: {str(e)}', 'error')
                return redirect(request.url)
                
            except Exception as e:
                # Clean up file on error
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                current_app.logger.error(f'Unexpected error during AI test: {str(e)}', exc_info=True)
                flash(f'AI analysis encountered an error: {str(e)}', 'error')
                return redirect(request.url)
                
        except Exception as e:
            current_app.logger.error(f'Error in AI test upload: {str(e)}')
            flash('An error occurred while processing your request. Please try again.', 'error')
            return redirect(request.url)
    
    return render_template('main/ai_test.html', title='AI Testing - Liver Pathology Analysis')


@bp.route('/ai-test/results')
@login_required
def ai_test_results_list():
    """View all saved AI test results."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get all AI test results for current user, ordered by most recent
    results = AITestResult.query.filter_by(user_id=current_user.id)\
        .order_by(AITestResult.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate some statistics
    total_tests = AITestResult.query.filter_by(user_id=current_user.id).count()
    evaluated_tests = AITestResult.query.filter_by(user_id=current_user.id)\
        .filter(AITestResult.overall_rating.isnot(None)).count()
    
    # Calculate average ratings
    avg_accuracy = db.session.query(db.func.avg(AITestResult.accuracy_rating))\
        .filter_by(user_id=current_user.id)\
        .filter(AITestResult.accuracy_rating.isnot(None)).scalar()
    
    avg_overall = db.session.query(db.func.avg(AITestResult.overall_rating))\
        .filter_by(user_id=current_user.id)\
        .filter(AITestResult.overall_rating.isnot(None)).scalar()
    
    stats = {
        'total_tests': total_tests,
        'evaluated_tests': evaluated_tests,
        'avg_accuracy': round(avg_accuracy, 2) if avg_accuracy else None,
        'avg_overall': round(avg_overall, 2) if avg_overall else None
    }
    
    return render_template('main/ai_test_results_list.html', 
                         title='AI Test Results History',
                         results=results,
                         stats=stats)


@bp.route('/ai-test/result/<int:result_id>')
@login_required
def view_ai_test_result(result_id):
    """View a specific AI test result."""
    result = AITestResult.query.filter_by(id=result_id, user_id=current_user.id).first_or_404()
    
    return render_template('main/ai_test_result_detail.html', 
                         title=f'AI Test Result - {result.original_filename}',
                         result=result)


@bp.route('/ai-test/result/<int:result_id>/image')
@login_required
def serve_ai_test_image(result_id):
    """Serve the saved AI test image."""
    result = AITestResult.query.filter_by(id=result_id, user_id=current_user.id).first_or_404()
    
    if not result.image_path or not os.path.exists(result.image_path):
        flash('Image file not found.', 'error')
        return redirect(url_for('main.view_ai_test_result', result_id=result_id))
    
    try:
        return send_file(result.image_path, as_attachment=False)
    except Exception as e:
        current_app.logger.error(f'Error serving AI test image for result {result_id}: {str(e)}')
        flash('Error loading image.', 'error')
        return redirect(url_for('main.view_ai_test_result', result_id=result_id))


@bp.route('/ai-test/<int:test_id>/findings')
@login_required
def view_ai_test_findings(test_id):
    """View structured findings for an AI test result."""
    test_result = AITestResult.query.filter_by(id=test_id, user_id=current_user.id).first_or_404()
    
    # Get AI-generated findings for this test
    findings = AIGeneratedFindings.query.filter_by(ai_test_result_id=test_id).first()
    
    return render_template('main/ai_test_findings.html',
                         title=f'AI Test Findings - #{test_id}',
                         test_result=test_result,
                         findings=findings)


@bp.route('/ai-test/<int:test_id>/image')
@login_required
def view_ai_test_image(test_id):
    """Serve the AI test image."""
    test_result = AITestResult.query.filter_by(id=test_id, user_id=current_user.id).first_or_404()
    
    if not test_result.image_path or not os.path.exists(test_result.image_path):
        flash('Image file not found.', 'error')
        return redirect(url_for('main.view_ai_test_findings', test_id=test_id))
    
    try:
        return send_file(test_result.image_path, as_attachment=False)
    except Exception as e:
        current_app.logger.error(f'Error serving AI test image for test {test_id}: {str(e)}')
        flash('Error loading image.', 'error')
        return redirect(url_for('main.view_ai_test_findings', test_id=test_id))


@bp.route('/ai-test/result/<int:result_id>/evaluate', methods=['POST'])
@login_required
def evaluate_ai_test_result(result_id):
    """Save evaluation for an AI test result."""
    result = AITestResult.query.filter_by(id=result_id, user_id=current_user.id).first_or_404()
    
    try:
        # Get evaluation data from form
        result.accuracy_rating = request.form.get('accuracy', type=int)
        result.completeness_rating = request.form.get('completeness', type=int)
        result.terminology_rating = request.form.get('terminology', type=int)
        result.overall_rating = request.form.get('overall', type=int)
        result.expected_pathology = request.form.get('expected_pathology', '').strip()
        result.ai_identified_pathology = request.form.get('ai_identified', '').strip()
        result.evaluation_comments = request.form.get('comments', '').strip()
        result.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Evaluation saved successfully!', 'success')
        current_app.logger.info(f'AI test result {result_id} evaluated by user {current_user.id}')
        
    except Exception as e:
        db.session.rollback()
        flash('Error saving evaluation. Please try again.', 'error')
        current_app.logger.error(f'Error saving evaluation for AI test result {result_id}: {str(e)}')
    
    return redirect(url_for('main.view_ai_test_result', result_id=result_id))


@bp.route('/ai-test/result/<int:result_id>/delete', methods=['POST'])
@login_required
def delete_ai_test_result(result_id):
    """Delete an AI test result and its associated image."""
    result = AITestResult.query.filter_by(id=result_id, user_id=current_user.id).first_or_404()
    
    try:
        # Delete the image file
        if result.image_path and os.path.exists(result.image_path):
            try:
                os.remove(result.image_path)
                current_app.logger.info(f'Deleted AI test image: {result.image_path}')
            except OSError as e:
                current_app.logger.warning(f'Could not delete AI test image {result.image_path}: {str(e)}')
        
        # Delete the database record
        filename = result.original_filename
        db.session.delete(result)
        db.session.commit()
        
        flash(f'AI test result for "{filename}" has been deleted successfully.', 'success')
        current_app.logger.info(f'AI test result {result_id} deleted by user {current_user.id}')
        
    except Exception as e:
        db.session.rollback()
        flash('Error deleting AI test result. Please try again.', 'error')
        current_app.logger.error(f'Error deleting AI test result {result_id}: {str(e)}')
    
    return redirect(url_for('main.ai_test_results_list'))



# ============================================================================
# Structured Findings Evaluation Routes
# ============================================================================

def extract_field_correctness_from_form(form_data):
    """Extract field correctness data from evaluation form."""
    field_correctness = {}
    
    # Define all possible finding fields
    finding_fields = [
        'liver_size', 'liver_texture', 'liver_focal_defect', 'liver_cbd', 'liver_pv',
        'spleen_size', 'spleen_focal_defect',
        'gb_calculus', 'gb_wall_edema',
        'right_kidney_size', 'right_kidney_texture', 'right_kidney_other',
        'left_kidney_size', 'left_kidney_texture', 'left_kidney_other',
        'pancreas_findings',
        'bladder_filling', 'bladder_stone_mass', 'bladder_mucosal_irregularity',
        'prostate_findings',
        'ascites', 'pleural_effusions', 'para_aortic_lymph_nodes', 'other_findings',
        'comments'
    ]
    
    # Extract correctness for each field
    for field in finding_fields:
        checkbox_value = form_data.get(f'correct_{field}')
        if checkbox_value is not None:
            field_correctness[field] = checkbox_value == 'on'
    
    return field_correctness


def calculate_organ_metrics(evaluations):
    """Calculate accuracy metrics per organ system."""
    from app.models import FindingsEvaluation
    
    organ_groups = {
        'Liver': ['liver_size', 'liver_texture', 'liver_focal_defect', 'liver_cbd', 'liver_pv'],
        'Spleen': ['spleen_size', 'spleen_focal_defect'],
        'Gall Bladder': ['gb_calculus', 'gb_wall_edema'],
        'Right Kidney': ['right_kidney_size', 'right_kidney_texture', 'right_kidney_other'],
        'Left Kidney': ['left_kidney_size', 'left_kidney_texture', 'left_kidney_other'],
        'Pancreas': ['pancreas_findings'],
        'Urinary Bladder': ['bladder_filling', 'bladder_stone_mass', 'bladder_mucosal_irregularity'],
        'Prostate': ['prostate_findings'],
        'Additional': ['ascites', 'pleural_effusions', 'para_aortic_lymph_nodes', 'other_findings']
    }
    
    organ_metrics = {}
    
    for organ_name, fields in organ_groups.items():
        total_fields = 0
        correct_fields = 0
        
        for evaluation in evaluations:
            field_correctness = evaluation.field_correctness or {}
            for field in fields:
                if field in field_correctness:
                    total_fields += 1
                    if field_correctness[field]:
                        correct_fields += 1
        
        if total_fields > 0:
            accuracy = (correct_fields / total_fields) * 100
            organ_metrics[organ_name] = {
                'total': total_fields,
                'correct': correct_fields,
                'accuracy': round(accuracy, 2)
            }
    
    return organ_metrics


def calculate_field_metrics(evaluations):
    """Calculate accuracy metrics per field type."""
    from app.models import FindingsEvaluation
    
    field_metrics = {}
    
    for evaluation in evaluations:
        field_correctness = evaluation.field_correctness or {}
        for field, is_correct in field_correctness.items():
            if field not in field_metrics:
                field_metrics[field] = {'total': 0, 'correct': 0}
            
            field_metrics[field]['total'] += 1
            if is_correct:
                field_metrics[field]['correct'] += 1
    
    # Calculate accuracy percentages
    for field, stats in field_metrics.items():
        if stats['total'] > 0:
            stats['accuracy'] = round((stats['correct'] / stats['total']) * 100, 2)
        else:
            stats['accuracy'] = 0
    
    # Sort by field name
    field_metrics = dict(sorted(field_metrics.items()))
    
    return field_metrics


def calculate_temporal_metrics(evaluations):
    """Calculate temporal trends in accuracy."""
    from app.models import FindingsEvaluation
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Group evaluations by date
    daily_metrics = defaultdict(lambda: {'total': 0, 'correct': 0})
    
    for evaluation in evaluations:
        date_key = evaluation.created_at.date()
        daily_metrics[date_key]['total'] += evaluation.total_fields or 0
        daily_metrics[date_key]['correct'] += evaluation.correct_fields or 0
    
    # Calculate accuracy for each day
    temporal_data = []
    for date_key in sorted(daily_metrics.keys()):
        stats = daily_metrics[date_key]
        if stats['total'] > 0:
            accuracy = (stats['correct'] / stats['total']) * 100
            temporal_data.append({
                'date': date_key.strftime('%Y-%m-%d'),
                'total': stats['total'],
                'correct': stats['correct'],
                'accuracy': round(accuracy, 2)
            })
    
    return temporal_data


@bp.route('/ai-test/result/<int:result_id>/evaluate-findings', methods=['GET', 'POST'])
@login_required
def evaluate_findings(result_id):
    """Evaluate AI-generated structured findings."""
    from app.models import AITestResult, AIGeneratedFindings, FindingsEvaluation
    
    # Get the AI test result
    test_result = AITestResult.query.filter_by(
        id=result_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Get AI-generated findings for this test result
    ai_findings = AIGeneratedFindings.query.filter_by(
        ai_test_result_id=result_id
    ).first()
    
    if not ai_findings:
        flash('No AI-generated findings found for this test result.', 'error')
        return redirect(url_for('main.view_ai_test_result', result_id=result_id))
    
    # Check if already evaluated
    existing_evaluation = FindingsEvaluation.query.filter_by(
        ai_finding_id=ai_findings.id,
        user_id=current_user.id
    ).first()
    
    if request.method == 'POST':
        try:
            # Extract field correctness from form
            field_correctness = extract_field_correctness_from_form(request.form)
            
            # Calculate metrics
            total_fields = len(field_correctness)
            correct_fields = sum(1 for v in field_correctness.values() if v)
            accuracy = (correct_fields / total_fields * 100) if total_fields > 0 else 0
            
            # Get evaluation notes
            evaluation_notes = request.form.get('evaluation_notes', '').strip()
            
            if existing_evaluation:
                # Update existing evaluation
                existing_evaluation.field_correctness = field_correctness
                existing_evaluation.total_fields = total_fields
                existing_evaluation.correct_fields = correct_fields
                existing_evaluation.accuracy_percentage = accuracy
                existing_evaluation.evaluation_notes = evaluation_notes
                existing_evaluation.created_at = datetime.utcnow()
                
                flash(f'Evaluation updated! Accuracy: {accuracy:.1f}%', 'success')
            else:
                # Create new evaluation
                evaluation = FindingsEvaluation(
                    ai_finding_id=ai_findings.id,
                    user_id=current_user.id,
                    field_correctness=field_correctness,
                    total_fields=total_fields,
                    correct_fields=correct_fields,
                    accuracy_percentage=accuracy,
                    evaluation_notes=evaluation_notes
                )
                db.session.add(evaluation)
                
                flash(f'Evaluation saved! Accuracy: {accuracy:.1f}%', 'success')
            
            db.session.commit()
            
            current_app.logger.info(
                f'Findings evaluation saved for AI finding {ai_findings.id} by user {current_user.id}. '
                f'Accuracy: {accuracy:.1f}%'
            )
            
            return redirect(url_for('main.view_ai_test_result', result_id=result_id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while saving the evaluation. Please try again.', 'error')
            current_app.logger.error(f'Error saving findings evaluation: {str(e)}')
    
    return render_template('main/evaluate_findings.html',
                         title='Evaluate AI Findings',
                         test_result=test_result,
                         findings=ai_findings,
                         evaluation=existing_evaluation)


@bp.route('/findings/metrics')
@login_required
def findings_metrics():
    """View accuracy metrics dashboard for AI-generated findings."""
    from app.models import FindingsEvaluation, AIGeneratedFindings, AITestResult
    
    # Get all evaluations for current user
    evaluations = db.session.query(FindingsEvaluation)\
        .join(AIGeneratedFindings)\
        .join(AITestResult, AIGeneratedFindings.ai_test_result_id == AITestResult.id)\
        .filter(AITestResult.user_id == current_user.id)\
        .all()
    
    if not evaluations:
        return render_template('main/findings_metrics.html',
                             title='Findings Metrics',
                             has_data=False,
                             total_evaluations=0)
    
    # Calculate overall metrics
    total_evaluations = len(evaluations)
    total_fields_evaluated = sum(e.total_fields or 0 for e in evaluations)
    total_correct_fields = sum(e.correct_fields or 0 for e in evaluations)
    overall_accuracy = (total_correct_fields / total_fields_evaluated * 100) if total_fields_evaluated > 0 else 0
    
    # Calculate per-organ metrics
    organ_metrics = calculate_organ_metrics(evaluations)
    
    # Calculate per-field metrics
    field_metrics = calculate_field_metrics(evaluations)
    
    # Calculate temporal trends
    temporal_metrics = calculate_temporal_metrics(evaluations)
    
    # Get recent evaluations
    recent_evaluations = db.session.query(FindingsEvaluation)\
        .join(AIGeneratedFindings)\
        .join(AITestResult, AIGeneratedFindings.ai_test_result_id == AITestResult.id)\
        .filter(AITestResult.user_id == current_user.id)\
        .order_by(FindingsEvaluation.created_at.desc())\
        .limit(10)\
        .all()
    
    return render_template('main/findings_metrics.html',
                         title='Findings Metrics Dashboard',
                         has_data=True,
                         total_evaluations=total_evaluations,
                         total_fields_evaluated=total_fields_evaluated,
                         total_correct_fields=total_correct_fields,
                         overall_accuracy=round(overall_accuracy, 2),
                         organ_metrics=organ_metrics,
                         field_metrics=field_metrics,
                         temporal_metrics=temporal_metrics,
                         recent_evaluations=recent_evaluations)
