"""
Script to get API token by logging in to the CapitalX application
"""

import requests
from bs4 import BeautifulSoup

def get_api_token(email, password, base_url="http://127.0.0.1:8000"):
    """
    Log in to the application and retrieve an API token
    """
    # Create a session to maintain cookies
    session = requests.Session()
    
    try:
        # Step 1: Get the login page to retrieve CSRF token
        print("Getting login page...")
        login_page_url = f"{base_url}/login/"
        response = session.get(login_page_url)
        
        if response.status_code != 200:
            print(f"Failed to get login page: {response.status_code}")
            return None
        
        # Parse the HTML to extract CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        
        if not csrf_token_input:
            print("Failed to find CSRF token")
            return None
        
        csrf_token = csrf_token_input.get('value', '') if hasattr(csrf_token_input, 'get') else ''
        print(f"CSRF Token: {csrf_token}")
        
        # Step 2: Perform login
        print("Logging in...")
        login_data = {
            'csrfmiddlewaretoken': csrf_token,
            'email': email,
            'password': password
        }
        
        # Include referer header
        headers = {
            'Referer': login_page_url
        }
        
        response = session.post(login_page_url, data=login_data, headers=headers)
        
        # Check if login was successful
        if response.status_code == 200 or response.status_code == 302:
            print("Login successful!")
        else:
            print(f"Login failed: {response.status_code}")
            print(f"Response URL: {response.url}")
            return None
        
        # Step 3: Get API token
        print("Getting API token...")
        token_url = f"{base_url}/api/generate-token/"
        response = session.get(token_url)
        
        if response.status_code == 200:
            try:
                data = response.json()
                api_token = data.get('token')
                print(f"API Token: {api_token}")
                return api_token
            except Exception as e:
                print(f"Failed to parse token response: {e}")
                print(f"Response content: {response.text}")
                return None
        else:
            print(f"Failed to get API token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """
    Main function to demonstrate getting an API token
    """
    print("CapitalX - Get API Token")
    print("=" * 30)
    
    # Replace with your actual credentials
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    
    print("\nProcessing...")
    api_token = get_api_token(email, password)
    
    if api_token:
        print("\n" + "=" * 50)
        print("SUCCESS! Your API token is:")
        print(api_token)
        print("=" * 50)
        print("\nUse this token in your bot by setting:")
        print(f'API_TOKEN = "{api_token}"')
    else:
        print("\nFailed to get API token. Please check your credentials and try again.")

if __name__ == "__main__":
    main()