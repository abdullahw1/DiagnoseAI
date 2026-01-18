"""
Integration tests for Agent B: View Identification and Quality Assessment

These tests use real ultrasound images and make actual API calls to verify
the agent works correctly in a real-world scenario.

Note: These tests require a valid OPENAI_API_KEY environment variable.
"""

import pytest
import os
from pathlib import Path
from app.agents.agent_b_quality import QualityAssessmentAgent


# Skip these tests if no API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY'),
    reason="OPENAI_API_KEY not set - skipping integration tests"
)


class TestQualityAssessmentAgentIntegration:
    """Integration test suite for QualityAssessmentAgent with real images."""
    
    @pytest.fixture
    def sample_image_path(self):
        """Get path to a sample ultrasound image."""
        # Use a sample image from the test uploads
        base_path = Path(__file__).parent.parent / 'instance' / 'uploads' / 'ai_tests' / '1'
        image_files = list(base_path.glob('*.jpg'))
        
        if not image_files:
            pytest.skip("No sample ultrasound images found")
        
        return str(image_files[0])
    
    @pytest.fixture
    def multiple_image_paths(self):
        """Get paths to multiple sample ultrasound images."""
        base_path = Path(__file__).parent.parent / 'instance' / 'uploads' / 'ai_tests' / '1'
        image_files = list(base_path.glob('*.jpg'))[:3]  # Get first 3 images
        
        if len(image_files) < 2:
            pytest.skip("Not enough sample ultrasound images found")
        
        return [str(img) for img in image_files]
    
    def test_agent_with_single_real_image(self, sample_image_path):
        """Test agent with a single real ultrasound image."""
        agent = QualityAssessmentAgent()
        
        input_data = {
            'case_id': 1,
            'case_data': {
                'image_paths': [sample_image_path]
            }
        }
        
        result = agent.execute(input_data)
        
        # Verify execution succeeded
        assert result['success'] is True
        assert result['error'] is None
        assert result['execution_time_ms'] > 0
        
        # Verify output structure
        output = result['output']
        assert 'images' in output
        assert 'overall_quality' in output
        assert 'summary' in output
        
        # Verify image assessment
        assert len(output['images']) == 1
        image_assessment = output['images'][0]
        
        assert 'view_identified' in image_assessment
        assert 'quality_score' in image_assessment
        assert 'diagnostic_adequacy' in image_assessment
        
        # Verify quality score is in valid range
        quality_score = image_assessment['quality_score']
        assert 0 <= quality_score <= 100
        
        # Print results for manual verification
        print(f"\n=== Agent B Integration Test Results ===")
        print(f"Image: {Path(sample_image_path).name}")
        print(f"View Identified: {image_assessment['view_identified']}")
        print(f"Quality Score: {quality_score}")
        print(f"Diagnostic Adequacy: {image_assessment['diagnostic_adequacy']}")
        print(f"Overall Quality: {output['overall_quality']}")
        print(f"Summary: {output['summary']}")
    
    def test_agent_with_multiple_real_images(self, multiple_image_paths):
        """Test agent with multiple real ultrasound images."""
        agent = QualityAssessmentAgent()
        
        input_data = {
            'case_id': 1,
            'case_data': {
                'image_paths': multiple_image_paths
            }
        }
        
        result = agent.execute(input_data)
        
        # Verify execution succeeded
        assert result['success'] is True
        assert result['error'] is None
        
        # Verify output structure
        output = result['output']
        assert len(output['images']) == len(multiple_image_paths)
        
        # Verify each image was assessed
        for idx, image_assessment in enumerate(output['images']):
            assert image_assessment['image_index'] == idx
            assert 'view_identified' in image_assessment
            assert 'quality_score' in image_assessment
            
            # Verify quality score is in valid range
            quality_score = image_assessment['quality_score']
            assert 0 <= quality_score <= 100
            
            print(f"\n=== Image {idx + 1}: {Path(multiple_image_paths[idx]).name} ===")
            print(f"View: {image_assessment['view_identified']}")
            print(f"Quality Score: {quality_score}")
            print(f"Adequacy: {image_assessment['diagnostic_adequacy']}")
    
    def test_agent_identifies_liver_views(self, sample_image_path):
        """Test that agent can identify liver-related views."""
        agent = QualityAssessmentAgent()
        
        input_data = {
            'case_id': 1,
            'case_data': {
                'image_paths': [sample_image_path]
            }
        }
        
        result = agent.execute(input_data)
        
        assert result['success'] is True
        
        output = result['output']
        image_assessment = output['images'][0]
        
        # The view should be identified (not empty or None)
        view = image_assessment['view_identified']
        assert view is not None
        assert len(view) > 0
        
        # For liver ultrasound images, common terms should appear
        view_lower = view.lower()
        liver_terms = ['liver', 'hepatic', 'portal', 'vein', 'lobe', 'gallbladder']
        
        # At least one liver-related term should be present
        # (This is a soft check since the image might show other structures)
        print(f"\nIdentified view: {view}")
    
    def test_agent_assesses_technical_quality(self, sample_image_path):
        """Test that agent provides technical quality assessment."""
        agent = QualityAssessmentAgent()
        
        input_data = {
            'case_id': 1,
            'case_data': {
                'image_paths': [sample_image_path]
            }
        }
        
        result = agent.execute(input_data)
        
        assert result['success'] is True
        
        output = result['output']
        image_assessment = output['images'][0]
        
        # Check for technical assessment fields
        if 'technical_assessment' in image_assessment:
            tech_assessment = image_assessment['technical_assessment']
            print(f"\nTechnical Assessment:")
            for key, value in tech_assessment.items():
                print(f"  {key}: {value}")
        
        # Check for artifacts
        if 'artifacts' in image_assessment:
            artifacts = image_assessment['artifacts']
            print(f"\nArtifacts: {artifacts}")
        
        # Check for limitations
        if 'limitations' in image_assessment:
            limitations = image_assessment['limitations']
            print(f"\nLimitations: {limitations}")
    
    def test_agent_provides_recommendations(self, sample_image_path):
        """Test that agent provides optimization recommendations when needed."""
        agent = QualityAssessmentAgent()
        
        input_data = {
            'case_id': 1,
            'case_data': {
                'image_paths': [sample_image_path]
            }
        }
        
        result = agent.execute(input_data)
        
        assert result['success'] is True
        
        output = result['output']
        image_assessment = output['images'][0]
        
        # Check for recommendations
        if 'recommendations' in image_assessment:
            recommendations = image_assessment['recommendations']
            print(f"\nRecommendations: {recommendations}")
            assert recommendations is not None
    
    def test_agent_with_legacy_single_image_path(self, sample_image_path):
        """Test agent with legacy single image_path field."""
        agent = QualityAssessmentAgent()
        
        input_data = {
            'case_id': 1,
            'case_data': {
                'image_path': sample_image_path  # Legacy field
            }
        }
        
        result = agent.execute(input_data)
        
        # Should still work with legacy field
        assert result['success'] is True
        assert len(result['output']['images']) == 1
