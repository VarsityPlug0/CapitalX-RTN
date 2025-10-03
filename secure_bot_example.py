"""
Secure Bot Example for CapitalX API
This bot uses a secret passphrase for authentication instead of username/password
"""

import requests
import json
import time

class SecureCapitalXBot:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.bot_secret = None
    
    def set_bot_secret(self, secret):
        """
        Set the bot secret for authentication
        """
        self.bot_secret = secret
        print("Bot secret set successfully!")
    
    def validate_secret(self):
        """
        Validate that the bot secret is correct
        """
        if not self.bot_secret:
            print("No bot secret set!")
            return False
        
        url = f"{self.base_url}/api/validate-bot-secret/"
        data = {'secret': self.bot_secret}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('valid'):
                    print(f"✅ Bot secret is valid for user: {result['user']['username']}")
                    return True
                else:
                    print(f"❌ Bot secret is invalid: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Validation failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error validating secret: {e}")
            return False
    
    def get_financial_info(self):
        """
        Get financial information using the bot secret
        """
        if not self.bot_secret:
            print("No bot secret set!")
            return None
        
        url = f"{self.base_url}/api/bot/financial-info/"
        data = {'secret': self.bot_secret}
        
        try:
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error fetching financial info: {e}")
            return None
    
    def display_financial_summary(self):
        """
        Display a summary of financial information
        """
        data = self.get_financial_info()
        if not data or not data.get('success'):
            print("Failed to retrieve financial data")
            return
        
        print("\n" + "="*50)
        print("💰 CAPITALX FINANCIAL SUMMARY")
        print("="*50)
        print(f"User: {data['user']['username']}")
        print(f"Wallet Balance: R{data['wallet']['balance']:.2f}")
        print(f"Active Investments: R{data['investments']['total_active_amount']:.2f}")
        print(f"Plan Investments: R{data['plan_investments']['total_active_amount']:.2f}")
        
        # Show recent deposits
        if data['recent_deposits']:
            print("\n📥 Recent Deposits:")
            for deposit in data['recent_deposits'][:3]:
                print(f"   R{deposit['amount']:.2f} via {deposit['payment_method']} "
                      f"on {deposit['created_at'][:10]}")
        
        # Show recent withdrawals
        if data['recent_withdrawals']:
            print("\n📤 Recent Withdrawals:")
            for withdrawal in data['recent_withdrawals'][:3]:
                status = withdrawal['status'].upper()
                print(f"   R{withdrawal['amount']:.2f} via {withdrawal['payment_method']} "
                      f"({status}) on {withdrawal['created_at'][:10]}")
        
        print("="*50)
    
    def monitor_account(self, interval=60):
        """
        Continuously monitor the account for changes
        """
        print(f"🔍 Starting account monitoring (checking every {interval} seconds)...")
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
                            print(f"📈 Balance increased by R{change:.2f}! New balance: R{current_balance:.2f}")
                        else:
                            print(f"📉 Balance decreased by R{abs(change):.2f}. New balance: R{current_balance:.2f}")
                    
                    last_balance = current_balance
                    print(f"📊 Current balance: R{current_balance:.2f}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")

def setup_bot():
    """
    Guide the user through setting up the bot
    """
    print("🤖 CapitalX Secure Bot Setup")
    print("="*40)
    
    # Create bot instance
    bot = SecureCapitalXBot()
    
    # Get bot secret from user
    print("To use this bot, you need a bot secret.")
    print("Get your bot secret by:")
    print("1. Logging into your CapitalX account")
    print("2. Visiting: http://127.0.0.1:8000/api/generate-bot-secret/")
    print("3. Copy the secret from the JSON response")
    print()
    
    secret = input("Enter your bot secret: ").strip()
    
    if not secret:
        print("❌ No secret provided. Exiting.")
        return None
    
    bot.set_bot_secret(secret)
    
    # Validate the secret
    if not bot.validate_secret():
        print("❌ Failed to validate bot secret. Exiting.")
        return None
    
    print("✅ Bot setup complete!")
    return bot

def main():
    """
    Main function to run the bot
    """
    print("CapitalX Secure Bot")
    print("="*30)
    
    # Setup the bot
    bot = setup_bot()
    if not bot:
        return
    
    # Main menu
    while True:
        print("\n📋 What would you like to do?")
        print("1. Display financial summary")
        print("2. Monitor account for changes")
        print("3. Validate bot secret")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            bot.display_financial_summary()
        elif choice == "2":
            interval = input("Enter monitoring interval in seconds (default 60): ").strip()
            try:
                interval = int(interval) if interval else 60
            except ValueError:
                interval = 60
            bot.monitor_account(interval)
        elif choice == "3":
            bot.validate_secret()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()