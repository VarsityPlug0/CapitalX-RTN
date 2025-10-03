"""
Complete example of a bot that connects to the CapitalX API
"""

import requests
import json
import time

class CapitalXBot:
    def __init__(self, api_token, base_url="http://127.0.0.1:8000"):
        """
        Initialize the bot with an API token
        """
        self.api_token = api_token
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json'
        }
    
    def get_financial_info(self):
        """
        Get current financial information
        """
        url = f"{self.base_url}/api/user/financial-info/"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching financial info: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None
    
    def display_wallet_balance(self):
        """
        Display current wallet balance
        """
        data = self.get_financial_info()
        if data and data.get('success'):
            balance = data['wallet']['balance']
            print(f"Current Wallet Balance: R{balance:.2f}")
            return balance
        else:
            print("Failed to retrieve wallet balance")
            return None
    
    def list_active_investments(self):
        """
        List all active investments
        """
        data = self.get_financial_info()
        if data and data.get('success'):
            investments = data['investments']['active']
            if investments:
                print(f"\nActive Investments ({len(investments)}):")
                for inv in investments:
                    days_left = inv.get('days_remaining', 'Unknown')
                    print(f"  - {inv['company']}: R{inv['amount']:.2f} "
                          f"(Return: R{inv['return_amount']:.2f}, "
                          f"{days_left} days remaining)")
            else:
                print("\nNo active investments")
            return investments
        else:
            print("Failed to retrieve investments")
            return None
    
    def monitor_account(self, interval=60):
        """
        Continuously monitor the account for changes
        """
        print(f"Starting account monitoring (checking every {interval} seconds)...")
        print("Press Ctrl+C to stop")
        
        last_balance = None
        
        try:
            while True:
                data = self.get_financial_info()
                if data and data.get('success'):
                    current_balance = data['wallet']['balance']
                    
                    # Report balance changes
                    if last_balance is not None and current_balance != last_balance:
                        change = current_balance - last_balance
                        if change > 0:
                            print(f"💰 Balance increased by R{change:.2f}! New balance: R{current_balance:.2f}")
                        else:
                            print(f"💰 Balance decreased by R{abs(change):.2f}. New balance: R{current_balance:.2f}")
                    
                    last_balance = current_balance
                    
                    # Report any new investments
                    active_investments = data['investments']['active']
                    print(f"📊 Current balance: R{current_balance:.2f} | Active investments: {len(active_investments)}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

def main():
    """
    Example usage of the CapitalXBot
    """
    print("CapitalX Bot - Financial Monitoring")
    print("=" * 40)
    
    # Replace with your actual API token
    API_TOKEN = "YOUR_API_TOKEN_HERE"
    
    if API_TOKEN == "YOUR_API_TOKEN_HERE":
        print("Please replace 'YOUR_API_TOKEN_HERE' with your actual API token.")
        print("\nTo get your API token:")
        print("1. Run the server: python manage.py runserver")
        print("2. Log in to the web application")
        print("3. Visit: http://127.0.0.1:8000/api/generate-token/")
        print("4. Copy the token and replace 'YOUR_API_TOKEN_HERE' above")
        return
    
    # Create bot instance
    bot = CapitalXBot(API_TOKEN)
    
    # Test connection
    print("Testing API connection...")
    data = bot.get_financial_info()
    
    if not data:
        print("❌ Failed to connect to API")
        return
    
    if not data.get('success'):
        print("❌ API returned an error:")
        print(f"   {data.get('error', 'Unknown error')}")
        return
    
    print("✅ Successfully connected to API!")
    print(f"👋 Hello, {data['user']['username']}!")
    
    # Display current information
    bot.display_wallet_balance()
    bot.list_active_investments()
    
    # Ask user what they want to do
    print("\nWhat would you like to do?")
    print("1. Display current information")
    print("2. Monitor account for changes")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        # Already displayed above
        pass
    elif choice == "2":
        interval = input("Enter monitoring interval in seconds (default 60): ").strip()
        try:
            interval = int(interval) if interval else 60
        except ValueError:
            interval = 60
        bot.monitor_account(interval)
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()