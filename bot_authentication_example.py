"""
Example bot implementation for the secure bot authentication system
"""

import requests
import json

class FinancialBot:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.secret = None
    
    def generate_secret(self, username, password):
        """
        Generate a bot secret by logging in and calling the generate API
        """
        # First, login to get session
        login_data = {
            'username': username,
            'password': password
        }
        
        session = requests.Session()
        login_response = session.post(f"{self.base_url}/login/", data=login_data)
        
        if login_response.status_code != 200:
            raise Exception("Failed to login")
        
        # Then generate the bot secret
        secret_response = session.get(f"{self.base_url}/api/generate-bot-secret/")
        
        if secret_response.status_code == 200:
            data = secret_response.json()
            if data.get('success'):
                self.secret = data['secret']
                return self.secret
            else:
                raise Exception(f"Failed to generate secret: {data.get('error')}")
        else:
            raise Exception(f"Failed to generate secret: {secret_response.status_code}")
    
    def validate_secret(self, secret=None):
        """
        Validate a bot secret
        """
        secret_to_check = secret or self.secret
        if not secret_to_check:
            raise Exception("No secret provided")
        
        data = {'secret': secret_to_check}
        response = requests.post(f"{self.base_url}/api/validate-bot-secret/", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Validation failed: {response.status_code}")
    
    def get_financial_info(self, secret=None):
        """
        Get financial information using bot secret authentication
        """
        secret_to_use = secret or self.secret
        if not secret_to_use:
            raise Exception("No secret provided")
        
        data = {'secret': secret_to_use}
        response = requests.post(f"{self.base_url}/api/bot/financial-info/", json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get financial info: {response.status_code}")

# Example usage
if __name__ == "__main__":
    # Initialize the bot
    bot = FinancialBot("http://localhost:8000")  # Change to your actual URL
    
    try:
        # Generate a secret (requires user login)
        # secret = bot.generate_secret("your_username", "your_password")
        # print(f"Generated secret: {secret}")
        
        # Or use an existing secret
        # bot.secret = "your_existing_secret"
        
        # Validate the secret
        # validation_result = bot.validate_secret()
        # print(f"Secret validation: {validation_result}")
        
        # Get financial information
        # financial_info = bot.get_financial_info()
        # print(f"Financial info: {json.dumps(financial_info, indent=2)}")
        
        print("Bot authentication example ready!")
        print("Uncomment the example code and provide your credentials to test.")
        
    except Exception as e:
        print(f"Error: {e}")