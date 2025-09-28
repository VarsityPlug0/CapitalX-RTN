import os
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import CustomUser, Wallet, InvestmentPlan, PlanInvestment

def test_investment_payout():
    """Test that investments automatically close and pay out after their duration"""
    
    # Get the test user
    try:
        user = CustomUser.objects.get(email='admin@example.com')
    except CustomUser.DoesNotExist:
        print("Admin user not found.")
        return
    
    # Get the user's wallet
    wallet, created = Wallet.objects.get_or_create(user=user)
    initial_balance = wallet.balance
    
    print(f"Initial wallet balance: R{initial_balance}")
    
    # Get the shortest duration plan investment (Shoprite Plan)
    try:
        investment = PlanInvestment.objects.filter(user=user, plan__name='Shoprite Plan').first()
        if not investment:
            print("No investment found for Shoprite Plan.")
            return
            
        print(f"Testing investment: {investment.plan.name}")
        print(f"Investment amount: R{investment.amount}")
        print(f"Expected return: R{investment.return_amount}")
        print(f"Total expected payout: R{investment.amount + investment.return_amount}")
        print(f"Investment start: {investment.start_date}")
        print(f"Investment end: {investment.end_date}")
        
        # Simulate time passing by manually setting the investment end date to now
        print("Simulating time passage by setting investment end date to now...")
        investment.end_date = timezone.now()
        investment.save()
        
        # Refresh the investment from the database
        investment.refresh_from_db()
        
        print(f"Is investment complete? {investment.is_complete()}")
        print(f"Is investment active? {investment.is_active}")
        print(f"Has profit been paid? {investment.profit_paid}")
        
        # Trigger the save method which should process the payout
        print("Triggering investment save to process payout...")
        investment.save()
        
        # Refresh the investment and wallet from the database
        investment.refresh_from_db()
        wallet.refresh_from_db()
        
        print(f"Is investment complete? {investment.is_complete()}")
        print(f"Is investment active? {investment.is_active}")
        print(f"Has profit been paid? {investment.profit_paid}")
        print(f"Final wallet balance: R{wallet.balance}")
        
        expected_balance = initial_balance + investment.amount + investment.return_amount
        print(f"Expected wallet balance: R{expected_balance}")
        
        if wallet.balance == expected_balance:
            print("✅ Payout successful! Wallet balance matches expected amount.")
        else:
            print("❌ Payout failed! Wallet balance does not match expected amount.")
            
    except Exception as e:
        print(f"Error testing investment payout: {e}")

if __name__ == '__main__':
    print("Testing investment payout functionality...")
    test_investment_payout()
    print("Test complete!")