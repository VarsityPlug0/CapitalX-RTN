import os
import django
from decimal import Decimal
from django.utils import timezone

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import CustomUser, Wallet, InvestmentPlan, PlanInvestment

def verify_investment_functionality():
    """Verify that investments automatically close and pay out after their duration"""
    
    # Get a test user (or create one if needed)
    try:
        user = CustomUser.objects.get(email='admin@example.com')
    except CustomUser.DoesNotExist:
        print("Admin user not found. Please run this script after setting up the admin user.")
        return
    
    # Get the user's wallet
    wallet, created = Wallet.objects.get_or_create(user=user)
    initial_balance = wallet.balance
    
    print(f"Initial wallet balance: R{initial_balance}")
    
    # Get the shortest duration plan (Shoprite Plan - 12 hours)
    try:
        plan = InvestmentPlan.objects.get(name='Shoprite Plan')
        print(f"Testing with plan: {plan.name} (R{plan.min_amount} -> R{plan.return_amount})")
        
        # Check if user already has an investment in this plan
        existing_investment = PlanInvestment.objects.filter(user=user, plan=plan).first()
        if existing_investment:
            print("User already has an investment in this plan. Skipping creation.")
            print(f"Investment details: R{existing_investment.amount} -> R{existing_investment.return_amount}")
            print(f"Investment start: {existing_investment.start_date}")
            print(f"Investment end: {existing_investment.end_date}")
            print(f"Time remaining: {existing_investment.time_remaining()}")
            
            # Check if investment is complete
            if existing_investment.is_complete() and existing_investment.is_active and not existing_investment.profit_paid:
                print("Investment is complete but not yet paid out. Triggering payout...")
                # Manually trigger the save method to process the payout
                existing_investment.save()
                wallet.refresh_from_db()
                print(f"Updated wallet balance: R{wallet.balance}")
                print(f"Payout amount: R{existing_investment.amount + existing_investment.return_amount}")
            elif existing_investment.profit_paid:
                print("Investment has already been paid out.")
                wallet.refresh_from_db()
                print(f"Current wallet balance: R{wallet.balance}")
            else:
                print("Investment is still active.")
        else:
            # Check if user has sufficient balance
            if wallet.balance >= plan.min_amount:
                print("Creating a test investment...")
                # Create a test investment
                investment = PlanInvestment.objects.create(
                    user=user,
                    plan=plan,
                    amount=plan.min_amount,
                    return_amount=plan.return_amount
                )
                print(f"Created investment: R{investment.amount} -> R{investment.return_amount}")
                print(f"Investment start: {investment.start_date}")
                print(f"Investment end: {investment.end_date}")
                
                # Deduct amount from wallet (this should be done in the view)
                wallet.balance -= plan.min_amount
                wallet.save()
                print(f"Wallet balance after investment: R{wallet.balance}")
            else:
                print(f"Insufficient balance. Need R{plan.min_amount} but only have R{wallet.balance}")
                
    except InvestmentPlan.DoesNotExist:
        print("Shoprite Plan not found.")
        return

if __name__ == '__main__':
    print("Verifying investment functionality...")
    verify_investment_functionality()
    print("Verification complete!")