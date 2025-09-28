import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import Company

def update_investment_tiers():
    """
    Update investment tiers to match the new structure:
    
    Foundation Tier (Beginner Friendly):
    • R70 - R1,120
    
    Growth Tier (Intermediate):
    • R2,240 - R17,920
    
    Premium Tier (Advanced):
    • R35,840 - R50,000
    """
    
    # Define the new tiers with proper ranges
    new_tiers = [
        {
            'name': 'Foundation Tier',
            'share_price': Decimal('70.00'),
            'expected_return': Decimal('1120.00'),
            'duration_days': 7,
            'min_level': 1,
            'description': 'Beginner Friendly - Investment range: R70 - R1,120'
        },
        {
            'name': 'Growth Tier',
            'share_price': Decimal('2240.00'),
            'expected_return': Decimal('17920.00'),
            'duration_days': 14,
            'min_level': 1,
            'description': 'Intermediate - Investment range: R2,240 - R17,920'
        },
        {
            'name': 'Premium Tier',
            'share_price': Decimal('35840.00'),
            'expected_return': Decimal('50000.00'),
            'duration_days': 30,
            'min_level': 1,
            'description': 'Advanced - Investment range: R35,840 - R50,000'
        },
    ]

    # Update or create the new tiers
    for tier in new_tiers:
        company, created = Company.objects.update_or_create(
            name=tier['name'],
            defaults={
                'share_price': tier['share_price'],
                'expected_return': tier['expected_return'],
                'duration_days': tier['duration_days'],
                'min_level': tier['min_level'],
                'description': tier['description']
            }
        )
        
        if created:
            print(f"Created new tier: {tier['name']}")
        else:
            print(f"Updated existing tier: {tier['name']}")

    # Remove any old tiers if they exist
    old_tier_names = ['Sasol', 'Shoprite Holdings', 'Naspers', 'MTN Group', 'Woolworths Holdings', 'Bidvest Group']
    for name in old_tier_names:
        deleted_count, _ = Company.objects.filter(name=name).delete()
        if deleted_count > 0:
            print(f"Removed old tier: {name}")

if __name__ == '__main__':
    print("Updating investment tiers...")
    update_investment_tiers()
    print("Investment tiers updated successfully!")