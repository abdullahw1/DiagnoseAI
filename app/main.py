import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image
from app.models import Case, Report
from app.forms import UploadForm
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
                current_app.logger.info(f'Generating AI draft report for case {case.id}')
                raw_response, formatted_text = generate_draft_report(
                    image_path=file_path,
                    clinical_notes=case.clinical_notes or ""
                )
                
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
                flash(f'Case #{case.id} created successfully, but AI report generation failed. The case has been marked for manual review.', 'warning')
                
            except Exception as e:
                # Log unexpected errors
                current_app.logger.error(f'Unexpected error during AI report generation for case {case.id}: {str(e)}')
                case.status = 'ai_failed'
                db.session.commit()
                flash(f'Case #{case.id} created successfully, but AI report generation encountered an error. The case has been marked for manual review.', 'warning')
            
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