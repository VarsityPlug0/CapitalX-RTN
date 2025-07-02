import random
from core.models import Company

COMPANIES = [
    {
        'name': 'Tesla Inc.',
        'share_price': 1200.00,
        'expected_return': 1320.00,
        'duration_days': 30,
        'description': 'Electric vehicles and clean energy.'
    },
    {
        'name': 'Apple Inc.',
        'share_price': 180.00,
        'expected_return': 200.00,
        'duration_days': 30,
        'description': 'Consumer electronics and software.'
    },
    {
        'name': 'Amazon.com Inc.',
        'share_price': 3400.00,
        'expected_return': 3740.00,
        'duration_days': 30,
        'description': 'E-commerce and cloud computing.'
    },
    {
        'name': 'Microsoft Corp.',
        'share_price': 300.00,
        'expected_return': 330.00,
        'duration_days': 30,
        'description': 'Software, hardware, and cloud.'
    },
    {
        'name': 'Netflix Inc.',
        'share_price': 500.00,
        'expected_return': 550.00,
        'duration_days': 30,
        'description': 'Streaming entertainment.'
    },
    {
        'name': 'Alphabet Inc.',
        'share_price': 2800.00,
        'expected_return': 3080.00,
        'duration_days': 30,
        'description': 'Google and other tech ventures.'
    },
    {
        'name': 'Nvidia Corp.',
        'share_price': 700.00,
        'expected_return': 770.00,
        'duration_days': 30,
        'description': 'Graphics and AI hardware.'
    },
    {
        'name': 'Meta Platforms',
        'share_price': 350.00,
        'expected_return': 385.00,
        'duration_days': 30,
        'description': 'Social media and metaverse.'
    },
    {
        'name': 'Coca-Cola Co.',
        'share_price': 60.00,
        'expected_return': 66.00,
        'duration_days': 30,
        'description': 'Beverages and consumer goods.'
    },
    {
        'name': 'Visa Inc.',
        'share_price': 220.00,
        'expected_return': 242.00,
        'duration_days': 30,
        'description': 'Payments and financial services.'
    },
]

def create_companies():
    for data in COMPANIES:
        Company.objects.get_or_create(
            name=data['name'],
            defaults={
                'share_price': data['share_price'],
                'expected_return': data['expected_return'],
                'duration_days': data['duration_days'],
                'description': data['description'],
            }
        )
    print('Demo companies created!')

if __name__ == '__main__':
    create_companies() 