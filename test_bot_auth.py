"""
Test script for bot authentication system
"""

import requests
import json

# Test the API endpoints
def test_api_endpoints():
    base_url = "http://127.0.0.1:8000"
    
    print("Testing bot authentication system...")
    
    # Test the simple test API endpoint
    try:
        response = requests.get(f"{base_url}/api/test/")
        print(f"Test API endpoint status: {response.status_code}")
        if response.status_code == 200:
            print(f"Test API response: {response.json()}")
    except Exception as e:
        print(f"Error testing API endpoint: {e}")
    
    # Test the financial info API (requires authentication)
    try:
        response = requests.get(f"{base_url}/api/user/financial-info/")
        print(f"User financial info API status: {response.status_code}")
        # This should return 403 or 401 since we're not authenticated
    except Exception as e:
        print(f"Error testing user financial info API: {e}")
    
    print("API endpoint tests completed.")

if __name__ == "__main__":
    test_api_endpoints()