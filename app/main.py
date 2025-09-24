import os
from datetime import datetime
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
from app.models import Case, Report
from app.forms import UploadForm, ReportEditForm
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
    # Get user's cases for display
    cases = Case.query.filter_by(user_id=current_user.id).order_by(Case.created_at.desc()).all()
    return render_template('main/dashboard.html', title='Dashboard', cases=cases)

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
            
            # Create new case record
            case = Case(
                user_id=current_user.id,
                image_filename=filename,
                image_path=file_path,
                clinical_notes=form.clinical_notes.data.strip(),
                status='uploaded'
            )
            
            # Save to database
            db.session.add(case)
            db.session.commit()
            
            # Generate AI draft report automatically
            try:
                current_app.logger.info(f'Starting AI draft report generation for case {case.id}')
                current_app.logger.info(f'Image path: {file_path}')
                current_app.logger.info(f'Clinical notes length: {len(case.clinical_notes or "")} characters')
                
                raw_response, formatted_text = generate_draft_report(
                    image_path=file_path,
                    clinical_notes=case.clinical_notes or ""
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
                
                flash(f'Case #{case.id} created successfully! AI draft report has been generated and is ready for review.', 'success')
                current_app.logger.info(f'AI draft report generated successfully for case {case.id}')
                
            except AIServiceError as e:
                # Log the error but don't fail the case creation
                current_app.logger.error(f'AI service error for case {case.id}: {str(e)}')
                case.status = 'ai_failed'
                db.session.commit()
                flash(f'Case #{case.id} created successfully, but AI report generation failed: {str(e)}. The case has been marked for manual review.', 'warning')
                
            except Exception as e:
                # Log unexpected errors
                current_app.logger.error(f'Unexpected error during AI report generation for case {case.id}: {str(e)}', exc_info=True)
                case.status = 'ai_failed'
                db.session.commit()
                flash(f'Case #{case.id} created successfully, but AI report generation encountered an error: {str(e)}. The case has been marked for manual review.', 'warning')
            
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

CLINICAL NOTES:
{case.clinical_notes or 'No clinical notes provided.'}

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
        
        # Clinical notes
        story.append(Paragraph("CLINICAL NOTES", heading_style))
        clinical_notes = case.clinical_notes or 'No clinical notes provided.'
        story.append(Paragraph(clinical_notes, styles['Normal']))
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