#!/usr/bin/env python3
"""
Test script to simulate form submission
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_form_submission():
    """Test form submission to the upload endpoint."""
    print("🧪 Testing Form Submission")
    print("=" * 30)
    
    # First, let's get the login page to get a session
    session = requests.Session()
    
    # Get login page
    login_url = "http://127.0.0.1:5003/auth/login"
    response = session.get(login_url)
    
    if response.status_code != 200:
        print(f"❌ Could not access login page: {response.status_code}")
        return False
    
    print("✅ Accessed login page")
    
    # Extract CSRF token from login form
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    if not csrf_token:
        print("❌ Could not find CSRF token")
        return False
    
    csrf_token_value = csrf_token.get('value')
    print(f"✅ Found CSRF token: {csrf_token_value[:10]}...")
    
    # Login with test user
    login_data = {
        'username': 'testuser',
        'password': 'password123',
        'csrf_token': csrf_token_value
    }
    
    response = session.post(login_url, data=login_data)
    
    if response.status_code != 200 and response.status_code != 302:
        print(f"❌ Login failed: {response.status_code}")
        return False
    
    print("✅ Logged in successfully")
    
    # Now test the upload form
    upload_url = "http://127.0.0.1:5003/upload"
    response = session.get(upload_url)
    
    if response.status_code != 200:
        print(f"❌ Could not access upload page: {response.status_code}")
        return False
    
    print("✅ Accessed upload page")
    
    # Extract CSRF token from upload form
    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})
    
    if not csrf_token:
        print("❌ Could not find CSRF token in upload form")
        return False
    
    csrf_token_value = csrf_token.get('value')
    print(f"✅ Found upload CSRF token: {csrf_token_value[:10]}...")
    
    # Test image path
    test_image_path = 'instance/uploads/1/20250919_161031_666562_img-sample-1.jpg'
    
    if not os.path.exists(test_image_path):
        print(f"❌ Test image not found: {test_image_path}")
        return False
    
    print(f"✅ Found test image: {test_image_path}")
    
    # Submit upload form
    with open(test_image_path, 'rb') as f:
        files = {
            'image': ('test_ultrasound.jpg', f, 'image/jpeg')
        }
        
        data = {
            'clinical_notes': 'Test clinical notes for form submission test. Patient presents with abdominal pain and requires ultrasound examination.',
            'csrf_token': csrf_token_value
        }
        
        response = session.post(upload_url, data=data, files=files)
        
        print(f"📤 Form submission response: {response.status_code}")
        
        if response.status_code == 200:
            # Check if there are validation errors in the response
            if 'Please select an image file' in response.text or 'Clinical notes are required' in response.text:
                print("❌ Form validation failed")
                print("Response contains validation errors")
                return False
            else:
                print("✅ Form submitted successfully (no validation errors)")
                return True
        elif response.status_code == 302:
            print("✅ Form submitted successfully (redirected)")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False

if __name__ == '__main__':
    try:
        success = test_form_submission()
        if success:
            print("\n🎉 Form submission test passed!")
        else:
            print("\n💥 Form submission test failed!")
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()