from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, HiddenField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, Optional
from datetime import date

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


class PatientForm(FlaskForm):
    """Form for creating and editing patient information."""
    
    patient_id = StringField('Patient ID', validators=[
        DataRequired(message='Patient ID is required.'),
        Length(min=3, max=20, message='Patient ID must be between 3 and 20 characters.')
    ], render_kw={'placeholder': 'e.g., P001234'})
    
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required.'),
        Length(min=1, max=50, message='First name must be between 1 and 50 characters.')
    ])
    
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required.'),
        Length(min=1, max=50, message='Last name must be between 1 and 50 characters.')
    ])
    
    date_of_birth = DateField('Date of Birth', validators=[Optional()], 
                             default=None, render_kw={'max': date.today().isoformat()})
    
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('unknown', 'Unknown')
    ], validators=[Optional()])
    
    phone = StringField('Phone Number', validators=[
        Optional(),
        Length(max=20, message='Phone number must be less than 20 characters.')
    ], render_kw={'placeholder': '(555) 123-4567'})
    
    email = StringField('Email', validators=[
        Optional(),
        Email(message='Please enter a valid email address.'),
        Length(max=120, message='Email must be less than 120 characters.')
    ])
    
    address = TextAreaField('Address', validators=[Optional()], 
                           render_kw={'rows': 3, 'placeholder': 'Street address, city, state, zip'})
    
    emergency_contact = StringField('Emergency Contact', validators=[
        Optional(),
        Length(max=100, message='Emergency contact name must be less than 100 characters.')
    ])
    
    emergency_phone = StringField('Emergency Phone', validators=[
        Optional(),
        Length(max=20, message='Emergency phone must be less than 20 characters.')
    ])
    
    medical_record_number = StringField('Medical Record Number', validators=[
        Optional(),
        Length(max=20, message='MRN must be less than 20 characters.')
    ])
    
    insurance_info = TextAreaField('Insurance Information', validators=[Optional()], 
                                  render_kw={'rows': 2, 'placeholder': 'Insurance provider and policy details'})
    
    submit = SubmitField('Save Patient')


class CaseForm(FlaskForm):
    """Form for creating new radiology cases."""
    
    patient_id = SelectField('Patient', validators=[
        DataRequired(message='Please select a patient.')
    ], coerce=int)
    
    study_type = SelectField('Study Type', choices=[
        ('Ultrasound', 'Ultrasound'),
        ('X-Ray', 'X-Ray'),
        ('CT Scan', 'CT Scan'),
        ('MRI', 'MRI'),
        ('Mammography', 'Mammography'),
        ('Nuclear Medicine', 'Nuclear Medicine')
    ], default='Ultrasound', validators=[DataRequired()])
    
    body_part = StringField('Body Part/Region', validators=[
        Optional(),
        Length(max=100, message='Body part must be less than 100 characters.')
    ], render_kw={'placeholder': 'e.g., Abdomen, Pelvis, Chest'})
    
    indication = TextAreaField('Clinical Indication', validators=[
        DataRequired(message='Clinical indication is required.'),
        Length(min=10, max=500, message='Clinical indication must be between 10 and 500 characters.')
    ], render_kw={
        'placeholder': 'Reason for the study (e.g., abdominal pain, follow-up, screening)',
        'rows': 3
    })
    
    clinical_history = TextAreaField('Clinical History', validators=[
        Optional(),
        Length(max=1000, message='Clinical history must be less than 1000 characters.')
    ], render_kw={
        'placeholder': 'Relevant patient history, symptoms, previous studies...',
        'rows': 4
    })
    
    referring_physician = StringField('Referring Physician', validators=[
        Optional(),
        Length(max=100, message='Referring physician name must be less than 100 characters.')
    ], render_kw={'placeholder': 'Dr. Smith, Internal Medicine'})
    
    priority = SelectField('Priority', choices=[
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('stat', 'STAT')
    ], default='routine', validators=[DataRequired()])
    
    image = FileField('Medical Image', validators=[
        FileRequired(message='Please select an image file.'),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'dcm'], 
                   message='Only image files are allowed (jpg, jpeg, png, gif, bmp, tiff, dcm).')
    ])
    
    submit = SubmitField('Create Case')


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