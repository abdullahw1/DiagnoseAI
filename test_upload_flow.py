#!/usr/bin/env python3
"""
Test script to simulate the full upload flow
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_upload_flow():
    """Test the complete upload flow."""
    print("🧪 Testing DiagnoseAI Upload Flow")
    print("=" * 40)
    
    from app import create_app, db
    from app.models import User, Case, Report
    from app.ai_service import generate_draft_report
    
    app = create_app()
    
    with app.app_context():
        # 1. Check if we have a user
        user = User.query.filter_by(username='testuser').first()
        if not user:
            print("❌ No test user found")
            return False
        
        print(f"✅ Found test user: {user.username}")
        
        # 2. Check if we have a test image
        test_image_path = 'instance/uploads/1/20250919_161031_666562_img-sample-1.jpg'
        if not os.path.exists(test_image_path):
            print(f"❌ Test image not found: {test_image_path}")
            return False
        
        print(f"✅ Found test image: {test_image_path}")
        
        # 3. Create a test case
        print("🔄 Creating test case...")
        case = Case(
            user_id=user.id,
            image_filename='test_ultrasound.jpg',
            image_path=test_image_path,
            clinical_notes='Test clinical notes: Patient presents with abdominal pain.',
            status='uploaded'
        )
        
        db.session.add(case)
        db.session.commit()
        print(f"✅ Test case created: #{case.id}")
        
        # 4. Test AI report generation
        print("🔄 Testing AI report generation...")
        try:
            raw_response, formatted_text = generate_draft_report(
                image_path=test_image_path,
                clinical_notes=case.clinical_notes
            )
            
            print("✅ AI report generated successfully!")
            print(f"📝 Report preview: {formatted_text[:200]}...")
            
            # 5. Save the report
            report = Report(
                case_id=case.id,
                draft_json=raw_response,
                draft_text=formatted_text,
                is_finalized=False
            )
            
            case.status = 'draft_ready'
            db.session.add(report)
            db.session.commit()
            
            print("✅ Report saved to database!")
            
            # 6. Verify everything
            final_case_count = Case.query.count()
            final_report_count = Report.query.count()
            
            print(f"\n📊 Final counts:")
            print(f"   Cases: {final_case_count}")
            print(f"   Reports: {final_report_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ AI report generation failed: {e}")
            return False

if __name__ == '__main__':
    success = test_upload_flow()
    if success:
        print("\n🎉 Upload flow test completed successfully!")
    else:
        print("\n💥 Upload flow test failed!")
        sys.exit(1)