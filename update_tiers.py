import os
import sys
import django
from decimal import Decimal

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import Company

def update_tiers_to_match_content():
    # Define the new tiers as shown in the content
    new_tiers = [
        {
            'name': 'Foundation Tier',
            'share_price': Decimal('50.00'),
            'expected_return': Decimal('1120.00'),
            'duration_days': 7,
            'min_level': 1,
            'description': 'Perfect for beginners. Start your investment journey with our Foundation Tier.'
        },
        {
            'name': 'Growth Tier',
            'share_price': Decimal('500.00'),
            'expected_return': Decimal('17920.00'),
            'duration_days': 14,
            'min_level': 1,
            'description': 'For growing investors. Higher returns with our Growth Tier investment plan.'
        },
        {
            'name': 'Premium Tier',
            'share_price': Decimal('2000.00'),
            'expected_return': Decimal('50000.00'),
            'duration_days': 30,
            'min_level': 1,
            'description': 'Maximum returns for serious investors. Premium opportunities with our top tier.'
        }
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

    # Optionally, delete old tiers that don't match the new structure
    # Uncomment the following lines if you want to remove old tiers
    # old_tier_names = ['Sasol', 'Shoprite Holdings', 'Naspers', 'MTN Group', 'Woolworths Holdings', 'Bidvest Group']
    # for name in old_tier_names:
    #     Company.objects.filter(name=name).delete()
    #     print(f"Removed old tier: {name}")

if __name__ == '__main__':
    print("Updating investment tiers to match content...")
    update_tiers_to_match_content()
    print("Investment tiers updated successfully!")