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
    role = db.Column(db.String(50), default='radiologist')  # radiologist, admin, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    cases = db.relationship('Case', backref='user', lazy=True, cascade='all, delete-orphan')
    patients = db.relationship('Patient', backref='created_by_user', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='user', lazy=True)
    prompt_versions = db.relationship('PromptVersion', backref='creator', lazy=True)
    
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
    patient_history = db.Column(db.Text)  # Additional patient history for multi-agent
    clinical_indication = db.Column(db.Text)  # Structured clinical indication
    lab_results = db.Column(db.Text)  # Lab results for context
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
    agent_outputs = db.relationship('AgentOutput', backref='case', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='case', lazy=True)
    
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
    confidence_score = db.Column(db.Float)  # AI confidence score
    safety_flags = db.Column(db.JSON)  # Safety validation flags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feedback = db.relationship('Feedback', backref='report', lazy=True)
    rag_cases = db.relationship('RAGCase', backref='report', lazy=True)
    
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


class AgentOutput(db.Model):
    """Stores intermediate results from each agent in the multi-agent pipeline."""
    __tablename__ = 'agent_outputs'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    agent_name = db.Column(db.String(50), nullable=False)  # agent_a_context, agent_b_quality, etc.
    input_data = db.Column(db.JSON)  # Input passed to the agent
    output_data = db.Column(db.JSON)  # Output produced by the agent
    execution_time_ms = db.Column(db.Integer)  # Execution time in milliseconds
    error_message = db.Column(db.Text)  # Error message if agent failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AgentOutput {self.agent_name} for Case {self.case_id}>'


class Feedback(db.Model):
    """Captures radiologist actions and modifications for continuous improvement."""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # 'approve', 'modify', 'reject'
    modifications = db.Column(db.JSON)  # Diff of changes made
    rejection_reason = db.Column(db.Text)  # Reason for rejection
    confidence_level = db.Column(db.Integer)  # 1-5 scale for approval confidence
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.action} for Report {self.report_id}>'


class Metric(db.Model):
    """Stores calculated performance metrics for the AI system."""
    __tablename__ = 'metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)  # acceptance_rate, edit_rate, etc.
    metric_value = db.Column(db.Float, nullable=False)
    metric_category = db.Column(db.String(50))  # 'overall', 'finding_type', 'pathology'
    time_period = db.Column(db.String(20))  # 'daily', 'weekly', 'monthly'
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Metric {self.metric_name}: {self.metric_value}>'


class PromptVersion(db.Model):
    """Tracks prompt changes for continuous improvement with rollback capability."""
    __tablename__ = 'prompt_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_name = db.Column(db.String(50), nullable=False)  # Which agent this prompt is for
    version = db.Column(db.Integer, nullable=False)  # Version number
    prompt_template = db.Column(db.Text, nullable=False)  # The actual prompt text
    change_description = db.Column(db.Text)  # Description of what changed
    is_active = db.Column(db.Boolean, default=False)  # Currently active version
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PromptVersion {self.agent_name} v{self.version}>'


class RAGCase(db.Model):
    """Stores approved cases for RAG-based retrieval in the multi-agent pipeline."""
    __tablename__ = 'rag_cases'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False)
    embedding = db.Column(db.LargeBinary)  # Vector embedding for similarity search
    pathology_tags = db.Column(db.JSON)  # Array of pathology tags for filtering
    quality_score = db.Column(db.Float)  # Quality score for this case
    is_exemplar = db.Column(db.Boolean, default=False)  # Marked as exemplar case
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    case = db.relationship('Case', backref='rag_cases', lazy=True)
    
    def __repr__(self):
        return f'<RAGCase {self.id} for Case {self.case_id}>'


