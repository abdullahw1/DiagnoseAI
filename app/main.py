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
from app.models import Case, Report, Patient
from app.forms import UploadForm, ReportEditForm, PatientForm, CaseForm
from app.ai_service import generate_draft_report, AIServiceError
from app import db

bp = Blueprint('main', __name__)

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

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

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
    
    # Populate patient choices
    patients = Patient.query.filter_by(created_by=current_user.id).order_by(Patient.last_name, Patient.first_name).all()
    form.patient_id.choices = [(0, 'Select a patient...')] + [(p.id, f"{p.full_name} (ID: {p.patient_id})") for p in patients]
    
    if form.validate_on_submit():
        try:
            # Generate unique case number
            case_count = Case.query.count() + 1
            case_number = f"{case_count:06d}"
            
            # Get the uploaded file
            file = form.image.data
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            if not filename:
                flash('Invalid filename. Please select a valid image file.', 'error')
                return render_template('main/new_case.html', title='New Case', form=form)
            
            # Add timestamp to filename to avoid conflicts
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f_')
            filename = timestamp + filename
            
            # Create user-specific upload directory
            user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
            os.makedirs(user_upload_dir, exist_ok=True)
            
            # Save file path
            file_path = os.path.join(user_upload_dir, filename)
            
            # Save the file
            file.save(file_path)
            
            # Validate the uploaded image
            if not validate_image(file_path):
                os.remove(file_path)  # Clean up invalid file
                flash('The uploaded file is not a valid image. Please try again.', 'error')
                return render_template('main/new_case.html', title='New Case', form=form)
            
            # Create new case record
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
                image_filename=filename,
                image_path=file_path,
                status='processing'
            )
            
            # Save to database
            db.session.add(case)
            db.session.commit()
            
            # Generate AI draft report automatically
            try:
                current_app.logger.info(f'Starting AI draft report generation for case {case.formatted_case_number}')
                
                # Combine clinical information for AI
                clinical_notes = f"Indication: {case.indication}\n"
                if case.clinical_history:
                    clinical_notes += f"Clinical History: {case.clinical_history}\n"
                if case.body_part:
                    clinical_notes += f"Body Part: {case.body_part}\n"
                
                raw_response, formatted_text = generate_draft_report(
                    image_path=file_path,
                    clinical_notes=clinical_notes
                )
                
                current_app.logger.info(f'AI draft report generated, creating report record for case {case.formatted_case_number}')
                
                # Create report record
                report = Report(
                    case_id=case.id,
                    draft_json=raw_response,
                    draft_text=formatted_text,
                    is_finalized=False
                )
                
                # Update case status
                case.status = 'draft_ready'
                
                db.session.add(report)
                db.session.commit()
                
                flash(f'Case {case.formatted_case_number} created successfully! AI draft report has been generated and is ready for review.', 'success')
                current_app.logger.info(f'AI draft report generated successfully for case {case.formatted_case_number}')
                
            except AIServiceError as e:
                # Log the error but don't fail the case creation
                current_app.logger.error(f'AI service error for case {case.formatted_case_number}: {str(e)}')
                case.status = 'ai_failed'
                db.session.commit()
                flash(f'Case {case.formatted_case_number} created successfully, but AI report generation failed: {str(e)}. The case has been marked for manual review.', 'warning')
                
            except Exception as e:
                # Log unexpected errors
                current_app.logger.error(f'Unexpected error during AI report generation for case {case.formatted_case_number}: {str(e)}', exc_info=True)
                case.status = 'ai_failed'
                db.session.commit()
                flash(f'Case {case.formatted_case_number} created successfully, but AI report generation encountered an error: {str(e)}. The case has been marked for manual review.', 'warning')
            
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            # Clean up file if it was saved
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            flash('An error occurred while creating the case. Please try again.', 'error')
            current_app.logger.error(f'Case creation error for user {current_user.id}: {str(e)}')
    
    return render_template('main/new_case.html', title='New Case', form=form)


