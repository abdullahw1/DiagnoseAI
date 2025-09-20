from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length

class UploadForm(FlaskForm):
    """Form for uploading ultrasound images with clinical notes."""
    
    image = FileField('Ultrasound Image', validators=[
        FileRequired(message='Please select an image file.'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'], 
                   message='Only image files are allowed (jpg, jpeg, png, gif, bmp, tiff).')
    ])
    
    clinical_notes = TextAreaField('Clinical Notes', validators=[
        DataRequired(message='Clinical notes are required.'),
        Length(min=10, max=2000, message='Clinical notes must be between 10 and 2000 characters.')
    ], render_kw={
        'placeholder': 'Enter clinical notes, patient history, symptoms, or other relevant information...',
        'rows': 6
    })
    
    submit = SubmitField('Upload and Create Case')


class ReportEditForm(FlaskForm):
    """Form for editing and finalizing AI-generated draft reports."""
    
    report_text = TextAreaField('Report Content', validators=[
        DataRequired(message='Report content is required.'),
        Length(min=50, max=5000, message='Report content must be between 50 and 5000 characters.')
    ], render_kw={
        'placeholder': 'Edit the AI-generated draft report...',
        'rows': 15,
        'class': 'form-control'
    })
    
    case_id = HiddenField()
    
    save_draft = SubmitField('Save Draft', render_kw={'class': 'btn btn-secondary me-2'})
    finalize_report = SubmitField('Finalize Report', render_kw={'class': 'btn btn-success'})