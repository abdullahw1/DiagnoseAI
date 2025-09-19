from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import TextAreaField, SubmitField
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