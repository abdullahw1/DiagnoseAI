from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    title = db.Column(db.String(20))  # Dr., MD, etc.
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cases = db.relationship('Case', backref='user', lazy=True, cascade='all, delete-orphan')
    patients = db.relationship('Patient', backref='created_by_user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password using bcrypt."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches the hash using bcrypt."""
        password_bytes = password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    
    @property
    def full_name(self):
        """Return the user's full name with title."""
        name_parts = []
        if self.title:
            name_parts.append(self.title)
        if self.first_name:
            name_parts.append(self.first_name)
        if self.last_name:
            name_parts.append(self.last_name)
        return ' '.join(name_parts) if name_parts else self.username
    
    def __repr__(self):
        return f'<User {self.username}>'

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Hospital patient ID
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    medical_record_number = db.Column(db.String(20))
    insurance_info = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cases = db.relationship('Case', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    def __repr__(self):
        return f'<Patient {self.patient_id}: {self.full_name}>'

class Case(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True, nullable=False, index=True)  # Hospital case number
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    study_type = db.Column(db.String(100), default='Ultrasound')
    body_part = db.Column(db.String(100))
    indication = db.Column(db.Text)  # Reason for study
    clinical_history = db.Column(db.Text)
    referring_physician = db.Column(db.String(100))
    priority = db.Column(db.String(20), default='routine')  # routine, urgent, stat
    # Keep legacy fields for backward compatibility, but make them nullable
    image_filename = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), default='pending', nullable=False)
    study_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reports = db.relationship('Report', backref='case', lazy=True, cascade='all, delete-orphan')
    images = db.relationship('CaseImage', backref='case', lazy=True, cascade='all, delete-orphan', order_by='CaseImage.order_index')
    
    @property
    def formatted_case_number(self):
        return f"RAD-{self.case_number}"
    
    @property
    def primary_image(self):
        """Get the first/primary image for the case."""
        if self.images:
            return self.images[0]
        return None
    
    @property
    def all_image_paths(self):
        """Get all image paths for this case."""
        return [img.image_path for img in self.images]
    
    def __repr__(self):
        return f'<Case {self.case_number}: {self.patient.full_name if self.patient else "Unknown"}>'

class CaseImage(db.Model):
    __tablename__ = 'case_images'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    order_index = db.Column(db.Integer, default=0, nullable=False)  # For ordering images
    description = db.Column(db.String(255))  # Optional description for each image
    file_size = db.Column(db.Integer)  # File size in bytes
    mime_type = db.Column(db.String(50))  # image/jpeg, image/png, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CaseImage {self.filename} for Case {self.case_id}>'

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    draft_json = db.Column(db.JSON)
    draft_text = db.Column(db.Text)
    final_text = db.Column(db.Text)
    is_finalized = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Report {self.id} for Case {self.case_id}>'


class AITestResult(db.Model):
    __tablename__ = 'ai_test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    saved_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)
    view_type = db.Column(db.String(100))
    image_context = db.Column(db.Text)
    expected_pathology = db.Column(db.String(255))
    ai_analysis = db.Column(db.Text, nullable=False)
    raw_response = db.Column(db.JSON)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(50))
    
    # Evaluation fields (optional, filled when user evaluates)
    accuracy_rating = db.Column(db.Integer)  # 1-5 stars
    completeness_rating = db.Column(db.Integer)  # 1-5 stars
    terminology_rating = db.Column(db.Integer)  # 1-5 stars
    overall_rating = db.Column(db.Integer)  # 1-5 stars
    ai_identified_pathology = db.Column(db.String(255))
    evaluation_comments = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ai_test_results', lazy=True)
    
    @property
    def average_rating(self):
        """Calculate average rating from all rating fields."""
        ratings = [r for r in [self.accuracy_rating, self.completeness_rating, 
                              self.terminology_rating, self.overall_rating] if r is not None]
        return sum(ratings) / len(ratings) if ratings else None
    
    @property
    def is_evaluated(self):
        """Check if this test result has been evaluated."""
        return any([self.accuracy_rating, self.completeness_rating, 
                   self.terminology_rating, self.overall_rating])
    
    def __repr__(self):
        return f'<AITestResult {self.id}: {self.original_filename}>'