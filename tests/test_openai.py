#!/usr/bin/env python3
"""
Test script to verify OpenAI API connectivity and functionality
"""
import os
import sys
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_connection():
    """Test basic OpenAI API connectivity."""
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...")
        
        client = OpenAI(api_key=api_key)
        
        # Test simple completion
        print("🔄 Testing basic API call...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Say 'API test successful' and nothing else."}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API Response: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def test_image_analysis():
    """Test image analysis functionality with a sample image."""
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        client = OpenAI(api_key=api_key)
        
        # Check if there's a sample image
        sample_image_path = None
        upload_dirs = ['instance/uploads', 'static/uploads']
        
        for upload_dir in upload_dirs:
            if os.path.exists(upload_dir):
                for root, dirs, files in os.walk(upload_dir):
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            sample_image_path = os.path.join(root, file)
                            break
                    if sample_image_path:
                        break
        
        if not sample_image_path:
            print("⚠️  No sample image found for testing")
            return True
        
        print(f"🔄 Testing image analysis with: {sample_image_path}")
        
        # Encode image
        with open(sample_image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Test image analysis
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe this image in one sentence."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ Image Analysis Response: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Image analysis test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 DiagnoseAI OpenAI API Test Suite")
    print("=" * 40)
    
    # Test 1: Basic connectivity
    print("\n1. Testing OpenAI API connectivity...")
    if not test_openai_connection():
        sys.exit(1)
    
    # Test 2: Image analysis
    print("\n2. Testing image analysis...")
    if not test_image_analysis():
        print("⚠️  Image analysis test failed, but this might be due to no sample images")
    
    print("\n✅ All tests completed!")
    print("\n💡 If the upload is still hanging, check:")
    print("   • Server logs for detailed error messages")
    print("   • Network connectivity to OpenAI API")
    print("   • Image file size and format")
    print("   • Database connectivity")

if __name__ == '__main__':
    main()