class StructuredFindings(db.Model):
    """User-provided structured findings during case creation."""
    __tablename__ = 'structured_findings'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False, unique=True)
    
    # Liver findings
    liver_size = db.Column(db.String(20))  # Normal, Enlarged, Shrunken
    liver_texture = db.Column(db.String(20))  # Normal, Fatty, Coarse
    liver_focal_defect = db.Column(db.String(20))  # Absent, Present
    liver_cbd = db.Column(db.String(20))  # Normal, Dilated
    liver_pv = db.Column(db.String(20))  # Normal, Dilated
    
    # Spleen findings
    spleen_size = db.Column(db.String(20))  # Normal, Enlarged
    spleen_focal_defect = db.Column(db.String(20))  # Absent, Present
    
    # Gall Bladder findings
    gb_calculus = db.Column(db.String(20))  # Absent, Present
    gb_wall_edema = db.Column(db.String(20))  # Absent, Present
    
    # Right Kidney findings
    right_kidney_size = db.Column(db.String(20))  # Normal, Shrunken
    right_kidney_texture = db.Column(db.String(20))  # Normal, Echogenic
    right_kidney_other = db.Column(db.String(200))  # Stone/Cyst/Hydronephrosis
    
    # Left Kidney findings
    left_kidney_size = db.Column(db.String(20))  # Normal, Shrunken
    left_kidney_texture = db.Column(db.String(20))  # Normal, Echogenic
    left_kidney_other = db.Column(db.String(200))  # Stone/Cyst/Hydronephrosis
    
    # Pancreas findings
    pancreas_findings = db.Column(db.Text)  # Free text
    
    # Urinary Bladder findings
    bladder_filling = db.Column(db.String(20))  # Full, Partially filled, Empty
    bladder_stone_mass = db.Column(db.String(20))  # Absent, Present
    bladder_mucosal_irregularity = db.Column(db.String(20))  # Absent, Present
    
    # Prostate findings
    prostate_findings = db.Column(db.Text)  # Free text
    
    # Additional findings
    ascites = db.Column(db.String(20))  # Absent, Present
    pleural_effusions = db.Column(db.String(20))  # Absent, Present
    para_aortic_lymph_nodes = db.Column(db.String(20))  # Absent, Present
    other_findings = db.Column(db.String(200))  # Short text
    
    # Comments
    comments = db.Column(db.Text)  # Free text
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    case = db.relationship('Case', backref=db.backref('structured_findings', uselist=False))
    
    def __repr__(self):
        return f'<StructuredFindings for Case {self.case_id}>'


class AIGeneratedFindings(db.Model):
    """AI-generated structured findings from image analysis."""
    __tablename__ = 'ai_generated_findings'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    ai_test_result_id = db.Column(db.Integer, db.ForeignKey('ai_test_results.id'), nullable=True)
    
    # Same structure as StructuredFindings
    liver_size = db.Column(db.String(20))
    liver_texture = db.Column(db.String(20))
    liver_focal_defect = db.Column(db.String(20))
    liver_cbd = db.Column(db.String(20))
    liver_pv = db.Column(db.String(20))
    
    spleen_size = db.Column(db.String(20))
    spleen_focal_defect = db.Column(db.String(20))
    
    gb_calculus = db.Column(db.String(20))
    gb_wall_edema = db.Column(db.String(20))
    
    right_kidney_size = db.Column(db.String(20))
    right_kidney_texture = db.Column(db.String(20))
    right_kidney_other = db.Column(db.String(200))
    
    left_kidney_size = db.Column(db.String(20))
    left_kidney_texture = db.Column(db.String(20))
    left_kidney_other = db.Column(db.String(200))
    
    pancreas_findings = db.Column(db.Text)
    
    bladder_filling = db.Column(db.String(20))
    bladder_stone_mass = db.Column(db.String(20))
    bladder_mucosal_irregularity = db.Column(db.String(20))
    
    prostate_findings = db.Column(db.Text)
    
    ascites = db.Column(db.String(20))
    pleural_effusions = db.Column(db.String(20))
    para_aortic_lymph_nodes = db.Column(db.String(20))
    other_findings = db.Column(db.String(200))
    
    comments = db.Column(db.Text)
    
    confidence_scores = db.Column(db.JSON)  # Confidence per field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    case = db.relationship('Case', backref='ai_findings')
    ai_test_result = db.relationship('AITestResult', backref='ai_findings')
    
    def __repr__(self):
        return f'<AIGeneratedFindings for Case {self.case_id}>'


class FindingsEvaluation(db.Model):
    """Radiologist evaluation of AI-generated findings."""
    __tablename__ = 'findings_evaluations'
    
    id = db.Column(db.Integer, primary_key=True)
    ai_finding_id = db.Column(db.Integer, db.ForeignKey('ai_generated_findings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Field-by-field correctness (JSON structure)
    # Example: {"liver_size": true, "liver_texture": false, ...}
    field_correctness = db.Column(db.JSON, nullable=False)
    
    # Overall metrics
    total_fields = db.Column(db.Integer)
    correct_fields = db.Column(db.Integer)
    accuracy_percentage = db.Column(db.Float)
    
    # Comments
    evaluation_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ai_finding = db.relationship('AIGeneratedFindings', backref='evaluations')
    user = db.relationship('User', backref='findings_evaluations')
    
    def __repr__(self):
        return f'<FindingsEvaluation {self.id} for AIFinding {self.ai_finding_id}>'
