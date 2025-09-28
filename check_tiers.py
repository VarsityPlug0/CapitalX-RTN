import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import Company

def check_investment_tiers():
    """Check current investment tiers"""
    companies = Company.objects.all().order_by('share_price')
    
    print("Current Investment Tiers:")
    print("=" * 50)
    
    for company in companies:
        roi = ((company.expected_return - company.share_price) / company.share_price) * 100
        print(f"Name: {company.name}")
        print(f"Investment: R{company.share_price}")
        print(f"Return: R{company.expected_return}")
        print(f"Duration: {company.duration_days} days")
        print(f"ROI: {roi:.1f}%")
        print(f"Description: {company.description}")
        print("-" * 30)

if __name__ == '__main__':
    check_investment_tiers()