@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle ultrasound image upload and case creation."""
    form = UploadForm()
    

    if form.validate_on_submit():
        try:
            # Get the uploaded file
            file = form.image.data
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            if not filename:
                flash('Invalid filename. Please select a valid image file.', 'error')
                return render_template('main/upload.html', title='Upload Image', form=form)
            
            # Add timestamp to filename to avoid conflicts
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f_')
            filename = timestamp + filename
            
            # Create user-specific upload directory
            user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id))
            os.makedirs(user_upload_dir, exist_ok=True)
            
            # Save file path
            file_path = os.path.join(user_upload_dir, filename)
            
            # Save the file
            file.save(file_path)
            
            # Validate the uploaded image
            if not validate_image(file_path):
                os.remove(file_path)  # Clean up invalid file
                flash('The uploaded file is not a valid image. Please try again.', 'error')
                return render_template('main/upload.html', title='Upload Image', form=form)
            
            # Create new case record (legacy upload route - should use new_case instead)
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
            
            case = Case(
                case_number=case_number,
                user_id=current_user.id,
                patient_id=default_patient.id,
                study_type='Ultrasound',
                indication=form.clinical_notes.data.strip(),
                priority='routine',
                image_filename=filename,
                image_path=file_path,
                status='processing'
            )
            
            # Save to database
            db.session.add(case)
            db.session.commit()
            
            # Generate AI draft report automatically
            try:
                current_app.logger.info(f'Starting AI draft report generation for case {case.formatted_case_number}')
                current_app.logger.info(f'Image path: {file_path}')
                
                # Combine clinical information for AI
                clinical_notes = f"Indication: {case.indication}\n"
                if case.clinical_history:
                    clinical_notes += f"Clinical History: {case.clinical_history}\n"
                if case.body_part:
                    clinical_notes += f"Body Part: {case.body_part}\n"
                
                current_app.logger.info(f'Clinical notes length: {len(clinical_notes)} characters')
                
                raw_response, formatted_text = generate_draft_report(
                    image_path=file_path,
                    clinical_notes=clinical_notes
                )
                
                current_app.logger.info(f'AI draft report generated, creating report record for case {case.id}')
                
                # Create report record
                report = Report(
                    case_id=case.id,
                    draft_json=raw_response,
                    draft_text=formatted_text,
                    is_finalized=False
                )
                
                # Update case status
                case.status = 'draft_ready'
                
                db.session.add(report)
                db.session.commit()
                
                flash(f'Case {case.formatted_case_number} created successfully! AI draft report has been generated and is ready for review.', 'success')
                current_app.logger.info(f'AI draft report generated successfully for case {case.formatted_case_number}')
                
            except AIServiceError as e:
                # Log the error but don't fail the case creation
                current_app.logger.error(f'AI service error for case {case.formatted_case_number}: {str(e)}')
                case.status = 'ai_failed'
                db.session.commit()
                flash(f'Case {case.formatted_case_number} created successfully, but AI report generation failed: {str(e)}. The case has been marked for manual review.', 'warning')
                
            except Exception as e:
                # Log unexpected errors
                current_app.logger.error(f'Unexpected error during AI report generation for case {case.formatted_case_number}: {str(e)}', exc_info=True)
                case.status = 'ai_failed'
                db.session.commit()
                flash(f'Case {case.formatted_case_number} created successfully, but AI report generation encountered an error: {str(e)}. The case has been marked for manual review.', 'warning')
            
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            # Clean up file if it was saved
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            flash('An error occurred while uploading your image. Please try again.', 'error')
            current_app.logger.error(f'Upload error for user {current_user.id}: {str(e)}')
    
    return render_template('main/upload.html', title='Upload Image', form=form)

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
        
        # Delete associated image file if it exists
        if case.image_path and os.path.exists(case.image_path):
            try:
                os.remove(case.image_path)
                current_app.logger.info(f'Deleted image file: {case.image_path}')
            except OSError as e:
                current_app.logger.warning(f'Could not delete image file {case.image_path}: {str(e)}')
        
        # Delete the case (reports will be deleted automatically due to cascade)
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