#!/usr/bin/env python3
"""
Debug script to check environment variable loading
"""
import os
from dotenv import load_dotenv

print("🔍 Environment Variable Debug")
print("=" * 40)

# Check current working directory
print(f"Current directory: {os.getcwd()}")

# Check if .env file exists
env_file = ".env"
if os.path.exists(env_file):
    print(f"✅ .env file exists: {os.path.abspath(env_file)}")
    
    # Read .env file content
    with open(env_file, 'r') as f:
        content = f.read()
    
    print("\n📄 .env file content:")
    print("-" * 20)
    for line_num, line in enumerate(content.split('\n'), 1):
        if 'OPENAI_API_KEY' in line:
            # Mask the API key for security
            if '=' in line:
                key, value = line.split('=', 1)
                masked_value = value[:10] + '*' * (len(value) - 20) + value[-10:] if len(value) > 20 else '*' * len(value)
                print(f"{line_num:2d}: {key}={masked_value}")
            else:
                print(f"{line_num:2d}: {line}")
        else:
            print(f"{line_num:2d}: {line}")
else:
    print("❌ .env file not found")

print("\n🔧 Before loading .env:")
openai_key_before = os.getenv('OPENAI_API_KEY')
print(f"OPENAI_API_KEY = {openai_key_before}")

# Load environment variables
print("\n📥 Loading .env file...")
load_dotenv()

print("\n🔧 After loading .env:")
openai_key_after = os.getenv('OPENAI_API_KEY')
if openai_key_after:
    # Mask the API key for security
    masked_key = openai_key_after[:10] + '*' * (len(openai_key_after) - 20) + openai_key_after[-10:] if len(openai_key_after) > 20 else '*' * len(openai_key_after)
    print(f"OPENAI_API_KEY = {masked_key}")
    print(f"Key length: {len(openai_key_after)} characters")
    print(f"Starts with 'sk-': {openai_key_after.startswith('sk-')}")
else:
    print("OPENAI_API_KEY = None")

# Check other environment variables
print(f"FLASK_APP = {os.getenv('FLASK_APP')}")
print(f"FLASK_ENV = {os.getenv('FLASK_ENV')}")
print(f"DATABASE_URL = {os.getenv('DATABASE_URL', 'Not set')[:50]}...")

# Test if the API key is valid format
if openai_key_after:
    if openai_key_after.startswith('sk-'):
        if len(openai_key_after) > 40:
            print("✅ API key format looks correct")
        else:
            print("⚠️  API key seems too short")
    else:
        print("❌ API key doesn't start with 'sk-'")
        if 'your-openai-api-key-here' in openai_key_after:
            print("❌ API key is still the placeholder value!")
else:
    print("❌ No API key found")

print("\n💡 Recommendations:")
if not openai_key_after or 'your-openai-api-key-here' in str(openai_key_after):
    print("- Get a real OpenAI API key from https://platform.openai.com/api-keys")
    print("- Replace the placeholder in .env file")
elif not openai_key_after.startswith('sk-'):
    print("- Check that your API key is correct")
    print("- OpenAI API keys should start with 'sk-'")
else:
    print("- API key looks good!")
    print("- If you're still getting errors, the key might be invalid or expired")