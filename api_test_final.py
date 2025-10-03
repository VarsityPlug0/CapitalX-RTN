import requests
import json
import time

def test_api_endpoints():
    """
    Test the API endpoints for the financial information system
    """
    base_url = "http://127.0.0.1:8000"
    
    print("Testing API endpoints...")
    print("=" * 50)
    
    # Test 1: Simple test endpoint
    print("\n1. Testing simple test endpoint:")
    try:
        response = requests.get(f"{base_url}/api/simple-test/", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                print(f"   Response (non-JSON): {response.text}")
        else:
            print(f"   Error Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   Error: Could not connect to server")
    except requests.exceptions.Timeout:
        print("   Error: Request timed out")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Main test endpoint
    print("\n2. Testing main test endpoint:")
    try:
        response = requests.get(f"{base_url}/api/test/", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except json.JSONDecodeError:
                print(f"   Response (non-JSON): {response.text}")
        else:
            print(f"   Error Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   Error: Could not connect to server")
    except requests.exceptions.Timeout:
        print("   Error: Request timed out")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 50)
    print("API testing completed.")
    print("\nTo use the financial info API with your bot:")
    print("1. Register or log in to the application")
    print("2. Generate an API token at /api/generate-token/")
    print("3. Use the token in the Authorization header for subsequent requests")
    print("\nExample bot implementation:")
    print("""
import requests

API_TOKEN = "your_generated_token_here"
headers = {
    "Authorization": f"Token {{API_TOKEN}}",
    "Content-Type": "application/json"
}

# Get financial information
response = requests.get(
    "http://127.0.0.1:8000/api/user/financial-info/",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Wallet Balance: R{{data['wallet']['balance']}}")
    # Process other financial data as needed
""")

if __name__ == "__main__":
    test_api_endpoints()