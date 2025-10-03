"""
Simple example of how to connect your bot to the CapitalX API
"""

import requests
import json

# Replace with your actual API token (obtained by logging in and visiting /api/generate-token/)
API_TOKEN = "YOUR_API_TOKEN_HERE"

# Base URL of your application
BASE_URL = "http://127.0.0.1:8000"

def get_financial_info():
    """
    Get financial information from the API
    """
    # API endpoint for financial information
    url = f"{BASE_URL}/api/user/financial-info/"
    
    # Headers with authentication token
    headers = {
        'Authorization': f'Token {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Make the API request
        response = requests.get(url, headers=headers, timeout=30)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()
            return data
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None

def display_financial_summary(financial_data):
    """
    Display a summary of the financial information
    """
    if not financial_data:
        print("No financial data to display")
        return
    
    if not financial_data.get('success'):
        print("API request was not successful")
        print(f"Error: {financial_data.get('error', 'Unknown error')}")
        return
    
    print("=== CapitalX Financial Summary ===")
    print(f"User: {financial_data['user']['username']}")
    print(f"Email: {financial_data['user']['email']}")
    print(f"Wallet Balance: R{financial_data['wallet']['balance']:.2f}")
    print(f"Total Active Investments: R{financial_data['investments']['total_active_amount']:.2f}")
    print(f"Total Plan Investments: R{financial_data['plan_investments']['total_active_amount']:.2f}")
    
    # Display active investments
    if financial_data['investments']['active']:
        print("\nActive Investments:")
        for investment in financial_data['investments']['active']:
            print(f"  - {investment['company']}: R{investment['amount']:.2f} "
                  f"(Return: R{investment['return_amount']:.2f})")
    
    # Display recent deposits
    if financial_data['recent_deposits']:
        print("\nRecent Deposits:")
        for deposit in financial_data['recent_deposits'][:5]:  # Show last 5
            print(f"  - R{deposit['amount']:.2f} via {deposit['payment_method']} "
                  f"on {deposit['created_at']}")
    
    # Display recent withdrawals
    if financial_data['recent_withdrawals']:
        print("\nRecent Withdrawals:")
        for withdrawal in financial_data['recent_withdrawals'][:5]:  # Show last 5
            print(f"  - R{withdrawal['amount']:.2f} via {withdrawal['payment_method']} "
                  f"({withdrawal['status']}) on {withdrawal['created_at']}")

def main():
    """
    Main function to demonstrate bot functionality
    """
    print("CapitalX Bot - Financial Information Retrieval")
    print("=" * 50)
    
    # Check if API token is set
    if API_TOKEN == "YOUR_API_TOKEN_HERE":
        print("Please replace 'YOUR_API_TOKEN_HERE' with your actual API token.")
        print("\nTo get your API token:")
        print("1. Log in to your CapitalX application")
        print("2. Visit: http://127.0.0.1:8000/api/generate-token/")
        print("3. Copy the token from the JSON response")
        print("4. Replace 'YOUR_API_TOKEN_HERE' with the copied token")
        return
    
    # Get financial information
    print("Retrieving financial information...")
    financial_data = get_financial_info()
    
    if financial_data:
        # Display the information
        display_financial_summary(financial_data)
    else:
        print("Failed to retrieve financial information")
        print("\nTroubleshooting tips:")
        print("1. Ensure the server is running (python manage.py runserver)")
        print("2. Verify your API token is correct")
        print("3. Check that you have network connectivity")
        print("4. Ensure the API endpoint is accessible")

if __name__ == "__main__":
    main()