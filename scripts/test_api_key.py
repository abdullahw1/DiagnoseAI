#!/usr/bin/env python3
"""
Test script to verify OpenAI API key is working
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_key():
    """Test if the OpenAI API key is valid."""
    api_key = os.getenv('OPENAI_API_KEY')
    
    print("🔑 OpenAI API Key Test")
    print("=" * 30)
    
    if not api_key:
        print("❌ No API key found in environment")
        return False
    
    if api_key == 'your-openai-api-key-here':
        print("❌ API key is still the placeholder value")
        return False
    
    # Mask the key for display
    masked_key = api_key[:10] + '*' * (len(api_key) - 20) + api_key[-10:] if len(api_key) > 20 else '*' * len(api_key)
    print(f"✅ API key found: {masked_key}")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Starts with 'sk-': {api_key.startswith('sk-')}")
    
    # Test the API key with a simple request
    try:
        from openai import OpenAI
        
        print("\n🧪 Testing API key with OpenAI...")
        client = OpenAI(api_key=api_key)
        
        # Make a simple request to test the key
        response = client.models.list()
        
        print("✅ API key is valid!")
        print(f"   Available models: {len(response.data)} models found")
        return True
        
    except Exception as e:
        print(f"❌ API key test failed: {str(e)}")
        
        # Check for specific error types
        if "401" in str(e) or "Incorrect API key" in str(e):
            print("   → The API key is invalid or expired")
            print("   → Get a new key from https://platform.openai.com/api-keys")
        elif "quota" in str(e).lower():
            print("   → You've exceeded your API quota")
            print("   → Check your OpenAI billing at https://platform.openai.com/account/billing")
        else:
            print("   → Unknown error, check your internet connection")
        
        return False

if __name__ == '__main__':
    success = test_openai_key()
    
    if success:
        print("\n🎉 Your OpenAI API key is working correctly!")
        print("   The DiagnoseAI app should be able to generate AI reports.")
    else:
        print("\n🔧 To fix this:")
        print("1. Get a valid OpenAI API key from https://platform.openai.com/api-keys")
        print("2. Update the OPENAI_API_KEY in your .env file")
        print("3. Make sure you have billing set up in your OpenAI account")
        print("4. Run this test again to verify")