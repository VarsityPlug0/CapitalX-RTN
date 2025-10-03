import requests
import json

# Test the API endpoints
def test_api():
    try:
        # Test the simple API endpoint
        response = requests.get('http://127.0.0.1:8000/api/test/')
        print("Test API Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text}")
        print()
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Response Data: {data}")
            except json.JSONDecodeError:
                print("Response is not valid JSON")
        
        print()
        print("API endpoints are working correctly!")
        print("To use the financial info API, you'll need to:")
        print("1. Register or log in to the application")
        print("2. Generate an API token at http://127.0.0.1:8000/api/generate-token/")
        print("3. Use the token in the Authorization header for subsequent requests")
        print()
        print("Example for bot implementation:")
        print("""
import requests

API_TOKEN = "your_token_here"
headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

# Get financial information
response = requests.get(
    "http://127.0.0.1:8000/api/user/financial-info/",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Wallet Balance: R{data['wallet']['balance']}")
    # Process other financial data as needed
""")
        
    except requests.exceptions.ConnectionError:
        print("Could not connect to the server. Make sure the Django server is running.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_api()