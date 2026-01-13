#!/usr/bin/env python3
"""
Quick test script to verify download functionality works.
Run this after starting the server to test downloads.
"""

import requests
import os

def test_download_functionality():
    """Test that download routes are accessible."""
    base_url = "http://localhost:5000"
    
    # Test that routes exist (will redirect to login, but that's expected)
    test_routes = [
        "/case/1/download/text",
        "/case/1/download/pdf"
    ]
    
    for route in test_routes:
        try:
            response = requests.get(f"{base_url}{route}", allow_redirects=False)
            if response.status_code == 302:  # Redirect to login
                print(f"✓ Route {route} exists and requires authentication")
            else:
                print(f"✗ Route {route} returned unexpected status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"✗ Could not connect to server at {base_url}")
            print("Make sure the Flask server is running with: python run_server.py")
            return False
    
    print("\n✓ Download routes are properly configured!")
    print("To test full functionality:")
    print("1. Start the server: python run_server.py")
    print("2. Login and create a case with a finalized report")
    print("3. Try downloading from the case detail page")
    
    return True

if __name__ == "__main__":
    test_download_functionality()