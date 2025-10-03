"""
Example bot implementation for connecting to the CapitalX API
"""

import requests
import json

class CapitalXBot:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.api_token = None
    
    def login(self, email, password):
        """
        Log in to the application to get a session
        """
        login_url = f"{self.base_url}/login/"
        
        # First, get the login page to retrieve the CSRF token
        response = self.session.get(login_url)
        if response.status_code != 200:
            print(f"Failed to get login page: {response.status_code}")
            return False
        
        # Extract CSRF token from the response (simplified)
        # In a real implementation, you'd parse the HTML to get the CSRF token
        # For this example, we'll proceed without it and let Django handle it
        
        # Perform login
        login_data = {
            'email': email,
            'password': password
        }
        
        response = self.session.post(login_url, data=login_data)
        
        if response.status_code == 200 or response.status_code == 302:
            print("Login successful!")
            return True
        else:
            print(f"Login failed: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            return False
    
    def generate_api_token(self):
        """
        Generate an API token for authenticated requests
        """
        token_url = f"{self.base_url}/api/generate-token/"
        
        response = self.session.get(token_url)
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.api_token = data.get('token')
                print(f"API Token generated: {self.api_token}")
                return self.api_token
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
                print(f"Response content: {response.text}")
                return None
        else:
            print(f"Failed to generate API token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def get_financial_info(self):
        """
        Get financial information using the API token
        """
        if not self.api_token:
            print("No API token available. Please generate one first.")
            return None
        
        financial_url = f"{self.base_url}/api/user/financial-info/"
        
        # Set the authorization header
        headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        response = self.session.get(financial_url, headers=headers)
        
        if response.status_code == 200:
            try:
                return response.json()
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
                print(f"Response content: {response.text}")
                return None
        else:
            print(f"Failed to get financial info: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    def display_financial_summary(self, financial_data):
        """
        Display a summary of the financial information
        """
        if not financial_data or not financial_data.get('success'):
            print("Failed to retrieve financial data")
            return
        
        print("\n=== Financial Summary ===")
        print(f"Username: {financial_data['user']['username']}")
        print(f"Wallet Balance: R{financial_data['wallet']['balance']}")
        print(f"Total Active Investments: R{financial_data['investments']['total_active_amount']}")
        print(f"Total Plan Investments: R{financial_data['plan_investments']['total_active_amount']}")
        
        # Display recent deposits
        print("\nRecent Deposits:")
        for deposit in financial_data['recent_deposits'][:3]:  # Show first 3
            print(f"  - R{deposit['amount']} via {deposit['payment_method']} on {deposit['created_at']}")
        
        # Display recent withdrawals
        print("\nRecent Withdrawals:")
        for withdrawal in financial_data['recent_withdrawals'][:3]:  # Show first 3
            print(f"  - R{withdrawal['amount']} via {withdrawal['payment_method']} ({withdrawal['status']}) on {withdrawal['created_at']}")

def main():
    """
    Example usage of the CapitalXBot
    """
    # Create bot instance
    bot = CapitalXBot()
    
    # Note: You need to have a valid user account
    # Replace with actual credentials
    email = "your_email@example.com"
    password = "your_password"
    
    print("CapitalX Bot - API Connection Example")
    print("=" * 40)
    
    # Login to the application
    if bot.login(email, password):
        # Generate API token
        if bot.generate_api_token():
            # Get financial information
            financial_data = bot.get_financial_info()
            
            if financial_data:
                # Display the financial summary
                bot.display_financial_summary(financial_data)
            else:
                print("Failed to retrieve financial information")
        else:
            print("Failed to generate API token")
    else:
        print("Failed to login to the application")
        print("\nPlease ensure you have:")
        print("1. A valid user account")
        print("2. Correct email and password")
        print("3. The server is running (python manage.py runserver)")

if __name__ == "__main__":
    main()