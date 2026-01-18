"""
Tests for structured findings integration with case creation.

These tests verify that structured findings can be optionally added during
case creation and are properly stored and retrieved.
"""

import pytest
from io import BytesIO
from PIL import Image
from unittest.mock import patch, Mock
from app.models import Case, Patient, User, StructuredFindings
from app import db


class TestStructuredFindingsIntegration:
    """Tests for structured findings integration with case creation."""
    
    def create_test_image(self, format='JPEG', size=(100, 100)):
        """Create a test image file in memory."""
        img = Image.new('RGB', size, color='red')
        img_io = BytesIO()
        img.save(img_io, format=format)
        img_io.seek(0)
        return img_io
    
    @pytest.fixture
    def test_patient(self, app):
        """Create a test patient."""
        with app.app_context():
            # Get the user within the app context
            user = User.query.filter_by(username='testuser').first()
            patient = Patient(
                patient_id='FIND001',
                first_name='Findings',
                last_name='Test',
                created_by=user.id
            )
            db.session.add(patient)
            db.session.commit()
            yield patient
    
    @pytest.fixture
    def mock_pipeline(self):
        """Mock the multi-agent pipeline."""
        with patch('app.main.run_multi_agent_pipeline') as mock:
            mock.return_value = {
                'success': True,
                'report_id': 1,
                'errors': [],
                'execution_log': []
            }
            yield mock
    
    def test_case_creation_without_findings(self, client, auth, app, user, test_patient, mock_pipeline):
        """Test that case creation works without any findings (all optional)."""
        auth.login()
        
        # Create a test image
        test_image = self.create_test_image()
        
        # Submit case without findings
        response = client.post('/cases/new', data={
            'patient_id': test_patient.id,
            'study_type': 'Ultrasound',
            'body_part': 'Abdomen',
            'indication': 'Abdominal pain evaluation',
            'clinical_history': 'Patient presents with RUQ pain',
            'priority': 'routine',
            'image1': (test_image, 'test.jpg')
        }, follow_redirects=True, content_type='multipart/form-data')
        
        # Verify case was created
        assert response.status_code == 200
        
        with app.app_context():
            # Query by username instead of user.id
            user_in_context = User.query.filter_by(username='testuser').first()
            case = Case.query.filter_by(user_id=user_in_context.id).first()
            assert case is not None
            
            # Verify no findings were created
            findings = StructuredFindings.query.filter_by(case_id=case.id).first()
            assert findings is None
    
    def test_case_creation_with_partial_findings(self, client, auth, app, user, test_patient, mock_pipeline):
        """Test that case creation works with partial findings filled in."""
        auth.login()
        
        # Create a test image
        test_image = self.create_test_image()
        
        # Submit case with partial findings
        response = client.post('/cases/new', data={
            'patient_id': test_patient.id,
            'study_type': 'Ultrasound',
            'body_part': 'Abdomen',
            'indication': 'Liver assessment',
            'clinical_history': 'Elevated liver enzymes',
            'priority': 'routine',
            'image1': (test_image, 'test.jpg'),
            # Partial findings
            'liver_size': 'Enlarged',
            'liver_texture': 'Fatty',
            'spleen_size': 'Normal',
            'gb_calculus': 'Absent'
        }, follow_redirects=True, content_type='multipart/form-data')
        
        # Verify case was created
        assert response.status_code == 200
        
        with app.app_context():
            user_in_context = User.query.filter_by(username='testuser').first()
            case = Case.query.filter_by(user_id=user_in_context.id).first()
            assert case is not None
            
            # Verify findings were created and stored correctly
            findings = StructuredFindings.query.filter_by(case_id=case.id).first()
            assert findings is not None
            assert findings.liver_size == 'Enlarged'
            assert findings.liver_texture == 'Fatty'
            assert findings.spleen_size == 'Normal'
            assert findings.gb_calculus == 'Absent'
            # Verify unfilled fields are None
            assert findings.liver_focal_defect is None
            assert findings.pancreas_findings is None
    
    def test_case_creation_with_all_findings(self, client, auth, app, user, test_patient, mock_pipeline):
        """Test that case creation works with all findings filled in."""
        auth.login()
        
        # Create a test image
        test_image = self.create_test_image()
        
        # Submit case with all findings
        response = client.post('/cases/new', data={
            'patient_id': test_patient.id,
            'study_type': 'Ultrasound',
            'body_part': 'Abdomen',
            'indication': 'Complete abdominal ultrasound',
            'clinical_history': 'Comprehensive evaluation',
            'priority': 'routine',
            'image1': (test_image, 'test.jpg'),
            # All findings
            'liver_size': 'Normal',
            'liver_texture': 'Normal',
            'liver_focal_defect': 'Absent',
            'liver_cbd': 'Normal',
            'liver_pv': 'Normal',
            'spleen_size': 'Normal',
            'spleen_focal_defect': 'Absent',
            'gb_calculus': 'Absent',
            'gb_wall_edema': 'Absent',
            'right_kidney_size': 'Normal',
            'right_kidney_texture': 'Normal',
            'right_kidney_other': 'No stones or cysts',
            'left_kidney_size': 'Normal',
            'left_kidney_texture': 'Normal',
            'left_kidney_other': 'No stones or cysts',
            'pancreas_findings': 'Normal appearance',
            'bladder_filling': 'Full',
            'bladder_stone_mass': 'Absent',
            'bladder_mucosal_irregularity': 'Absent',
            'prostate_findings': 'Normal size',
            'ascites': 'Absent',
            'pleural_effusions': 'Absent',
            'para_aortic_lymph_nodes': 'Absent',
            'other_findings': 'No additional findings',
            'comments': 'Complete normal study'
        }, follow_redirects=True, content_type='multipart/form-data')
        
        # Verify case was created
        assert response.status_code == 200
        
        with app.app_context():
            user_in_context = User.query.filter_by(username='testuser').first()
            case = Case.query.filter_by(user_id=user_in_context.id).first()
            assert case is not None
            
            # Verify all findings were stored correctly
            findings = StructuredFindings.query.filter_by(case_id=case.id).first()
            assert findings is not None
            assert findings.liver_size == 'Normal'
            assert findings.liver_texture == 'Normal'
            assert findings.liver_focal_defect == 'Absent'
            assert findings.liver_cbd == 'Normal'
            assert findings.liver_pv == 'Normal'
            assert findings.spleen_size == 'Normal'
            assert findings.spleen_focal_defect == 'Absent'
            assert findings.gb_calculus == 'Absent'
            assert findings.gb_wall_edema == 'Absent'
            assert findings.right_kidney_size == 'Normal'
            assert findings.right_kidney_texture == 'Normal'
            assert findings.right_kidney_other == 'No stones or cysts'
            assert findings.left_kidney_size == 'Normal'
            assert findings.left_kidney_texture == 'Normal'
            assert findings.left_kidney_other == 'No stones or cysts'
            assert findings.pancreas_findings == 'Normal appearance'
            assert findings.bladder_filling == 'Full'
            assert findings.bladder_stone_mass == 'Absent'
            assert findings.bladder_mucosal_irregularity == 'Absent'
            assert findings.prostate_findings == 'Normal size'
            assert findings.ascites == 'Absent'
            assert findings.pleural_effusions == 'Absent'
            assert findings.para_aortic_lymph_nodes == 'Absent'
            assert findings.other_findings == 'No additional findings'
            assert findings.comments == 'Complete normal study'
    
    def test_findings_form_validation(self, client, auth, app, user, test_patient, mock_pipeline):
        """Test that findings form validates correctly with optional fields."""
        auth.login()
        
        # Create a test image
        test_image = self.create_test_image()
        
        # Submit case with empty string values (should be treated as None)
        response = client.post('/cases/new', data={
            'patient_id': test_patient.id,
            'study_type': 'Ultrasound',
            'body_part': 'Abdomen',
            'indication': 'Test validation',
            'clinical_history': 'Test',
            'priority': 'routine',
            'image1': (test_image, 'test.jpg'),
            'liver_size': '',  # Empty string
            'liver_texture': 'Normal',  # Valid value
            'comments': ''  # Empty string
        }, follow_redirects=True, content_type='multipart/form-data')
        
        # Verify case was created
        assert response.status_code == 200
        
        with app.app_context():
            user_in_context = User.query.filter_by(username='testuser').first()
            case = Case.query.filter_by(user_id=user_in_context.id).first()
            assert case is not None
            
            # Verify findings were created with proper None handling
            findings = StructuredFindings.query.filter_by(case_id=case.id).first()
            assert findings is not None
            assert findings.liver_size is None  # Empty string should be None
            assert findings.liver_texture == 'Normal'
            assert findings.comments is None  # Empty string should be None
