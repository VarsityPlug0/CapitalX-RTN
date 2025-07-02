import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safechain_ai.settings')
django.setup()

from core.models import Company

def create_tiers_like_screenshot():
    tiers = [
        {
            'name': 'Sasol',
            'share_price': Decimal('50.00'),
            'expected_return': Decimal('100.00'),
            'duration_days': 1,
            'min_level': 1,
            'description': 'Integrated energy and chemical company.'
        },
        {
            'name': 'Shoprite Holdings',
            'share_price': Decimal('200.00'),
            'expected_return': Decimal('400.00'),
            'duration_days': 3,
            'min_level': 1,
            'description': "Africa's largest food retailer."
        },
        {
            'name': 'Naspers',
            'share_price': Decimal('500.00'),
            'expected_return': Decimal('1000.00'),
            'duration_days': 5,
            'min_level': 1,
            'description': 'Global internet group and technology investor.'
        },
        {
            'name': 'MTN Group',
            'share_price': Decimal('1000.00'),
            'expected_return': Decimal('2000.00'),
            'duration_days': 7,
            'min_level': 1,
            'description': 'Multinational mobile telecommunications company.'
        },
        {
            'name': 'Woolworths Holdings',
            'share_price': Decimal('2000.00'),
            'expected_return': Decimal('4000.00'),
            'duration_days': 10,
            'min_level': 1,
            'description': 'Retail group with food, clothing, and financial services.'
        },
        {
            'name': 'Bidvest Group',
            'share_price': Decimal('5000.00'),
            'expected_return': Decimal('10000.00'),
            'duration_days': 15,
            'min_level': 1,
            'description': 'Diversified industrial group.'
        },
    ]

    for tier in tiers:
        Company.objects.update_or_create(
            name=tier['name'],
            defaults={
                'share_price': tier['share_price'],
                'expected_return': tier['expected_return'],
                'duration_days': tier['duration_days'],
                'min_level': tier['min_level'],
                'description': tier['description']
            }
        )

if __name__ == '__main__':
    print("Creating investment tiers to match screenshot...")
    create_tiers_like_screenshot()
    print("Investment tiers created successfully!") 