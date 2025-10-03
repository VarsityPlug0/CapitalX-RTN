"""
Simple script to demonstrate how to get your API token
"""

import requests
import getpass

def get_api_token_manually():
    """
    Instructions for getting your API token manually
    """
    print("How to get your API token:")
    print("=" * 40)
    print("1. Start your Django server:")
    print("   python manage.py runserver")
    print()
    print("2. Open your web browser and go to:")
    print("   http://127.0.0.1:8000/login/")
    print()
    print("3. Log in with your credentials")
    print()
    print("4. After logging in, visit:")
    print("   http://127.0.0.1:8000/api/generate-token/")
    print()
    print("5. Copy the token from the JSON response")
    print("   It will look something like:")
    print('   {"token": "abcd1234efgh5678ijkl9012mnop3456qrst7890"}')
    print()
    print("6. Use this token in your bot code")

def main():
    """
    Main function
    """
    print("CapitalX API Token Retrieval")
    print("=" * 30)
    print()
    
    get_api_token_manually()
    
    print("\n" + "=" * 50)
    print("Once you have your token, update your bot code:")
    print("# Replace 'YOUR_API_TOKEN_HERE' with your actual token")
    print('API_TOKEN = "abcd1234efgh5678ijkl9012mnop3456qrst7890"')
    print()
    print("# Use it in your requests:")
    print('headers = {"Authorization": f"Token {API_TOKEN}"}')
    print('response = requests.get("http://127.0.0.1:8000/api/user/financial-info/", headers=headers)')

if __name__ == "__main__":
    main()